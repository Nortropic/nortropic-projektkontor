"""Aquarium v0: bounded read-only reading of the office and Runtime, projected display-safe.

Import is inert. `project` is pure: it never imports, opens, reads or runs anything;
`collect` does the bounded real reading through replaceable readers. Nothing here starts,
approves, switches or changes anything.
"""
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys

SCHEMA = 2
ERROR = 'Ogiltigt underlag för Aquariums projektion.'
COMMAND_ERROR = 'Kunde inte skapa Aquariums projektion.'
FAILURES = (OSError, ValueError, TypeError, KeyError, IndexError, OverflowError, RecursionError)

PROBE_SOURCES = ('release', 'staffing', 'questions', 'service', 'engine')
RUNTIME_SOURCES = PROBE_SOURCES + ('tasks',)
SOURCES = RUNTIME_SOURCES + ('watch', 'office')
TITLES = {'release': 'Runtime · aktiv release', 'staffing': 'Runtime · bemanning',
          'questions': 'Runtime · modellfrågor', 'service': 'Runtime · tjänsten',
          'engine': 'Runtime · motorn', 'tasks': 'Runtime · uppdragsfiler',
          'watch': 'Runtime · bevakningen',
          'office': 'Kontoret · beslut och leveranser'}
STALE_RUNTIME = 300
STALE_OFFICE = 3600
SERVICE_PARTS = ('daemon', 'engine', 'worker')
NOT_WORK = ('ServiceIdentity', 'PrivateAssessment')
IDENTITY_TYPE = 'ServiceIdentity'
TASK_LIMIT = 32
TASK_BYTES = 512
TITLE_LIMIT = 120
CAPACITY_CAUSE = 'leverantören tog inte emot analysen (kapacitet)'
DECISIONS = {'retain': 'behåll', 'not_applicable': 'inte tillämpligt',
             'insufficient': 'otillräcklig', 'propose_action': 'förslag till åtgärd'}
WATCH_EXECUTOR = 'codex'
PROBE_TIMEOUT = 30
GIT_TIMEOUT = 30
PROPOSAL_WINDOW = 600

PROBE = """import asyncio, json
from pathlib import Path
out = {}
def part(name, fn):
    try:
        out[name] = {'ok': True, 'value': fn()}
    except Exception:
        out[name] = {'ok': False}
def release_part():
    from runtime.release import installed
    c = installed()
    return {'config_sha256': c['config_sha256'], 'runtime_revision': c['runtime_revision'], 'office_revision': c['office_revision']}
def staffing_part():
    from runtime.release import installed
    from runtime.development_model import executors, models
    from runtime import profile
    c = installed()
    return {'executors': executors(c), 'models_run': models(c), 'watch_model': getattr(profile, 'MODEL', None)}
def questions_part():
    from runtime.release import installed
    from runtime.development_model import models
    from runtime import model_question
    running = models(installed())
    found = model_question.recent()
    if any(q.get('unreadable') for q in found):
        raise ValueError('unreadable question record')
    return {'items': [{'asked_at': q.get('asked_at'), 'executor': q.get('executor'), 'model': q.get('model'),
                       'still_selected': q.get('model') is not None and running.get(q.get('executor')) == q.get('model')}
                      for q in found]}
def service_part():
    from runtime.release import ROOT
    from runtime.shared import process_identity
    s = json.loads((ROOT / '.runtime/ap10/service.json').read_text())
    return {'parts': {k: {'identity_matches': bool(s[k].get('identity')) and process_identity(s[k]['pid']) == s[k]['identity']}
                      for k in ('daemon', 'engine', 'worker')}}
def engine_part():
    from temporalio.client import Client
    async def run():
        client = await Client.connect('127.0.0.1:7339', namespace='nortropic-runtime')
        rows = []
        async for e in client.list_workflows('ExecutionStatus = "Running"'):
            raw = (await client.get_workflow_handle(e.id, run_id=e.run_id).describe()).raw_description
            rows.append({'id': e.id, 'type': e.workflow_type, 'pending_activities': [a.activity_type.name for a in raw.pending_activities],
                         'pending_workflow_task': raw.HasField('pending_workflow_task'),
                         'start': e.start_time.isoformat() if e.start_time else None})
        return {'executions': rows}
    return asyncio.run(run())
def refusal_part():
    from runtime.release import ROOT
    from runtime.development_model import capacity_lost
    rounds = [p for p in (ROOT / '.runtime/ap10/rounds').iterdir() if (p / 'report/result.json').is_file()]
    latest = max(rounds, key=lambda p: json.loads((p / 'report/result.json').read_text()).get('reported_at') or '')
    events = latest / 'analysis/events.jsonl'
    rows = [json.loads(l) for l in events.read_text().splitlines() if l.strip()] if events.is_file() else []
    return {'capacity': bool(capacity_lost('codex', rows))}
for name, fn in (('release', release_part), ('staffing', staffing_part), ('questions', questions_part),
                 ('service', service_part), ('engine', engine_part), ('refusal', refusal_part)):
    part(name, fn)
print(json.dumps(out))
"""

