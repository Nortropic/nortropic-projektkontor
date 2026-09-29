"""Partnerns privata lager.

Tre delar med olika status:

* **Journalen** (`journal/journal.jsonl`) är originalet: varje inspel, tur, förståelse, rättelse och
  överlämning läggs till som en rad och skrivs till disk (fsync) innan något annat händer. Rader ändras
  aldrig; en rättelse är en ny rad som pekar på det den ersätter.
* **Originalfilerna** (`blobs/`) är bilagornas exakta byte, namngivna efter sin SHA-256 och skrivna 0600.
* **Indexet** (`index.sqlite`) är härlett. Det byggs om ur journalen (och källorna) och är aldrig en
  auktoritet i sig. Saknas eller skadas det byggs det om vid start.

Bara serverprocessen skriver. Verktyg som modellen anropar går genom servern (se mcp_brygga.py), så
journalen har en enda skrivare; låset nedan skyddar ändå mot en andra process på samma katalog.
"""
from __future__ import annotations

import fcntl
import hashlib
import json
import os
import secrets
import sqlite3
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = 4


def nu() -> str:
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'


def nytt_id(prefix: str) -> str:
    return '%s_%011x%s' % (prefix, int(time.time() * 1000), secrets.token_hex(4))


def _privat_katalog(p: Path) -> Path:
    p.mkdir(parents=True, exist_ok=True)
    os.chmod(p, 0o700)
    return p


def _skriv_privat(path: Path, data: bytes) -> None:
    tmp = path.with_name('.%s.%s.tmp' % (path.name, secrets.token_hex(4)))
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        os.write(fd, data)
        os.fsync(fd)
    finally:
        os.close(fd)
    os.replace(tmp, path)


