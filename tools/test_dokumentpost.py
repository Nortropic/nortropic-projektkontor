"""Prov för tools/dokumentpost.py (DOKUMENTVAG-20261001): regeln för en ren dokumentändring, granskningens underlag och
publiceringens tidiga vägran, på syntetiska repon med ett eget lokalt origin. Ingen modell, inget nät, ingen utfärdare."""
import ast
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import aquarium  # noqa: E402
import dokumentpost as dp  # noqa: E402

PLAN = """# Plan

Text om ÄGARENS TUR i löptext.

ÄGARENS TUR
- [beslut] Första beslutet (POST-A) — sedan 2026-09-01
- [operatörshandling] En handling (POST-B) — sedan 2026-09-02

Efter blocket.
"""
BESLUT = """# Beslut

## POST-A — första

Text.

## POST-B — andra

Text med 3 tal.
"""


def run(cwd, *args):
    return subprocess.run(['git', *args], cwd=cwd, check=True, capture_output=True, text=True,
                          env={**os.environ, 'GIT_CONFIG_GLOBAL': '/dev/null', 'GIT_CONFIG_NOSYSTEM': '1',
                               'GIT_AUTHOR_NAME': 'Prov', 'GIT_AUTHOR_EMAIL': 'prov@invalid',
                               'GIT_COMMITTER_NAME': 'Prov', 'GIT_COMMITTER_EMAIL': 'prov@invalid'}).stdout.strip()


class Rig(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='dokumentpost-')
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name).resolve()
        self.origin, self.repo = root / 'origin.git', root / 'repo'
        run(root, 'init', '-q', '--bare', '-b', 'main', str(self.origin))
        run(root, 'init', '-q', '-b', 'main', str(self.repo))
        for rel, text in (('docs/plan.md', PLAN), ('docs/decisions.md', BESLUT), ('docs/annat.md', 'annat\n'),
                          ('tools/x.py', 'x = 1\n'), ('AGENTS.md', 'regler\n')):
            (self.repo / rel).parent.mkdir(parents=True, exist_ok=True)
            (self.repo / rel).write_text(text)
        run(self.repo, 'add', '-A'); run(self.repo, 'commit', '-qm', 'bas')
        run(self.repo, 'remote', 'add', 'origin', str(self.origin)); run(self.repo, 'push', '-q', 'origin', 'main')
        self.bas = run(self.repo, 'rev-parse', 'HEAD')

    def commit(self, **filer):
        for rel, text in filer.items():
            rel = rel.replace('__', '/')
            path = self.repo / rel
            if text is None:
                run(self.repo, 'rm', '-q', rel)
                continue
            path.parent.mkdir(parents=True, exist_ok=True)
            if isinstance(text, bytes):
                path.write_bytes(text)
            else:
                path.write_text(text)
            run(self.repo, 'add', rel)
        run(self.repo, 'commit', '-qm', 'kandidat')
        return run(self.repo, 'rev-parse', 'HEAD')

    def nekar(self, ref='HEAD', bas=None, text=''):
        with self.assertRaises(dp.Nekad) as fel:
            dp.regel(self.repo, ref, bas=bas or self.bas)
        self.assertIn(text, str(fel.exception))