# Display safety: paths, run or thread identifiers and e-mail addresses never reach the view.
HIDDEN = '[dolt]'
_UNSAFE = re.compile(
    r'/Users/\S*|/private/\S*|/home/\S*|\.runtime\S*|evidence/\S*local\S*'
    r'|[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}'
    r'|[^\s@]+@[^\s@]+\.[^\s@]+')
# A date is `YYYY-MM-DD` with no digit beside it, or `YYYYMMDD` with no letter or digit
# beside it, so an eight-digit run inside a commit hash or digest is never a date.
_DATE = re.compile(r'(?<!\d)(\d{4})-(\d{2})-(\d{2})(?!\d)'
                   r'|(?<![0-9A-Za-z])(\d{4})(\d{2})(\d{2})(?![0-9A-Za-z])')
_SINCE = re.compile(r'\s*—\s*sedan\s+(\d{4}-\d{2}-\d{2})\s*$')
_TASK_ID = re.compile(r'[a-z0-9][a-z0-9-]{0,79}')
_WHITESPACE = re.compile(r'\s+')


def _fail():
    raise ValueError(ERROR)


def _dict(value):
    if type(value) is not dict:
        _fail()
    return value


def _list(value):
    if type(value) is not list:
        _fail()
    return value


def _string(value):
    if type(value) is not str:
        _fail()
    return value


def _optional_string(value):
    if value is not None and type(value) is not str:
        _fail()
    return value


def _flag(value):
    if type(value) is not bool:
        _fail()
    return value


def _hex(value, length):
    if type(value) is not str or re.fullmatch('[0-9a-f]{%d}' % length, value) is None:
        _fail()
    return value


def _aware(value):
    """An aware ISO 8601 point in time; naive or unparsable input is invalid."""
    if type(value) is not str:
        _fail()
    try:
        parsed = datetime.fromisoformat(value)
    except (ValueError, TypeError):
        _fail()
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        _fail()
    return parsed


def _iso(value):
    _aware(value)
    return value


def _optional_iso(value):
    return None if value is None else _iso(value)


def _moment(value):
    """A lenient time: an observation that cannot be read is skipped, never an error."""
    if type(value) is not str:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except (ValueError, TypeError):
        return None
    return parsed if parsed.tzinfo is not None and parsed.utcoffset() is not None else None


def _display_safe(value):
    if type(value) is str:
        return _UNSAFE.sub(HIDDEN, value)
    if type(value) is list:
        return [_display_safe(item) for item in value]
    if type(value) is dict:
        return {key: _display_safe(item) for key, item in value.items()}
    return value


# --- input shapes -----------------------------------------------------------------


def _release_value(value):
    value = _dict(value)
    return {'config_sha256': _hex(value.get('config_sha256'), 64),
            'runtime_revision': _hex(value.get('runtime_revision'), 40),
            'office_revision': _hex(value.get('office_revision'), 40)}


def _staffing_value(value):
    value = _dict(value)
    executors = _dict(value.get('executors'))
    models_run = _dict(value.get('models_run'))
    for role, executor in executors.items():
        _string(role)
        if executor not in ('claude', 'codex'):
            _fail()
    for name, model in models_run.items():
        _string(name)
        _optional_string(model)
    return {'executors': dict(executors), 'models_run': dict(models_run),
            'watch_model': _optional_string(value.get('watch_model'))}


def _questions_value(value):
    value = _dict(value)
    items = []
    for item in _list(value.get('items')):
        item = _dict(item)
        items.append({'asked_at': _optional_iso(item.get('asked_at')),
                      'executor': _optional_string(item.get('executor')),
                      'model': _optional_string(item.get('model')),
                      'still_selected': _flag(item.get('still_selected'))})
    return {'items': items}


def _service_value(value):
    value = _dict(value)
    parts = _dict(value.get('parts'))
    return {'parts': {name: {'identity_matches': _flag(_dict(parts.get(name)).get('identity_matches'))}
                      for name in SERVICE_PARTS}}


def _engine_value(value):
    value = _dict(value)
    executions = []
    for item in _list(value.get('executions')):
        item = _dict(item)
        activities = [_string(name) for name in _list(item.get('pending_activities'))]
        executions.append({'id': _string(item.get('id')), 'type': _string(item.get('type')),
                           'pending_activities': activities,
                           'pending_workflow_task': _flag(item.get('pending_workflow_task')),
                           'start': _optional_iso(item.get('start'))})
    return {'executions': executions}


