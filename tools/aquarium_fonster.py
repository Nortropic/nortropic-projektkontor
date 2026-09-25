"""Aquarium v0's window: a user-owned reading process on 127.0.0.1 that keeps one page open.

The snapshot of `tools/aquarium_vy.py` is one page from one reading. This window lets that page stay
open, for example full screen or mirrored to a TV, without becoming a service: it is one process the
owner starts and stops, it listens only on 127.0.0.1, it serves only `GET /` and `GET /lasning.json`
to 127.0.0.1, and it pushes, starts, approves and changes nothing. A reading is made only when the
page asks for one, and at most every other minute (`INTERVALL`) counted from when the previous
reading began, so the sources are left alone while no page is open. One reading runs at a time; a
failed reading keeps the previous projection and its page and still counts as begun. The window
holds at most the latest projection and the page rendered from it in memory: no written file, no
event engine, no database and no history.

`jamfor` compares the two latest readings and lets the page show that the same work object has a new
observed state. That is an illustration of an updated state and nothing more: it never evidences
when, how, by which route or by whom the state changed, and it never describes a handover between
two executors, because the sources evidence none. At the first reading, after a restart or when the
basis is insufficient, only the current state is shown and no earlier transition is invented; the
same change is never replayed as new work. Freshness is not the window's to decide: the page decides
from its own reading's age, through the pinned `SKRIPT`, so nothing the window does or fails to do
can make a page look fresher than its reading.

Importing this module reads nothing, runs nothing, serves nothing and starts no thread. `jamfor` and
`svar` are pure; only `las` reads, and it reads exactly what the command of `tools/aquarium.py`
reads.
"""
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import sys
import threading
import time

import aquarium
import aquarium_vy

ADRESS = '127.0.0.1'
PORT = 8741
INTERVALL = 120
JAMFOR_GRANS = 300
ERROR = 'Ogiltig läsning för Aquariums fönster.'
COMMAND_ERROR = 'Kunde inte starta Aquariums fönster.'
HTML = 'text/html; charset=utf-8'
JSON = 'application/json; charset=utf-8'
TEXT = 'text/plain; charset=utf-8'
ONLY_GET = 'Fönstret tar bara emot läsförfrågningar.\n'
ONLY_LOCAL = 'Fönstret svarar bara på 127.0.0.1.\n'
NOT_FOUND = 'Finns inte.\n'
NO_READING = 'Ingen läsning ännu.\n'

DIGITS = '0123456789'
LOWEST_PORT = 1024
HIGHEST_PORT = 65535


def _refuse():
    raise ValueError(ERROR)


def las():
    """One bounded real reading, exactly the one the command of tools/aquarium.py makes."""
    office = Path(__file__).absolute().parents[1]
    return aquarium.project(aquarium.collect(office.parent / 'Nortropic Runtime', office),
                            datetime.now(timezone.utc))


# --- the comparison of two consecutive readings -------------------------------------


def _instant(value):
    """An aware ISO time as a point in time; anything else is no basis for a comparison."""
    if type(value) is not str:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except (ValueError, TypeError):
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return None
    return parsed


def _mellanrum(forra, nu):
    """The seconds from one read time to the next, fractions included, or None."""
    before, after = _instant(forra), _instant(nu)
    if before is None or after is None:
        return None
    return (after - before).total_seconds()


def _behall(states, seen, task, lage):
    """A task id seen twice in one reading is ambiguous and has no state in that reading."""
    if task in seen:
        states.pop(task, None)
        return
    seen.add(task)
    states[task] = lage


def _lagen(projection):
    """One reading's observed state per task: work with its step, or a task that does not work."""
    states, seen = {}, set()
    for item in projection['verkstaden']['items']:
        _behall(states, seen, item['task'],
                {'plats': 'arbete', 'step': item['step'], 'state': item['state'],
                 'executor': item['executor']})
    for item in projection['verkstaden']['parked']:
        _behall(states, seen, item['task'],
                {'plats': 'vilar', 'step': None, 'state': None, 'executor': None})
    return states


def jamfor(forra, nu):
    """Compare two consecutive projections. Pure: nothing is read, written or mutated.

    The result says only that a task's observed state differs from the previous reading's, never
    when, how or by whom it changed. Without a previous reading, or without a sound basis, the
    current state stands alone and no earlier transition is invented.
    """
    if forra is None:
        return {'grund': 'första', 'forra_read_at': None, 'uppdrag': {}}
    gap = _mellanrum(forra['read_at'], nu['read_at'])
    if (forra['provdata'] != nu['provdata']
            or forra['verkstaden']['status'] != 'ok' or nu['verkstaden']['status'] != 'ok'
            or gap is None or not 0 < gap <= JAMFOR_GRANS):
        return {'grund': 'otillräcklig', 'forra_read_at': None, 'uppdrag': {}}
    before, after = _lagen(forra), _lagen(nu)
    changed = {task: dict(lage) for task, lage in before.items()
               if task in after and after[task] != lage}
    return {'grund': 'jämförd', 'forra_read_at': forra['read_at'], 'uppdrag': changed}


# --- the window's state -------------------------------------------------------------


