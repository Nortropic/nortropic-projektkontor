"""Synthetic tests for Aquarium v0's view. No real source, no network, no model call.

Every projection here is made up and marked `provdata`, and every temporary file lives under the
repository's existing `.scratch`, which is never removed, replaced or recreated.
"""
from contextlib import redirect_stderr
import base64
from copy import deepcopy
import hashlib
import html
import io
import json
import os
from pathlib import Path
import tempfile
import unittest

import aquarium_vy

SCRATCH = Path(__file__).absolute().parents[1] / '.scratch'
READ_AT = '2026-09-24T12:52:00+00:00'          # 24 sep 14:52 in Stockholm
WINTER = '2026-01-15T12:52:00+00:00'           # 15 jan 13:52 in Stockholm
TITLES = {'release': 'Runtime · aktiv release', 'staffing': 'Runtime · bemanning',
          'questions': 'Runtime · modellfrågor', 'service': 'Runtime · tjänsten',
          'engine': 'Runtime · motorn', 'tasks': 'Runtime · uppdragsfiler',
          'watch': 'Runtime · bevakningen', 'office': 'Kontoret · beslut och leveranser'}


def sources(unavailable=()):
    return {name: {'title': TITLES[name],
                   'status': 'otillgänglig' if name in unavailable else 'ok',
                   'read_at': READ_AT,
                   'stale_after_seconds': 3600 if name == 'office' else 300}
            for name in aquarium_vy.SOURCES}


def projection(**overrides):
    base = {
        'schema': 2, 'provdata': True, 'read_at': READ_AT, 'sources': sources(),
        'revisions': {'office_main': '1a1a1a1a', 'office_main_date': '2026-09-24T08:00:00+02:00',
                      'runtime': 'cdcdcdcd', 'config': 'abababab'},
        'headline': {'pagar': 0, 'vantar': 0, 'behover_dig': 0, 'lugnt': True},
        'arkivet': {'status': 'ok', 'items': []},
        'verkstaden': {'status': 'ok', 'items': [], 'parked': [], 'titles': 'ok'},
        'utkiken': {'status': 'ok', 'schedule': 'aktiverat', 'next_planned': None, 'running': 0,
                    'starts': [], 'latest': None, 'reviewed': None, 'waiting': False,
                    'model': {'executor': 'codex', 'model': 'gpt-5-codex',
                              'follows_model_choice': False}},
        'agarens_bord': {'status': 'ok', 'items': []},
        'sockeln': {'service': {'state': 'igång', 'verified': 3, 'of': 3, 'config': 'abababab'},
                    'staffing': [{'role': 'granskare', 'executor': 'codex',
                                  'model': 'gpt-5-codex'},
                                 {'role': 'utvecklare', 'executor': 'claude',
                                  'model': 'claude-opus-5'}],
                    'watch_staffing': {'executor': 'codex', 'model': 'gpt-5-codex'},
                    'idle_tasks': 0, 'identity_records': 0, 'busy': 0}}
    base.update(overrides)
    return base


def work(task='office-bygge', step='utförande', state='pågår', executor='claude',
         activities=('execute_claude',), since='2026-09-24T09:20:00+00:00', kind='Bygge'):
    return {'task': task, 'short': task[len('office-'):] if task.startswith('office-') else task,
            'type': kind, 'since': since, 'step': step, 'state': state, 'executor': executor,
            'executor_basis': None if executor is None else 'motorns steg execute_' + executor,
            'activities': list(activities)}


def parked(task='office-vilar', title='En vilande rubrik', status='läst',
           since='2026-09-24T09:10:00+00:00'):
    return {'task': task, 'short': task[len('office-'):] if task.startswith('office-') else task,
            'type': 'Vilande', 'since': since, 'title': title, 'title_status': status}


def page(**overrides):
    return aquarium_vy.render(projection(**overrides))


