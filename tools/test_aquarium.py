"""Synthetic tests for Aquarium v0. No real source, probe, git repository or network.

Every temporary file lives under the repository's existing `.scratch`, which is never
removed, replaced or recreated.
"""
from contextlib import redirect_stderr
from copy import deepcopy
from datetime import datetime, timezone
import io
import json
import os
from pathlib import Path
import tempfile
import unittest

import aquarium

SCRATCH = Path(__file__).absolute().parents[1] / '.scratch'
NOW = datetime(2026, 9, 24, 12, 0, tzinfo=timezone.utc)
READ_AT = '2026-09-24T12:00:00+00:00'


def values():
    return {
        'release': {'config_sha256': 'ab' * 32, 'runtime_revision': 'cd' * 20,
                    'office_revision': 'ef' * 20},
        'staffing': {'executors': {'utvecklare': 'claude', 'granskare': 'codex'},
                     'models_run': {'claude': 'claude-opus-5', 'codex': 'gpt-5-codex'},
                     'watch_model': 'gpt-5-codex'},
        'questions': {'items': []},
        'service': {'parts': {'daemon': {'identity_matches': True},
                              'engine': {'identity_matches': True},
                              'worker': {'identity_matches': True}}},
        'engine': {'executions': []},
        'tasks': {'items': []},
        'watch': {'native': {'paused': False, 'note': '', 'next_action_times': [],
                             'running': [], 'recent': []},
                  'latest': None, 'reviewed': None, 'refused_for_capacity': False,
                  'owner_question': None},
        'office': {'main': '1a' * 20, 'main_date': '2026-09-24T08:00:00+02:00',
                   'entries': [], 'notes': [], 'plan_owner_turn': []}}


def readings(unavailable=(), **overrides):
    base = values()
    base.update(overrides)
    sources = {}
    for name in aquarium.SOURCES:
        if name in unavailable:
            sources[name] = {'status': 'unavailable', 'read_at': READ_AT, 'value': None}
        else:
            sources[name] = {'status': 'ok', 'read_at': READ_AT, 'value': base[name]}
    return {'schema': 2, 'provdata': False, 'read_started_at': READ_AT, 'sources': sources}


def entry(identity, title, text=''):
    return {'id': identity, 'title': title, 'text': text}


def execution(kind, activities=(), workflow_task=False, start=None, task='office-uppdrag'):
    """One engine execution; Runtime starts each task's workflow with the task id."""
    return {'id': task, 'type': kind, 'pending_activities': list(activities),
            'pending_workflow_task': workflow_task, 'start': start}


def task_item(identity, status='läst', title='En rubrik'):
    return {'id': identity, 'title': title if status == 'läst' else None, 'status': status}


class Envelope(unittest.TestCase):
    def test_sources_titles_and_staleness(self):
        result = aquarium.project(readings(), NOW)
        self.assertEqual(result['schema'], 2)
        self.assertIs(result['provdata'], False)
        self.assertEqual(result['read_at'], READ_AT)
        self.assertEqual(aquarium.SOURCES, ('release', 'staffing', 'questions', 'service',
                                            'engine', 'tasks', 'watch', 'office'))
        self.assertEqual(set(result['sources']), set(aquarium.SOURCES))
        self.assertEqual(result['sources']['office']['title'], 'Kontoret · beslut och leveranser')
        self.assertEqual(result['sources']['watch']['title'], 'Runtime · bevakningen')
        self.assertEqual(result['sources']['tasks']['title'], 'Runtime · uppdragsfiler')
        self.assertEqual(result['sources']['office']['stale_after_seconds'], 3600)
        for name in aquarium.RUNTIME_SOURCES + ('watch',):
            self.assertEqual(result['sources'][name]['stale_after_seconds'], 300)
            self.assertEqual(result['sources'][name]['status'], 'ok')
            self.assertEqual(result['sources'][name]['read_at'], READ_AT)

    def test_output_keys_are_exactly_the_contract(self):
        result = aquarium.project(readings(), NOW)
        self.assertEqual(set(result), {'schema', 'provdata', 'read_at', 'sources', 'revisions',
                                       'headline', 'arkivet', 'verkstaden', 'utkiken',
                                       'agarens_bord', 'sockeln'})
        self.assertEqual(set(result['revisions']),
                         {'office_main', 'office_main_date', 'runtime', 'config'})
        self.assertEqual(set(result['headline']), {'pagar', 'vantar', 'behover_dig', 'lugnt'})
        self.assertEqual(set(result['sockeln']), {'service', 'staffing', 'watch_staffing',
                                                  'idle_tasks', 'identity_records', 'busy'})
        self.assertEqual(set(result['verkstaden']), {'status', 'items', 'parked', 'titles'})

    def test_revisions_are_shortened(self):
        result = aquarium.project(readings(), NOW)['revisions']
        self.assertEqual(result['office_main'], '1a1a1a1a')
        self.assertEqual(result['office_main_date'], '2026-09-24T08:00:00+02:00')
        self.assertEqual(result['runtime'], 'cdcdcdcd')
        self.assertEqual(result['config'], 'abababab')

    def test_input_is_never_mutated(self):
        given = readings(engine={'executions': [execution('Bygge', ['Steg'])]})
        untouched = deepcopy(given)
        aquarium.project(given, NOW)
        self.assertEqual(given, untouched)

    def test_invalid_input_is_refused_without_private_values(self):
        for broken in (None, {}, {'schema': 2}, 'text', dict(readings(), schema=1)):
            with self.assertRaises(ValueError):
                aquarium.project(broken, NOW)
        missing = readings()
        del missing['sources']['watch']
        with self.assertRaises(ValueError) as caught:
            aquarium.project(missing, NOW)
        self.assertEqual(str(caught.exception), aquarium.ERROR)
        without_tasks = readings()  # A reading must carry all eight sources.
        del without_tasks['sources']['tasks']
        with self.assertRaises(ValueError):
            aquarium.project(without_tasks, NOW)
        naive = readings()
        with self.assertRaises(ValueError):
            aquarium.project(naive, datetime(2026, 9, 24, 12, 0))
        with self.assertRaises(ValueError):
            aquarium.project(readings(release={'config_sha256': 'kort', 'runtime_revision': 'cd' * 20,
                                               'office_revision': 'ef' * 20}), NOW)


