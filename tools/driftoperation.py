"""Office's bounded intake/drift/monitor handler. Runtime/Temporal supplies the wakeup.

No model execution, publication, mail or arbitrary command is selected by input
events. This module is loaded only from the reviewed release with frozen config.
The local recipient is Office's private incident inbox; it is not an email claim.

With `period_seconds` the work is due-based, never tick-based: the wakeup interval
only asks whether the period has elapsed against durable state. A period missed
because the host slept is therefore performed by the first wakeup that becomes
possible instead of being skipped, and a wakeup inside the current period reads
nothing and writes nothing. Without `period_seconds` every run is due, which is
D038's unchanged behaviour.
"""
from datetime import datetime, timedelta, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import time
import uuid
import urllib.error
import urllib.parse
import urllib.request


# Each bounded channel's own wall-clock ceiling. BOUND_SECONDS is what Runtime's
# activity/schedule timeouts must exceed; a test asserts the sum, so the bound and
# its parts can never drift apart silently.
INTAKE_BOUND = 120
DRIFT_BOUND = 90
MONITOR_TIMEOUT = 8                              # per blocking socket operation
MONITOR_DEADLINE = 25                            # enforced wall clock for both attempts
# A urlopen timeout bounds each blocking socket operation, not the whole attempt: a
# server that trickles bytes slower than the timeout keeps read() going indefinitely.
# The monitor therefore carries its own wall clock, and its ceiling allows for one
# operation that was already blocked when the deadline passed.
MONITOR_BOUND = MONITOR_DEADLINE + MONITOR_TIMEOUT
TERMINATION_BOUND = 6                            # SIGTERM wait then SIGKILL wait
BOUND_SECONDS = INTAKE_BOUND + DRIFT_BOUND + 2 * TERMINATION_BOUND + MONITOR_BOUND

# A period record from the future would silence the work until that future arrives.
# A little skew is ordinary; more than this is treated as malformed state.
CLOCK_SKEW = 300

# Weekly is the ordered period; the range keeps an hour's floor and a month's ceiling
# so neither a busy loop nor an unbounded silence can be bound as an accepted period.
PERIOD_FLOOR, PERIOD_CEILING = 3600, 2678400

CHANNELS = {'monitor': 'pending.json', 'intake': 'intake-pending.json',
            'drift': 'drift-pending.json'}


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def regular(path):
    path = Path(path).absolute()
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError('Symlink in operation input/state')
    return path


def write(path, value):
    raw = (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()
    temp = regular(path).with_name(path.name + '.tmp')
    fd = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(raw); stream.flush(); os.fsync(stream.fileno())
    os.replace(temp, path)


def secret(path):
    path = regular(path)
    if not path.is_file() or stat.S_IMODE(path.stat().st_mode) != 0o600:
        raise ValueError('Private credential file must be regular and 0600')
    value = path.read_text().strip()
    if len(value) < 16 or '\n' in value or '\r' in value:
        raise ValueError('Invalid private credential')
    return value


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *_args, **_kwargs):
        return None