class Formats(unittest.TestCase):
    def test_the_policy_pins_the_script(self):
        digest = base64.b64encode(hashlib.sha256(
            aquarium_vy.SKRIPT.encode('utf-8')).digest()).decode('ascii')
        self.assertEqual(aquarium_vy.csp(),
                         "default-src 'none'; style-src 'unsafe-inline'; script-src 'sha256-"
                         + digest + "'; base-uri 'none'; form-action 'none'")

    def test_summer_and_winter_time(self):
        self.assertEqual(aquarium_vy.TID(READ_AT), '24 sep 14:52')
        self.assertEqual(aquarium_vy.TID(WINTER), '15 jan 13:52')
        self.assertEqual(aquarium_vy.TID('2026-09-24T23:30:00+00:00'), '25 sep 01:30')
        self.assertEqual(aquarium_vy.DATUM('2026-09-24T23:30:00+00:00'), '25 sep')
        self.assertEqual(aquarium_vy.DATUM('2026-01-05'), '5 jan')
        self.assertEqual(aquarium_vy.NÄR('2026-01-05'), '5 jan')
        self.assertEqual(aquarium_vy.NÄR(WINTER), '15 jan 13:52')
        self.assertNotIn('i dag', aquarium_vy.TID(READ_AT))

    def test_names_executors_and_counts(self):
        self.assertEqual(aquarium_vy.NAMN('a' * 22), 'a' * 22)
        self.assertEqual(aquarium_vy.NAMN('a' * 23), 'a' * 21 + '…')
        self.assertEqual(aquarium_vy.EXEC('claude'), 'Claude')
        self.assertEqual(aquarium_vy.EXEC('codex'), 'Codex')
        self.assertEqual(aquarium_vy.EXEC('egen'), 'egen')
        self.assertEqual(aquarium_vy.MODELL('claude', 'claude-opus-5'), 'Claude claude-opus-5')
        self.assertEqual(aquarium_vy.MODELL('codex', None), 'Codex · modell okänd')
        self.assertEqual(aquarium_vy.ANTAL(1, '1 leverans', '%d leveranser'), '1 leverans')
        self.assertEqual(aquarium_vy.ANTAL(0, '1 leverans', '%d leveranser'), '0 leveranser')
        self.assertEqual(aquarium_vy.ANTAL(2, '1 leverans', '%d leveranser'), '2 leveranser')

    def test_a_missing_start_is_not_invented(self):
        self.assertEqual(aquarium_vy.SEDAN(work()), 'sedan 24 sep 11:20')
        self.assertEqual(aquarium_vy.SEDAN(work(since=None)), 'starttid okänd')

    def test_the_source_line_names_every_asked_source(self):
        given = sources(unavailable=('tasks',))
        self.assertEqual(aquarium_vy.KÄLLA(given, ('engine',)),
                         'Källa: Runtime · motorn · läst 24 sep 14:52')
        self.assertEqual(aquarium_vy.KÄLLA(given, ('engine', 'tasks')),
                         'Källor: Runtime · motorn · läst 24 sep 14:52; '
                         'Runtime · uppdragsfiler · otillgänglig')