def _tasks_value(value):
    """One item per asked task id: a title exactly when the brief could be read."""
    value = _dict(value)
    items = []
    for item in _list(value.get('items')):
        item = _dict(item)
        status = item.get('status')
        if status not in ('läst', 'saknas', 'oläslig'):
            _fail()
        title = item.get('title')
        if status == 'läst':
            _string(title)
        elif title is not None:
            _fail()
        items.append({'id': _string(item.get('id')), 'title': title, 'status': status})
    return {'items': items}


def _watch_value(value):
    value = _dict(value)
    native = _dict(value.get('native'))
    # The watch view's own rule: `paused` and `note` are observations, never validated away.
    times = [item for item in _list(native.get('next_action_times', [])) if type(item) is str]
    running = _list(native.get('running', []))
    recent = []
    for item in _list(native.get('recent', [])):
        if type(item) is dict and type(item.get('started_at')) is str:
            recent.append({'started_at': item['started_at']})
    latest = value.get('latest')
    if latest is not None:
        latest = _dict(latest)
        latest = {'reported_at': _iso(latest.get('reported_at')), 'reviewed': _flag(latest.get('reviewed')),
                  'decision': _optional_string(latest.get('decision'))}
    reviewed = value.get('reviewed')
    if reviewed is not None:
        reviewed = _dict(reviewed)
        reviewed = {'reviewed_at': _iso(reviewed.get('reviewed_at')),
                    'decision': _optional_string(reviewed.get('decision'))}
    refused = value.get('refused_for_capacity')
    if refused is not None and type(refused) is not bool:
        _fail()
    return {'native': {'paused': native.get('paused'), 'note': native.get('note'),
                       'next_action_times': times, 'running': list(running), 'recent': recent},
            'latest': latest, 'reviewed': reviewed, 'refused_for_capacity': refused,
            'owner_question': _optional_string(value.get('owner_question'))}


def _office_value(value):
    value = _dict(value)
    entries = []
    for item in _list(value.get('entries')):
        item = _dict(item)
        entries.append({'id': _string(item.get('id')), 'title': _string(item.get('title')),
                        'text': _string(item.get('text'))})
    notes = []
    for item in _list(value.get('notes')):
        item = _dict(item)
        notes.append({'ap': _string(item.get('ap')), 'title': _string(item.get('title')),
                      'text': _string(item.get('text'))})
    turns = []
    for item in _list(value.get('plan_owner_turn')):
        item = _dict(item)
        if item.get('kind') not in ('beslut', 'operatörshandling'):
            _fail()
        turns.append({'kind': item['kind'], 'text': _string(item.get('text')),
                      'since': _optional_string(item.get('since'))})
    return {'main': _hex(value.get('main'), 40), 'main_date': _iso(value.get('main_date')),
            'entries': entries, 'notes': notes, 'plan_owner_turn': turns}


VALUES = {'release': _release_value, 'staffing': _staffing_value, 'questions': _questions_value,
          'service': _service_value, 'engine': _engine_value, 'tasks': _tasks_value,
          'watch': _watch_value, 'office': _office_value}


def _validated(readings, now):
    """Validate the envelope and copy only the documented keys; extras are ignored."""
    if not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() is None:
        _fail()
    readings = _dict(readings)
    for key in ('schema', 'provdata', 'read_started_at', 'sources'):
        if key not in readings:
            _fail()
    if type(readings['schema']) is not int or readings['schema'] != SCHEMA:
        _fail()
    _flag(readings['provdata'])
    _iso(readings['read_started_at'])
    sources = _dict(readings['sources'])
    result = {}
    for name in SOURCES:
        if name not in sources:
            _fail()
        source = _dict(sources[name])
        if source.get('status') not in ('ok', 'unavailable'):
            _fail()
        if 'read_at' not in source or 'value' not in source:
            _fail()
        read_at = source['read_at']
        if read_at is not None:
            _iso(read_at)
        value = VALUES[name](source['value']) if source['status'] == 'ok' else None
        result[name] = {'status': source['status'], 'read_at': read_at, 'value': value}
    return {'schema': SCHEMA, 'provdata': readings['provdata'],
            'read_started_at': readings['read_started_at'], 'sources': result}


# --- the places -------------------------------------------------------------------


def _calendar_date(year, month, day):
    """A real calendar date from 2000-01-01 to 2099-12-31, else None."""
    if not 2000 <= year <= 2099:
        return None
    try:
        datetime(year, month, day)
    except ValueError:
        return None
    return '%04d-%02d-%02d' % (year, month, day)


