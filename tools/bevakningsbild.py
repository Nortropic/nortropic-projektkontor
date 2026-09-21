"""Dated AP08 projection. Import is inert; collection is bounded and read-only."""
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys

import agarbild

OBLIGATION = 'office-python-temporal'
JSON_LIMIT = 8 * 1024 * 1024
DOCUMENT_LIMIT = 64 * 1024 * 1024
CODE_LIMIT = 512 * 1024 * 1024
ROUND_LIMIT = 512
ERROR = 'Otillgängligt eller ogiltigt underlag.'
FAILURES = (OSError, ValueError, TypeError, KeyError, IndexError, OverflowError, RecursionError)


def _require(value):
    if not value:
        raise ValueError(ERROR)


def _text(value):
    if type(value) is not str or not value.strip():
        return False
    try:
        value.encode('utf-8')
        return True
    except UnicodeError:
        return False


def _digest(value):
    return type(value) is str and re.fullmatch('[0-9a-f]{64}', value) is not None


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=True, allow_nan=False).encode('utf-8')


def _hash(raw):
    return sha256(raw).hexdigest()


def _time(value):
    _require(_text(value))
    # AP08's strict parser also rejects invalid offsets and fractional minutes.
    normalized = value[:10] + 'T' + value[11:] if len(value) > 10 and value[10] == ' ' else value
    agarbild._date(normalized)
    return datetime.fromisoformat(normalized.replace('Z', '+00:00')).astimezone(timezone.utc)


def _date(value, generated):
    try:
        parsed = _time(value)
        return parsed.isoformat() if parsed <= generated else None
    except FAILURES:
        return None


def _show(value):
    if value is None:
        return 'saknas'
    try:
        return json.dumps(value, ensure_ascii=True, allow_nan=False, sort_keys=True)
    except FAILURES:
        return 'ogiltig uppgift'


def _strings(value):
    return type(value) is list and all(_text(s) for s in value)


def _report_shape(report, packet):
    """Shared documentary shape; never coerces flags or fills missing evidence."""
    _require(type(report) is dict and type(packet) is dict)
    _require(type(report.get('schema')) is int and report['schema'] == 1)
    _require(type(packet.get('schema')) is int and packet['schema'] == 1)
    _require(report.get('completed') is True and type(report.get('reviewed')) is bool)
    _require(type(packet.get('complete')) is bool)
    _require(report.get('obligation') == OBLIGATION and _text(report.get('run_id'))
             and _text(report.get('case_id')) and _digest(report.get('packet_sha256'))
             and _digest(report.get('context_sha256')))
    _require(report.get('action_executed') is False and report.get('publication') is False)
    _require(report.get('reused_from') is None or _text(report['reused_from']))
    versions = packet.get('versions')
    _require(type(versions) is dict and all(_text(versions.get(k)) for k in ('python', 'temporalio')))
    for key in ('runtime_revision', 'office_revision'):
        _require(type(report.get(key)) is str and re.fullmatch('[0-9a-f]{40}', report[key])
                 and report[key] == versions.get(key))
    _require(_digest(report.get('active_config_sha256')) and
             report['active_config_sha256'] == versions.get('active_config_sha256'))
    _fingerprint(packet)
    observed = _time(packet.get('observed_at'))
    _require(_time(report.get('observed_at')) == observed)
    _require(_time(report.get('first_treated_at')) <= observed <= _time(report.get('reported_at')))
    _require(report.get('decision') in ('retain', 'not_applicable', 'insufficient', 'propose_action'))
    _require(type(report.get('reasoning')) is dict and
             set(report['reasoning']) == {'vendor', 'local', 'judgment', 'authority'} and
             all(_text(v) for v in report['reasoning'].values()))
    for key in ('old_gaps', 'limitations', 'evidence', 'contradictions'):
        _require(_strings(report.get(key)))
    _require(len(set(report['evidence'])) == len(report['evidence']))
    if report['reviewed']:
        _require(_time(report.get('first_treated_at')) <= _time(report.get('reviewed_at'))
                 <= _time(report['reported_at']))
        if report.get('reused_from') is None:
            _require(observed <= _time(report['reviewed_at']))
        review = report.get('review')
        _require(type(review) is dict)
        _require(all(_digest(review.get(k)) for k in
                     ('assessment_sha256', 'analysis_result_sha256', 'review_result_sha256')))
        _require(_text(review.get('analysis_thread_id')) and _text(review.get('review_thread_id'))
                 and review['analysis_thread_id'] != review['review_thread_id'])
        _require(_text(report.get('review_origin')))
        _require(packet['complete'] or report['decision'] == 'insufficient')
        _require(not report['contradictions'] or report['decision'] == 'insufficient')
        if report['decision'] == 'propose_action':
            _draft_shape(report.get('ap06'))
        else:
            _require(report.get('ap06') is None)
    else:
        _require(report['decision'] == 'insufficient')