class Page(unittest.TestCase):
    def test_every_placeholder_and_slot_is_filled(self):
        result = page()
        self.assertNotIn('{{AQ_', result)
        self.assertNotIn('<!--AQ:', result)
        self.assertIn('<script>' + aquarium_vy.SKRIPT + '</script>', result)
        # The policy passes the same escaping as every other placeholder value.
        self.assertIn('content="' + html.escape(aquarium_vy.csp(), quote=True) + '"', result)
        self.assertIn('data-read-at="' + READ_AT + '"', result)
        self.assertIn('data-stale-after="300"', result)
        self.assertIn('class="aq-inaktuell aq-provdata"', result)
        self.assertIn('läst 24 sep 14:52 · <tspan id="aq-alder">ålder okänd</tspan>', result)
        self.assertIn('senast kända 24 sep 14:52', result)

    def test_the_same_projection_gives_the_same_page_and_nothing_is_mutated(self):
        given = projection(verkstaden={'status': 'ok', 'items': [work()],
                                       'parked': [parked()], 'titles': 'ok'})
        untouched = deepcopy(given)
        first = aquarium_vy.render(given)
        self.assertEqual(given, untouched)
        self.assertEqual(first, aquarium_vy.render(given))

    def test_the_headline_counts_work_the_watch_and_the_owner(self):
        calm = page()
        self.assertIn('PROVDATA · Lugnt · inget uppdrag arbetar i Runtime · bevakningen i vila '
                      '· inget väntar på dig', calm)
        one = page(headline={'pagar': 1, 'vantar': 0, 'behover_dig': 1, 'lugnt': False},
                   provdata=False,
                   agarens_bord={'status': 'ok', 'items': [
                       {'kind': 'beslut', 'text': 'Välj väg', 'since': '2026-09-20',
                        'basis': 'planens ägartur'}]})
        self.assertIn('>Ett uppdrag arbetar i Runtime · bevakningen i vila · ett beslut väntar '
                      'på dig<', one)
        many = page(headline={'pagar': 4, 'vantar': 0, 'behover_dig': 2, 'lugnt': False},
                    provdata=False,
                    agarens_bord={'status': 'ok', 'items': [
                        {'kind': 'beslut', 'text': 'A', 'since': None, 'basis': 'b'},
                        {'kind': 'modellfråga', 'text': 'B', 'since': None, 'basis': 'b'}]})
        self.assertIn('>4 uppdrag arbetar i Runtime · bevakningen i vila · 2 ärenden väntar '
                      'på dig<', many)

    def test_an_unknown_count_is_never_shown_as_nothing(self):
        result = page(provdata=False, sources=sources(unavailable=('engine', 'tasks')),
                      headline={'pagar': None, 'vantar': 0, 'behover_dig': 0, 'lugnt': False},
                      verkstaden={'status': 'otillgänglig', 'items': [], 'parked': [],
                                  'titles': 'otillgänglig'},
                      sockeln=dict(projection()['sockeln'], idle_tasks=None, busy=None,
                                   identity_records=None))
        self.assertIn('>Motorn kunde inte läsas · bevakningen i vila · inget väntar på dig<',
                      result)
        self.assertIn('class="aq-plats aq-verkstaden aq-otillganglig"', result)
        self.assertIn('motorn kunde inte läsas', result)
        self.assertIn('Motorn kunde inte läsas; inget visas som noll', result)
        self.assertIn('tekniska poster okända', result)
        self.assertIn('>Arbetar inte</span>okänt<', result)
        self.assertIn('>Pågår</span>okänt<', result)
        self.assertIn('Runtime · motorn</span>otillgänglig vid läsningen', result)
        self.assertNotIn('inget uppdrag arbetar i Runtime', result)

    def test_an_unavailable_source_beside_working_ones(self):
        result = page(sources=sources(unavailable=('office',)),
                      arkivet={'status': 'otillgänglig', 'items': []},
                      agarens_bord={'status': 'otillgänglig', 'items': []},
                      headline={'pagar': 0, 'vantar': 0, 'behover_dig': None, 'lugnt': False})
        self.assertIn('class="aq-plats aq-arkivet aq-otillganglig"', result)
        self.assertIn('kontorets källa kunde inte läsas', result)
        self.assertIn('Kontorets källa kunde inte läsas; inget visas som tomt', result)
        self.assertIn('okänt om något väntar på dig', result)
        self.assertIn('Kontoret · beslut och leveranser</span>otillgänglig vid läsningen', result)
        self.assertIn('Runtime · motorn</span>läst 24 sep 14:52 · inaktuell efter 5 min', result)
        self.assertIn('data-stale-after="300"', result)

    def test_the_smallest_limit_governs_freshness(self):
        only_office = page(sources=dict(
            sources(unavailable=('release', 'staffing', 'questions', 'service', 'engine', 'tasks',
                                 'watch'))))
        self.assertIn('data-stale-after="3600"', only_office)
        self.assertIn('inaktuell efter 60 min', only_office)
        nothing = page(sources=sources(unavailable=aquarium_vy.SOURCES))
        self.assertIn('data-stale-after="0"', nothing)