def _date_in(text):
    """The first real date in one text; a candidate that is no date is skipped."""
    if type(text) is not str:
        return None
    for found in _DATE.finditer(text):
        parts = found.groups()
        year, month, day = parts[0:3] if parts[0] is not None else parts[3:6]
        date = _calendar_date(int(year), int(month), int(day))
        if date is not None:
            return date
    return None


def _first_date(*texts):
    for text in texts:
        date = _date_in(text)
        if date is not None:
            return date
    return None


def _delivery_key(identity):
    """A delivered or closed commitment, named by the part of the id before its marker."""
    if '-LEVERANS-' in identity:
        key = identity.split('-LEVERANS-')[0]
    elif identity.endswith('-LEVERANS'):
        key = identity[:-len('-LEVERANS')]
    elif '-AVSLUT' in identity:
        key = identity.split('-AVSLUT')[0]
    else:
        return None
    return key or None


def _arkivet(available, office):
    if not available:
        return {'status': 'otillgänglig', 'items': []}
    items, delivered = [], set()
    for entry in office['entries']:
        key = _delivery_key(entry['id'])
        if key is None:
            continue
        delivered.add(key)
        items.append({'key': key, 'title': entry['title'],
                      'date': _first_date(entry['id'], entry['text']),
                      'basis': 'beslutsloggen ' + entry['id']})
    for note in office['notes']:
        if note['ap'] in delivered:
            continue
        items.append({'key': note['ap'], 'title': note['title'],
                      'date': _first_date(note['ap'], note['text']),
                      'basis': 'leveransbesked ' + note['ap']})
    dated = sorted([item for item in items if item['date']], key=lambda item: item['date'], reverse=True)
    return {'status': 'ok', 'items': dated + [item for item in items if not item['date']]}


def _short(identity):
    """The task name without the office's prefix; a bare prefix keeps its own name."""
    prefix = 'office-'
    return identity[len(prefix):] if identity.startswith(prefix) and len(identity) > len(prefix) \
        else identity


def _step(pending):
    """Step, state and executor from the pending activity names only, never from configuration."""
    if any('review' in name.lower() for name in pending):
        return 'granskning', 'granskas', None
    if 'execute_claude' in pending or 'execute_codex' in pending:
        named = [name for name in ('claude', 'codex') if 'execute_' + name in pending]
        return 'utförande', 'pågår', named[0] if len(named) == 1 else None
    if 'publish_candidate' in pending:
        return 'integration', 'integreras', None
    if pending:
        return 'steg', 'pågår', None
    return 'arbetsflödessteg', 'pågår', None


def _is_parked(execution):
    """A task in the engine that is neither work nor a technical record."""
    return (execution['type'] not in NOT_WORK and not execution['pending_activities']
            and not execution['pending_workflow_task'])


def _parked_ids(engine):
    """The parked tasks' ids in engine order, without repetition, at most the first 32."""
    identities = []
    for execution in engine['executions']:
        if _is_parked(execution) and execution['id'] not in identities:
            identities.append(execution['id'])
    return identities[:TASK_LIMIT]


def _work_and_parked(engine, titles_available, tasks):
    """Work items and parked tasks from one engine reading, in engine order."""
    titles = {}
    if titles_available:
        for item in tasks['items']:
            titles.setdefault(item['id'], item)
    work, parked = [], []
    for execution in engine['executions']:
        if execution['type'] in NOT_WORK:
            continue  # A technical identity record and the watch's own round are not work.
        shared = {'task': execution['id'], 'short': _short(execution['id']),
                  'type': execution['type'], 'since': execution['start']}
        pending = execution['pending_activities']
        if pending or execution['pending_workflow_task']:
            step, state, executor = _step(pending)
            work.append(dict(shared, step=step, state=state, executor=executor,
                             executor_basis=None if executor is None
                             else 'motorns steg execute_' + executor,
                             activities=list(pending)))
        elif not titles_available:
            parked.append(dict(shared, title=None, title_status='okänd'))
        else:
            item = titles.get(execution['id'])
            parked.append(dict(shared, title=None if item is None else item['title'],
                               title_status='oläslig' if item is None else item['status']))
    return work, parked


