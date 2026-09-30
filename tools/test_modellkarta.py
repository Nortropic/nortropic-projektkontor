"""Flödet (MODELLKARTA-20260929): kartans val, ur sina riktiga källor, och bara det som bevisligen fungerar.

Samma uppställning som `tools/test_partner.py`: en riktig server i processen på 127.0.0.1. Claude Codes och Codex
inställningsfiler är provfiler i provkatalogen (aldrig Johnnys riktiga), Runtimes release läses genom en injicerad
läsare och mätningen är ett skrivet kvitto. Mätverktyget prövas mot falska program som svarar som Claude Code och Codex.
"""
from __future__ import annotations

import json
import os
import unittest
from pathlib import Path
from unittest import mock

import test_partner as tp

from partnern import konfig as kf
from partnern import modellkarta as mk
from partnern import modellmatning as mm

CLAUDE_NIVAER = ['low', 'medium', 'high', 'xhigh', 'max']
CODEX_NIVAER = ['low', 'medium', 'high', 'xhigh', 'max', 'ultra']
RUNTIME = {'config_sha256': 'ec6ecbd9566df6a0e894e3a91d5c3b8c45eb86ddf0c44057a5ef1151e6632dfb',
           'executors': {r: 'claude' for r in ('interactive', 'driver', 'preparation-review', 'diagnosis',
                                               'final-review', 'implementation', 'review')},
           'models_run': {'claude': 'claude-opus-5', 'codex': 'gpt-6-astra'},
           'efforts': {'claude': 'medium', 'codex': 'high'}, 'efforts_source': 'code',
           'watch': {'executor': 'codex', 'model': 'gpt-6-astra', 'effort': 'high'}, 'watch_source': 'code'}
CLAUDE_CODE = {'env': {'X': '1'}, 'permissions': {'allow': ['Read'], 'deny': []}, 'model': 'opus[1m]',
               'hooks': {'Stop': []}, 'effortLevel': 'high',
               'modelSettings': {'claude-fable-5-1': {'effortLevel': 'xhigh'}, 'claude-opus-5-5': {'effortLevel': 'xhigh'}},
               'theme': 'dark', 'tui': {'x': True}}
CODEX = ('model = "gpt-6-astra"\nmodel_reasoning_effort = "ultra"\napproval_policy = "on-request"\n\n[desktop]\nx = 1\n\n'
         '[profiles.snabb]\nmodel = "gpt-5.5"\nmodel_reasoning_effort = "low"\n\n[projects."/Users/x"]\ntrust_level = "trusted"\n')


def resultat(program, modell, nivaer, ok=True, fel=None):
    return [{'program': program, 'modell': modell, 'niva': n, 'ok': ok, 'fel': fel, 'sekunder': 1.0,
             'forsok': [{'ok': ok, 'fel': fel, 'sekunder': 1.0}]} for n in nivaer]


def matning(**utan):
    """Ett kvitto som liknar det uppmätta 2026-09-29: Runtimes äldre program kan inte köra de nyaste modellerna."""
    r = []
    for m in ('claude-opus-5-5', 'claude-fable-5-1', 'claude-sonnet-5', 'claude-opus-5', 'claude-haiku-4-5-20251001'):
        r += resultat('claude_egen', m, [n for n in CLAUDE_NIVAER if (m, n) not in utan.get('claude_egen', ())])
        r += resultat('claude_runtime', m, CLAUDE_NIVAER, ok=m != 'claude-opus-5-5',
                      fel=None if m != 'claude-opus-5-5' else 'API Error: 400 Claude Code 2.1.257 does not support this model')
    r += [{'program': 'claude_egen', 'modell': 'opus', 'niva': None, 'ok': True, 'upplost': 'claude-opus-5-5'},
          {'program': 'claude_runtime', 'modell': 'opus', 'niva': None, 'ok': True, 'upplost': 'claude-opus-5'}]
    for m in ('gpt-6.1-sol', 'gpt-6-astra', 'gpt-6-sol'):
        r += resultat('codex_egen', m, CODEX_NIVAER)
    r += resultat('codex_runtime', 'gpt-6-astra', CODEX_NIVAER) + resultat('codex_runtime', 'gpt-6-sol', CODEX_NIVAER)
    return {'schema': 'modellmatning/2', 'matt': '2026-09-29T22:05:00.000Z', 'klar': '2026-09-29T22:08:00.000Z',
            'fraga': mm.FRAGA,
            'binarer': {'claude_egen': {'version': '2.1.280 (Claude Code)'}, 'claude_runtime': {'version': '2.1.257 (Claude Code)'},
                        'codex_egen': {'version': 'codex-cli 0.159.0'}, 'codex_runtime': {'version': 'codex-cli 0.155.1'}},
            'codex_modellista': {'codex_egen': [{'modell': m, 'nivaer': CODEX_NIVAER} for m in ('gpt-6.1-sol', 'gpt-6-astra', 'gpt-6-sol')],
                                 'codex_runtime': [{'modell': m, 'nivaer': CODEX_NIVAER} for m in ('gpt-6-astra', 'gpt-6-sol')]},
            'resultat': r}


class KartaMiljo(tp.Miljo):
    def setUp(self):
        super().setUp()
        self.k.claude_installningar = self.rot / 'claude-settings.json'
        self.k.codex_installningar = self.rot / 'codex-config.toml'
        self.k.runtime_onskemal = self.rot / 'runtime-workplace-choice.json'
        self.k.runtime_status = self.rot / 'runtime-automatic-choice-status.json'
        self.claude_fore = (json.dumps(CLAUDE_CODE, ensure_ascii=False, indent=2) + '\n').encode()
        self.k.claude_installningar.write_bytes(self.claude_fore)
        self.k.codex_installningar.write_text(CODEX, 'utf-8')
        self.skriv_matning(matning())
        self.runtime_anrop = 0

        def korare():
            self.runtime_anrop += 1
            if getattr(self, 'runtime_fel', False):
                raise ValueError('releasen svarar inte')
            return RUNTIME
        self.S.runtime_val = mk.RuntimeLasning(self.k, korare=korare)
        self.logga_in()

    def skriv_matning(self, kvitto):
        (Path(self.k.data) / 'modellmatning.json').write_text(json.dumps(kvitto), 'utf-8')

    def karta(self):
        kod, d = self.json('GET', '/api/arbetsplats/karta')
        self.assertEqual(kod, 200, d)
        return d

    def valj(self, val, modell, anstrangning=None):
        return self.json('POST', '/api/arbetsplats/karta', {'val': val, 'modell': modell, 'anstrangning': anstrangning})

    def modellval_i_journalen(self):
        return [json.loads(r['data']) for r in self.S.lager.fraga("select data from handelse where typ='modellval' order by seq")]


