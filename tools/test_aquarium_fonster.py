"""Synthetic tests for Aquarium v0's window. No real source, no socket, no network, no model call.

Every projection here is made up and marked `provdata`, every reader and clock is a fake, and no
test binds, opens or connects a socket: the handler is driven through an in-memory connection, and
`server` and `main` are tested with the server and the reading replaced. Nothing is written, so the
repository's existing `.scratch` is left exactly as it was found.
"""
import base64
from contextlib import redirect_stderr, redirect_stdout
from copy import deepcopy
import hashlib
import io
import json
import unittest
from unittest.mock import patch

import aquarium_fonster
import aquarium_vy
from test_aquarium_vy import parked, projection, sources, work

READ1 = '2026-09-24T12:52:00+00:00'            # 24 sep 14:52 in Stockholm
READ2 = '2026-09-24T12:54:00+00:00'            # 120 seconds later, 14:54
READ3 = '2026-09-24T12:55:00+00:00'            # 180 seconds after READ1, 14:55
GRANS = '2026-09-24T12:57:00+00:00'            # exactly 300 seconds after READ1
OVER = '2026-09-24T12:57:00.500000+00:00'      # 300.5 seconds after READ1

VILAR = {'plats': 'vilar', 'step': None, 'state': None, 'executor': None}
ARBETE = {'plats': 'arbete', 'step': 'utförande', 'state': 'pågår', 'executor': 'claude'}
FIRST = {'grund': 'första', 'forra_read_at': None, 'uppdrag': {}}
GRANSKNING = dict(work(task='office-gransk', step='granskning', state='granskas', executor=None,
                       activities=('review_candidate',)))


def lage(**overrides):
    return dict(ARBETE, **overrides)


def arbetsvarld(read_at=READ2, items=(), parkerade=()):
    """One synthetic projection whose workshop is what the test needs it to be."""
    return projection(read_at=read_at,
                      verkstaden={'status': 'ok', 'items': list(items),
                                  'parked': list(parkerade), 'titles': 'ok'})


def ingen_motor(read_at=READ2):
    return projection(read_at=read_at, sources=sources(unavailable=('engine', 'tasks')),
                      headline={'pagar': None, 'vantar': 0, 'behover_dig': 0, 'lugnt': False},
                      verkstaden={'status': 'otillgänglig', 'items': [], 'parked': [],
                                  'titles': 'otillgänglig'})


class Klocka:
    """A clock the test owns: seconds, and no relation to the wall clock."""

    def __init__(self, nu=1000.0):
        self.nu = nu

    def __call__(self):
        return self.nu


class Misslyckad(Exception):
    """A reading that fails, as a source that cannot be read makes one fail."""


class Lasare:
    """A reader that hands out prepared projections; an exception stands for a failed reading."""

    def __init__(self, svar):
        self.svar = list(svar)
        self.antal = 0

    def __call__(self):
        self.antal += 1
        item = self.svar.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


class Aterkommande:
    """A reader that asks its own window to read while it is reading."""

    def __init__(self, projektion):
        self.projektion = projektion
        self.fonster = None
        self.antal = 0
        self.inre = None

    def __call__(self):
        self.antal += 1
        self.inre = self.fonster.las_om()
        return self.projektion


class FalsktFonster:
    """A window stand-in that records exactly what `svar` asked it for."""

    def __init__(self, sida=None, read_at=None):
        self._sida = sida
        self._read_at = read_at
        self.anrop = []

    def sida(self):
        self.anrop.append('sida')
        return self._sida

    def read_at(self):
        self.anrop.append('read_at')
        return self._read_at

    def kanske_las(self):
        self.anrop.append('kanske_las')
        return True

    def las_om(self):
        self.anrop.append('las_om')
        return True


class Skrivning(io.RawIOBase):
    """The write side of the in-memory connection."""

    def __init__(self, koppling):
        self.koppling = koppling

    def writable(self):
        return True

    def write(self, data):
        self.koppling.sendall(data)
        return len(data)


class Koppling:
    """An in-memory connection: the raw request is read from memory and the answer is collected."""

    def __init__(self, raw):
        self.raw = raw
        self.sent = bytearray()

    def makefile(self, mode, *args, **kwargs):
        return Skrivning(self) if 'w' in mode else io.BytesIO(self.raw)

    def sendall(self, data):
        self.sent += bytes(data)


class Vard:
    """A server stand-in with only what the handler asks of it."""

    def __init__(self, fonster, port=aquarium_fonster.PORT):
        self.fonster = fonster
        self.server_address = (aquarium_fonster.ADRESS, port)


class FalskServer:
    """Stands in for one ThreadingHTTPServer; it binds nothing and serves nothing."""

    def __init__(self, address, handler, avbryt=False):
        self.server_address = address
        self.handler = handler
        self.avbryt = avbryt
        self.daemon_threads = False
        self.fonster = None
        self.servad = 0
        self.stangd = 0

    def serve_forever(self):
        self.servad += 1
        if self.avbryt:
            raise KeyboardInterrupt

    def server_close(self):
        self.stangd += 1


