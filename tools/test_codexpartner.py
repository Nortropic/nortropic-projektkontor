"""Partnern på Codex (MODELLKARTA-20260929 steg 1b): modellen avgör utföraren, och Codex körs lika avgränsat som Claude.

Samma uppställning som `tools/test_partner.py`: en riktig server i processen på 127.0.0.1. Codex är ett falskt program
som gör det riktiga Codex gör i en partnertur: läser prompten på stdin, kör partnerns krok (PreToolUse) mot servern med
körningens nyckel ur miljön, startar MCP-bryggan med bara de namngivna miljövariablerna och skriver `codex exec --json`-
händelser. Ingen modell och inget nät.
"""
from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
import unittest
from pathlib import Path

import test_partner as tp

from partnern import agent as ag
from partnern import webbpolicy as wp

FEJK_CODEX = r'''#!/usr/bin/env python3
import json, os, re, subprocess, sys
from pathlib import Path
args = sys.argv[1:]
prompt = sys.stdin.read()
c = {}
for i, a in enumerate(args):
    if a == '-c':
        nyckel, _, varde = args[i + 1].partition('=')
        c[nyckel] = varde
bilder = [args[i + 1] for i, a in enumerate(args) if a == '-i']
logg = {'argv': args, 'prompt': prompt, 'bilder': [Path(b).read_bytes().hex()[:16] for b in bilder],
        'env_nycklar': sorted(k for k in os.environ if k.startswith('PARTNER_')), 'nyckel': os.environ.get('PARTNER_KORNING')}
def ut(o):
    sys.stdout.write(json.dumps(o, ensure_ascii=False) + '\n'); sys.stdout.flush()
# kroken, som Codex kör före varje verktyg: kommandot ur konfigurationen, med Codex egen miljö
krok = json.loads(re.search(r'command=("(?:[^"\\]|\\.)*")', c['hooks.PreToolUse']).group(1))
def fraga_krok(namn, indata):
    r = subprocess.run(krok, shell=True, input=json.dumps({'hook_event_name': 'PreToolUse', 'tool_name': namn,
                                                           'tool_input': indata}), capture_output=True, text=True)
    return json.loads(r.stdout)['hookSpecificOutput']['permissionDecision']
# MCP-bryggan, med bara env_vars ur Codex miljö (som Codex gör)
namn_env = json.loads(c['mcp_servers.partner.env_vars'])
env = {k: os.environ[k] for k in ('PATH', 'HOME') if k in os.environ}
env.update({k: os.environ[k] for k in namn_env if k in os.environ})
bro = subprocess.Popen([json.loads(c['mcp_servers.partner.command'])] + json.loads(c['mcp_servers.partner.args']),
                       stdin=subprocess.PIPE, stdout=subprocess.PIPE, env=env, text=True)
n = [0]
def rpc(metod, p=None):
    n[0] += 1
    bro.stdin.write(json.dumps({'jsonrpc': '2.0', 'id': n[0], 'method': metod, 'params': p or {}}) + '\n'); bro.stdin.flush()
    return json.loads(bro.stdout.readline())
rpc('initialize', {'protocolVersion': '2025-06-18'})
verktyg = [v['name'] for v in rpc('tools/list')['result']['tools']]
ut({'type': 'thread.started', 'thread_id': '01a0ef8a-08f9-7c31-a850-420ceafc2645'})
ut({'type': 'turn.started'})
if Path(__file__).with_name('tillfalligt-fel').exists():   # som när Codex återansluter mitt i en tur
    ut({'type': 'error', 'message': 'Reconnecting... 1/5 (unexpected status 403 Forbidden)'})
ut({'type': 'item.completed', 'item': {'id': 'e0', 'type': 'error', 'message': '`--dangerously-bypass-hook-trust` is enabled.'}})
beslut = {}
beslut['sok'] = fraga_krok('mcp__partner__sok', {'fraga': 'nortropic'})
ut({'type': 'item.started', 'item': {'id': 'i1', 'type': 'mcp_tool_call', 'server': 'partner', 'tool': 'sok', 'arguments': {'fraga': 'nortropic'}}})
svar = rpc('tools/call', {'name': 'sok', 'arguments': {'fraga': 'nortropic'}})['result']
ut({'type': 'item.completed', 'item': {'id': 'i1', 'type': 'mcp_tool_call', 'server': 'partner', 'tool': 'sok', 'status': 'completed'}})
beslut['webrun_sok'] = fraga_krok('webrun', {'search_query': [{'q': 'temporal python sdk release'}], 'response_length': 'short'})
ut({'type': 'item.completed', 'item': {'id': 'i2', 'type': 'web_search', 'query': 'temporal python sdk release',
    'action': {'type': 'search'}, 'results': [{'type': 'text_result', 'domain': 'pypi.org', 'ref_id': 'turn0search0'}]}})
beslut['webrun_ref'] = fraga_krok('webrun', {'open': [{'ref_id': 'turn0search0'}], 'response_length': 'short'})
beslut['webrun_okand_ref'] = fraga_krok('webrun', {'open': [{'ref_id': 'turn9search9'}]})
beslut['view_image'] = fraga_krok('view_image', {'path': '/etc/passwd'})
beslut['apply_patch'] = fraga_krok('apply_patch', {'command': '*** Begin Patch'})
beslut['agent'] = fraga_krok('collaborationspawn_agent', {'task_name': 'x'})
logg['beslut'] = beslut
logg['verktyg'] = verktyg
logg['sok_svar'] = (svar.get('content') or [{}])[0].get('text', '')[:120]
with open(Path(__file__).with_name('codexlogg.jsonl'), 'a') as f:
    f.write(json.dumps(logg, ensure_ascii=False) + '\n')
ut({'type': 'item.completed', 'item': {'id': 'i3', 'type': 'agent_message', 'text': 'Svar från Codex: ' + json.dumps(beslut, sort_keys=True)}})
ut({'type': 'turn.completed', 'usage': {'input_tokens': 1200, 'cached_input_tokens': 800, 'output_tokens': 40, 'reasoning_output_tokens': 10}})
bro.stdin.close()
'''