class LasningAvValen(KartaMiljo):
    def test_varje_val_lases_ur_sin_egen_kalla(self):
        d = self.karta()
        v = d['val']
        self.assertEqual((v['partner']['modell'], v['partner']['anstrangning'], v['partner']['bevisad']),
                         ('claude-opus-5-5', 'high', True))
        cc, cx = v['sessioner']['program']['claude_code'], v['sessioner']['program']['codex']
        # "opus[1m]" löses upp med mätningens kortnamn; ansträngningen för modellen går före grundvärdet high
        self.assertEqual((cc['modell'], cc['anstrangning'], cc['varde'], cc['langt_fonster'], cc['bevisad']),
                         ('claude-opus-5-5', 'xhigh', 'opus[1m]', True, True))
        # bara den översta delen av Codex fil räknas, aldrig en profils egen modell
        self.assertEqual((cx['modell'], cx['anstrangning'], cx['bevisad']), ('gpt-6-astra', 'ultra', True))
        self.assertEqual((v['runtime']['utforare'], v['runtime']['modell'], v['runtime']['anstrangning'],
                          v['runtime']['config'], v['runtime']['valbar'], v['runtime']['bevisad']),
                         ('claude', 'claude-opus-5', 'medium', 'ec6ecbd9', True, True))
        self.assertEqual((v['bevakning']['utforare'], v['bevakning']['modell'], v['bevakning']['anstrangning']),
                         ('codex', 'gpt-6-astra', 'high'))
        self.assertEqual((v['lasare']['status'], v['lasare']['modell']), ('sessionen', None))
        self.assertEqual(d['startvakt'], {'pa': False, 'utforare': 'claude', 'modell': 'claude-opus-5',
                                          'anstrangning': 'high', 'anstrangning_ur': 'kontoret', 'bevisad': True})
        self.assertEqual(d['matning']['program']['claude_runtime'], '2.1.257 (Claude Code)')

    def test_bara_det_som_fungerade_i_programmet_som_kor_hallplatsen_erbjuds(self):
        v = self.karta()['val']
        ids = lambda lista: [m['id'] for m in lista]
        # partnern kör på Claude Code eller Codex (steg 1b): båda programmens uppmätta modeller erbjuds
        self.assertEqual(ids(v['partner']['erbjud']), ['claude-opus-5-5', 'claude-fable-5-1', 'claude-sonnet-5',
                                                       'claude-opus-5', 'claude-haiku-4-5-20251001',
                                                       'gpt-6.1-sol', 'gpt-6-astra', 'gpt-6-sol'])
        self.assertEqual(ids(v['sessioner']['program']['codex']['erbjud']), ['gpt-6.1-sol', 'gpt-6-astra', 'gpt-6-sol'])
        # läsarna går genom Runtimes äldre program: Opus 5.5 och gpt-6.1-sol fungerade inte där och erbjuds inte
        self.assertEqual(ids(v['lasare']['erbjud']), ['claude-fable-5-1', 'claude-sonnet-5', 'claude-opus-5',
                                                      'claude-haiku-4-5-20251001', 'gpt-6-astra', 'gpt-6-sol'])
        self.assertEqual({m['id']: m['nivaer'] for m in v['lasare']['erbjud']}['gpt-6-astra'], ['high'])

    def test_ett_program_utan_modell_eller_niva_ar_okant_inte_obevisat(self):
        self.k.codex_installningar.write_text('approval_policy = "never"\n[x]\n', 'utf-8')
        cc = dict(CLAUDE_CODE)
        cc.pop('effortLevel')
        cc['modelSettings'] = {}
        self.k.claude_installningar.write_text(json.dumps(cc, ensure_ascii=False, indent=2) + '\n', 'utf-8')
        p = self.karta()['val']['sessioner']['program']
        self.assertEqual((p['codex']['status'], p['codex']['bevisad']), ('ofullstandig', None))
        self.assertEqual((p['claude_code']['status'], p['claude_code']['bevisad']), ('ofullstandig', None))

    def test_en_niva_som_inte_fungerade_erbjuds_inte_och_nuvarande_varde_markeras(self):
        self.skriv_matning(matning(claude_egen={('claude-opus-5-5', 'xhigh'), ('claude-opus-5-5', 'max')}))
        v = self.karta()['val']
        opus = next(m for m in v['sessioner']['program']['claude_code']['erbjud'] if m['id'] == 'claude-opus-5-5')
        self.assertEqual(opus['nivaer'], ['low', 'medium', 'high'])
        self.assertIs(v['sessioner']['program']['claude_code']['bevisad'], False)

    def test_utan_matning_erbjuds_ingenting(self):
        (Path(self.k.data) / 'modellmatning.json').unlink()
        v = self.karta()['val']
        self.assertFalse(v['partner']['valbar'])
        self.assertFalse(v['sessioner']['valbar'])
        self.assertEqual(v['partner']['erbjud'], [])
        self.assertIn('matmodeller', v['partner']['skal'])
        kod, d = self.valj('claude_code', 'claude-sonnet-5', 'high')
        self.assertEqual(kod, 400, d)
        self.assertEqual(self.k.claude_installningar.read_bytes(), self.claude_fore)

    def test_lasarnas_varde_ar_okant_inte_obevisat_nar_runtime_inte_gar_att_lasa(self):
        self.assertEqual(self.valj('lasare', 'gpt-6-astra')[0], 200)
        self.S.runtime_val = mk.RuntimeLasning(self.k, korare=lambda: (_ for _ in ()).throw(ValueError('x')))
        la = self.karta()['val']['lasare']
        self.assertEqual((la['modell'], la['anstrangning'], la['bevisad']), ('gpt-6-astra', None, None))

    def test_en_release_som_inte_gar_att_lasa_ar_okand_aldrig_ett_varde(self):
        self.runtime_fel = True
        self.S.runtime_val = mk.RuntimeLasning(self.k, korare=lambda: (_ for _ in ()).throw(ValueError('x')))
        v = self.karta()['val']
        self.assertEqual((v['runtime']['status'], v['runtime']['modell']), ('olasbar', None))
        self.assertEqual((v['bevakning']['status'], v['bevakning']['modell']), ('olasbar', None))
        self.assertFalse(v['lasare']['valbar'])
        self.assertEqual(self.karta()['startvakt']['modell'], None)

    def test_runtimes_lasning_sparas_en_minut(self):
        self.karta()
        self.karta()
        self.assertEqual(self.runtime_anrop, 1)