class Fabrik:
    """Stands in for the name `ThreadingHTTPServer` in the module."""

    def __init__(self, avbryt=False):
        self.gjorda = []
        self.avbryt = avbryt

    def __call__(self, address, handler):
        made = FalskServer(address, handler, self.avbryt)
        self.gjorda.append(made)
        return made


def begar(metod='GET', sokvag='/', vard='127.0.0.1:%d' % aquarium_fonster.PORT):
    linjer = ['%s %s HTTP/1.1' % (metod, sokvag)]
    if vard is not None:
        linjer.append('Host: ' + vard)
    return ('\r\n'.join(linjer) + '\r\n\r\n').encode('utf-8')


def kor(raw, fonster, port=aquarium_fonster.PORT, klient='127.0.0.1'):
    """One request through the in-memory connection; the answer and anything on standard error."""
    koppling = Koppling(raw)
    fel = io.StringIO()
    with redirect_stderr(fel):
        aquarium_fonster.Handler(koppling, (klient, 51000), Vard(fonster, port))
    return bytes(koppling.sent), fel.getvalue()


def delar(answer):
    """The header block's whole lines and the body; the block has no CRLF after its last line."""
    head, _, body = answer.partition(b'\r\n\r\n')
    return head.split(b'\r\n'), body


class Jamforelsen(unittest.TestCase):
    def test_the_first_reading_shows_only_the_current_state(self):
        self.assertEqual(aquarium_fonster.jamfor(None, arbetsvarld(items=[work()])), FIRST)

    def test_no_change_is_no_task_in_a_new_state(self):
        forra = arbetsvarld(read_at=READ1, items=[work()], parkerade=[parked()])
        nu = arbetsvarld(read_at=READ2, items=[work()], parkerade=[parked()])
        self.assertEqual(aquarium_fonster.jamfor(forra, nu),
                         {'grund': 'jämförd', 'forra_read_at': READ1, 'uppdrag': {}})

    def test_a_different_title_start_or_activity_is_no_change(self):
        forra = arbetsvarld(read_at=READ1, items=[work(activities=('execute_claude',))],
                            parkerade=[parked(title='En rubrik')])
        nu = arbetsvarld(read_at=READ2,
                         items=[work(activities=('execute_claude', 'extra'),
                                     since='2026-09-24T10:00:00+00:00', kind='Annat')],
                         parkerade=[parked(title='En annan rubrik')])
        self.assertEqual(aquarium_fonster.jamfor(forra, nu)['uppdrag'], {})

    def test_a_changed_step_is_a_new_state(self):
        forra = arbetsvarld(read_at=READ1, items=[work()])
        nu = arbetsvarld(read_at=READ2, items=[dict(GRANSKNING, task='office-bygge')])
        result = aquarium_fonster.jamfor(forra, nu)
        self.assertEqual(result['grund'], 'jämförd')
        self.assertEqual(result['forra_read_at'], READ1)
        self.assertEqual(result['uppdrag'], {'office-bygge': lage()})

    def test_a_changed_executor_is_a_new_state(self):
        forra = arbetsvarld(read_at=READ1, items=[work(executor='claude')])
        nu = arbetsvarld(read_at=READ2, items=[work(executor='codex')])
        self.assertEqual(aquarium_fonster.jamfor(forra, nu)['uppdrag'],
                         {'office-bygge': lage(executor='claude')})

    def test_a_changed_place_is_a_new_state_in_both_directions(self):
        working = arbetsvarld(read_at=READ1, items=[work()])
        resting = arbetsvarld(read_at=READ2, parkerade=[parked(task='office-bygge')])
        later = arbetsvarld(read_at=GRANS, items=[work()])
        self.assertEqual(aquarium_fonster.jamfor(working, resting)['uppdrag'],
                         {'office-bygge': lage()})
        self.assertEqual(aquarium_fonster.jamfor(resting, later)['uppdrag'],
                         {'office-bygge': dict(VILAR)})

    def test_a_new_or_vanished_task_is_never_a_new_state(self):
        forra = arbetsvarld(read_at=READ1, items=[work(task='office-borta')])
        nu = arbetsvarld(read_at=READ2, items=[work(task='office-ny')])
        self.assertEqual(aquarium_fonster.jamfor(forra, nu)['uppdrag'], {})

    def test_a_repeated_task_id_has_no_state_in_that_reading(self):
        forra = arbetsvarld(read_at=READ1, items=[work(task='office-x')])
        twice = arbetsvarld(read_at=READ2, items=[work(task='office-x', step='granskning',
                                                       state='granskas', executor=None)],
                            parkerade=[parked(task='office-x')])
        both = arbetsvarld(read_at=READ2, items=[work(task='office-x'),
                                                 work(task='office-x', executor='codex')])
        self.assertEqual(aquarium_fonster.jamfor(forra, twice)['uppdrag'], {})
        self.assertEqual(aquarium_fonster.jamfor(forra, both)['uppdrag'], {})

    def test_an_unread_engine_in_either_reading_leaves_no_basis(self):
        working = arbetsvarld(read_at=READ1, items=[work()])
        resting = arbetsvarld(read_at=READ2, parkerade=[parked(task='office-bygge')])
        for forra, nu in ((ingen_motor(READ1), resting), (working, ingen_motor(READ2))):
            self.assertEqual(aquarium_fonster.jamfor(forra, nu),
                             {'grund': 'otillräcklig', 'forra_read_at': None, 'uppdrag': {}})

    def test_a_provdata_difference_leaves_no_basis(self):
        forra = arbetsvarld(read_at=READ1, items=[work()])
        nu = arbetsvarld(read_at=READ2, parkerade=[parked(task='office-bygge')])
        nu['provdata'] = False
        self.assertEqual(aquarium_fonster.jamfor(forra, nu)['grund'], 'otillräcklig')

    def test_the_gap_between_two_readings_decides_the_basis(self):
        def grund(forra_read_at, nu_read_at):
            forra = arbetsvarld(read_at=forra_read_at, items=[work()])
            nu = arbetsvarld(read_at=nu_read_at, parkerade=[parked(task='office-bygge')])
            return aquarium_fonster.jamfor(forra, nu)['grund']

        self.assertEqual(grund(READ1, READ1), 'otillräcklig')            # 0 seconds
        self.assertEqual(grund(READ2, READ1), 'otillräcklig')            # below 0
        self.assertEqual(grund(READ1, READ2), 'jämförd')                 # 120 seconds
        self.assertEqual(grund(READ1, GRANS), 'jämförd')                 # exactly 300
        self.assertEqual(grund(READ1, OVER), 'otillräcklig')             # 300.5
        self.assertEqual(grund(READ1, 'inte en tid'), 'otillräcklig')
        self.assertEqual(aquarium_fonster.JAMFOR_GRANS, 300)

    def test_the_result_shares_nothing_with_the_readings(self):
        forra = arbetsvarld(read_at=READ1, items=[work()])
        nu = arbetsvarld(read_at=READ2, parkerade=[parked(task='office-bygge')])
        orort_forra, orort_nu = deepcopy(forra), deepcopy(nu)
        result = aquarium_fonster.jamfor(forra, nu)
        result['uppdrag']['office-bygge']['step'] = 'ändrat'
        result['uppdrag']['office-tillagt'] = dict(VILAR)
        self.assertEqual(forra, orort_forra)
        self.assertEqual(nu, orort_nu)
        self.assertEqual(aquarium_fonster.jamfor(forra, nu)['uppdrag'],
                         {'office-bygge': lage()})