def _utkiken(available, watch, staffing_available, staffing, now):
    model = {'executor': WATCH_EXECUTOR,
             'model': staffing['watch_model'] if staffing_available else None,
             'follows_model_choice': False}
    if not available:
        return {'status': 'otillgänglig', 'schedule': 'okänt', 'next_planned': None, 'running': None,
                'starts': [], 'latest': None, 'reviewed': None, 'waiting': False, 'model': model}
    native = watch['native']
    note, paused = native['note'], native['paused']
    if type(note) is str and note.startswith('STOPPED'):
        schedule = 'stoppat'
    elif paused is True:
        schedule = 'pausat'
    elif paused is False:
        schedule = 'aktiverat'
    else:
        schedule = 'okänt'
    planned = [(moment, value) for moment, value in
               ((_moment(value), value) for value in native['next_action_times'])
               if moment is not None and moment > now]
    starts = [(moment, item['started_at']) for moment, item in
              ((_moment(item['started_at']), item) for item in native['recent']) if moment is not None]
    starts.sort(key=lambda pair: pair[0], reverse=True)
    latest = None
    if watch['latest'] is not None:
        outcome = 'genomförd, granskad' if watch['latest']['reviewed'] else 'genomförd, otillräcklig'
        latest = {'at': watch['latest']['reported_at'], 'outcome': outcome,
                  'cause': CAPACITY_CAUSE if watch['refused_for_capacity'] is True else None}
    reviewed = None
    if watch['reviewed'] is not None:
        decision = watch['reviewed']['decision']
        moment = _moment(watch['reviewed']['reviewed_at'])
        reviewed = {'at': watch['reviewed']['reviewed_at'],
                    'decision': DECISIONS.get(decision, decision),
                    'older_than_a_day': moment is not None and now - moment > timedelta(days=1)}
    return {'status': 'ok', 'schedule': schedule,
            'next_planned': min(planned)[1] if planned else None,
            'running': len(native['running']), 'starts': [value for _, value in starts[:3]],
            'latest': latest, 'reviewed': reviewed,
            'waiting': watch['latest'] is not None and watch['latest']['reviewed'] is not True,
            'model': model}


def _model_questions(questions):
    """One question per distinct executor and model that is still the selected one."""
    pairs, newest, items = {}, {}, []
    for item in questions['items']:
        if item['still_selected'] is not True:
            continue
        pair = (item['executor'], item['model'])
        if pair not in pairs:
            pairs[pair], newest[pair] = None, None
            items.append(pair)
        moment = _moment(item['asked_at'])
        if moment is not None and (newest[pair] is None or moment > newest[pair]):
            newest[pair], pairs[pair] = moment, item['asked_at']
    return [{'kind': 'modellfråga',
             'text': 'Vald modell ' + str(model) + ' för ' + str(executor)
                     + ' tog inte emot anrop: vänta eller byt modell',
             'since': pairs[(executor, model)], 'basis': 'Runtimes modellfråga'}
            for executor, model in items]


def _owner_items(available, values):
    items = []
    if available['office']:
        entries = values['office']['entries']
        accepts = [entry['id'] for entry in entries]
        for entry in entries:
            if '-BEREDNING' not in entry['id']:
                continue
            if 'förslag' not in entry['text'][:PROPOSAL_WINDOW].lower():
                continue
            prefix = entry['id'].split('-BEREDNING')[0] + '-ACCEPT'
            if any(other.startswith(prefix) for other in accepts):
                continue
            items.append({'kind': 'beslut', 'text': 'Ta ställning till ' + entry['title'],
                          'since': _first_date(entry['id'], entry['text']),
                          'basis': 'beslutsloggen ' + entry['id']})
        for turn in values['office']['plan_owner_turn']:
            items.append({'kind': turn['kind'], 'text': turn['text'], 'since': turn['since'],
                          'basis': 'planens ägartur'})
    questions = _model_questions(values['questions']) if available['questions'] else []
    items.extend(questions)
    if available['watch'] and values['watch']['owner_question'] is not None:
        latest = values['watch']['latest']
        items.append({'kind': 'beslut', 'text': values['watch']['owner_question'],
                      'since': latest['reported_at'] if latest is not None else None,
                      'basis': 'bevakningens förslag'})
    return items, len(questions)


def _sockeln(available, values, work, parked):
    if available['service']:
        matches = sum(1 for name in SERVICE_PARTS
                      if values['service']['parts'][name]['identity_matches'])
        state = 'igång' if matches == 3 else 'delvis' if matches else 'okänt'
        verified = matches
    else:
        state, verified = 'okänt', None
    service = {'state': state, 'verified': verified, 'of': 3,
               'config': values['release']['config_sha256'][:8] if available['release'] else None}
    staffing, watch_staffing = [], {'executor': WATCH_EXECUTOR, 'model': None}
    if available['staffing']:
        models_run = values['staffing']['models_run']
        staffing = [{'role': role, 'executor': executor, 'model': models_run.get(executor)}
                    for role, executor in sorted(values['staffing']['executors'].items())]
        watch_staffing = {'executor': WATCH_EXECUTOR, 'model': values['staffing']['watch_model']}
    idle = identities = busy = None
    if available['engine']:
        identities = sum(1 for execution in values['engine']['executions']
                         if execution['type'] == IDENTITY_TYPE)
        idle, busy = len(parked), len(work)
    return {'service': service, 'staffing': staffing, 'watch_staffing': watch_staffing,
            'idle_tasks': idle, 'identity_records': identities, 'busy': busy}