def monitor(config):
    parsed = urllib.parse.urlsplit(config['url'])
    test_loopback = config.get('isolated_test') is True and parsed.hostname in ('127.0.0.1', 'localhost')
    if (parsed.username or parsed.password or parsed.fragment or not parsed.hostname
            or (parsed.scheme != 'https' and not (test_loopback and parsed.scheme == 'http'))):
        raise ValueError('Monitor requires an explicit HTTPS endpoint')
    if not re.fullmatch('[0-9a-f]{40}', config['candidate']):
        raise ValueError('Monitor requires an exact candidate')
    headers = {'Accept': 'application/json', 'Cache-Control': 'no-cache'}
    if config.get('bypass_file'):
        headers['x-vercel-protection-bypass'] = secret(config['bypass_file'])
    opener = urllib.request.build_opener(NoRedirect())
    attempts = []
    deadline = time.monotonic() + MONITOR_DEADLINE
    for number in range(2):
        transient = False
        if time.monotonic() > deadline:
            attempts.append({'error': 'monitor_bound_exceeded', 'healthy': False})
            break
        try:
            with opener.open(urllib.request.Request(config['url'], headers=headers), timeout=MONITOR_TIMEOUT) as response:
                raw = b''
                while len(raw) <= 65536:
                    if time.monotonic() > deadline:
                        raise TimeoutError('Health read exceeded the monitor bound')
                    # read1, not read: read(n) blocks until it has all n bytes, so a
                    # server trickling inside the socket timeout would never be cut.
                    chunk = response.read1(min(8192, 65537 - len(raw)))
                    if not chunk:
                        break
                    raw += chunk
                if len(raw) > 65536:
                    raise ValueError('Oversized health response')
                body = json.loads(raw)
                healthy = (response.status == 200 and body.get('status') == 'ok'
                           and body.get('candidate') == config['candidate']
                           and body.get('storage') == 'available')
                attempts.append({'http': response.status, 'body_sha256': digest(raw), 'healthy': healthy})
                return {'healthy': healthy, 'reason': 'verified' if healthy else 'wrong_candidate_or_unhealthy',
                        'attempts': attempts, 'observed_at': now(), 'candidate': config['candidate']}
        except urllib.error.HTTPError as error:
            transient = error.code in (429, 502, 503, 504)
            attempts.append({'http': error.code, 'healthy': False})
        except (urllib.error.URLError, TimeoutError, OSError):
            transient = True
            attempts.append({'error': 'transport_unavailable', 'healthy': False})
        except (ValueError, TypeError, AttributeError):
            attempts.append({'error': 'invalid_health_response', 'healthy': False})
        if not transient or number == 1:
            break
        time.sleep(1)
    return {'healthy': False, 'reason': 'endpoint_unavailable', 'attempts': attempts,
            'observed_at': now(), 'candidate': config['candidate']}


def frozen_digitala(config, required):
    """The exact reviewed interpreter and Digitala bytes, for every channel alike.

    `required` names the tool this channel actually starts, so a binding that omits
    it is refused instead of running whatever else happens to be frozen.
    """
    interpreter = regular(config['python_path'])
    if (not Path(config['python_path']).is_absolute() or not interpreter.is_file()
            or not os.access(interpreter, os.X_OK)
            or digest(interpreter.read_bytes()) != config['python_sha256']):
        raise ValueError('Consumer interpreter differs from reviewed binding')
    root = regular(config['digitala_root'])
    files = config['digitala_files']
    if not files or required not in files:
        raise ValueError('Missing frozen Digitala tool: ' + required)
    for name, expected in files.items():
        relative = Path(name)
        if relative.is_absolute() or '..' in relative.parts:
            raise ValueError('Unsafe consumer file')
        path = regular(root / relative)
        if digest(path.read_bytes()) != expected:
            raise ValueError('Digitala consumer changed after release review')
    if any(str(path.relative_to(root)) not in files for path in (root / 'verktyg').rglob('*.py')):
        raise ValueError('Unbound Python module in consumer directory')
    return interpreter, root


def bounded_start(argv, root, environment, bound, stdout, stderr):
    """Start a frozen tool in its own session and end it inside `bound` seconds."""
    with stdout.open('xb') as out, stderr.open('xb') as err:
        process = subprocess.Popen(argv, cwd=root, env=environment, stdout=out, stderr=err,
                                   start_new_session=True)
        try:
            return process.wait(timeout=bound)
        except subprocess.TimeoutExpired:
            import signal
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=TERMINATION_BOUND // 2)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL); process.wait(timeout=TERMINATION_BOUND // 2)
            return None


def consume(config, output):
    interpreter, root = frozen_digitala(config, 'verktyg/kundstart.py')
    environment = {k: v for k, v in os.environ.items() if k in ('PATH', 'HOME', 'LANG', 'LC_ALL', 'TMPDIR')}
    environment.update(PYTHONDONTWRITEBYTECODE='1', KUNDSTART_BAS_URL=config['base_url'],
                       KUNDSTART_NYCKEL_FIL=str(regular(config['key_file'])))
    if config.get('bypass_file'):
        environment['KUNDSTART_BYPASS_FIL'] = str(regular(config['bypass_file']))
    argv = [str(interpreter), '-I', '-B', str(root / 'verktyg/kundstart.py'), 'konsumera',
            '--kund', str(regular(config['customer'])), '--utforare', config['executor']]
    status = bounded_start(argv, root, environment, INTAKE_BOUND,
                           output / 'intake.stdout', output / 'intake.stderr')
    if status is None:
        return {'completed': False, 'reason': 'consumer_timeout'}
    return {'completed': status == 0, 'returncode': status,
            'python_sha256': config['python_sha256'],
            'stdout_sha256': digest((output / 'intake.stdout').read_bytes()),
            'stderr_sha256': digest((output / 'intake.stderr').read_bytes())}


