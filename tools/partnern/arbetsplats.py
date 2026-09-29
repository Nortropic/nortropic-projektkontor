"""Nortropics gemensamma arbetsplats: Hem, Kontoret och Kundstart bredvid partnerns samtalsyta.

Arbetsplatsen är partnerns tjänst, med samma process, inloggning och Host-/Origin-skydd. Allt här är läsning. Ingen
modell anropas, ingenting skrivs i partnerns journal eller i något annat system, och inget uppdrag startas. Källorna
är de som redan finns:

- partnerns eget lager (trådar och överlämningar);
- Aquarium genom fönstrets egen `Fonster`, med samma avgränsade läsning som `tools/aquarium.py`, samma takt (högst en
  läsning varannan minut och bara när någon frågar) och samma renderare och fästa skript;
- de lokala repona genom Git utan hämtning (senast hämtade origin/main);
- Kundstarts lokala testserver genom ett enda GET av dess startsida, utan kakor eller nycklar.

Kundstarts ärenden visas som metadata (ägarens beslut ARBETSPLATS-KUNDSTART-ARENDEN-20260929): listan hämtas från den
lokala testservern med Kundstarts interna nyckel, som läses ur Kundstarts `.env.local` vid varje hämtning, bara den raden,
och aldrig sparas, loggas eller lämnar servern. Bara listans godkända fält behålls. En hämtning läser varje ärende i
Kundstarts lagring och tar ungefär en minut, så den görs i bakgrunden, bara när Kundstart-delen visas och högst var
15:e minut. Varje del som inte går att läsa ger sin egen status i stället för att hela vyn fallerar,
och okänt blir aldrig noll.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from .kallor import KLASSER
from .lager import nu

TOOLS = Path(__file__).resolve().parents[1]
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))
import aquarium_fonster  # noqa: E402  (läser, kör och serverar ingenting vid import)

KUNDSTART_ADRESS = 'http://127.0.0.1:3131'
class _IngenOmdirigering(urllib.request.HTTPRedirectHandler):
    """Följer aldrig en omdirigering: en begäran med nyckel får aldrig föras vidare till en annan adress."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise urllib.error.HTTPError(req.full_url, code, 'omdirigering följs inte', headers, fp)


LOKAL = urllib.request.build_opener(urllib.request.ProxyHandler({}), _IngenOmdirigering())  # ingen proxy, ingen omdirigering, inga kakor
KUNDSTART_PROV = Path(os.environ.get('KUNDSTART_PROV_DATA') or Path.home() / '.nortropic-kundstart-prov')
MAX_KONTEXT = 6
ARENDE_FALT = ('id', 'kund', 'testdialog', 'skapad', 'uppdaterad', 'revision', 'svar', 'material', 'senaste_inlamning',
               'andrat_efter_inlamning')
INLAMNING_FALT = ('tid', 'revision', 'svar', 'material')
ARENDE_CACHE = 900   # en hämtning läser varje ärende i Blob (~1000 läsningar); högst var 15:e minut
ARENDE_SIDOR = 20
ARENDE_SIDTID = 30
ARENDE_FEL_CACHE = 60  # ett misslyckat försök prövas om efter en minut
ARENDE_MAX = 2000
OPPNA_OVL = ('lamnad', 'mottagen', 'startad')
REPON = (('kontoret', 'Kontoret'), ('digitala', 'Digitala'), ('kundstart', 'Kundstart'), ('runtime', 'Runtime'))
BESLUT_ID = r'[A-ZÅÄÖ0-9][A-ZÅÄÖ0-9-]{1,119}'
OBJEKT = re.compile(r'^(?:(?P<ovl>OVL-\d{8}-[A-Za-z0-9]{6}(?:-(?:kontoret|digitala|runtime|kundstart)\d*)?)'
                    r'|beslut:(?P<beslut>' + BESLUT_ID + r')|uppdrag:(?P<uppdrag>[a-z0-9][a-z0-9-]{0,79}))$')