def project(readings, now):
    """Pure projection of one reading. No file, clock, process or network access."""
    data = _validated(readings, now)
    available = {name: data['sources'][name]['status'] == 'ok' for name in SOURCES}
    values = {name: data['sources'][name]['value'] for name in SOURCES}

    sources = {name: {'title': TITLES[name], 'status': 'ok' if available[name] else 'otillgänglig',
                      'read_at': data['sources'][name]['read_at'],
                      'stale_after_seconds': STALE_OFFICE if name == 'office' else STALE_RUNTIME}
               for name in SOURCES}
    revisions = {
        'office_main': values['office']['main'][:8] if available['office'] else None,
        'office_main_date': values['office']['main_date'] if available['office'] else None,
        'runtime': values['release']['runtime_revision'][:8] if available['release'] else None,
        'config': values['release']['config_sha256'][:8] if available['release'] else None}

    arkivet = _arkivet(available['office'], values['office'])
    work, parked = (_work_and_parked(values['engine'], available['tasks'], values['tasks'])
                    if available['engine'] else ([], []))
    verkstaden = {'status': 'ok' if available['engine'] else 'otillgänglig', 'items': work,
                  'parked': parked, 'titles': 'ok' if available['tasks'] else 'otillgänglig'}
    utkiken = _utkiken(available['watch'], values['watch'], available['staffing'],
                       values['staffing'], now)
    owner, questions = _owner_items(available, values)
    agarens_bord = {'status': 'ok' if all(available[name] for name in ('office', 'questions', 'watch'))
                    else 'otillgänglig', 'items': owner}

    # An unknown count is never shown as zero work.
    pagar = len(work) if available['engine'] else None
    vantar = ((1 if utkiken['waiting'] else 0) + questions
              if available['watch'] and available['questions'] else None)
    behover_dig = len(owner) if agarens_bord['status'] == 'ok' else None
    headline = {'pagar': pagar, 'vantar': vantar, 'behover_dig': behover_dig,
                'lugnt': pagar == 0 and vantar == 0 and behover_dig == 0
                         and all(available[name] for name in SOURCES)}

    return _display_safe({'schema': SCHEMA, 'provdata': data['provdata'],
                          'read_at': data['read_started_at'], 'sources': sources,
                          'revisions': revisions, 'headline': headline, 'arkivet': arkivet,
                          'verkstaden': verkstaden, 'utkiken': utkiken,
                          'agarens_bord': agarens_bord,
                          'sockeln': _sockeln(available, values, work, parked)})


# --- bounded real reading ---------------------------------------------------------


def _now():
    return datetime.now(timezone.utc).isoformat()


def _environment(**extra):
    env = {key: os.environ[key] for key in ('PATH', 'HOME', 'USER', 'LOGNAME', 'LANG', 'TMPDIR')
           if key in os.environ}
    env.update(PYTHONDONTWRITEBYTECODE='1', LC_ALL='C')
    env.update(extra)
    return env


def _read_file(path):
    fd = os.open(str(path), os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode):
            _fail()
        return stream.read(8 * 1024 * 1024)


def runtime_probe(runtime_root):
    """Run the frozen release's own code once, bounded, and return its JSON parts."""
    root = Path(runtime_root).absolute()
    active = json.loads(_read_file(root / '.runtime/ap10/active.json').decode('utf-8'))
    pointer = active['config']
    if type(pointer) is not str or not pointer:
        _fail()
    path = Path(pointer) if pointer.startswith('/') else root / pointer
    launcher = root / '.runtime/temporal-venv/bin/python'
    result = subprocess.run([str(launcher), '-B', '-c', PROBE], cwd=str(path.parent / 'runtime'),
                            shell=False, capture_output=True, text=True, encoding='utf-8',
                            errors='replace', timeout=PROBE_TIMEOUT,
                            env=_environment(NR_HOST_ROOT=str(root),
                                             NR_CONFIG_SHA256=str(active['sha256'])))
    if result.returncode != 0:
        _fail()
    return json.loads(result.stdout)