def drift(config, output):
    """Digitala's own reading drift check on its frozen bytes, into the customer path.

    `drift_kontroll.py` exits 1 when it found an incident. That is a check that ran,
    not a broken mechanism, so `ran` and `healthy` are reported separately. The exit
    code is believed only when the receipt it wrote agrees with it: the receipt is
    the same artefact `underhall.py besked` later reads, so a green result here can
    not come from a check that wrote nothing.
    """
    interpreter, root = frozen_digitala(config, 'verktyg/drift_kontroll.py')
    plan = regular(config['plan'])
    if digest(plan.read_bytes()) != config['plan_sha256']:
        raise ValueError('Drift plan changed after release review')
    target = regular(config['receipts'])
    if not target.is_dir():
        raise ValueError('Drift receipt directory must be the existing customer path')
    argv = [str(interpreter), '-I', '-B', str(root / 'verktyg/drift_kontroll.py'),
            '--plan', str(plan), '--ut', str(target)]
    if config.get('isolated_test') is True:
        # Only an isolated loopback fixture may be read over plain HTTP.
        argv.append('--tillat-http')
    environment = {k: v for k, v in os.environ.items() if k in ('PATH', 'HOME', 'LANG', 'LC_ALL', 'TMPDIR')}
    environment['PYTHONDONTWRITEBYTECODE'] = '1'
    status = bounded_start(argv, root, environment, DRIFT_BOUND,
                           output / 'drift.stdout', output / 'drift.stderr')
    base = {'plan_sha256': config['plan_sha256'], 'returncode': status,
            'stdout_sha256': digest((output / 'drift.stdout').read_bytes()),
            'stderr_sha256': digest((output / 'drift.stderr').read_bytes())}
    if status is None:
        return {'ran': False, 'reason': 'drift_timeout', **base}
    if status not in (0, 1):
        return {'ran': False, 'reason': 'drift_refused' if status == 2 else 'drift_failed', **base}
    # The receipt is named to the whole second and is overwritten by a same-second
    # rerun, so a newly appeared filename cannot be the evidence. The tool's own
    # stdout names the file it wrote; that name is then held to the customer path.
    try:
        declared = json.loads((output / 'drift.stdout').read_bytes().splitlines()[-1])
        receipt = regular(target / Path(declared['ut']).name)
        if (Path(declared['ut']).resolve() != receipt or receipt.parent != target
                or not re.fullmatch(r'DRIFT-[0-9TZ]{1,40}\.json', receipt.name)
                or not receipt.is_file()):
            raise ValueError('Receipt outside the customer path')
        raw = receipt.read_bytes()
        value = json.loads(raw)
        rows = value['sajter']
        incidents = value['incidenter']
    except (ValueError, OSError, KeyError, TypeError, IndexError):
        return {'ran': False, 'reason': 'drift_receipt_unreadable', **base}
    if (value.get('schema') != 1 or not isinstance(rows, list) or not rows
            or type(incidents) is not int
            or declared.get('incidenter') != incidents
            or incidents != sum(1 for row in rows if isinstance(row, dict) and row.get('incident'))
            or (incidents > 0) != (status == 1)):
        # Exit code, the tool's own count and the receipt's rows must agree; if they
        # do not, this is not evidence either way and the check did not run.
        return {'ran': False, 'reason': 'drift_receipt_inconsistent', **base}
    return {'ran': True, 'healthy': incidents == 0,
            'reason': 'verified' if not incidents else 'site_incident',
            'incidents': incidents, 'sites': len(rows), 'receipt': receipt.name,
            'receipt_sha256': digest(raw),
            'findings': [{'adress': str(row.get('adress'))[:200],
                          'fynd': [str(item)[:200] for item in (row.get('fynd') or [])][:10]}
                         for row in rows if row.get('incident')][:20], **base}


class StateError(ValueError):
    """Named malformed durable-state error; raw state is never used as a path."""


def timestamp(value):
    if not isinstance(value, str):
        raise StateError('invalid_timestamp')
    try:
        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is None:
            raise ValueError()
    except ValueError as error:
        raise StateError('invalid_timestamp') from error