class ClaudeCode(KartaMiljo):
    def test_bara_tre_varden_andras_och_allt_annat_star_kvar(self):
        kod, d = self.valj('claude_code', 'claude-sonnet-5', 'high')
        self.assertEqual(kod, 200, d)
        efter = json.loads(self.k.claude_installningar.read_text())
        vantat = json.loads(json.dumps(CLAUDE_CODE))
        vantat['model'] = 'claude-sonnet-5[1m]'          # det långa fönstret behålls
        vantat['effortLevel'] = 'high'
        vantat['modelSettings']['claude-sonnet-5'] = {'effortLevel': 'high'}
        self.assertEqual(efter, vantat)
        self.assertEqual(list(efter), list(vantat))       # samma ordning
        self.assertEqual(self.k.claude_installningar.read_text(), json.dumps(vantat, ensure_ascii=False, indent=2) + '\n')
        cc = d['val']['sessioner']['program']['claude_code']
        self.assertEqual((cc['modell'], cc['anstrangning']), ('claude-sonnet-5', 'high'))
        self.assertEqual(self.modellval_i_journalen()[-1]['val'], 'claude_code')
        self.assertEqual(self.modellval_i_journalen()[-1]['efter']['varde'], 'claude-sonnet-5[1m]')

    def test_en_lankad_fil_skrivs_i_lankens_mal(self):
        mal = self.rot / 'dotfiler' / 'settings.json'
        mal.parent.mkdir()
        mal.write_bytes(self.claude_fore)
        self.k.claude_installningar.unlink()
        self.k.claude_installningar.symlink_to(mal)
        self.assertEqual(self.valj('claude_code', 'claude-opus-5', 'low')[0], 200)
        self.assertTrue(self.k.claude_installningar.is_symlink())
        self.assertEqual(json.loads(mal.read_text())['model'], 'claude-opus-5[1m]')

    def test_en_annan_form_an_den_som_skrivs_vagras(self):
        annan = (json.dumps(CLAUDE_CODE, ensure_ascii=False, indent=4) + '\n').encode()
        self.k.claude_installningar.write_bytes(annan)
        kod, d = self.valj('claude_code', 'claude-opus-5', 'low')
        self.assertEqual(kod, 400, d)
        self.assertIn('annan form', d['fel'])
        self.assertEqual(self.k.claude_installningar.read_bytes(), annan)

    def test_filens_rattigheter_behalls(self):
        self.k.claude_installningar.chmod(0o600)
        self.assertEqual(self.valj('claude_code', 'claude-opus-5', 'low')[0], 200)
        self.assertEqual(self.k.claude_installningar.stat().st_mode & 0o777, 0o600)

    def test_haiku_far_aldrig_det_langa_fonstret(self):
        self.assertEqual(self.valj('claude_code', 'claude-haiku-4-5-20251001', 'low')[0], 200)
        self.assertEqual(json.loads(self.k.claude_installningar.read_text())['model'], 'claude-haiku-4-5-20251001')

    def test_ett_val_som_inte_fungerade_vagras_och_inget_skrivs(self):
        self.skriv_matning(matning(claude_egen={('claude-opus-5-5', 'max')}))
        kod, d = self.valj('claude_code', 'claude-opus-5-5', 'max')
        self.assertEqual(kod, 400, d)
        self.assertIn('inte fungerat', d['fel'])
        for modell, niva in (('claude-okand', 'high'), ('claude-opus-5-5', 'ultra'), ('', '')):
            self.assertEqual(self.valj('claude_code', modell, niva)[0], 400, (modell, niva))
        self.assertEqual(self.k.claude_installningar.read_bytes(), self.claude_fore)
        self.assertEqual(self.modellval_i_journalen(), [])

    def test_en_samtidig_skrivning_provas_om_och_ger_upp_utan_att_skriva(self):
        original = mk._skriv_atomart
        forsok = []

        def forst_upptagen(*a):
            forsok.append(1)
            return False if len(forsok) < 3 else original(*a)
        with mock.patch.object(mk, '_skriv_atomart', forst_upptagen):
            self.assertEqual(mk.spara_claude_code(self.k, 'claude-opus-5', 'low'), {'varde': 'claude-opus-5[1m]'})
        self.assertEqual(len(forsok), 3)
        with mock.patch.object(mk, '_skriv_atomart', lambda *a: False):
            with self.assertRaises(ValueError):
                mk.spara_claude_code(self.k, 'claude-sonnet-5', 'low')
        self.assertEqual(json.loads(self.k.claude_installningar.read_text())['model'], 'claude-opus-5[1m]')
        self.assertEqual([p.name for p in self.rot.iterdir() if p.name.startswith('.settings.json.arbetsplatsen')], [])

    def test_atomar_skrivning_andrar_inget_om_filen_hann_andras(self):
        fil = self.rot / 'f.json'
        fil.write_bytes(b'{"a": 1}\n')
        self.assertFalse(mk._skriv_atomart(fil, b'{"a": 0}\n', b'{"a": 2}\n', '.f-'))
        self.assertEqual(fil.read_bytes(), b'{"a": 1}\n')
        self.assertTrue(mk._skriv_atomart(fil, b'{"a": 1}\n', b'{"a": 2}\n', '.f-'))
        self.assertEqual(fil.read_bytes(), b'{"a": 2}\n')