class UnavailableSources(unittest.TestCase):
    def test_office_unavailable_beside_working_sources(self):
        result = aquarium.project(readings(unavailable=('office',)), NOW)
        self.assertEqual(result['sources']['office']['status'], 'otillgänglig')
        self.assertEqual(result['sources']['engine']['status'], 'ok')
        self.assertEqual(result['arkivet'], {'status': 'otillgänglig', 'items': []})
        self.assertIsNone(result['revisions']['office_main'])
        self.assertIsNone(result['revisions']['office_main_date'])
        self.assertEqual(result['revisions']['runtime'], 'cdcdcdcd')
        self.assertEqual(result['agarens_bord']['status'], 'otillgänglig')
        self.assertIsNone(result['headline']['behover_dig'])
        self.assertEqual(result['headline']['pagar'], 0)
        self.assertIs(result['headline']['lugnt'], False)

    def test_engine_unavailable(self):
        result = aquarium.project(readings(unavailable=('engine',)), NOW)
        self.assertEqual(result['verkstaden'], {'status': 'otillgänglig', 'items': [],
                                                'parked': [], 'titles': 'ok'})
        self.assertIsNone(result['headline']['pagar'])
        for key in ('idle_tasks', 'identity_records', 'busy'):
            self.assertIsNone(result['sockeln'][key])
        # The real reading never asks for task files without the engine, so both are unavailable.
        both = aquarium.project(readings(unavailable=('engine', 'tasks')), NOW)
        self.assertEqual(both['verkstaden'], {'status': 'otillgänglig', 'items': [],
                                             'parked': [], 'titles': 'otillgänglig'})

    def test_task_files_unavailable_beside_a_read_engine(self):
        given = readings(unavailable=('tasks',),
                         engine={'executions': [execution('Vilande', task='office-vilar')]})
        result = aquarium.project(given, NOW)
        self.assertEqual(result['verkstaden']['titles'], 'otillgänglig')
        self.assertEqual(result['verkstaden']['status'], 'ok')
        parked = result['verkstaden']['parked']
        self.assertEqual([(item['title'], item['title_status']) for item in parked],
                         [(None, 'okänd')])
        self.assertEqual(result['sockeln']['idle_tasks'], 1)
        self.assertIs(result['headline']['lugnt'], False)

    def test_watch_unavailable(self):
        result = aquarium.project(readings(unavailable=('watch',)), NOW)
        utkiken = result['utkiken']
        self.assertEqual(utkiken['status'], 'otillgänglig')
        self.assertEqual(utkiken['schedule'], 'okänt')
        self.assertIsNone(utkiken['next_planned'])
        self.assertIsNone(utkiken['running'])
        self.assertEqual(utkiken['starts'], [])
        self.assertIsNone(utkiken['latest'])
        self.assertIsNone(utkiken['reviewed'])
        self.assertIs(utkiken['waiting'], False)
        self.assertEqual(utkiken['model']['model'], 'gpt-5-codex')
        self.assertIsNone(result['headline']['vantar'])
        self.assertIsNone(result['headline']['behover_dig'])

    def test_staffing_unavailable_leaves_the_watch_readable(self):
        result = aquarium.project(readings(unavailable=('staffing',)), NOW)
        self.assertEqual(result['utkiken']['status'], 'ok')
        self.assertIsNone(result['utkiken']['model']['model'])
        self.assertEqual(result['utkiken']['model']['executor'], 'codex')
        self.assertIs(result['utkiken']['model']['follows_model_choice'], False)
        self.assertEqual(result['sockeln']['staffing'], [])
        self.assertEqual(result['sockeln']['watch_staffing'], {'executor': 'codex', 'model': None})

    def test_service_and_release_unavailable(self):
        result = aquarium.project(readings(unavailable=('service', 'release')), NOW)['sockeln']
        self.assertEqual(result['service']['state'], 'okänt')
        self.assertIsNone(result['service']['verified'])
        self.assertIsNone(result['service']['config'])
        self.assertEqual(result['service']['of'], 3)

    def test_owner_table_keeps_items_from_available_sources(self):
        given = readings(unavailable=('questions',),
                         office={'main': '1a' * 20, 'main_date': READ_AT, 'entries': [],
                                 'notes': [],
                                 'plan_owner_turn': [{'kind': 'beslut', 'text': 'Välj väg',
                                                      'since': '2026-09-20'}]})
        result = aquarium.project(given, NOW)
        self.assertEqual(result['agarens_bord']['status'], 'otillgänglig')
        self.assertEqual([item['text'] for item in result['agarens_bord']['items']], ['Välj väg'])
        self.assertIsNone(result['headline']['behover_dig'])
        self.assertIsNone(result['headline']['vantar'])