def _wrapper(value, generated):
    if type(value) is not dict:
        return False
    try:
        _require(set(value) == {'report', 'packet', 'integrity', 'locator'})
        _require(value['integrity'] == 'available' and _text(value['locator']))
        _report_shape(value['report'], value['packet'])
        _require(_date(value['packet']['observed_at'], generated) is not None)
        _require(_date(value['report']['reported_at'], generated) is not None)
        return True
    except FAILURES:
        return False


def _range(value, start, end=None):
    end = start if end is None else end
    return (type(value) is list and len(value) == 1 and type(value[0]) is dict
            and type(value[0].get('start')) is int and value[0]['start'] == start
            and type(value[0].get('end')) is int and value[0]['end'] == end
            and type(value[0].get('step')) is int and value[0]['step'] == 1)


def _bounded_ranges(value, low, high):
    return (type(value) is list and bool(value) and all(
        type(r) is dict and type(r.get('start')) is int and type(r.get('end')) is int
        and low <= r['start'] <= r['end'] <= high and type(r.get('step')) is int
        and r['step'] > 0 for r in value))


def _native_lists_valid(native):
    """Validate entries as well as containers before claiming a known schema."""
    try:
        for key in ('next_action_times', 'running', 'recent'):
            _require(type(native.get(key)) is list)
        for value in native['next_action_times']:
            _time(value)
        for group in ('running', 'recent'):
            for entry in native[group]:
                _require(type(entry) is dict)
                action = entry.get('action') if group == 'recent' else entry
                _require(type(action) is dict and all(_text(action.get(key)) for key in
                         ('workflow_id', 'first_execution_run_id')))
                if group == 'recent':
                    _time(entry.get('scheduled_at'))
                    _time(entry.get('started_at'))
        return True
    except FAILURES:
        return False


def _schedule(native):
    """Return known control state separately from the qualified calendar."""
    note = native.get('note')
    stopped = type(note) is str and note.startswith('STOPPED')
    state = ('stoppat' if stopped else 'pausat' if native.get('paused') is True else
             'aktiverat' if native.get('paused') is False else 'okänt')
    spec = native.get('schedule')
    qualified = None
    if type(spec) is dict:
        cron = spec.get('cron_expressions')
        empty_cron = (type(cron) is str and cron == '[]') or (type(cron) is list and not cron)
        calendars = spec.get('calendars')
        if (empty_cron and type(calendars) is list and len(calendars) == 1
                and type(calendars[0]) is dict and spec.get('time_zone_name') == 'Europe/Stockholm'
                and spec.get('intervals', []) == [] and spec.get('skip', []) == []
                and spec.get('start_at') is None and spec.get('end_at') is None
                and spec.get('jitter') in (None, '0:00:00')):
            cal = calendars[0]
            daily = (_range(cal.get('hour'), 9) and _range(cal.get('minute'), 0)
                     and _range(cal.get('second'), 0) and _range(cal.get('day_of_month'), 1, 31)
                     and _range(cal.get('month'), 1, 12) and _range(cal.get('day_of_week'), 0, 6))
            if native.get('limited_actions') is False and cal.get('year') == [] and daily:
                qualified = 'dygnsschema 09:00 Europe/Stockholm'
            years = cal.get('year')
            if (native.get('limited_actions') is True and _bounded_ranges(years, 1, 9999)
                    and all(_bounded_ranges(cal.get(key), low, high) for key, low, high in (
                        ('second', 0, 59), ('minute', 0, 59), ('hour', 0, 23),
                        ('day_of_month', 1, 31), ('month', 1, 12), ('day_of_week', 0, 6)))):
                qualified = 'årsbundet engångsprov, inte flera dygns drift'
    policy = native.get('policy')
    catchup = type(policy) is dict and policy.get('catchup_window') == '22:00:00'
    known = (qualified is not None and catchup and state != 'okänt'
             and type(note) is str and type(native.get('paused')) is bool
             and all(type(native.get(k)) is int and native[k] >= 0 for k in
                     ('remaining_actions', 'actions', 'missed_catchup', 'skipped_overlap'))
             and _native_lists_valid(native))
    text = 'Enligt schemaobservationen: ' + state + '. '
    text += (qualified + '. ') if qualified else 'Annat eller okänt schema. '
    text += ('Återkomstfönster 22 timmar (now22hours). ' if catchup else
             'Återkomstpolicy är annan eller okänd; äldre 24 timmar är inte slutramen. ')
    text += 'Paus/stopp visar inte att en redan pågående omgång avbrutits.'
    running = native.get('running')
    if type(running) is list:
        text += ' Pågående native åtgärder: ' + str(len(running)) + '; detta är starter, inte färdiga intag.'
    else:
        text += ' Pågående native åtgärder: okänt.'
    return state, known, text


