"""Körningsströmmens tolk (PARTNER-INSYN-20261001): rena prov utan server, modell eller nät.

Händelseformerna är tagna ur verkliga strömmar lästa 2026-10-01 (Claude Code 2.1.280 i partnern, 2.1.285 och 2.1.257 i
mottagarsessioner): assistant-händelser per innehållsblock med samma message.id, user/tool_result med
tool_use_result som dict (Bash, Edit, Read), lista (MCP) eller saknad, stream_event med message_start/delta,
content_block_*, thinking_delta med estimated_tokens, system/status (requesting, compacting, null),
system/thinking_tokens, compact_boundary, api_retry, vcs_state_changed, code_change_published, task_started,
rate_limit_event, tool_progress och result. Codex-formen följer `_tolka_codex` och Codex SDK:s events.ts; ingen
verklig Codex-ström från partnern finns sparad, så command_execution och file_change är prövade mot fejkens form.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRATCH = REPO / '.scratch'
sys.path.insert(0, str(REPO / 'tools'))

from partnern import strom  # noqa: E402

TS = '2026-10-01T09:12:03.412Z'
TS2 = '2026-10-01T09:12:04.100Z'


def assistant(block, mid='msg_1', ts=TS, foralder=None, usage=None):
    return {'type': 'assistant', 'parent_tool_use_id': foralder, 'timestamp': ts,
            'message': {'id': mid, 'content': [block], 'usage': usage or {}}}


def tool_use(vid, namn, indata, **kw):
    return assistant({'type': 'tool_use', 'id': vid, 'name': namn, 'input': indata}, **kw)


def tool_result(vid, content, tur=None, fel=False, ts=TS2, foralder=None):
    ev = {'type': 'user', 'parent_tool_use_id': foralder, 'timestamp': ts,
          'message': {'role': 'user', 'content': [{'type': 'tool_result', 'tool_use_id': vid, 'content': content, 'is_error': fel}]}}
    if tur is not None:
        ev['tool_use_result'] = tur
    return ev


def kor(tolk, *handelser):
    logg = strom.Logg(None)
    for ev in handelser:
        logg.lagg_flera(tolk.mata(ev))
    return logg.alla()


class TolkProv(unittest.TestCase):
    def test_anrop_och_resultat_paras_med_tid_och_status(self):
        t = strom.Tolk('claude')
        rader = kor(t, tool_use('toolu_1', 'mcp__partner__sok', {'fraga': 'ägarens bord', 'omfang': ['partner']}),
                    tool_result('toolu_1', [{'type': 'text', 'text': '7 träffar\nS-1203 …'}], tur=[{'type': 'text', 'text': '7 träffar'}]))
        self.assertEqual([r['typ'] for r in rader], ['verktyg', 'resultat'])
        self.assertEqual(rader[0]['text'], 'Söker("ägarens bord", partner)')
        self.assertEqual(rader[0]['status'], 'pagar')
        self.assertEqual((rader[1]['id'], rader[1]['status'], rader[1]['ms']), ('toolu_1', 'klar', 688))
        self.assertEqual(rader[1]['resultat']['utdrag'], '7 träffar')
        self.assertEqual(rader[1]['resultat']['rader'], 2)
        self.assertEqual(t.lage()['raknare']['verktyg'], 1)
        self.assertEqual(t.lage()['fas']['lage'], 'svarar')

    def test_saknat_id_tolereras(self):
        t = strom.Tolk('claude')
        rader = kor(t, assistant({'type': 'tool_use', 'name': 'mcp__partner__resonemang', 'input': {'lage': 'prov'}}),
                    tool_result('', 'ok'))
        self.assertEqual(rader[0]['typ'], 'verktyg')
        self.assertIsNone(rader[0]['id'])
        self.assertEqual(rader[1]['typ'], 'resultat')
        self.assertIsNone(rader[1]['ms'])

    def test_bash_edit_read_sammanfattas_utan_filinnehall(self):
        t = strom.Tolk('claude')
        hemlig = 'ghp_' + 'A' * 36
        rader = kor(t,
                    tool_use('b1', 'Bash', {'command': 'git status --porcelain && echo x', 'description': 'Kolla git'}),
                    tool_result('b1', ' M tools/x.py\n?? y.py', tur={'stdout': ' M tools/x.py\n?? y.py', 'stderr': '', 'interrupted': False}),
                    tool_use('e1', 'Edit', {'file_path': '/Users/x/repo/tools/partnern/agent.py', 'old_string': 'HEMLIGT_GAMMALT', 'new_string': 'NYTT'}),
                    tool_result('e1', 'The file has been updated.', tur={'filePath': '/Users/x/repo/tools/partnern/agent.py', 'oldString': 'HEMLIGT_GAMMALT',
                                                                           'newString': 'NYTT', 'originalFile': 'HELA FILEN HÄR token=' + hemlig,
                                                                           'structuredPatch': [{'lines': ['-a', '+b', '+c', ' d']}]}),
                    tool_use('r1', 'Read', {'file_path': '/Users/x/repo/AGENTS.md', 'offset': 10, 'limit': 20}),
                    tool_result('r1', 'innehåll', tur={'type': 'text', 'file': {'filePath': '/Users/x/repo/AGENTS.md', 'content': 'HELA FILEN',
                                                                               'numLines': 20, 'startLine': 10, 'totalLines': 120}}),
                    tool_use('b2', 'Bash', {'command': 'python3 -m pytest -q'}),
                    tool_result('b2', 'E AttributeError', tur={'stdout': '', 'stderr': 'Traceback\nAttributeError: x', 'interrupted': False}, fel=True))
        dump = json.dumps(rader, ensure_ascii=False)
        for forbjudet in ('originalFile', 'oldString', 'newString', 'HELA FILEN', 'HEMLIGT_GAMMALT', hemlig, 'old_string', 'new_string'):
            self.assertNotIn(forbjudet, dump, forbjudet)
        per = {r['id']: r for r in rader if r['typ'] == 'resultat'}
        self.assertEqual(rader[0]['text'], 'Bash(git status --porcelain && echo x)')
        self.assertEqual(rader[0]['beskrivning'], 'Kolla git')
        self.assertEqual(rader[0]['indata'], 'git status --porcelain && echo x')
        self.assertEqual(per['b1']['resultat']['utdrag'], 'M tools/x.py')
        self.assertEqual(rader[2]['text'], 'Edit(…/partnern/agent.py)')
        self.assertEqual(per['e1']['resultat']['utdrag'], '…/partnern/agent.py: +2 −1')
        self.assertEqual(per['e1']['data'], {'fil': '…/partnern/agent.py', 'plus': 2, 'minus': 1, 'hunkar': 1})
        self.assertEqual(per['e1']['resultat']['utdrag_lang'], '')
        self.assertEqual(rader[4]['text'], 'Read(…/repo/AGENTS.md, rad 10 +20)')
        self.assertEqual(per['r1']['resultat']['utdrag'], 'rader 10–29 av 120')
        self.assertEqual(per['b2']['status'], 'fel')
        self.assertEqual(per['b2']['resultat']['utdrag'], 'Fel: Traceback')
        self.assertEqual(t.lage()['raknare']['fel'], 1)
        self.assertEqual(t.lage()['raknare']['verktyg'], 4)

    def test_utdrag_begransas_och_tvattas(self):
        t = strom.Tolk('claude')
        lang = 'x' * 5000 + '\nsk-ant-' + 'B' * 30
        rader = kor(t, tool_use('m1', 'mcp__partner__oppna', {'id': 'F-1'}), tool_result('m1', lang))
        res = rader[1]['resultat']
        self.assertEqual(len(res['utdrag']), strom.UTDRAG_KORT)
        self.assertLessEqual(len(res['utdrag_lang']), strom.UTDRAG_LANG + 10)
        self.assertEqual(res['storlek'], len(lang))
        rader = kor(t, tool_use('m2', 'mcp__partner__oppna', {'id': 'F-2'}), tool_result('m2', 'nyckel: sk-ant-' + 'B' * 30))
        self.assertIn('[DOLT]', rader[1]['resultat']['utdrag'])
        self.assertNotIn('B' * 30, json.dumps(rader))

    def test_hjartslag_blir_fas_inte_rader(self):
        t = strom.Tolk('claude')
        handelser = []
        for n in range(1000):
            handelser.append({'type': 'stream_event', 'parent_tool_use_id': None, 'event': {
                'type': 'content_block_delta', 'index': 0, 'delta': {'type': 'thinking_delta', 'thinking': '', 'estimated_tokens': 50 * (n + 1)}}})
            handelser.append({'type': 'system', 'subtype': 'thinking_tokens', 'estimated_tokens': 50 * (n + 1), 'estimated_tokens_delta': 50})
        rader = kor(t, *handelser)
        self.assertEqual(rader, [])
        lage = t.lage()
        self.assertEqual(lage['fas']['lage'], 'tanker')
        self.assertEqual(lage['fas']['tankt_tokens'], 50000)
        self.assertEqual(lage['raknare']['tankt_tokens'], 50000)
        self.assertEqual(lage['raknare']['utan_tolkning'], 0)

    def test_status_requesting_compacting_och_null(self):
        t = strom.Tolk('claude')
        kor(t, {'type': 'system', 'subtype': 'status', 'status': 'requesting'})
        self.assertEqual(t.lage()['fas']['lage'], 'begar')
        kor(t, {'type': 'system', 'subtype': 'status', 'status': 'compacting'})
        self.assertEqual(t.lage()['fas']['lage'], 'komprimerar')
        kor(t, {'type': 'system', 'subtype': 'status', 'status': None})
        self.assertEqual(t.lage()['fas']['lage'], 'svarar')
        kor(t, tool_use('b1', 'Bash', {'command': 'sleep 5'}))
        kor(t, {'type': 'system', 'subtype': 'status', 'status': None})
        self.assertEqual(t.lage()['fas']['lage'], 'verktyg')
        self.assertEqual(t.lage()['fas']['verktyg']['namn'], 'Bash')
        kor(t, {'type': 'tool_progress', 'tool_use_id': 'b1', 'tool_name': 'Bash', 'elapsed_time_seconds': 41, 'parent_tool_use_id': 'b1'})
        self.assertGreaterEqual(t.lage()['fas']['verktyg']['sekunder'], 41)

    def test_komprimering_omforsok_push_pr_uppgift(self):
        t = strom.Tolk('claude')
        rader = kor(t,
                    {'type': 'system', 'subtype': 'compact_boundary', 'compact_metadata': {'trigger': 'auto', 'pre_tokens': 969637, 'post_tokens': 18749, 'duration_ms': 82517}},
                    {'type': 'system', 'subtype': 'api_retry', 'attempt': 2, 'error': 'overloaded_error', 'error_status': 529},
                    {'type': 'system', 'subtype': 'vcs_state_changed', 'kind': 'push', 'branch': 'kontor/postkontroll-20260929'},
                    {'type': 'system', 'subtype': 'vcs_state_changed', 'kind': 'commit', 'branch': 'x'},
                    {'type': 'system', 'subtype': 'code_change_published', 'provider': 'github', 'action': 'created',
                     'url': 'https://github.com/Nortropic/nortropic-projektkontor/pull/136'},
                    {'type': 'system', 'subtype': 'task_started', 'task_id': 'b1', 'description': 'Run Digitala baseline test suite', 'task_type': 'local_bash'},
                    {'type': 'system', 'subtype': 'task_notification', 'task_id': 'b1', 'status': 'completed', 'summary': 'Klar: 321/321'},
                    {'type': 'system', 'subtype': 'background_tasks_changed'},
                    {'type': 'command_lifecycle', 'state': 'started'})
        self.assertEqual([r['typ'] for r in rader], ['komprimering', 'omforsok', 'push', 'pr', 'uppgift', 'uppgift'])
        self.assertEqual(rader[0]['text'], 'Komprimerade sammanhanget · 969,6k → 18,7k tokens · 1 min 22 s')
        self.assertEqual(rader[0]['data']['fore'], 969637)
        self.assertIn('nytt försök 2', rader[1]['text'])
        self.assertEqual(rader[2]['data'], {'gren': 'kontor/postkontroll-20260929'})
        self.assertEqual(rader[3]['text'], 'PR #136 skapad · https://github.com/Nortropic/nortropic-projektkontor/pull/136')
        self.assertEqual(rader[3]['data']['nummer'], 136)
        self.assertEqual(rader[4]['text'], 'Bakgrund: Run Digitala baseline test suite')
        self.assertEqual(rader[5]['text'], 'Bakgrund klar: Klar: 321/321')
        r = t.lage()['raknare']
        self.assertEqual((r['komprimeringar'], r['omforsok'], r['utan_tolkning']), (1, 1, 0))

    def test_kvot_rad_bara_vid_troskel_eller_stopp(self):
        t = strom.Tolk('claude')
        def kvot(fem, sju, status='allowed'):
            return {'type': 'rate_limit_event', 'rate_limit_info': {'status': status, 'rateLimitType': 'five_hour', 'resetsAt': 1790000000,
                                                                      'unifiedWindows': {'five_hour': {'utilization': fem}, 'seven_day': {'utilization': sju}}}}
        rader = kor(t, kvot(0.06, 0.51), kvot(0.07, 0.51), kvot(0.1, 0.86), kvot(0.1, 0.86), kvot(0.1, 0.87), kvot(0.1, 0.95, 'rejected'))
        self.assertEqual([r['typ'] for r in rader], ['kvot', 'kvot'])
        self.assertTrue(rader[0]['text'].startswith('Kvot 86 % av veckofönstret'))
        self.assertIn('återställs', rader[0]['text'])
        self.assertIn('stoppad', rader[1]['text'])
        self.assertEqual(t.lage()['raknare']['kvot']['sju_dagar'], 0.95)
        rader = kor(strom.Tolk('claude'), kvot(0.1, 0.2, 'allowed_warning'))
        self.assertEqual(rader[0]['typ'], 'kvot')

    def test_meddelanden_tokens_och_kontext(self):
        t = strom.Tolk('claude')
        u = {'input_tokens': 22, 'cache_read_input_tokens': 300000, 'cache_creation_input_tokens': 8000}
        kor(t, {'type': 'stream_event', 'parent_tool_use_id': None, 'event': {'type': 'message_start', 'message': {'id': 'msg_a', 'usage': u}}},
            {'type': 'stream_event', 'parent_tool_use_id': None, 'event': {'type': 'message_delta', 'usage': {'output_tokens': 1200}}},
            assistant({'type': 'text', 'text': 'Kort läge.'}, mid='msg_a', usage=u),
            assistant({'type': 'tool_use', 'id': 'x', 'name': 'mcp__partner__backlog', 'input': {}}, mid='msg_a', usage=u))
        r = t.lage()['raknare']
        self.assertEqual((r['meddelanden'], r['tokens_in'], r['cache_lasta'], r['cache_skrivna'], r['tokens_ut'], r['kontext']),
                         (1, 22, 300000, 8000, 1200, 308022))
        # utan partiella meddelanden (mottagarsessioner): assistant-händelserna räknar själva, en gång per message.id
        t2 = strom.Tolk('claude')
        kor(t2, assistant({'type': 'text', 'text': 'a'}, mid='m1', usage=u), assistant({'type': 'tool_use', 'id': 'y', 'name': 'Bash', 'input': {'command': 'ls'}}, mid='m1', usage=u),
            assistant({'type': 'text', 'text': 'b'}, mid='m2', usage=u))
        self.assertEqual(t2.lage()['raknare']['meddelanden'], 2)
        self.assertEqual(t2.lage()['raknare']['kontext'], 308022)

    def test_underagent_far_foralder(self):
        t = strom.Tolk('claude')
        rader = kor(t,
                    tool_use('ag1', 'Agent', {'subagent_type': 'utredare', 'description': 'prisnivåer Railway', 'prompt': 'HEMLIG PROMPT'}),
                    tool_use('w1', 'WebSearch', {'query': 'Railway pricing 2026'}, foralder='ag1'),
                    tool_result('w1', 'träffar', foralder='ag1', tur={'query': 'Railway pricing 2026', 'results': [{'content': [{'url': 'https://railway.com'}, {'url': 'https://docs.railway.com'}]}], 'durationSeconds': 2.1}),
                    assistant({'type': 'text', 'text': 'underagentens text'}, foralder='ag1'),
                    tool_result('ag1', 'Klar: 3 verktyg'))
        self.assertEqual(rader[0]['text'], 'Utredaren(prisnivåer Railway)')
        self.assertNotIn('HEMLIG PROMPT', json.dumps(rader))
        self.assertEqual((rader[1]['typ'], rader[1]['foralder']), ('utredare', 'ag1'))
        self.assertEqual(rader[2]['resultat']['utdrag'], '2 träffar')
        self.assertEqual([r['typ'] for r in rader], ['verktyg', 'utredare', 'resultat', 'resultat'])
        r = t.lage()['raknare']
        self.assertEqual((r['verktyg'], r['underagent']['verktyg']), (1, 1))

    def test_result_med_och_utan_resultatnyckel(self):
        t = strom.Tolk('claude')
        rader = kor(t, {'type': 'result', 'subtype': 'success', 'is_error': False, 'num_turns': 66, 'duration_ms': 802493, 'total_cost_usd': 34.84,
                        'usage': {'input_tokens': 10, 'output_tokens': 5, 'cache_read_input_tokens': 7}, 'result': 'svar'})
        self.assertEqual(rader[0]['text'], 'Klart · 66 varv · 13 min 22 s')
        self.assertEqual(rader[0]['status'], 'klar')
        self.assertTrue(t.slut)
        self.assertEqual(t.lage()['fas']['lage'], 'klar')
        self.assertEqual(t.lage()['raknare']['tokens_in'], 10)
        t2 = strom.Tolk('claude')
        rader = kor(t2, tool_use('b', 'Bash', {'command': 'x'}),
                    {'type': 'result', 'subtype': 'error_during_execution', 'is_error': True, 'num_turns': 90, 'errors': ['x'], 'terminal_reason': 'aborted_tools'})
        self.assertEqual(rader[-1]['text'], 'Slutade med fel (error_during_execution) · 90 varv')
        self.assertEqual(rader[-1]['data']['stopp'], 'aborted_tools')
        self.assertEqual(rader[-1]['status'], 'fel')

    def test_start_rad_bara_for_egen_start(self):
        init = {'type': 'system', 'subtype': 'init', 'model': 'claude-opus-5', 'claude_code_version': '2.1.285', 'session_id': 'abc',
                'permissionMode': 'auto', 'cwd': '/Users/x/repo', 'tools': ['Bash'], 'mcp_servers': []}
        self.assertEqual(kor(strom.Tolk('claude'), init), [])
        rader = kor(strom.Tolk('claude', egen_start=True), init)
        self.assertEqual(rader[0]['typ'], 'start')
        self.assertEqual(rader[0]['text'], 'Sessionen startade (claude-opus-5, Claude Code 2.1.285)')
        self.assertNotIn('/Users/x', json.dumps(rader))

    def test_okant_anrop_ger_bara_forsta_raden(self):  # granskningens not 2: ett resultat utan sett anrop får inget långt utdrag
        t = strom.Tolk('claude')
        rader = kor(t, tool_result('aldrig_sedd', 'HELA FILENS INNEHÅLL\nrad 2\nrad 3', tur={'file': {'content': 'HELA FILEN'}}))
        self.assertEqual(rader[0]['resultat']['utdrag'], 'HELA FILENS INNEHÅLL')
        self.assertEqual(rader[0]['resultat']['utdrag_lang'], 'HELA FILENS INNEHÅLL')
        self.assertNotIn('rad 2', json.dumps(rader))

    def test_tool_use_result_bara_till_ett_ensamt_resultat(self):  # not 3: två resultat i ett meddelande får inte dela dict
        t = strom.Tolk('claude')
        kor(t, tool_use('a', 'Bash', {'command': 'ls'}), tool_use('b', 'Bash', {'command': 'pwd'}))
        ev = {'type': 'user', 'parent_tool_use_id': None, 'timestamp': TS2, 'tool_use_result': {'stdout': 'ur a', 'stderr': ''},
              'message': {'role': 'user', 'content': [{'type': 'tool_result', 'tool_use_id': 'a', 'content': 'ur a'},
                                                      {'type': 'tool_result', 'tool_use_id': 'b', 'content': 'ur b'}]}}
        rader = kor(t, ev)
        self.assertEqual([r['resultat']['utdrag'] for r in rader], ['ur a', 'ur b'])
        self.assertEqual([r['data'] for r in rader], [{}, {}])

    def test_codex_bypassnotis_blir_ingen_varning(self):  # not 1: Codex eget besked om partnerns krok tiger tolken om
        rader = kor(strom.Tolk('codex'), {'type': 'item.completed', 'item': {'id': 'e', 'type': 'error', 'message': 'hooks run with dangerously-bypass-hook-trust'}},
                    {'type': 'item.completed', 'item': {'id': 'f', 'type': 'error', 'message': 'något annat'}})
        self.assertEqual([r['text'] for r in rader], ['något annat'])

    def test_trasig_handelse_ger_varning_och_fortsatt_tolkning(self):
        t = strom.Tolk('claude')
        rader = kor(t, {'type': 'assistant', 'message': {'content': [{'type': 'tool_use', 'id': 1, 'name': None, 'input': 'inte en dict'}]}},
                    {'type': 'user', 'message': {'content': 'bara text'}},
                    {'type': 'okand_typ'}, 'ingen dict',
                    tool_use('ok', 'Grep', {'pattern': 'underhall', 'path': 'verktyg/'}))
        self.assertEqual(rader[-1]['text'], 'Grep("underhall", verktyg/)')
        self.assertEqual(t.lage()['raknare']['utan_tolkning'], 1)
        self.assertTrue(all(r['typ'] in ('verktyg', 'varning') for r in rader))

    def test_codex_item_typer(self):
        t = strom.Tolk('codex')
        rader = kor(t,
                    {'type': 'thread.started', 'thread_id': 'thr_1'},
                    {'type': 'turn.started'},
                    {'type': 'item.started', 'item': {'id': 'i1', 'type': 'reasoning'}},
                    {'type': 'item.completed', 'item': {'id': 'i1', 'type': 'reasoning', 'text': 'tänker'}},
                    {'type': 'item.started', 'item': {'id': 'i2', 'type': 'command_execution', 'command': 'git status'}},
                    {'type': 'item.completed', 'item': {'id': 'i2', 'type': 'command_execution', 'command': 'git status', 'exit_code': 1, 'aggregated_output': 'fatal: not a git repo', 'status': 'completed'}},
                    {'type': 'item.started', 'item': {'id': 'i3', 'type': 'file_change', 'changes': [{'path': 'tools/x.py', 'kind': 'update'}, {'path': 'tools/y.py', 'kind': 'add'}]}},
                    {'type': 'item.completed', 'item': {'id': 'i3', 'type': 'file_change', 'changes': [{'path': 'tools/x.py', 'kind': 'update'}, {'path': 'tools/y.py', 'kind': 'add'}], 'status': 'completed'}},
                    {'type': 'item.started', 'item': {'id': 'i4', 'type': 'mcp_tool_call', 'server': 'partner', 'tool': 'sok', 'arguments': {'fraga': 'x'}}},
                    {'type': 'item.completed', 'item': {'id': 'i4', 'type': 'mcp_tool_call', 'server': 'partner', 'tool': 'sok', 'arguments': {'fraga': 'x'}, 'status': 'failed', 'error': {'message': 'nekat av kroken'}}},
                    {'type': 'item.completed', 'item': {'id': 'i5', 'type': 'web_search', 'query': 'Railway', 'results': [{'domain': 'railway.com'}]}},
                    {'type': 'item.completed', 'item': {'id': 'i6', 'type': 'agent_message', 'text': 'Svaret.'}},
                    {'type': 'item.completed', 'item': {'id': 'i7', 'type': 'nytt_slag', 'foo': 'bar'}},
                    {'type': 'error', 'message': 'Reconnecting... (403)'},
                    {'type': 'turn.completed', 'usage': {'input_tokens': 1000, 'cached_input_tokens': 900, 'output_tokens': 50, 'reasoning_output_tokens': 20}})
        typer = [r['typ'] for r in rader]
        self.assertEqual(typer, ['verktyg', 'resultat', 'verktyg', 'resultat', 'verktyg', 'resultat', 'verktyg', 'resultat',
                                 'text', 'omforsok', 'slut'])
        self.assertEqual(rader[0]['text'], 'Bash(git status)')
        self.assertEqual((rader[1]['status'], rader[1]['resultat']['utdrag']), ('fel', 'exit 1 · fatal: not a git repo'))
        self.assertEqual(rader[2]['text'], 'Edit(2 filer)')
        self.assertEqual(rader[4]['text'], 'Söker("x")')
        self.assertEqual((rader[5]['status'], rader[5]['resultat']['utdrag']), ('fel', 'Fel: nekat av kroken'))
        self.assertEqual(rader[6]['text'], 'Webbsökning("Railway")')
        self.assertEqual(rader[7]['resultat']['utdrag'], '1 träffar')
        self.assertEqual(rader[8]['text'], 'Svaret.')
        self.assertEqual(rader[9]['text'], 'Codex: Reconnecting... (403)')
        r = t.lage()['raknare']
        self.assertEqual(r['utan_tolkning'], 1)  # okänd item-typ räknas, visas aldrig som brus, stoppar inget
        self.assertEqual((r['tokens_in'], r['cache_lasta'], r['tokens_ut'], r['omforsok'], r['fel']), (100, 900, 70, 1, 2))
        self.assertTrue(t.slut)


class LoggProv(unittest.TestCase):
    def setUp(self):
        SCRATCH.mkdir(exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(prefix='strom-', dir=SCRATCH)
        self.addCleanup(self.tmp.cleanup)
        self.fil = Path(self.tmp.name) / 'handelser.jsonl'

    def test_n_tid_fil_och_markor(self):
        logg = strom.Logg(self.fil)
        logg.lagg({'typ': 'start', 'text': 'x'})
        logg.lagg_flera([{'typ': 'verktyg', 'id': 'a', 'text': 'Bash(ls)', 'status': 'pagar'},
                         {'typ': 'resultat', 'id': 'a', 'status': 'klar', 'ms': 3000, 'resultat': {'fel': False}}, {'inte': 'en rad'}])
        self.assertEqual(logg.nasta, 3)
        rader, nasta = logg.fran(1)
        self.assertEqual(([r['n'] for r in rader], nasta), ([1, 2], 3))
        self.assertEqual(logg.fran(3), ([], 3))
        self.assertEqual(logg.fran(99), ([], 3))
        self.assertEqual(logg.fran(-5)[0][0]['n'], 0)
        self.assertTrue(all(r['tid'].endswith('Z') for r in rader))
        self.assertEqual(oct(os.stat(self.fil).st_mode & 0o777), '0o600')
        fil_rader, antal = strom.las_handelser(self.fil)
        self.assertEqual(antal, 3)
        self.assertEqual(fil_rader, logg.alla())
        steg = logg.steg(60)
        self.assertEqual(steg, [{'tid': steg[0]['tid'], 'typ': 'start', 'text': 'x'}, {'tid': steg[1]['tid'], 'typ': 'verktyg', 'text': 'Bash(ls) · 3,0 s'}])

    def test_ofullstandig_sista_rad_hoppas_over(self):
        self.fil.write_text('{"typ":"start","text":"a","n":0,"tid":"t"}\n{"typ":"verktyg","text":"b","n":1,"tid":"t"}\n{"typ":"res', 'utf-8')
        rader, antal = strom.las_handelser(self.fil)
        self.assertEqual(antal, 2)
        self.assertEqual(strom.las_handelser(self.fil, 1)[0][0]['text'], 'b')
        self.assertEqual(strom.las_handelser(Path(self.tmp.name) / 'finns-inte.jsonl'), ([], 0))

    def test_steg_viker_ihop_fel(self):
        rader = [{'typ': 'verktyg', 'id': 'a', 'text': 'Läser(x)'}, {'typ': 'text', 'text': 'mellanrad'},
                 {'typ': 'resultat', 'id': 'a', 'status': 'fel', 'resultat': {'fel': True}}, {'typ': 'uppgift', 'text': 'bakgrund'},
                 {'typ': 'slut', 'text': 'Klart'}]
        self.assertEqual([(s['typ'], s['text']) for s in strom.steg_ur(rader)], [('verktyg', 'Läser(x) · fel'), ('slut', 'Klart')])
        self.assertEqual(len(strom.steg_ur([{'typ': 'verktyg', 'text': str(i)} for i in range(100)], 60)), 60)

    def test_sammanfatta(self):
        rader = [{'typ': 'verktyg', 'verktyg': 'Edit'}, {'typ': 'resultat', 'resultat': {'fel': True}}, {'typ': 'utredare'},
                 {'typ': 'push'}, {'typ': 'pr'}, {'typ': 'nekat'}, {'typ': 'komprimering'}, {'typ': 'slut', 'text': 'Klart', 'status': 'klar'}]
        s = strom.sammanfatta(rader)
        self.assertEqual((s['verktyg'], s['utredare'], s['fel'], s['andringar'], s['push'], s['pr'], s['nekat'], s['komprimeringar']), (1, 1, 1, 1, 1, 1, 1, 1))
        self.assertEqual(s['slut']['text'], 'Klart')


class SvansProv(unittest.TestCase):
    def setUp(self):
        SCRATCH.mkdir(exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(prefix='svans-', dir=SCRATCH)
        self.addCleanup(self.tmp.cleanup)
        self.fil = Path(self.tmp.name) / 'korning-01.jsonl'

    def test_tillvaxt_och_tillbakahallen_rad(self):
        s = strom.Svans(self.fil)
        self.assertEqual(s.las(), [])
        with open(self.fil, 'ab') as f:
            f.write(b'{"type":"a"}\n{"type":"b"}\n{"type":"c')
        self.assertEqual([e['type'] for e in s.las()], ['a', 'b'])
        self.assertEqual(s.las(), [])
        with open(self.fil, 'ab') as f:
            f.write(b'"}\ninte json\n{"type":"d"}\n')
        self.assertEqual([e['type'] for e in s.las()], ['c', 'd'])
        self.assertEqual(s.ogiltiga, 1)

    def test_inode_byte_borjar_om_och_lank_vagras(self):
        s = strom.Svans(self.fil)
        self.fil.write_bytes(b'{"type":"a"}\n{"type":"b"}\n')
        self.assertEqual(len(s.las()), 2)
        ny = Path(self.tmp.name) / 'ny.jsonl'
        ny.write_bytes(b'{"type":"x"}\n')
        os.replace(ny, self.fil)  # ny inode, kortare fil
        self.assertEqual([e['type'] for e in s.las()], ['x'])
        lank = Path(self.tmp.name) / 'lank.jsonl'
        lank.symlink_to(self.fil)
        with self.assertRaises(ValueError):
            strom.Svans(lank).las()

    def test_stor_fil_i_delar(self):
        rad = b'{"type":"a","fyll":"' + b'x' * 1000 + b'"}\n'
        with open(self.fil, 'wb') as f:
            for _ in range(10000):
                f.write(rad)
        s = strom.Svans(self.fil)
        forsta = s.las()
        self.assertLess(len(forsta), 10000)
        self.assertGreater(len(forsta), 7000)
        resten = s.las()
        self.assertEqual(len(forsta) + len(resten), 10000)


if __name__ == '__main__':
    unittest.main()