class Arkivet(unittest.TestCase):
    def project(self, office):
        return aquarium.project(readings(office=office), NOW)['arkivet']

    def test_deliveries_notes_dates_and_order(self):
        office = {'main': '1a' * 20, 'main_date': READ_AT, 'notes': [
            {'ap': 'AP04', 'title': 'AP04 levererat', 'text': 'Klart 2026-09-10.'},
            {'ap': 'AP11', 'title': 'Skuggat besked', 'text': 'Ska inte räknas två gånger.'}],
            'plan_owner_turn': [], 'entries': [
            entry('AP10-LEVERANS', 'AP10 levererad', 'Slutfört 2026-09-15.'),
            entry('AP10-SIGNALRATTNING-LEVERANS-20260924', 'Signalrättning levererad'),
            entry('AP11-AVSLUT-20260924', 'AP11 avslutat'),
            entry('AQUARIUM-V0-ACCEPT-20260924', 'Accept av Aquarium v0')]}
        result = self.project(office)
        self.assertEqual(result['status'], 'ok')
        self.assertEqual([(item['key'], item['date']) for item in result['items']],
                         [('AP10-SIGNALRATTNING', '2026-09-24'), ('AP11', '2026-09-24'),
                          ('AP10', '2026-09-15'), ('AP04', '2026-09-10')])
        self.assertEqual(result['items'][0]['title'], 'Signalrättning levererad')
        self.assertEqual(result['items'][0]['basis'],
                         'beslutsloggen AP10-SIGNALRATTNING-LEVERANS-20260924')
        self.assertEqual(result['items'][-1]['basis'], 'leveransbesked AP04')

    def test_undated_items_last_and_nothing_invented(self):
        office = {'main': '1a' * 20, 'main_date': READ_AT, 'notes': [], 'plan_owner_turn': [],
                  'entries': [entry('AP12-AVSLUT', 'Utan datum'),
                              entry('AP13-LEVERANS-20260901', 'Med datum'),
                              entry('AP14-BEREDNING-20260902', 'Ingen leverans')]}
        result = self.project(office)
        self.assertEqual([item['key'] for item in result['items']], ['AP13', 'AP12'])
        self.assertIsNone(result['items'][1]['date'])
        self.assertEqual(len(result['items']), 2)

    def test_eight_digit_date_and_text_fallback(self):
        office = {'main': '1a' * 20, 'main_date': READ_AT, 'notes': [], 'plan_owner_turn': [],
                  'entries': [entry('AP15-LEVERANS', 'Datum i texten', 'Levererat 20260812.')]}
        self.assertEqual(self.project(office)['items'][0]['date'], '2026-08-12')

    def test_a_commit_hash_is_never_a_date(self):
        # The first real reading dated three deliveries from digit runs inside commit hashes.
        office = {'main': '1a' * 20, 'main_date': READ_AT, 'notes': [], 'plan_owner_turn': [],
                  'entries': [
                      entry('AP20-LEVERANS', 'Bara en hash',
                            'Publicerad som 3510182456789abc0778277412345def.'),
                      entry('AP21-LEVERANS', 'Hash och datum',
                            'main 0151714312ab34cd — levererad 2026-09-12.')]}
        items = self.project(office)['items']
        dates = {item['key']: item['date'] for item in items}
        self.assertIsNone(dates['AP20'])
        self.assertEqual(dates['AP21'], '2026-09-12')

    def test_an_undated_delivery_takes_the_date_of_its_note(self):
        office = {'main': '1a' * 20, 'main_date': READ_AT, 'plan_owner_turn': [],
                  'notes': [{'ap': 'AP10', 'title': 'AP10 levererat', 'text': 'Klart 2026-09-15.'}],
                  'entries': [entry('AP10-LEVERANS', 'AP10 levererad')]}
        items = self.project(office)['items']
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]['key'], 'AP10')
        self.assertEqual(items[0]['date'], '2026-09-15')
        self.assertEqual(items[0]['basis'],
                         'beslutsloggen AP10-LEVERANS, datum ur leveransbesked AP10')

    def test_the_entry_date_wins_and_an_undated_note_invents_nothing(self):
        office = {'main': '1a' * 20, 'main_date': READ_AT, 'plan_owner_turn': [],
                  'notes': [{'ap': 'AP10', 'title': 'AP10 levererat', 'text': 'Klart 2026-09-15.'},
                            {'ap': 'AP12', 'title': 'AP12 levererat', 'text': 'Utan datum.'}],
                  'entries': [entry('AP10-LEVERANS-20260924', 'AP10 levererad'),
                              entry('AP12-LEVERANS', 'AP12 levererad')]}
        items = {item['key']: item for item in self.project(office)['items']}
        self.assertEqual(items['AP10']['date'], '2026-09-24')
        self.assertEqual(items['AP10']['basis'], 'beslutsloggen AP10-LEVERANS-20260924')
        self.assertIsNone(items['AP12']['date'])
        self.assertEqual(items['AP12']['basis'], 'beslutsloggen AP12-LEVERANS')


class DateRule(unittest.TestCase):
    def test_written_dates_are_read(self):
        self.assertEqual(aquarium._first_date('AP10-LEVERANS-20260924'), '2026-09-24')
        self.assertEqual(aquarium._first_date('levererad 2026-09-24 kl 12'), '2026-09-24')
        self.assertEqual(aquarium._first_date('20000101'), '2000-01-01')
        self.assertEqual(aquarium._first_date('2099-12-31'), '2099-12-31')

    def test_candidates_that_are_no_dates_are_skipped(self):
        for text in ('2026-13-45', '20260231', '1999-01-01', '2100-01-01', '2026-02-30',
                     'a20260924', '20260924b', '120260924', '202609241', '2026-09-241',
                     '12026-09-24', 'inget datum alls'):
            self.assertIsNone(aquarium._first_date(text), text)

    def test_the_search_goes_on_past_a_broken_candidate(self):
        self.assertEqual(aquarium._first_date('2026-13-45 men 2026-09-24'), '2026-09-24')
        self.assertEqual(aquarium._first_date('20260231 och 20260301'), '2026-03-01')
        self.assertEqual(aquarium._first_date('sha 4f8920260931ab, datum 2026-09-30'),
                         '2026-09-30')

    def test_the_id_comes_before_the_text(self):
        self.assertEqual(aquarium._first_date('AP-20260901', 'texten 20260902'), '2026-09-01')
        self.assertEqual(aquarium._first_date('AP-utan-datum', 'texten 20260902'), '2026-09-02')
        self.assertIsNone(aquarium._first_date(None, 17, 'ingenting'))

    def test_the_same_rule_holds_for_an_open_proposal(self):
        office = {'main': '1a' * 20, 'main_date': READ_AT, 'notes': [], 'plan_owner_turn': [],
                  'entries': [entry('AP22-BEREDNING-abc35101824', 'AP22',
                                    'Ett förslag, skrivet 2026-09-19.')]}
        items = aquarium.project(readings(office=office), NOW)['agarens_bord']['items']
        self.assertEqual(items[0]['since'], '2026-09-19')