class Verkstaden(unittest.TestCase):
    def test_a_figure_only_for_work_the_engine_evidences(self):
        result = page(verkstaden={'status': 'ok', 'titles': 'ok', 'parked': [],
                                  'items': [work(), work(task='office-codex', executor='codex',
                                                 activities=('execute_codex',)),
                                            work(task='office-okand', executor=None,
                                                 activities=('execute_claude', 'execute_codex'))]},
                      headline={'pagar': 3, 'vantar': 0, 'behover_dig': 0, 'lugnt': False})
        self.assertIn('class="aq-bank aq-pagar aq-figur aq-claude"', result)
        self.assertIn('class="aq-bank aq-pagar aq-figur aq-codex"', result)
        self.assertIn('class="aq-bank aq-pagar aq-figur aq-okand"', result)
        self.assertIn('Claude · utförare', result)
        self.assertIn('Codex · utförare', result)
        self.assertIn('utförare ej belagd', result)
        self.assertIn('3 i arbete · 0 uppdrag arbetar inte', result)

    def test_a_step_without_an_executor_is_no_figure(self):
        result = page(verkstaden={'status': 'ok', 'titles': 'ok', 'parked': [],
                                  'items': [work(task='office-steg', step='steg', executor=None,
                                                 activities=('prepare',))]},
                      headline={'pagar': 1, 'vantar': 0, 'behover_dig': 0, 'lugnt': False})
        self.assertIn('class="aq-bank aq-pagar"', result)
        for figure in ('aq-figur aq-claude', 'aq-figur aq-codex', 'aq-figur aq-okand'):
            self.assertNotIn(figure, result)
        self.assertIn('steg pågår', result)
        self.assertIn('1 i arbete · 0 uppdrag arbetar inte', result)
        self.assertIn('ledig bänk', result)

    def test_configured_staffing_is_never_an_observed_figure(self):
        result = page()
        self.assertIn('inget arbete observerat i motorn', result)
        # The page names the configured staffing only in Maskinrummet, never as a figure.
        self.assertNotIn('aq-figur', result.split('</style>')[1])
        self.assertIn('class="aq-bank aq-vilar"', result)
        self.assertIn('Konfigurerad · utvecklare</span>Claude claude-opus-5', result)
        self.assertIn('Konfigurerad · bevakningen</span>Codex gpt-5-codex · följer inte '
                      'modellvalet', result)

    def test_parked_tasks_and_their_titles(self):
        result = page(verkstaden={'status': 'ok', 'titles': 'otillgänglig', 'items': [],
                                  'parked': [parked(), parked(task='office-saknas', title=None,
                                                             status='saknas'),
                                             parked(task='office-olaslig', title=None,
                                                    status='oläslig'),
                                             parked(task='office-okand', title=None,
                                                    status='okänd')]},
                      sources=sources(unavailable=('tasks',)),
                      sockeln=dict(projection()['sockeln'], idle_tasks=4),
                      headline={'pagar': 0, 'vantar': 0, 'behover_dig': 0, 'lugnt': False})
        self.assertIn('class="aq-park aq-pa"', result)
        self.assertIn('class="aq-park aq-pa aq-titel-saknas"', result)
        self.assertIn('En vilande rubrik · office-vilar · sedan 24 sep 11:10', result)
        self.assertIn('titel saknas i uppdragsfilen', result)
        self.assertIn('titeln kunde inte läsas', result)
        self.assertIn('uppdragsfilerna kunde inte läsas', result)
        self.assertIn('kunde inte läsas; titlarna är okända men uppdragen visas', result)
        self.assertIn('4 uppdrag', result)
        self.assertIn('inget arbete observerat i motorn · 4 uppdrag arbetar inte', result)
        self.assertIn('Runtime · uppdragsfiler</span>otillgänglig vid läsningen', result)

    def test_the_review_desk_shows_review_and_integration(self):
        review = page(verkstaden={'status': 'ok', 'titles': 'ok', 'parked': [], 'items': [
            work(task='office-gransk', step='granskning', state='granskas', executor=None,
                 activities=('review_candidate',)),
            work(task='office-int', step='integration', state='integreras', executor=None,
                 activities=('publish_candidate',))]},
            headline={'pagar': 2, 'vantar': 0, 'behover_dig': 0, 'lugnt': False})
        self.assertIn('class="aq-gransk aq-granskas aq-figur aq-okand"', review)
        self.assertIn('granskare ej belagd', review)
        self.assertIn('1 granskas · 1 integreras', review)
        self.assertIn('+1', review)
        self.assertIn('>Granskas</span>office-gransk · granskare ej belagd · sedan 24 sep 11:20 '
                      '· steg review_candidate<', review)
        self.assertIn('>Integreras</span>office-int · värdens integration', review)
        self.assertIn('Inget arbete pågår i motorn', review)
        integration = page(verkstaden={'status': 'ok', 'titles': 'ok', 'parked': [], 'items': [
            work(task='office-int', step='integration', state='integreras', executor=None,
                 activities=('publish_candidate',))]},
            headline={'pagar': 1, 'vantar': 0, 'behover_dig': 0, 'lugnt': False})
        self.assertIn('class="aq-gransk aq-integreras"', integration)
        self.assertIn('1 integreras', integration)
        self.assertNotIn('granskas ·', integration)
        empty = page()
        self.assertIn('class="aq-gransk aq-vilar"', empty)
        self.assertIn('ingen granskning observerad', empty)
        self.assertIn('Ingen granskning eller integration pågår i motorn', empty)

    def test_more_than_the_places_show_a_rest(self):
        result = page(verkstaden={'status': 'ok', 'titles': 'ok',
                                  'items': [work(task='office-%d' % n) for n in range(5)],
                                  'parked': [parked(task='office-p%d' % n) for n in range(10)]},
                      sockeln=dict(projection()['sockeln'], busy=5, idle_tasks=10),
                      headline={'pagar': 5, 'vantar': 0, 'behover_dig': 0, 'lugnt': False})
        self.assertEqual(result.count('>+2<'), 2)  # two benches over and two cards over
        self.assertNotIn('ledig bänk', result)
        self.assertIn('5 i arbete · 10 uppdrag arbetar inte', result)


