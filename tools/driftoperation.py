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
import sys
import threading
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
MONITOR_DEADLINE = 33                            # the monitor channel's wall clock
# A urlopen timeout bounds each blocking socket operation, not a whole attempt, and
# nothing inside the request covers the status line and headers at all: a server that
# trickles header bytes just inside the timeout stalls for as long as it likes. Checking
# a deadline between reads cannot bound that, so the attempts run in their own daemon
# thread and the channel returns when the join times out. A stranded thread holds no
# durable lock - the handler returns and releases its state lock on time - and ends by
# itself as soon as its socket does. This IS the ceiling, with nothing added to it.
MONITOR_BOUND = MONITOR_DEADLINE
# A join bounds the channel, not the socket the OS still holds. So stranded work is
# bounded in two further ways: it is told to stop, which prevents a late second attempt
# after the channel has already reported its timeout, and only this many may be alive
# at once - beyond that the channel refuses immediately rather than adding another.
MONITOR_STRANDED_LIMIT = 2
# Runtime loads this module afresh for every activity, so module-level state does NOT
# survive between wakeups - a registry kept here would reset the cap each time while
# earlier threads were still alive. The threads accumulate in the interpreter, so the
# registry is anchored there instead, under one explicit name.
_STRANDED = 'nortropic_office_drift_stranded_monitors'


def _stranded_registry():
    registry = getattr(sys, _STRANDED, None)
    if registry is None:
        registry = ([], threading.Lock())
        setattr(sys, _STRANDED, registry)
    return registry


def stranded_monitors(add=None):
    """How many abandoned health threads are still alive; pruned as they finish."""
    threads, lock = _stranded_registry()
    with lock:
        if add is not None:
            threads.append(add)
        threads[:] = [thread for thread in threads if thread.is_alive()]
        return len(threads)
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
    """Health observation under a real wall clock, never a socket timeout alone.

    The binding is checked here, before the thread: a misconfigured endpoint must be
    refused loudly rather than reported as a bound that ran out. Only the I/O is bounded.
    """
    headers = monitor_binding(config)
    abandoned = stranded_monitors()
    def exceeded(reason, answered=False):
        # `observed` False says no health answer was obtained at all. That is NOT the
        # same as an unhealthy endpoint, and it must not close the channel's period:
        # nothing was checked, so the check is still owed. But an answer that DID
        # arrive before the bound ran out is still an observation of the site.
        return {'healthy': False, 'observed': bool(answered), 'reason': reason,
                'stranded_threads': stranded_monitors(),
                'attempts': [{'error': reason, 'healthy': False}],
                'observed_at': now(), 'candidate': config['candidate']}
    if abandoned >= MONITOR_STRANDED_LIMIT:
        # Refuse rather than let abandoned network work pile up in the long-lived worker.
        return exceeded('monitor_stranded_limit')
    # The thread records an answer as soon as one arrives, so a body read that then
    # times out - or the outer deadline - cannot erase an observation already made.
    progress = {'answered': False}
    answer, failure, stop = {}, [], threading.Event()
    def work():
        try:
            answer.update(observe_health(config, headers, stop, progress))
        except BaseException as error:              # noqa: BLE001 - re-raised below
            failure.append(error)
    thread = threading.Thread(target=work, daemon=True)
    thread.start()
    thread.join(MONITOR_DEADLINE)
    if failure:
        raise failure[0]
    if thread.is_alive() or not answer:
        # Told to stop, so it cannot start a further attempt after this answer; it holds
        # no lock, is never waited on again, and is counted until it ends by itself.
        stop.set()
        stranded_monitors(add=thread)
        return exceeded('monitor_bound_exceeded', progress['answered'])
    return answer


def monitor_binding(config):
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
    return headers