def view(native, latest, reviewed, generated_at):
    """Pure AP08 schema-1 input. No clock, I/O, mutations or operational authority."""
    generated = _time(generated_at)
    issues, evidence, work = [], [], []

    def gap(text, refs):
        issues.append(dict(text=text, evidence=refs))

    def add(identity, title, state, text, observed, locator, detail):
        if observed is not None and generated - _time(observed) > timedelta(days=1):
            age = ' Inaktuell (inaktuell observation): avser endast ' + observed + '.'
            text += age
            gap(title + ':' + age, [identity])
        evidence.append(dict(id=identity, title=title, kind='Daterat privat underlag',
            observed_at=observed, revision='Se bindningar i underlaget', locator=locator,
            sha256=None, text=detail))
        work.append(dict(title=title, state=state, text=text, observed_at=observed, evidence=[identity]))

    native = native if type(native) is dict else {}
    native_date = _date(native.get('observed_at'), generated)
    native_ok = (native.get('obligation') == OBLIGATION and native.get('unavailable') is not True
                 and native_date is not None)
    control, qualified, schedule_text = _schedule(native)
    if not native_ok:
        schedule_text = 'Schemaobservation saknas eller är otillgänglig. ' + schedule_text
        gap('Aktuellt schemaläge kan inte beläggas; okänd, framtida eller ogiltig observation.', ['native'])
    elif not qualified:
        gap('Schemat eller återkomstpolicyn kan inte identifieras som den granskade ramen.', ['native'])
    next_times = native.get('next_action_times')
    planned = []
    if type(next_times) is list:
        for value in next_times:
            try:
                if _time(value) > generated:
                    planned.append(_time(value).isoformat())
            except FAILURES:
                gap('Ogiltig planerad schematid.', ['native'])
    if planned:
        schedule_text += ' Nästa planerade native åtgärd: ' + min(planned) + ' (inte observation).'
    schedule_state = ('waiting' if control in ('pausat', 'stoppat') else 'accepted') if native_ok and qualified else 'unknown'
    native_detail = '\n'.join(k + ': ' + _show(native.get(k)) for k in (
        'observed_at', 'obligation', 'reason', 'paused', 'note', 'limited_actions', 'remaining_actions',
        'schedule', 'policy', 'next_action_times', 'actions', 'missed_catchup', 'skipped_overlap',
        'running', 'recent', 'meaning'))
    add('native', 'Schema', schedule_state, schedule_text, native_date,
        'Fryst Runtime: runtime.obligation status', native_detail)

    valid = {}
    for identity, title, wrapper in (('latest', 'Senaste observation', latest),
                                     ('reviewed', 'Senast granskade besked', reviewed)):
        wrapper = wrapper if type(wrapper) is dict else {}
        report = wrapper.get('report') if type(wrapper.get('report')) is dict else {}
        packet = wrapper.get('packet') if type(wrapper.get('packet')) is dict else {}
        date = _date(report.get('reviewed_at') if identity == 'reviewed' else
                     packet.get('observed_at', report.get('observed_at')), generated)
        ok = _wrapper(wrapper, generated)
        reviewed_ok = ok and report['reviewed'] is True
        valid[identity] = reviewed_ok
        complete = ok and packet['complete'] is True
        state = 'finished' if reviewed_ok and complete else 'waiting' if ok else 'unknown'
        if identity == 'reviewed' and reviewed_ok and wrapper != latest:
            state = 'superseded'
        if reviewed_ok:
            decision = {'retain': 'Behåll avgränsad användning', 'not_applicable': 'Inte tillämpligt',
                        'insufficient': 'Otillräckligt underlag', 'propose_action': 'Ogenomfört åtgärdsförslag'}[report['decision']]
            text = decision + '. ' + report['reasoning']['judgment']
            if report.get('reused_from') is not None:
                text += ' Återanvänd granskning, ingen ny oberoende granskning.'
            if identity == 'reviewed' and wrapper != latest:
                text += ' Daterad historik; inget nytt accepterat arbete.'
            if not complete:
                text += ' Intaget är ofullständigt; ingen lyckad komplett observation.'
        else:
            text = 'Granskat besked saknas för denna observation; teknisk väntan eller okänt underlag.'
            gap(title + ': saknat, ofullständigt, skadat eller ogranskat underlag.', [identity])
        text += (' Paket observerat: ' + _show(packet.get('observed_at', report.get('observed_at')))
                 + '. Ärendets baslinje först behandlad: ' + _show(report.get('first_treated_at'))
                 + '. Rapporterat: ' + _show(report.get('reported_at'))
                 + '. Ursprungligen granskat: ' + _show(report.get('reviewed_at')) + '.')
        if date is None:
            gap(title + ': observationstid saknas, är ogiltig eller ligger i framtiden.', [identity])
        detail = 'Integritet: ' + _show(wrapper.get('integrity')) + '\n' + _show(report)
        locator = wrapper.get('locator') if _text(wrapper.get('locator')) else 'Underlag saknas'
        add(identity, title, state, text, date, locator, detail)
        for key, label in (('old_gaps', 'Tidigare lucka'), ('limitations', 'Begränsning')):
            if _strings(report.get(key)):
                for item in report[key]:
                    gap(label + ': ' + item, [identity])

    # Native starts do not establish successful intake. Match an actual run plus
    # a report no earlier than that start, never the native query timestamp.
    report_wrappers = [w for w in (latest, reviewed) if _wrapper(w, generated)]
    action_gap = False
    for group in ('recent', 'running'):
        entries = native.get(group)
        if type(entries) is not list:
            if native_ok:
                gap('Native uppgift om ' + group + ' saknas eller är ogiltig.', ['native'])
            continue
        for entry in entries:
            if type(entry) is not dict:
                action_gap = True
                continue
            action = entry.get('action') if group == 'recent' else entry
            start = _date(entry.get('started_at'), generated)
            ids = {action.get(k) for k in ('workflow_id', 'first_execution_run_id')
                   if type(action) is dict and _text(action.get(k))}
            matched = any(w['report']['run_id'] in ids and
                          (start is None or _time(w['report']['reported_at']) >= _time(start))
                          for w in report_wrappers)
            latest_time = max((_time(w['packet']['observed_at']) for w in report_wrappers), default=None)
            if not matched and (group == 'running' or start is None or latest_time is None
                                or _time(start) > latest_time):
                action_gap = True
    if action_gap:
        gap('Aktuell lucka: senare eller pågående native start saknar matchande läsbar rapport. En start är inte slutfört källintag.', ['native', 'latest'])
        latest_work = next(row for row in work if row['title'] == 'Senaste observation')
        if latest_work['state'] == 'finished':
            latest_work['state'] = 'waiting'
        latest_work['text'] += ' Senare eller pågående native start saknar matchande läsbar rapport.'
        latest_work['evidence'].append('native')
        work.append(dict(title='Aktuell rapportlucka', state='waiting',
            text='Native aktivitet saknar matchande läsbart besked; kedjedrivaren utreder inom mandatet.',
            observed_at=native_date, evidence=['native', 'latest']))
    latest_reviewed = valid['latest'] and latest['packet']['complete'] is True
    fresh = (latest_reviewed and
             generated - _time(latest['packet']['observed_at']) <= timedelta(days=1))
    proposal = (latest_reviewed and not action_gap and latest['report']['decision'] == 'propose_action'
                and type(latest['report'].get('ap06')) is dict and bool(latest['report']['ap06']))
    handling = ('Utred saknat eller felaktigt underlag inom befintligt mandat.'
                if not fresh or action_gap or not native_ok or not qualified else
                'Invänta nästa namngivna planerade omgång inom befintligt mandat' +
                (': ' + min(planned) + '.' if planned else '; nästa tid är okänd.'))
    if control in ('pausat', 'stoppat'):
        handling += ' Respektera att åtagandet är ' + control + '; ingen automatisk återstart.'
    if proposal:
        handling = 'Kedjedrivaren lämnar det bundna AP06-utkastet som en ogenomförd ägarfråga. ' + handling
    result = dict(schema=1, generated_at=generated.isoformat(), title='Daterad bevakningsbild',
        summary='Privat daterad läsbild av schema, senaste observation och senast granskade besked. Inte live eller notifiering.',
        scope='Det namngivna Python-/Temporalåtagandet. Ingen ny befogenhet eller garanti för aktuell lyckad bevakning.',
        capabilities=[], work=work,
        next_action=dict(text=handling, owner='Kedjedrivaren', authority='proposed' if proposal else 'none',
                         evidence=['native', 'latest']),
        owner_decision=dict(needed='yes' if proposal else 'no',
            question='Ta ställning till det ogenomförda AP06-förslaget.' if proposal else 'Ingen rutinmässig ägarfråga.',
            reason='Separat handlingsspecifikt mandat saknas.' if proposal else
                   'Teknisk väntan, saknad granskning och äldre förslag ger inget nytt ägargodkännande.',
            evidence=['latest', 'reviewed']), issues=issues, evidence=evidence)
    agarbild.validate(result)
    return result