class CodexMiljo(tp.Miljo):
    def setUp(self):
        super().setUp()
        self.fejk_codex = self.rot / 'codex'
        self.fejk_codex.write_text(FEJK_CODEX.replace('/usr/bin/env python3', tp.sys.executable), 'utf-8')
        self.fejk_codex.chmod(0o755)
        self.S.k.codex = str(self.fejk_codex)
        self.S.k.modell.huvud, self.S.k.modell.anstrangning = 'gpt-6-astra', 'ultra'
        self.logga_in()

    def codexlogg(self):
        f = self.rot / 'codexlogg.jsonl'
        return [json.loads(r) for r in f.read_text().splitlines()] if f.exists() else []


class EnTurPaCodex(CodexMiljo):
    def test_modellen_avgor_utforaren_och_turen_gar_genom_codex(self):
        d = self.skicka('Vad vet du om Nortropic?')
        trad = d['inspel']['trad']
        vy = self.vanta(trad, lambda v: self.turer(v, 'svarad'))
        tur = self.turer(vy, 'svarad')[0]
        self.assertIn('Svar från Codex', tur['svar'])
        self.assertEqual(self.fejkanrop(), [])                  # Claude Code startades aldrig
        logg = self.codexlogg()
        self.assertEqual(len(logg), 1)
        self.assertIn('Vad vet du om Nortropic?', logg[0]['prompt'])
        self.assertIn('sok', logg[0]['verktyg'])
        self.assertTrue(logg[0]['sok_svar'])                   # bryggan nådde servern med körningens nyckel
        self.assertEqual(logg[0]['env_nycklar'], ['PARTNER_KORNING', 'PARTNER_URL'])
        rad = self.S.lager.en('select data from tur where id=?', (tur['id'],))
        klar = json.loads(rad['data'])['klar']
        self.assertEqual((klar['forbrukning']['utforare'], klar['forbrukning']['modell'], klar['forbrukning']['anstrangning']),
                         ('codex', 'gpt-6-astra', 'ultra'))
        self.assertEqual((klar['forbrukning']['tokens_in'], klar['forbrukning']['tokens_ut']), (1200, 50))

    def test_kroken_slapper_partnerns_verktyg_och_webben_men_nekar_resten(self):
        d = self.skicka('Sök och läs.')
        self.vanta(d['inspel']['trad'], lambda v: self.turer(v, 'svarad'))
        beslut = self.codexlogg()[0]['beslut']
        self.assertEqual(beslut, {'sok': 'allow', 'webrun_sok': 'allow', 'webrun_ref': 'allow', 'webrun_okand_ref': 'deny',
                                  'view_image': 'deny', 'apply_patch': 'deny', 'agent': 'deny'})

    def test_argumenten_stanger_skal_och_egen_konfiguration_och_nyckeln_star_aldrig_i_dem(self):
        d = self.skicka('Hej.')
        self.vanta(d['inspel']['trad'], lambda v: self.turer(v, 'svarad'))
        argv = self.codexlogg()[0]['argv']
        for flagga in ('exec', '--json', '--ephemeral', '--ignore-user-config', '--dangerously-bypass-hook-trust'):
            self.assertIn(flagga, argv)
        self.assertEqual(argv[argv.index('-s') + 1], 'read-only')
        self.assertEqual(argv[argv.index('-m') + 1], 'gpt-6-astra')
        avstangt = {argv[i + 1] for i, a in enumerate(argv) if a == '--disable'}
        self.assertTrue({'shell_tool', 'unified_exec', 'multi_agent', 'apps', 'plugins', 'computer_use', 'view_image',
                         'sleep_tool'} <= avstangt)
        c = {argv[i + 1].split('=', 1)[0]: argv[i + 1].split('=', 1)[1] for i, a in enumerate(argv) if a == '-c'}
        self.assertEqual(c['model_reasoning_effort'], '"ultra"')
        self.assertEqual(c['approval_policy'], '"never"')
        self.assertEqual(json.loads(c['mcp_servers.partner.env_vars']), ['PARTNER_URL', 'PARTNER_KORNING'])
        self.assertIn('Den här körningen (Codex)', json.loads(c['developer_instructions']))
        nyckel = self.codexlogg()[0]['nyckel']
        self.assertTrue(nyckel and len(nyckel) >= 32)            # körningens nyckel fanns i Codex miljö …
        self.assertNotIn(nyckel, ' '.join(argv))                 # … men aldrig i processargumenten
        self.assertEqual(argv[-1], '-')