SUBJEKT_ID = re.compile(r'\((' + BESLUT_ID + r')\)(?:\s*\(#\d+\))?\s*$')
SUBJEKT_PR = re.compile(r'\(#(\d+)\)\s*$')


def _git(repo: Path, *args, timeout: int = 10) -> str | None:
    try:
        r = subprocess.run(['git', '-C', str(repo)] + list(args), capture_output=True, text=True, timeout=timeout,
                           check=False)
    except (OSError, subprocess.SubprocessError):
        return None
    return r.stdout if r.returncode == 0 else None


def _mtime_iso(p: Path) -> str | None:
    try:
        return datetime.fromtimestamp(p.stat().st_mtime, timezone.utc).isoformat(timespec='seconds')
    except OSError:
        return None


class Arbetsplats:
    def __init__(self, server, lasare=None):
        self.s = server
        self._lasare = lasare or self._las_aquarium
        self.fonster = aquarium_fonster.Fonster(reader=self._las)
        self.kundstart_adress = KUNDSTART_ADRESS
        self.kundstart_prov = KUNDSTART_PROV
        self._las_lock = threading.Lock()
        self._kandidat = None
        self._projektion = None
        self._senaste_forsok = None
        self._senaste_fel = None
        self._pagar = False
        self._bakgrund = False
        self._arenden = None  # (monotonisk tid, svar) — bara ärendelistans godkända fält, aldrig nyckeln
        self._arenden_las = threading.Lock()
        self._arenden_pagar = False

    # ------------------------------------------------------------- Aquarium
    def _las_aquarium(self) -> dict:
        """Samma avgränsade läsning som `tools/aquarium.py`, i en egen process med tidsgräns."""
        runtime = Path(self.s.k.repon.get('runtime', ''))
        kontor = Path(self.s.k.kontor_primar)
        kod = ('import sys, json; from datetime import datetime, timezone; sys.path.insert(0, %r); import aquarium; '
               'print(json.dumps(aquarium.project(aquarium.collect(%r, %r), datetime.now(timezone.utc)), '
               'ensure_ascii=False))' % (str(TOOLS), str(runtime), str(kontor)))
        r = subprocess.run([sys.executable, '-B', '-c', kod], capture_output=True, text=True, timeout=90, check=False)
        if r.returncode != 0:
            raise RuntimeError('aquarium-läsningen misslyckades')
        return json.loads(r.stdout)

    def _las(self) -> dict:
        with self._las_lock:
            self._pagar = True
            self._senaste_forsok = nu()
        try:
            p = self._lasare()
        except Exception:
            with self._las_lock:
                self._senaste_fel = nu()
                self._pagar = False
            raise
        with self._las_lock:
            self._kandidat = p
            self._pagar = False
        return p

    def _las_vid_behov(self, vanta: bool) -> None:
        """En ny läsning i fönstrets takt. Bara Aquarium-sidan väntar, och bara på den allra första läsningen; allt
        annat får senaste läsningen direkt medan en ny görs i bakgrunden, så att en långsam källa aldrig håller upp
        Hem, Kundstart eller listan."""
        if vanta and self.fonster.read_at() is None:
            slut = time.monotonic() + 95  # en pågående läsning (t.ex. startad av Hem) väntas in, en ny görs inte
            while time.monotonic() < slut:
                with self._las_lock:
                    pagar = self._pagar or self._bakgrund
                if not pagar:
                    break
                time.sleep(0.1)
            if self.fonster.read_at() is None:
                self.fonster.kanske_las()
            return
        with self._las_lock:
            if self._pagar or self._bakgrund:
                return
            self._bakgrund = True

        def las():
            try:
                self.fonster.kanske_las()
            finally:
                with self._las_lock:
                    self._bakgrund = False
        threading.Thread(target=las, name='aquarium-lasning', daemon=True).start()

    def aquarium(self, vanta: bool = False) -> dict:
        """Senaste visningssäkra projektion; en ny läsning bara i fönstrets takt (högst varannan minut)."""
        self._las_vid_behov(vanta)
        read_at = self.fonster.read_at()
        with self._las_lock:
            if self._kandidat is not None and self._kandidat.get('read_at') == read_at:
                self._projektion = self._kandidat
            projektion = self._projektion if read_at is not None else None
            fel, forsok, pagar = self._senaste_fel, self._senaste_forsok, self._pagar or self._bakgrund
            # läst men inte visad: renderaren vägrade läsningen, så den behandlas som otillgänglig
            ovisad = self._kandidat is not None and self._kandidat.get('read_at') != read_at and not pagar
        if projektion is not None and not ovisad:
            status = 'ok'
        elif projektion is not None:
            status = 'ok'  # den förra visade läsningen gäller; fönstret behåller den
        else:
            status = 'laser' if pagar else ('otillganglig' if fel or ovisad else 'ingen_lasning')
        return {'status': status, 'projektion': projektion, 'senaste_fel': fel, 'senaste_forsok': forsok,
                'takt_sekunder': aquarium_fonster.INTERVALL}

    def aquarium_sida(self) -> str | None:
        self._las_vid_behov(vanta=True)
        return self.fonster.sida()

    def aquarium_lasning(self) -> dict:
        self._las_vid_behov(vanta=False)
        return {'read_at': self.fonster.read_at()}

    # ------------------------------------------------------------- objekt och hänvisningar
    def objekt(self, ref: str, med_tradar: bool = True) -> dict | None:
        """Ett arbetsobjekt som arbetsplatsen kan visa och hänvisa till, eller None om det inte finns."""
        m = OBJEKT.match(ref or '')
        if not m:
            return None
        S = self.s
        if m.group('ovl'):
            rad = S.lager.en('select * from overlamning where id=?', (ref,))
            if not rad:
                return None
            d = json.loads(rad['data'] or '{}')
            trad = S.lager.trad(rad['trad']) or {}
            vilande = d.get('status') == 'vilande'  # en vilande beställning är lämnad först när Johnny släppt den
            lamnad = (next((h.get('tid') for h in d.get('historik') or [] if h.get('status') == 'lamnad'), None)
                      if vilande else rad['tid'])
            ut = {'ref': ref, 'typ': 'overlamning', 'titel': d.get('rubrik') or ref, 'status': rad['status'],
                  'mottagare': d.get('mottagare'), 'lamnad': lamnad, 'vilande_fran': rad['tid'] if vilande else None,
                  'uppdaterad': rad['uppdaterad'], 'markning': d.get('markning'),
                  'historik': [{k: h.get(k) for k in ('status', 'tid', 'kvitterad', 'av', 'bevis')}
                               for h in d.get('historik') or []],
                  'start': d.get('start'), 'paket': d.get('katalog_visning'), 'ap06': d.get('ap06'),
                  'bestalld_i': {'id': rad['trad'], 'titel': trad.get('titel')} if trad else None,
                  'kallor': [{'id': rad['trad'], 'titel': 'Tråden där den beställdes'}] if trad else []}
        elif m.group('beslut'):
            k = S.lager.en('select id, titel, datum from kalla where id=?', ('kontor:beslut:' + m.group('beslut'),))
            if not k:
                return None
            ut = {'ref': ref, 'typ': 'beslut', 'titel': k['titel'], 'datum': k['datum'] or None,
                  'kallor': [{'id': k['id'], 'titel': 'Posten i kontorets beslutslogg (main)'}]}
        else:
            namn = m.group('uppdrag')
            p = self.aquarium()['projektion']
            if not p or p.get('verkstaden', {}).get('status') not in (None, 'ok'):
                return None
            traff = None
            for lage, lista in (('arbetar', p['verkstaden'].get('items') or []), ('vilar', p['verkstaden'].get('parked') or [])):
                for x in lista:
                    if x.get('task') == namn:
                        traff = (lage, x)
            if not traff:
                return None
            lage, x = traff
            ut = {'ref': ref, 'typ': 'uppdrag', 'titel': x.get('title') or namn, 'uppdrag': namn, 'lage': lage,
                  'steg': x.get('step'), 'tillstand': x.get('state'), 'utforare': x.get('executor'),
                  'sedan': x.get('since'), 'titel_status': x.get('title_status'), 'lasttid': p.get('read_at'),
                  'kallor': []}
        if med_tradar:
            ut['tradar'] = self.tradar_om(ref)
        return ut

    def tradar_om(self, ref: str) -> list:
        """Trådar där Johnny tog med objektet som sammanhang."""
        ut, sedda = [], set()
        for h in self.s.lager.fraga("select trad, data from handelse where typ='inspel' and data like ? order by seq",
                                    ('%"kontext"%',)):
            try:
                d = json.loads(h['data'])
            except ValueError:
                continue
            if any(k.get('ref') == ref for k in d.get('kontext') or []) and h['trad'] not in sedda:
                sedda.add(h['trad'])
                t = self.s.lager.trad(h['trad']) or {}
                ut.append({'id': h['trad'], 'titel': t.get('titel') or h['trad']})
        return ut

    def prova_kontext(self, refs) -> list:
        """Hänvisningarna som följer med ett inspel: bara befintliga objekt, högst sex, titlar tagna ur källan."""
        if refs in (None, []):
            return []
        if not isinstance(refs, list) or len(refs) > MAX_KONTEXT or not all(isinstance(r, str) for r in refs):
            raise ValueError('Sammanhanget kan bara vara högst %d hänvisningar.' % MAX_KONTEXT)
        ut = []
        for ref in dict.fromkeys(refs):
            o = self.objekt(ref, med_tradar=False)
            if not o:
                raise ValueError('Okänd hänvisning i sammanhanget: %s' % ref[:80])
            ut.append({'ref': ref, 'typ': o['typ'], 'titel': (o['titel'] or ref)[:200],
                       'kalla': o['kallor'][0]['id'] if o['kallor'] else None})
        return ut

    # ------------------------------------------------------------- Hem
    def hem(self) -> dict:
        S = self.s
        tradar = S.lager.fraga('select id, titel, senast from trad where arkiverad=0 order by senast desc limit 6')
        for t in tradar:
            t['aktiv'] = bool(S.aktiv_tur(t['id']))
        return {'lasttid': nu(), 'tradar': tradar, 'overlamningar': self.overlamningar(),
                'kontoret': self._kontorsbild(), 'andringar': self.andringar(), 'kundstart': self.kundstart(kort=True),
                'sok': self.sokomfang()}

    def overlamningar(self) -> list:
        ut = []
        for r in self.s.lager.fraga('select id, trad, status, tid, uppdaterad, data from overlamning order by tid desc'):
            d = json.loads(r['data'] or '{}')
            ut.append({'id': r['id'], 'trad': r['trad'], 'status': r['status'], 'lamnad': r['tid'],
                       'uppdaterad': r['uppdaterad'], 'rubrik': d.get('rubrik'), 'mottagare': d.get('mottagare'),
                       'start': d.get('start'), 'oppen': r['status'] in OPPNA_OVL})
        return ut

    def _kontorsbild(self) -> dict:
        a = self.aquarium()
        p = a.pop('projektion')
        if not p:
            return a
        a.update({k: p.get(k) for k in ('read_at', 'headline', 'agarens_bord', 'utkiken', 'sources', 'provdata')})
        a['arkivet'] = dict(p.get('arkivet') or {}, items=((p.get('arkivet') or {}).get('items') or [])[:8])
        v = p.get('verkstaden') or {}
        last = v.get('status') == 'ok'  # en motor som inte gick att läsa har tomma listor: okänt, aldrig noll
        a['verkstaden'] = {'status': v.get('status'), 'pagar': len(v.get('items') or []) if last else None,
                           'vilar': len(v.get('parked') or []) if last else None}
        return a

    def andringar(self) -> dict:
        """Senaste sammanfogningar på varje repos lokala origin/main, med commitens egen tid (händelsetid)."""
        poster, repon = [], []
        for namn, visning in REPON:
            rot = self.s.k.repon.get(namn)
            if not rot:
                continue
            rot = Path(rot)
            ut = _git(rot, 'log', 'origin/main', '-n', '8', '--format=%H%x1f%cI%x1f%s')
            gemensam = (_git(rot, 'rev-parse', '--git-common-dir') or '').strip()
            hamtad = None
            if gemensam:
                g = Path(gemensam)
                hamtad = _mtime_iso((g if g.is_absolute() else rot / g) / 'FETCH_HEAD')
            repon.append({'repo': namn, 'namn': visning, 'status': 'ok' if ut is not None else 'otillganglig',
                          'hamtad': hamtad})
            for rad in (ut or '').splitlines():
                delar = rad.split('\x1f')
                if len(delar) != 3:
                    continue
                sha, tid_, rubrik = delar
                mid, mpr = SUBJEKT_ID.search(rubrik), SUBJEKT_PR.search(rubrik)
                poster.append({'repo': namn, 'namn': visning, 'sha': sha[:7], 'tid': tid_, 'rubrik': rubrik[:300],
                               'beslut': mid.group(1) if mid else None, 'pr': int(mpr.group(1)) if mpr else None})
        poster.sort(key=lambda p: _epok(p['tid']), reverse=True)
        return {'lasttid': nu(), 'repon': repon, 'poster': poster[:16],
                'not': 'Sammanfogningar på varje repos lokala origin/main (senast hämtad enligt Git); tiden är '
                       'commitens egen, inte när den lästes.'}

    def sokomfang(self) -> dict:
        rader = self.s.lager.fraga('select klass, count(*) as n from kalla group by klass')
        egna = self.s.lager.en("select count(*) as n from sok where klass like 'partner:%'")['n']
        omfang = [{'klass': r['klass'], 'namn': KLASSER.get(r['klass'], r['klass']), 'antal': r['n']} for r in rader]
        omfang.append({'klass': 'partner', 'namn': 'Partnerns trådar, svar och förståelse', 'antal': egna})
        return {'omfang': omfang, 'utanfor': ['Kundstarts ärenden', 'Runtimes körningar och loggar',
                                              'Aquariums läsning (visas i Kontoret)']}

    # ------------------------------------------------------------- Kundstart
    def _intern_nyckel(self):
        """Kundstarts interna nyckel ur dess .env.local, läst nu och bara den raden; None om den saknas."""
        rot = self.s.k.repon.get('kundstart')
        if not rot:
            return None
        try:
            for rad in (Path(rot) / '.env.local').read_text().splitlines():
                m = re.match(r'^KUNDSTART_INTERN_NYCKEL="?([^"\s]+)"?\s*$', rad.strip())
                if m:
                    return m.group(1)
        except OSError:
            return None
        return None

    def _kundstart_get(self, vag: str, nyckel: str):
        req = urllib.request.Request(self.kundstart_adress + vag, method='GET', headers={'Authorization': 'Bearer ' + nyckel})
        try:
            with LOKAL.open(req, timeout=ARENDE_SIDTID) as r:
                return r.status, json.loads(r.read(4_000_000).decode('utf-8'))
        except urllib.error.HTTPError as fel:
            return fel.code, None
        except (OSError, ValueError):
            return None, None

    def kundstart_arenden(self) -> dict:
        """Ärendenas metadata (kundstart-arenden/1): senaste hämtning direkt, en ny i bakgrunden högst var 15:e minut."""
        with self._arenden_las:
            farsk = self._arenden and time.monotonic() - self._arenden[0] < (
                ARENDE_CACHE if self._arenden[1].get('status') == 'ok' else ARENDE_FEL_CACHE)
            if not farsk and not self._arenden_pagar:
                self._arenden_pagar = True
                threading.Thread(target=self._bakgrund_arenden, name='kundstart-arenden', daemon=True).start()
            if self._arenden:
                return dict(self._arenden[1], pagar=self._arenden_pagar)
            return {'status': 'laser', 'lasttid': None, 'arenden': None, 'pagar': True,
                    'skal': 'Läser ärendelistan ur Kundstart; det tar ungefär en minut.'}

    def _bakgrund_arenden(self) -> None:
        try:
            ut = self._hamta_arenden()
        except Exception:
            ut = {'status': 'fel', 'lasttid': nu(), 'arenden': None, 'skal': 'Ärendelistan kunde inte läsas.'}
        with self._arenden_las:
            self._arenden = (time.monotonic(), ut)
            self._arenden_pagar = False

    def _hamta_arenden(self) -> dict:
        lasttid = nu()
        nyckel = self._intern_nyckel()
        if not nyckel:
            return {'status': 'ej_ansluten', 'lasttid': lasttid, 'arenden': None,
                    'skal': 'Kundstarts interna nyckel finns inte i Kundstart-repots .env.local.'}
        rader, cursor, olasbara = [], '', 0
        for _ in range(ARENDE_SIDOR):
            kod, d = self._kundstart_get('/api/intern/arenden' + ('?cursor=' + urllib.parse.quote(cursor, safe='') if cursor else ''), nyckel)
            if kod is None:
                return {'status': 'ej_ansluten', 'lasttid': lasttid, 'arenden': None, 'skal': 'Testservern svarar inte.'}
            if kod == 404 or kod == 405:
                return {'status': 'saknas', 'lasttid': lasttid, 'arenden': None,
                        'skal': 'Testservern har inte ärendelistan än; starta om den ur Kundstarts main.'}
            if kod != 200 or not isinstance(d, dict) or d.get('schema') != 'kundstart-arenden/1':
                return {'status': 'fel', 'lasttid': lasttid, 'arenden': None, 'skal': 'Testservern svarade %s.' % kod}
            for a in d.get('arenden') if isinstance(d.get('arenden'), list) else []:
                rad = _arenderad(a)
                if rad is None:
                    olasbara += 1
                elif len(rader) < ARENDE_MAX:
                    rader.append(rad)
            olasbara += d.get('olasbara') if type(d.get('olasbara')) is int and d.get('olasbara') >= 0 else 0
            cursor = d.get('cursor')
            if cursor is not None and (type(cursor) is not str or len(cursor) > 2000):
                return {'status': 'fel', 'lasttid': lasttid, 'arenden': None, 'skal': 'Testservern gav en ogiltig sidmarkör.'}
            cursor = cursor or ''
            if not cursor:
                return {'status': 'ok', 'lasttid': lasttid, 'arenden': rader, 'komplett': True, 'olasbara': olasbara}
        return {'status': 'ok', 'lasttid': lasttid, 'arenden': rader, 'komplett': False, 'olasbara': olasbara,
                'skal': 'Listan är avkortad efter %d sidor.' % ARENDE_SIDOR}

    def kundstart(self, kort: bool = False) -> dict:
        S = self.s
        lasttid = nu()
        server = {'adress': self.kundstart_adress, 'lasttid': lasttid}
        try:
            with LOKAL.open(urllib.request.Request(self.kundstart_adress + '/', method='GET'), timeout=2) as r:
                server.update(kor=True, http=r.status)
        except urllib.error.HTTPError as fel:
            server.update(kor=True, http=fel.code)
        except (OSError, ValueError):
            server.update(kor=False, http=None)
        rot = S.k.repon.get('kundstart')
        kod = {'status': 'okand'}
        if rot:
            head, main = _git(Path(rot), 'rev-parse', 'HEAD'), _git(Path(rot), 'rev-parse', 'origin/main')
            if head and main:
                kod = {'status': 'ok', 'head': head.strip()[:7], 'main': main.strip()[:7],
                       'ar_main': head.strip() == main.strip()}
        try:
            byggd = json.loads((self.kundstart_prov / 'byggd.json').read_text())
            kod['byggd'] = str(byggd.get('head') or '')[:7] or None
            kod['byggd_tid'] = str(byggd.get('tid') or '')[:25] or None
        except (OSError, ValueError):
            kod['byggd'] = None
        ut = {'lasttid': lasttid, 'provserver': server, 'kod': kod, 'lage': 'prov'}
        if kort:
            return ut
        beslut = S.lager.fraga("select id, titel, datum from kalla where id like 'kontor:beslut:KUNDSTART%' "
                               "order by datum desc, id desc")
        ut['beslut'] = [{'ref': 'beslut:' + b['id'][len('kontor:beslut:'):], 'id': b['id'][len('kontor:beslut:'):],
                         'titel': b['titel'], 'datum': b['datum'] or None} for b in beslut]
        ut['overlamningar'] = [o for o in self.overlamningar() if o['mottagare'] == 'kundstart']
        a = self.aquarium()
        p = a['projektion']
        if p and (p.get('agarens_bord') or {}).get('status', 'ok') == 'ok':
            ut['agarrader'] = {'status': 'ok', 'read_at': p.get('read_at'),
                               'rader': [x for x in p['agarens_bord'].get('items') or [] if 'Kundstart' in (x.get('text') or '')]}
        else:  # ingen läsning, eller ett bord som inte lästes helt: okänt, aldrig en tom lista
            ut['agarrader'] = {'status': 'ofullstandig' if p else a['status'], 'rader': None}
        dig = S.k.repon.get('digitala')
        if dig:
            finns = _git(Path(dig), 'cat-file', '-e', 'origin/main:verktyg/kundstart.py') is not None
            sha = _git(Path(dig), 'rev-parse', '--short=7', 'origin/main')
            ut['digitala'] = {'status': 'ok', 'verktyg': finns, 'main': (sha or '').strip() or None}
        else:
            ut['digitala'] = {'status': 'okand'}
        ut['arenden'] = self.kundstart_arenden()
        return ut