def observe_health(config, headers, stop, progress):
    """`observed` says whether the endpoint actually answered, not whether we tried.

    A status code or a body read is an answer about the site, healthy or not, and the
    week's check is then done. A transport failure, a DNS failure or a timeout is not:
    nothing was learned, so the check is still owed and the period must stay open.
    Otherwise one transient network fault would postpone a real check a whole week.
    """
    opener = urllib.request.build_opener(NoRedirect())
    attempts, answered = [], False
    for number in range(2):
        transient = False
        if stop.is_set():
            # The channel already answered without this attempt; do not start one now.
            attempts.append({'error': 'monitor_abandoned', 'healthy': False})
            break
        try:
            with opener.open(urllib.request.Request(config['url'], headers=headers), timeout=MONITOR_TIMEOUT) as response:
                # The endpoint answered. Record it before reading the body, so a read
                # that times out cannot turn a received status into "never answered".
                answered = True; progress['answered'] = True
                raw = b''
                while len(raw) <= 65536:
                    # read1, not read: read(n) blocks until it has all n bytes, so one
                    # call could hold the whole body. The outer join is the real bound.
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
                return {'healthy': healthy, 'observed': True,
                        'reason': 'verified' if healthy else 'wrong_candidate_or_unhealthy',
                        'attempts': attempts, 'observed_at': now(), 'candidate': config['candidate']}
        except urllib.error.HTTPError as error:
            # The server answered. That is an observation of the site, and an unhealthy one.
            transient = error.code in (429, 502, 503, 504)
            answered = True; progress['answered'] = True
            attempts.append({'http': error.code, 'healthy': False})
        except (urllib.error.URLError, TimeoutError, OSError):
            # Nothing was learned about the site at all.
            transient = True
            attempts.append({'error': 'transport_unavailable', 'healthy': False})
        except (ValueError, TypeError, AttributeError):
            # Read, but unreadable as a health answer: an observation, and unhealthy.
            answered = True; progress['answered'] = True
            attempts.append({'error': 'invalid_health_response', 'healthy': False})
        if not transient or number == 1 or stop.wait(1):
            break
    return {'healthy': False, 'observed': answered,
            'reason': 'endpoint_unhealthy' if answered else 'endpoint_unavailable',
            'attempts': attempts, 'observed_at': now(), 'candidate': config['candidate']}


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


def validate_settled(value, sequence, closed=False):
    """A settled outcome is only ever valid for the one period it describes.

    `closed` False asks for the period not yet closed (`sequence + 1`), which is a
    commit still owed. `closed` True asks for the period already closed (`sequence`),
    whose outcome is what an interrupted run's own receipt must be written from.
    """
    if (not isinstance(value, dict)
            or set(value) != {'closes_sequence', 'healthy', 'reason', 'run_id', 'observed_at'}
            or type(value['closes_sequence']) is not int
            or value['closes_sequence'] != (sequence if closed else sequence + 1)
            or type(value['healthy']) is not bool
            or not isinstance(value['reason'], str) or not re.fullmatch('[a-z_]{1,80}', value['reason'])
            or not isinstance(value['run_id'], str)
            or not re.fullmatch('[a-zA-Z0-9-]{1,100}', value['run_id'])):
        raise StateError('invalid_settled_outcome')
    timestamp(value['observed_at'])
    return value


def settle_outcome(home, channel, sequence, healthy, reason, run_id):
    """Record what this channel found, before its period is closed.

    Two phases, in this order: the outcome is durable first, the period second. An
    interruption between them therefore leaves the work findable, so the next wakeup
    completes the period instead of reading the customer's site a second time inside
    the same week - and the receipt it writes carries the health that was actually
    observed rather than a fresh guess.

    The record names the one period it closes, so it can never be reused in a later
    one. Once the period advances the record no longer matches and is ignored.
    """
    state = {'closes_sequence': sequence + 1, 'healthy': healthy, 'reason': reason,
             'run_id': run_id, 'observed_at': now()}
    path = regular(home / ('settled-' + channel + '.json'))
    write(path, state)
    if load_state(path) != state:
        raise StateError('settled_readback_failed')
    return state


def settled(home, channel, sequence, closed=False):
    """This channel's already-recorded outcome for one exact period."""
    path = regular(home / ('settled-' + channel + '.json'))
    if not path.exists():
        return None
    try:
        return validate_settled(load_state(path), sequence, closed)
    except StateError:
        pass
    # Not the record asked for. A WELL-FORMED record for the other of the two periods
    # is simply not the one wanted, and is left alone. Anything else is malformed and is
    # preserved for diagnosis. Neither may attest anything.
    for other in (not closed, closed):
        try:
            validate_settled(load_state(path), sequence, other)
            return None
        except StateError:
            continue
    path.rename(path.with_name(path.name + '.invalid-' + uuid.uuid4().hex))
    return None