class Fonsterlaget(unittest.TestCase):
    """The window mode of the renderer, beside the unchanged snapshot."""

    def sida(self):
        nu = arbetsvarld(items=[work(), dict(GRANSKNING)], parkerade=[parked()])
        jamforelse = {'grund': 'jämförd', 'forra_read_at': READ1, 'uppdrag': {
            'office-bygge': dict(VILAR),
            'office-gransk': lage(executor='codex'),
            'office-vilar': {'plats': 'arbete', 'step': 'integration', 'state': 'integreras',
                             'executor': None}}}
        return aquarium_vy.render(nu, jamforelse)

    def test_the_window_page_holds_both_scripts_in_order_and_pins_both(self):
        result = self.sida()
        self.assertIn('<script>' + aquarium_vy.SKRIPT + '</script><script>'
                      + aquarium_vy.FONSTERSKRIPT + '</script>', result)
        self.assertEqual(result.count('<script>'), 2)
        self.assertIn('content="' + aquarium_vy.fonster_csp().replace("'", '&#x27;') + '"', result)
        self.assertIn("connect-src &#x27;self&#x27;", result)

    def test_the_policy_pins_the_two_scripts_and_nothing_else(self):
        def digest(script):
            return base64.b64encode(hashlib.sha256(script.encode('utf-8')).digest()).decode('ascii')

        self.assertEqual(aquarium_vy.fonster_csp(),
                         "default-src 'none'; style-src 'unsafe-inline'; script-src 'sha256-"
                         + digest(aquarium_vy.SKRIPT) + "' 'sha256-"
                         + digest(aquarium_vy.FONSTERSKRIPT)
                         + "'; connect-src 'self'; base-uri 'none'; form-action 'none'")

    def test_the_body_says_that_the_page_is_the_windows(self):
        self.assertIn('<body class="aq-inaktuell aq-provdata aq-fonsterlage"', self.sida())
        nu = arbetsvarld()
        nu['provdata'] = False
        self.assertIn('<body class="aq-inaktuell aq-fonsterlage"',
                      aquarium_vy.render(nu, dict(FIRST)))

    def test_the_mark_sits_on_every_shown_compared_task_and_nowhere_else(self):
        result = self.sida()
        self.assertIn('class="aq-bank aq-pagar aq-figur aq-claude aq-nytt-lage"', result)
        self.assertIn('class="aq-gransk aq-granskas aq-figur aq-okand aq-nytt-lage"', result)
        self.assertIn('class="aq-park aq-pa aq-nytt-lage"', result)
        self.assertIn('class="aq-bank aq-vilar"', result)        # an empty bench is never marked
        self.assertIn('class="aq-park aq-av"', result)           # an empty card is never marked
        self.assertEqual(result.count('aq-nytt-lage"'), 3)

    def test_a_task_beyond_the_shown_places_gets_its_row_but_no_mark(self):
        nu = arbetsvarld(items=[work(task='office-a'), work(task='office-b'),
                                work(task='office-c'), work(task='office-d')])
        result = aquarium_vy.render(nu, {'grund': 'jämförd', 'forra_read_at': READ1,
                                         'uppdrag': {'office-d': dict(VILAR)}})
        self.assertEqual(result.count('aq-nytt-lage"'), 0)
        self.assertIn('<li><span class="aq-etikett">Pågår</span>office-d · Claude · utförare · '
                      'sedan 24 sep 11:20 · steg execute_claude · nytt läge; förra läsningen '
                      '24 sep 14:52: arbetade inte</li>', result)

    def test_every_marked_row_says_the_previous_reading_and_its_state(self):
        result = self.sida()
        self.assertIn('<li><span class="aq-etikett">Pågår</span>office-bygge · Claude · '
                      'utförare · sedan 24 sep 11:20 · steg execute_claude · nytt läge; '
                      'förra läsningen 24 sep 14:52: arbetade inte</li>', result)
        self.assertIn('<li><span class="aq-etikett">Arbetar inte</span>office-vilar · '
                      'En vilande rubrik · sedan 24 sep 11:10 · nytt läge; förra läsningen '
                      '24 sep 14:52: integration</li>', result)
        self.assertIn('<li><span class="aq-etikett">Granskas</span>office-gransk · '
                      'granskare ej belagd · sedan 24 sep 11:20 · steg review_candidate · '
                      'nytt läge; förra läsningen 24 sep 14:52: utförande · Codex</li>', result)

    def test_the_previous_state_is_written_out_for_every_step(self):
        self.assertEqual(aquarium_vy.FÖRRA(dict(VILAR)), 'arbetade inte')
        self.assertEqual(aquarium_vy.FÖRRA(lage()), 'utförande · Claude')
        self.assertEqual(aquarium_vy.FÖRRA(lage(executor=None)),
                         'utförande · utförare ej belagd')
        self.assertEqual(aquarium_vy.FÖRRA(lage(step='granskning', state='granskas',
                                                executor=None)), 'granskning')
        self.assertEqual(aquarium_vy.FÖRRA(lage(step='integration', state='integreras',
                                                executor=None)), 'integration')
        self.assertEqual(aquarium_vy.FÖRRA(lage(step='steg', executor=None)), 'steg pågår')
        self.assertEqual(aquarium_vy.FÖRRA(lage(step='arbetsflödessteg', executor=None)),
                         'arbetsflödessteg')

    def test_the_comparison_row_is_last_in_the_workshop_for_every_basis(self):
        def sista(result, text):
            return ('<li><span class="aq-etikett">Jämförelse</span>' + text
                    + '</li></ul>') in result

        self.assertTrue(sista(self.sida(),
                              'jämfört med läsningen 24 sep 14:52: 3 uppdrag i nytt läge; '
                              'nytt läge visar det uppdaterade läget, inte när eller hur det '
                              'ändrades'))
        one = aquarium_vy.render(arbetsvarld(items=[work()]),
                                 {'grund': 'jämförd', 'forra_read_at': READ1,
                                  'uppdrag': {'office-bygge': dict(VILAR)}})
        self.assertTrue(sista(one, 'jämfört med läsningen 24 sep 14:52: 1 uppdrag i nytt läge; '
                                   'nytt läge visar det uppdaterade läget, inte när eller hur '
                                   'det ändrades'))
        none = aquarium_vy.render(arbetsvarld(items=[work()]),
                                  {'grund': 'jämförd', 'forra_read_at': READ1, 'uppdrag': {}})
        self.assertTrue(sista(none, 'jämfört med läsningen 24 sep 14:52: inget uppdrag i nytt '
                                    'läge; nytt läge visar det uppdaterade läget, inte när eller '
                                    'hur det ändrades'))
        self.assertTrue(sista(aquarium_vy.render(arbetsvarld(), dict(FIRST)),
                              'första läsningen sedan fönstret startade; bilden visar bara '
                              'aktuellt läge'))
        # Also when the engine could not be read: the window still says what it rests on.
        unread = aquarium_vy.render(ingen_motor(), {'grund': 'otillräcklig',
                                                    'forra_read_at': None, 'uppdrag': {}})
        self.assertTrue(sista(unread, 'underlaget räcker inte för en jämförelse; bilden visar '
                                      'bara aktuellt läge'))
        self.assertIn('Motorn kunde inte läsas', unread)

    def test_the_window_page_never_describes_a_handover(self):
        result = self.sida()
        self.assertNotIn('överlämn', result.lower())
        self.assertNotIn('tog över', result)
        self.assertNotIn('lämnade över', result)

    def test_the_snapshot_is_unchanged_and_nothing_is_mutated(self):
        given = arbetsvarld(items=[work()], parkerade=[parked()])
        untouched = deepcopy(given)
        jamforelse = {'grund': 'jämförd', 'forra_read_at': READ1,
                      'uppdrag': {'office-bygge': dict(VILAR)}}
        orort = deepcopy(jamforelse)
        snapshot = aquarium_vy.render(given)
        self.assertEqual(snapshot, aquarium_vy.render(given, None))
        self.assertEqual(snapshot.count('<script>'), 1)
        self.assertIn('content="' + aquarium_vy.csp().replace("'", '&#x27;') + '"', snapshot)
        self.assertIn('<body class="aq-inaktuell aq-provdata"', snapshot)
        self.assertEqual(snapshot.count('aq-nytt-lage"'), 0)
        self.assertNotIn('Jämförelse', snapshot)
        window = aquarium_vy.render(given, jamforelse)
        self.assertNotEqual(snapshot, window)
        self.assertEqual(window, aquarium_vy.render(given, jamforelse))
        self.assertEqual(given, untouched)
        self.assertEqual(jamforelse, orort)

    def test_anything_that_is_not_a_comparison_is_refused(self):
        refused = [
            'jämförd',
            {'grund': 'jämförd', 'forra_read_at': READ1},
            {'grund': 'jämförd', 'forra_read_at': READ1, 'uppdrag': {}, 'extra': 1},
            {'grund': 'okänd', 'forra_read_at': None, 'uppdrag': {}},
            {'grund': 'jämförd', 'forra_read_at': None, 'uppdrag': {}},
            {'grund': 'jämförd', 'forra_read_at': '2026-09-24T12:52:00', 'uppdrag': {}},
            {'grund': 'första', 'forra_read_at': None,
             'uppdrag': {'office-bygge': dict(VILAR)}},
            {'grund': 'otillräcklig', 'forra_read_at': READ1, 'uppdrag': {}},
            {'grund': 'jämförd', 'forra_read_at': READ1, 'uppdrag': []},
            {'grund': 'jämförd', 'forra_read_at': READ1, 'uppdrag': {7: dict(VILAR)}},
            {'grund': 'jämförd', 'forra_read_at': READ1, 'uppdrag': {'office-bygge': 'vilar'}},
            {'grund': 'jämförd', 'forra_read_at': READ1,
             'uppdrag': {'office-bygge': {'plats': 'vilar', 'step': None, 'state': None}}},
            {'grund': 'jämförd', 'forra_read_at': READ1,
             'uppdrag': {'office-bygge': dict(VILAR, step='utförande')}},
            {'grund': 'jämförd', 'forra_read_at': READ1,
             'uppdrag': {'office-bygge': lage(step=None)}},
            {'grund': 'jämförd', 'forra_read_at': READ1,
             'uppdrag': {'office-bygge': lage(executor=7)}},
            {'grund': 'jämförd', 'forra_read_at': READ1,
             'uppdrag': {'office-bygge': dict(VILAR, plats='annat')}}]
        for jamforelse in refused:
            with self.subTest(jamforelse=jamforelse):
                with self.assertRaises(ValueError) as raised:
                    aquarium_vy.render(arbetsvarld(), jamforelse)
                self.assertEqual(str(raised.exception), aquarium_vy.ERROR)