def _absolute(value):
    raw = os.fspath(value)
    _require(type(raw) is str and raw and '\x00' not in raw)
    _require('..' not in raw.split('/') and '.' not in raw.split('/'))
    path = Path(raw)
    return path if path.is_absolute() else Path.cwd() / path


def _under(value, root):
    path = _absolute(value)
    _require(path != root and path.is_relative_to(root))
    return path


@contextmanager
def _directory(path):
    """Walk every ancestor with no-follow directory descriptors, including /tmp."""
    path = _absolute(path)
    flags = getattr(os, 'O_SEARCH', getattr(os, 'O_PATH', os.O_RDONLY))
    flags |= os.O_DIRECTORY | os.O_NOFOLLOW
    fd = os.open(path.anchor, flags)
    try:
        for part in path.parts[1:]:
            child = os.open(part, flags, dir_fd=fd)
            os.close(fd)
            fd = child
        yield fd
    finally:
        os.close(fd)


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        _require(key not in result)
        result[key] = value
    return result


def _nonfinite(_value):
    raise ValueError(ERROR)


def _decode(raw):
    _require(len(raw) <= JSON_LIMIT)
    value = json.loads(raw, object_pairs_hook=_pairs, parse_constant=_nonfinite)
    # This also rejects overflowed numeric literals such as 1e999.
    _canonical(value)
    return value