def _brief_title(root, identity):
    """Open only `.runtime/tasks/<id>/brief.md`, component by component, and keep its title line."""
    descriptors = []
    try:
        try:
            descriptors.append(os.open(str(root), os.O_RDONLY | os.O_DIRECTORY))
            for name in ('.runtime', 'tasks', identity):
                descriptors.append(os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                                           dir_fd=descriptors[-1]))
            descriptors.append(os.open('brief.md', os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                                       dir_fd=descriptors[-1]))
        except FileNotFoundError:
            return None, 'saknas'
        except OSError:
            return None, 'oläslig'
        try:
            # A directory opens but cannot be read as a file: check before reading or wrapping.
            if not stat.S_ISREG(os.fstat(descriptors[-1]).st_mode):
                return None, 'oläslig'
            raw = b''
            while len(raw) < TASK_BYTES:  # At most 512 bytes, and no more than the first line.
                chunk = os.read(descriptors[-1], TASK_BYTES - len(raw))
                if not chunk:
                    break
                raw += chunk
                if b'\n' in raw:
                    break
        except OSError:
            return None, 'oläslig'
    finally:
        for descriptor in descriptors:
            os.close(descriptor)
    try:
        line = raw.split(b'\n', 1)[0].decode('utf-8')
    except UnicodeDecodeError:
        return None, 'oläslig'
    if line.endswith('\r'):
        line = line[:-1]
    if not line.startswith('# ') or not line[2:].strip():
        return None, 'oläslig'
    title = _WHITESPACE.sub(' ', line[2:]).strip()
    return (title if len(title) <= TITLE_LIMIT else title[:TITLE_LIMIT - 1] + '…'), 'läst'


def task_reader(runtime_root, identities):
    """The title line of each named task's brief: no listing, no other file, nothing else kept."""
    root = Path(runtime_root).absolute()
    items = []
    for identity in list(identities)[:TASK_LIMIT]:
        if type(identity) is not str or _TASK_ID.fullmatch(identity) is None:
            items.append({'id': identity, 'title': None, 'status': 'oläslig'})
            continue
        title, status = _brief_title(root, identity)
        items.append({'id': identity, 'title': title, 'status': status})
    return {'items': items}


def watch_reader(runtime_root):
    """The office's existing watch reading; imported here so importing aquarium is inert."""
    import bevakningsbild
    values = bevakningsbild.collect(runtime_root)
    question = None
    try:
        seen = bevakningsbild.view(values['native'], values['latest'], values['reviewed'], _now())
        if seen['owner_decision']['needed'] == 'yes':
            question = seen['owner_decision']['question']
    except Exception:
        question = None  # A question that cannot be read is no owner question.
    return dict(values, owner_question=question)


def _report_fields(wrapper):
    """Keep only the four documented report fields; a damaged wrapper is unavailable."""
    if wrapper is None:
        return None
    wrapper = _dict(wrapper)
    row = wrapper['report'] if 'report' in wrapper or 'integrity' in wrapper else wrapper
    if type(row) is not dict:
        _fail()
    return {key: row.get(key) for key in ('reported_at', 'reviewed', 'reviewed_at', 'decision')}


def _watch_source(values, refusal):
    """Take only the documented fields; damaged or unreadable evidence stays unavailable."""
    values = _dict(values)
    native, latest, reviewed = values.get('native'), values.get('latest'), values.get('reviewed')
    if type(native) is not dict or native.get('unavailable') is True:
        _fail()
    if type(latest) is dict and 'integrity' in latest and latest.get('integrity') != 'available':
        _fail()
    kept_latest, kept_reviewed = _report_fields(latest), _report_fields(reviewed)
    return {'native': native,
            'latest': None if kept_latest is None else
                      {'reported_at': kept_latest['reported_at'], 'reviewed': kept_latest['reviewed'],
                       'decision': kept_latest['decision']},
            'reviewed': None if kept_reviewed is None else
                        {'reviewed_at': kept_reviewed['reviewed_at'],
                         'decision': kept_reviewed['decision']},
            'refused_for_capacity': refusal,
            'owner_question': values.get('owner_question')}


def _git(office_root, arguments):
    result = subprocess.run(['git', '-C', str(office_root)] + arguments, shell=False,
                            capture_output=True, text=True, encoding='utf-8', errors='replace',
                            timeout=GIT_TIMEOUT, env=_environment(GIT_TERMINAL_PROMPT='0'))
    if result.returncode != 0:
        _fail()
    return result.stdout