def validate_state(value):
    if (not isinstance(value, dict) or set(value) != {'healthy', 'sequence', 'observed_at'}
            or type(value['healthy']) is not bool or type(value['sequence']) is not int
            or value['sequence'] < 0):
        raise StateError('invalid_state')
    timestamp(value['observed_at'])


def validate_event(event, channel=None):
    if (not isinstance(event, dict) or set(event) != {'id', 'channel', 'kind', 'state', 'observation'}
            or event['channel'] not in CHANNELS
            or (channel is not None and event['channel'] != channel)
            or not isinstance(event['id'], str)
            or not re.fullmatch(event['channel'] + '-[0-9a-f]{32}', event['id'])):
        raise StateError('invalid_event_identity')
    validate_state(event['state'])
    if event['kind'] != ('recovered' if event['state']['healthy'] else 'incident'):
        raise StateError('invalid_event_kind')
    observation = event['observation']
    if (not isinstance(observation, dict)
            or set(observation) != {'healthy', 'reason', 'observed_at', 'detail_sha256'}
            or type(observation['healthy']) is not bool
            or observation['healthy'] != event['state']['healthy']
            or observation['observed_at'] != event['state']['observed_at']
            or not isinstance(observation['reason'], str)
            or not re.fullmatch('[a-z_]{1,80}', observation['reason'])
            or not isinstance(observation['detail_sha256'], str)
            or not re.fullmatch('[0-9a-f]{64}', observation['detail_sha256'])):
        raise StateError('invalid_event_observation')
    return event


def load_state(path):
    try:
        return json.loads(regular(path).read_text())
    except (ValueError, OSError) as error:
        raise StateError('unreadable_state') from error


def deliver(home, event):
    """The private Office inbox consumes each stable event once, including retries."""
    validate_event(event)
    inbox = regular(home / 'inbox'); inbox.mkdir(mode=0o700, exist_ok=True)
    target = regular(inbox / (event['id'] + '.json'))
    if target.parent != inbox:
        raise StateError('recipient_path_escape')
    if target.exists():
        existing = load_state(target)
        if (not isinstance(existing, dict) or set(existing) != {'event', 'receipt'}
                or existing['event'] != event):
            raise StateError('recipient_event_collision')
        receipt = existing['receipt']
        if (not isinstance(receipt, dict) or set(receipt) != {'recipient', 'received_at', 'event_id'}
                or receipt['recipient'] != 'kontorets-privata-driftyta'
                or receipt['event_id'] != event['id']):
            raise StateError('invalid_recipient_receipt')
        timestamp(receipt['received_at'])
        return receipt
    receipt = {'recipient': 'kontorets-privata-driftyta', 'received_at': now(), 'event_id': event['id']}
    write(target, {'event': event, 'receipt': receipt})
    if load_state(target) != {'event': event, 'receipt': receipt}:
        raise StateError('recipient_readback_failed')
    return receipt


def transition(home, channel, current):
    """Independent channels, durable outbox before actual inbox acknowledgement."""
    state_file = regular(home / (channel + '.json'))
    pending = regular(home / CHANNELS[channel])
    receipts = []
    previous = {'healthy': True, 'sequence': 0, 'observed_at': now()}
    try:
        if state_file.exists():
            previous = load_state(state_file); validate_state(previous)
        if pending.exists():
            event = validate_event(load_state(pending), channel)
            receipts.append({'resumed': True, **deliver(home, event)})
            write(state_file, event['state']); pending.unlink()
            previous = event['state']
    except StateError as error:
        # Preserve malformed inputs for diagnosis, never silently treat them as
        # healthy. The next ordinary run can recover from the explicit incident.
        for path in (state_file, pending):
            if path.exists():
                path.rename(path.with_name(path.name + '.invalid-' + uuid.uuid4().hex))
        observed = now()
        detail = {'error_code': str(error), 'channel': channel}
        current = {'healthy': False, 'reason': 'invalid_persisted_state',
                   'observed_at': observed,
                   'detail_sha256': digest(json.dumps(detail, sort_keys=True).encode())}
        previous = {'healthy': True, 'sequence': 0, 'observed_at': observed}
        state_error = str(error)
    else:
        state_error = None
    if current['healthy'] != previous['healthy']:
        state = {'healthy': current['healthy'], 'sequence': previous['sequence'] + 1,
                 'observed_at': current['observed_at']}
        event = {'id': channel + '-' + uuid.uuid4().hex, 'channel': channel,
                 'kind': 'recovered' if current['healthy'] else 'incident',
                 'state': state, 'observation': current}
        validate_event(event, channel)
        write(pending, event)
        receipts.append({'resumed': False, **deliver(home, event)})
        write(state_file, state); pending.unlink()
    return {'receipts': receipts, 'state_error': state_error}