class _Reader:
    def __init__(self):
        self.document_left = DOCUMENT_LIMIT
        self.code_left = CODE_LIMIT
        self.document_incomplete = False

    def document_size(self, size):
        if size > min(JSON_LIMIT, self.document_left):
            self.document_incomplete = True
            raise ValueError(ERROR)

    def read(self, path, code=False):
        path = _absolute(path)
        remaining = self.code_left if code else self.document_left
        limit = remaining if code else min(JSON_LIMIT, remaining)
        with _directory(path.parent) as parent:
            fd = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
        with os.fdopen(fd, 'rb') as stream:
            before = os.fstat(stream.fileno())
            _require(stat.S_ISREG(before.st_mode))
            if not code:
                self.document_size(before.st_size)
            _require(before.st_size <= limit)
            raw = stream.read(limit + 1)
            after = os.fstat(stream.fileno())
            if not code:
                self.document_size(len(raw))
                self.document_left -= len(raw)
            _require(len(raw) <= limit and (before.st_size, before.st_mtime_ns, before.st_ino) ==
                     (after.st_size, after.st_mtime_ns, after.st_ino))
        if code:
            self.code_left -= len(raw)
        return raw, after

    def json(self, path):
        raw, info = self.read(path)
        value = _decode(raw)
        _require(type(value) is dict)
        return value, raw, info


def _relative(value):
    _require(_text(value) and not value.startswith('/') and
             all(part not in ('', '.', '..') for part in value.split('/')))
    return Path(value)


def _selected_files(value):
    if type(value) is dict:
        entries = list(value.items())
    else:
        _require(type(value) is list)
        entries = []
        for item in value:
            _require(type(item) is dict and set(item) == {'path', 'sha256'})
            entries.append((item['path'], item['sha256']))
    result = {}
    for name, digest in entries:
        _relative(name)
        _require(name not in result and _digest(digest))
        result[name] = digest
    _require('runtime/runtime/obligation.py' in result and 'context/watch.json' in result)
    return result


def _frozen_runtime_tree(release, files):
    """Close the import tree over the manifest, including bytecode read by -B."""
    runtime = release / 'runtime'
    selected = {release / name for name in files if name.startswith('runtime/')}
    directories = {runtime}
    for path in selected:
        directories.update(parent for parent in path.parents if parent.is_relative_to(runtime))
    pending = [runtime]
    while pending:
        directory = pending.pop()
        with _directory(directory) as parent:
            fd = os.open('.', os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent)
            try:
                with os.scandir(fd) as entries:
                    for entry in entries:
                        path = directory / entry.name
                        mode = entry.stat(follow_symlinks=False).st_mode
                        if stat.S_ISDIR(mode):
                            _require(path in directories)
                            pending.append(path)
                        else:
                            _require(stat.S_ISREG(mode) and path in selected)
            finally:
                os.close(fd)