def note_attempt(home, channel, sequence, run_id):
    """Mark that this channel's reading is about to start, before it has any effect.

    A crash after this and before the outcome is recorded means we genuinely do not know
    whether the check completed. The honest answer is then to read again - closing a
    period whose result was never seen would hide the week - so the next wakeup redoes it
    exactly once and says so in its receipt (`retried_after_interruption`). This marker
    exists to make that duplicate visible and counted, not to prevent it: nothing can
    know the outcome of work before it is done.
    """
    write(regular(home / ('attempt-' + channel + '.json')),
          {'starts_sequence': sequence + 1, 'run_id': run_id, 'started_at': now()})


def interrupted_attempt(home, channel, sequence):
    """Was a reading started for the period now due, without its outcome recorded?"""
    path = regular(home / ('attempt-' + channel + '.json'))
    if not path.exists():
        return None
    try:
        value = load_state(path)
        if (not isinstance(value, dict) or set(value) != {'starts_sequence', 'run_id', 'started_at'}
                or type(value['starts_sequence']) is not int
                or value['starts_sequence'] != sequence + 1
                or not isinstance(value['run_id'], str)
                or not re.fullmatch('[a-zA-Z0-9-]{1,100}', value['run_id'])):
            raise StateError('invalid_attempt_marker')
        timestamp(value['started_at'])
        return value
    except StateError:
        path.rename(path.with_name(path.name + '.invalid-' + uuid.uuid4().hex))
        return None


def due(home, config, channel, run_id):
    """Is this channel's period due? Read from durable state, never from the wakeup.

    Each channel keeps its own period, which is what makes both halves of the order
    hold at once. A period missed because the host slept stays due, so the first wakeup
    after the host returns performs it. And a channel that keeps failing is retried at
    every wakeup without dragging the others with it: a drift check that did run stays
    closed for its whole week even while a broken intake is still being retried.

    A record this very run wrote means the run was interrupted after closing this
    channel's period. The work is done, so the channel is NOT due again: resuming
    finishes the receipt without reading the customer's site or Kundstart a second time.
    Nothing is ever reused across periods - a result is only ever recorded by the run
    that produced it, in the period it was produced in.

    Malformed period state is preserved and treated as due: silence about a week is
    worse than one extra reading run.
    """
    period = config['period_seconds']
    if type(period) is not int or not PERIOD_FLOOR <= period <= PERIOD_CEILING:
        raise ValueError('Invalid bounded operation period')
    path = regular(home / ('period-' + channel + '.json'))
    observed = datetime.now(timezone.utc)
    overdue = {'due': True, 'period_seconds': period, 'completed_at': None,
               'due_at': observed.isoformat(), 'overdue_seconds': 0, 'sequence': 0}
    if not path.exists():
        done = settled(home, channel, 0)
        if done is not None:
            return {**overdue, 'due': False, 'reason': 'already_performed', 'settled': done}
        return {**overdue, 'reason': 'no_period_recorded',
                'interrupted_attempt': interrupted_attempt(home, channel, 0)}
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
    done = settled(home, channel, value['sequence'])
    if done is not None:
        # The work for the next period is already recorded but its period was never
        # closed. Finish the commit from what was observed; do not read again.
        return {'due': False, 'reason': 'already_performed', 'period_seconds': period,
                'completed_at': value['completed_at'], 'due_at': due_at.isoformat(),
                'overdue_seconds': 0, 'sequence': value['sequence'], 'settled': done}
    late = observed - due_at
    answer = {'due': late >= timedelta(0),
              'reason': 'period_elapsed' if late >= timedelta(0) else 'not_due',
              'period_seconds': period, 'completed_at': value['completed_at'],
              'due_at': due_at.isoformat(),
              'overdue_seconds': max(0, int(late.total_seconds())),
              'sequence': value['sequence']}
    if answer['due']:
        answer['interrupted_attempt'] = interrupted_attempt(home, channel, value['sequence'])
    else:
        # The outcome of the period that IS closed. A run that lost its own receipt
        # writes it from this instead of claiming success it cannot re-observe.
        answer['outcome'] = settled(home, channel, value['sequence'], closed=True)
    return answer