class Lager:
    def __init__(self, data: Path):
        self.data = _privat_katalog(Path(data))
        self.journal = _privat_katalog(self.data / 'journal') / 'journal.jsonl'
        self.blobs = _privat_katalog(self.data / 'blobs')
        self.harlett = _privat_katalog(self.data / 'harlett')
        self.tmp = _privat_katalog(self.data / 'tmp')
        self.turer = _privat_katalog(self.data / 'turer')
        self.index_fil = self.data / 'index.sqlite'
        self._las = threading.RLock()
        if not self.journal.exists():
            fd = os.open(self.journal, os.O_WRONLY | os.O_CREAT, 0o600)
            os.close(fd)
        self._db = self._oppna_index()
        self._ikapp()

    # ------------------------------------------------------------------ index
    def _oppna_index(self) -> sqlite3.Connection:
        ny = not self.index_fil.exists()
        db = sqlite3.connect(str(self.index_fil), check_same_thread=False, isolation_level=None)
        db.row_factory = sqlite3.Row
        if ny:
            os.chmod(self.index_fil, 0o600)
        try:
            version = db.execute("select varde from meta where nyckel='schema'").fetchone()
        except sqlite3.DatabaseError:
            version = None
        if version is None or int(version[0]) != SCHEMA:
            db.close()
            for suffix in ('', '-wal', '-shm', '-journal'):
                p = Path(str(self.index_fil) + suffix)
                if p.exists():
                    p.unlink()
            db = sqlite3.connect(str(self.index_fil), check_same_thread=False, isolation_level=None)
            db.row_factory = sqlite3.Row
            os.chmod(self.index_fil, 0o600)
            self._skapa_schema(db)
        db.execute('pragma journal_mode=wal')
        return db

    @staticmethod
    def _skapa_schema(db: sqlite3.Connection) -> None:
        db.executescript('''
        create table meta(nyckel text primary key, varde text);
        create table handelse(seq integer primary key, id text unique, typ text, tid text, trad text, data text);
        create table trad(id text primary key, titel text, skapad text, senast text, session text,
                          arkiverad integer default 0, titel_av text);
        create table inspel(id text primary key, trad text, klient_id text unique, tid text, text text,
                            lage text, bilagor text);
        create table tur(id text primary key, trad text, inspel text, status text, startad text, klar text,
                         svar text, session text, modell text, data text);
        create table forstaelse(id text primary key, nr integer, slag text, text text, auktoritet text,
                                kallor text, ersatter text, ersatt_av text, trad text, tur text, tid text,
                                data text);
        create table resonemang(seq integer primary key, trad text, tid text, data text);
        create table blob(sha text primary key, namn text, typ text, klass text, storlek integer, tid text);
        create table koppling(id text primary key, trad text, till text, inspel text, skal text, tid text);
        create table jobb(id text primary key, trad text, status text, data text, tid text, uppdaterad text);
        create table overlamning(id text primary key, trad text, inspel text, status text, data text,
                                 tid text, uppdaterad text, nyckel text unique);
        create table kalla(id text primary key, klass text, titel text, talare text, datum text, ref text,
                           text text, grupp text, ordning integer, data text);
        create virtual table sok using fts5(kalla_id unindexed, klass unindexed, titel, talare unindexed,
                                            datum unindexed, text, tokenize='unicode61 remove_diacritics 0');
        create index kalla_grupp on kalla(grupp, ordning);
        create index inspel_trad on inspel(trad, tid);
        create index tur_trad on tur(trad, startad);
        ''')
        db.execute("insert into meta values('schema', ?)", (str(SCHEMA),))
        db.execute("insert into meta values('journal_seq', '0')")

    def _ikapp(self) -> None:
        with self._las:
            senast = int(self._db.execute("select varde from meta where nyckel='journal_seq'").fetchone()[0])
            for ev in self._las_journal():
                if ev['seq'] > senast:
                    self._indexera(ev)

    def _las_journal(self):
        with open(self.journal, 'rb') as f:
            for rad in f:
                if not rad.endswith(b'\n'):
                    break  # en avbruten sista rad är inte en händelse; den räknas inte
                try:
                    yield json.loads(rad)
                except ValueError:
                    continue

    def bygg_om_index(self) -> int:
        """Bygg om journaldelen av indexet ur journalen. Källdelen byggs av kallor.py."""
        with self._las:
            db = self._db
            for tabell in ('handelse', 'trad', 'inspel', 'tur', 'forstaelse', 'resonemang', 'blob', 'koppling',
                           'jobb', 'overlamning'):
                db.execute('delete from %s' % tabell)
            db.execute("delete from sok where klass like 'partner:%'")
            db.execute("update meta set varde='0' where nyckel='journal_seq'")
            antal = 0
            for ev in self._las_journal():
                self._indexera(ev)
                antal += 1
            return antal

    # ---------------------------------------------------------------- journal
    def _sista_seq_pa_disk(self, f) -> int:
        f.seek(0, os.SEEK_END)
        storlek = f.tell()
        if storlek == 0:
            return 0
        steg = 65536
        while True:
            start = max(0, storlek - steg)
            f.seek(start)
            svans = f.read(storlek - start)
            kompletta = svans.split(b'\n')[:-1]  # sista biten är tom eller en avbruten rad
            if start > 0:
                kompletta = kompletta[1:]  # första biten kan vara en halv rad
            for rad in reversed(kompletta):
                if rad.strip():
                    try:
                        return int(json.loads(rad)['seq'])
                    except (ValueError, KeyError, TypeError):
                        continue  # en skadad rad räknas inte; fortsätt till närmast föregående giltiga
            if start == 0:
                return 0
            steg *= 4

    def lagg_till(self, typ: str, **data) -> dict:
        with self._las:
            with open(self.journal, 'a+b') as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                try:
                    seq = self._sista_seq_pa_disk(f) + 1
                    ev = {'seq': seq, 'id': data.pop('id', None) or nytt_id('ev'), 'typ': typ, 'tid': nu()}
                    ev.update(data)
                    rad = json.dumps(ev, ensure_ascii=False, separators=(',', ':')).encode('utf-8') + b'\n'
                    f.seek(0, os.SEEK_END)
                    if f.tell() > 0:
                        f.seek(-1, os.SEEK_END)
                        if f.read(1) != b'\n':
                            rad = b'\n' + rad  # avsluta en avbruten rad så att den aldrig smälter ihop med nästa
                        f.seek(0, os.SEEK_END)
                    f.write(rad)
                    f.flush()
                    os.fsync(f.fileno())
                finally:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
            self._indexera(ev)
            return ev

    def inspel_kontext(self, inspel_id: str) -> list:
        """Arbetsplatsens hänvisningar som följde med ett inspel, ur journalens händelse (tom för äldre inspel)."""
        rad = self.en("select data from handelse where id=? and typ='inspel'", (inspel_id,))
        try:
            return list(json.loads(rad['data']).get('kontext') or []) if rad else []
        except ValueError:
            return []

    # --------------------------------------------------------------- indexera
    def _fts(self, kalla_id: str, klass: str, titel: str, talare: str, datum: str, text: str) -> None:
        self._db.execute('delete from sok where kalla_id=?', (kalla_id,))
        self._db.execute('insert into sok values(?,?,?,?,?,?)', (kalla_id, klass, titel or '', talare or '',
                                                                 datum or '', text or ''))

    def _indexera(self, ev: dict) -> None:
        db = self._db
        typ = ev['typ']
        trad = ev.get('trad')
        db.execute('begin')
        try:
            db.execute('insert or ignore into handelse values(?,?,?,?,?,?)',
                       (ev['seq'], ev['id'], typ, ev['tid'], trad, json.dumps(ev, ensure_ascii=False)))
            if typ == 'trad':
                db.execute('insert or ignore into trad(id,titel,skapad,senast,titel_av) values(?,?,?,?,?)',
                           (trad, ev.get('titel') or 'Ny tråd', ev['tid'], ev['tid'], ev.get('titel_av', 'agare')))
            elif typ == 'trad_titel':
                db.execute('update trad set titel=?, titel_av=? where id=?',
                           (ev['titel'], ev.get('titel_av', 'agare'), trad))
            elif typ == 'trad_arkiv':
                db.execute('update trad set arkiverad=? where id=?', (1 if ev.get('arkiverad', True) else 0, trad))
            elif typ == 'blob':
                db.execute('insert or ignore into blob values(?,?,?,?,?,?)',
                           (ev['sha'], ev.get('namn'), ev.get('mime'), ev.get('klass'), ev.get('storlek'), ev['tid']))
            elif typ == 'inspel':
                db.execute('insert or ignore into inspel values(?,?,?,?,?,?,?)',
                           (ev['id'], trad, ev.get('klient_id'), ev['tid'], ev.get('text', ''), ev.get('lage'),
                            json.dumps(ev.get('bilagor') or [], ensure_ascii=False)))
                db.execute('update trad set senast=? where id=?', (ev['tid'], trad))
                namn = ' '.join(b.get('namn', '') for b in ev.get('bilagor') or [])
                self._fts('partner:' + ev['id'], 'partner:inspel', namn, 'Johnny', ev['tid'][:10], ev.get('text', ''))
            elif typ == 'tur_start':
                db.execute('insert or replace into tur(id,trad,inspel,status,startad,session,modell,data) '
                           'values(?,?,?,?,?,?,?,?)',
                           (ev['tur'], trad, json.dumps(ev.get('inspel') or []), 'undersoker', ev['tid'],
                            ev.get('session'), ev.get('modell'), json.dumps(ev, ensure_ascii=False)))
            elif typ == 'tur_klar':
                rad = db.execute('select data from tur where id=?', (ev['tur'],)).fetchone()
                data = json.loads(rad[0]) if rad and rad[0] else {}
                data['klar'] = ev
                db.execute('update tur set status=?, klar=?, svar=?, session=coalesce(?, session), data=? where id=?',
                           (ev['status'], ev['tid'], ev.get('svar'), ev.get('session'),
                            json.dumps(data, ensure_ascii=False), ev['tur']))
                if ev.get('svar'):
                    self._fts('partner:' + ev['tur'], 'partner:svar', '', 'partnern', ev['tid'][:10], ev['svar'])
                if ev.get('session') and ev['status'] in ('svarad', 'begransad'):
                    db.execute('update trad set session=?, senast=? where id=?', (ev['session'], ev['tid'], trad))
                elif trad:
                    db.execute('update trad set senast=? where id=?', (ev['tid'], trad))
            elif typ == 'forstaelse':
                nr = db.execute('select coalesce(max(nr),0)+1 from forstaelse').fetchone()[0]
                db.execute('insert or ignore into forstaelse values(?,?,?,?,?,?,?,?,?,?,?,?)',
                           (ev['id'], nr, ev.get('slag'), ev.get('text'), ev.get('auktoritet'),
                            json.dumps(ev.get('kallor') or [], ensure_ascii=False),
                            json.dumps(ev.get('ersatter') or []), None, trad, ev.get('tur'), ev['tid'],
                            json.dumps(ev, ensure_ascii=False)))
                for gammal in ev.get('ersatter') or []:
                    db.execute('update forstaelse set ersatt_av=? where id=? and ersatt_av is null', (ev['id'], gammal))
                self._fts('partner:' + ev['id'], 'partner:forstaelse', ev.get('slag', ''), ev.get('auktoritet', ''),
                          ev['tid'][:10], ev.get('text', ''))
            elif typ == 'resonemang':
                db.execute('insert or ignore into resonemang values(?,?,?,?)',
                           (ev['seq'], trad, ev['tid'], json.dumps(ev, ensure_ascii=False)))
            elif typ == 'koppling':
                db.execute('insert or ignore into koppling values(?,?,?,?,?,?)',
                           (ev['id'], trad, ev.get('till'), ev.get('inspel'), ev.get('skal'), ev['tid']))
            elif typ == 'jobb':
                db.execute('insert or ignore into jobb values(?,?,?,?,?,?)',
                           (ev['jobb'], trad, 'registrerat', json.dumps(ev, ensure_ascii=False), ev['tid'], ev['tid']))
            elif typ == 'jobb_status':
                rad = db.execute('select data from jobb where id=?', (ev['jobb'],)).fetchone()
                data = json.loads(rad[0]) if rad else {}
                data.setdefault('historik', []).append({k: ev.get(k) for k in ('status', 'tid', 'orsak', 'session')})
                if ev.get('resultat') is not None:
                    data['resultat'] = ev['resultat']
                    self._fts('partner:' + ev['jobb'], 'partner:jobb', data.get('rubrik', ''), 'utredare',
                              ev['tid'][:10], ev['resultat'])
                if ev.get('session'):
                    data['session'] = ev['session']
                if ev.get('forbrukning'):
                    data.setdefault('forbrukning', []).append(dict(ev['forbrukning'], tid=ev['tid']))
                db.execute('update jobb set status=?, data=?, uppdaterad=? where id=?',
                           (ev['status'], json.dumps(data, ensure_ascii=False), ev['tid'], ev['jobb']))
            elif typ == 'overlamning':
                db.execute('insert or ignore into overlamning values(?,?,?,?,?,?,?,?)',
                           (ev['overlamning'], trad, ev.get('inspel'), ev.get('status') or 'lamnad',
                            json.dumps(ev, ensure_ascii=False),
                            ev['tid'], ev['tid'], ev.get('nyckel')))
            elif typ == 'overlamning_start':
                rad = db.execute('select data from overlamning where id=?', (ev['overlamning'],)).fetchone()
                data = json.loads(rad[0]) if rad else {}
                data['start'] = ev.get('start') or {}
                data.setdefault('starthistorik', []).append(data['start'])
                db.execute('update overlamning set data=? where id=?',
                           (json.dumps(data, ensure_ascii=False), ev['overlamning']))
            elif typ == 'overlamning_status':
                rad = db.execute('select data from overlamning where id=?', (ev['overlamning'],)).fetchone()
                data = json.loads(rad[0]) if rad else {}
                data.setdefault('historik', []).append({k: ev.get(k) for k in ('status', 'tid', 'bevis', 'av', 'kvitterad')})
                db.execute('update overlamning set status=?, data=?, uppdaterad=? where id=?',
                           (ev['status'], json.dumps(data, ensure_ascii=False), ev['tid'], ev['overlamning']))
            db.execute("update meta set varde=? where nyckel='journal_seq'", (str(ev['seq']),))
            db.execute('commit')
        except Exception:
            db.execute('rollback')
            raise

    # ------------------------------------------------------------------ blobs
    def blob_sokvag(self, sha: str) -> Path:
        if len(sha) != 64 or any(c not in '0123456789abcdef' for c in sha):
            raise ValueError('ogiltig blob')
        return self.blobs / sha[:2] / sha

    def spara_blob_fran_fil(self, tmp: Path) -> str:
        h = hashlib.sha256()
        with open(tmp, 'rb') as f:
            for bit in iter(lambda: f.read(1 << 20), b''):
                h.update(bit)
        sha = h.hexdigest()
        mal = self.blob_sokvag(sha)
        _privat_katalog(mal.parent)
        if mal.exists():
            tmp.unlink()
        else:
            os.chmod(tmp, 0o600)
            with open(tmp, 'rb') as f:
                os.fsync(f.fileno())
            os.replace(tmp, mal)
        return sha

    def spara_blob(self, data: bytes) -> str:
        sha = hashlib.sha256(data).hexdigest()
        mal = self.blob_sokvag(sha)
        _privat_katalog(mal.parent)
        if not mal.exists():
            _skriv_privat(mal, data)
        return sha

    def blob_meta(self, sha: str):
        return self.en('select * from blob where sha=?', (sha,))

    # --------------------------------------------------------------- frågor
    def fraga(self, sql: str, args=()) -> list:
        with self._las:
            return [dict(r) for r in self._db.execute(sql, args).fetchall()]

    def en(self, sql: str, args=()):
        with self._las:
            r = self._db.execute(sql, args).fetchone()
            return dict(r) if r else None

    def kor(self, sql: str, args=()) -> None:
        with self._las:
            self._db.execute(sql, args)

    def skrivning(self):
        """Transaktion för källindexering (inte journal)."""
        return _Transaktion(self)

    def inspel_for_klient(self, klient_id: str):
        return self.en('select * from inspel where klient_id=?', (klient_id,))

    def trad(self, trad_id: str):
        return self.en('select * from trad where id=?', (trad_id,))

    def forstaelse_aktiv(self) -> list:
        return self.fraga('select * from forstaelse where ersatt_av is null order by nr')

    def forstaelse_alla(self) -> list:
        return self.fraga('select * from forstaelse order by nr')

    def resonemang_senast(self, trad_id: str):
        r = self.en('select data from resonemang where trad=? order by seq desc limit 1', (trad_id,))
        return json.loads(r['data']) if r else None

    def spara_privat_fil(self, path: Path, data: bytes) -> None:
        _privat_katalog(path.parent)
        _skriv_privat(path, data)


class _Transaktion:
    def __init__(self, lager: Lager):
        self.lager = lager

    def __enter__(self):
        self.lager._las.acquire()
        self.lager._db.execute('begin')
        return self.lager._db

    def __exit__(self, typ, varde, tb):
        try:
            self.lager._db.execute('commit' if typ is None else 'rollback')
        finally:
            self.lager._las.release()
        return False