class Utkiken(unittest.TestCase):
    def watch(self, **overrides):
        return page(utkiken=dict(projection()['utkiken'], **overrides),
                    headline={'pagar': 0, 'vantar': 0, 'behover_dig': 0, 'lugnt': False})

    def test_a_planned_round_is_not_a_started_round(self):
        result = self.watch(next_planned='2026-09-25T09:00:00+00:00')
        self.assertIn('>25<', result)
        self.assertIn('nästa omgång planerad 25 sep 11:00 · inte genomförd', result)
        self.assertIn('nästa omgång 25 sep 11:00', result)
        self.assertIn('planerad 25 sep 11:00 · inte genomförd', result)
        self.assertIn('>Senaste starter</span>inga kända<', result)
        self.assertIn('class="aq-plats aq-utkiken  aq-lugn"', result)
        self.assertNotIn('Igång vid läsningen', result)

    def test_a_running_round_shows_the_watch_figure(self):
        result = self.watch(running=1, starts=['2026-09-24T12:40:00+00:00'])
        self.assertIn('class="aq-plats aq-utkiken  aq-kor"', result)
        self.assertIn('>Bevakningen<', result)
        self.assertIn('utförare ej belagd', result)
        self.assertIn('omgång startad 24 sep 14:40', result)
        self.assertIn('>Igång vid läsningen</span>1 omgång<', result)
        self.assertIn('bevakningen kör en omgång', result)
        without = self.watch(running=2, starts=[])
        self.assertIn('omgång pågår · starttid okänd', without)
        self.assertIn('>Igång vid läsningen</span>2 omgångar<', without)

    def test_an_old_reviewed_decision_stays_old(self):
        result = self.watch(reviewed={'at': '2026-09-20T09:00:00+00:00',
                                      'decision': 'förslag till åtgärd',
                                      'older_than_a_day': True})
        self.assertIn('>20 sep<', result)
        self.assertIn('senast granskade besked 20 sep 11:00 · förslag till åtgärd · äldre än ett '
                      'dygn', result)
        self.assertIn('>Senast granskade besked</span>20 sep 11:00 · förslag till åtgärd · äldre '
                      'än ett dygn<', result)
        unknown = self.watch(reviewed={'at': '2026-09-24T09:00:00+00:00', 'decision': None,
                                       'older_than_a_day': False})
        self.assertIn('senast granskade besked 24 sep 11:00 · beslut okänt', unknown)
        self.assertNotIn('äldre än ett dygn', unknown)
        none = self.watch()
        self.assertIn('inget granskat besked', none)
        self.assertIn('>inget<', none)

    def test_a_report_and_its_cause(self):
        result = self.watch(latest={'at': '2026-09-24T09:30:00+00:00',
                                    'outcome': 'genomförd, otillräcklig',
                                    'cause': 'leverantören tog inte emot analysen (kapacitet)'},
                            waiting=True, next_planned='2026-09-25T09:00:00+00:00')
        self.assertIn('senaste rapport 24 sep 11:30 · genomförd, otillräcklig · leverantören '
                      'tog inte emot analysen (kapacitet)', result)
        self.assertIn('senaste omgången otillräcklig · nästa 25 sep 11:00', result)
        self.assertIn('bevakningens senaste omgång otillräcklig', result)
        waiting = self.watch(latest={'at': None, 'outcome': 'genomförd, granskad', 'cause': None},
                             waiting=True)
        self.assertIn('senaste rapport tid okänd · genomförd, granskad', waiting)
        self.assertIn('besked väntar på granskning', waiting)
        self.assertIn('class="aq-plats aq-utkiken  aq-vantar"', waiting)

    def test_schedule_states_and_an_unreadable_watch(self):
        self.assertIn('bevakningen stoppad', self.watch(schedule='stoppat'))
        self.assertIn('>stoppad<', self.watch(schedule='stoppat'))
        self.assertIn('bevakningen pausad', self.watch(schedule='pausat'))
        self.assertIn('schemat är okänt', self.watch(schedule='okänt'))
        unreadable = page(
            sources=sources(unavailable=('watch',)),
            utkiken={'status': 'otillgänglig', 'schedule': 'okänt', 'next_planned': None,
                     'running': None, 'starts': [], 'latest': None, 'reviewed': None,
                     'waiting': False,
                     'model': {'executor': 'codex', 'model': 'gpt-5-codex',
                               'follows_model_choice': False}},
            headline={'pagar': 0, 'vantar': None, 'behover_dig': None, 'lugnt': False},
            agarens_bord={'status': 'otillgänglig', 'items': []})
        self.assertIn('class="aq-plats aq-utkiken aq-otillganglig "', unreadable)
        self.assertIn('bevakningen kunde inte läsas', unreadable)
        self.assertIn('Bevakningen kunde inte läsas; inget visas som lugnt', unreadable)
        self.assertIn('bevakningens plats · konfigurerad: Codex gpt-5-codex', unreadable)
        self.assertNotIn('bevakningen i vila', unreadable)