class Codex(KartaMiljo):
    def test_bara_de_tva_oversta_raderna_andras(self):
        kod, d = self.valj('codex', 'gpt-6.1-sol', 'max')
        self.assertEqual(kod, 200, d)
        self.assertEqual(self.k.codex_installningar.read_text(),
                         CODEX.replace('model = "gpt-6-astra"\nmodel_reasoning_effort = "ultra"',
                                       'model = "gpt-6.1-sol"\nmodel_reasoning_effort = "max"'))
        cx = d['val']['sessioner']['program']['codex']
        self.assertEqual((cx['modell'], cx['anstrangning']), ('gpt-6.1-sol', 'max'))

    def test_saknade_nycklar_laggs_forst_och_resten_star_kvar(self):
        utan = CODEX.split('\n', 2)[2]
        self.k.codex_installningar.write_text(utan, 'utf-8')
        self.assertEqual(self.karta()['val']['sessioner']['program']['codex']['status'], 'ofullstandig')
        self.assertEqual(self.valj('codex', 'gpt-6-sol', 'low')[0], 200)
        self.assertEqual(self.k.codex_installningar.read_text(),
                         'model = "gpt-6-sol"\nmodel_reasoning_effort = "low"\n' + utan)

    def test_en_lista_over_flera_rader_overst_foljs_och_nyckeln_efter_den_hittas(self):
        # samma form som Johnnys riktiga fil (notify över fyra rader) och granskarens fall: en rad som börjar med [ inne i
        # listan är ingen tabellrubrik, och nyckeln efter listan är fortfarande överst
        text = ('model = "gpt-6-astra"\nnotify = [\n    "/Applications/X.app/Contents/MacOS/X",\n    "turn-ended",\n]\n'
                'extra = [\n  [1, 2]\n]\nmodel_reasoning_effort = "ultra"\nservice_tier = "priority"\n\n[desktop]\nx = 1\n'
                '[profiles.p]\nmodel_reasoning_effort = "low"\n')
        self.k.codex_installningar.write_text(text, 'utf-8')
        cx = self.karta()['val']['sessioner']['program']['codex']
        self.assertEqual((cx['status'], cx['modell'], cx['anstrangning']), ('ok', 'gpt-6-astra', 'ultra'))
        self.assertEqual(self.valj('codex', 'gpt-6-sol', 'low')[0], 200)
        self.assertEqual(self.k.codex_installningar.read_text(),
                         text.replace('model = "gpt-6-astra"', 'model = "gpt-6-sol"', 1)
                             .replace('model_reasoning_effort = "ultra"', 'model_reasoning_effort = "low"', 1))

    def test_flerradigt_overst_ger_okant_lage_och_ingen_skrivning(self):
        for text in ('model = "gpt-6-astra"\nextra = [\n  [1, 2]\n\nmodel_reasoning_effort = "high"\n[x]\n',
                     'model = "gpt-6-astra"\nnotes = """rad ett\n[inte en tabell]\n"""\n[x]\n',
                     "notes = 'ej stängd\nmodel = \"x\"\n[x]\n",
                     'tbl = { a = 1,\n  b = 2 }\n[x]\n'):
            self.k.codex_installningar.write_text(text, 'utf-8')
            self.assertEqual(self.karta()['val']['sessioner']['program']['codex']['status'], 'olasbar', text)
            self.assertEqual(self.valj('codex', 'gpt-6-sol', 'low')[0], 400, text)
            self.assertEqual(self.k.codex_installningar.read_text(), text)

    def test_en_lista_pa_en_rad_och_en_hakparentes_i_en_strang_godtas(self):
        text = 'model = "gpt-6-astra"\nlista = ["a", "b]"]  # [kommentar\n[x]\nmodel = "annan"\n'
        self.k.codex_installningar.write_text(text, 'utf-8')
        self.assertEqual(self.valj('codex', 'gpt-6-sol', 'low')[0], 200)
        self.assertEqual(self.k.codex_installningar.read_text(),
                         'model_reasoning_effort = "low"\nmodel = "gpt-6-sol"\nlista = ["a", "b]"]  # [kommentar\n[x]\nmodel = "annan"\n')

    def test_en_okand_form_ger_okant_lage_och_ingen_skrivning(self):
        for text in ('model = gpt-6-astra\n', "'model' = 1\n", 'model = """x"""\n'):
            self.k.codex_installningar.write_text(text, 'utf-8')
            self.assertEqual(self.karta()['val']['sessioner']['program']['codex']['status'], 'olasbar', text)
            self.assertEqual(self.valj('codex', 'gpt-6-sol', 'low')[0], 400, text)
            self.assertEqual(self.k.codex_installningar.read_text(), text)

    def test_enkla_citattecken_och_kommentar_godtas(self):
        self.k.codex_installningar.write_text("model = 'gpt-6-sol'  # min\n[x]\n", 'utf-8')
        cx = self.karta()['val']['sessioner']['program']['codex']
        self.assertEqual((cx['modell'], cx['anstrangning']), ('gpt-6-sol', None))
        self.assertEqual(self.valj('codex', 'gpt-6-astra', 'high')[0], 200)
        self.assertEqual(self.k.codex_installningar.read_text(),
                         'model_reasoning_effort = "high"\nmodel = "gpt-6-astra"\n[x]\n')

    def test_en_codexmodell_som_inte_fungerade_vagras(self):
        self.assertEqual(self.valj('codex', 'gpt-okand', 'high')[0], 400)
        self.assertEqual(self.valj('codex', 'gpt-6-astra', 'minimal')[0], 400)
        self.assertEqual(self.k.codex_installningar.read_text(), CODEX)