class Verkstaden(unittest.TestCase):
    def project(self, executions, tasks=None):
        given = readings(engine={'executions': executions})
        if tasks is not None:
            given['sources']['tasks']['value'] = {'items': tasks}
        return aquarium.project(given, NOW)

    def test_identity_idle_busy_and_workflow_task(self):
        result = self.project([
            execution('ServiceIdentity', ['Ping'], True, '2026-09-24T09:00:00+00:00',
                      task='identitet-1'),
            execution('Vilande', [], False, '2026-09-24T09:10:00+00:00', task='office-vilar'),
            execution('Bygge', ['Kompilera', 'Prova'], False, '2026-09-24T09:20:00+00:00',
                      task='office-bygge'),
            execution('Kedja', [], True, '2026-09-24T09:30:00+00:00', task='office-kedja')],
            tasks=[task_item('office-vilar', title='Vilande uppdrag')])
        verkstaden = result['verkstaden']
        self.assertEqual(verkstaden['status'], 'ok')
        self.assertEqual(verkstaden['titles'], 'ok')
        self.assertEqual(verkstaden['items'], [
            {'task': 'office-bygge', 'short': 'bygge', 'type': 'Bygge',
             'since': '2026-09-24T09:20:00+00:00', 'step': 'steg', 'state': 'pågår',
             'executor': None, 'executor_basis': None,
             'activities': ['Kompilera', 'Prova']},
            {'task': 'office-kedja', 'short': 'kedja', 'type': 'Kedja',
             'since': '2026-09-24T09:30:00+00:00', 'step': 'arbetsflödessteg', 'state': 'pågår',
             'executor': None, 'executor_basis': None, 'activities': []}])
        self.assertEqual(verkstaden['parked'], [
            {'task': 'office-vilar', 'short': 'vilar', 'type': 'Vilande',
             'since': '2026-09-24T09:10:00+00:00', 'title': 'Vilande uppdrag',
             'title_status': 'läst'}])
        self.assertEqual(result['headline']['pagar'], 2)
        self.assertEqual(result['sockeln']['identity_records'], 1)
        self.assertEqual(result['sockeln']['idle_tasks'], 1)
        self.assertEqual(result['sockeln']['busy'], 2)

    def test_review_activity_is_under_review(self):
        result = self.project([execution('Granskning', ['SeparateReviewStep'], True,
                                         task='office-granskning')])
        item = result['verkstaden']['items'][0]
        self.assertEqual(item['state'], 'granskas')
        self.assertEqual(item['step'], 'granskning')
        self.assertIsNone(item['executor'])
        self.assertIsNone(item['executor_basis'])
        self.assertEqual(item['activities'], ['SeparateReviewStep'])
        self.assertEqual(item['type'], 'Granskning')
        self.assertIsNone(item['since'])

    def test_every_step_rule_in_order(self):
        result = self.project([
            execution('A', ['execute_claude', 'review_candidate'], task='office-a'),
            execution('B', ['execute_claude'], task='office-b'),
            execution('C', ['execute_codex'], task='office-c'),
            execution('D', ['execute_claude', 'execute_codex'], task='office-d'),
            execution('E', ['publish_candidate'], task='office-e'),
            execution('F', ['prepare'], task='office-f'),
            execution('G', [], True, task='office-g')])
        items = result['verkstaden']['items']
        self.assertEqual([(item['step'], item['state'], item['executor'], item['executor_basis'])
                          for item in items],
                         [('granskning', 'granskas', None, None),
                          ('utförande', 'pågår', 'claude', 'motorns steg execute_claude'),
                          ('utförande', 'pågår', 'codex', 'motorns steg execute_codex'),
                          ('utförande', 'pågår', None, None),
                          ('integration', 'integreras', None, None),
                          ('steg', 'pågår', None, None),
                          ('arbetsflödessteg', 'pågår', None, None)])
        self.assertEqual(result['sockeln']['busy'], 7)
        self.assertEqual(result['sockeln']['idle_tasks'], 0)

    def test_the_watch_round_and_technical_records_are_not_work(self):
        result = self.project([
            execution('PrivateAssessment', ['assess'], task='bevakning-1'),
            execution('PrivateAssessment', [], task='bevakning-2'),
            execution('ServiceIdentity', [], task='identitet-1')])
        self.assertEqual(result['verkstaden']['items'], [])
        self.assertEqual(result['verkstaden']['parked'], [])
        self.assertEqual(result['headline']['pagar'], 0)
        self.assertEqual(result['sockeln']['identity_records'], 1)
        self.assertEqual(result['sockeln']['idle_tasks'], 0)

    def test_short_names_and_parked_titles_in_every_status(self):
        result = self.project([execution('T', task='office-ett'), execution('T', task='office-'),
                              execution('T', task='utan-prefix'), execution('T', task='office-fyra')],
                              tasks=[task_item('office-ett', title='Rubrik ett'),
                                     task_item('office-', 'saknas'),
                                     task_item('utan-prefix', 'oläslig')])
        parked = result['verkstaden']['parked']
        self.assertEqual([item['short'] for item in parked],
                         ['ett', 'office-', 'utan-prefix', 'fyra'])
        self.assertEqual([(item['title'], item['title_status']) for item in parked],
                         [('Rubrik ett', 'läst'), (None, 'saknas'), (None, 'oläslig'),
                          (None, 'oläslig')])

    def test_a_malformed_task_value_is_refused(self):
        for broken in ({'items': [{'id': 'a', 'title': 'x', 'status': 'saknas'}]},
                       {'items': [{'id': 'a', 'title': None, 'status': 'läst'}]},
                       {'items': [{'id': 'a', 'title': None, 'status': 'annat'}]},
                       {'items': 'inte en lista'}):
            given = readings()
            given['sources']['tasks']['value'] = broken
            with self.assertRaises(ValueError):
                aquarium.project(given, NOW)


