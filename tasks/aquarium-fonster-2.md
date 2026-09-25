# Aquarium v0: the window — a local reading process on 127.0.0.1 and the comparison of two readings

Write `tools/aquarium_fonster.py` as sections 1 to 4 state, add the window mode to `tools/aquarium_vy.py` as section 5
states, write `tools/test_aquarium_fonster.py` as section 6 states and add the section of section 7 to `tools/AQUARIUM.md`.
Existing Runtime builds and tests this product; its review and integration follow the office's working form. Do not
modify any other file (in particular not `tools/aquarium.py`, `tools/test_aquarium.py` or `tools/test_aquarium_vy.py`),
any active execution, host acceptance or publication authority. Standard library only (Python 3.11+). No new services,
model calls, scheduler, database, history, written files or network access beyond the one loopback server of section 4.

Aquarium v0 is a calm, read-only view of the office's work world. `tools/aquarium.py` reads the office and Runtime into a
display-safe schema 2 projection, and `tools/aquarium_vy.py` renders one projection into one page, a snapshot. This task
makes the view a window that can stay open, for example full screen or mirrored to a TV: a user-owned process that
listens only on 127.0.0.1, reads the sources at most every other minute and only while a page is open, and serves the
latest page, which reloads itself when there is a newer reading. The owner also allowed one addition (d): compare two
consecutive readings and show that the same work object has a new observed state. Truth governs everything below:

- A new observed state is an illustration of an updated state, never evidence of when, how, by which route or by whom it
  changed, and never a handover between two executors. The sources evidence no handover, so the window never describes
  one.
- At the first reading, after a restart or when the basis is insufficient, only the current state is shown, without an
  invented earlier transition. The same change is not replayed as new work.
- Freshness fails closed: the page decides from its own reading's age whether it is fresh. Nothing the window does or
  fails to do can make the page look fresher.
- Minimal presentation logic: two readings in memory, no event engine, database, history or written file.

The texts in `code format` below are exact, character for character (the page and the messages are Swedish).

## 1. `tools/aquarium_fonster.py`: module, constants and the real reading

