"""Kontorets granskning genom Runtimes läsarprofil med läsarnas val (LASARNAS-VAL-20260930).

Runtime är en låtsas-release i provkatalogen: active.json med rätt sha256, en egen kopia av läsarprofilen som bokför
anropet och gör det provet ber om, och en python i releasens venv-plats. Läsarnas val står i provets egen datakatalog,
aldrig i den ordinarie tjänstens.
"""
from __future__ import annotations

import contextlib
import hashlib
import io
import json
import os
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
SCRATCH = REPO / '.scratch'
sys.path.insert(0, str(REPO / 'tools'))

import granska  # noqa: E402

FEJK_KRITIK = r'''"""Låtsas-Runtimes läsarprofil: bokför anropet och gör det beteende.json säger."""
import argparse, hashlib, json, os, signal, sys, time
from pathlib import Path
ROT = Path(os.environ['NR_HOST_ROOT'])
p = argparse.ArgumentParser()
for flagga in ('--underlag', '--fraga', '--schema', '--utforare', '--modell', '--etikett', '--tid'):
    p.add_argument(flagga, required=True)
a = p.parse_args()
with (ROT / 'anrop.jsonl').open('a') as f:
    f.write(json.dumps({'argv': sys.argv[1:], 'cwd': os.getcwd(), 'miljo': sorted(os.environ),
                        'schema': json.loads(Path(a.schema).read_text())}) + '\n')
utfall = json.loads((ROT / 'beteende.json').read_text())['utfall'] if (ROT / 'beteende.json').exists() else 'svar_giltigt'
if utfall == 'vagrad':
    print(json.dumps({'outcome': 'vagrad', 'reason': 'The manifest is {"filer": [...]} with 1-200 files'}))
    sys.exit(2)
if utfall == 'sov':
    def stopp(n, f):
        (ROT / 'fick-sigterm').write_text(str(n))
        print(json.dumps({'outcome': 'avbruten', 'reason': 'signal %d' % n}))
        sys.exit(3)
    signal.signal(signal.SIGTERM, stopp)
    (ROT / 'startad').write_text('1')
    time.sleep(60)
    sys.exit(9)
bas = ROT / '.runtime/profiler/kritik'
bas.mkdir(parents=True, exist_ok=True)
run = bas / ('%03d-%s' % (len(list(bas.iterdir())), a.etikett))
(run / 'arbetsyta').mkdir(parents=True)
(run / 'arbetsyta/FILES.md').write_text('# Filer\n')
if utfall == 'svar_ogiltigt':
    (run / 'svar-ra.txt').write_text('inte json')
else:
    (run / 'svar.json').write_text(json.dumps({'verdict': 'approved', 'blocking_findings': [], 'summary': 'ok',
                                               'residual_notes': ['en anteckning']}))
outputs = {str(q.relative_to(run)): {'sha256': hashlib.sha256(q.read_bytes()).hexdigest(), 'bytes': q.stat().st_size}
           for q in sorted(run.rglob('*')) if q.is_file()}
kvitto = {'profile': 'kritik', 'active_release': True, 'parameters': {'executor': a.utforare, 'model': a.modell},
          'underlag': [{'place': 'kandidat/x.py'}, {'place': 'kandidat/y.py'}], 'session': {'reported_model': a.modell},
          'outcome': 'svar_ogiltigt' if utfall == 'svar_ogiltigt' else 'svar_giltigt', 'outputs': outputs}
data = (json.dumps(kvitto, sort_keys=True) + '\n').encode()
(run / 'KVITTO.json').write_bytes(data)
(run / 'KVITTO.sha256').write_text(('0' * 64 if utfall == 'fel_kvittohash' else hashlib.sha256(data).hexdigest()) + '  KVITTO.json\n')
if utfall == 'andrat_svar':
    (run / 'svar.json').write_text(json.dumps({'verdict': 'approved', 'blocking_findings': [], 'summary': 'annat',
                                               'residual_notes': []}))
print(json.dumps({'run': str(run), 'outcome': kvitto['outcome'], 'images_complete': True}))
sys.exit(0 if kvitto['outcome'] == 'svar_giltigt' else 1)
'''


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