class Utkiken(unittest.TestCase):
    def project(self, **watch):
        value = values()['watch']
        native = dict(value['native'], **watch.pop('native', {}))
        value.update(watch)
        value['native'] = native
        return aquarium.project(readings(watch=value), NOW)['utkiken']

    def test_schedule_states(self):
        self.assertEqual(self.project(native={'paused': False})['schedule'], 'aktiverat')
        self.assertEqual(self.project(native={'paused': True})['schedule'], 'pausat')
        self.assertEqual(self.project(native={'paused': True, 'note': 'STOPPED av ägaren'})
                         ['schedule'], 'stoppat')

    def test_unknown_paused_is_not_an_error(self):
        for odd in ('ja', 1, None):
            result = self.project(native={'paused': odd, 'running': [{}, {}]})
            self.assertEqual(result['schedule'], 'okänt')
            self.assertEqual(result['status'], 'ok')
            self.assertEqual(result['running'], 2)
        value = values()['watch']  # A missing `paused` is read through the same rule.
        value['native'] = {'note': '', 'next_action_times': [], 'running': [], 'recent': []}
        self.assertEqual(aquarium.project(readings(watch=value), NOW)['utkiken']['schedule'], 'okänt')

    def test_next_planned_is_a_plan_not_a_performed_round(self):
        result = self.project(native={'next_action_times': ['2026-09-24T09:00:00+00:00',
                                                            '2026-09-26T09:00:00+00:00',
                                                            '2026-09-25T09:00:00+00:00']})
        self.assertEqual(result['next_planned'], '2026-09-25T09:00:00+00:00')
        past = self.project(native={'next_action_times': ['2026-09-23T09:00:00+00:00']})
        self.assertIsNone(past['next_planned'])

    def test_starts_are_newest_first_and_at_most_three(self):
        result = self.project(native={'recent': [
            {'started_at': '2026-09-21T09:00:00+00:00'},
            {'started_at': '2026-09-24T09:00:00+00:00'},
            {'started_at': '2026-09-22T09:00:00+00:00'},
            {'started_at': '2026-09-23T09:00:00+00:00'}]})
        self.assertEqual(result['starts'], ['2026-09-24T09:00:00+00:00',
                                            '2026-09-23T09:00:00+00:00',
                                            '2026-09-22T09:00:00+00:00'])

    def test_latest_outcome_cause_and_waiting(self):
        reviewed = self.project(latest={'reported_at': '2026-09-24T09:30:00+00:00',
                                        'reviewed': True, 'decision': 'retain'})
        self.assertEqual(reviewed['latest'], {'at': '2026-09-24T09:30:00+00:00',
                                              'outcome': 'genomförd, granskad', 'cause': None})
        self.assertIs(reviewed['waiting'], False)
        waiting = self.project(latest={'reported_at': '2026-09-24T09:30:00+00:00',
                                       'reviewed': False, 'decision': 'insufficient'},
                               refused_for_capacity=True)
        self.assertEqual(waiting['latest']['outcome'], 'genomförd, otillräcklig')
        self.assertEqual(waiting['latest']['cause'], aquarium.CAPACITY_CAUSE)
        self.assertIs(waiting['waiting'], True)
        unknown = self.project(latest={'reported_at': '2026-09-24T09:30:00+00:00',
                                       'reviewed': False, 'decision': 'insufficient'},
                               refused_for_capacity=None)
        self.assertIsNone(unknown['latest']['cause'])

    def test_a_fresh_reading_never_makes_an_old_decision_current(self):
        result = self.project(reviewed={'reviewed_at': '2026-09-20T09:00:00+00:00',
                                        'decision': 'propose_action'},
                              latest={'reported_at': '2026-09-24T09:30:00+00:00',
                                      'reviewed': False, 'decision': 'insufficient'})
        self.assertEqual(result['reviewed'], {'at': '2026-09-20T09:00:00+00:00',
                                              'decision': 'förslag till åtgärd',
                                              'older_than_a_day': True})
        fresh = self.project(reviewed={'reviewed_at': '2026-09-24T09:00:00+00:00',
                                       'decision': 'not_applicable'})
        self.assertEqual(fresh['reviewed'], {'at': '2026-09-24T09:00:00+00:00',
                                             'decision': 'inte tillämpligt',
                                             'older_than_a_day': False})
        other = self.project(reviewed={'reviewed_at': '2026-09-24T09:00:00+00:00',
                                       'decision': 'eget-ord'})
        self.assertEqual(other['reviewed']['decision'], 'eget-ord')

    def test_the_watch_model_never_becomes_a_model_question(self):
        result = aquarium.project(readings(), NOW)
        self.assertEqual(result['utkiken']['model'],
                         {'executor': 'codex', 'model': 'gpt-5-codex', 'follows_model_choice': False})
        self.assertEqual(result['agarens_bord']['items'], [])


class OwnerTable(unittest.TestCase):
    def test_proposal_with_and_without_a_later_accept(self):
        office = {'main': '1a' * 20, 'main_date': READ_AT, 'notes': [], 'plan_owner_turn': [],
                  'entries': [
                      entry('AQUARIUM-V0-BEREDNING-20260924', 'Aquarium v0',
                            'Ett samlat förslag till ägaren.'),
                      entry('AQUARIUM-V0-ACCEPT-20260924', 'Accept', 'Accepterat.'),
                      entry('AP12-BEREDNING-20260922', 'AP12', 'Här lämnas ett Förslag.'),
                      entry('AP13-BEREDNING-20260921', 'AP13', 'Ingen begäran här.'),
                      entry('AP14-BEREDNING-20260920', 'AP14', 'x' * 700 + ' förslag')]}
        items = aquarium.project(readings(office=office), NOW)['agarens_bord']['items']
        self.assertEqual(items, [{'kind': 'beslut', 'text': 'Ta ställning till AP12',
                                  'since': '2026-09-22',
                                  'basis': 'beslutsloggen AP12-BEREDNING-20260922'}])

    def test_plan_owner_turn_is_kept_as_given(self):
        office = {'main': '1a' * 20, 'main_date': READ_AT, 'notes': [], 'entries': [],
                  'plan_owner_turn': [{'kind': 'operatörshandling', 'text': 'Starta tjänsten',
                                       'since': None},
                                      {'kind': 'beslut', 'text': 'Välj modell',
                                       'since': '2026-09-23'}]}
        items = aquarium.project(readings(office=office), NOW)['agarens_bord']['items']
        self.assertEqual(items, [
            {'kind': 'operatörshandling', 'text': 'Starta tjänsten', 'since': None,
             'basis': 'planens ägartur'},
            {'kind': 'beslut', 'text': 'Välj modell', 'since': '2026-09-23',
             'basis': 'planens ägartur'}])

    def test_model_questions_are_one_per_distinct_pair(self):
        questions = {'items': [
            {'asked_at': '2026-09-23T09:00:00+00:00', 'executor': 'codex', 'model': 'gpt-5-codex',
             'still_selected': True},
            {'asked_at': '2026-09-24T09:00:00+00:00', 'executor': 'codex', 'model': 'gpt-5-codex',
             'still_selected': True},
            {'asked_at': '2026-09-24T10:00:00+00:00', 'executor': 'claude', 'model': 'claude-opus-5',
             'still_selected': False}]}
        result = aquarium.project(readings(questions=questions), NOW)
        self.assertEqual(result['agarens_bord']['items'], [
            {'kind': 'modellfråga',
             'text': 'Vald modell gpt-5-codex för codex tog inte emot anrop: vänta eller byt modell',
             'since': '2026-09-24T09:00:00+00:00', 'basis': 'Runtimes modellfråga'}])
        self.assertEqual(result['headline']['vantar'], 1)
        self.assertEqual(result['headline']['behover_dig'], 1)

    def test_watch_owner_question(self):
        watch = dict(values()['watch'], owner_question='Ta ställning till förslaget',
                     latest={'reported_at': '2026-09-24T09:30:00+00:00', 'reviewed': True,
                             'decision': 'propose_action'})
        items = aquarium.project(readings(watch=watch), NOW)['agarens_bord']['items']
        self.assertEqual(items, [{'kind': 'beslut', 'text': 'Ta ställning till förslaget',
                                  'since': '2026-09-24T09:30:00+00:00',
                                  'basis': 'bevakningens förslag'}])
        without = dict(values()['watch'], owner_question='Ta ställning till förslaget')
        self.assertIsNone(aquarium.project(readings(watch=without), NOW)
                          ['agarens_bord']['items'][0]['since'])