class Regeln(Rig):
    def test_en_ny_post_och_en_markering_godtas_med_poster_och_tal(self):
        ny = BESLUT.replace('Text.\n\n## POST-B', 'Text.\n\n**Delvis ersatt av:** POST-C, i fråga om x. Övrigt gäller.\n\n## POST-B')
        ny += '\n## POST-C — tredje\n\nMätt 140 av 140 kl. 05:04Z.\n'
        self.commit(**{'docs__decisions.md': ny, 'docs__ny.md': 'ny fil\n'})
        r = dp.regel(self.repo, 'HEAD', bas=self.bas)
        self.assertEqual(sorted(r['filer']), ['docs/decisions.md', 'docs/ny.md'])
        self.assertEqual(r['nya_poster'], ['POST-C'])
        self.assertEqual(r['agarens_tur_rader'], 2)
        self.assertIn('140', r['tal_i_tillagda_rader']); self.assertIn('05:04', r['tal_i_tillagda_rader'])

    def test_en_ny_rad_i_agarens_tur_godtas(self):
        self.commit(**{'docs__plan.md': PLAN.replace('— sedan 2026-09-02\n', '— sedan 2026-09-02\n- [beslut] Ny (POST-C) — sedan 2026-10-01\n')})
        self.assertEqual(dp.regel(self.repo, 'HEAD', bas=self.bas)['agarens_tur_rader'], 3)

    def test_kod_agents_och_allt_utanfor_docs_nekas(self):
        for rel in ('tools/x.py', 'AGENTS.md', 'README.md', 'docs/x.txt', 'docs/plan.markdown'):
            with self.subTest(fil=rel):
                run(self.repo, 'reset', '-q', '--hard', self.bas)
                self.commit(**{rel.replace('/', '__'): 'ändrat\n'})
                self.nekar(text='den vanliga vägen')

    def test_borttagning_och_namnbyte_nekas(self):
        self.commit(**{'docs__annat.md': None})
        self.nekar(text='status D')
        run(self.repo, 'reset', '-q', '--hard', self.bas)
        run(self.repo, 'mv', 'docs/annat.md', 'docs/annat2.md'); run(self.repo, 'commit', '-qm', 'namnbyte')
        self.nekar(text='status D')

    def test_beslutsloggen_far_bara_vaxa(self):
        self.commit(**{'docs__decisions.md': BESLUT.replace('Text med 3 tal.', 'Text med 4 tal.')})
        self.nekar(text='får bara växa')

    def test_en_borttagen_avdelare_som_liknar_ett_filhuvud_nekas(self):
        self.commit(**{'docs__decisions.md': BESLUT.replace('Text.\n', 'Text.\n\n---\n')})
        bas = run(self.repo, 'rev-parse', 'HEAD')
        self.commit(**{'docs__decisions.md': BESLUT.replace('Text.\n', 'Text.\n\n') + '\n## POST-C — tredje\n'})
        self.nekar(bas=bas, text='får bara växa: 1 rader')

    def test_en_tillagd_rad_som_liknar_ett_filhuvud_raknas(self):
        self.commit(**{'docs__decisions.md': BESLUT + '\n## POST-C — tredje\n\n++ 17 tal\n'})
        self.assertIn('17', dp.regel(self.repo, 'HEAD', bas=self.bas)['tal_i_tillagda_rader'])

    def test_prosa_som_bryter_agarens_tur_eller_en_rad_utanfor_blocket_nekas(self):
        bruten = PLAN.replace('- [operatörshandling] En handling', 'En mening mitt i blocket.\n- [operatörshandling] En handling')
        self.commit(**{'docs__plan.md': bruten})
        self.nekar(text='ÄGARENS TUR')
        run(self.repo, 'reset', '-q', '--hard', self.bas)
        self.commit(**{'docs__plan.md': PLAN + '\n- [beslut] En rad långt efter blocket\n'})
        self.nekar(text='ÄGARENS TUR')

    def test_lankar_korbara_filer_och_annat_an_utf8_nekas(self):
        os.symlink('plan.md', self.repo / 'docs/lank.md'); run(self.repo, 'add', 'docs/lank.md'); run(self.repo, 'commit', '-qm', 'l')
        self.nekar(text='ingen vanlig fil')
        run(self.repo, 'reset', '-q', '--hard', self.bas)
        (self.repo / 'docs/kor.md').write_text('x\n'); os.chmod(self.repo / 'docs/kor.md', 0o755)
        run(self.repo, 'add', 'docs/kor.md'); run(self.repo, 'commit', '-qm', 'k')
        self.nekar(text='ingen vanlig fil')
        run(self.repo, 'reset', '-q', '--hard', self.bas)
        self.commit(**{'docs__latin.md': 'r\xe4ksm\xf6rg\xe5s\n'.encode('latin-1')})
        self.nekar(text='inte UTF-8')

    def test_kandidaten_ska_vara_en_commit_direkt_pa_main(self):
        self.commit(**{'docs__a.md': 'a\n'}); self.commit(**{'docs__b.md': 'b\n'})
        self.nekar(text='inte direkt på origin/main')
        self.nekar(ref=self.bas, bas=self.bas, text='exakt en förälder')

    def test_proben_och_forseglingen_har_samma_dokumentmonster(self):
        for fil in ('dokumentpost_prov.py', 'dokumentpost_utfardare.py'):
            with self.subTest(fil=fil):
                trad = ast.parse((HERE / fil).read_text(encoding='utf-8'))
                [varde] = [n.value.args[0].value for n in trad.body if isinstance(n, ast.Assign)
                           and [getattr(m, 'id', None) for m in n.targets] == ['DOKUMENT']]
                self.assertEqual(varde, dp.DOKUMENT.pattern)

    def test_samma_grammatik_som_aquarium_pa_kontorets_plan(self):
        plan = (HERE.parent / 'docs/plan.md').read_text(encoding='utf-8')
        self.assertEqual(dp.agarens_tur(plan), aquarium.parse_owner_turn(plan, raw=True))