class Granskning(unittest.TestCase):
    def setUp(self):
        SCRATCH.mkdir(exist_ok=True)
        tmp = tempfile.TemporaryDirectory(prefix='granska-', dir=SCRATCH)
        self.addCleanup(tmp.cleanup)
        self.rot = Path(tmp.name).resolve()
        self.host = self.rot / 'runtime'
        rel = self.host / '.runtime/ap10/releases/r1'
        (rel / 'runtime/runtime').mkdir(parents=True)
        (rel / 'runtime/runtime/__init__.py').write_text('')
        (rel / 'runtime/runtime/web_critique.py').write_text(FEJK_KRITIK)
        self.config = rel / 'config.json'
        self.config.write_text('{"release": "r1"}\n')
        (self.host / '.runtime/ap10/active.json').write_text(json.dumps({'config': str(self.config), 'sha256': sha(self.config)}))
        venv = self.host / '.runtime/temporal-venv/bin'
        venv.mkdir(parents=True)
        (venv / 'python').write_text("#!/bin/sh\nexec '%s' \"$@\"\n" % sys.executable)
        (venv / 'python').chmod(0o755)
        self.data = self.rot / 'data'
        self.data.mkdir()
        (self.rot / 'kontor').mkdir()
        self.katalog = self.rot / 'Kontor R1 (steg 3)'
        self.katalog.mkdir()
        kalla = self.rot / 'x.py'
        kalla.write_text('print(1)\n')
        (self.katalog / 'underlag.json').write_text(json.dumps({'filer': [{'kalla': str(kalla), 'plats': 'kandidat/x.py',
                                                                            'vad': 'kandidatens fil'}]}))
        (self.katalog / 'fraga.md').write_text('Granska kandidaten.\n')
        self.env = {'PARTNER_DATA': str(self.data), 'PARTNER_KONTOR_PRIMAR': str(self.rot / 'kontor'),
                    'NR_HOST_ROOT': str(self.host), 'HEMLIG_NYCKEL': 'får aldrig följa med'}

    def lasare(self, modell):
        (self.data / 'installningar.json').write_text(json.dumps({'modell': {'huvud': 'claude-opus-5-5'},
                                                                  **({'lasare': {'modell': modell}} if modell else {})}))

    def beteende(self, utfall):
        (self.host / 'beteende.json').write_text(json.dumps({'utfall': utfall}))

    def kor(self, *argv):
        ut, fel = io.StringIO(), io.StringIO()
        with mock.patch.dict(os.environ, self.env), contextlib.redirect_stdout(ut), contextlib.redirect_stderr(fel):
            kod = granska.main([str(self.katalog), *argv])
        return kod, ut.getvalue() + fel.getvalue()

    def anrop(self):
        fil = self.host / 'anrop.jsonl'
        return [json.loads(r) for r in fil.read_text().splitlines()] if fil.exists() else []

    def utfallet(self):
        return json.loads((self.katalog / 'review.json').read_text())

    def test_lasarnas_val_avgor_modell_och_utforare(self):
        for modell, utforare in (('gpt-6-astra', 'codex'), ('claude-opus-5', 'claude')):
            with self.subTest(modell=modell):
                (self.katalog / 'review.json').unlink(missing_ok=True)
                self.lasare(modell)
                kod, text = self.kor()
                self.assertEqual(kod, 0, text)
                argv = self.anrop()[-1]['argv']
                self.assertEqual(argv[argv.index('--utforare') + 1], utforare)
                self.assertEqual(argv[argv.index('--modell') + 1], modell)
                u = self.utfallet()
                self.assertEqual((u['model'], u['executor'], u['model_from']), (modell, utforare, 'readers'))
                self.assertEqual(u['answer']['verdict'], 'approved')
                self.assertEqual(u['reported_model'], modell)
                run = Path(u['run'])
                self.assertEqual(u['receipt_sha256'], sha(run / 'KVITTO.json'))
                self.assertEqual((u['workspace'], u['files'], u['active_release']), (str(run / 'arbetsyta'), 2, True))
                self.assertIn('Dom: approved', text)

    def test_profilen_kors_ur_den_aktiva_releasen_med_ren_miljo_och_granskningens_schema(self):
        self.lasare('gpt-6-astra')
        self.assertEqual(self.kor()[0], 0)
        a = self.anrop()[-1]
        self.assertEqual(Path(a['cwd']).resolve(), (self.config.parent / 'runtime').resolve())
        self.assertNotIn('HEMLIG_NYCKEL', a['miljo']); self.assertNotIn('PARTNER_DATA', a['miljo'])
        self.assertIn('NR_HOST_ROOT', a['miljo'])
        self.assertEqual(a['schema'], granska.SCHEMA)
        argv = a['argv']
        self.assertEqual(argv[argv.index('--etikett') + 1], 'granskning-kontor-r1-steg-3')
        self.assertEqual(argv[argv.index('--tid') + 1], '2700')

        def sluten(nod):   # Runtimes dialekt: varje objekt kräver alla sina egenskaper och förbjuder andra
            if nod['type'] == 'object':
                self.assertIs(nod['additionalProperties'], False)
                self.assertEqual(sorted(nod['required']), sorted(nod['properties']))
                for barn in nod['properties'].values():
                    sluten(barn)
            if nod['type'] == 'array':
                sluten(nod['items'])
        sluten(granska.SCHEMA)

    def test_en_annan_modell_an_lasarnas_val_nekas_och_ingen_lasare_startar(self):
        self.lasare('gpt-6-astra')
        kod, text = self.kor('--modell', 'claude-sonnet-5')
        self.assertEqual(kod, 2); self.assertIn('Läsarnas val i Flödet är gpt-6-astra', text)
        self.assertEqual(self.anrop(), []); self.assertFalse((self.katalog / 'review.json').exists())
        kod, text = self.kor('--modell', 'gpt-6-astra')              # samma modell som valet går bra
        self.assertEqual(kod, 0, text)
        self.assertEqual(self.utfallet()['model_from'], 'readers')

    def test_utan_lasarval_valjer_sessionen_med_modell(self):
        self.lasare(None)
        kod, text = self.kor()
        self.assertEqual(kod, 2); self.assertIn('ange --modell', text); self.assertEqual(self.anrop(), [])
        kod, text = self.kor('--modell', 'claude-sonnet-5')
        self.assertEqual(kod, 0, text)
        u = self.utfallet()
        self.assertEqual((u['model'], u['executor'], u['model_from']), ('claude-sonnet-5', 'claude', 'argument'))

    def test_ett_felstavat_claude_namn_nekas_i_stallet_for_att_koras_som_codex(self):
        self.lasare(None)
        kod, text = self.kor('--modell', 'claude-opus-4')
        self.assertEqual(kod, 2); self.assertIn('Okänd Claude-modell', text); self.assertEqual(self.anrop(), [])

    def test_en_tid_utanfor_runtimes_grans_nekas_fore_start(self):
        self.lasare('gpt-6-astra')
        for tid in ('59', '2701'):
            with self.subTest(tid=tid):
                kod, text = self.kor('--tid', tid)
                self.assertEqual(kod, 2); self.assertIn('--tid', text)
        self.assertEqual(self.anrop(), []); self.assertFalse((self.katalog / 'review.json').exists())

    def test_ett_lasarval_som_inte_gar_att_lasa_nekas(self):
        for innehall in ('{', json.dumps({'lasare': {'modell': 5}})):
            with self.subTest(innehall=innehall):
                (self.data / 'installningar.json').write_text(innehall)
                kod, text = self.kor('--modell', 'claude-sonnet-5')
                self.assertEqual(kod, 2); self.assertIn('okänt', text)
        self.assertEqual(self.anrop(), [])

    def test_ett_tidigare_utfall_skrivs_aldrig_over(self):
        self.lasare('gpt-6-astra')
        (self.katalog / 'review.json').write_text('{"tidigare": true}')
        kod, text = self.kor()
        self.assertEqual(kod, 2); self.assertIn('finns redan', text)
        self.assertEqual(self.utfallet(), {'tidigare': True}); self.assertEqual(self.anrop(), [])

    def test_ett_ogiltigt_svar_ger_inget_svar(self):
        self.lasare('gpt-6-astra'); self.beteende('svar_ogiltigt')
        kod, text = self.kor()
        self.assertEqual(kod, 1, text)
        u = self.utfallet()
        self.assertIsNone(u['answer']); self.assertEqual((u['outcome'], u['receipt_outcome']), ('svar_ogiltigt', 'svar_ogiltigt'))

    def test_svaret_godtas_bara_med_ett_kvitto_som_stammer(self):
        for utfall, problem in (('fel_kvittohash', 'kvitto stämmer inte'), ('andrat_svar', 'svar.json stämmer inte')):
            with self.subTest(utfall=utfall):
                (self.katalog / 'review.json').unlink(missing_ok=True)
                self.lasare('gpt-6-astra'); self.beteende(utfall)
                kod, text = self.kor()
                self.assertEqual(kod, 1, text)
                u = self.utfallet()
                self.assertIsNone(u['answer']); self.assertIn(problem, u['problem'])

    def test_nekar_runtime_fore_korningen_kan_katalogen_anvandas_igen(self):
        self.lasare('gpt-6-astra'); self.beteende('vagrad')
        kod, text = self.kor()
        self.assertEqual(kod, 2); self.assertIn('Runtimes läsarprofil nekade', text)
        self.assertFalse((self.katalog / 'review.json').exists())
        self.beteende('svar_giltigt')
        self.assertEqual(self.kor()[0], 0)

    def test_en_aktiv_release_med_annan_sha256_nekas(self):
        self.lasare('gpt-6-astra')
        self.config.write_text('{"release": "ändrad"}\n')
        kod, text = self.kor()
        self.assertEqual(kod, 2); self.assertIn('annan sha256', text); self.assertEqual(self.anrop(), [])

    def test_ett_avbrott_skickas_vidare_och_utfallet_bokfors(self):
        self.lasare('gpt-6-astra'); self.beteende('sov')
        env = {n: v for n, v in os.environ.items() if n in ('PATH', 'HOME', 'USER', 'TMPDIR')}
        env.update(self.env)
        proc = subprocess.Popen([sys.executable, '-B', str(REPO / 'tools/granska.py'), str(self.katalog)], env=env,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.addCleanup(lambda: proc.poll() is None and proc.kill())
        slut = time.monotonic() + 30
        while not (self.host / 'startad').exists() and time.monotonic() < slut:
            time.sleep(0.05)
        self.assertTrue((self.host / 'startad').exists(), 'läsarprofilen startade aldrig')
        proc.send_signal(signal.SIGINT)
        ut, fel = proc.communicate(timeout=30)
        self.assertEqual(proc.returncode, 3, ut + fel)
        self.assertEqual((self.host / 'fick-sigterm').read_text(), str(int(signal.SIGTERM)))
        u = self.utfallet()
        self.assertEqual((u['interrupted'], u['outcome'], u['answer']), (True, 'avbruten', None))

    def test_etiketten_har_runtimes_form(self):
        self.assertEqual(granska.etikett(Path('/x/Kontor R1 (steg 3)')), 'granskning-kontor-r1-steg-3')
        lang = granska.etikett(Path('/x/' + 'a-' * 40))
        self.assertLessEqual(len(lang), 40); self.assertFalse(lang.endswith('-'))


if __name__ == '__main__':
    unittest.main()