A module docstring states what the window is and does, truthfully and in line with this brief. The module imports
`aquarium` and `aquarium_vy` (the office's modules beside it) at module level. Importing it reads nothing, runs nothing,
serves nothing and starts no thread.

Constants, exactly: `ADRESS = '127.0.0.1'`, `PORT = 8741`, `INTERVALL = 120`, `JAMFOR_GRANS = 300`,
`ERROR = 'Ogiltig läsning för Aquariums fönster.'`, `COMMAND_ERROR = 'Kunde inte starta Aquariums fönster.'`,
`HTML = 'text/html; charset=utf-8'`, `JSON = 'application/json; charset=utf-8'`, `TEXT = 'text/plain; charset=utf-8'`,
`ONLY_GET = 'Fönstret tar bara emot läsförfrågningar.\n'`, `ONLY_LOCAL = 'Fönstret svarar bara på 127.0.0.1.\n'`,
`NOT_FOUND = 'Finns inte.\n'` and `NO_READING = 'Ingen läsning ännu.\n'`.

`las()` makes one bounded real reading exactly as the command of `tools/aquarium.py` does: with
`office = Path(__file__).absolute().parents[1]` it returns
`aquarium.project(aquarium.collect(office.parent / 'Nortropic Runtime', office), datetime.now(timezone.utc))`. Call
`collect` and `project` through the module (`aquarium.collect`, `aquarium.project`), never through names imported from it.

## 2. `jamfor(forra, nu) -> dict` (pure)

The comparison of two consecutive readings, where `forra` is the previous projection or `None` and `nu` the current one
(both schema 2 projections as `aquarium.project` returns them). It reads, writes and mutates nothing and returns a new
dict with exactly the keys `grund`, `forra_read_at` and `uppdrag`:

1. `forra` is `None` (the first reading, or the first after a restart): `{'grund': 'första', 'forra_read_at': None,
   'uppdrag': {}}`.
2. The basis is insufficient when `forra['provdata'] != nu['provdata']`, when `forra['verkstaden']['status']` or
   `nu['verkstaden']['status']` is not `'ok'` (the engine could not be read in one of them), or when the number of seconds
   from `forra['read_at']` to `nu['read_at']` (both aware ISO times, compared as instants, fractions of a second included)
   is not greater than 0 and at most `JAMFOR_GRANS`. Then: `{'grund': 'otillräcklig', 'forra_read_at': None, 'uppdrag': {}}`.
3. Otherwise `{'grund': 'jämförd', 'forra_read_at': forra['read_at'], 'uppdrag': changed}`, with `forra['read_at']`
   exactly as given. A reading's observed state of a task: each item in `verkstaden['items']` gives its `task` the state
   `{'plats': 'arbete', 'step': item['step'], 'state': item['state'], 'executor': item['executor']}`, and each item in
   `verkstaden['parked']` gives its `task` the state `{'plats': 'vilar', 'step': None, 'state': None, 'executor': None}`.
   A task id that occurs more than once in a reading (twice in one list or once in each) is ambiguous and has no state in
   that reading. `changed` maps every task that has a state in both readings, where the two states differ, to its state in
   `forra` (a new dict, not shared with anything else). A task only in one of the readings is never in `changed`, and a
   different title, start time or activity list with the same step, state and executor is no change.

## 3. `class Fonster`: the window's state

`Fonster(reader=None, clock=None)`: `reader` is a function without arguments that returns one projection (default the
module's `las`, looked up when the object is made); `clock` is a function without arguments that returns seconds as a
number (default `time.monotonic`). A new window holds no projection and no page, reads nothing and starts nothing. It
guards its state with one `threading.Lock` and holds at most the latest projection and the page rendered from it.

A reading: if a reading is already running (in another thread, or inside the reader itself), return `False` at once
without calling the reader. Otherwise mark a reading as running and record `clock()` as the time the reading began,
then, outside the lock, call the reader and render its projection with
`aquarium_vy.render(new, jamfor(latest, new))`, where `latest` is the projection the window held when the reading began.
If the reader or the rendering raises any `Exception`, keep the latest projection and page unchanged, clear the running
mark and return `False`; the reading still counts as begun at its recorded time. Otherwise replace the latest projection
and page with the new ones, clear the running mark and return `True`.

- `las_om()` makes a reading now, whatever the interval.
- `kanske_las()` makes a reading only when no reading runs and either no reading has begun yet or
  `clock() - <the time the last reading began> >= INTERVALL`; otherwise it returns `False` without calling the reader.
- `read_at()` returns the latest projection's `read_at`, or `None` before any successful reading.
- `sida()` returns the latest page (a `str`), or `None` before any successful reading.

## 4. The answers, the handler, the server and the command

`svar(fonster, metod, sokvag, vard, klient, port) -> (status, headers, body)` answers one request: `metod` the request
method, `sokvag` the request path exactly as received, `vard` the `Host` header or `None`, `klient` the client address
and `port` the server's port. `headers` is a list of `(name, value)` pairs and `body` is `bytes` (UTF-8). With
`_headers(kind) = [('Content-Type', kind), ('Cache-Control', 'no-store'), ('X-Content-Type-Options', 'nosniff'),
('Referrer-Policy', 'no-referrer'), ('Content-Security-Policy', "frame-ancestors 'none'")]`, in this order and by the
first rule that applies:

1. `metod` is not `GET`: `405`, `[('Allow', 'GET')] + _headers(TEXT)`, `ONLY_GET`.
2. `klient` is not `ADRESS`, or `vard` is not exactly `'%s:%d' % (ADRESS, port)`: `403`, `_headers(TEXT)`, `ONLY_LOCAL`.
3. `sokvag` is `/`: `fonster.sida()`; when it is `None`, `503`, `_headers(TEXT)`, `NO_READING`; otherwise `200`,
   `_headers(HTML)` and the page.
4. `sokvag` is `/lasning.json`: first `fonster.kanske_las()`, then `200`, `_headers(JSON)` and
   `json.dumps({'read_at': fonster.read_at()}) + '\n'`.
5. Anything else: `404`, `_headers(TEXT)`, `NOT_FOUND`.

Only rule 4 may start a reading, and only through `kanske_las`; no other rule calls anything on `fonster` but `sida` (rule 3).

`class Handler(BaseHTTPRequestHandler)`, a thin adapter that logs nothing (import both `BaseHTTPRequestHandler` and
`ThreadingHTTPServer` at module level with `from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer`):
`server_version = 'Aquarium'`; `version_string()` returns `self.server_version`, so the `Server` header is exactly
`Aquarium`; `log_message` does nothing; `do_GET`, `do_HEAD`, `do_POST`, `do_PUT`, `do_DELETE`, `do_PATCH` and
`do_OPTIONS` all call one method that asks `svar(self.server.fonster, self.command, self.path, self.headers.get('Host'),
self.client_address[0], self.server.server_address[1])`, sends the status with `send_response`, each header with
`send_header`, then `Content-Length` with the body's length, ends the headers and writes the body unless the method is
`HEAD`. Keep http.server's default protocol version and its default answers to other methods and malformed requests.

`server(fonster, port)` returns `ThreadingHTTPServer((ADRESS, port), Handler)` (the name imported from `http.server` at
module level and looked up when `server` runs) with `daemon_threads = True` and the attribute `fonster` set to the window.

`main(argv=None)` (the arguments are `sys.argv[1:]` when `argv` is `None`), and `if __name__ == '__main__':
sys.exit(main())`. The arguments are either none (port `PORT`) or exactly `--port` and a number written as 4 or 5 digits
from 1024 to 65535; anything else is refused before anything is read. Then make `Fonster()`, call its `las_om()` and
refuse if it returns `False`, then make the server with `server(...)`. If any of this raises, or is refused, print only
`COMMAND_ERROR` to standard error and return `2`, with nothing on standard output. Otherwise print
`'Aquarium-fönstret: http://%s:%d/ · stoppa med Ctrl-C' % (ADRESS, port)` to standard output with `flush=True`, then
`serve_forever()`; a `KeyboardInterrupt` ends it quietly, the server is closed with `server_close()` in every case after
serving began, and `main` returns `0`.

## 5. The window mode in `tools/aquarium_vy.py`

`SCEN` and `SKRIPT` stay byte for byte as they are, and so does everything `render(projection)` does today: called with
one argument, or with `None` as its second, `render` returns exactly the page it returns at the base, and `csp()` is
unchanged. Add, next to `SKRIPT`, this constant, exactly (two spaces per indentation level, no trailing spaces, no newline
before the closing quotes):

```
FONSTERSKRIPT = '''(function () {
  var read = document.body.getAttribute('data-read-at');
  function poll() {
    fetch('/lasning.json', {cache: 'no-store'}).then(function (answer) {
      return answer.ok ? answer.json() : null;
    }).then(function (latest) {
      if (latest && typeof latest.read_at === 'string' && latest.read_at !== read) location.reload();
    }).catch(function () {});
  }
  poll();
  setInterval(poll, 30000);
})();'''
```

and `fonster_csp()`, which returns `"default-src 'none'; style-src 'unsafe-inline'; script-src 'sha256-<S>' 'sha256-<F>';
connect-src 'self'; base-uri 'none'; form-action 'none'"` as one line, where `<S>` and `<F>` are the base64 of the SHA-256
of `SKRIPT` and of `FONSTERSKRIPT` (UTF-8), like `csp()` does for `SKRIPT`; compute it at import, as `csp()` is.

`render(projection, jamforelse=None)`. With a comparison (not `None`) the page is the window's page. The comparison is
first checked, and anything else raises `ValueError(ERROR)`, the module's existing refusal: a dict with exactly the keys
`grund`, `forra_read_at` and `uppdrag`; `grund` is `första`, `otillräcklig` or `jämförd`; `uppdrag` is a dict; for
`jämförd`, `forra_read_at` is an aware ISO time (as `_moment` accepts it); for the other two, `forra_read_at` is `None` and
`uppdrag` is empty; each key of `uppdrag` is a string and each value a dict with exactly the keys `plats`, `step`,
`state` and `executor`, where `plats` is `vilar` with the other three `None`, or `arbete` with `step` and `state` strings
and `executor` `None` or a string. Then, compared with the snapshot of the same projection, and nothing else:

- `AQ_CSP` is `fonster_csp()` instead of `csp()`.
- `AQ_BODY_CLASS` is `aq-provdata aq-fonsterlage` for a provdata projection and `aq-fonsterlage` otherwise.
- The script slot holds `'<script>' + SKRIPT + '</script><script>' + FONSTERSKRIPT + '</script>'`.
- Marks: the class value of every place that shows a task whose `task` is a key of `uppdrag` gets ` aq-nytt-lage`
  appended (a space and the class): a bench (`AQ_BANK_n_CLASS`), the review desk (`AQ_GRANSK_CLASS`, which shows the first
  desk task) or a board card (`AQ_PARK_n_CLASS`). A place that shows no task never gets it, and a task beyond the shown
  places gets no mark, only its row below.
- Rows: the row of every such task in the Verkstaden panel (`Pågår` and `Arbetar inte`) and in the Granskningen panel
  (`Granskas` and `Integreras`) gets ` · nytt läge; förra läsningen <TID(forra_read_at)>: <FÖRRA(its state in uppdrag)>`
  appended to its text. `FÖRRA(state)` is `arbetade inte` for `vilar`; for `arbete` it is `utförande · ` followed by
  `EXEC(executor)` or, when the executor is `None`, `utförare ej belagd`, for the step `utförande`; `granskning` for
  `granskning`; `integration` for `integration`; `steg pågår` for `steg`; and `arbetsflödessteg` for any other step.
- The Verkstaden list gets one more row, last, in every case (also when the engine could not be read): the label
  `Jämförelse` and the text `JÄMFÖRELSE(jamforelse)`, which is
  `första läsningen sedan fönstret startade; bilden visar bara aktuellt läge` for `första`,
  `underlaget räcker inte för en jämförelse; bilden visar bara aktuellt läge` for `otillräcklig`, and for `jämförd`
  `jämfört med läsningen <TID(forra_read_at)>: ` followed by `inget uppdrag i nytt läge` when `uppdrag` is empty, else
  `1 uppdrag i nytt läge` or `<n> uppdrag i nytt läge` (n the number of keys of `uppdrag`), followed by
  `; nytt läge visar det uppdaterade läget, inte när eller hur det ändrades`.

`render` stays pure (no file, clock, process or network; inputs never mutated; the same inputs give the same page). The
mark classes and the window's footer line already exist in `SCEN`; the arrival of a mark is already styled there, once in
the fresh look, only on a bench and at the review desk. Update the module docstring so that it describes the window mode
truthfully and no longer says that `render` sets neither class; it must not claim that `SCEN` changed.

## 6. Tests

You work with file tools only and cannot run the tests, so make every assertion follow from a rule of this brief and read
the code you test against. `tools/test_aquarium.py` and `tools/test_aquarium_vy.py` stay unchanged; they are not
affected, because `render(projection)` with one argument keeps giving the base page, and the host runs them beside yours.
`tools/test_aquarium_fonster.py` may import the helpers `projection`, `work`, `parked` and `sources` from
`test_aquarium_vy` and uses only synthetic projections (provdata true) and fakes. It never binds or opens a socket and
never calls `serve_forever` on a real server: the sandbox refuses every socket, loopback included, with
`PermissionError`. So ask `svar` directly, drive `Handler` through an in-memory connection (an object whose `makefile(mode,
*args, **kwargs)` returns an `io.BytesIO` of the raw request and whose `sendall(data)` collects the response) with a
server stand-in that has `fonster` and `server_address`, and replace `ThreadingHTTPServer` and `las` in the module (for
example with `unittest.mock.patch.object`) to test `server` and `main`. At least 15 tests, covering: `jamfor` for each
rule (the first reading; no change; a change of step, of plats in both directions and of executor; new, vanished and
repeated tasks; an unread engine in either reading; a provdata difference; a gap of 0, below 0, of exactly 300 and above
300 seconds; that the result shares nothing with the inputs); the window page (both scripts in order, the policy, the
body class, marks exactly on the shown compared tasks and never on an empty place, the row texts, the comparison row for
each `grund`, no handover wording) and the snapshot unchanged; refused comparisons; the window's cadence with a fake
clock (not before 120 seconds, at 120 seconds), a failed reading that keeps the page and still counts, the comparison
with the latest good reading, a restart without an earlier change, and no second reading while one runs; every rule of
`svar`; the handler's answers and its silence on standard error; `server`; and `main` with the printed line, the port
bounds, wrong arguments and a failed first reading.

Pitfalls of exactly this kind ended the first attempt at this task: its product met every frozen check, and one of its
own tests failed on a detail that only running the tests would have shown. Read each of your assertions against the
exact bytes your code and http.server produce, and mind in particular:

- A raw response split at the first `b'\r\n\r\n'` leaves a header block with no CRLF after its last line, and
  http.server sends `Content-Length` last, just before the blank line. Find a header by splitting the block with
  `split(b'\r\n')` and comparing whole lines, never by searching the block for `b'Name: value\r\n'`.
- http.server adds `Server` and `Date` to every answer; never assert the whole header block byte for byte.
- The page's style sheet names the classes `aq-fonsterlage` and `aq-nytt-lage` whether or not an element has them, so
  assert on the body tag (`<body class="...">`) or on a place's class attribute (`class="... aq-nytt-lage"`), never on
  the bare class name anywhere in the page.
- `json.dumps({'read_at': ...})` writes a space after the colon: `{"read_at": "..."}`.
- The log methods of `BaseHTTPRequestHandler` write to `sys.stderr` unless overridden, so the handler's silence is seen
  with `contextlib.redirect_stderr`; `redirect_stdout` is where `main`'s printed line goes.
- Replace a module attribute where the code looks it up (`unittest.mock.patch.object(aquarium_fonster, 'las', ...)`,
  `patch.object(aquarium_fonster, 'ThreadingHTTPServer', ...)`); replacing a name in another module changes nothing.

How the host verifies, as measured: it copies only the four files of this task into a fresh clone of the repository at
the base (no `TASK.md` and nothing else uncommitted is there) and runs its frozen acceptance in that clone inside a
sandbox. There the repository is read-only except the existing `.scratch` directory, which must never be removed,
replaced or recreated, and which your tests must leave exactly as they found it. There is no network and no socket. The
environment is minimal: rely on nothing beyond `PATH`, `HOME` and `LANG`; `TMPDIR` may not be writable. Python runs with
`-I -B`. The host audits `jamfor`, `render`, `svar` and a `Fonster` with a fake reader and clock for any file, process,
socket, `os` or `ctypes` event, so nothing is imported, opened or run inside them; it checks that importing the module
reads and starts nothing; it drives the handler through an in-memory connection, `server` and `main` with replaced
server and reader, and `las` with replaced `aquarium.collect` and `aquarium.project`; and it runs
`python3 -I -B -m unittest discover -s tools -p test_aquarium_fonster.py`, `... -p test_aquarium_vy.py` and
`... -p test_aquarium.py`, each of which must pass.

## 7. `tools/AQUARIUM.md`

Keep everything that is there, with two corrections of the section `## Scenen` and one of the introduction, and add a
Swedish section `## Fönstret` at the end:

- The introduction names `tools/aquarium_fonster.py`, which keeps the page open as a local window.
- `## Scenen` says that the page is a snapshot, and that in the window it is reloaded when there is a new reading (see
  Fönstret); and that besides never reading a source or calling a model, the page fetches nothing over the network except
  that the window's page asks its own window on 127.0.0.1 for the latest read time.
- `## Fönstret`: the command `python3 -B tools/aquarium_fonster.py [--port PORT]` in a code block; the first reading, the
  address 127.0.0.1 with port 8741 or the given one (1024-65535), the printed line, Ctrl-C and exit 0, exit 2 and the
  line `Kunde inte starta Aquariums fönster.` for wrong arguments, a failed first reading or a port that cannot be
  opened, and that it is a user-owned process with no start at login, no background service and no outward network;
  opening the address in Chrome in full screen and mirroring the screen to the TV; `FONSTERSKRIPT`, pinned beside
  `SKRIPT` in the window page's policy, asking every 30 seconds for the latest read time from `/lasning.json` and
  reloading the page when it differs, an open panel staying open; the reading cadence (only when the page asks and at
  least 120 seconds after the previous reading began, so högst varannan minut and only while a page is open; one at a
  time; a failed reading keeps the previous one and still counts); freshness decided by the page's own `SKRIPT`, never
  by the window script, so that a stopped window or a sleeping computer gives a page that becomes `inaktuell` when its
  reading is older than five minutes (checked every 30 seconds); `nytt läge`: only the window's two latest readings,
  what counts as the observed state, where the mark appears and what the deep dive says, that it says only that the
  state differs from the previous reading, not when, how or by whom it changed, and that it describes no överlämning;
  when there is no comparison and that the deep dive says which; that the mark concerns only the reading after the
  change, arrives once on a bench and at the review desk in the fresh look, and that a board card never moves; memory,
  not history (the latest reading and its page in memory, no written file, no event engine, database or history); only
  `GET` of `/` and `/lasning.json`, only from 127.0.0.1 with the host name `127.0.0.1:PORT`, 405, 403 and 404 with a
  fixed line otherwise and 503 for `/` before the first reading, no cache, no embedding, no log; and how the tests work
  without a socket.

The host checks that the file keeps `## Scenen`, that `## Fönstret` comes after it, that the file is at least 2 500
characters longer than at the base, and that it contains word for word (any run of whitespace, line breaks included,
counts as one space) `python3 -B tools/aquarium_fonster.py [--port PORT]`, `127.0.0.1`, `8741`, `nytt läge`,
`högst varannan minut`, `Kunde inte starta Aquariums fönster.`, `inaktuell`, `överlämning`, `/lasning.json` and
`FONSTERSKRIPT`. A separate review checks that it is true.

## 8. Design notes (for understanding; the rules above govern)

The window is the build decision's stage 2: a user-owned reading process on 127.0.0.1 that re-reads the sources at most
every other minute while the view is open; the page fetches the latest reading; nothing is pushed out and nothing is
replayed. Reading on demand keeps the sources untouched when no page is open. The page reloads itself rather than
patching its content, so that the renderer stays the only place that turns a projection into a page, and the pinned
`SKRIPT` keeps deciding freshness at every load. A reload happens only when the read time differs, so a change is shown
once, on the page of the reading that follows it; the next reading compares again and the mark is gone unless the state
changed again. The previous reading's time in the rows is a reading time, not an event time. The Host check keeps other
web pages in the owner's browser from reading the window through another name for 127.0.0.1.
