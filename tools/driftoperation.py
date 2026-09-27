"""Office's bounded intake/monitor handler. Runtime/Temporal supplies the schedule.

No model execution, publication, mail or arbitrary command is selected by input
events. This module is loaded only from the reviewed release with frozen config.
The local recipient is Office's private incident inbox; it is not an email claim.
"""
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request


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
    for number in range(2):
        transient = False
        try:
            with opener.open(urllib.request.Request(config['url'], headers=headers), timeout=8) as response:
                raw = response.read(65537)
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


def consume(config, output):
    root = regular(config['digitala_root'])
    files = config['digitala_files']
    if not files or 'verktyg/kundstart.py' not in files:
        raise ValueError('Missing frozen Digitala consumer')
    for name, expected in files.items():
        relative = Path(name)
        if relative.is_absolute() or '..' in relative.parts:
            raise ValueError('Unsafe consumer file')
        path = regular(root / relative)
        if digest(path.read_bytes()) != expected:
            raise ValueError('Digitala consumer changed after release review')
    if any(str(path.relative_to(root)) not in files for path in (root / 'verktyg').rglob('*.py')):
        raise ValueError('Unbound Python module in consumer directory')
    environment = {k: v for k, v in os.environ.items() if k in ('PATH', 'HOME', 'LANG', 'LC_ALL', 'TMPDIR')}
    environment.update(PYTHONDONTWRITEBYTECODE='1', KUNDSTART_BAS_URL=config['base_url'],
                       KUNDSTART_NYCKEL_FIL=str(regular(config['key_file'])))
    if config.get('bypass_file'):
        environment['KUNDSTART_BYPASS_FIL'] = str(regular(config['bypass_file']))
    argv = [sys.executable, '-B', str(root / 'verktyg/kundstart.py'), 'konsumera',
            '--kund', str(regular(config['customer'])), '--utforare', config['executor']]
    with (output / 'intake.stdout').open('xb') as out, (output / 'intake.stderr').open('xb') as err:
        process = subprocess.Popen(argv, cwd=root, env=environment, stdout=out, stderr=err,
                                   start_new_session=True)
        try:
            status = process.wait(timeout=120)
        except subprocess.TimeoutExpired:
            import signal
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL); process.wait(timeout=3)
            return {'completed': False, 'reason': 'consumer_timeout'}
    return {'completed': status == 0, 'returncode': status,
            'stdout_sha256': digest((output / 'intake.stdout').read_bytes()),
            'stderr_sha256': digest((output / 'intake.stderr').read_bytes())}


def deliver(home, event):
    """The private Office inbox consumes each stable event once, including retries."""
    inbox = home / 'inbox'; inbox.mkdir(mode=0o700, exist_ok=True)
    target = regular(inbox / (event['id'] + '.json'))
    if target.exists():
        existing = json.loads(target.read_text())
        if existing['event'] != event:
            raise ValueError('Incident id collision')
        return existing['receipt']
    receipt = {'recipient': 'kontorets-privata-driftyta', 'received_at': now(), 'event_id': event['id']}
    write(target, {'event': event, 'receipt': receipt})
    # Read back the recipient's durable record before acknowledging delivery.
    if json.loads(target.read_text())['event'] != event:
        raise ValueError('Incident recipient readback failed')
    return receipt


def run(config, run_id):
    if config.get('schema') != 'office-drift/1' or not re.fullmatch('[a-zA-Z0-9-]{1,100}', run_id):
        raise ValueError('Unknown operation schema or run identity')
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
        if config.get('monitor'):
            current = monitor(config['monitor']); result['monitor'] = current
            state_file = regular(home / 'monitor.json')
            previous = json.loads(state_file.read_text()) if state_file.exists() else {'healthy': True, 'sequence': 0}
            # Persist an outbox item BEFORE delivery. A crash resumes the same event.
            pending = home / 'pending.json'
            if pending.exists():
                event = json.loads(pending.read_text())
                deliver(home, event)
                write(state_file, event['state']); pending.unlink()
                previous = event['state']
            if current['healthy'] != previous['healthy']:
                state = {'healthy': current['healthy'], 'sequence': previous['sequence'] + 1,
                         'observed_at': current['observed_at']}
                event = {'id': 'incident-%06d' % state['sequence'], 'kind': 'recovered' if current['healthy'] else 'incident',
                         'state': state, 'observation': current}
                write(pending, event)
                result['delivery'] = deliver(home, event)
                write(state_file, state); pending.unlink()
            result['completed'] = result['completed'] and current['healthy']
        result['finished_at'] = now(); write(result_file, result)
        return result
