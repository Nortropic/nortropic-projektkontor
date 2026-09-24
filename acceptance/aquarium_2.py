"""Frozen host contract for Aquarium v0's reading and projection; candidate code runs native-sandboxed on synthetic data.

Second version, for office-aquarium-projection-2: identical to acceptance/aquarium.py except two host defects found when
the first task ran: the PROBE check compares a SHA-256 instead of reading TASK.md, which Runtime's verification workspace
does not hold, and the documentation check asks only for what the brief states (the command), not for one chosen word.
"""
import json
import subprocess
from pathlib import Path
SCRIPT = r'''
import sys, pathlib, copy, json, re, subprocess, tempfile, os
from datetime import datetime, timedelta, timezone
sys.path.insert(0, str(pathlib.Path('tools').resolve()))
import aquarium as m
NOW = datetime(2026, 9, 24, 15, 0, tzinfo=timezone.utc)
T = lambda **k: (NOW - timedelta(**k)).isoformat()
RUN_ID = '01a0d236-c5db-7c5f-baa5-c0b1daf0254a'
PRIVATE = ['/Users/', '/private/', '/home/', '.runtime', 'local/', RUN_ID, 'usage limit', 'prov@example.invalid', 'locator', 'PRIVATE-MARKER']
def ok(value, minutes=1): return {'status': 'ok', 'read_at': T(minutes=minutes), 'value': value}
def base():
    return {'schema': 1, 'provdata': True, 'read_started_at': T(minutes=1), 'sources': {
     'release': ok({'config_sha256': 'e' * 64, 'runtime_revision': 'c' * 40, 'office_revision': 'd' * 40, 'locator': '/Users/x/.runtime/ap10'}),
     'staffing': ok({'executors': {'review': 'claude', 'implementation': 'claude', 'driver': 'codex'}, 'models_run': {'claude': 'modell-a', 'codex': 'modell-b'}, 'watch_model': 'modell-b'}),
     'questions': ok({'items': [{'asked_at': T(hours=5), 'executor': 'codex', 'model': 'modell-b', 'still_selected': True},
                                {'asked_at': T(days=2), 'executor': 'claude', 'model': 'gammal', 'still_selected': False},
                                {'asked_at': T(hours=2), 'executor': 'codex', 'model': 'modell-b', 'still_selected': True, 'provider_said': 'usage limit'}]}),
     'service': ok({'parts': {'daemon': {'identity_matches': True}, 'engine': {'identity_matches': True}, 'worker': {'identity_matches': True}}}),
     'engine': ok({'executions': [{'type': 'ServiceIdentity', 'pending_activities': [], 'pending_workflow_task': False, 'start': T(days=1)} for _ in range(3)] + [
          {'type': 'DevelopmentTask', 'pending_activities': [], 'pending_workflow_task': False, 'start': T(days=3), 'id': RUN_ID},
          {'type': 'DevelopmentTask', 'pending_activities': ['execute_step'], 'pending_workflow_task': False, 'start': T(minutes=20)},
          {'type': 'FiniteAssessment', 'pending_activities': ['review_candidate'], 'pending_workflow_task': False, 'start': T(minutes=5)},
          {'type': 'DevelopmentTask', 'pending_activities': [], 'pending_workflow_task': True, 'start': T(minutes=40)}]}),
     'watch': ok({'native': {'paused': False, 'note': 'AP10 explicit operator resume', 'next_action_times': [T(hours=1), T(hours=-40), T(hours=-16)], 'running': [],
                             'recent': [{'started_at': T(days=2)}, {'started_at': T(days=1)}, {'started_at': T(hours=8)}, {'started_at': T(days=3)}]},
                  'latest': {'reported_at': T(hours=8), 'reviewed': False, 'decision': 'insufficient', 'locator': '/Users/x/.runtime/ap10/rounds/' + RUN_ID},
                  'reviewed': {'reviewed_at': T(days=3), 'decision': 'retain'}, 'refused_for_capacity': True, 'owner_question': None}),
     'office': ok({'main': 'a' * 40, 'main_date': T(hours=1), 'entries': [
          {'id': 'AP08-LEVERANS', 'title': 'redovisningsförmåga', 'text': 'Levererad 2026-09-21. Se evidence/ap08/local/final.json och prov@example.invalid.'},
          {'id': 'AP10-LEVERANS', 'title': 'namngivet bevakningsansvar', 'text': 'Verifierat 2026-09-21, /Users/x/privat.'},
          {'id': 'AP11-AVSLUT-20260924', 'title': 'AP-11 godkänt och avslutat', 'text': 'Status: avslutat.'},
          {'id': 'AP10-SIGNALRATTNING-LEVERANS-20260924', 'title': 'del A levererad och aktiv', 'text': 'Status: registrerat.'},
          {'id': 'AP10-SIGNAL-OCH-AQUARIUM-BEREDNING-20260924', 'title': 'riktad rättning och beredning', 'text': '**Status:** registrerat av kedjedrivaren. Ägarens beslut om två arbeten.'},
          {'id': 'AQUARIUM-V0-BEREDNING-20260924', 'title': 'byggbeslut för Aquarium v0, endast förslag', 'text': '**Status:** berett. **Förslag, inte accepterat.**'},
          {'id': 'XYZ-BEREDNING', 'title': 'ett tidigare förslag', 'text': 'FÖRSLAG till beslut.'},
          {'id': 'XYZ-ACCEPT', 'title': 'accepterat', 'text': 'Ägaren accepterade.'}],
        'notes': [{'ap': 'AP04', 'title': 'AP04 — uppdragskedjan', 'text': 'Levererad 2026-09-20. PRIVATE-MARKER'}, {'ap': 'AP08', 'title': 'AP08 — privat bild', 'text': 'x'}],
        'plan_owner_turn': [{'kind': 'operatörshandling', 'text': 'Aktivera övergång 16', 'since': '2026-09-24'}]}, minutes=2)}}
def keys(d, want, where):
    assert set(d) == set(want), (where, sorted(d), sorted(want))
R = base(); orig = copy.deepcopy(R)
blocked = {'on': False}
def audit(e, a):
    if blocked['on'] and (e == 'open' or e.startswith(('socket.', 'subprocess.', 'os.', 'ctypes.'))): raise AssertionError('projection side effect: ' + e)
sys.addaudithook(audit)
blocked['on'] = True; P = m.project(R, NOW); P2 = m.project(R, NOW); blocked['on'] = False
assert R == orig, 'input mutated'; assert P == P2, 'projection is not deterministic'
keys(P, ['schema', 'provdata', 'read_at', 'sources', 'revisions', 'headline', 'arkivet', 'verkstaden', 'utkiken', 'agarens_bord', 'sockeln'], 'top')
assert P['schema'] == 1 and P['provdata'] is True and P['read_at'] == R['read_started_at']
assert P['revisions'] == {'office_main': 'aaaaaaaa', 'office_main_date': T(hours=1), 'runtime': 'cccccccc', 'config': 'eeeeeeee'}, P['revisions']
titles = {'release': 'Runtime · aktiv release', 'staffing': 'Runtime · bemanning', 'questions': 'Runtime · modellfrågor', 'service': 'Runtime · tjänsten',
          'engine': 'Runtime · motorn', 'watch': 'Runtime · bevakningen', 'office': 'Kontoret · beslut och leveranser'}
keys(P['sources'], titles, 'sources')
for k, s in P['sources'].items():
    keys(s, ['title', 'status', 'read_at', 'stale_after_seconds'], 'source ' + k)
    assert s['title'] == titles[k] and s['status'] == 'ok' and s['read_at'] == R['sources'][k]['read_at']
    assert s['stale_after_seconds'] == (3600 if k == 'office' else 300)
# Arkivet: conservation, keys, dates, order, basis
A = P['arkivet']; keys(A, ['status', 'items'], 'arkivet'); assert A['status'] == 'ok'
got = [(i['key'], i['date'], i['basis']) for i in A['items']]
want = [('AP11', '2026-09-24', 'beslutsloggen AP11-AVSLUT-20260924'), ('AP10-SIGNALRATTNING', '2026-09-24', 'beslutsloggen AP10-SIGNALRATTNING-LEVERANS-20260924'),
        ('AP08', '2026-09-21', 'beslutsloggen AP08-LEVERANS'), ('AP10', '2026-09-21', 'beslutsloggen AP10-LEVERANS'), ('AP04', '2026-09-20', 'leveransbesked AP04')]
assert sorted(got) == sorted(want), got
dates = [d for _, d, _ in got]; assert dates == sorted(dates, reverse=True), dates
x = base(); x['sources']['office']['value']['entries'].append({'id': 'AP99-LEVERANS', 'title': 'odaterad', 'text': 'inget datum'})
assert [i['date'] for i in m.project(x, NOW)['arkivet']['items']][-1] is None
for i in A['items']: keys(i, ['key', 'title', 'date', 'basis'], 'arkivet item')
assert {i['key']: i['title'] for i in A['items']}['AP04'] == 'AP04 — uppdragskedjan'
# Verkstaden: identities and idle are not work; review is granskas; no model evidence
V = P['verkstaden']; keys(V, ['status', 'items', 'model_evidence'], 'verkstaden'); assert V['status'] == 'ok' and V['model_evidence'] is False
assert sorted((i['state'], i['what'], i['since']) for i in V['items']) == sorted([('pågår', 'DevelopmentTask · execute_step', T(minutes=20)), ('granskas', 'FiniteAssessment · review_candidate', T(minutes=5)),
                                                                           ('pågår', 'DevelopmentTask · arbetsflödessteg', T(minutes=40))]), V['items']
for i in V['items']: keys(i, ['state', 'what', 'since'], 'verkstaden item')
# Utkiken
U = P['utkiken']; keys(U, ['status', 'schedule', 'next_planned', 'running', 'starts', 'latest', 'reviewed', 'waiting', 'model'], 'utkiken')
assert U['status'] == 'ok' and U['schedule'] == 'aktiverat' and U['next_planned'] == T(hours=-16) and U['running'] == 0
assert U['starts'] == [T(hours=8), T(days=1), T(days=2)], U['starts']
assert U['latest'] == {'at': T(hours=8), 'outcome': 'genomförd, otillräcklig', 'cause': 'leverantören tog inte emot analysen (kapacitet)'}, U['latest']
assert U['reviewed'] == {'at': T(days=3), 'decision': 'behåll', 'older_than_a_day': True}, U['reviewed']
assert U['waiting'] is True and U['model'] == {'executor': 'codex', 'model': 'modell-b', 'follows_model_choice': False}
x = base(); x['sources']['watch']['value']['native']['note'] = 'STOPPED: AP10 explicit stop'; x['sources']['watch']['value']['native']['paused'] = True
assert m.project(x, NOW)['utkiken']['schedule'] == 'stoppat'
x = base(); x['sources']['watch']['value']['native']['paused'] = True; assert m.project(x, NOW)['utkiken']['schedule'] == 'pausat'
for bad in ('ja', None, 1):
    x = base(); x['sources']['watch']['value']['native']['paused'] = bad; assert m.project(x, NOW)['utkiken']['schedule'] == 'okänt', bad
x = base(); del x['sources']['watch']['value']['native']['paused']; assert m.project(x, NOW)['utkiken']['schedule'] == 'okänt'
x = base(); x['sources']['watch']['value']['native']['next_action_times'] = [T(hours=2), T(minutes=1)]; assert m.project(x, NOW)['utkiken']['next_planned'] is None
for word, sv in (('not_applicable', 'inte tillämpligt'), ('insufficient', 'otillräcklig'), ('okänd_ordning', 'okänd_ordning')):
    x = base(); x['sources']['watch']['value']['reviewed']['decision'] = word; assert m.project(x, NOW)['utkiken']['reviewed']['decision'] == sv, word
x = base(); x['sources']['watch']['value']['refused_for_capacity'] = None; assert m.project(x, NOW)['utkiken']['latest']['cause'] is None
x = base(); w = x['sources']['watch']['value']; w['latest'] = {'reported_at': T(hours=1), 'reviewed': True, 'decision': 'retain'}; w['reviewed'] = {'reviewed_at': T(hours=1), 'decision': 'propose_action'}; w['refused_for_capacity'] = False
u = m.project(x, NOW)['utkiken']; assert u['latest'] == {'at': T(hours=1), 'outcome': 'genomförd, granskad', 'cause': None} and u['waiting'] is False
assert u['reviewed'] == {'at': T(hours=1), 'decision': 'förslag till åtgärd', 'older_than_a_day': False}
# Ägarens bord: open proposal, not accepted, not owner decisions, plan turn, still-selected question only
O = P['agarens_bord']; keys(O, ['status', 'items'], 'agarens_bord'); assert O['status'] == 'ok'
for i in O['items']: keys(i, ['kind', 'text', 'since', 'basis'], 'owner item')
assert sorted((i['kind'], i['text'], i['since'], i['basis']) for i in O['items']) == sorted([
    ('beslut', 'Ta ställning till byggbeslut för Aquarium v0, endast förslag', '2026-09-24', 'beslutsloggen AQUARIUM-V0-BEREDNING-20260924'),
    ('operatörshandling', 'Aktivera övergång 16', '2026-09-24', 'planens ägartur'),
    ('modellfråga', 'Vald modell modell-b för codex tog inte emot anrop: vänta eller byt modell', T(hours=2), 'Runtimes modellfråga')]), O['items']
x = base(); x['sources']['watch']['value']['owner_question'] = 'Ska åtgärden beredas?'
assert [(i['text'], i['since'], i['basis']) for i in m.project(x, NOW)['agarens_bord']['items'] if i['basis'] == 'bevakningens förslag'] == [('Ska åtgärden beredas?', T(hours=8), 'bevakningens förslag')]
x = base(); x['sources']['office']['value']['entries'].append({'id': 'LANG-BEREDNING-20260920', 'title': 'lång beredning', 'text': 'x' * 700 + ' förslag'})
assert not any('lång beredning' in i['text'] for i in m.project(x, NOW)['agarens_bord']['items'])
x = base(); x['sources']['office']['value']['entries'].append({'id': 'KORT-BEREDNING-20260920', 'title': 'kort beredning', 'text': 'Ett Förslag.'})
assert any(i['text'] == 'Ta ställning till kort beredning' and i['since'] == '2026-09-20' for i in m.project(x, NOW)['agarens_bord']['items'])
# Sockeln
S = P['sockeln']; keys(S, ['service', 'staffing', 'watch_staffing', 'idle_tasks', 'identity_records', 'busy'], 'sockeln')
assert S['service'] == {'state': 'igång', 'verified': 3, 'of': 3, 'config': 'eeeeeeee'}, S['service']
assert S['staffing'] == [{'role': 'driver', 'executor': 'codex', 'model': 'modell-b'}, {'role': 'implementation', 'executor': 'claude', 'model': 'modell-a'}, {'role': 'review', 'executor': 'claude', 'model': 'modell-a'}], S['staffing']
assert S['watch_staffing'] == {'executor': 'codex', 'model': 'modell-b'} and (S['idle_tasks'], S['identity_records'], S['busy']) == (1, 3, 3)
for failing, want in ((('worker',), ('delvis', 2)), (('worker', 'engine'), ('delvis', 1)), (('worker', 'engine', 'daemon'), ('okänt', 0))):
    x = base()
    for k in failing: x['sources']['service']['value']['parts'][k]['identity_matches'] = False
    s = m.project(x, NOW)['sockeln']['service']; assert (s['state'], s['verified']) == want, (failing, s)
# Headline
assert P['headline'] == {'pagar': 3, 'vantar': 2, 'behover_dig': 3, 'lugnt': False}, P['headline']
q = base(); q['provdata'] = False; q['sources']['engine']['value']['executions'] = [e for e in q['sources']['engine']['value']['executions'] if not e['pending_activities'] and not e['pending_workflow_task']]
q['sources']['questions']['value']['items'] = []; qw = q['sources']['watch']['value']; qw['latest'] = {'reported_at': T(hours=1), 'reviewed': True, 'decision': 'retain'}; qw['refused_for_capacity'] = False
q['sources']['office']['value']['entries'] = [e for e in q['sources']['office']['value']['entries'] if 'BEREDNING' not in e['id'] or e['id'].startswith('XYZ')]; q['sources']['office']['value']['plan_owner_turn'] = []
Q = m.project(q, NOW); assert Q['headline'] == {'pagar': 0, 'vantar': 0, 'behover_dig': 0, 'lugnt': True} and Q['provdata'] is False, Q['headline']
# Unavailable sources: isolated, never zero work, never quiet
for src, place in (('office', 'arkivet'), ('engine', 'verkstaden'), ('watch', 'utkiken')):
    x = base(); x['sources'][src] = {'status': 'unavailable', 'read_at': T(minutes=1), 'value': None}; X = m.project(x, NOW)
    assert X['sources'][src]['status'] == 'otillgänglig' and X[place]['status'] == 'otillgänglig' and X['headline']['lugnt'] is False
    assert all(X['sources'][k]['status'] == 'ok' for k in X['sources'] if k != src)
    if place in ('arkivet', 'verkstaden'): assert X[place]['items'] == []
    if place == 'utkiken': assert (X['utkiken']['schedule'], X['utkiken']['next_planned'], X['utkiken']['running'], X['utkiken']['starts'], X['utkiken']['latest'], X['utkiken']['reviewed'], X['utkiken']['waiting']) == ('okänt', None, None, [], None, None, False)
    if src == 'engine': assert (X['sockeln']['idle_tasks'], X['sockeln']['identity_records'], X['sockeln']['busy']) == (None, None, None) and X['headline']['pagar'] is None and X['headline']['behover_dig'] == 3
    if src == 'office':
        assert X['agarens_bord']['status'] == 'otillgänglig' and [i['kind'] for i in X['agarens_bord']['items']] == ['modellfråga'] and X['utkiken']['status'] == 'ok' and X['headline']['behover_dig'] is None and X['headline']['pagar'] == 3
        assert X['revisions'] == {'office_main': None, 'office_main_date': None, 'runtime': 'cccccccc', 'config': 'eeeeeeee'}, X['revisions']
    if src == 'watch': assert X['headline']['vantar'] is None and X['headline']['behover_dig'] is None and X['agarens_bord']['status'] == 'otillgänglig'
x = base(); x['sources']['service'] = {'status': 'unavailable', 'read_at': None, 'value': None}; X = m.project(x, NOW)
assert X['sockeln']['service'] == {'state': 'okänt', 'verified': None, 'of': 3, 'config': 'eeeeeeee'}, X['sockeln']['service']
x = base(); x['sources']['staffing'] = {'status': 'unavailable', 'read_at': None, 'value': None}; X = m.project(x, NOW)
assert X['sockeln']['staffing'] == [] and X['sockeln']['watch_staffing']['model'] is None and X['utkiken']['model']['model'] is None
assert X['utkiken']['status'] == 'ok' and X['utkiken']['schedule'] == 'aktiverat' and X['headline']['lugnt'] is False
x = base(); x['sources']['release'] = {'status': 'unavailable', 'read_at': None, 'value': None}; X = m.project(x, NOW)
assert X['revisions'] == {'office_main': 'aaaaaaaa', 'office_main_date': T(hours=1), 'runtime': None, 'config': None} and X['sockeln']['service']['config'] is None, X['revisions']
# Display safety
blob = json.dumps(P, ensure_ascii=False)
for bad in PRIVATE: assert bad not in blob, bad
assert not re.search(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', blob)
for bad_input in [dict(base(), schema=2), dict(base(), sources={})]:
    try: m.project(bad_input, NOW)
    except ValueError as e: assert 'PRIVATE' not in str(e)
    else: raise AssertionError('invalid readings accepted')
try: m.project(base(), datetime(2026, 9, 24, 15, 0))
except ValueError: pass
else: raise AssertionError('naive now accepted')
# collect with injected readers: isolation and read times
def probe(root): return {'release': {'ok': True, 'value': {'config_sha256': 'e' * 64, 'runtime_revision': 'c' * 40, 'office_revision': 'd' * 40}}, 'staffing': {'ok': False},
                         'questions': {'ok': True, 'value': {'items': []}}, 'service': {'ok': True, 'value': {'parts': {k: {'identity_matches': True} for k in ('daemon', 'engine', 'worker')}}},
                         'engine': {'ok': True, 'value': {'executions': []}}, 'refusal': {'ok': True, 'value': {'capacity': False}}}
def broken_watch(root): raise OSError('PRIVATE-MARKER /Users/x')
def office(root): return {'main': 'a' * 40, 'main_date': T(hours=1), 'entries': [], 'notes': [], 'plan_owner_turn': []}
C = m.collect(pathlib.Path('/nonexistent/runtime'), pathlib.Path('.'), runtime_probe=probe, watch_reader=broken_watch, office_reader=office)
assert C['provdata'] is False and C['schema'] == 1 and datetime.fromisoformat(C['read_started_at']).utcoffset() is not None
st = {k: v['status'] for k, v in C['sources'].items()}
assert st == {'release': 'ok', 'staffing': 'unavailable', 'questions': 'ok', 'service': 'ok', 'engine': 'ok', 'watch': 'unavailable', 'office': 'ok'}, st
assert all(datetime.fromisoformat(v['read_at']).utcoffset() is not None for v in C['sources'].values())
assert 'PRIVATE-MARKER' not in json.dumps(C)
m.project(C, NOW)
def bad_probe(root): raise OSError('PRIVATE-MARKER')
C = m.collect(pathlib.Path('/nonexistent/runtime'), pathlib.Path('.'), runtime_probe=bad_probe, watch_reader=broken_watch, office_reader=lambda r: {'garbage': True})
assert all(v['status'] == 'unavailable' for v in C['sources'].values()), C['sources']
Z = m.project(C, NOW); assert Z['headline']['lugnt'] is False and 'PRIVATE-MARKER' not in json.dumps(Z)
# the probe constant is the brief's section 4 block (its SHA-256 after stripping; Runtime's verification workspace holds no TASK.md)
import hashlib
assert hashlib.sha256(m.PROBE.strip().encode('utf-8')).hexdigest() == 'e99f4882fd46daf34325879bfb70ecdb2a9880f796be3a3b2496233d5b074d84', 'PROBE is not the brief constant'
# command: exclusive private output, unavailable sources are not a failure, fixed error
with tempfile.TemporaryDirectory(dir='.scratch', prefix='aquarium-') as td:
    root = pathlib.Path(td); out = root / 'ny'
    env = {k: v for k, v in os.environ.items() if k in ('PATH', 'HOME', 'LANG', 'TMPDIR')}
    p = subprocess.run([sys.executable, '-I', '-B', 'tools/aquarium.py', str(out)], capture_output=True, text=True, timeout=120, env=env)
    assert p.returncode == 0 and p.stdout == '' , (p.returncode, p.stderr[-2000:])
    assert (out.stat().st_mode & 0o777) == 0o700 and ((out / 'projection.json').stat().st_mode & 0o777) == 0o600
    text = (out / 'projection.json').read_text(encoding='utf-8'); J = json.loads(text)
    assert J['schema'] == 1 and J['provdata'] is False and set(J['sources']) == set(titles)
    assert text == json.dumps(J, ensure_ascii=False, indent=1, sort_keys=True) + '\n', 'projection.json is not in the stated form'
    p = subprocess.run([sys.executable, '-I', '-B', 'tools/aquarium.py', str(out)], capture_output=True, text=True, timeout=120, env=env)
    assert p.returncode == 2 and p.stderr.strip() == 'Kunde inte skapa Aquariums projektion.' and str(root) not in p.stderr + p.stdout
    link = root / 'lank'; link.symlink_to(root, target_is_directory=True)
    p = subprocess.run([sys.executable, '-I', '-B', 'tools/aquarium.py', str(link / 'x')], capture_output=True, text=True, timeout=120, env=env)
    assert p.returncode == 2 and not (root / 'x').exists()
    p = subprocess.run([sys.executable, '-I', '-B', 'tools/aquarium.py', str(root / 'saknas' / 'ny')], capture_output=True, text=True, timeout=120, env=env)
    assert p.returncode == 2 and not (root / 'saknas').exists() and p.stderr.strip() == 'Kunde inte skapa Aquariums projektion.'
# the candidate's own tests pass
before = sorted(os.listdir('.scratch'))
p = subprocess.run([sys.executable, '-I', '-B', '-m', 'unittest', 'discover', '-s', 'tools', '-p', 'test_aquarium.py'], capture_output=True, text=True, timeout=300)
assert p.returncode == 0, p.stderr[-3000:]
assert sorted(os.listdir('.scratch')) == before, 'tests left files in .scratch'
doc = pathlib.Path('tools/AQUARIUM.md').read_text()
assert 'aquarium.py' in doc and len(doc) > 1500, 'AQUARIUM.md does not document the command'
print(json.dumps({'passed': True, 'checks': ['Pure deterministic projection with exact output schema', 'Deliveries conserved, keyed, dated and ordered from the decision log and notes',
  'Engine work from pending activities and pending workflow tasks, never from identities, idle executions or model evidence',
  'Watch schedule (unknown without a boolean), earliest later plan vs performed, latest outcome and cause, reviewed decision keeps its date',
  'Owner items only from open proposals, the plan block, still-selected D030 questions once per model and the watch, each with basis',
  'Service verified only by matching identities; none verified is unknown', 'Read revisions of the office and the release',
  'Per-source availability isolated; never zero work, never quiet',
  'Display safety: no paths, run ids, provider text or addresses', 'Collector readers isolated per source', 'Exclusive private command output in the stated form and fixed error', 'Candidate tests pass and leave .scratch as they found it'],
  'scope': 'Reading and projection on synthetic data only; the real read path and the rendered view are verified separately by the host'}))
'''
def verify(candidate):
    from runtime.profile import sandbox_command, environment
    p = subprocess.run(sandbox_command(Path(candidate), ['/opt/homebrew/bin/python3.12', '-I', '-B', '-c', SCRIPT]), env=environment(), capture_output=True, text=True, timeout=600)
    if p.returncode:
        return {'passed': False, 'reason': 'Aquarium projection host contract failed', 'stderr': p.stderr[-6000:]}
    try:
        return json.loads(p.stdout)
    except ValueError:
        return {'passed': False, 'reason': 'Missing host acceptance result'}