class PartnernOchLasarna(KartaMiljo):
    def test_samtalsytans_modellvaljare_erbjuder_bara_uppmatta_modeller(self):
        kvitto = matning()
        kvitto['resultat'] = [r for r in kvitto['resultat'] if not (r['program'] == 'claude_egen' and r['modell'] == 'claude-fable-5-1')]
        self.skriv_matning(kvitto)
        ids = [m['id'] for m in self.json('GET', '/api/installningar')[1]['modeller']]
        self.assertNotIn('claude-fable-5-1', ids)
        self.assertIn('claude-opus-5-5', ids)
        (Path(self.k.data) / 'modellmatning.json').unlink()   # utan mätning: hela listan, som förut
        self.assertEqual(len(self.json('GET', '/api/installningar')[1]['modeller']), len(kf.MODELLER))

    def test_en_matning_utan_lyckade_anrop_erbjuder_ingenting_och_samtalsytan_provar_valet(self):
        kvitto = matning()
        kvitto['resultat'] = [r for r in kvitto['resultat'] if r['program'] not in ('claude_egen', 'codex_egen')]
        self.skriv_matning(kvitto)
        self.assertEqual(self.json('GET', '/api/installningar')[1]['modeller'], [])
        kod, d = self.json('POST', '/api/installningar', {'huvud': 'claude-sonnet-5', 'anstrangning': 'low'})
        self.assertEqual(kod, 400, d)
        self.skriv_matning(matning(claude_egen={('claude-sonnet-5', 'max')}))
        self.assertEqual(self.json('POST', '/api/installningar', {'huvud': 'claude-sonnet-5', 'anstrangning': 'max'})[0], 400)
        self.assertEqual(self.json('POST', '/api/installningar', {'huvud': 'claude-sonnet-5', 'anstrangning': 'low'})[0], 200)

    def test_partnerns_val_galler_direkt_med_claude_eller_codex_om_det_fungerat(self):
        kod, d = self.valj('partner', 'claude-sonnet-5', 'low')
        self.assertEqual(kod, 200, d)
        self.assertEqual((self.S.k.modell.huvud, self.S.k.modell.anstrangning), ('claude-sonnet-5', 'low'))
        self.assertEqual(self.json('GET', '/api/installningar')[1]['huvud'], 'claude-sonnet-5')
        kod, d = self.valj('partner', 'gpt-6-astra', 'high')
        self.assertEqual(kod, 200, d)
        self.assertEqual(d['val']['partner']['utforare'], 'codex')
        self.assertEqual(self.valj('partner', 'gpt-okand', 'high')[0], 400)
        self.assertEqual(self.valj('partner', 'gpt-6-astra', 'minimal')[0], 400)

    def test_lasarna_sparas_tas_bort_och_vagras_utanfor_matningen(self):
        kod, d = self.valj('lasare', 'gpt-6-astra')
        self.assertEqual(kod, 200, d)
        la = d['val']['lasare']
        self.assertEqual((la['modell'], la['utforare'], la['anstrangning'], la['status']), ('gpt-6-astra', 'codex', 'high', 'ok'))
        val = json.loads((Path(self.k.data) / 'installningar.json').read_text())
        self.assertEqual(val['lasare'], {'modell': 'gpt-6-astra'})
        self.assertEqual(self.valj('lasare', 'claude-opus-5-5')[0], 400)   # fungerade inte i Runtimes program
        kod, d = self.valj('lasare', None)
        self.assertEqual((kod, d['val']['lasare']['status']), (200, 'sessionen'))
        self.assertNotIn('lasare', json.loads((Path(self.k.data) / 'installningar.json').read_text()))

    def test_ett_okant_val_nekas(self):
        # Runtime och bevakningen väljs sedan steg 2 (klassen RuntimeOchBevakningen); ett okänt val nekas alltid
        kod, d = self.valj('okant', 'claude-opus-5', 'medium')
        self.assertEqual(kod, 400, d)

    def test_skrivning_kraver_samtalsytans_huvud(self):
        kod, _, _ = self.anrop('POST', '/api/arbetsplats/karta', {'val': 'claude_code', 'modell': 'claude-opus-5',
                                                                  'anstrangning': 'low'}, huvud={'X-Partner': '0'})
        self.assertEqual(kod, 403)
        self.assertEqual(self.k.claude_installningar.read_bytes(), self.claude_fore)


class AdressOchFiler(KartaMiljo):
    def test_flodet_har_en_egen_adress_och_egna_filer(self):
        index = (tp.srv.UI / 'index.html').read_bytes()
        self.assertEqual(self.anrop('GET', '/flodet', kaka=False)[::2], (200, index))
        for vag, typ in (('/karta.js', 'text/javascript'), ('/karta.css', 'text/css')):
            kod, huvud, _ = self.anrop('GET', vag, kaka=False)
            self.assertEqual(kod, 200, vag)
            self.assertIn(typ, huvud['Content-Type'])
        self.assertEqual(self.anrop('GET', '/flodet/x')[0], 404)
        self.assertEqual(self.json('GET', '/api/arbetsplats/karta', kaka=False)[0], 401)
        self.assertIn(b'href="/flodet"', index)


FALSK_RELEASE = {
    'runtime/__init__.py': '',
    'runtime/release.py': "def installed():\n    return {'config_sha256': 'cd' * 32, 'development': {}}\n",
    'runtime/claude_profile.py': ("def command(workspace, allowed_paths=(), writable=True, model=None):\n"
                                  "    return ['claude', '-p', '--model', model, '--effort','medium', '--x']\n"),
    'runtime/profile.py': "MODEL = 'gpt-6-astra'\nREASONING_EFFORT = 'high'\n",
    'runtime/development_model.py': ("def executors(c):\n    return {'driver': 'claude', 'review': 'claude'}\n"
                                     "def models(c):\n    return {'claude': 'claude-opus-5', 'codex': 'gpt-6-astra'}\n"),
}