class Underlaget(Rig):
    def test_beslutsloggen_bara_som_patch_och_bindningen_finns(self):
        self.commit(**{'docs__decisions.md': BESLUT + '\n## POST-C — tredje\n\nText.\n', 'docs__plan.md': PLAN + '\nMer.\n'})
        r = dp.regel(self.repo, 'HEAD', bas=self.bas)
        runda = Path(self.tmp.name).resolve() / 'r1'; runda.mkdir()
        kalla = Path(self.tmp.name).resolve() / 'agarord.md'; kalla.write_text('ord\n')
        underlag = dp.bygg_underlag(self.repo, r, runda, kalla, [])
        platser = [f['plats'] for f in underlag['filer']]
        self.assertIn('kandidat/FULL.patch', platser); self.assertIn('kandidat/docs/plan.md', platser)
        self.assertNotIn('kandidat/docs/decisions.md', platser)
        bindning = json.loads((runda / 'filer/kandidat/files-sha256.json').read_text())
        self.assertEqual(bindning['files_sha256'], r['filer'])
        self.assertTrue((runda / 'fraga.md').read_text().startswith('Du är den separata granskaren'))

    def test_en_fil_over_lasarens_grans_nekas(self):
        self.commit(**{'docs__stor.md': 'x' * (dp.LASARENS_GRANS + 1)})
        r = dp.regel(self.repo, 'HEAD', bas=self.bas)
        runda = Path(self.tmp.name).resolve() / 'r1'; runda.mkdir()
        kalla = Path(self.tmp.name).resolve() / 'agarord.md'; kalla.write_text('ord\n')
        with self.assertRaisesRegex(dp.Nekad, 'läsarens gräns'):
            dp.bygg_underlag(self.repo, r, runda, kalla, [])


class Publiceringen(Rig):
    def setUp(self):
        super().setUp()
        self.kandidat = self.commit(**{'docs__decisions.md': BESLUT + '\n## POST-C — tredje\n\nText.\n'})
        self.tillstand = Path(self.tmp.name) / 'tillstand'
        patcher = mock.patch.multiple(dp, KONTOR=self.repo, TILLSTAND=self.tillstand)
        patcher.start(); self.addCleanup(patcher.stop)

    def runda(self, svar, filer=None):
        runda = self.tillstand / 'p1/granskning/r1'; runda.mkdir(parents=True)
        r = dp.regel(self.repo, self.kandidat, bas=self.bas)
        (runda / 'regel.json').write_text(json.dumps({**r, 'filer': filer or r['filer'], 'kalla': '/x', 'bevis': []}))
        (runda / 'review.json').write_text(json.dumps({'answer': svar}))

    def test_utan_granskning_vagras_publiceringen(self):
        with self.assertRaisesRegex(dp.Nekad, 'kör granska först'):
            dp.publicera('p1', None, True)

    def test_en_underkand_eller_blockerande_granskning_vagras(self):
        for svar in ({'verdict': 'rejected', 'blocking_findings': []},
                     {'verdict': 'approved', 'blocking_findings': ['fel tal']}):
            with self.subTest(svar=svar):
                if (self.tillstand / 'p1').exists():
                    import shutil; shutil.rmtree(self.tillstand / 'p1')
                self.runda(svar)
                with self.assertRaisesRegex(dp.Nekad, 'inte godkänd'):
                    dp.publicera('p1', None, True)

    def test_andra_byte_an_de_granskade_vagras(self):
        self.runda({'verdict': 'approved', 'blocking_findings': []}, filer={'docs/decisions.md': '0' * 64})
        with self.assertRaisesRegex(dp.Nekad, 'andra byte än de granskade'):
            dp.publicera('p1', None, True)

    def test_main_som_flyttat_vagras_med_anvisning(self):
        self.runda({'verdict': 'approved', 'blocking_findings': []})
        annan = Path(self.tmp.name) / 'annan'
        run(Path(self.tmp.name), 'clone', '-q', str(self.origin), str(annan))
        (annan / 'docs/annat.md').write_text('flyttat\n'); run(annan, 'commit', '-qam', 'm'); run(annan, 'push', '-q', 'origin', 'main')
        with self.assertRaisesRegex(dp.Nekad, 'publicera p1 --ref'):
            dp.publicera('p1', None, True)


class Proben(unittest.TestCase):
    def test_proben_lases_som_data_och_ger_samma_tur_som_aquarium(self):
        with tempfile.TemporaryDirectory() as t:
            kalla = Path(t) / 'source'
            (kalla / 'docs').mkdir(parents=True)
            (kalla / 'docs/plan.md').write_text(PLAN); (kalla / 'docs/decisions.md').write_text(BESLUT)
            os.symlink('plan.md', kalla / 'docs/lank.md')
            ut = subprocess.run([sys.executable, '-B', str(HERE / 'dokumentpost_prov.py'), str(kalla)],
                                input=json.dumps({'filer': ['docs/plan.md', 'docs/lank.md', 'tools/x.py']}),
                                capture_output=True, text=True, check=True).stdout
        v = json.loads(ut)
        self.assertTrue(v['filer']['docs/plan.md']['regelratt'])
        self.assertFalse(v['filer']['docs/lank.md']['regelratt'])
        self.assertFalse(v['filer']['tools/x.py']['regelratt'])
        self.assertEqual(v['agarens_tur']['rader'], len(aquarium.parse_owner_turn(PLAN, raw=True)))
        self.assertTrue(v['agarens_tur']['varje_radformad_rad_last'])
        self.assertEqual(v['beslut'], {'rubriker': 2, 'sista': 'POST-B'})


if __name__ == '__main__':
    unittest.main()