def record_period(home, channel, period, completed_at, run_id):
    """Close this channel's period, counted from the run that did the work.

    Only ever called by the run that just performed the channel, so `completed_at` is
    always the time the reading actually happened - never a later run's clock.
    """
    path = regular(home / ('period-' + channel + '.json'))
    state = {'completed_at': completed_at, 'sequence': period['sequence'] + 1, 'run_id': run_id}
    write(path, state)
    if load_state(path) != state:
        raise StateError('period_readback_failed')
    return state


def observation(healthy, reason, detail):
    return {'healthy': healthy, 'reason': reason, 'observed_at': now(),
            'detail_sha256': digest(json.dumps(detail, sort_keys=True).encode())}


def commit_settled(home, result, periods, run_id):
    """Close the period of every channel whose work was already recorded.

    This is the second phase of a settle-then-commit that was interrupted. The health
    reported is the one that was actually observed then, read back from the record and
    validated against the period it closes - never a default, never a fresh guess, and
    never a state from an earlier period.
    """
    for channel in sorted(periods):
        done = periods[channel].get('settled')
        if done is None:
            continue
        result['settled_channels'][channel] = done
        if not done['healthy']:
            result['completed'] = False
        try:
            result['periods_recorded'][channel] = record_period(
                home, channel, periods[channel], done['observed_at'], done['run_id'])
        except StateError as error:
            result['periods_recorded'][channel] = {'error_code': str(error)}
            result['completed'] = False


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
        # Dueness is read after the cache, per channel, and it alone decides which
        # channels this wakeup reads. A channel inside its current period is skipped
        # entirely - no request, no receipt - and a channel still failing is retried
        # without holding back one that already did its week's work.
        bound = [channel for channel in CHANNELS if config.get(channel)]
        periods = ({channel: due(home, config, channel, run_id) for channel in bound}
                   if 'period_seconds' in config else {})
        wanted = [channel for channel in bound if not periods or periods[channel]['due']]
        skipped = sorted(channel for channel in bound if channel not in wanted)
        if not wanted:
            # Nothing is due. An ordinary tick inside the period reads nothing and
            # writes nothing at all, so it needs no run record; the native schedule
            # already counts it. A run whose own directory exists was interrupted after
            # doing the work, and `already_performed` says so rather than claiming the
            # period merely had not elapsed - that receipt is finished here.
            observed = now()
            commit_owed = any(periods[channel].get('settled') for channel in skipped)
            # This run's OWN outcome for a period already closed: it did the work and
            # then lost its receipt. Only its own - a later ordinary tick must not
            # inherit last week's incident.
            mine = {channel: periods[channel]['outcome'] for channel in skipped
                    if (periods[channel].get('outcome') or {}).get('run_id') == run_id}
            answer = {'run_id': run_id, 'config_sha256': config_sha256, 'completed': True,
                      'performed': False, 'performed_channels': [],
                      'skipped': 'already_performed' if (commit_owed or mine) else 'not_due',
                      'skipped_channels': skipped, 'periods': periods,
                      'periods_recorded': {}, 'settled_channels': {},
                      'started_at': observed, 'finished_at': observed}
            if commit_owed:
                # Work was recorded but its period was never closed. Finish that commit
                # and report the health that was actually observed then. This holds
                # however the other channels answered, not only when all of them did.
                commit_settled(home, answer, periods, run_id)
            for channel, outcome in sorted(mine.items()):
                answer['settled_channels'][channel] = outcome
                if not outcome['healthy']:
                    answer['completed'] = False
            if commit_owed or mine:
                answer['attested_by'] = 'settled_outcome'
            if output.exists() or commit_owed or mine:
                output.mkdir(mode=0o700, exist_ok=True)
                write(result_file, answer)
            return answer
        output.mkdir(mode=0o700, exist_ok=True)
        binding_file = output / 'binding.json'
        if binding_file.exists():
            if json.loads(binding_file.read_text()) != {'config_sha256': config_sha256}:
                raise ValueError('Interrupted run belongs to another configuration')
        else:
            write(binding_file, {'config_sha256': config_sha256})
        result = {'run_id': run_id, 'config_sha256': config_sha256, 'started_at': now(),
                  'completed': True, 'periods': periods, 'skipped_channels': skipped,
                  'deliveries': {}, 'performed_channels': [], 'periods_recorded': {},
                  'settled_channels': {}}
        commit_settled(home, result, periods, run_id)

        def bounded(channel, produce, failure=None):
            """One channel's own reading. With `failure` its errors are named so they
            cannot hide the other channels; without one they propagate, because a
            monitor binding that is wrong is a release error for the operator, not an
            incident to record for weeks (D038's behaviour, kept)."""
            # A prior interrupted consumer is resumed through its ordinary idempotency
            # journal; each attempt keeps all earlier output.
            if periods:
                note_attempt(home, channel, periods[channel]['sequence'], run_id)
            work = output / (channel + '-' + str(time.time_ns())); work.mkdir(mode=0o700)
            if failure is None:
                return produce(work)
            try:
                return produce(work)
            except (ValueError, OSError, KeyError, TypeError, subprocess.SubprocessError) as error:
                # Store only the error class, never credentials or tool output.
                return {**failure, 'error_type': type(error).__name__}

        def settle(channel, healthy, reason, performed):
            """Deliver this channel's transition and close its period at once.

            Closing here and not at the end is what keeps a later channel's failure -
            including a monitor binding error, which is raised on purpose - from
            preventing a check that already ran from closing its own week. Otherwise a
            standing monitor fault would turn the weekly drift check into an hourly one.
            """
            delivery = transition(home, channel, observation(healthy, reason, result[channel]))
            result['deliveries'][channel] = delivery
            if not healthy:
                result['completed'] = False
            if delivery['state_error']:
                result['completed'] = False
                return
            if not performed:
                result['completed'] = False
                return
            result['performed_channels'].append(channel)
            if not periods:
                return
            try:
                # Two phases: the outcome is durable before the period is closed, so an
                # interruption between them leaves the work findable instead of lost.
                settle_outcome(home, channel, periods[channel]['sequence'],
                               healthy, reason, run_id)
                result['periods_recorded'][channel] = record_period(
                    home, channel, periods[channel], result['started_at'], run_id)
            except StateError as error:
                result['periods_recorded'][channel] = {'error_code': str(error)}
                result['completed'] = False

        if 'intake' in wanted:
            result['intake'] = bounded('intake', lambda work: consume(config['intake'], work),
                                       {'completed': False, 'reason': 'consumer_failed'})
            done = result['intake']['completed']
            settle('intake', done, 'verified' if done else 'consumer_failed', done)
        if 'drift' in wanted:
            result['drift'] = bounded('drift', lambda work: drift(config['drift'], work),
                                      {'ran': False, 'reason': 'drift_binding_failed'})
            check = result['drift']
            settle('drift', check.get('healthy') is True, check['reason'], check['ran'])
        if 'monitor' in wanted:
            def probe(_work):
                observed = monitor(config['monitor'])
                observed['access_scope'] = ('internal_protection_bypass'
                                            if config['monitor'].get('bypass_file')
                                            else 'ordinary_endpoint')
                return observed
            # Deliberately last: its binding error is raised, and by now every other
            # channel has already delivered and closed its own period.
            result['monitor'] = bounded('monitor', probe)
            current = result['monitor']
            # `observed` False means no health answer was obtained at all - a bound that
            # ran out or a stranded-thread refusal. Nothing was checked, so the check is
            # still owed and the period stays open.
            settle('monitor', current['healthy'], current['reason'], current.get('observed') is True)

        result['performed_channels'].sort()
        result['performed'] = bool(result['performed_channels'])
        retried = sorted(channel for channel in wanted
                         if (periods.get(channel) or {}).get('interrupted_attempt'))
        if retried:
            # An earlier run started these readings and never recorded their outcome, so
            # whether they completed is unknown. Reading again is the honest answer -
            # closing a period whose result was never seen would hide the week - and it
            # happens exactly once, because this run does record its outcome.
            result['retried_after_interruption'] = retried
        if periods and any(value['reason'] == 'invalid_period_state' for value in periods.values()):
            result['completed'] = False
        result['finished_at'] = now(); write(result_file, result)
        return result