class RuntimeLasningenMotEnFalskRelease(unittest.TestCase):
    """PROBE körs som i tjänsten: releasens egen kod ur .runtime/ap10/active.json, med Runtimes egen tolk."""

    def release(self, rot, filer):
        rel = rot / '.runtime/ap10/releases/r1'
        for namn, text in filer.items():
            f = rel / 'runtime' / namn
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(text)
        (rel / 'config.json').write_text('{}')
        (rot / '.runtime/ap10/active.json').write_text(json.dumps({'config': str(rel / 'config.json'), 'sha256': 'cd' * 32}))
        tolk = rot / '.runtime/temporal-venv/bin/python'
        tolk.parent.mkdir(parents=True, exist_ok=True)
        tolk.symlink_to(tp.sys.executable)

    def las(self, filer):
        import tempfile
        with tempfile.TemporaryDirectory(prefix='falsk-runtime-') as t:
            rot = Path(t)
            self.release(rot, filer)
            k = kf.Konfig(data=rot / 'data', hemligheter=rot / 'h', repon={'runtime': rot})
            return mk.RuntimeLasning(k).las()

    def test_dagens_release_ger_anstrangningen_ur_koden(self):
        v = self.las(FALSK_RELEASE)
        self.assertEqual(v['status'], 'ok', v)
        self.assertEqual((v['utforare'], v['modeller']['claude'], v['anstrangning'], v['anstrangning_ur'], v['config']),
                         ('claude', 'claude-opus-5', {'claude': 'medium', 'codex': 'high'}, 'kod', 'cdcdcdcd'))
        self.assertEqual(v['bevakning'], {'utforare': 'codex', 'modell': 'gpt-6-astra', 'anstrangning': 'high', 'ur': 'kod'})

    def test_en_release_med_val_for_anstrangning_och_bevakning_gar_fore(self):
        filer = dict(FALSK_RELEASE)
        filer['runtime/development_model.py'] += ("def efforts(c):\n    return {'claude': 'xhigh', 'codex': 'ultra'}\n"
                                                  "def watch(c):\n    return {'executor': 'claude', 'model': 'claude-sonnet-5', 'effort': 'low'}\n")
        v = self.las(filer)
        self.assertEqual((v['anstrangning'], v['anstrangning_ur']), ({'claude': 'xhigh', 'codex': 'ultra'}, 'release'))
        self.assertEqual(v['bevakning'], {'utforare': 'claude', 'modell': 'claude-sonnet-5', 'anstrangning': 'low', 'ur': 'release'})

    def test_en_release_som_inte_gar_att_kora_ar_olasbar(self):
        filer = dict(FALSK_RELEASE)
        filer['runtime/release.py'] = "def installed():\n    raise ValueError('trasig')\n"
        self.assertEqual(self.las(filer)['status'], 'olasbar')


class RuntimeOchBevakningen(KartaMiljo):
    """Steg 2 (Runtimes D040): Runtime och bevakningen väljs här, bara bland det Runtimes egna program klarade, och valet
    skrivs som ett önskemål i Runtimes inkorg; Runtime aktiverar det själv och kartan visar Runtimes status."""

    def inkorg(self):
        return json.loads(self.k.runtime_onskemal.read_text('utf-8'))

    def status(self, lage, alder=0, **extra):
        from datetime import datetime, timedelta, timezone
        tid = (datetime.now(timezone.utc) - timedelta(seconds=alder)).isoformat()
        self.k.runtime_status.write_text(json.dumps({'schema': 'automatic-choice-status/1', 'checked_at': tid,
                                                     'state': lage, **extra}), 'utf-8')

    def test_runtime_och_bevakningen_ar_valbara_med_runtimes_egna_program(self):
        v = self.karta()['val']
        for namn in ('runtime', 'bevakning'):
            with self.subTest(val=namn):
                self.assertTrue(v[namn]['valbar'])
                self.assertEqual([m['id'] for m in v[namn]['erbjud']],
                                 ['claude-fable-5-1', 'claude-sonnet-5', 'claude-opus-5', 'claude-haiku-4-5-20251001',
                                  'gpt-6-astra', 'gpt-6-sol'])        # Opus 5.5 och gpt-6.1-sol klarade inte Runtimes program
                self.assertIsNone(v[namn]['onskat'])

    def test_ett_runtimeval_blir_ett_onskemal_och_bevakningen_ar_den_som_kor(self):
        kod, d = self.valj('runtime', 'gpt-6-sol', 'ultra')
        self.assertEqual(kod, 200, d)
        o = self.inkorg()
        self.assertEqual(set(o), {'schema', 'id', 'requested_at', 'runtime', 'watch'})
        self.assertEqual(o['schema'], 'workplace-choice/1'); self.assertRegex(o['id'], r'\Aw\d{8}T\d{6}Z-[0-9a-f]{6}\Z')
        self.assertEqual(o['runtime'], {'executor': 'codex', 'model': 'gpt-6-sol', 'effort': 'ultra'})
        self.assertEqual(o['watch'], {'executor': 'codex', 'model': 'gpt-6-astra', 'effort': 'high'})
        v = d['val']
        self.assertEqual(v['runtime']['onskat'], {'utforare': 'codex', 'modell': 'gpt-6-sol', 'anstrangning': 'ultra'})
        self.assertEqual((v['runtime']['modell'], v['runtime']['anstrangning']), ('claude-opus-5', 'medium'), 'det som kör är oförändrat')
        self.assertIsNone(v['bevakning']['onskat'])
        journal = self.modellval_i_journalen()
        self.assertEqual(journal[-1]['val'], 'runtime'); self.assertEqual(journal[-1]['efter']['runtime']['model'], 'gpt-6-sol')

    def test_ett_bevakningsval_behaller_det_vantande_runtimevalet(self):
        self.valj('runtime', 'gpt-6-sol', 'ultra'); forsta = self.inkorg()['id']
        kod, d = self.valj('bevakning', 'claude-opus-5', 'high')
        self.assertEqual(kod, 200, d)
        o = self.inkorg()
        self.assertEqual(o['runtime'], {'executor': 'codex', 'model': 'gpt-6-sol', 'effort': 'ultra'})
        self.assertEqual(o['watch'], {'executor': 'claude', 'model': 'claude-opus-5', 'effort': 'high'})
        self.assertNotEqual(o['id'], forsta, 'varje sparat val är ett nytt önskemål')
        self.assertEqual(d['val']['bevakning']['onskat'], {'utforare': 'claude', 'modell': 'claude-opus-5', 'anstrangning': 'high'})

    def test_ett_obevisat_val_nekas_och_inget_skrivs(self):
        for val, modell, niva in (('runtime', 'claude-opus-5-5', 'high'), ('bevakning', 'gpt-6.1-sol', 'high'),
                                  ('runtime', 'gpt-6-sol', 'minimal'), ('bevakning', '--flagga', 'high')):
            with self.subTest(val=val, modell=modell, niva=niva):
                kod, d = self.valj(val, modell, niva)
                self.assertEqual(kod, 400, d)
        self.assertFalse(self.k.runtime_onskemal.exists())

    def test_ett_val_som_redan_kor_visas_inte_som_onskat(self):
        kod, d = self.valj('runtime', 'claude-opus-5', 'medium')
        self.assertEqual(kod, 200, d)
        self.assertIsNone(d['val']['runtime']['onskat'])
        self.assertEqual(self.inkorg()['runtime'], {'executor': 'claude', 'model': 'claude-opus-5', 'effort': 'medium'})

    def test_utan_inkorg_kan_runtime_inte_valjas(self):
        self.k.runtime_onskemal = None
        v = self.karta()['val']
        self.assertFalse(v['runtime']['valbar']); self.assertIn('inkorg', v['runtime']['varfor_inte'])
        self.assertEqual(self.valj('runtime', 'gpt-6-sol', 'ultra')[0], 400)

    def test_en_lankad_inkorg_skrivs_aldrig(self):
        mal = self.rot / 'annan.json'; mal.write_text('{}', 'utf-8')
        self.k.runtime_onskemal.symlink_to(mal)
        self.assertEqual(self.valj('runtime', 'gpt-6-sol', 'ultra')[0], 400)
        self.assertEqual(mal.read_text('utf-8'), '{}')

    def test_aktiveringens_status_och_om_aktiveraren_gar(self):
        self.valj('runtime', 'gpt-6-sol', 'ultra')
        self.assertIsNone(self.karta()['val']['runtime']['aktivering'], 'ingen status: aktiveraren har aldrig tittat')
        self.status('waiting', reason='REFUSED: an AP10 watch run is in progress; activate later', request_id='w1')
        a = self.karta()['val']['runtime']['aktivering']
        self.assertEqual((a['lage'], a['igang'], a['onskemal']), ('waiting', True, 'w1')); self.assertIn('AP10', a['skal'])
        self.status('activated', alder=3600, activated_at='2026-09-30T03:00:00+00:00')
        a = self.karta()['val']['bevakning']['aktivering']
        self.assertEqual((a['lage'], a['igang'], a['aktiverad']), ('activated', False, '2026-09-30T03:00:00+00:00'))
        self.status('nagot-nytt')
        self.assertEqual(self.karta()['val']['runtime']['aktivering']['lage'], 'okant')

    def test_en_samtidig_skrivning_skriver_inget(self):
        with mock.patch.object(mk, '_skriv_atomart', lambda *a: False):
            kod, d = self.valj('runtime', 'gpt-6-sol', 'ultra')
        self.assertEqual(kod, 400, d); self.assertFalse(self.k.runtime_onskemal.exists())

    def test_en_trasig_eller_okand_status_ar_ingen_status(self):
        self.valj('runtime', 'gpt-6-sol', 'ultra')
        for innehall in ('inte json', json.dumps({'schema': 'annan/1', 'state': 'activated'}), json.dumps(['activated'])):
            with self.subTest(innehall=innehall):
                self.k.runtime_status.write_text(innehall, 'utf-8')
                self.assertIsNone(self.karta()['val']['runtime']['aktivering'])

    def test_kortet_bar_onskemalets_id_sa_att_en_aldre_status_kan_skiljas_ut(self):
        self.valj('runtime', 'gpt-6-sol', 'ultra')
        v = self.karta()['val']
        self.assertEqual(v['runtime']['onskemal_id'], self.inkorg()['id']); self.assertEqual(v['bevakning']['onskemal_id'], self.inkorg()['id'])

    def test_ett_varde_utanfor_runtimes_form_skrivs_aldrig(self):
        kvitto = matning()
        kvitto['resultat'] += resultat('codex_runtime', 'gpt-6-astra', ['Ultra'])      # ett kvitto med en udda nivå
        self.skriv_matning(kvitto)
        self.assertEqual(self.valj('bevakning', 'gpt-6-astra', 'Ultra')[0], 400)
        self.assertFalse(self.k.runtime_onskemal.exists())

    def test_startvakten_foljer_runtimes_anstrangning_nar_releasen_bar_valet(self):
        valt = dict(RUNTIME, efforts={'claude': 'max', 'codex': 'low'}, efforts_source='release')
        self.S.runtime_val = mk.RuntimeLasning(self.k, korare=lambda: valt)
        s = self.karta()['startvakt']
        self.assertEqual((s['anstrangning'], s['anstrangning_ur']), ('max', 'runtime'))