class Sockeln(unittest.TestCase):
    def service(self, daemon, engine, worker):
        return {'parts': {'daemon': {'identity_matches': daemon},
                          'engine': {'identity_matches': engine},
                          'worker': {'identity_matches': worker}}}

    def test_service_states(self):
        running = aquarium.project(readings(), NOW)['sockeln']['service']
        self.assertEqual(running, {'state': 'igång', 'verified': 3, 'of': 3, 'config': 'abababab'})
        partly = aquarium.project(readings(service=self.service(True, False, True)),
                                  NOW)['sockeln']['service']
        self.assertEqual((partly['state'], partly['verified']), ('delvis', 2))
        none = aquarium.project(readings(service=self.service(False, False, False)),
                                NOW)['sockeln']['service']
        self.assertEqual((none['state'], none['verified']), ('okänt', 0))

    def test_staffing_is_sorted_by_role(self):
        result = aquarium.project(readings(), NOW)['sockeln']
        self.assertEqual(result['staffing'], [
            {'role': 'granskare', 'executor': 'codex', 'model': 'gpt-5-codex'},
            {'role': 'utvecklare', 'executor': 'claude', 'model': 'claude-opus-5'}])
        self.assertEqual(result['watch_staffing'], {'executor': 'codex', 'model': 'gpt-5-codex'})


class Headline(unittest.TestCase):
    def test_calm_only_when_everything_is_read_and_empty(self):
        result = aquarium.project(readings(), NOW)['headline']
        self.assertEqual(result, {'pagar': 0, 'vantar': 0, 'behover_dig': 0, 'lugnt': True})

    def test_waiting_counts_the_watch_and_the_questions(self):
        watch = dict(values()['watch'], latest={'reported_at': '2026-09-24T09:30:00+00:00',
                                                'reviewed': False, 'decision': 'insufficient'})
        questions = {'items': [{'asked_at': '2026-09-24T09:00:00+00:00', 'executor': 'codex',
                                'model': 'gpt-5-codex', 'still_selected': True}]}
        result = aquarium.project(readings(watch=watch, questions=questions), NOW)['headline']
        self.assertEqual(result, {'pagar': 0, 'vantar': 2, 'behover_dig': 1, 'lugnt': False})

    def test_unknown_is_never_zero(self):
        result = aquarium.project(readings(unavailable=('engine', 'questions')), NOW)['headline']
        self.assertIsNone(result['pagar'])
        self.assertIsNone(result['vantar'])
        self.assertIsNone(result['behover_dig'])
        self.assertIs(result['lugnt'], False)


class DisplaySafety(unittest.TestCase):
    def test_private_looking_values_never_reach_the_view(self):
        office = {'main': '1a' * 20, 'main_date': READ_AT, 'notes': [], 'entries': [
            entry('AP16-LEVERANS-20260919', '/Users/agaren/evidence/ap16/local/hemligt.md',
                  'Privat text som aldrig kopieras i sin helhet.'),
            entry('AP17-BEREDNING-20260918', 'Förslag i .runtime/ap10/rounds',
                  'Ett förslag från agaren@example.com.')],
            'plan_owner_turn': [{'kind': 'beslut',
                                 'text': 'Kör 3f2504e0-4f89-11d3-9a0c-0305e82c3301 i /home/agaren',
                                 'since': None}]}
        watch = dict(values()['watch'], owner_question='Se /private/var/folders/x och evidence/ap10/local')
        result = aquarium.project(readings(office=office, watch=watch), NOW)
        document = json.dumps(result, ensure_ascii=False)
        for forbidden in ('/Users/', '/private/', '/home/', '.runtime', 'evidence/ap10/local',
                          'agaren@example.com', '3f2504e0-4f89-11d3-9a0c-0305e82c3301'):
            self.assertNotIn(forbidden, document)
        self.assertIn(aquarium.HIDDEN, document)

    def test_unlisted_input_keys_are_never_copied(self):
        extra = values()
        extra['office']['entries'] = [dict(entry('AP18-LEVERANS-20260917', 'Med extra'),
                                           hemlig_nyckel='hemligt värde')]
        extra['engine'] = {'executions': [dict(execution('Bygge', ['Steg']), run_id='privat-id')]}
        document = json.dumps(aquarium.project(readings(**extra), NOW), ensure_ascii=False)
        self.assertNotIn('hemlig_nyckel', document)
        self.assertNotIn('hemligt värde', document)
        self.assertNotIn('privat-id', document)