def due(home, config, run_id):
    """Is the period's work due? Read from durable state, never from the wakeup.

    A period missed because the host slept stays due, so the first wakeup after the
    host returns performs it. Malformed period state is preserved and treated as due:
    silence about a week is worse than one extra reading run. A record this very run
    wrote means the run was interrupted after closing its period; it resumes as due
    and must not close the same period a second time.
    """
    period = config['period_seconds']
    if type(period) is not int or not PERIOD_FLOOR <= period <= PERIOD_CEILING:
        raise ValueError('Invalid bounded operation period')
    path = regular(home / 'period.json')
    observed = datetime.now(timezone.utc)
    overdue = {'due': True, 'period_seconds': period, 'completed_at': None,
               'due_at': observed.isoformat(), 'overdue_seconds': 0, 'sequence': 0}
    if not path.exists():
        return {**overdue, 'reason': 'no_period_recorded'}
    try:
        value = load_state(path)
        if (not isinstance(value, dict) or set(value) != {'completed_at', 'sequence', 'run_id'}
                or type(value['sequence']) is not int or value['sequence'] < 1
                or not isinstance(value['run_id'], str)
                or not re.fullmatch('[a-zA-Z0-9-]{1,100}', value['run_id'])):
            raise StateError('invalid_period_state')
        timestamp(value['completed_at'])
        last = datetime.fromisoformat(value['completed_at'])
        if last > observed + timedelta(seconds=CLOCK_SKEW):
            # A future stamp would report a skipped wakeup as success until that date,
            # and a year like 9999 overflows the addition below. Neither hides a week.
            raise StateError('invalid_period_state')
        due_at = last + timedelta(seconds=period)
    except (StateError, OverflowError, OSError, ValueError):
        path.rename(path.with_name(path.name + '.invalid-' + uuid.uuid4().hex))
        return {**overdue, 'reason': 'invalid_period_state'}
    if value['run_id'] == run_id:
        return {**overdue, 'reason': 'own_period_record', 'completed_at': value['completed_at'],
                'sequence': value['sequence'], 'due_at': due_at.isoformat()}
    late = observed - due_at
    return {'due': late >= timedelta(0),
            'reason': 'period_elapsed' if late >= timedelta(0) else 'not_due',
            'period_seconds': period, 'completed_at': value['completed_at'],
            'due_at': due_at.isoformat(),
            'overdue_seconds': max(0, int(late.total_seconds())),
            'sequence': value['sequence']}


def record_period(home, period, completed_at, run_id):
    """Close the period once per run, counted from this run, after a read-back.

    An interrupted run that already closed its own period re-reads that record instead
    of closing the period again, so resuming can never advance the sequence twice.
    """
    path = regular(home / 'period.json')
    if period['reason'] == 'own_period_record':
        return load_state(path)
    state = {'completed_at': completed_at, 'sequence': period['sequence'] + 1, 'run_id': run_id}
    write(path, state)
    if load_state(path) != state:
        raise StateError('period_readback_failed')
    return state


def observation(healthy, reason, detail):
    return {'healthy': healthy, 'reason': reason, 'observed_at': now(),
            'detail_sha256': digest(json.dumps(detail, sort_keys=True).encode())}