class Bordet(unittest.TestCase):
    def item(self, kind='beslut', text='Ta ställning till AP12', since='2026-09-22'):
        return {'kind': kind, 'text': text, 'since': since, 'basis': 'beslutsloggen AP12'}

    def test_letters_a_mark_and_the_rows(self):
        result = page(agarens_bord={'status': 'ok', 'items': [
            self.item(), self.item('operatörshandling', 'Starta tjänsten', None),
            self.item('modellfråga', 'Byt modell', '2026-09-24T09:00:00+00:00'),
            self.item(text='Fyra'), self.item(text='Fem')]},
            headline={'pagar': 0, 'vantar': 0, 'behover_dig': 5, 'lugnt': False})
        self.assertIn('class="aq-plats aq-bordet aq-harbord"', result)
        self.assertIn('Beslut: Ta ställning till AP12 · sedan 22 sep', result)
        self.assertIn('Operatörshandling: Starta tjänsten<', result)
        self.assertIn('Modellfråga: Byt modell · sedan 24 sep 11:00', result)
        self.assertIn('>5<', result)
        self.assertIn('>+1<', result)
        self.assertIn('5 ärenden väntar på dig', result)
        self.assertIn('>Beslut · sedan 22 sep</span>Ta ställning till AP12 — beslutsloggen AP12<',
                      result)

    def test_an_empty_table_and_an_incomplete_one(self):
        empty = page()
        self.assertIn('class="aq-plats aq-bordet "', empty)
        self.assertIn('Inga ärenden väntar på dig', empty)
        incomplete = page(agarens_bord={'status': 'otillgänglig', 'items': [self.item()]},
                          headline={'pagar': 0, 'vantar': None, 'behover_dig': None,
                                    'lugnt': False},
                          sources=sources(unavailable=('questions',)))
        self.assertIn('class="aq-plats aq-bordet aq-harbord aq-ofullstandig"', incomplete)
        self.assertIn('ett beslut väntar på dig · fler kan finnas', incomplete)
        self.assertIn('En källa kunde inte läsas; fler ärenden kan finnas', incomplete)


class Arkivet(unittest.TestCase):
    def item(self, key='AP10', title='AP10 levererad', date='2026-09-15'):
        return {'key': key, 'title': title, 'date': date,
                'basis': 'beslutsloggen ' + key + '-LEVERANS'}

    def test_volumes_dates_and_the_newest_mark(self):
        result = page(arkivet={'status': 'ok', 'items': [
            self.item('AP11', 'AP11 avslutat', '2026-09-24'), self.item(),
            self.item('AP12', 'Utan datum', None)]})
        self.assertIn('class="aq-vol aq-vol-0 aq-pa aq-ny"', result)
        self.assertIn('class="aq-vol aq-vol-1 aq-pa"', result)
        self.assertIn('AP11 · AP11 avslutat · 24 sep', result)
        self.assertIn('AP12 · Utan datum · odaterad', result)
        self.assertIn('3 leveranser · senast 24 sep', result)
        self.assertIn('>15 sep</span>AP10 · AP10 levererad — beslutsloggen AP10-LEVERANS<',
                      result)
        self.assertIn('>odaterad</span>AP12 · Utan datum — beslutsloggen AP12-LEVERANS<', result)
        self.assertIn('main 1a1a1a1a', result)
        self.assertIn('class="aq-vol aq-vol-3 aq-av"', result)

    def test_one_delivery_and_none(self):
        one = page(arkivet={'status': 'ok', 'items': [self.item()]})
        self.assertIn('1 leverans · senast 15 sep', one)
        self.assertIn('Inga leveranser registrerade', page())
        many = page(arkivet={'status': 'ok', 'items': [self.item('AP%d' % n) for n in range(20)]})
        self.assertIn('>+4<', many)
        self.assertIn('20 leveranser', many)