class KontinuitetOchFel(CodexMiljo):
    def test_tillbaka_till_claude_far_codex_svaret_i_historiken_och_en_egen_session(self):
        d = self.skicka('Första frågan, på Codex.')
        trad = d['inspel']['trad']
        self.vanta(trad, lambda v: self.turer(v, 'svarad'))
        self.assertEqual(self.S.lager.trad(trad)['session'], 'codex-01a0ef8a-08f9-7c31-a850-420ceafc2645')
        self.S.k.modell.huvud, self.S.k.modell.anstrangning = 'claude-opus-5-5', 'high'
        self.skicka('Andra frågan, på Claude.', trad=trad)
        self.vanta(trad, lambda v: len(self.turer(v, 'svarad')) == 2)
        anrop = self.fejkanrop()[-1]
        session = anrop['argv'][anrop['argv'].index('--session-id') + 1]
        self.assertRegex(session, r'\A[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\Z')
        self.assertNotIn('--resume', anrop['argv'])
        self.assertIn('Svar från Codex', anrop['text'])        # Codex-turens svar finns i Claudes historik
        self.assertIn('Första frågan, på Codex.', anrop['text'])

    def test_ett_tillfalligt_fel_blir_ett_omforsok_och_turen_svarar(self):
        (self.rot / 'tillfalligt-fel').write_text('1')
        d = self.skicka('Hej.')
        vy = self.vanta(d['inspel']['trad'], lambda v: self.turer(v, 'svarad'))
        tur = self.turer(vy, 'svarad')[0]
        self.assertIn('Svar från Codex', tur['svar'])
        self.assertTrue(any(s['typ'] == 'omforsok' and 'Reconnecting' in s['text'] for s in tur['steg']))

    def test_en_oppnad_sida_gor_aldrig_en_annan_vard_oppningsbar(self):
        k = ag.Korning(self.S, 'tur', self.S.ny_trad()['id'], [])
        k.utforare = 'codex'
        utfall = {'usage': None, 'fel': []}
        self.S.agent._tolka_codex(k, {'type': 'item.completed', 'item': {
            'type': 'web_search', 'query': 'https://docs.python.org/3/', 'action': {'type': 'open_page', 'url': 'https://docs.python.org/3/'},
            'results': [{'domain': 'docs.python.org', 'ref_id': 'turn0view0'}, {'domain': 'annan.example', 'ref_id': 'turn0view1'}]}}, utfall)
        self.assertEqual(k.codex_ref, {'turn0view0': 'docs.python.org'})
        self.assertEqual(k.sokvardar, set())
        self.assertEqual(wp.prova_codex(k, 'webrun', {'open': [{'ref_id': 'turn0view1'}]})[0], 'deny')
        self.assertEqual(wp.prova_codex(k, 'webrun', {'open': [{'ref_id': 'turn0view0', 'lineno': 40}]})[0], 'allow')

    def test_en_stor_systemprompt_laggs_i_prompten_i_stallet_for_argumenten(self):
        k = ag.Korning(self.S, 'tur', self.S.ny_trad()['id'], [])
        k.modell, k.anstrangning, k.utforare = 'gpt-6-astra', 'high', 'codex'
        stor = 'x' * (ag.CODEX_INSTRUKTION_MAX + 1)
        argv = self.S.agent.argv_codex(k, stor, [])
        self.assertNotIn(stor, ' '.join(argv))
        self.assertLess(len(' '.join(argv)), 50_000)