class Fonstret(unittest.TestCase):
    """The window's own state: one reading at a time, at most every other minute."""

    def test_a_new_window_holds_nothing_and_reads_nothing(self):
        lasare = Lasare([])
        fonster = aquarium_fonster.Fonster(reader=lasare, clock=Klocka())
        self.assertIsNone(fonster.sida())
        self.assertIsNone(fonster.read_at())
        self.assertEqual(lasare.antal, 0)

    def test_the_cadence_is_at_most_every_other_minute(self):
        klocka, lasare = Klocka(), Lasare([arbetsvarld(read_at=READ1, items=[work()]),
                                           arbetsvarld(read_at=READ2, items=[work()])])
        fonster = aquarium_fonster.Fonster(reader=lasare, clock=klocka)
        self.assertTrue(fonster.kanske_las())         # no reading has begun yet
        self.assertEqual(fonster.read_at(), READ1)
        self.assertFalse(fonster.kanske_las())
        klocka.nu += aquarium_fonster.INTERVALL - 1
        self.assertFalse(fonster.kanske_las())
        self.assertEqual(lasare.antal, 1)
        klocka.nu += 1                                # exactly 120 seconds after it began
        self.assertTrue(fonster.kanske_las())
        self.assertEqual(lasare.antal, 2)
        self.assertEqual(fonster.read_at(), READ2)
        self.assertEqual(aquarium_fonster.INTERVALL, 120)

    def test_las_om_reads_whatever_the_interval(self):
        klocka, lasare = Klocka(), Lasare([arbetsvarld(read_at=READ1), arbetsvarld(read_at=READ2)])
        fonster = aquarium_fonster.Fonster(reader=lasare, clock=klocka)
        self.assertTrue(fonster.las_om())
        self.assertTrue(fonster.las_om())
        self.assertEqual(lasare.antal, 2)
        self.assertEqual(fonster.read_at(), READ2)

    def test_a_failed_reading_keeps_the_page_and_still_counts(self):
        klocka = Klocka()
        lasare = Lasare([arbetsvarld(read_at=READ1, items=[work()]), Misslyckad(),
                         arbetsvarld(read_at=READ3, parkerade=[parked(task='office-bygge',
                                                                      title='Rubrik')])])
        fonster = aquarium_fonster.Fonster(reader=lasare, clock=klocka)
        self.assertTrue(fonster.las_om())
        forsta = fonster.sida()
        klocka.nu += aquarium_fonster.INTERVALL
        self.assertFalse(fonster.kanske_las())        # the reading runs and fails
        self.assertEqual(fonster.sida(), forsta)
        self.assertEqual(fonster.read_at(), READ1)
        klocka.nu += aquarium_fonster.INTERVALL - 1
        self.assertFalse(fonster.kanske_las())        # the failed reading counts as begun
        self.assertEqual(lasare.antal, 2)
        klocka.nu += 1
        self.assertTrue(fonster.kanske_las())
        self.assertEqual(lasare.antal, 3)
        # The comparison is with the latest good reading, not with the failed one.
        sida = fonster.sida()
        self.assertIn('<li><span class="aq-etikett">Arbetar inte</span>office-bygge · Rubrik · '
                      'sedan 24 sep 11:10 · nytt läge; förra läsningen 24 sep 14:52: '
                      'utförande · Claude</li>', sida)
        self.assertIn('class="aq-park aq-pa aq-nytt-lage"', sida)
        self.assertIn('jämfört med läsningen 24 sep 14:52: 1 uppdrag i nytt läge', sida)

    def test_a_restart_shows_the_current_state_without_an_earlier_transition(self):
        lasare = Lasare([arbetsvarld(read_at=READ3, parkerade=[parked(task='office-bygge')])])
        fonster = aquarium_fonster.Fonster(reader=lasare, clock=Klocka())
        self.assertTrue(fonster.las_om())
        sida = fonster.sida()
        self.assertEqual(sida.count('aq-nytt-lage"'), 0)
        self.assertIn('<li><span class="aq-etikett">Jämförelse</span>första läsningen sedan '
                      'fönstret startade; bilden visar bara aktuellt läge</li></ul>', sida)
        self.assertIn('<body class="aq-inaktuell aq-provdata aq-fonsterlage"', sida)

    def test_no_second_reading_while_one_runs(self):
        lasare = Aterkommande(arbetsvarld(read_at=READ1))
        fonster = aquarium_fonster.Fonster(reader=lasare, clock=Klocka())
        lasare.fonster = fonster
        self.assertTrue(fonster.las_om())
        self.assertIs(lasare.inre, False)
        self.assertEqual(lasare.antal, 1)
        self.assertEqual(fonster.read_at(), READ1)

    def test_a_refused_render_leaves_the_window_as_it_was(self):
        trasig = arbetsvarld(read_at=READ2)
        del trasig['headline']
        lasare = Lasare([arbetsvarld(read_at=READ1), trasig])
        fonster = aquarium_fonster.Fonster(reader=lasare, clock=Klocka())
        self.assertTrue(fonster.las_om())
        forsta = fonster.sida()
        self.assertFalse(fonster.las_om())
        self.assertEqual(fonster.sida(), forsta)
        self.assertEqual(fonster.read_at(), READ1)