def _binding(root, reader):
    active_path = root / '.runtime/ap10/active.json'
    active, active_raw, _ = reader.json(active_path)
    _require(set(active) == {'config', 'sha256'} and _digest(active['sha256']))
    pointer = active['config']
    _require(_text(pointer))
    path = _absolute(pointer) if pointer.startswith('/') else root / _relative(pointer)
    releases = root / '.runtime/ap10/releases'
    path = _under(path, releases)
    # A release is an immediate directory, and its config is an immediate file.
    _require(len(path.relative_to(releases).parts) == 2)
    config, config_raw, _ = reader.json(path)
    _require(_hash(config_raw) == active['sha256'])
    release = path.parent
    if 'directory' in config:
        _require(config['directory'] == str(release))
    _require(config.get('host_root') == str(root))
    office = _absolute(config['office_root'])
    _require(config['office_root'] == str(office) and office == root.parent / 'nortropic-projektkontor')
    # Office is an exact mapping only; collection never reads that directory.
    database = _under(config['database'], root / '.runtime')
    _require(config['database'] == str(database) and database == root / '.runtime/runtime.sqlite')
    with _directory(database.parent) as parent:
        try:
            info = os.stat(database.name, dir_fd=parent, follow_symlinks=False)
        except FileNotFoundError:
            info = None  # Status itself may report that no shared service exists.
        _require(info is None or stat.S_ISREG(info.st_mode))
    for key in ('runtime_revision', 'office_revision'):
        _require(type(config.get(key)) is str and re.fullmatch('[0-9a-f]{40}', config[key]))
    files = _selected_files(config['files'])
    _frozen_runtime_tree(release, files)
    watch_raw = None
    context_hashes = {}
    for name, digest in files.items():
        raw, _ = reader.read(release / name, code=True)
        _require(_hash(raw) == digest)
        if name == 'context/watch.json':
            reader.document_size(len(raw))
            reader.document_left -= len(raw)
            watch_raw = raw
        if name in ('context/case.json', 'context/watch.json',
                    'context/authority.md', 'context/prior-decision.md'):
            context_hashes[Path(name).name] = digest
    watch = _decode(watch_raw)
    _require(type(watch) is dict and type(watch.get('schema')) is int and watch['schema'] == 1
             and _text(watch.get('case_id')))
    _time(watch.get('first_treated_at'))
    _require(_strings(watch.get('old_gaps')))
    config = deepcopy(config)
    config.update(directory=str(release), config_sha256=active['sha256'])
    context_hash = _hash(_canonical(context_hashes)) if len(context_hashes) == 4 else None
    return config, watch, context_hash, (active_raw, path, config_raw)


def _status(root, config):
    launcher = root / '.runtime/temporal-venv/bin/python'
    # Only the fixed, already-qualified interpreter's leaf symlink is allowed.
    with _directory(launcher.parent):
        pass
    env = {key: os.environ[key] for key in ('PATH', 'HOME', 'USER', 'LOGNAME', 'LANG', 'TMPDIR')
           if key in os.environ}
    env.update(PYTHONDONTWRITEBYTECODE='1', NR_HOST_ROOT=str(root),
               NR_CONFIG_SHA256=config['config_sha256'])
    result = subprocess.run([str(launcher), '-B', '-m', 'runtime.obligation', 'status'],
        cwd=str(Path(config['directory']) / 'runtime'), shell=False, capture_output=True,
        text=True, timeout=20, env=env)
    _require(result.returncode == 0)
    value = _decode(result.stdout.encode('utf-8'))
    _require(type(value) is dict and value.get('obligation') == OBLIGATION)
    _time(value.get('observed_at'))
    return value


def _unavailable(reason):
    return dict(obligation=OBLIGATION, unavailable=True, reason=reason,
                observed_at=datetime.now(timezone.utc).isoformat())


def _fingerprint(packet):
    basis = {'versions': packet['versions']}
    ids = set()
    for group in ('sources', 'local'):
        _require(type(packet.get(group)) is list)
        records = []
        for record in packet[group]:
            _require(type(record) is dict and _text(record.get('id')) and record['id'] not in ids)
            ids.add(record['id'])
            _require(record.get('status') in ('available', 'unavailable'))
            if packet['complete']:
                _require(record['status'] == 'available' and _digest(record.get('sha256')))
            records.append({key: record[key] for key in ('id', 'status', 'sha256')})
        basis[group] = sorted(records, key=lambda item: item['id'])
    fingerprint = _hash(_canonical(basis)) if packet['complete'] else None
    _require(packet.get('fingerprint') == fingerprint)
    return fingerprint, ids


def _draft_shape(draft):
    _require(type(draft) is dict and draft.get('status') == 'draft'
             and draft.get('mechanical_complete') is False)
    package, private = draft.get('package'), draft.get('private')
    _require(type(package) is dict and package.get('task_draft') == {})
    if 'private' in draft:
        _require(type(private) is dict and type(private.get('spec')) is dict
                 and private['spec'].get('task') == {})
    else:
        _require(_text(package.get('brief')) and 'gaps' in package)
    # Full and compact documentary forms share the same non-executable boundary.
    # Validate every present list: fallback must never conceal damaged root gaps.
    _require('gaps' in draft or 'gaps' in package)
    for container in (draft, package):
        if 'gaps' in container:
            gaps = container['gaps']
            _require(type(gaps) is list and all(type(g) is dict and _text(g.get('code'))
                                              and _text(g.get('subject')) for g in gaps))
            _require(any(g['code'] == 'action_authority_missing' for g in gaps))
    if 'gaps' in draft and 'gaps' in package:
        _require(_canonical(draft['gaps']) == _canonical(package['gaps']))