class Collect(unittest.TestCase):
    def probe(self, **overrides):
        parts = {'release': {'ok': True, 'value': values()['release']},
                 'staffing': {'ok': True, 'value': values()['staffing']},
                 'questions': {'ok': True, 'value': values()['questions']},
                 'service': {'ok': True, 'value': values()['service']},
                 'engine': {'ok': True, 'value': values()['engine']},
                 'refusal': {'ok': True, 'value': {'capacity': True}}}
        parts.update(overrides)
        return lambda runtime_root: parts

    def watch(self, **overrides):
        value = {'native': values()['watch']['native'], 'latest': None, 'reviewed': None,
                 'owner_question': None}
        value.update(overrides)
        return lambda runtime_root: value

    def office(self):
        return lambda office_root: values()['office']

    def tasks(self, items=()):
        self.asked = None

        def reader(runtime_root, identities):
            self.asked = list(identities)
            return {'items': list(items)}

        return reader

    def collect(self, **overrides):
        arguments = {'runtime_probe': self.probe(), 'watch_reader': self.watch(),
                     'office_reader': self.office(), 'task_reader': self.tasks()}
        arguments.update(overrides)
        return aquarium.collect('/finns/inte/runtime', '/finns/inte/kontor', **arguments)

    def test_a_full_reading_projects(self):
        result = self.collect()
        self.assertIs(result['provdata'], False)
        self.assertEqual(result['schema'], 2)
        aquarium._aware(result['read_started_at'])
        for name in aquarium.SOURCES:
            self.assertEqual(result['sources'][name]['status'], 'ok', name)
            aquarium._aware(result['sources'][name]['read_at'])
        projection = aquarium.project(result, NOW)
        self.assertEqual(projection['utkiken']['status'], 'ok')
        self.assertEqual(projection['sockeln']['service']['state'], 'igång')

    def test_a_failing_reader_only_makes_its_own_source_unavailable(self):
        def broken(root):
            raise OSError('/Users/agaren/privat')

        result = self.collect(office_reader=broken)
        self.assertEqual(result['sources']['office']['status'], 'unavailable')
        self.assertIsNone(result['sources']['office']['value'])
        aquarium._aware(result['sources']['office']['read_at'])
        self.assertEqual(result['sources']['engine']['status'], 'ok')
        self.assertEqual(result['sources']['watch']['status'], 'ok')

    def test_a_failing_probe_leaves_only_runtime_parts_unavailable(self):
        def broken(root):
            raise RuntimeError('probe')

        reader = self.tasks()
        result = self.collect(runtime_probe=broken, task_reader=reader)
        for name in aquarium.RUNTIME_SOURCES:
            self.assertEqual(result['sources'][name]['status'], 'unavailable', name)
        self.assertEqual(result['sources']['office']['status'], 'ok')
        self.assertIsNone(result['sources']['watch']['value']['refused_for_capacity'])
        self.assertIsNone(self.asked)  # Without the engine no task file is asked for.

    def test_the_task_reader_is_asked_only_for_the_parked_tasks(self):
        executions = [execution('Bygge', ['execute_claude'], task='office-arbetar'),
                      execution('Vilande', task='office-vilar'),
                      execution('Vilande', task='office-vilar'),
                      execution('ServiceIdentity', task='identitet-1'),
                      execution('PrivateAssessment', task='bevakning-1')]
        reader = self.tasks([task_item('office-vilar', title='Vilar')])
        result = self.collect(runtime_probe=self.probe(
            engine={'ok': True, 'value': {'executions': executions}}), task_reader=reader)
        self.assertEqual(self.asked, ['office-vilar'])
        self.assertEqual(result['sources']['tasks']['status'], 'ok')
        self.assertEqual(result['sources']['tasks']['value'],
                         {'items': [{'id': 'office-vilar', 'title': 'Vilar', 'status': 'läst'}]})
        aquarium._aware(result['sources']['tasks']['read_at'])
        projection = aquarium.project(result, NOW)
        self.assertEqual(projection['verkstaden']['parked'][0]['title'], 'Vilar')
        self.assertEqual(projection['verkstaden']['items'][0]['executor'], 'claude')

    def test_a_failing_task_reader_is_only_its_own_source(self):
        def broken(runtime_root, identities):
            raise OSError('/Users/agaren/privat')

        result = self.collect(task_reader=broken)
        self.assertEqual(result['sources']['tasks']['status'], 'unavailable')
        self.assertIsNone(result['sources']['tasks']['value'])
        self.assertEqual(result['sources']['engine']['status'], 'ok')
        self.assertEqual(result['sources']['office']['status'], 'ok')
        malformed = self.collect(task_reader=lambda root, ids: {'items': [{'id': 1}]})
        self.assertEqual(malformed['sources']['tasks']['status'], 'unavailable')

    def test_a_malformed_part_is_only_its_own_source(self):
        result = self.collect(runtime_probe=self.probe(
            engine={'ok': True, 'value': {'executions': 'inte en lista'}},
            staffing={'ok': False}))
        self.assertEqual(result['sources']['engine']['status'], 'unavailable')
        self.assertEqual(result['sources']['staffing']['status'], 'unavailable')
        self.assertEqual(result['sources']['release']['status'], 'ok')

    def test_watch_wrappers_are_reduced_and_checked(self):
        wrapper = {'report': {'reported_at': '2026-09-24T09:30:00+00:00', 'reviewed': True,
                              'reviewed_at': '2026-09-24T09:20:00+00:00', 'decision': 'retain',
                              'run_id': 'privat-körning', 'review_origin': '/Users/agaren/x'},
                   'packet': {}, 'integrity': 'available', 'locator': '/Users/agaren/x'}
        result = self.collect(watch_reader=self.watch(latest=wrapper, reviewed=wrapper,
                                                      owner_question='Ta ställning'))
        value = result['sources']['watch']['value']
        self.assertEqual(value['latest'], {'reported_at': '2026-09-24T09:30:00+00:00',
                                           'reviewed': True, 'decision': 'retain'})
        self.assertEqual(value['reviewed'], {'reviewed_at': '2026-09-24T09:20:00+00:00',
                                             'decision': 'retain'})
        self.assertIs(value['refused_for_capacity'], True)
        self.assertNotIn('privat-körning', json.dumps(value, ensure_ascii=False))

    def test_unavailable_watch_observations(self):
        unavailable = self.collect(watch_reader=self.watch(
            native={'unavailable': True, 'reason': 'invalid_frozen_binding'}))
        self.assertEqual(unavailable['sources']['watch']['status'], 'unavailable')
        damaged = self.collect(watch_reader=self.watch(
            latest={'report': None, 'packet': None, 'integrity': 'unavailable', 'locator': 'x'}))
        self.assertEqual(damaged['sources']['watch']['status'], 'unavailable')