def office_reader(office_root):
    """Read the published office only: `origin/main`, never the working tree."""
    ref = 'refs/remotes/origin/main'
    entries, current = [], None
    for line in _git(office_root, ['show', ref + ':docs/decisions.md']).splitlines():
        if line.startswith('## '):
            heading = line[3:].strip()
            head, separator, tail = heading.partition(' — ')
            current = {'id': head.strip() if separator else heading,
                       'title': tail.strip() if separator else heading, 'text': ''}
            entries.append(current)
        elif current is not None:
            current['text'] += line + '\n'
    for entry in entries:
        entry['text'] = entry['text'].strip()

    notes = []
    for path in _git(office_root, ['ls-tree', '-r', '--name-only', ref]).splitlines():
        found = re.fullmatch(r'evidence/(ap\d+)/leverans\.md', path.strip(), re.IGNORECASE)
        if not found:
            continue
        text = _git(office_root, ['show', ref + ':' + path.strip()])
        title = next((line[2:].strip() for line in text.splitlines() if line.startswith('# ')), '')
        notes.append({'ap': found.group(1).upper(), 'title': title, 'text': text})

    turns, inside = [], False
    for line in _git(office_root, ['show', ref + ':docs/plan.md']).splitlines():
        stripped = line.strip()
        if 'ÄGARENS TUR' in stripped:
            inside = True
            continue
        if not inside:
            continue
        kind = ('beslut' if stripped.startswith('- [beslut] ') else
                'operatörshandling' if stripped.startswith('- [operatörshandling] ') else None)
        if kind is None:
            inside = False
            continue
        text = stripped.split('] ', 1)[1].strip()
        since = _SINCE.search(text)
        turns.append({'kind': kind, 'text': _SINCE.sub('', text).strip(),
                      'since': since.group(1) if since else None})

    return {'main': _git(office_root, ['rev-parse', ref]).strip(),
            'main_date': _git(office_root, ['log', '-1', '--format=%cI', ref]).strip(),
            'entries': entries, 'notes': notes, 'plan_owner_turn': turns}


def collect(runtime_root, office_root, runtime_probe=None, watch_reader=None, office_reader=None,
            task_reader=None):
    """Bounded read-only collection. A failing reader makes only its own source unavailable."""
    probe_reader = runtime_probe or globals()['runtime_probe']
    watch = watch_reader or globals()['watch_reader']
    office = office_reader or globals()['office_reader']
    tasks = task_reader or globals()['task_reader']
    started = _now()
    sources = {name: {'status': 'unavailable', 'read_at': started, 'value': None} for name in SOURCES}

    parts, refusal = {}, None
    try:
        parts = _dict(probe_reader(runtime_root))
    except Exception:
        parts = {}
    read_at = _now()
    for name in PROBE_SOURCES:
        sources[name]['read_at'] = read_at
        try:
            part = _dict(parts.get(name))
            if part.get('ok') is not True:
                _fail()
            sources[name].update(status='ok', value=VALUES[name](part.get('value')))
        except FAILURES:
            sources[name].update(status='unavailable', value=None)
    try:
        part = _dict(parts.get('refusal'))
        if part.get('ok') is True:
            refusal = bool(_dict(part.get('value')).get('capacity'))
    except FAILURES:
        refusal = None

    # The task files are asked for only by the parked tasks the engine reading itself names.
    if sources['engine']['status'] == 'ok':
        sources['tasks']['read_at'] = _now()
        try:
            given = _parked_ids(sources['engine']['value'])
            sources['tasks'].update(status='ok', value=_tasks_value(tasks(runtime_root, given)))
        except Exception:
            sources['tasks'].update(status='unavailable', value=None)

    sources['watch']['read_at'] = _now()
    try:
        sources['watch'].update(status='ok',
                                value=_watch_value(_watch_source(watch(runtime_root), refusal)))
    except Exception:
        sources['watch'].update(status='unavailable', value=None)

    sources['office']['read_at'] = _now()
    try:
        sources['office'].update(status='ok', value=_office_value(office(office_root)))
    except Exception:
        sources['office'].update(status='unavailable', value=None)

    return {'schema': SCHEMA, 'provdata': False, 'read_started_at': started, 'sources': sources}


# --- command ----------------------------------------------------------------------


def _write(target, raw):
    path = Path(target).absolute()
    if path.name in ('', '.', '..'):
        _fail()
    parent = os.open(str(path.parent), os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.mkdir(path.name, 0o700, dir_fd=parent)
        directory = os.open(path.name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent)
        try:
            os.fchmod(directory, 0o700)
            fd = os.open('projection.json', os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                         0o600, dir_fd=directory)
            with os.fdopen(fd, 'wb') as stream:
                os.fchmod(stream.fileno(), 0o600)
                stream.write(raw)
        finally:
            os.close(directory)
    finally:
        os.close(parent)


def main(argv=None):
    arguments = sys.argv[1:] if argv is None else argv
    try:
        if len(arguments) != 1:
            _fail()
        office = Path(__file__).absolute().parents[1]
        readings = collect(office.parent / 'Nortropic Runtime', office)
        projection = project(readings, datetime.now(timezone.utc))
        document = json.dumps(projection, ensure_ascii=False, indent=1, sort_keys=True) + '\n'
        _write(arguments[0], document.encode('utf-8'))
        return 0
    except Exception:
        print(COMMAND_ERROR, file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