def _fresh_review(home, report, packet, reader):
    answers, threads = {}, []
    for role in ('analysis', 'review'):
        result, raw, info = reader.json(home / role / 'result.json')
        _require(_hash(raw) == report['review'][role + '_result_sha256'])
        provider = result.get('provider')
        _require(type(provider) is dict and result.get('completed') is True
                 and result.get('process_group_removed') is True and provider.get('valid_terminal') is True
                 and _text(provider.get('thread_id')))
        _require(provider['thread_id'] == report['review'][role + '_thread_id'])
        threads.append(provider['thread_id'])
        answer = result.get('answer')
        _require(type(answer) is dict and answer.get('case_id') == report['case_id']
                 and answer.get('packet_sha256') == report['packet_sha256'])
        answers[role] = answer
        if role == 'review':
            _require(_time(report['reviewed_at']) == datetime.fromtimestamp(info.st_mtime, timezone.utc))
    _require(threads[0] != threads[1])
    analysis, review = answers['analysis'], answers['review']
    digest = _hash(_canonical(analysis))
    _require(digest == report['review']['assessment_sha256'] == review.get('assessment_sha256'))
    _require(review.get('verdict') == 'approved' and review.get('blockers') == [] and _text(review.get('reason')))
    _require(set(analysis) == {'case_id', 'packet_sha256', 'decision', 'vendor', 'local',
                              'judgment', 'authority', 'evidence', 'contradictions', 'proposal'})
    _require(analysis.get('decision') == report['decision'])
    _require(_canonical({key: analysis[key] for key in ('vendor', 'local', 'judgment', 'authority')})
             == _canonical(report['reasoning']))
    for key in ('evidence', 'contradictions'):
        _require(_canonical(analysis.get(key)) == _canonical(report[key]))
    _, ids = _fingerprint(packet)
    _require(report['evidence'] and set(report['evidence']) <= ids)
    if report['decision'] == 'propose_action':
        proposal = analysis.get('proposal')
        _require(type(proposal) is dict and all(_text(proposal.get(k)) for k in
                 ('text', 'reason', 'requirement', 'observable')))
        _require(_strings(proposal.get('claims')) and proposal['claims'] and
                 len(set(proposal['claims'])) == len(proposal['claims']))
    else:
        _require(analysis.get('proposal') is None)


class _Reports:
    def __init__(self, rounds, config, watch, context_hash, reader):
        self.rounds, self.config, self.watch = rounds, config, watch
        self.context_hash, self.reader, self.cache = context_hash, reader, {}

    def get(self, home, origin=False):
        if home in self.cache:
            wrapper = self.cache[home]
            _require(not origin or (wrapper['integrity'] == 'available' and
                     wrapper['report'].get('reused_from') is None))
            return wrapper
        _require(home.parent == self.rounds)
        _require(len(self.cache) < ROUND_LIMIT)
        wrapper = dict(report=None, packet=None, integrity='unavailable',
                       locator=str(home / 'report/result.json'))
        # Store first, so any attempted cycle is unavailable, never recursion.
        self.cache[home] = wrapper
        try:
            report, _, _ = self.reader.json(home / 'report/result.json')
            wrapper['report'] = report
            packet, raw, _ = self.reader.json(home / 'intake/data/packet.json')
            wrapper['packet'] = packet
            _report_shape(report, packet)
            _require(report['case_id'] == self.watch['case_id'] and report['run_id'] == home.name)
            _require(report['packet_sha256'] == _hash(raw))
            _require(report['first_treated_at'] == self.watch['first_treated_at'] and
                     _canonical(report['old_gaps']) == _canonical(self.watch['old_gaps']))
            if self.context_hash is not None and report.get('active_config_sha256') == self.config['config_sha256']:
                _require(report['context_sha256'] == self.context_hash)
            versions = packet['versions']
            for key in ('runtime_revision', 'office_revision'):
                _require(type(report.get(key)) is str and re.fullmatch('[0-9a-f]{40}', report[key])
                         and report[key] == versions[key])
            # Old releases remain dated history. The current pin authorizes only
            # the query; report revisions bind to that report's own packet.
            _require(_digest(report.get('active_config_sha256')) and
                     report['active_config_sha256'] == versions['active_config_sha256'])
            fingerprint, _ = _fingerprint(packet)
            if report['reviewed']:
                review_origin = _absolute(report['review_origin'])
                _require(review_origin.parent == self.rounds)
                if report.get('reused_from') is None:
                    _require(review_origin == home)
                    _fresh_review(home, report, packet, self.reader)
                else:
                    _require(not origin and review_origin != home and packet['complete'] is True)
                    previous = self.get(review_origin, origin=True)
                    _require(previous['integrity'] == 'available' and previous['report']['reviewed'] is True)
                    original, original_packet = previous['report'], previous['packet']
                    _require(original_packet['complete'] is True and fingerprint == _fingerprint(original_packet)[0])
                    _require(_time(original['reported_at']) <= _time(report['observed_at']))
                    for key in ('case_id', 'context_sha256', 'decision', 'reasoning', 'evidence',
                                'contradictions', 'review', 'reviewed_at', 'review_origin', 'ap06'):
                        _require(_canonical(report[key]) == _canonical(original[key]))
                    _require(_absolute(report['reused_from']).parent == self.rounds)
            wrapper['integrity'] = 'available'
        except FAILURES:
            pass
        _require(not origin or (wrapper['integrity'] == 'available' and
                 wrapper['report'].get('reused_from') is None))
        return wrapper