class Fonster:
    """The window's state: at most the latest projection and the page rendered from it.

    One reading at a time, guarded by one lock; the reading itself happens outside the lock, so a
    slow source never blocks an answer. A failed reading changes nothing but still counts as begun.
    """

    def __init__(self, reader=None, clock=None):
        self._reader = las if reader is None else reader
        self._clock = time.monotonic if clock is None else clock
        self._lock = threading.Lock()
        self._projektion = None
        self._sida = None
        self._pagar = False
        self._borjade = None

    def _las(self):
        """One reading: mark it running, read and render outside the lock, then keep or discard."""
        with self._lock:
            if self._pagar:
                return False
            self._pagar = True
            self._borjade = self._clock()
            latest = self._projektion
        try:
            ny = self._reader()
            sida = aquarium_vy.render(ny, jamfor(latest, ny))
        except Exception:
            with self._lock:
                self._pagar = False
            return False
        with self._lock:
            self._projektion, self._sida = ny, sida
            self._pagar = False
        return True

    def las_om(self):
        """Read now, whatever the interval."""
        return self._las()

    def kanske_las(self):
        """Read only when none runs and the interval has passed since the last one began."""
        with self._lock:
            if self._pagar:
                return False
            if self._borjade is not None and self._clock() - self._borjade < INTERVALL:
                return False
        return self._las()

    def read_at(self):
        """The latest projection's read time, or None before any successful reading."""
        with self._lock:
            return None if self._projektion is None else self._projektion['read_at']

    def sida(self):
        """The latest page, or None before any successful reading."""
        with self._lock:
            return self._sida


# --- the answers, the handler, the server and the command ---------------------------


def _headers(kind):
    """The same headers on every answer: no cache, no sniffing, no referrer, no embedding."""
    return [('Content-Type', kind), ('Cache-Control', 'no-store'),
            ('X-Content-Type-Options', 'nosniff'), ('Referrer-Policy', 'no-referrer'),
            ('Content-Security-Policy', "frame-ancestors 'none'")]


def svar(fonster, metod, sokvag, vard, klient, port):
    """One answer to one request. Pure but for the reading `/lasning.json` may ask the window for.

    The Host check keeps another page in the owner's browser from reading the window through another
    name for 127.0.0.1; only `/lasning.json` may start a reading, and only through `kanske_las`.
    """
    if metod != 'GET':
        return 405, [('Allow', 'GET')] + _headers(TEXT), ONLY_GET.encode('utf-8')
    if klient != ADRESS or vard != '%s:%d' % (ADRESS, port):
        return 403, _headers(TEXT), ONLY_LOCAL.encode('utf-8')
    if sokvag == '/':
        sida = fonster.sida()
        if sida is None:
            return 503, _headers(TEXT), NO_READING.encode('utf-8')
        return 200, _headers(HTML), sida.encode('utf-8')
    if sokvag == '/lasning.json':
        fonster.kanske_las()
        body = json.dumps({'read_at': fonster.read_at()}) + '\n'
        return 200, _headers(JSON), body.encode('utf-8')
    return 404, _headers(TEXT), NOT_FOUND.encode('utf-8')


class Handler(BaseHTTPRequestHandler):
    """A thin adapter: it decides nothing, answers only through `svar` and logs nothing."""

    server_version = 'Aquarium'

    def version_string(self):
        return self.server_version

    def log_message(self, format, *args):
        """The window keeps no log of what was asked for."""

    def _svara(self):
        status, headers, body = svar(self.server.fonster, self.command, self.path,
                                     self.headers.get('Host'), self.client_address[0],
                                     self.server.server_address[1])
        self.send_response(status)
        for name, value in headers:
            self.send_header(name, value)
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        if self.command != 'HEAD':
            self.wfile.write(body)

    do_GET = do_HEAD = do_POST = do_PUT = do_DELETE = do_PATCH = do_OPTIONS = _svara


def server(fonster, port):
    """One loopback server for one window; nothing is exposed outward."""
    made = ThreadingHTTPServer((ADRESS, port), Handler)
    made.daemon_threads = True
    made.fonster = fonster
    return made


def _port(text):
    """A port written as 4 or 5 digits, from 1024 to 65535; anything else is refused."""
    if type(text) is not str or not 4 <= len(text) <= 5:
        _refuse()
    if any(character not in DIGITS for character in text):
        _refuse()
    number = int(text)
    if not LOWEST_PORT <= number <= HIGHEST_PORT:
        _refuse()
    return number


def main(argv=None):
    arguments = sys.argv[1:] if argv is None else argv
    try:
        if not arguments:
            port = PORT
        elif len(arguments) == 2 and arguments[0] == '--port':
            port = _port(arguments[1])
        else:
            _refuse()
        fonster = Fonster()
        if not fonster.las_om():
            _refuse()
        served = server(fonster, port)
    except Exception:
        print(COMMAND_ERROR, file=sys.stderr)
        return 2
    print('Aquarium-fönstret: http://%s:%d/ · stoppa med Ctrl-C' % (ADRESS, port), flush=True)
    try:
        served.serve_forever()
    except KeyboardInterrupt:
        pass  # Ctrl-C is how the owner closes the window.
    finally:
        served.server_close()
    return 0


if __name__ == '__main__':
    sys.exit(main())