class Maskinrummet(unittest.TestCase):
    def sockeln(self, **overrides):
        return page(sockeln=dict(projection()['sockeln'], **overrides),
                    headline={'pagar': 0, 'vantar': 0, 'behover_dig': 0, 'lugnt': False})

    def test_the_service_and_the_technical_records(self):
        running = self.sockeln(identity_records=2, busy=1, idle_tasks=3)
        self.assertIn('class="aq-plats aq-maskinrummet aq-igang"', running)
        self.assertIn('tjänsten igång · 3 av 3 verifierade · 2 tekniska poster, inte agenter',
                      running)
        self.assertIn('>Tjänsten</span>tjänsten igång · 3 av 3 verifierade · konfiguration '
                      'abababab<', running)
        self.assertIn('>Identitetsposter</span>2 tekniska poster, inte agenter<', running)
        self.assertIn('>Revision</span>Runtime cdcdcdcd · konfiguration abababab<', running)
        one = self.sockeln(identity_records=1)
        self.assertIn('1 teknisk post, inte en agent', one)
        partly = self.sockeln(service={'state': 'delvis', 'verified': 2, 'of': 3,
                                       'config': 'abababab'})
        self.assertIn('class="aq-plats aq-maskinrummet aq-delvis"', partly)
        self.assertIn('tjänsten delvis igång · 2 av 3 verifierade', partly)
        nothing = self.sockeln(service={'state': 'okänt', 'verified': 0, 'of': 3, 'config': None})
        self.assertIn('tjänsten okänd · ingen verifierad', nothing)
        self.assertIn('class="aq-plats aq-maskinrummet aq-okand"', nothing)
        unread = self.sockeln(service={'state': 'okänt', 'verified': None, 'of': 3,
                                       'config': None})
        self.assertIn('tjänsten kunde inte läsas', unread)

    def test_an_unknown_staffing_and_revision(self):
        result = self.sockeln(staffing=[], watch_staffing={'executor': 'codex', 'model': None})
        self.assertIn('>Konfigurerad bemanning</span>okänd<', result)
        self.assertIn('Codex · modell okänd · följer inte modellvalet', result)
        unknown = page(revisions={'office_main': None, 'office_main_date': None, 'runtime': None,
                                  'config': None},
                       sources=sources(unavailable=('office', 'release')),
                       arkivet={'status': 'otillgänglig', 'items': []},
                       agarens_bord={'status': 'otillgänglig', 'items': []},
                       headline={'pagar': 0, 'vantar': 0, 'behover_dig': None, 'lugnt': False})
        self.assertIn('>Kontoret · revision</span>okänd<', unknown)
        self.assertIn('>Runtime · revision</span>okänd<', unknown)
        self.assertNotIn(' · main None', unknown)


class Safety(unittest.TestCase):
    def test_hostile_text_is_escaped(self):
        hostile = '<script>alert("x")</script> & \'slut\''
        result = page(arkivet={'status': 'ok', 'items': [
            {'key': hostile, 'title': hostile, 'date': None, 'basis': hostile}]},
            agarens_bord={'status': 'ok', 'items': [
                {'kind': hostile, 'text': hostile, 'since': None, 'basis': hostile}]},
            headline={'pagar': 0, 'vantar': 0, 'behover_dig': 1, 'lugnt': False})
        self.assertNotIn('<script>alert', result)
        self.assertIn('&lt;script&gt;alert(&quot;x&quot;)&lt;/script&gt; &amp; &#x27;slut&#x27;',
                      result)
        self.assertIn('<script>' + aquarium_vy.SKRIPT + '</script>', result)

    def test_a_projection_that_is_not_schema_two_is_refused(self):
        for broken in (None, {}, 'text', [], dict(projection(), schema=1),
                       dict(projection(), schema='2'), dict(projection(), provdata='ja'),
                       dict(projection(), read_at='2026-09-24T12:52:00'),
                       dict(projection(), read_at=None)):
            with self.assertRaises(ValueError):
                aquarium_vy.render(broken)
        extra = projection()
        extra['extra'] = 1
        with self.assertRaises(ValueError):
            aquarium_vy.render(extra)
        missing = projection()
        del missing['sockeln']
        with self.assertRaises(ValueError):
            aquarium_vy.render(missing)

    def test_a_broken_source_or_count_is_refused(self):
        without = projection()
        del without['sources']['tasks']
        with self.assertRaises(ValueError):
            aquarium_vy.render(without)
        bad_status = projection()
        bad_status['sources']['engine']['status'] = 'unavailable'
        with self.assertRaises(ValueError):
            aquarium_vy.render(bad_status)
        naive = projection()
        naive['sources']['engine']['read_at'] = '2026-09-24T12:52:00'
        with self.assertRaises(ValueError):
            aquarium_vy.render(naive)
        no_limit = projection()
        no_limit['sources']['engine']['stale_after_seconds'] = None
        with self.assertRaises(ValueError):
            aquarium_vy.render(no_limit)
        count = projection()
        count['headline']['pagar'] = '3'
        with self.assertRaises(ValueError) as caught:
            aquarium_vy.render(count)
        self.assertEqual(str(caught.exception), aquarium_vy.ERROR)
        self.assertNotIn('3', str(caught.exception))


