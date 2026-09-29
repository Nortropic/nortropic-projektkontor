"""Partnerns lokala server: samtalsytan, API:t och modellkörningarna.

Lyssnar bara på 127.0.0.1. Varje begäran prövas mot tillåtna Host-namn; webbläsarens API kräver inloggning
(signerad httpOnly-kaka, SameSite=Strict) och ett eget huvud på skrivningar; de interna vägarna för
MCP-bryggan och webbkroken kräver en körningsnyckel som bara gäller medan körningen pågår. Inspel och original
sparas i journalen innan någon modell anropas; sparande och vanliga gränssnittshandlingar anropar aldrig en modell.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import secrets
import signal
import subprocess
import sys
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, unquote, urlparse

from . import VERSION
from . import bilagor as bil
from .agent import Agent, Korning
from .jobb import Jobb
from .kallor import Kallindex, KLASSER
from .konfig import ANSTRANGNING, MODELLER, Konfig, spara_modellval
from .lager import Lager, nu, nytt_id
from .overlamning import Overlamning
from .start import Startvakt
from .systemlage import Systemlage
from .verktyg import Verktyg, Verktygsfel, specifikationer
from .webbpolicy import prova

UI = Path(__file__).resolve().parent / 'ui'
KAKA = 'partner'
KAKA_DAGAR = 30
BARA_SPARA = re.compile(r'^\s*(bara\s+spara|spara\s+bara|spara\s+(det\s+här|detta|den\s+här|dem)|spara)\s*[.!]?\s*$', re.I)
BARA_SPARA_START = re.compile(r'^\s*bara\s+spara\b', re.I)
NYTT_INSPEL = 'Johnny skickade ett nytt inspel under arbetet'
OMSTART = 'serveromstart under arbetet'
BARA_SPARA_AVBROTT = 'Johnny avbröt och sparade utan svar'
ATERUPPTA_INOM = 3600
KALLVAKT_SEKUNDER = 600   # källindexet byggs om inom tio minuter när det det byggs ur har ändrats
STARTVAKT_SEKUNDER = 60   # lämnade överlämningar prövas för start varje minut (och direkt när tjänsten startar)


def las_hemlighet(katalog: Path, namn: str, skapa: bool = True) -> str:
    katalog.mkdir(parents=True, exist_ok=True)
    os.chmod(katalog, 0o700)
    fil = katalog / namn
    if not fil.exists():
        if not skapa:
            raise FileNotFoundError(str(fil))
        fd = os.open(fil, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, 'w') as f:
            f.write(secrets.token_urlsafe(32))
    return fil.read_text().strip()


class Server:
    def __init__(self, k: Konfig):
        self.k = k
        self.url = 'http://127.0.0.1:%d' % k.port
        self.lager = Lager(k.data)
        self.kallor = Kallindex(self.lager, k)
        self.systemlage = Systemlage(k, self.lager)
        self.verktyg = Verktyg(self)
        self.agent = Agent(self)
        self.jobb = Jobb(self)
        self.overlamning = Overlamning(self)
        self.startvakt = Startvakt(self)
        self.inloggning = las_hemlighet(Path(k.hemligheter), 'inloggning.secret')
        self.kaknyckel = las_hemlighet(Path(k.hemligheter), 'kaka.secret').encode()
        self.vardar = {'127.0.0.1:%d' % k.port, 'localhost:%d' % k.port}
        self._korningar = {}
        self._tradkorning = {}
        self._las = threading.RLock()
        self._misslyckade = []
        self.startad = nu()
        self.kodrevision = self._kodrevision()

    # ------------------------------------------------------------- körningar
    def registrera_korning(self, k: Korning) -> None:
        with self._las:
            self._korningar[k.nyckel] = k
            if k.typ == 'tur':
                self._tradkorning[k.trad] = k

    def avregistrera_korning(self, k: Korning) -> None:
        with self._las:
            self._korningar.pop(k.nyckel, None)
            if self._tradkorning.get(k.trad) is k:
                self._tradkorning.pop(k.trad, None)

    def korning_for_nyckel(self, nyckel: str):
        with self._las:
            for n, k in self._korningar.items():
                if hmac.compare_digest(n, nyckel or ''):
                    return k
        return None

    def aktiv_tur(self, trad: str):
        with self._las:
            return self._tradkorning.get(trad)

    # ------------------------------------------------------------- start/stopp
    def aterhamta(self) -> dict:
        """Efter en omstart, ordnad eller efter krasch.

        Turer som stod som pågående utan process (krasch) markeras avbrutna med sitt sparade delsvar. Turer som
        avbröts av en omstart — ordnat stopp eller krasch — återupptas om de startade inom den senaste timmen och
        inte redan tagits om av en senare tur; äldre står kvar som avbrutna med en knapp. Inspel som sparades men
        aldrig hann få en tur plockas upp. Registrerade och omstartsavbrutna utredningar köas igen.
        """
        avbrutna = []
        for t in self.lager.fraga("select * from tur where status='undersoker'"):
            delsvar = ''
            fil = Path(self.lager.turer) / t['id'] / 'delsvar.txt'
            if fil.exists():
                delsvar = fil.read_text('utf-8', errors='replace')
            self.lager.lagg_till('tur_klar', tur=t['id'], trad=t['trad'], status='avbruten', orsak=OMSTART,
                                 delsvar=delsvar[-8000:], forbrukning={'modellanrop': True, 'okand': True})
            avbrutna.append(t['id'])
        ater = []
        for t in self.lager.fraga("select * from tur where status='avbruten' order by startad"):
            klar = (json.loads(t['data'] or '{}').get('klar') or {})
            if klar.get('orsak') != OMSTART or time.time() - _epoch(t['startad']) >= ATERUPPTA_INOM:
                continue
            egna = set(json.loads(t['inspel'] or '[]'))
            senare = [u for u in self.lager.fraga('select inspel, startad from tur where trad=? and startad>?',
                                                  (t['trad'], t['startad'])) if egna & set(json.loads(u['inspel'] or '[]'))]
            if senare or t['trad'] in {a['trad'] for a in ater}:
                continue
            ater.append(t)
        jobb = self.jobb.aterstall_vid_start()
        for t in ater:
            self.ateruppta_tur(t['id'], orsak='automatiskt efter serveromstart')
        upplockade = []
        for trad in {i['trad'] for i in self.lager.fraga("select trad, tid from inspel where lage='svara'")
                     if time.time() - _epoch(i['tid']) < ATERUPPTA_INOM}:
            if not self.aktiv_tur(trad) and any(i['lage'] == 'svara' for i in self.ohanterade(trad)) \
                    and not self._har_misslyckad_tur(trad):
                if self.starta_tur_om_behov(trad):
                    upplockade.append(trad)
        return {'avbrutna_turer': avbrutna, 'aterupptagna_turer': [t['id'] for t in ater], 'jobb': jobb,
                'upplockade_tradar': upplockade}

    def _har_misslyckad_tur(self, trad: str) -> bool:
        """Inspel vars egen tur slutade med fel eller avbröts av Johnny tas inte om automatiskt (ingen omstartsloop)."""
        ohanterade = {i['id'] for i in self.ohanterade(trad)}
        for t in self.lager.fraga("select inspel, status, data from tur where trad=? and status in ('fel','avbruten')", (trad,)):
            orsak = (json.loads(t['data'] or '{}').get('klar') or {}).get('orsak')
            if orsak != OMSTART and ohanterade & set(json.loads(t['inspel'] or '[]')):
                return True
        return False

    def stanga(self) -> None:
        """Ordnat stopp: pågående körningar avbryts och journalförs (avregistreras först efter journalen)."""
        with self._las:
            aktiva = list(self._korningar.values())
        for k in aktiva:
            k.avbryt(OMSTART)
        slut = time.time() + 45  # vakten ger modellen 25 s efter SIGINT och 10 s efter SIGTERM
        while time.time() < slut:
            with self._las:
                if not self._korningar:
                    break
            time.sleep(0.5)

    # ------------------------------------------------------------- trådar och inspel
    def ny_trad(self, titel: str = '', av: str = 'agare') -> dict:
        tid = nytt_id('t')
        self.lager.lagg_till('trad', trad=tid, titel=titel.strip()[:90] or 'Ny tråd',
                             titel_av=av if titel.strip() else 'ingen')
        return self.lager.trad(tid)

    def spara_inspel(self, trad: str, klient_id: str, text: str, blobbar: list, lage: str | None) -> tuple:
        g = self.k.gransar
        if not re.match(r'^[A-Za-z0-9_-]{8,80}$', klient_id or ''):
            raise ValueError('klient_id saknas')
        if len(text or '') > g.inspel_max_tecken:
            raise ValueError('Texten är för lång (högst %d tecken).' % g.inspel_max_tecken)
        if len(blobbar) > g.inspel_max_bilagor:
            raise ValueError('För många bilagor (högst %d).' % g.inspel_max_bilagor)
        if not (text or '').strip() and not blobbar:
            raise ValueError('Tomt inspel.')
        with self._las:
            finns = self.lager.inspel_for_klient(klient_id)
            if finns:
                return finns, True
            if trad == 'ny' or not self.lager.trad(trad):
                trad = self.ny_trad()['id']
            kanda = {}
            nasta = 1
            for i in self.lager.fraga('select bilagor from inspel where trad=?', (trad,)):
                for b in json.loads(i['bilagor'] or '[]'):
                    kanda[b['sha']] = b['ref']
                    nasta = max(nasta, int(b['ref'][1:]) + 1)
            bilagor = []
            for sha in blobbar:
                meta = self.lager.blob_meta(sha)
                if not meta:
                    raise ValueError('Okänd bilaga; ladda upp den igen.')
                ref = kanda.get(sha)
                if not ref:
                    ref = 'B%d' % nasta
                    kanda[sha] = ref
                    nasta += 1
                bilagor.append({'ref': ref, 'sha': sha, 'namn': meta['namn'], 'typ': meta['typ'],
                                'klass': meta['klass'], 'storlek': meta['storlek']})
            if lage not in ('svara', 'bara_spara'):
                lage = 'bara_spara' if (text and (BARA_SPARA.match(text) or BARA_SPARA_START.match(text))) else 'svara'
            ev = self.lager.lagg_till('inspel', trad=trad, klient_id=klient_id, text=text or '', lage=lage,
                                      bilagor=bilagor)
        return self.lager.en('select * from inspel where id=?', (ev['id'],)), False

    def ohanterade(self, trad: str) -> list:
        hanterade = set()
        for t in self.lager.fraga("select inspel, status from tur where trad=?", (trad,)):
            if t['status'] in ('svarad', 'begransad', 'undersoker'):
                hanterade.update(json.loads(t['inspel'] or '[]'))
        return [i for i in self.lager.fraga('select * from inspel where trad=? order by tid', (trad,))
                if i['id'] not in hanterade]

    def starta_tur_om_behov(self, trad: str, avbryt_pagaende: bool = False) -> str | None:
        with self._las:
            pagar = self.aktiv_tur(trad)
            if pagar:
                if avbryt_pagaende:
                    pagar.avbryt(NYTT_INSPEL)  # turens tråd startar nästa tur när avbrottet är journalfört
                return None
            vantar = self.ohanterade(trad)
            if not vantar or all(i['lage'] == 'bara_spara' for i in vantar):
                return None
            return self._starta(trad, vantar, None)

    def avbryt_pagaende(self, trad: str, orsak: str) -> bool:
        """Avbryt trådens pågående tur utan att starta en ny (bara spara med avbryt pågående)."""
        with self._las:
            pagar = self.aktiv_tur(trad)
            return bool(pagar and pagar.avbryt(orsak))

    def ateruppta_tur(self, tur_id: str, orsak: str = 'Johnny återupptog') -> str | None:
        t = self.lager.en('select * from tur where id=?', (tur_id,))
        if not t or t['status'] not in ('avbruten', 'fel', 'begransad'):
            return None
        with self._las:
            if self.aktiv_tur(t['trad']):
                return None
            ids = json.loads(t['inspel'] or '[]')
            vantar = [i for i in self.ohanterade(t['trad'])] or \
                [self.lager.en('select * from inspel where id=?', (i,)) for i in ids]
            return self._starta(t['trad'], [v for v in vantar if v], tur_id, fortsatt=True)

    def _starta(self, trad: str, inspel: list, ateruppta: str | None, fortsatt: bool = False) -> str:
        korning = Korning(self, 'tur', trad, inspel, ateruppta=ateruppta)
        korning.fortsatt_avbruten = fortsatt
        sparr = self.agent.sparrad()
        session = (self.lager.trad(trad) or {}).get('session')
        if ateruppta:
            tidigare = self.lager.en('select session from tur where id=?', (ateruppta,))
            session = (tidigare or {}).get('session') or session
        if not session:
            session = str(uuid.uuid4())  # journalförs före starten så att en krasch inte tappar sessionen
        self.lager.lagg_till('tur_start', tur=korning.id, trad=trad, inspel=[i['id'] for i in inspel],
                             session=session, modell=self.k.modell.huvud, anstrangning=self.k.modell.anstrangning,
                             ateruppta=ateruppta)
        if sparr:
            self.lager.lagg_till('tur_klar', tur=korning.id, trad=trad, status='begransad',
                                 svar='Jag har sparat ditt inspel, men %s Det räknas om vid midnatt (UTC), eller '
                                      'när gränsen höjs i installningar.json.' % sparr, orsak=sparr,
                                 forbrukning={'modellanrop': False})
            return korning.id
        self.registrera_korning(korning)
        threading.Thread(target=self._kor_tur, args=(korning, session), name='tur-' + korning.id, daemon=True).start()
        return korning.id

    def _kor_tur(self, korning: Korning, session: str | None) -> None:
        try:
            res = self.agent.kor(korning, session)
        except Exception as fel:
            res = {'status': 'fel', 'svar': '', 'orsak': 'internt fel: %s' % type(fel).__name__, 'delsvar': korning.delsvar,
                   'session': korning.session, 'forbrukning': {'modellanrop': True}, 'steg': korning.steg[-60:],
                   'kallor': korning.kallor[:120], 'modell': korning.modell}
        try:
            self.lager.lagg_till('tur_klar', tur=korning.id, trad=korning.trad, status=res['status'], svar=res.get('svar'),
                                 orsak=res.get('orsak') or None, delsvar=(res.get('delsvar') or '')[-8000:] or None,
                                 session=res.get('session'), modell=res.get('modell'), forbrukning=res.get('forbrukning'),
                                 steg=res.get('steg'), kallor=res.get('kallor'))
        finally:
            self.avregistrera_korning(korning)  # först när utfallet står i journalen
        if korning.avbruten_av == OMSTART:
            return  # tjänsten stängs; återupptas vid nästa start
        with self._las:
            if self.aktiv_tur(korning.trad):
                return
            egna = {i['id'] for i in korning.inspel}
            vantar = [i for i in self.ohanterade(korning.trad)
                      if res['status'] in ('svarad', 'begransad') or korning.avbruten_av == NYTT_INSPEL or i['id'] not in egna]
            if vantar and not all(i['lage'] == 'bara_spara' for i in vantar):
                self._starta(korning.trad, vantar, korning.id if korning.avbruten_av == NYTT_INSPEL else None)

    # ------------------------------------------------------------- vyer
    def historik(self, trad: str, max_tecken: int = 40000, utom: set | None = None) -> list:
        poster = []
        for i in self.lager.fraga('select * from inspel where trad=? order by tid', (trad,)):
            if utom and i['id'] in utom:
                continue
            b = json.loads(i['bilagor'] or '[]')
            poster.append((i['tid'], 'Johnny (%s, %s)%s:\n%s' % (i['tid'][:16].replace('T', ' '), i['id'],
                                                                 (' [bilagor: %s]' % ', '.join('%s %s' % (x['ref'], x['namn']) for x in b)) if b else '',
                                                                 i['text'])))
        for t in self.lager.fraga("select * from tur where trad=? and svar is not null order by klar", (trad,)):
            poster.append((t['klar'] or t['startad'], 'Partnern (%s, %s):\n%s' % ((t['klar'] or '')[:16].replace('T', ' '),
                                                                                t['id'], t['svar'])))
        for j in self.lager.fraga("select * from jobb where trad=? and status='klart'", (trad,)):
            d = json.loads(j['data'])
            poster.append((j['uppdaterad'], 'Utredningen "%s" (%s) blev klar:\n%s' % (d.get('rubrik'), j['id'],
                                                                                   (d.get('resultat') or '')[:6000])))
        poster.sort(key=lambda x: x[0])
        ut, summa = [], 0
        for _, text in reversed(poster):
            if summa + len(text) > max_tecken:
                ut.append('[… äldre delar av tråden utelämnade; sök eller öppna tråden för dem]')
                break
            ut.append(text)
            summa += len(text)
        return list(reversed(ut))

    def bilaga_i_trad(self, trad: str, ref: str):
        ref = (ref or '').strip()
        for i in self.lager.fraga('select bilagor from inspel where trad=?', (trad,)):
            for b in json.loads(i['bilagor'] or '[]'):
                if b['ref'].lower() == ref.lower() or (len(ref) >= 8 and b['sha'].startswith(ref.lower())):
                    return b
        return None

    def tackningstext(self) -> str:
        t = self.kallor.tackning()
        imp = t.get('improvements') or {}
        bygge = (' Källindexet byggdes %s ur kontorets main %s och byggs om inom tio minuter när repons origin/main, '
                 'de sparade ägarorden eller korpusens manifest ändras; repo-verktygen läser alltid origin/main.') % (
            (self.kallor.byggt() or '?')[:16].replace('T', ' ') + ' UTC',
            ((t.get('kontoret') or {}).get('main') or '?')[:8])
        if not imp or imp.get('fel'):
            return 'Improvements-korpusen är inte ansluten just nu (%s).%s' % (imp.get('fel') or 'inget index byggt',
                                                                                bygge)
        grans = imp.get('kallgrans') or {}
        b = imp.get('bilagor') or {}
        return ('Improvements: %d samtal (%d meddelanden) och %d projektfiler, fångade till och med %s (källgräns '
                'fryst %s, inventering %s). Bilagor: %d fångade, %d registrerade utan bytes; %d historiskt '
                'otillgängliga. Samtal i ChatGPT-projektet efter källgränsen finns inte i korpusen, och tjänsten '
                'har ingen direktåtkomst till ChatGPT. Senare arbetsordrar och ägarord finns bara där sessioner '
                'sparat dem ordagrant i kontorets privata bevis (%d filer). Övrigt: kontorets beslutslogg och plan '
                '(main), förberedelsekampanjens intervju och syntes (härledd), dokument i Runtime, Digitala och '
                'Kundstart (main).') % (
            imp.get('samtal', 0), imp.get('meddelanden', 0), imp.get('dokument', 0),
            (grans.get('observation_slut') or '?')[:16], (grans.get('fryst') or '?')[:16], imp.get('inventering'),
            b.get('fangade', 0), b.get('saknade', 0), grans.get('historiskt_otillgangliga', 0),
            (t.get('privat') or {}).get('filer', 0)) + bygge

    def tradvy(self, trad: str) -> dict:
        t = self.lager.trad(trad)
        if not t:
            return {}
        poster = []
        for i in self.lager.fraga('select * from inspel where trad=? order by tid', (trad,)):
            poster.append({'slag': 'inspel', 'id': i['id'], 'tid': i['tid'], 'text': i['text'], 'lage': i['lage'],
                           'bilagor': json.loads(i['bilagor'] or '[]')})
        for u in self.lager.fraga('select * from tur where trad=? order by startad', (trad,)):
            d = json.loads(u['data'] or '{}')
            klar = d.get('klar') or {}
            poster.append({'slag': 'tur', 'id': u['id'], 'tid': u['startad'], 'klar': u['klar'], 'status': u['status'],
                           'svar': u['svar'], 'orsak': klar.get('orsak'), 'delsvar': klar.get('delsvar'),
                           'inspel': json.loads(u['inspel'] or '[]'), 'steg': klar.get('steg') or [],
                           'kallor': klar.get('kallor') or [], 'forbrukning': klar.get('forbrukning') or {},
                           'modell': klar.get('modell') or u['modell'], 'ateruppta': d.get('ateruppta')})
        for j in self.lager.fraga('select * from jobb where trad=? order by tid', (trad,)):
            d = json.loads(j['data'])
            poster.append({'slag': 'jobb', 'id': j['id'], 'tid': j['tid'], 'uppdaterad': j['uppdaterad'],
                           'status': j['status'], 'rubrik': d.get('rubrik'), 'uppdrag': d.get('uppdrag'),
                           'resultat': d.get('resultat'), 'historik': d.get('historik') or []})
        for o in self.lager.fraga('select * from overlamning where trad=? order by tid', (trad,)):
            d = json.loads(o['data'])
            poster.append({'slag': 'overlamning', 'id': o['id'], 'tid': o['tid'], 'status': o['status'],
                           'rubrik': d.get('rubrik'), 'mottagare': d.get('mottagare'), 'katalog': d.get('katalog_visning'),
                           'ap06': d.get('ap06'), 'historik': d.get('historik') or [], 'agarcitat': d.get('agarcitat'),
                           'start': d.get('start')})
        for kp in self.lager.fraga('select * from koppling where trad=? or till=? order by tid', (trad, trad)):
            annan = kp['till'] if kp['trad'] == trad else kp['trad']
            poster.append({'slag': 'koppling', 'id': kp['id'], 'tid': kp['tid'], 'annan': annan,
                           'annan_titel': (self.lager.trad(annan) or {}).get('titel'), 'skal': kp['skal'],
                           'riktning': 'ut' if kp['trad'] == trad else 'in'})
        for f in self.lager.fraga('select * from forstaelse where trad=? order by nr', (trad,)):
            poster.append({'slag': 'forstaelse', 'id': f['id'], 'tid': f['tid'], 'nr': f['nr'], 'typ': f['slag'],
                           'auktoritet': f['auktoritet'], 'text': f['text'], 'ersatt': bool(f['ersatt_av'])})
        poster.sort(key=lambda p: p['tid'])
        aktiv = self.aktiv_tur(trad)
        jobb_aktiva = {}
        for p in poster:
            if p['slag'] == 'jobb' and p['status'] == 'pagar':
                k = self.jobb.korning(p['id'])
                if k:
                    jobb_aktiva[p['id']] = k.lage()
        return {'trad': t, 'resonemang': self.lager.resonemang_senast(trad), 'poster': poster,
                'aktiv': aktiv.lage() if aktiv else None, 'jobb_aktiva': jobb_aktiva,
                'seq': self.lager.en("select varde from meta where nyckel='journal_seq'")['varde']}

    def modellval(self) -> dict:
        return {'huvud': self.k.modell.huvud, 'anstrangning': self.k.modell.anstrangning,
                'utredare': self.k.modell.utredare, 'modeller': list(MODELLER), 'nivaer': list(ANSTRANGNING)}

    def lagevy(self) -> dict:
        with self._las:
            aktiva = [k.lage() for k in self._korningar.values()]
        return {'version': VERSION, 'kodrevision': self.kodrevision, 'startad': self.startad,
                'modell': {'huvud': self.k.modell.huvud, 'anstrangning': self.k.modell.anstrangning,
                           'utredare': self.k.modell.utredare},
                'forbrukning': self.agent.dygnsforbrukning(), 'gransar': self.k.gransar.__dict__,
                'tackning': self.tackningstext(), 'aktiva': aktiva, 'prov_dolj': list(self.k.prov_dolj),
                'beroende': ('Tjänsten körs lokalt på Johnnys Mac (127.0.0.1:%d) och nås bara när den är igång. '
                             'Modellen är Claude genom Johnnys egen Claude Code-inloggning; ingen annan leverantör '
                             'och inga köpta krediter.' % self.k.port),
                'jobb': self.lager.fraga("select status, count(*) as n from jobb group by status"),
                'overlamningar': self.lager.fraga("select status, count(*) as n from overlamning group by status"),
                'startvakt': self.startvakt.lage()}

    def _kodrevision(self) -> dict:
        rot = Path(__file__).resolve().parents[2]
        def git(*a):
            try:
                r = subprocess.run(['git', '-C', str(rot)] + list(a), capture_output=True, text=True, timeout=10)
            except (OSError, subprocess.SubprocessError):
                return ''
            return r.stdout.strip() if r.returncode == 0 else ''
        head = git('rev-parse', 'HEAD')
        main = git('rev-parse', 'origin/main')
        andrad = bool(git('status', '--porcelain', '--untracked-files=no', '--', 'tools/partnern', 'tools/partner.py'))
        return {'rot': str(rot), 'head': head[:12], 'origin_main': main[:12], 'ar_main': bool(head) and head == main,
                'gren': git('rev-parse', '--abbrev-ref', 'HEAD'), 'lokala_andringar': andrad}

    # ------------------------------------------------------------- inloggning
    def kaka_for(self) -> str:
        data = json.dumps({'exp': int(time.time()) + KAKA_DAGAR * 86400, 'n': secrets.token_hex(8)}).encode()
        del_ = _b64(data)
        return del_ + '.' + _b64(hmac.new(self.kaknyckel, del_.encode(), hashlib.sha256).digest())

    def kaka_ok(self, varde: str) -> bool:
        if not varde or '.' not in varde:
            return False
        del_, sig = varde.rsplit('.', 1)
        ratt = _b64(hmac.new(self.kaknyckel, del_.encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(sig, ratt):
            return False
        try:
            return json.loads(_ub64(del_)).get('exp', 0) > time.time()
        except ValueError:
            return False

    def logga_in(self, nyckel: str) -> bool:
        nu_ = time.time()
        with self._las:
            self._misslyckade = [t for t in self._misslyckade if nu_ - t < 600]
            if len(self._misslyckade) >= 8:
                return False
        if hmac.compare_digest((nyckel or '').encode(), self.inloggning.encode()):
            return True
        with self._las:
            self._misslyckade.append(nu_)
        return False

    def hemligheter(self) -> tuple:
        return (self.inloggning, self.kaknyckel.decode())


def _b64(b: bytes) -> str:
    import base64
    return base64.urlsafe_b64encode(b).decode().rstrip('=')


def _ub64(s: str) -> bytes:
    import base64
    return base64.urlsafe_b64decode(s + '=' * (-len(s) % 4))


def _epoch(tid: str) -> float:
    from datetime import datetime, timezone
    try:
        return datetime.strptime(tid[:19], '%Y-%m-%dT%H:%M:%S').replace(tzinfo=timezone.utc).timestamp()
    except (ValueError, TypeError):
        return 0.0


CSP = ("default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self' blob: data:; connect-src 'self'; "
       "font-src 'self'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'")
STATISKA = {'/': ('index.html', 'text/html; charset=utf-8'), '/app.js': ('app.js', 'text/javascript; charset=utf-8'),
            '/app.css': ('app.css', 'text/css; charset=utf-8'), '/favicon.svg': ('favicon.svg', 'image/svg+xml')}
VISNINGSBARA = {'image/png', 'image/jpeg', 'image/gif', 'image/webp'}


class Hanterare(BaseHTTPRequestHandler):
    server_version = 'Partner'
    sys_version = ''
    protocol_version = 'HTTP/1.1'
    S: Server = None  # sätts av starta()

    def log_message(self, fmt, *args):  # inga innehåll, frågor eller nycklar i loggen
        kod = args[1] if len(args) > 1 and fmt.startswith('"%s" %s') else ''
        sys.stderr.write('%s %s %s %s\n' % (nu()[:19], self.command, urlparse(self.path).path[:60], kod))

    # ------------------------------------------------------------- svar
    def _svara(self, kod: int, data=None, typ='application/json; charset=utf-8', huvud=None, kropp: bytes | None = None):
        if kropp is None:
            kropp = json.dumps(data if data is not None else {}, ensure_ascii=False).encode('utf-8')
        self.send_response(kod)
        self.send_header('Content-Type', typ)
        self.send_header('Content-Length', str(len(kropp)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'no-referrer')
        self.send_header('X-Frame-Options', 'DENY')
        if 'Content-Security-Policy' not in (huvud or {}):
            self.send_header('Content-Security-Policy', CSP)
        for k, v in (huvud or {}).items():
            self.send_header(k, v)
        self.end_headers()
        if self.command != 'HEAD':
            self.wfile.write(kropp)

    def _fel(self, kod: int, text: str):
        self._svara(kod, {'fel': text})

    def _host_ok(self) -> bool:
        return (self.headers.get('Host') or '') in self.S.vardar

    def _inloggad(self) -> bool:
        kakor = self.headers.get('Cookie') or ''
        for del_ in kakor.split(';'):
            namn, _, varde = del_.strip().partition('=')
            if namn == KAKA and self.S.kaka_ok(varde):
                return True
        return False

    def _skrivning_ok(self) -> bool:
        if self.headers.get('X-Partner') != '1':
            return False
        ursprung = self.headers.get('Origin')
        if ursprung and urlparse(ursprung).netloc not in self.S.vardar:
            return False
        return True

    def _json(self, max_byte: int = 2_000_000):
        langd = int(self.headers.get('Content-Length') or 0)
        if langd > max_byte:
            raise ValueError('för stor begäran')
        data = self.rfile.read(langd) if langd else b'{}'
        return json.loads(data.decode('utf-8') or '{}')

    # ------------------------------------------------------------- GET
    def do_GET(self):
        if not self._host_ok():
            return self._fel(421, 'fel värd')
        u = urlparse(self.path)
        p = u.path
        q = {k: v[0] for k, v in parse_qs(u.query).items()}
        if p in STATISKA:
            namn, typ = STATISKA[p]
            return self._svara(200, typ=typ, kropp=(UI / namn).read_bytes())
        if p == '/halsa':
            return self._svara(200, {'ok': True, 'version': VERSION, 'startad': self.S.startad})
        if p == '/intern/verktyg':
            k = self.S.korning_for_nyckel(self.headers.get('X-Partner-Korning'))
            if not k:
                return self._fel(403, 'ingen giltig körning')
            return self._svara(200, {'verktyg': specifikationer(k.typ)})
        if not p.startswith('/api/'):
            return self._fel(404, 'finns inte')
        if p == '/api/session':  # svarar även utloggad, så att ytan kan visa inloggningen utan ett fel
            return self._svara(200, {'inloggad': self._inloggad()})
        if not self._inloggad():
            return self._fel(401, 'logga in')
        try:
            return self._get_api(p, q)
        except Exception as fel:
            return self._fel(500, 'internt fel: %s' % type(fel).__name__)

    def _get_api(self, p, q):
        S = self.S
        if p == '/api/installningar':
            return self._svara(200, S.modellval())
        if p == '/api/lage':
            S.overlamning.las_kvittenser()
            return self._svara(200, S.lagevy())
        if p == '/api/tradar':
            rader = S.lager.fraga('select * from trad where arkiverad=0 order by senast desc limit 200')
            for r in rader:
                r['aktiv'] = bool(S.aktiv_tur(r['id']))
                r['inspel'] = S.lager.en('select count(*) as n from inspel where trad=?', (r['id'],))['n']
                r.pop('session', None)
            return self._svara(200, {'tradar': rader})
        m = re.match(r'^/api/trad/(t_[A-Za-z0-9]+)$', p)
        if m:
            vy = S.tradvy(m.group(1))
            return self._svara(200, vy) if vy else self._fel(404, 'tråden finns inte')
        if p == '/api/sok':
            omfang = [x for x in (q.get('omfang') or '').split(',') if x]
            return self._svara(200, {'traffar': S.kallor.sok(q.get('q', ''), omfang or None, int(q.get('antal') or 20))})
        if p == '/api/kalla':
            kid = q.get('id', '')
            try:
                text = self._kalltext(kid)
                if text is not None:
                    return self._svara(200, {'id': kid, 'text': text})
                ut = S.kallor.oppna(kid, int(q.get('omkrets') or 2))
            except Verktygsfel as fel:
                return self._fel(404, str(fel))
            return self._svara(200, ut) if ut else self._fel(404, 'källan finns inte')
        if p == '/api/forstaelse':
            rader = S.lager.forstaelse_alla()
            for r in rader:
                d = json.loads(r.pop('data'))
                r['agarcitat'] = d.get('agarcitat')
                r['kallor'] = json.loads(r['kallor'] or '[]')
                r['ersatter'] = json.loads(r['ersatter'] or '[]')
            return self._svara(200, {'poster': rader})
        m = re.match(r'^/api/bilaga/([0-9a-f]{64})$', p)
        if m:
            return self._bilaga(m.group(1), q)
        if p == '/api/overlamningar':
            S.overlamning.las_kvittenser()
            rader = S.lager.fraga('select id, trad, status, tid, uppdaterad, data from overlamning order by tid desc')
            for r in rader:
                d = json.loads(r.pop('data'))
                r.update({k: d.get(k) for k in ('rubrik', 'mottagare', 'katalog_visning', 'ap06', 'historik', 'start')})
            return self._svara(200, {'overlamningar': rader})
        return self._fel(404, 'finns inte')

    def _kalltext(self, kid: str):
        """Referenser som öppnas genom samma läsvägar som verktygen (repo, GitHub, systemläge, partnerposter)."""
        S = self.S
        if kid.startswith(('partner:', 'F-', 't_')):
            return S.verktyg.v_oppna(_Visning(), {'id': kid})['text']
        m = re.match(r'^repo:([a-z]+)@([^:]+):(.+)$', kid)
        if m:
            return S.verktyg.v_repo_las(_Visning(), {'repo': m.group(1), 'ref': m.group(2), 'sokvag': m.group(3)})['text']
        if kid.startswith('github:'):
            return S.verktyg.v_github(_Visning(), {'sokvag': kid[7:]})['text']
        if kid.startswith('systemlage:'):
            return json.dumps(S.systemlage.las([kid[11:]]), ensure_ascii=False, indent=1)
        return None

    def _bilaga(self, sha: str, q):
        meta = self.S.lager.blob_meta(sha)
        if not meta:
            return self._fel(404, 'finns inte')
        fil = self.S.lager.blob_sokvag(sha)
        typ = meta['typ'] or 'application/octet-stream'
        namn = meta['namn'] or 'fil'
        visa = typ in VISNINGSBARA and q.get('ladda') != '1'
        if meta['klass'] == 'bild' and typ not in VISNINGSBARA and q.get('ladda') != '1':
            info = bil.harled(fil, meta['klass'], typ, self.S.lager.harlett / sha)
            if info.get('modellbild') and info.get('modellbild_fil') != 'original':
                fil, typ, visa = self.S.lager.harlett / sha / info['modellbild_fil'], 'image/jpeg', True
        huvud = {'Content-Security-Policy': "default-src 'none'; sandbox", 'Cross-Origin-Resource-Policy': 'same-origin',
                 'Content-Disposition': '%s; filename*=UTF-8\'\'%s' % ('inline' if visa else 'attachment', quote(namn))}
        return self._svara(200, typ=typ if visa else 'application/octet-stream', huvud=huvud, kropp=fil.read_bytes())

    # ------------------------------------------------------------- POST
    def do_POST(self):
        if not self._host_ok():
            return self._fel(421, 'fel värd')
        p = urlparse(self.path).path
        if p.startswith('/intern/'):
            return self._intern(p)
        if not p.startswith('/api/'):
            return self._fel(404, 'finns inte')
        if not self._skrivning_ok():
            return self._fel(403, 'skrivningar kräver samtalsytans eget huvud och ursprung')
        if p == '/api/logga-in':
            try:
                d = self._json(10_000)
            except ValueError:
                return self._fel(400, 'felaktig begäran')
            if self.S.logga_in(str(d.get('nyckel') or '')):
                kaka = '%s=%s; HttpOnly; SameSite=Strict; Path=/; Max-Age=%d' % (KAKA, self.S.kaka_for(), KAKA_DAGAR * 86400)
                return self._svara(200, {'inloggad': True}, huvud={'Set-Cookie': kaka})
            return self._fel(403, 'fel nyckel (eller för många försök; vänta tio minuter)')
        if not self._inloggad():
            return self._fel(401, 'logga in')
        try:
            if p == '/api/bilaga':
                return self._ladda_upp()
            d = self._json()
            return self._post_api(p, d)
        except ValueError as fel:
            return self._fel(400, str(fel))
        except Exception as fel:
            return self._fel(500, 'internt fel: %s' % type(fel).__name__)

    def _ladda_upp(self):
        S = self.S
        langd = int(self.headers.get('Content-Length') or 0)
        if langd <= 0:
            raise ValueError('tom fil')
        if langd > S.k.gransar.bilaga_max_byte:
            raise ValueError('Filen är för stor (högst %d MB).' % (S.k.gransar.bilaga_max_byte // 1_000_000))
        namn = bil.sakert_namn(unquote(self.headers.get('X-Filnamn') or 'fil'))
        tmp = Path(S.lager.tmp) / ('upp-' + secrets.token_hex(8))
        fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        huvud = b''
        kvar = langd
        with os.fdopen(fd, 'wb') as f:
            while kvar > 0:
                bit = self.rfile.read(min(1 << 20, kvar))
                if not bit:
                    break
                if len(huvud) < 4096:
                    huvud += bit[:4096 - len(huvud)]
                f.write(bit)
                kvar -= len(bit)
        if kvar:
            tmp.unlink()
            raise ValueError('uppladdningen avbröts')
        typ = bil.identifiera(namn, huvud)
        sha = S.lager.spara_blob_fran_fil(tmp)
        with S._las:
            if not S.lager.blob_meta(sha):
                S.lager.lagg_till('blob', sha=sha, namn=namn, mime=typ['mime'], klass=typ['klass'], storlek=langd)
        meta = S.lager.blob_meta(sha)
        threading.Thread(target=bil.harled, args=(S.lager.blob_sokvag(sha), meta['klass'], meta['typ'],
                                                  S.lager.harlett / sha), daemon=True).start()
        return self._svara(200, {'sha': sha, 'namn': namn, 'klass': meta['klass'], 'typ': meta['typ'],
                                 'storlek': meta['storlek'], 'sparad': meta['tid']})

    def _post_api(self, p, d):
        S = self.S
        if p == '/api/logga-ut':
            return self._svara(200, {'ok': True}, huvud={'Set-Cookie': '%s=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0' % KAKA})
        if p == '/api/tradar':
            return self._svara(200, S.ny_trad(str(d.get('titel') or '')))
        if p == '/api/installningar':
            fore = {'huvud': S.k.modell.huvud, 'anstrangning': S.k.modell.anstrangning}
            ny = spara_modellval(S.k, str(d.get('huvud') or fore['huvud']), str(d.get('anstrangning') or fore['anstrangning']))
            if ny != fore:
                S.lager.lagg_till('installning', fore=fore, **ny)
            return self._svara(200, S.modellval())
        if p == '/api/inspel':
            inspel, dubblett = S.spara_inspel(str(d.get('trad') or 'ny'), str(d.get('klient_id') or ''),
                                              str(d.get('text') or ''), [str(x) for x in d.get('bilagor') or []],
                                              d.get('lage'))
            tur = None
            if not dubblett and inspel['lage'] != 'bara_spara':  # att spara anropar aldrig en modell
                tur = S.starta_tur_om_behov(inspel['trad'], avbryt_pagaende=bool(d.get('avbryt_pagaende')))
            elif not dubblett and d.get('avbryt_pagaende'):
                S.avbryt_pagaende(inspel['trad'], BARA_SPARA_AVBROTT)
            return self._svara(200, {'inspel': inspel, 'dubblett': dubblett, 'tur': tur})
        m = re.match(r'^/api/trad/(t_[A-Za-z0-9]+)/(titel|arkivera)$', p)
        if m:
            if not S.lager.trad(m.group(1)):
                return self._fel(404, 'tråden finns inte')
            if m.group(2) == 'titel':
                S.lager.lagg_till('trad_titel', trad=m.group(1), titel=str(d.get('titel') or '').strip()[:90] or 'Tråd',
                                  titel_av='agare')
            else:
                S.lager.lagg_till('trad_arkiv', trad=m.group(1), arkiverad=bool(d.get('arkiverad', True)))
            return self._svara(200, {'ok': True})
        m = re.match(r'^/api/tur/(tur_[A-Za-z0-9]+)/(avbryt|ateruppta)$', p)
        if m:
            t = S.lager.en('select * from tur where id=?', (m.group(1),))
            if not t:
                return self._fel(404, 'turen finns inte')
            if m.group(2) == 'avbryt':
                k = S.aktiv_tur(t['trad'])
                ok = bool(k and k.id == t['id'] and k.avbryt('Johnny avbröt'))
                return self._svara(200, {'ok': ok})
            ny = S.ateruppta_tur(t['id'])
            return self._svara(200, {'ok': bool(ny), 'tur': ny})
        m = re.match(r'^/api/jobb/(jobb_[A-Za-z0-9]+)/(avbryt|ateruppta)$', p)
        if m:
            ok = S.jobb.avbryt(m.group(1)) if m.group(2) == 'avbryt' else S.jobb.ateruppta(m.group(1))
            return self._svara(200, {'ok': bool(ok)})
        return self._fel(404, 'finns inte')

    # ------------------------------------------------------------- internt (bryggan och kroken)
    def _intern(self, p):
        k = self.S.korning_for_nyckel(self.headers.get('X-Partner-Korning'))
        if not k:
            return self._fel(403, 'ingen giltig körning')
        try:
            d = self._json(200_000)
        except ValueError:
            return self._fel(400, 'felaktig begäran')
        if p == '/intern/krok':
            beslut, skal = prova(k, str(d.get('verktyg')), d.get('indata') or {}, self.S.hemligheter())
            if beslut == 'deny':
                k.handelse('nekat', skal)
            return self._svara(200, {'beslut': beslut, 'skal': skal})
        m = re.match(r'^/intern/verktyg/([a-z_]+)$', p)
        if not m:
            return self._fel(404, 'finns inte')
        try:
            svar = self.S.verktyg.anropa(k, m.group(1), d)
        except Verktygsfel as fel:
            return self._svara(200, {'fel': str(fel)})
        except Exception as fel:
            return self._svara(200, {'fel': 'Verktyget misslyckades (%s).' % type(fel).__name__})
        return self._svara(200, svar)

    do_HEAD = do_GET


class _Visning:
    typ = 'tur'
    trad = ''
    id = 'visning'

    def logga_kallor(self, *a):
        pass

    def handelse(self, *a):
        pass


def starta(k: Konfig, bygg_index: bool = True, pidfil: Path | None = None):
    S = Server(k)
    if bygg_index:  # även när källorna ändrats sedan förra bygget (ny main, nya sparade ägarord)
        try:
            S.kallor.uppdatera_om_inaktuellt()
        except Exception as fel:  # det tidigare indexet gäller; vakten försöker igen
            sys.stderr.write('%s källindexet kunde inte byggas om vid start (%s)\n' % (nu()[:19], type(fel).__name__))
    Hanterare.S = S
    httpd = ThreadingHTTPServer(('127.0.0.1', k.port), Hanterare)
    httpd.daemon_threads = True
    if pidfil:  # först när porten är bunden, så att en andra instans aldrig skriver över den körandes pid
        fd = os.open(pidfil, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        os.fchmod(fd, 0o600)
        os.write(fd, str(os.getpid()).encode())
        os.close(fd)
    S.jobb.starta_arbetare()
    aterhamtat = S.aterhamta()

    def stoppa(signum, ram):
        threading.Thread(target=lambda: (S.stanga(), httpd.shutdown()), daemon=True).start()
    signal.signal(signal.SIGTERM, stoppa)
    signal.signal(signal.SIGINT, stoppa)

    def kvittensvakt():
        while True:
            time.sleep(30)
            try:
                S.overlamning.las_kvittenser()
            except Exception:
                pass
    threading.Thread(target=kvittensvakt, daemon=True).start()

    def kallvakt():
        while True:
            time.sleep(KALLVAKT_SEKUNDER)
            try:
                S.kallor.uppdatera_om_inaktuellt()
            except Exception:
                pass
    if bygg_index:
        threading.Thread(target=kallvakt, daemon=True).start()

    def startvakt():  # först när porten är bunden: en andra instans når aldrig hit
        time.sleep(5)
        while True:
            try:
                S.overlamning.las_kvittenser()
                for oid, typ in S.startvakt.granska():
                    sys.stderr.write('%s startvakten: %s %s\n' % (nu()[:19], oid, typ))
            except Exception as fel:
                sys.stderr.write('%s startvakten: fel (%s)\n' % (nu()[:19], type(fel).__name__))
            time.sleep(STARTVAKT_SEKUNDER)
    if S.startvakt.paslagen():
        threading.Thread(target=startvakt, name='startvakt', daemon=True).start()
    sys.stderr.write('%s partner lyssnar på %s (kod %s, data %s); återhämtat: %s\n' % (
        nu()[:19], S.url, S.kodrevision.get('head'), k.data, json.dumps(aterhamtat)))
    httpd.serve_forever()
    return S