class KrokenNekarSjalv(CodexMiljo):
    """Codex kör verktyget om kroken dör utan svar eller inte hinner svara (steg1b/KVITTO-krokfel.txt); kroken får
    därför aldrig bli tyst."""

    def krokkommando(self):
        k = ag.Korning(self.S, 'tur', self.S.ny_trad()['id'], [])
        k.modell, k.anstrangning, k.utforare = 'gpt-6-astra', 'high', 'codex'
        c = [a for a in self.S.agent.argv_codex(k, 'SYSTEM', []) if a.startswith('hooks.PreToolUse=')][0]
        return json.loads(c[c.index('command=') + len('command='):c.index(', timeout=')])

    def test_startar_kroken_inte_nekar_skalets_reservrad(self):
        kommando = self.krokkommando()
        python = ag._citera(sys.executable)
        self.assertTrue(kommando.startswith(python + ' -B '))
        r = subprocess.run(['/bin/sh', '-c', '/usr/bin/false' + kommando[len(python):]], capture_output=True, text=True,
                           input=json.dumps({'tool_name': 'webrun', 'tool_input': {}}), timeout=30)
        svar = json.loads(r.stdout)['hookSpecificOutput']
        self.assertEqual((svar['permissionDecision'], svar['permissionDecisionReason']),
                         ('deny', 'Partnerns krok kunde inte köras; anropet nekas.'))

    def test_hanger_servern_svarar_kroken_nej_fore_tidsgransen(self):
        s = socket.socket()
        self.addCleanup(s.close)
        s.bind(('127.0.0.1', 0))
        s.listen(1)                                       # tar emot anslutningen men svarar aldrig
        verktyg = str(Path(__file__).resolve().parent)
        t0 = time.monotonic()
        r = subprocess.run([sys.executable, '-B', '-c', 'import sys; sys.path.insert(0, %r); from partnern import krok; '
                            'krok.FRIST = 1; sys.exit(krok.main())' % verktyg], capture_output=True, text=True, timeout=30,
                           input=json.dumps({'tool_name': 'webrun', 'tool_input': {}}),
                           env={'PATH': os.environ.get('PATH', ''), 'PARTNER_URL': 'http://127.0.0.1:%d' % s.getsockname()[1],
                                'PARTNER_KORNING': 'x'})
        self.assertLess(time.monotonic() - t0, 10)          # urlopen hade väntat 15 s
        svar = json.loads(r.stdout)['hookSpecificOutput']
        self.assertEqual((r.returncode, svar['permissionDecision'], svar['permissionDecisionReason']),
                         (0, 'deny', 'Partnerns server svarade inte i tid; anropet nekas.'))

    def test_fristen_ligger_under_programmens_tidsgrans(self):
        from partnern import krok
        k = ag.Korning(self.S, 'tur', self.S.ny_trad()['id'], [])
        k.modell, k.anstrangning, k.utforare = 'gpt-6-astra', 'high', 'codex'
        c = [a for a in self.S.agent.argv_codex(k, 'SYSTEM', []) if a.startswith('hooks.PreToolUse=')][0]
        self.assertIn('timeout=20}', c)
        self.assertLess(krok.FRIST, 20)

    def test_claudevagens_krok_har_samma_reservrad_och_frist(self):
        # Claude Code 2.1.280 släpper också igenom en webbsökning när kroken dör eller inte hinner svara
        # (steg3/KVITTO-krokfel-claude.txt); reservraden stoppade den.
        from partnern import krok
        k = ag.Korning(self.S, 'tur', self.S.ny_trad()['id'], [])
        k.modell, k.anstrangning, k.utforare = 'claude-opus-5-5', 'high', 'claude'
        a = self.S.agent.argv(k, 'e3b0c442-98fc-4c14-9afb-f4c8996fb924', True)
        hook = json.loads(a[a.index('--settings') + 1])['hooks']['PreToolUse'][0]['hooks'][0]
        self.assertEqual(hook['command'], ag._krokkommando(sys.executable))
        self.assertEqual(hook['timeout'], 20); self.assertLess(krok.FRIST, hook['timeout'])
        python = ag._citera(sys.executable)
        r = subprocess.run(['/bin/sh', '-c', '/usr/bin/false' + hook['command'][len(python):]], capture_output=True, text=True,
                           input=json.dumps({'tool_name': 'WebSearch', 'tool_input': {'query': 'x'}}), timeout=30)
        svar = json.loads(r.stdout)['hookSpecificOutput']
        self.assertEqual((svar['permissionDecision'], svar['permissionDecisionReason']),
                         ('deny', 'Partnerns krok kunde inte köras; anropet nekas.'))