def collect(runtime_root, status_reader=None):
    """Read pinned documentary evidence; injected status replaces only the query."""
    result = dict(native=None, latest=None, reviewed=None)
    reader = _Reader()
    try:
        root = _absolute(runtime_root)
        config, watch, context_hash, binding = _binding(root, reader)
    except FAILURES:
        result['native'] = _unavailable('invalid_frozen_binding')
        return result
    try:
        native = (status_reader or _status)(root, deepcopy(config))
        _require(type(native) is dict and native.get('obligation') == OBLIGATION)
        _canonical(native)
        _time(native.get('observed_at'))
        active_raw, path, config_raw = binding
        _require(reader.read(root / '.runtime/ap10/active.json')[0] == active_raw and
                 reader.read(path)[0] == config_raw)
        result['native'] = deepcopy(native)
    except Exception:
        # Query adapters and process errors must not disclose private diagnostics.
        result['native'] = _unavailable('native_status_unavailable_or_changed')
    rounds = root / '.runtime/ap10/rounds'
    reports = _Reports(rounds, config, watch, context_hash, reader)
    incomplete = False
    homes = []
    try:
        with _directory(rounds) as parent:
            fd = os.open('.', os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent)
            try:
                with os.scandir(fd) as entries:
                    for entry in entries:
                        if entry.is_symlink():
                            incomplete = True
                        elif entry.is_dir(follow_symlinks=False):
                            if len(homes) == ROUND_LIMIT:
                                incomplete = True
                                break
                            homes.append(rounds / entry.name)
            finally:
                os.close(fd)
        for home in sorted(homes):
            reports.get(home)
    except FAILURES:
        incomplete = True
    wrappers = list(reports.cache.values())

    def rank(wrapper):
        report = wrapper.get('report')
        try:
            return _time(report['observed_at']), _time(report['reported_at'])
        except FAILURES:
            return datetime.min.replace(tzinfo=timezone.utc), datetime.min.replace(tzinfo=timezone.utc)

    if wrappers:
        result['latest'] = max(wrappers, key=rank)
        approved = [w for w in wrappers if w['integrity'] == 'available' and w['report']['reviewed'] is True]
        if approved:
            result['reviewed'] = max(approved, key=rank)
        # Undated broken records might be newer. Do not quietly substitute success.
        unknown = [w for w in wrappers if rank(w)[0].year == 1]
        if unknown:
            result['latest'] = unknown[0]
    if incomplete or reader.document_incomplete:
        result['latest'] = dict(report=None, packet=None, integrity='unavailable',
                               locator='Ofullständig läsning: gräns eller otillgänglig omgång.')
    return result


def _output_parent(value):
    path = _absolute(value)
    _require(path.name not in ('', '.', '..'))
    with _directory(path.parent) as parent:
        try:
            os.stat(path.name, dir_fd=parent, follow_symlinks=False)
        except FileNotFoundError:
            return path
    raise ValueError(ERROR)


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    try:
        _require(len(args) == 1)
        output = _output_parent(args[0])  # Reject unsafe destinations before collection.
        office = Path(__file__).absolute().parents[1]
        root = office.parent / 'Nortropic Runtime'
        captured = collect(root)
        document = view(**captured, generated_at=datetime.now(timezone.utc).isoformat())
        files = {'input.json': _canonical(document),
                 'index.html': agarbild.render(document).encode('utf-8')}
        with _directory(output.parent) as parent:
            os.mkdir(output.name, mode=0o700, dir_fd=parent)
            fd = os.open(output.name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent)
            try:
                os.fchmod(fd, 0o700)
                for name, raw in files.items():
                    child = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                                    0o600, dir_fd=fd)
                    with os.fdopen(child, 'wb') as stream:
                        os.fchmod(stream.fileno(), 0o600)
                        stream.write(raw)
            finally:
                os.close(fd)
        return 0
    except FAILURES:
        print('Kunde inte skapa bevakningsbilden. Kontrollera underlag och ny privat målkatalog.', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