class ProvInstanser(unittest.TestCase):
    def test_en_prov_eller_utvecklingsinstans_ror_aldrig_de_riktiga_filerna(self):
        with mock.patch.dict(os.environ, {'PARTNER_DATA': '/tmp/prov-data', 'PARTNER_KONTOR_PRIMAR': '/tmp/kontor'}):
            k = kf.ladda()
        self.assertEqual((k.claude_installningar, k.codex_installningar),
                         (Path('/tmp/prov-data/claude-code-installningar.json'), Path('/tmp/prov-data/codex-installningar.toml')))
        self.assertEqual((k.runtime_onskemal, k.runtime_status),
                         (Path('/tmp/prov-data/runtime-workplace-choice.json'),
                          Path('/tmp/prov-data/runtime-automatic-choice-status.json')))
        with mock.patch.dict(os.environ, {'PARTNER_KONTOR_PRIMAR': '/tmp/kontor', 'HOME': '/tmp/ett-hem'}):
            os.environ.pop('PARTNER_DATA', None)
            os.environ.pop('PARTNER_PORT', None)
            k = kf.ladda()
        self.assertEqual(k.claude_installningar, Path('/tmp/ett-hem/.claude/settings.json'))
        # bara den ordinarie tjänsten skriver i Runtimes egen inkorg (D040)
        self.assertEqual(k.runtime_onskemal, Path(k.repon['runtime']) / '.runtime/ap10/workplace-choice.json')
        self.assertEqual(k.runtime_status, Path(k.repon['runtime']) / '.runtime/ap10/automatic-choice-status.json')
        self.assertIsNone(kf.Konfig(data=Path('/tmp/x'), hemligheter=Path('/tmp/y')).runtime_onskemal,
                          'en konfiguration som inte laddats har ingen inkorg alls')