class Webbgrinden(unittest.TestCase):
    """webbpolicy.prova_codex utan server: samma regler som WebSearch och WebFetch, och allt annat nekas."""

    class K:
        url_varder = {'example.org'}
        sokvardar = {'pypi.org'}
        codex_ref = {'turn0search0': 'pypi.org'}

    def prova(self, verktyg, indata):
        return wp.prova_codex(self.K(), verktyg, indata, ('hemligt-varde-123',))[0]

    def test_partnerns_verktyg_och_klockan_tillats_allt_annat_nekas(self):
        self.assertEqual(self.prova('mcp__partner__sok', {}), 'allow')
        self.assertEqual(self.prova('clockcurr_time', {}), 'allow')
        for namn in ('view_image', 'apply_patch', 'collaborationspawn_agent', 'exec', 'mcp__annan__x', 'mcp__partner__../x', ''):
            self.assertEqual(self.prova(namn, {}), 'deny', namn)

    def test_webbverktyget_provas_som_sokning_och_hamtning(self):
        self.assertEqual(self.prova('webrun', {'search_query': [{'q': 'temporal python'}]}), 'allow')
        self.assertEqual(self.prova('webrun', {'search_query': [{'q': 'nyckel hemligt-varde-123'}]}), 'deny')
        self.assertEqual(self.prova('webrun', {'search_query': [{'q': 'mejla anna@example.com'}]}), 'deny')
        self.assertEqual(self.prova('webrun', {'search_query': [{'q': 'x site:evil.example'}]}), 'deny')
        self.assertEqual(self.prova('webrun', {'search_query': [{'q': 'x', 'domains': ['evil.example']}]}), 'deny')
        self.assertEqual(self.prova('webrun', {'search_query': [{'q': 'x', 'domains': ['docs.python.org']}]}), 'allow')
        self.assertEqual(self.prova('webrun', {'open': [{'ref_id': 'https://docs.python.org/3/'}]}), 'allow')
        self.assertEqual(self.prova('webrun', {'open': [{'ref_id': 'https://pypi.org/project/x/'}]}), 'allow')
        self.assertEqual(self.prova('webrun', {'open': [{'ref_id': 'http://127.0.0.1:4760/api'}]}), 'deny')
        self.assertEqual(self.prova('webrun', {'open': [{'ref_id': 'https://okand.example/x'}]}), 'deny')
        self.assertEqual(self.prova('webrun', {'open': [{'ref_id': 'turn0search0'}]}), 'allow')
        self.assertEqual(self.prova('webrun', {'open': [{'ref_id': 'turn5search5'}]}), 'deny')

    def test_okand_form_nekas(self):
        for indata in ({}, {'click': [{'ref_id': 'x'}]}, {'search_query': 'text'}, {'search_query': [{'q': 1}]},
                       {'search_query': [{'q': 'x', 'okand': 1}]}, {'open': [{'url': 'https://docs.python.org'}]}, []):
            self.assertEqual(self.prova('webrun', indata), 'deny', indata)