class Svaret(unittest.TestCase):
    """Every rule of `svar`, in the order the rules apply."""

    def headers(self, kind):
        return [('Content-Type', kind), ('Cache-Control', 'no-store'),
                ('X-Content-Type-Options', 'nosniff'), ('Referrer-Policy', 'no-referrer'),
                ('Content-Security-Policy', "frame-ancestors 'none'")]

    def fraga(self, fonster, metod='GET', sokvag='/', vard='127.0.0.1:8741',
              klient='127.0.0.1', port=8741):
        return aquarium_fonster.svar(fonster, metod, sokvag, vard, klient, port)

    def test_only_a_read_request_is_answered(self):
        fonster = FalsktFonster(sida='sidan')
        for metod in ('POST', 'HEAD', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'):
            status, headers, body = self.fraga(fonster, metod=metod)
            self.assertEqual(status, 405)
            self.assertEqual(headers, [('Allow', 'GET')] + self.headers(aquarium_fonster.TEXT))
            self.assertEqual(body, aquarium_fonster.ONLY_GET.encode('utf-8'))
        # The first rule applies before the client and the host are looked at, and nothing is asked.
        self.assertEqual(self.fraga(fonster, metod='POST', klient='10.0.0.5')[0], 405)
        self.assertEqual(fonster.anrop, [])

    def test_only_the_loopback_and_its_own_name_are_answered(self):
        fonster = FalsktFonster(sida='sidan')
        for klient, vard in (('10.0.0.5', '127.0.0.1:8741'), ('::1', '127.0.0.1:8741'),
                             ('127.0.0.1', 'localhost:8741'), ('127.0.0.1', '127.0.0.1'),
                             ('127.0.0.1', '127.0.0.1:8742'), ('127.0.0.1', None)):
            status, headers, body = self.fraga(fonster, klient=klient, vard=vard)
            self.assertEqual((status, body),
                             (403, aquarium_fonster.ONLY_LOCAL.encode('utf-8')))
            self.assertEqual(headers, self.headers(aquarium_fonster.TEXT))
        self.assertEqual(self.fraga(fonster, vard='127.0.0.1:8742', port=8742)[0], 200)
        self.assertEqual(fonster.anrop, ['sida'])

    def test_the_page_is_served_only_after_a_reading(self):
        tom = FalsktFonster()
        status, headers, body = self.fraga(tom)
        self.assertEqual((status, body), (503, aquarium_fonster.NO_READING.encode('utf-8')))
        self.assertEqual(headers, self.headers(aquarium_fonster.TEXT))
        fonster = FalsktFonster(sida='sidan med ö')
        status, headers, body = self.fraga(fonster)
        self.assertEqual(status, 200)
        self.assertEqual(headers, self.headers(aquarium_fonster.HTML))
        self.assertEqual(body, 'sidan med ö'.encode('utf-8'))
        self.assertEqual(fonster.anrop, ['sida'])     # the page never starts a reading

    def test_only_the_read_time_may_ask_for_a_reading(self):
        fonster = FalsktFonster(sida='sidan', read_at=READ1)
        status, headers, body = self.fraga(fonster, sokvag='/lasning.json')
        self.assertEqual(status, 200)
        self.assertEqual(headers, self.headers(aquarium_fonster.JSON))
        self.assertEqual(body, ('{"read_at": "%s"}\n' % READ1).encode('utf-8'))
        self.assertEqual(fonster.anrop, ['kanske_las', 'read_at'])
        tom = FalsktFonster()
        self.assertEqual(self.fraga(tom, sokvag='/lasning.json')[2], b'{"read_at": null}\n')
        self.assertEqual(tom.anrop, ['kanske_las', 'read_at'])

    def test_anything_else_is_not_there(self):
        fonster = FalsktFonster(sida='sidan', read_at=READ1)
        for sokvag in ('/annat', '/lasning.json?x=1', '//', '/index.html', ''):
            status, headers, body = self.fraga(fonster, sokvag=sokvag)
            self.assertEqual((status, body), (404, aquarium_fonster.NOT_FOUND.encode('utf-8')))
            self.assertEqual(headers, self.headers(aquarium_fonster.TEXT))
        self.assertEqual(fonster.anrop, [])


class Hanteraren(unittest.TestCase):
    """The handler, driven through an in-memory connection; no socket is touched."""

    def test_the_page_is_answered_with_its_headers_and_nothing_is_logged(self):
        fonster = FalsktFonster(sida='sidan med ö')
        answer, fel = kor(begar(), fonster)
        lines, body = delar(answer)
        self.assertTrue(lines[0].startswith(b'HTTP/1.0 200 '))
        self.assertIn(b'Server: Aquarium', lines)
        self.assertIn(b'Content-Type: text/html; charset=utf-8', lines)
        self.assertIn(b'Cache-Control: no-store', lines)
        self.assertIn(b'X-Content-Type-Options: nosniff', lines)
        self.assertIn(b'Referrer-Policy: no-referrer', lines)
        self.assertIn(b"Content-Security-Policy: frame-ancestors 'none'", lines)
        self.assertEqual(body, 'sidan med ö'.encode('utf-8'))
        self.assertIn(b'Content-Length: %d' % len(body), lines)
        self.assertEqual(fel, '')

    def test_the_read_time_is_answered_as_json(self):
        fonster = FalsktFonster(sida='sidan', read_at=READ1)
        answer, fel = kor(begar(sokvag='/lasning.json'), fonster)
        lines, body = delar(answer)
        self.assertTrue(lines[0].startswith(b'HTTP/1.0 200 '))
        self.assertIn(b'Content-Type: application/json; charset=utf-8', lines)
        self.assertEqual(body, ('{"read_at": "%s"}\n' % READ1).encode('utf-8'))
        self.assertEqual(json.loads(body.decode('utf-8')), {'read_at': READ1})
        self.assertEqual(fonster.anrop, ['kanske_las', 'read_at'])
        self.assertEqual(fel, '')

    def test_a_head_gets_the_headers_without_the_body(self):
        answer, fel = kor(begar(metod='HEAD'), FalsktFonster(sida='sidan'))
        lines, body = delar(answer)
        self.assertTrue(lines[0].startswith(b'HTTP/1.0 405 '))
        self.assertIn(b'Allow: GET', lines)
        self.assertIn(b'Content-Length: %d'
                      % len(aquarium_fonster.ONLY_GET.encode('utf-8')), lines)
        self.assertEqual(body, b'')
        self.assertEqual(fel, '')

    def test_a_write_request_and_a_foreign_host_are_refused(self):
        lines, body = delar(kor(begar(metod='POST'), FalsktFonster(sida='sidan'))[0])
        self.assertTrue(lines[0].startswith(b'HTTP/1.0 405 '))
        self.assertIn(b'Allow: GET', lines)
        self.assertEqual(body, aquarium_fonster.ONLY_GET.encode('utf-8'))
        lines, body = delar(kor(begar(vard='min-dator.example:8741'),
                                FalsktFonster(sida='sidan'))[0])
        self.assertTrue(lines[0].startswith(b'HTTP/1.0 403 '))
        self.assertEqual(body, aquarium_fonster.ONLY_LOCAL.encode('utf-8'))
        lines, body = delar(kor(begar(), FalsktFonster(sida='sidan'), klient='10.0.0.5')[0])
        self.assertTrue(lines[0].startswith(b'HTTP/1.0 403 '))
        lines, body = delar(kor(begar(sokvag='/annat'), FalsktFonster(sida='sidan'))[0])
        self.assertTrue(lines[0].startswith(b'HTTP/1.0 404 '))
        self.assertEqual(body, aquarium_fonster.NOT_FOUND.encode('utf-8'))

    def test_the_answer_names_no_version_and_the_window_stays_silent(self):
        answer, fel = kor(begar(), FalsktFonster(sida='sidan'))
        lines, _ = delar(answer)
        server = [line for line in lines if line.startswith(b'Server:')]
        self.assertEqual(server, [b'Server: Aquarium'])
        self.assertEqual(fel, '')


class Servern(unittest.TestCase):
    def test_the_server_is_local_and_carries_the_window(self):
        fabrik = Fabrik()
        fonster = FalsktFonster(sida='sidan')
        with patch.object(aquarium_fonster, 'ThreadingHTTPServer', fabrik):
            made = aquarium_fonster.server(fonster, 8741)
        self.assertEqual(made.server_address, ('127.0.0.1', 8741))
        self.assertIs(made.handler, aquarium_fonster.Handler)
        self.assertIs(made.fonster, fonster)
        self.assertTrue(made.daemon_threads)
        self.assertEqual(len(fabrik.gjorda), 1)
        self.assertEqual(aquarium_fonster.ADRESS, '127.0.0.1')
        self.assertEqual(aquarium_fonster.PORT, 8741)


class Kommandot(unittest.TestCase):
    def kor(self, argv, lasare=None, fabrik=None):
        lasare = Lasare([arbetsvarld(read_at=READ1)]) if lasare is None else lasare
        fabrik = Fabrik() if fabrik is None else fabrik
        ut, fel = io.StringIO(), io.StringIO()
        with patch.object(aquarium_fonster, 'las', lasare), \
                patch.object(aquarium_fonster, 'ThreadingHTTPServer', fabrik), \
                redirect_stdout(ut), redirect_stderr(fel):
            code = aquarium_fonster.main(argv)
        return code, ut.getvalue(), fel.getvalue(), fabrik, lasare

    def test_the_window_reads_once_and_prints_where_it_listens(self):
        code, ut, fel, fabrik, lasare = self.kor([])
        self.assertEqual(code, 0)
        self.assertEqual(ut, 'Aquarium-fönstret: http://127.0.0.1:8741/ · stoppa med Ctrl-C\n')
        self.assertEqual(fel, '')
        self.assertEqual(lasare.antal, 1)
        made = fabrik.gjorda[0]
        self.assertEqual(made.server_address, ('127.0.0.1', 8741))
        self.assertIsInstance(made.fonster, aquarium_fonster.Fonster)
        self.assertEqual(made.fonster.read_at(), READ1)
        self.assertEqual((made.servad, made.stangd), (1, 1))

    def test_a_given_port_is_used_within_its_bounds(self):
        for text, port in (('1024', 1024), ('8741', 8741), ('65535', 65535)):
            code, ut, fel, fabrik, _ = self.kor(['--port', text])
            self.assertEqual((code, fel), (0, ''))
            self.assertEqual(ut, 'Aquarium-fönstret: http://127.0.0.1:%d/ · stoppa med Ctrl-C\n'
                             % port)
            self.assertEqual(fabrik.gjorda[0].server_address, ('127.0.0.1', port))

    def test_wrong_arguments_are_refused_before_anything_is_read(self):
        for argv in (['--port', '1023'], ['--port', '999'], ['--port', '65536'],
                     ['--port', '008741'], ['--port', '87a1'], ['--port', ' 8741'],
                     ['--port', ''], ['--port'], ['--port', '8741', 'extra'],
                     ['--porta', '8741'], ['8741'], ['--help']):
            with self.subTest(argv=argv):
                code, ut, fel, fabrik, lasare = self.kor(argv)
                self.assertEqual(code, 2)
                self.assertEqual(ut, '')
                self.assertEqual(fel, aquarium_fonster.COMMAND_ERROR + '\n')
                self.assertEqual(lasare.antal, 0)
                self.assertEqual(fabrik.gjorda, [])

    def test_a_failed_first_reading_opens_no_window(self):
        code, ut, fel, fabrik, lasare = self.kor([], lasare=Lasare([Misslyckad()]))
        self.assertEqual(code, 2)
        self.assertEqual(ut, '')
        self.assertEqual(fel, aquarium_fonster.COMMAND_ERROR + '\n')
        self.assertEqual(lasare.antal, 1)
        self.assertEqual(fabrik.gjorda, [])

    def test_ctrl_c_ends_the_window_quietly(self):
        code, ut, fel, fabrik, _ = self.kor([], fabrik=Fabrik(avbryt=True))
        self.assertEqual(code, 0)
        self.assertEqual(fel, '')
        self.assertIn('stoppa med Ctrl-C', ut)
        self.assertEqual(fabrik.gjorda[0].stangd, 1)


if __name__ == '__main__':
    unittest.main()
