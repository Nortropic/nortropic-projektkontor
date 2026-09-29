"""Nortropics arbetsplats: adresser, Aquarium på samma ursprung, Hem, Kundstart, objekt och sammanhang.

Samma uppställning som `tools/test_partner.py`: en riktig server i processen på 127.0.0.1 med en fejkad `claude` och
syntetiska källor. Aquarium läses genom en injicerad läsare som lämnar en syntetisk projektion (`provdata`); ingen
sond, inget git mot verkliga repon och inget nät utåt. Kundstarts testserver ersätts av en liten lokal server på en
fri port.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
import threading
import urllib.parse
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import test_partner as tp
from test_aquarium_vy import parked, projection, sources, work

import aquarium_vy
from partnern import arbetsplats as ap

LAST = '2026-09-29T10:41:23+00:00'
BORD = {'status': 'ok', 'items': [
    {'kind': 'beslut', 'text': 'Digitala Kundstart: bevarandetid är inte beslutad (KUNDSTART-20260927)',
     'since': '2026-09-27', 'basis': 'planens ägartur'},
    {'kind': 'operatörshandling', 'text': 'Starta om testservern', 'since': '2026-09-28', 'basis': 'planens ägartur'},
    {'kind': 'operatörshandling', 'text': 'Överlämningen kunde inte startas', 'since': '2026-09-29T08:00:00Z',
     'basis': 'överlämningens startlogg'}]}


def en_projektion(read_at=LAST, **over):
    p = projection(read_at=read_at, verkstaden={'status': 'ok', 'titles': 'ok',
                                                'items': [work(task='office-bygge-1')],
                                                'parked': [parked(task='office-vilar-1')]})
    p['agarens_bord'] = BORD
    p.update(over)
    return p


class Lasare:
    """En räknande Aquarium-läsare: projektionen, eller ett fel."""

    def __init__(self, projektion=None, fel=False):
        self.projektion = projektion if projektion is not None else en_projektion()
        self.fel = fel
        self.antal = 0

    def __call__(self):
        self.antal += 1
        if self.fel:
            raise RuntimeError('källan svarar inte')
        return self.projektion


class KundstartAtrapp(BaseHTTPRequestHandler):
    antal = 0
    kakor = []

    def do_GET(self):
        KundstartAtrapp.antal += 1
        KundstartAtrapp.kakor.append(self.headers.get('Cookie'))
        self.send_response(200)
        self.send_header('Content-Length', '2')
        self.end_headers()
        self.wfile.write(b'ok')

    def log_message(self, *a):
        pass


class ArbetsplatsMiljo(tp.Miljo):
    def setUp(self):
        super().setUp()
        self.lasare = Lasare()
        self.S.arbetsplats = ap.Arbetsplats(self.S, lasare=self.lasare)
        self.S.arbetsplats.kundstart_adress = 'http://127.0.0.1:%d' % tp.fri_port()  # ingen server där
        self.S.arbetsplats.kundstart_prov = self.rot / 'kundstart-prov'
        self.logga_in()

    def forsta_lasning(self):
        """Aquarium-sidan är det enda som väntar på den första läsningen."""
        return self.anrop('GET', '/kontoret/aquarium')

    def journal_seq(self):
        return self.S.lager.en("select varde from meta where nyckel='journal_seq'")['varde']

    def overlamning(self, trad, oid='OVL-20260929-abc123', status='startad', mottagare='kontorets-kedjedrivare'):
        self.S.lager.lagg_till('overlamning', overlamning=oid, trad=trad, inspel='ev_x', nyckel=oid,
                               rubrik='Digitala: underhållsform', mottagare=mottagare,
                               katalog_visning='evidence/nasta-uppdrag/local/partner-' + oid)
        self.S.lager.lagg_till('overlamning_start', overlamning=oid, trad=trad,
                               start={'typ': 'vantar', 'skal': 'en annan session skriver'})
        if status != 'lamnad':
            self.S.lager.lagg_till('overlamning_status', overlamning=oid, trad=trad, status=status,
                                   kvitterad='2026-09-29T10:12:15Z', av='prov', bevis='')
        return oid


class Adresser(ArbetsplatsMiljo):
    def test_varje_del_har_en_direktadress_och_okanda_finns_inte(self):
        index = (tp.srv.UI / 'index.html').read_bytes()
        for vag in ('/', '/kontoret', '/kontoret/presentation', '/kontoret/objekt/beslut%3AKUNDSTART-20260927',
                    '/kundstart', '/forbattringar', '/forbattringar/ny', '/forbattringar/t_abc123'):
            kod, huvud, kropp = self.anrop('GET', vag, kaka=False)
            self.assertEqual((kod, kropp), (200, index), vag)
            self.assertEqual(huvud['X-Frame-Options'], 'DENY', vag)
        for vag in ('/kontoret/x', '/forbattringar/../api/tradar', '/kundstart/', '/hem', '/kontoret/objekt/'):
            self.assertEqual(self.anrop('GET', vag)[0], 404, vag)
        kod, huvud, kropp = self.anrop('GET', '/arbetsplats.js', kaka=False)
        self.assertEqual(kod, 200)
        self.assertIn('text/javascript', huvud['Content-Type'])

    def test_skalets_csp_ramar_bara_in_samma_ursprung(self):
        csp = self.anrop('GET', '/')[1]['Content-Security-Policy']
        self.assertIn("frame-src 'self'", csp)
        self.assertIn("frame-ancestors 'none'", csp)
        self.assertIn("script-src 'self'", csp)


class AquariumSammaUrsprung(ArbetsplatsMiljo):
    def test_sidan_ar_fonstrets_sida_bakom_inloggningen(self):
        kod, _, kropp = self.anrop('GET', '/kontoret/aquarium', kaka=False)
        self.assertEqual(kod, 401)
        self.assertNotIn(b'<html', kropp)
        kod, huvud, kropp = self.anrop('GET', '/kontoret/aquarium')
        self.assertEqual(kod, 200)
        self.assertEqual(kropp.decode('utf-8'), aquarium_vy.render(self.lasare.projektion,
                                                                  {'grund': 'första', 'forra_read_at': None, 'uppdrag': {}}))
        self.assertEqual(huvud.get_all('Content-Type'), ['text/html; charset=utf-8'])
        self.assertEqual(huvud.get_all('Content-Security-Policy'), ["frame-ancestors 'self'"])
        self.assertEqual(huvud.get_all('X-Frame-Options'), ['SAMEORIGIN'])
        self.assertEqual(huvud['X-Frame-Options'], 'SAMEORIGIN')
        self.assertEqual(huvud['Cache-Control'], 'no-store')

    def test_lasning_json_ger_lastid_och_fonstrets_takt_galler(self):
        self.assertEqual(self.anrop('GET', '/lasning.json', kaka=False)[0], 401)
        self.forsta_lasning()
        for _ in range(4):
            kod, d = self.json('GET', '/lasning.json')
            self.assertEqual((kod, d), (200, {'read_at': LAST}))
        self.json('GET', '/api/arbetsplats/kontoret')
        self.anrop('GET', '/kontoret/aquarium')
        self.assertEqual(self.lasare.antal, 1, 'högst en läsning varannan minut, oavsett hur många som frågar')

    def test_otillganglig_lasning_ar_okand_inte_tom(self):
        self.lasare.fel = True
        kod, huvud, kropp = self.anrop('GET', '/kontoret/aquarium')
        self.assertEqual(kod, 503)
        self.assertEqual(huvud['Retry-After'], '10')
        kod, d = self.json('GET', '/api/arbetsplats/kontoret')
        self.assertEqual((kod, d['status'], d['projektion']), (200, 'otillganglig', None))
        self.assertTrue(d['senaste_fel'])
        kod, h = self.json('GET', '/api/arbetsplats/hem')
        self.assertEqual(kod, 200)
        self.assertEqual(h['kontoret']['status'], 'otillganglig')
        self.assertNotIn('headline', h['kontoret'])
        self.assertIsInstance(h['tradar'], list)  # oberoende delar fungerar
        self.assertEqual(self.lasare.antal, 1, 'ett misslyckat försök räknas; nästa tidigast om 120 s')

    def test_projektionen_i_listan_ar_samma_visningssakra_uppgifter(self):
        self.forsta_lasning()
        kod, d = self.json('GET', '/api/arbetsplats/kontoret')
        self.assertEqual(kod, 200)
        self.assertEqual(d['projektion'], json.loads(json.dumps(self.lasare.projektion)))
        self.assertEqual(set(d), {'status', 'projektion', 'senaste_fel', 'senaste_forsok', 'takt_sekunder',
                                  'overlamningar'})

    def test_presentationen_bar_ingen_lista_i_sidan(self):
        ui = (tp.srv.UI / 'arbetsplats.js').read_text('utf-8')
        start = ui.index('  if (r.presentation) {')
        slut = ui.index('    return;\n  }', start)
        block = ui[start:slut]
        self.assertIn('scen', block)
        self.assertNotIn('kontor-lista', block)
        self.assertNotIn('api(', block)


class LangsamKalla(ArbetsplatsMiljo):
    def test_en_langsam_lasning_haller_inte_upp_hem_kundstart_eller_listan(self):
        def langsam():
            time.sleep(2.5)
            return en_projektion()
        self.S.arbetsplats._lasare = langsam
        for vag in ('/api/arbetsplats/hem', '/api/arbetsplats/kundstart', '/api/arbetsplats/kontoret'):
            start = time.time()
            kod, d = self.json('GET', vag)
            self.assertEqual(kod, 200, vag)
            self.assertLess(time.time() - start, 1.5, vag)
        self.assertEqual(d['status'], 'laser')
        self.assertIsNone(d['projektion'])
        slut = time.time() + 10
        while time.time() < slut and d['status'] != 'ok':
            time.sleep(0.2)
            d = self.json('GET', '/api/arbetsplats/kontoret')[1]
        self.assertEqual((d['status'], d['projektion']['read_at']), ('ok', LAST))

    def test_aquarium_sidan_vantar_in_en_lasning_som_hem_startat(self):
        def langsam():
            time.sleep(1.5)
            return en_projektion()
        self.S.arbetsplats._lasare = langsam
        self.assertEqual(self.json('GET', '/api/arbetsplats/hem')[1]['kontoret']['status'], 'laser')
        kod, _, kropp = self.anrop('GET', '/kontoret/aquarium')
        self.assertEqual(kod, 200)
        self.assertIn(b'<html', kropp)


class Anslutningen(ArbetsplatsMiljo):
    def test_en_nekad_skrivning_forstor_inte_nasta_begaran_pa_samma_anslutning(self):
        import http.client
        c = http.client.HTTPConnection('127.0.0.1', self.port, timeout=10)
        c.request('POST', '/api/inspel', body=b'{"text": "x"}', headers={'Host': '127.0.0.1:%d' % self.port,
                                                                      'Content-Type': 'application/json'})
        r = c.getresponse()
        r.read()
        self.assertEqual(r.status, 403)
        self.assertEqual(r.getheader('Connection'), 'close')
        c.close()
        c = http.client.HTTPConnection('127.0.0.1', self.port, timeout=10)
        for _ in range(2):  # en godkänd skrivning läser sin kropp och håller anslutningen öppen
            c.request('POST', '/api/logga-in', body=json.dumps({'nyckel': 'fel'}).encode(),
                      headers={'Host': '127.0.0.1:%d' % self.port, 'X-Partner': '1', 'Content-Type': 'application/json'})
            r = c.getresponse()
            r.read()
            self.assertEqual(r.status, 403)
            self.assertIsNone(r.getheader('Connection'))
        c.request('GET', '/api/session', headers={'Host': '127.0.0.1:%d' % self.port})
        r = c.getresponse()
        self.assertEqual((r.status, json.loads(r.read())), (200, {'inloggad': False}))


class Hem(ArbetsplatsMiljo):
    def test_hem_haller_isar_och_saknade_uppgifter_ar_inte_noll(self):
        self.forsta_lasning()
        t = self.skicka('bara spara en tanke om Kontoret')['inspel']['trad']
        self.overlamning(t)
        kod, d = self.json('GET', '/api/arbetsplats/hem')
        self.assertEqual(kod, 200)
        self.assertEqual([x['id'] for x in d['tradar']], [t])
        self.assertEqual([(o['id'], o['oppen'], o['start']['typ']) for o in d['overlamningar']],
                         [('OVL-20260929-abc123', True, 'vantar')])
        k = d['kontoret']
        self.assertEqual(k['status'], 'ok')
        self.assertEqual([x['basis'] for x in k['agarens_bord']['items']],
                         ['planens ägartur', 'planens ägartur', 'överlämningens startlogg'])
        self.assertEqual(k['verkstaden'], {'status': 'ok', 'pagar': 1, 'vilar': 1})
        self.assertEqual(d['kundstart']['provserver']['kor'], False)
        self.assertEqual(d['kundstart']['lage'], 'prov')
        self.assertIn('Kundstarts ärenden', d['sok']['utanfor'])
        self.assertTrue(all('antal' in o for o in d['sok']['omfang']))

    def test_en_okand_motor_blir_null_inte_noll(self):
        self.lasare.projektion = en_projektion(sources=sources(unavailable=('engine', 'tasks')),
                                               headline={'pagar': None, 'vantar': 0, 'behover_dig': 3, 'lugnt': False},
                                               verkstaden={'status': 'otillgänglig', 'items': [], 'parked': [],
                                                           'titles': 'otillgänglig'})
        self.forsta_lasning()
        kod, d = self.json('GET', '/api/arbetsplats/hem')
        self.assertEqual(d['kontoret']['verkstaden'], {'status': 'otillgänglig', 'pagar': None, 'vilar': None})
        self.assertIsNone(d['kontoret']['headline']['pagar'])

    def test_hem_visar_bara_halsningen(self):  # HEM-RUTOR-20260929: ägaren tog bort alla rutor på Hem
        ui = (tp.srv.UI / 'arbetsplats.js').read_text('utf-8')
        hem = ui[ui.index('// ' + '-' * 66 + ' Hem'):ui.index('// ' + '-' * 66 + ' Kontoret')]
        for borta in ('Fortsätt där du var', 'Kontoret just nu', 'Behöver dig', 'Sök i underlaget', 'Levererat och ändrat',
                      'Läs om', 'api('):
            self.assertFalse(borta in hem, 'kvar på Hem: ' + borta)  # "Behöver dig" är kvar som grupp i Kontorets lista
        for borta in ('h-fortsatt', 'h-kontoret', 'h-behover', 'h-sok', 'h-andrat', 'hemsok', 'uppdateraHemKontor',
                      'hem-rutnat', 'arbetsplats:besok', '/api/arbetsplats/hem'):
            self.assertFalse(borta in ui, 'kvar i ytan: ' + borta)
        self.assertIn("el('h1', { id: 'hem-rubrik', tabindex: '-1' }, halsning())", hem)
        self.assertIn("r.okand ?", hem)  # en okänd adress säger fortfarande att du är på Hem

    def test_forbattringars_meny_har_ny_trad_och_overlamningar(self):  # HEM-RUTOR-20260929: tre menyval bort
        index = (tp.srv.UI / 'index.html').read_text('utf-8')
        app = (tp.srv.UI / 'app.js').read_text('utf-8')
        meny = index[index.index('<nav class="sidnav"'):index.index('</nav>', index.index('<nav class="sidnav"'))]
        self.assertEqual(re.findall(r'<(?:button|form) id="(\w+)"', meny), ['nytrad', 'visaoverlamningar'])
        for borta in ('sokformular', 'sokfalt', 'visaforstaelse', 'visalage'):
            self.assertFalse(borta in index or borta in app, 'kvar: ' + borta)
        self.assertIn('async function visaKalla(', app)  # källpanelen öppnas fortfarande från notiser och källor

    def test_andringar_bar_commitens_tid_och_beslutsid(self):
        repo = self.rot / 'kontor'
        subprocess.run(['git', 'init', '-q', '-b', 'main', str(repo)], check=True)
        miljo = dict(os.environ, GIT_AUTHOR_NAME='p', GIT_AUTHOR_EMAIL='p@x', GIT_COMMITTER_NAME='p',
                     GIT_COMMITTER_EMAIL='p@x', GIT_COMMITTER_DATE='2026-09-29T10:08:35+00:00')
        subprocess.run(['git', '-C', str(repo), 'commit', '-q', '--allow-empty', '-m',
                           'Partnern: startvakt (FORBATTRINGSPARTNER-OVERLAMNING-AUTOSTART-20260929) (#124)'], check=True, env=miljo)
        subprocess.run(['git', '-C', str(repo), 'update-ref', 'refs/remotes/origin/main', 'HEAD'], check=True)
        a = self.S.arbetsplats.andringar()
        self.assertEqual([(p['repo'], ap._epok(p['tid']), p['beslut'], p['pr']) for p in a['poster']],
                         [('kontoret', ap._epok('2026-09-29T10:08:35+00:00'), 'FORBATTRINGSPARTNER-OVERLAMNING-AUTOSTART-20260929', 124)])
        self.assertEqual(a['repon'][0]['status'], 'ok')
        self.assertIsNone(a['repon'][0]['hamtad'], 'ingen FETCH_HEAD: okänd hämtning, ingen påhittad tid')


class Kundstart(ArbetsplatsMiljo):
    def test_stoppad_testserver_och_korande_utan_kakor(self):
        self.forsta_lasning()
        kod, d = self.json('GET', '/api/arbetsplats/kundstart')
        self.assertEqual((kod, d['provserver']['kor'], d['lage']), (200, False, 'prov'))
        self.assertEqual(d['agarrader']['status'], 'ok')
        self.assertEqual([r['text'][:18] for r in d['agarrader']['rader']], ['Digitala Kundstart'])
        self.assertEqual(d['digitala'], {'status': 'okand'})
        self.assertTrue(all(b['id'].startswith('KUNDSTART') for b in d['beslut']))
        port = tp.fri_port()
        atrapp = ThreadingHTTPServer(('127.0.0.1', port), KundstartAtrapp)
        threading.Thread(target=atrapp.serve_forever, daemon=True).start()
        self.addCleanup(atrapp.shutdown)
        self.S.arbetsplats.kundstart_adress = 'http://127.0.0.1:%d' % port
        (self.rot / 'kundstart-prov').mkdir()
        (self.rot / 'kundstart-prov' / 'byggd.json').write_text('{"head": "48dcecaaaaaa", "tid": "2026-09-29T08:30:00Z"}')
        KundstartAtrapp.antal, KundstartAtrapp.kakor = 0, []
        kod, d = self.json('GET', '/api/arbetsplats/kundstart')
        self.assertEqual((d['provserver']['kor'], d['provserver']['http'], d['kod']['byggd']), (True, 200, '48dceca'))
        self.assertEqual((KundstartAtrapp.antal, KundstartAtrapp.kakor), (1, [None]), 'ett GET, inga kakor')

    def test_ett_ofullstandigt_bord_ger_okant_inte_en_tom_lista(self):
        self.lasare.projektion = en_projektion(agarens_bord={'status': 'ofullständig', 'items': []})
        self.forsta_lasning()
        kod, d = self.json('GET', '/api/arbetsplats/kundstart')
        self.assertEqual(d['agarrader'], {'status': 'ofullstandig', 'rader': None})

    def test_kundstarts_beslut_lases_ur_indexet(self):
        self.S.lager.kor("insert into kalla(id, klass, titel, datum, grupp, ordning, text) values "
                           "('kontor:beslut:KUNDSTART-PROVBESLUT-20990101', 'kontor:beslut', "
                           "'KUNDSTART-PROVBESLUT-20990101 — ett provbeslut', '2099-01-01', 'kontor:beslut', 900, 'x')")
        kod, d = self.json('GET', '/api/arbetsplats/kundstart')
        self.assertEqual(d['beslut'][0], {'ref': 'beslut:KUNDSTART-PROVBESLUT-20990101', 'id': 'KUNDSTART-PROVBESLUT-20990101',
                                          'titel': 'KUNDSTART-PROVBESLUT-20990101 — ett provbeslut', 'datum': '2099-01-01'})


class ObjektOchSammanhang(ArbetsplatsMiljo):
    def beslut(self, bid='PROV-ARBETSPLATS-20990101'):
        self.S.lager.kor("insert into kalla(id, klass, titel, datum, grupp, ordning, text) values (?, 'kontor:beslut', ?, "
                           "'2026-09-27', 'kontor:beslut', 901, 'posten')", ('kontor:beslut:' + bid, bid + ' — Kundstart'))
        return 'beslut:' + bid

    def test_objekt_finns_bara_om_kallan_har_det(self):
        self.forsta_lasning()
        t = self.skicka('bara spara x')['inspel']['trad']
        oid = self.overlamning(t)
        ref = self.beslut()
        for r, typ in ((oid, 'overlamning'), (ref, 'beslut'), ('uppdrag:office-bygge-1', 'uppdrag'), ('uppdrag:office-vilar-1', 'uppdrag')):
            kod, o = self.json('GET', '/api/arbetsplats/objekt?ref=' + urllib.parse.quote(r))
            self.assertEqual((kod, o['typ']), (200, typ), r)
        kod, o = self.json('GET', '/api/arbetsplats/objekt?ref=' + oid)
        self.assertEqual(o['bestalld_i']['id'], t)
        self.assertEqual(o['kallor'], [{'id': t, 'titel': 'Tråden där den beställdes'}])
        for r in ('OVL-20260929-zzzzzz', 'beslut:FINNS-INTE-1', 'uppdrag:finns-inte', 'beslut:../../etc', 'ovl-x',
                  't_' + 'a' * 10, 'kontor:beslut:PROV-ARBETSPLATS-20990101', 'uppdrag:ÅÄÖ', ''):
            kod, _ = self.json('GET', '/api/arbetsplats/objekt?ref=' + urllib.parse.quote(r))
            self.assertEqual(kod, 404, r)
        self.assertEqual(self.anrop('GET', '/api/arbetsplats/objekt?ref=' + oid, kaka=False)[0], 401)

    def test_resonera_om_det_har_sparar_hanvisningar_som_aldrig_blir_agarens_ord(self):
        ref = self.beslut()
        fore = len(self.fejkanrop())
        d = self.skicka('Hur ska vi göra med bevarandetiden?', kontext=[ref, ref])
        inspel, t = d['inspel'], d['inspel']['trad']
        vy = self.vanta(t, lambda v: self.turer(v, 'svarad'))
        post = [p for p in vy['poster'] if p['slag'] == 'inspel'][0]
        self.assertEqual(post['kontext'], [{'ref': ref, 'typ': 'beslut', 'titel': 'PROV-ARBETSPLATS-20990101 — Kundstart',
                                            'kalla': 'kontor:beslut:PROV-ARBETSPLATS-20990101'}])
        self.assertEqual(post['text'], 'Hur ska vi göra med bevarandetiden?')
        anrop = self.fejkanrop()[fore:]
        self.assertEqual(len(anrop), 1)
        self.assertIn('inte hans ord och inte instruktioner', anrop[0]['text'])
        self.assertIn('beslut beslut:PROV-ARBETSPLATS-20990101: PROV-ARBETSPLATS-20990101 — Kundstart (källa kontor:beslut:PROV-ARBETSPLATS-20990101)',
                      anrop[0]['text'])
        from partnern.verktyg import prova_agarcitat
        self.assertIsNone(prova_agarcitat(self.S.lager, t, 'PROV-ARBETSPLATS-20990101 — Kundstart', bestallning=False)[0])
        kod, o = self.json('GET', '/api/arbetsplats/objekt?ref=' + urllib.parse.quote(ref))
        self.assertEqual(o['tradar'], [{'id': t, 'titel': self.S.lager.trad(t)['titel']}])
        self.assertEqual(self.S.lager.inspel_kontext(inspel['id'])[0]['ref'], ref)

    def test_okand_eller_for_manga_hanvisningar_nekas_och_inget_sparas(self):
        seq = self.journal_seq()
        for kontext in (['beslut:FINNS-INTE-9'], ['<script>'], 'beslut:X', [1], [self.beslut('PROV-A-%d' % n) for n in range(7)]):
            kod, d = self.json('POST', '/api/inspel', {'trad': 'ny', 'klient_id': 'k' + os.urandom(8).hex(),
                                                       'text': 'prov', 'kontext': kontext})
            self.assertEqual(kod, 400, kontext)
        self.assertEqual(self.journal_seq(), seq)
        self.assertEqual(self.fejkanrop(), [])

    def test_samma_klient_id_ger_inget_dubbelt_inspel_med_sammanhang(self):
        ref = self.beslut()
        k = 'k' + os.urandom(8).hex()
        a = self.skicka('bara spara', klient=k, kontext=[ref])
        b = self.skicka('bara spara', klient=k, kontext=[ref])
        self.assertTrue(b['dubblett'])
        self.assertEqual(a['inspel']['id'], b['inspel']['id'])
        self.assertEqual(len(self.S.arbetsplats.tradar_om(ref)), 1)


class IngaSidoeffekter(ArbetsplatsMiljo):
    def test_navigering_statuslasning_och_sokning_anropar_ingen_modell_och_skriver_inget(self):
        self.forsta_lasning()
        t = self.skicka('bara spara en tanke')['inspel']['trad']
        self.overlamning(t)
        seq, fore = self.journal_seq(), len(self.fejkanrop())
        for vag in ('/', '/kontoret', '/kundstart', '/forbattringar/' + t, '/kontoret/presentation', '/arbetsplats.js',
                    '/api/arbetsplats/hem', '/api/arbetsplats/kontoret', '/api/arbetsplats/kundstart',
                    '/api/arbetsplats/objekt?ref=OVL-20260929-abc123', '/kontoret/aquarium', '/lasning.json',
                    '/api/sok?q=Kontoret', '/api/tradar', '/api/trad/' + t):
            self.assertIn(self.anrop('GET', vag)[0], (200,), vag)
        self.assertEqual(self.journal_seq(), seq, 'läsning skriver inget i journalen')
        self.assertEqual(len(self.fejkanrop()), fore, 'läsning anropar ingen modell')
        self.assertEqual(self.S.lager.fraga('select count(*) as n from tur')[0]['n'], 0)


class ArendeAtrapp(BaseHTTPRequestHandler):
    """Kundstarts testserver: två sidor ärenden, med fält som aldrig får följa med."""
    anrop = []
    svar = 'ok'

    def do_GET(self):
        ArendeAtrapp.anrop.append((self.path, self.headers.get('Authorization'), self.headers.get('Cookie')))
        if ArendeAtrapp.svar != 'ok':
            kod = {'saknas': 404, 'nekad': 401}[ArendeAtrapp.svar]
            self.send_response(kod); self.send_header('Content-Length', '2'); self.end_headers(); self.wfile.write(b'{}')
            return
        if self.path == '/api/intern/arenden':
            d = {'schema': 'kundstart-arenden/1', 'cursor': '100', 'olasbara': 1, 'arenden': [
                {'id': 'A1', 'kund': 'Vikskär TEST', 'testdialog': True, 'skapad': '2026-09-28T10:00:00Z', 'uppdaterad': '2026-09-29T10:00:00Z',
                 'revision': 7, 'svar': 5, 'material': 1, 'andrat_efter_inlamning': False, 'fragor': ['HEMLIG KUNDTEXT'],
                 'lank_hash': 'x' * 64, 'senaste_inlamning': {'tid': '2026-09-29T09:00:00Z', 'revision': 7, 'svar': 5, 'material': 1, 'text': 'HEMLIG'}}]}
        else:
            d = {'schema': 'kundstart-arenden/1', 'cursor': None, 'arenden': [
                {'id': 'A2', 'kund': 'Riktig kund AB', 'testdialog': False, 'skapad': '2026-09-27T10:00:00Z', 'uppdaterad': '2026-09-27T11:00:00Z',
                 'revision': 2, 'svar': 1, 'material': 0, 'andrat_efter_inlamning': False, 'senaste_inlamning': None, 'kontakt': 'kund@example.invalid'}]}
        kropp = json.dumps(d).encode()
        self.send_response(200); self.send_header('Content-Length', str(len(kropp))); self.end_headers(); self.wfile.write(kropp)

    def log_message(self, *a):
        pass


class KundstartArenden(ArbetsplatsMiljo):
    NYCKEL = 'k' * 43

    def setUp(self):
        super().setUp()
        ks = self.rot / 'kundstart'
        ks.mkdir()
        (ks / '.env.local').write_text('BLOB_READ_WRITE_TOKEN="annat-hemligt"\nKUNDSTART_INTERN_NYCKEL="%s"\n' % self.NYCKEL)
        self.S.k.repon['kundstart'] = ks
        port = tp.fri_port()
        self.atrapp = ThreadingHTTPServer(('127.0.0.1', port), ArendeAtrapp)
        threading.Thread(target=self.atrapp.serve_forever, daemon=True).start()
        self.addCleanup(self.atrapp.shutdown)
        self.S.arbetsplats.kundstart_adress = 'http://127.0.0.1:%d' % port
        ArendeAtrapp.anrop, ArendeAtrapp.svar = [], 'ok'
        self.forsta_lasning()

    def test_listan_bara_godkanda_falt_nyckeln_stannar_pa_servern_och_en_hamtning_per_kvart(self):
        kod, huvud, kropp = self.anrop('GET', '/api/arbetsplats/kundstart')
        self.assertEqual((kod, json.loads(kropp)['arenden']['status']), (200, 'laser'), 'listan hämtas i bakgrunden, vyn väntar inte')
        slut = time.time() + 10
        while time.time() < slut:
            kod, huvud, kropp = self.anrop('GET', '/api/arbetsplats/kundstart')
            if json.loads(kropp)['arenden']['status'] != 'laser' and not json.loads(kropp)['arenden']['pagar']:
                break
            time.sleep(0.1)
        d = json.loads(kropp)['arenden']
        self.assertEqual((d['status'], d['komplett'], d['olasbara'], [a['id'] for a in d['arenden']]), ('ok', True, 1, ['A1', 'A2']))
        self.assertEqual(set(d['arenden'][0]), set(ap.ARENDE_FALT))
        self.assertEqual(set(d['arenden'][0]['senaste_inlamning']), set(ap.INLAMNING_FALT))
        text = kropp.decode('utf-8')
        for hemligt in (self.NYCKEL, 'annat-hemligt', 'HEMLIG', 'lank_hash', 'kund@example'):
            self.assertNotIn(hemligt, text)
        self.assertEqual([a for a in ArendeAtrapp.anrop if a[0] != '/'],
                         [('/api/intern/arenden', 'Bearer ' + self.NYCKEL, None), ('/api/intern/arenden?cursor=100', 'Bearer ' + self.NYCKEL, None)])
        self.assertTrue(all(a == ('/', None, None) for a in ArendeAtrapp.anrop if a[0] == '/'), 'statusprovet går utan nyckel')
        self.json('GET', '/api/arbetsplats/kundstart')
        self.assertEqual(len([a for a in ArendeAtrapp.anrop if a[0] != '/']), 2, 'högst en hämtning av listan per kvart')
        self.assertNotIn('arenden', self.json('GET', '/api/arbetsplats/hem')[1]['kundstart'], 'Hem hämtar aldrig listan')

    def test_utan_nyckel_utan_lista_och_nekad_ger_egen_status_aldrig_tom_lista(self):
        (self.S.k.repon['kundstart'] / '.env.local').write_text('BLOB_READ_WRITE_TOKEN="x"\n')
        self.assertEqual(self.S.arbetsplats._hamta_arenden()['status'], 'ej_ansluten')
        self.assertEqual(ArendeAtrapp.anrop, [])
        (self.S.k.repon['kundstart'] / '.env.local').write_text('KUNDSTART_INTERN_NYCKEL=%s\n' % self.NYCKEL)
        for svar, status in (('saknas', 'saknas'), ('nekad', 'fel')):
            ArendeAtrapp.svar = svar
            d = self.S.arbetsplats._hamta_arenden()
            self.assertEqual((d['status'], d['arenden']), (status, None))
        self.atrapp.shutdown()
        self.atrapp.server_close()
        ArendeAtrapp.svar = 'ok'
        self.assertEqual(self.S.arbetsplats._hamta_arenden()['status'], 'ej_ansluten')

    def test_en_omdirigering_foljs_aldrig_och_nyckeln_lamnar_aldrig_127001(self):
        ArendeAtrapp.anrop = []
        andra = []

        class Mal(BaseHTTPRequestHandler):
            def do_GET(self):
                andra.append(self.headers.get('Authorization'))
                self.send_response(200); self.send_header('Content-Length', '2'); self.end_headers(); self.wfile.write(b'{}')

            def log_message(self, *a):
                pass
        mal = ThreadingHTTPServer(('127.0.0.1', tp.fri_port()), Mal)
        threading.Thread(target=mal.serve_forever, daemon=True).start()
        self.addCleanup(mal.shutdown)

        class Omdirigerar(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(307); self.send_header('Location', 'http://localhost:%d/stold' % mal.server_address[1])
                self.send_header('Content-Length', '0'); self.end_headers()

            def log_message(self, *a):
                pass
        om = ThreadingHTTPServer(('127.0.0.1', tp.fri_port()), Omdirigerar)
        threading.Thread(target=om.serve_forever, daemon=True).start()
        self.addCleanup(om.shutdown)
        self.S.arbetsplats.kundstart_adress = 'http://127.0.0.1:%d' % om.server_address[1]
        d = self.S.arbetsplats._hamta_arenden()
        self.assertEqual((d['status'], d['arenden']), ('fel', None))
        self.assertEqual(andra, [], 'omdirigeringens mål fick ingen begäran och ingen nyckel')

    def test_fel_typer_och_storlek_rensas_bort(self):
        rad = ap._arenderad({'id': 'A', 'kund': {'hemligt': 'x'}, 'svar': 3})
        self.assertIsNone(rad)
        rad = ap._arenderad({'id': 'A', 'kund': 'K', 'svar': {'x': 'HEMLIG'}, 'material': -1, 'revision': '7', 'testdialog': 'ja',
                             'skapad': ['x'], 'senaste_inlamning': {'tid': 't', 'svar': 'HEMLIG', 'extra': 'HEMLIG'}})
        self.assertEqual(rad, {'id': 'A', 'kund': 'K', 'testdialog': False, 'skapad': None, 'uppdaterad': None, 'revision': None,
                               'svar': None, 'material': None, 'senaste_inlamning': {'tid': 't', 'revision': None, 'svar': None, 'material': None},
                               'andrat_efter_inlamning': False})


class NortropicApp(unittest.TestCase):
    """Nortropic.app: ett paket med fasta sökvägar som startar och öppnar arbetsplatsen, utan nyckel."""

    def setUp(self):
        tp.SCRATCH.mkdir(exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(prefix='app-', dir=tp.SCRATCH)
        self.addCleanup(self.tmp.cleanup)
        self.rot = Path(self.tmp.name)
        self.kontor = self.rot / 'kontor med mellanslag'
        (self.kontor / 'tools').mkdir(parents=True)
        self.logg = self.rot / 'anrop.jsonl'
        self.py = self.rot / 'fejkpython'
        import shlex
        self.py.write_text('#!/bin/sh\n'
                           'printf \'{"argv": "%s", "cwd": "%s", "data": "%s", "path": "%s"}\\n\' '
                           '"$*" "$(pwd)" "${PARTNER_DATA:-}" "$PATH" >> ' + shlex.quote(str(self.logg)) + '\nexit 0\n')
        self.py.chmod(0o755)

    def test_paketet_skriptet_och_inga_hemligheter(self):
        from partnern import macapp
        mal = self.rot / 'Applications' / 'Nortropic.app'
        ut = macapp.bygg(mal, self.kontor, str(self.py), ikon=False)
        self.assertFalse(ut['ikon'])
        import plistlib
        info = plistlib.loads((mal / 'Contents' / 'Info.plist').read_bytes())
        self.assertEqual((info['CFBundleExecutable'], info['CFBundlePackageType'], info['CFBundleIdentifier']),
                         ('Nortropic', 'APPL', 'se.nortropic.arbetsplats'))
        self.assertNotIn('CFBundleIconFile', info)
        prog = mal / 'Contents' / 'MacOS' / 'Nortropic'
        self.assertTrue(os.access(prog, os.X_OK))
        text = prog.read_text()
        self.assertNotIn('nyckel=', text)
        self.assertNotIn('secret', text)
        miljo = dict(os.environ, PARTNER_DATA='/fel/data', PATH='/usr/bin:/bin')
        r = subprocess.run([str(prog)], env=miljo, capture_output=True, timeout=30)
        self.assertEqual(r.returncode, 0, r.stderr)
        anrop = [json.loads(x) for x in self.logg.read_text().splitlines()]
        self.assertEqual([a['argv'] for a in anrop], ['-B tools/partner.py start', '-B tools/partner.py oppna'])
        self.assertTrue(all(a['cwd'] == str(self.kontor.resolve()) or a['cwd'] == str(self.kontor) for a in anrop))
        self.assertTrue(all(a['data'] == '' for a in anrop), 'provinstansens miljö följer aldrig med')
        self.assertTrue(all(a['path'].startswith('/opt/homebrew/bin:') for a in anrop))

    def test_ett_framande_paket_rors_aldrig_och_det_egna_ersatts(self):
        from partnern import macapp
        mal = self.rot / 'Nortropic.app'
        mal.mkdir()
        (mal / 'annat').write_text('ägarens egen app')
        with self.assertRaises(ValueError):
            macapp.bygg(mal, self.kontor, str(self.py), ikon=False)
        self.assertEqual((mal / 'annat').read_text(), 'ägarens egen app')
        eget = self.rot / 'eget' / 'Nortropic.app'
        macapp.bygg(eget, self.kontor, '/fel/python', ikon=False)
        macapp.bygg(eget, self.kontor, str(self.py), ikon=False)
        self.assertIn(str(self.py), (eget / 'Contents' / 'MacOS' / 'Nortropic').read_text())
        self.assertEqual([x.name for x in eget.parent.iterdir()], ['Nortropic.app'], 'inga tillfälliga rester')


if __name__ == '__main__':
    unittest.main()