class Command(unittest.TestCase):
    def setUp(self):
        self.assertTrue(SCRATCH.is_dir(), 'the repository keeps an existing .scratch')
        self.temporary = tempfile.TemporaryDirectory(dir=str(SCRATCH))
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.source = self.base / 'projection.json'
        self.source.write_text(json.dumps(projection(), ensure_ascii=False), encoding='utf-8')

    def run_command(self, arguments):
        stream = io.StringIO()
        with redirect_stderr(stream):
            code = aquarium_vy.main(arguments)
        return code, stream.getvalue()

    def test_a_private_page_is_written_once(self):
        target = self.base / 'vy.html'
        code, printed = self.run_command([str(self.source), str(target)])
        self.assertEqual((code, printed), (0, ''))
        self.assertEqual(os.stat(target).st_mode & 0o777, 0o600)
        self.assertEqual(target.read_text(encoding='utf-8'),
                         aquarium_vy.render(projection()))
        again, message = self.run_command([str(self.source), str(target)])
        self.assertEqual(again, 2)
        self.assertEqual(message, aquarium_vy.COMMAND_ERROR + '\n')

    def test_wrong_arguments_and_a_missing_parent(self):
        for arguments in ([], [str(self.source)], [str(self.source), 'a', 'b'],
                          [str(self.base / 'saknas.json'), str(self.base / 'ny.html')],
                          [str(self.source), str(self.base / 'saknas' / 'ny.html')]):
            code, message = self.run_command(arguments)
            self.assertEqual(code, 2)
            self.assertEqual(message, aquarium_vy.COMMAND_ERROR + '\n')

    def test_a_symlinked_source_and_a_directory_are_refused(self):
        linked = self.base / 'lankad.json'
        linked.symlink_to(self.source)
        code, message = self.run_command([str(linked), str(self.base / 'ny.html')])
        self.assertEqual(code, 2)
        self.assertEqual(message, aquarium_vy.COMMAND_ERROR + '\n')
        self.assertFalse((self.base / 'ny.html').exists())
        directory = self.base / 'katalog'
        directory.mkdir()
        self.assertEqual(self.run_command([str(directory), str(self.base / 'ny2.html')])[0], 2)

    def test_too_large_and_broken_content_is_refused(self):
        big = self.base / 'stor.json'
        big.write_bytes(b'{"x": "' + b'a' * 1000001 + b'"}')
        self.assertEqual(self.run_command([str(big), str(self.base / 'ny.html')])[0], 2)
        broken = self.base / 'trasig.json'
        broken.write_text('inte json', encoding='utf-8')
        self.assertEqual(self.run_command([str(broken), str(self.base / 'ny3.html')])[0], 2)
        self.assertFalse((self.base / 'ny3.html').exists())

    def test_the_page_is_written_as_utf8_with_the_pinned_script(self):
        target = self.base / 'vy2.html'
        self.assertEqual(self.run_command([str(self.source), str(target)])[0], 0)
        raw = target.read_bytes()
        self.assertIn('PROVDATA'.encode('utf-8'), raw)
        self.assertIn('inaktuell'.encode('utf-8'), raw)
        self.assertIn('läst 24 sep 14:52'.encode('utf-8'), raw)
        digest = base64.b64encode(hashlib.sha256(
            aquarium_vy.SKRIPT.encode('utf-8')).digest()).decode('ascii')
        self.assertIn(('sha256-' + digest).encode('utf-8'), raw)


if __name__ == '__main__':
    unittest.main()