def run(config, run_id):
    if config.get('schema') != 'office-drift/1' or not re.fullmatch('[a-zA-Z0-9-]{1,100}', run_id):
        raise ValueError('Unknown operation schema or run identity')
    if not any(config.get(channel) for channel in CHANNELS):
        # Without a channel there is nothing to read, and a recorded period would
        # then claim a week's check that never happened.
        raise ValueError('Operation binds no intake, drift or monitor channel')
    config_sha256 = digest(json.dumps(config, sort_keys=True, separators=(',', ':')).encode())
    home = regular(config['state'])
    home.mkdir(mode=0o700, parents=True, exist_ok=True); home.chmod(0o700)
    with regular(home / '.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        output = regular(home / run_id)
        result_file = output / 'result.json'
        if result_file.is_file():
            prior = json.loads(result_file.read_text())
            if prior.get('config_sha256') != config_sha256:
                raise ValueError('Run identity already belongs to another configuration')
            return prior
        # Dueness is read after the cache, and it alone decides. A run interrupted
        # after closing its own period is recognised by the record's run_id, so it
        # resumes as due and re-reads rather than closing the period twice.
        period = due(home, config, run_id) if 'period_seconds' in config else None
        if period is not None and not period['due']:
            # Inside the current period this wakeup reads nothing and writes nothing,
            # so it needs no run record; the native schedule already counts the tick.
            observed = now()
            return {'run_id': run_id, 'config_sha256': config_sha256, 'completed': True,
                    'performed': False, 'skipped': 'not_due', 'period': period,
                    'started_at': observed, 'finished_at': observed}
        output.mkdir(mode=0o700, exist_ok=True)
        binding_file = output / 'binding.json'
        if binding_file.exists():
            if json.loads(binding_file.read_text()) != {'config_sha256': config_sha256}:
                raise ValueError('Interrupted run belongs to another configuration')
        else:
            write(binding_file, {'config_sha256': config_sha256})
        result = {'run_id': run_id, 'config_sha256': config_sha256, 'started_at': now(), 'completed': True}
        if config.get('intake'):
            # A prior interrupted consumer is resumed through its ordinary idempotency
            # journal, with a new attempt directory preserving all earlier output.
            attempt = output / ('attempt-' + str(time.time_ns())); attempt.mkdir(mode=0o700)
            try:
                result['intake'] = consume(config['intake'], attempt)
            except (ValueError, OSError, KeyError, TypeError, subprocess.SubprocessError) as error:
                # A broken intake binding must not suppress the independent health
                # monitor. Store only the error class, never credentials or output.
                result['intake'] = {'completed': False, 'reason': 'consumer_failed',
                                    'error_type': type(error).__name__}
            result['completed'] = result['intake']['completed']
        if config.get('drift'):
            attempt = output / ('drift-' + str(time.time_ns())); attempt.mkdir(mode=0o700)
            try:
                result['drift'] = drift(config['drift'], attempt)
            except (ValueError, OSError, KeyError, TypeError, subprocess.SubprocessError) as error:
                # A broken drift binding must not suppress the other channels.
                result['drift'] = {'ran': False, 'reason': 'drift_binding_failed',
                                   'error_type': type(error).__name__}
            result['completed'] = result['completed'] and result['drift'].get('healthy') is True
        result['deliveries'] = {}
        if 'intake' in result:
            intake = result['intake']
            result['deliveries']['intake'] = transition(home, 'intake', observation(
                intake['completed'], 'verified' if intake['completed'] else 'consumer_failed', intake))
        if 'drift' in result:
            check = result['drift']
            result['deliveries']['drift'] = transition(home, 'drift', observation(
                check.get('healthy') is True, check['reason'], check))
        if config.get('monitor'):
            current = monitor(config['monitor']); result['monitor'] = current
            current['access_scope'] = ('internal_protection_bypass' if config['monitor'].get('bypass_file')
                                       else 'ordinary_endpoint')
            result['deliveries']['monitor'] = transition(home, 'monitor', observation(
                current['healthy'], current['reason'], current))
            result['completed'] = result['completed'] and current['healthy']
        state_error = any(item['state_error'] for item in result['deliveries'].values())
        result['completed'] = result['completed'] and not state_error
        # `performed` is the honest answer to "did the period's reading actually run".
        # `completed` additionally requires that nothing it read was unhealthy, so an
        # incident found by a check that ran is performed but not completed.
        result['performed'] = (result.get('intake', {'completed': True})['completed']
                               and result.get('drift', {'ran': True})['ran'] and not state_error)
        if period is not None:
            result['period'] = period
            if result['performed']:
                try:
                    result['period_recorded'] = record_period(home, period, result['started_at'], run_id)
                except StateError as error:
                    result['period_recorded'] = {'error_code': str(error)}
                    result['completed'] = False
            if period['reason'] == 'invalid_period_state':
                result['completed'] = False
        result['finished_at'] = now(); write(result_file, result)
        return result