FEJK_CLAUDE = r'''#!/usr/bin/env python3
import json, sys
a = sys.argv[1:]
modell = a[a.index('--model') + 1]
sys.stdin.read()
if modell == 'claude-opus-5-5':
    print(json.dumps({'type': 'result', 'subtype': 'success', 'is_error': True, 'result': 'API Error: 400 does not support this model'}))
elif modell in ('sonnet', 'haiku', 'fable'):
    print(json.dumps({'type': 'result', 'subtype': 'success', 'is_error': True, 'result': 'API Error: 400 unknown model'}))
elif modell == 'opus':
    print(json.dumps({'type': 'result', 'subtype': 'success', 'is_error': False, 'result': 'ok',
                      'modelUsage': {'claude-haiku-4-5-20251001': {}, 'claude-opus-5[1m]': {}}}))
else:
    print(json.dumps({'type': 'result', 'subtype': 'success', 'is_error': False, 'result': 'ok', 'modelUsage': {modell: {}}}))
'''
FEJK_CODEX = r'''#!/usr/bin/env python3
import json, os, sys
from pathlib import Path
a = sys.argv[1:]
modell = json.loads([x for x in a if x.startswith('model=')][0][6:])
niva = json.loads([x for x in a if x.startswith('model_reasoning_effort=')][0][23:])
sys.stdin.read()
lista = os.environ['FEJK_CODEX_LISTA'].split(',')
cache = Path(os.environ['HOME']) / '.codex/models_cache.json'
cache.parent.mkdir(parents=True, exist_ok=True)
cache.write_text(json.dumps({'client_version': os.environ['FEJK_CODEX_VERSION'], 'models': [
    {'slug': m, 'display_name': m.upper(), 'visibility': 'list', 'priority': i,
     'supported_reasoning_levels': [{'effort': 'low'}, {'effort': 'high'}]} for i, m in enumerate(lista)]}))
raknare = Path(os.environ['FEJK_RAKNARE'])
if modell == 'gpt-tillfallig' and not raknare.exists():
    raknare.write_text('1')
    print(json.dumps({'type': 'error', 'message': 'Reconnecting... 5/5 (unexpected status 403 Forbidden)'}))
    sys.exit(1)
if modell not in lista:
    print(json.dumps({'type': 'turn.failed', 'error': {'message': "The '%s' model is not supported" % modell}}))
    sys.exit(1)
print(json.dumps({'type': 'item.completed', 'item': {'type': 'agent_message', 'text': 'ok'}}))
print(json.dumps({'type': 'turn.completed', 'usage': {}}))
'''


class Matningen(unittest.TestCase):
    """Mätverktyget mot falska program: varje Codex skriver sin egen modellista, tydliga nej prövas inte om och
    ett tillfälligt fel prövas om tills det lyckas."""

    def setUp(self):
        import tempfile
        self.tmp = tempfile.TemporaryDirectory(prefix='matning-', dir=tp.SCRATCH if tp.SCRATCH.exists() else None)
        self.addCleanup(self.tmp.cleanup)
        self.rot = Path(self.tmp.name)
        self.bin = {}
        for namn, text in (('claude', FEJK_CLAUDE), ('codex-ny', FEJK_CODEX), ('codex-gammal', FEJK_CODEX)):
            p = self.rot / namn
            p.write_text(text.replace('/usr/bin/env python3', tp.sys.executable), 'utf-8')
            p.chmod(0o755)
            self.bin[namn] = str(p)

    def test_varje_program_mats_med_sin_egen_lista_och_tillfalliga_fel_provas_om(self):
        ny = self.rot / 'ny.sh'
        gammal = self.rot / 'gammal.sh'
        for fil, lista, version in ((ny, 'gpt-ny,gpt-tillfallig', '0.159.0'), (gammal, 'gpt-tillfallig', '0.155.1')):
            fil.write_text('#!/bin/sh\nFEJK_CODEX_LISTA=%s FEJK_CODEX_VERSION=%s exec %s "$@"\n' % (lista, version, self.bin['codex-ny']))
            fil.chmod(0o755)
        miljo = {'HOME': str(self.rot / 'hem'), 'FEJK_RAKNARE': str(self.rot / 'raknare')}
        with mock.patch.dict(os.environ, miljo), mock.patch.object(mm.time, 'sleep', lambda s: None), \
                mock.patch.object(mm, 'SAMTIDIGA', 1):
            kvitto = mm.mat(self.rot, '', logg=lambda s: None,
                            binarer={'claude_egen': self.bin['claude'], 'codex_egen': str(ny), 'codex_runtime': str(gammal)})
        self.assertEqual({p: [x['modell'] for x in l] for p, l in kvitto['codex_modellista'].items()},
                         {'codex_egen': ['gpt-ny', 'gpt-tillfallig'], 'codex_runtime': ['gpt-tillfallig']})
        f = mm.fungerar(self.rot)
        self.assertEqual(sorted(f['codex_egen']), ['gpt-ny', 'gpt-tillfallig'])
        self.assertEqual(f['codex_runtime'], {'gpt-tillfallig': ['low', 'high']})
        self.assertNotIn('claude-opus-5-5', f['claude_egen'])
        self.assertEqual(f['claude_egen']['claude-sonnet-5'], CLAUDE_NIVAER)
        tillfalliga = [r for r in kvitto['resultat'] if len(r['forsok']) > 1]
        self.assertEqual(len(tillfalliga), 1)
        self.assertEqual([x['ok'] for x in tillfalliga[0]['forsok']], [False, True])
        tydliga = [r for r in kvitto['resultat'] if r['modell'] == 'claude-opus-5-5']
        self.assertTrue(all(len(r['forsok']) == 1 and not r['ok'] for r in tydliga))   # ett tydligt nej prövas inte om
        self.assertEqual(mm.kortnamn(self.rot), {'opus': 'claude-opus-5'})
        self.assertEqual(json.loads((self.rot / 'modellmatning.json').read_text())['schema'], 'modellmatning/2')
        self.assertFalse((self.rot / '.modellmatning.json.tmp').exists())   # ingen kvarlämnad tillfällig fil
        self.assertEqual(oct((self.rot / 'modellmatning.json').stat().st_mode & 0o777), oct(0o600))

    def test_ett_forsok_skriver_inget_kvitto(self):
        with mock.patch.dict(os.environ, {'HOME': str(self.rot / 'hem')}):
            mm.mat(self.rot, '', logg=lambda s: None, forsok=True, binarer={'claude_egen': self.bin['claude']})
        self.assertFalse((self.rot / 'modellmatning.json').exists())


if __name__ == '__main__':
    unittest.main()