class ModellvaletMedCodex(CodexMiljo):
    def setUp(self):
        super().setUp()
        import test_modellkarta as tm
        (Path(self.S.k.data) / 'modellmatning.json').write_text(json.dumps(tm.matning()), 'utf-8')

    def test_samtalsytan_bar_codex_modellerna_med_egna_nivaer(self):
        d = self.json('GET', '/api/installningar')[1]
        m = {x['id']: x for x in d['modeller']}
        self.assertEqual(m['gpt-6-astra']['utforare'], 'codex')
        self.assertIn('ultra', m['gpt-6-astra']['nivaer'])
        self.assertNotIn('ultra', m['claude-opus-5-5']['nivaer'])
        self.assertEqual(d['utforare'], 'codex')

    def test_en_codex_modell_sparas_bara_om_den_fungerat(self):
        self.assertEqual(self.json('POST', '/api/installningar', {'huvud': 'gpt-6-sol', 'anstrangning': 'max'})[0], 200)
        self.assertEqual((self.S.k.modell.huvud, self.S.k.modell.anstrangning), ('gpt-6-sol', 'max'))
        self.assertEqual(self.json('POST', '/api/installningar', {'huvud': 'gpt-okand', 'anstrangning': 'high'})[0], 400)
        self.assertEqual(self.json('POST', '/api/installningar', {'huvud': 'gpt-6-sol', 'anstrangning': 'minimal'})[0], 400)
        (Path(self.S.k.data) / 'modellmatning.json').unlink()
        self.assertEqual(self.json('POST', '/api/installningar', {'huvud': 'gpt-6-astra', 'anstrangning': 'high'})[0], 400)

    def test_partnern_kan_valjas_pa_codex_i_flodet(self):
        from partnern import modellkarta as mk
        self.S.runtime_val = mk.RuntimeLasning(self.S.k, korare=lambda: (_ for _ in ()).throw(ValueError('x')))
        kod, d = self.json('POST', '/api/arbetsplats/karta', {'val': 'partner', 'modell': 'gpt-6.1-sol', 'anstrangning': 'ultra'})
        self.assertEqual(kod, 200, d)
        p = d['val']['partner']
        self.assertEqual((p['modell'], p['anstrangning'], p['utforare'], p['bevisad']), ('gpt-6.1-sol', 'ultra', 'codex', True))
        self.assertIn('gpt-6-astra', [x['id'] for x in p['erbjud']])


if __name__ == '__main__':
    unittest.main()