def _text(v, max_tecken=300):
    return v[:max_tecken] if isinstance(v, str) else None


def _antal(v):
    return v if type(v) is int and v >= 0 else None


def _arenderad(a) -> dict | None:
    """En rad ur Kundstarts ärendelista med bara godkända fält och typer; None om raden inte är ett ärende."""
    if not isinstance(a, dict) or not isinstance(a.get('id'), str) or not isinstance(a.get('kund'), str):
        return None
    inl = a.get('senaste_inlamning')
    return {'id': a['id'][:120], 'kund': a['kund'][:200], 'testdialog': a.get('testdialog') is True,
            'skapad': _text(a.get('skapad'), 40), 'uppdaterad': _text(a.get('uppdaterad'), 40), 'revision': _antal(a.get('revision')),
            'svar': _antal(a.get('svar')), 'material': _antal(a.get('material')),
            'senaste_inlamning': {'tid': _text(inl.get('tid'), 40), 'revision': _antal(inl.get('revision')),
                                  'svar': _antal(inl.get('svar')), 'material': _antal(inl.get('material'))}
            if isinstance(inl, dict) else None,
            'andrat_efter_inlamning': a.get('andrat_efter_inlamning') is True}


def _epok(tid: str) -> float:
    try:  # Python 3.9:s fromisoformat tar inte emot ett avslutande Z
        return datetime.fromisoformat(tid[:-1] + '+00:00' if tid.endswith('Z') else tid).timestamp()
    except (TypeError, ValueError):
        return 0.0