class TaskReader(unittest.TestCase):
    """The default reader, on its own temporary runtime root under the existing `.scratch`."""

    def setUp(self):
        self.assertTrue(SCRATCH.is_dir(), 'the repository keeps an existing .scratch')
        self.temporary = tempfile.TemporaryDirectory(dir=str(SCRATCH))
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.root = self.base / 'runtime'
        (self.root / '.runtime' / 'tasks').mkdir(parents=True)

    def brief(self, identity, raw):
        place = self.root / '.runtime' / 'tasks' / identity
        place.mkdir(parents=True, exist_ok=True)
        (place / 'brief.md').write_bytes(raw)

    def read(self, *identities):
        items = aquarium.task_reader(str(self.root), list(identities))['items']
        return {item['id']: (item['title'], item['status']) for item in items}

    def test_a_title_is_read_and_nothing_else_is_kept(self):
        self.brief('ok-uppdrag',
                   '# En  rubrik\tmed mellanrum \nandra raden med hemligheter\n'.encode('utf-8'))
        result = self.read('ok-uppdrag')
        self.assertEqual(result['ok-uppdrag'], ('En rubrik med mellanrum', 'läst'))
        self.assertNotIn('hemligheter', json.dumps(result, ensure_ascii=False))

    def test_a_carriage_return_and_a_file_without_a_newline(self):
        self.brief('crlf', b'# Rubrik\r\nnasta\r\n')
        self.brief('utan-radslut', b'# Bara en rad')
        result = self.read('crlf', 'utan-radslut')
        self.assertEqual(result['crlf'], ('Rubrik', 'läst'))
        self.assertEqual(result['utan-radslut'], ('Bara en rad', 'läst'))

    def test_a_missing_brief_and_a_missing_task(self):
        (self.root / '.runtime' / 'tasks' / 'tom-katalog').mkdir()
        result = self.read('tom-katalog', 'finns-inte')
        self.assertEqual(result['tom-katalog'], (None, 'saknas'))
        self.assertEqual(result['finns-inte'], (None, 'saknas'))

    def test_symlinks_and_a_directory_are_unreadable(self):
        tasks = self.root / '.runtime' / 'tasks'
        self.brief('riktigt', b'# Riktig rubrik\n')
        (tasks / 'lankad-brief').mkdir()
        (tasks / 'lankad-brief' / 'brief.md').symlink_to(tasks / 'riktigt' / 'brief.md')
        (tasks / 'lankad-katalog').symlink_to(tasks / 'riktigt')
        (tasks / 'katalog-brief' / 'brief.md').mkdir(parents=True)
        result = self.read('lankad-brief', 'lankad-katalog', 'katalog-brief', 'riktigt')
        self.assertEqual(result['lankad-brief'], (None, 'oläslig'))
        self.assertEqual(result['lankad-katalog'], (None, 'oläslig'))
        self.assertEqual(result['katalog-brief'], (None, 'oläslig'))
        self.assertEqual(result['riktigt'], ('Riktig rubrik', 'läst'))

    def test_a_symlinked_component_above_the_task(self):
        other = self.base / 'annat' / 'tasks' / 'uppdrag'
        other.mkdir(parents=True)
        (other / 'brief.md').write_bytes(b'# Genom en lank\n')
        root = self.base / 'lankad-runtime'
        (root / '.runtime').mkdir(parents=True)
        (root / '.runtime' / 'tasks').symlink_to(self.base / 'annat' / 'tasks')
        self.assertEqual(aquarium.task_reader(str(root), ['uppdrag'])['items'],
                         [{'id': 'uppdrag', 'title': None, 'status': 'oläslig'}])

    def test_no_heading_and_broken_utf8(self):
        self.brief('ingen-rubrik', b'Ingen rubrik alls\n')
        self.brief('tom-rubrik', b'#    \nnasta\n')
        self.brief('utan-mellanslag', b'#Rubrik\n')
        self.brief('trasig', b'# \xff\xfe rubrik\n')
        result = self.read('ingen-rubrik', 'tom-rubrik', 'utan-mellanslag', 'trasig')
        for identity, seen in result.items():
            self.assertEqual(seen, (None, 'oläslig'), identity)

    def test_a_long_title_is_shortened(self):
        self.brief('lang', ('# ' + 'a' * 200 + '\n').encode('utf-8'))
        title, status = self.read('lang')['lang']
        self.assertEqual(status, 'läst')
        self.assertEqual(title, 'a' * 119 + '…')
        self.assertEqual(len(title), 120)
        self.brief('jamnt', ('# ' + 'b' * 120 + '\n').encode('utf-8'))
        self.assertEqual(self.read('jamnt')['jamnt'], ('b' * 120, 'läst'))

    def test_an_invalid_id_never_touches_a_file(self):
        self.brief('riktigt', b'# Rubrik\n')
        for identity in ('Stora', '../riktigt', 'med mellanslag', '-bindestreck', '', 'a' * 81,
                         'riktigt/brief.md'):
            self.assertEqual(aquarium.task_reader(str(self.root), [identity])['items'],
                             [{'id': identity, 'title': None, 'status': 'oläslig'}], identity)

    def test_at_most_thirty_two_ids(self):
        items = aquarium.task_reader(str(self.root), ['u%d' % number for number in range(40)])
        self.assertEqual(len(items['items']), 32)
        self.assertEqual(items['items'][0]['id'], 'u0')


class Command(unittest.TestCase):
    def setUp(self):
        self.assertTrue(SCRATCH.is_dir(), 'the repository keeps an existing .scratch')
        self.temporary = tempfile.TemporaryDirectory(dir=str(SCRATCH))
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.original = aquarium.collect
        self.addCleanup(setattr, aquarium, 'collect', self.original)
        aquarium.collect = lambda runtime_root, office_root: readings()

    def test_private_output_is_written_once(self):
        target = self.base / 'projektion'
        self.assertEqual(aquarium.main([str(target)]), 0)
        self.assertEqual(os.stat(target).st_mode & 0o777, 0o700)
        path = target / 'projection.json'
        self.assertEqual(os.stat(path).st_mode & 0o777, 0o600)
        document = path.read_text(encoding='utf-8')
        self.assertTrue(document.endswith('\n'))
        projection = json.loads(document)
        self.assertEqual(document, json.dumps(projection, ensure_ascii=False, indent=1,
                                              sort_keys=True) + '\n')
        self.assertEqual(projection['headline']['lugnt'], True)

    def test_an_existing_directory_is_refused(self):
        target = self.base / 'redan'
        target.mkdir()
        stream = io.StringIO()
        with redirect_stderr(stream):
            self.assertEqual(aquarium.main([str(target)]), 2)
        self.assertEqual(stream.getvalue(), aquarium.COMMAND_ERROR + '\n')
        self.assertEqual(list(target.iterdir()), [])

    def test_a_missing_parent_and_wrong_arguments_are_refused(self):
        for arguments in ([str(self.base / 'saknas' / 'ny')], [], ['a', 'b']):
            stream = io.StringIO()
            with redirect_stderr(stream):
                self.assertEqual(aquarium.main(arguments), 2)
            self.assertEqual(stream.getvalue(), aquarium.COMMAND_ERROR + '\n')

    def test_unavailable_sources_are_not_a_failure(self):
        aquarium.collect = lambda runtime_root, office_root: readings(
            unavailable=aquarium.SOURCES)
        target = self.base / 'tomt'
        self.assertEqual(aquarium.main([str(target)]), 0)
        projection = json.loads((target / 'projection.json').read_text(encoding='utf-8'))
        self.assertEqual(projection['arkivet']['status'], 'otillgänglig')
        self.assertIsNone(projection['headline']['pagar'])


if __name__ == '__main__':
    unittest.main()
