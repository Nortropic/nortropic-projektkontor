"""Synthetic fixtures only, beneath .scratch. No native query or network."""
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import importlib
import importlib.machinery
import importlib.util
import io
import json
import marshal
import os
from pathlib import Path
import socket
import stat
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch, Mock

import agarbild
import bevakningsbild as picture

SCRATCH = Path(__file__).absolute().parents[1] / '.scratch'
GENERATED = '2026-09-21T18:00:00+00:00'


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = picture._canonical(value)
    path.write_bytes(raw)
    return sha256(raw).hexdigest()


def ranges(start, end=None):
    return [dict(start=start, end=start if end is None else end, step=1)]


def native():
    return dict(obligation=picture.OBLIGATION, observed_at='2026-09-21 17:00:00+00:00',
        paused=False, note='', limited_actions=False, remaining_actions=0,
        schedule=dict(calendars=[dict(second=ranges(0), minute=ranges(0), hour=ranges(9),
            day_of_month=ranges(1, 31), month=ranges(1, 12), day_of_week=ranges(0, 6), year=[])],
            cron_expressions=[], time_zone_name='Europe/Stockholm', intervals=[], skip=[]),
        policy=dict(catchup_window='22:00:00'),
        next_action_times=['2026-09-22 07:00:00+00:00'], actions=2,
        missed_catchup=0, skipped_overlap=0, running=[], recent=[], meaning='Synthetic status')


class PictureTests(unittest.TestCase):
    def setUp(self):
        SCRATCH.mkdir(exist_ok=True)
        temporary = tempfile.TemporaryDirectory(dir=SCRATCH)
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)
        self.root = self.base / 'Nortropic Runtime'
        self.office = self.base / 'nortropic-projektkontor'
        self.release = self.root / '.runtime/ap10/releases/synthetic-release'
        self.rounds = self.root / '.runtime/ap10/rounds'
        self.rounds.mkdir(parents=True)
        self.watch = dict(schema=1, case_id='synthetic-case', first_treated_at='2026-01-02T00:00:00Z',
                          old_gaps=['Syntetisk äldre bevislucka.'], source_map={'old': 'source'})
        self.files = {}
        for name, value in {'context/watch.json': self.watch,
                            'context/case.json': {'schema': 1, 'id': 'synthetic-case'}}.items():
            self.files[name] = write(self.release / name, value)
        for name, raw in {'runtime/runtime/obligation.py': b'# synthetic, never executed\n',
                          'context/authority.md': b'Synthetic observation mandate',
                          'context/prior-decision.md': b'Synthetic earlier review'}.items():
            path = self.release / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
            self.files[name] = sha256(raw).hexdigest()
        self.config = dict(host_root=str(self.root), office_root=str(self.office),
            database=str(self.root / '.runtime/runtime.sqlite'), runtime_revision='a' * 40,
            office_revision='b' * 40, files=self.files)
        self.pin()
        self.counter = 0
        self.query = Mock(return_value=native())
        # Every test fails if it accidentally attempts real process or network I/O.
        for target in ('subprocess.run', 'socket.create_connection', 'socket.socket'):
            guard = patch(target, side_effect=AssertionError('External I/O forbidden'))
            guard.start()
            self.addCleanup(guard.stop)

    def pin(self):
        self.config_hash = write(self.release / 'config.json', self.config)
        self.active = dict(config=str(self.release / 'config.json'), sha256=self.config_hash)
        write(self.root / '.runtime/ap10/active.json', self.active)

    def report(self, reviewed=True, decision='retain', complete=True, empty_groups=()):
        self.counter += 1
        home = self.rounds / ('synthetic-run-' + str(self.counter))
        observed = '2026-09-21T%02d:00:00+00:00' % (8 + self.counter)
        reviewed_at = '2026-09-21T%02d:10:00+00:00' % (8 + self.counter)
        reported_at = '2026-09-21T%02d:20:00+00:00' % (8 + self.counter)
        packet = dict(schema=1, observed_at=observed, complete=complete,
            sources=[dict(id='source', status='available', sha256='c' * 64)],
            local=[dict(id='local', status='available', sha256='d' * 64)],
            versions=dict(python='3.12.1', temporalio='1.8.0', runtime_revision='a' * 40,
                          office_revision='b' * 40, active_config_sha256=self.config_hash))
        for group in empty_groups:
            packet[group] = []
        basis = {'versions': packet['versions'], 'sources': packet['sources'], 'local': packet['local']}
        packet['fingerprint'] = picture._hash(picture._canonical(basis)) if complete else None
        packet_hash = write(home / 'intake/data/packet.json', packet)
        proposal = (dict(text='Syntetisk fråga', reason='Syntetiskt skäl', requirement='Syntetiskt krav',
                         observable='Syntetiskt prov', claims=['C1']) if decision == 'propose_action' else None)
        answer = dict(case_id=self.watch['case_id'], packet_sha256=packet_hash, decision=decision,
            vendor='Syntetisk leverantörsuppgift', local='Syntetisk lokal observation',
            judgment='Syntetiskt sakomdöme', authority='Inget ändringsmandat',
            evidence=[record['id'] for group in ('sources', 'local') for record in packet[group]],
            contradictions=[], proposal=proposal)
        review_answer = dict(case_id=self.watch['case_id'], packet_sha256=packet_hash,
            assessment_sha256=picture._hash(picture._canonical(answer)), verdict='approved',
            reason='Syntetisk oberoende granskning', blockers=[])
        review = dict(analysis_thread_id='analysis-thread', review_thread_id='review-thread',
                      assessment_sha256=review_answer['assessment_sha256'])
        for role, value in (('analysis', answer), ('review', review_answer)):
            review[role + '_result_sha256'] = write(home / role / 'result.json', dict(
                completed=True, process_group_removed=True, answer=value,
                provider=dict(valid_terminal=True, thread_id=role + '-thread'), elapsed_seconds=1))
        stamp = datetime.fromisoformat(reviewed_at).timestamp()
        os.utime(home / 'review/result.json', (stamp, stamp))
        draft = (dict(status='draft', mechanical_complete=False,
            gaps=[dict(code='action_authority_missing', subject='brief')],
            package=dict(task_draft={}), private=dict(spec=dict(task={}))) if proposal else None)
        context_hash = picture._hash(picture._canonical({Path(k).name: v for k, v in self.files.items()
                                                        if k.startswith('context/')}))
        report = dict(schema=1, completed=True, obligation=picture.OBLIGATION, run_id=home.name,
            case_id=self.watch['case_id'], packet_sha256=packet_hash, context_sha256=context_hash,
            observed_at=observed, first_treated_at=self.watch['first_treated_at'], reported_at=reported_at,
            reviewed=reviewed, reviewed_at=reviewed_at if reviewed else None,
            decision=decision if reviewed else 'insufficient',
            reasoning={k: answer[k] for k in ('vendor', 'local', 'judgment', 'authority')},
            evidence=answer['evidence'] if reviewed else [], contradictions=[],
            old_gaps=self.watch['old_gaps'], limitations=['Syntetiskt avgränsat urval.'],
            reused_from=None, review_origin=str(home) if reviewed else None, review=review if reviewed else None,
            ap05={}, ap06=draft, action_executed=False, publication=False,
            runtime_revision='a' * 40, office_revision='b' * 40, active_config_sha256=self.config_hash)
        write(home / 'report/result.json', report)
        return home, dict(report=report, packet=packet, integrity='available', locator=str(home / 'report/result.json'))

    def collect(self):
        return picture.collect(self.root, self.query)

    def view(self, latest=None, reviewed=None, status=None, generated=GENERATED):
        return picture.view(native() if status is None else status, latest, reviewed, generated)

    def row(self, result, title):
        return next(w for w in result['work'] if w['title'] == title)

    def test_pure_render_separate_dates_and_no_mutation(self):
        _, wrapper = self.report()
        inputs = [native(), wrapper, wrapper, GENERATED]
        before = deepcopy(inputs)
        with patch.object(picture, 'datetime') as clock:
            clock.fromisoformat = datetime.fromisoformat
            result = picture.view(*inputs)
            clock.now.assert_not_called()
        self.assertEqual(inputs, before)
        self.assertEqual([e['id'] for e in result['evidence']], ['native', 'latest', 'reviewed'])
        html = agarbild.render(result)
        self.assertIn('Inte live eller notifiering', html)
        self.assertEqual(self.row(result, 'Senaste observation')['state'], 'finished')
        self.assertEqual(self.row(result, 'Senaste observation')['observed_at'], wrapper['packet']['observed_at'])
        self.assertEqual(self.row(result, 'Senast granskade besked')['observed_at'], wrapper['report']['reviewed_at'])
        self.assertEqual(result['evidence'][2]['observed_at'], wrapper['report']['reviewed_at'])
        self.assertIn(wrapper['report']['first_treated_at'], html)
        self.assertIn(wrapper['report']['reviewed_at'], html)
        self.assertNotIn('<script', html)

    def test_old_review_never_hides_latest_unreviewed_or_missing_packet(self):
        _, old = self.report()
        _, latest = self.report(reviewed=False)
        for replacement in (latest, None, dict(latest, packet=None), dict(latest, integrity='unavailable')):
            with self.subTest(replacement=replacement):
                result = self.view(replacement, old)
                self.assertIn(self.row(result, 'Senaste observation')['state'], ('waiting', 'unknown'))
                self.assertEqual(self.row(result, 'Senast granskade besked')['state'], 'superseded')
                self.assertEqual(result['owner_decision']['needed'], 'no')

    def test_strict_flags_and_incomplete_packet(self):
        _, wrapper = self.report()
        for value in ('true', 1, None):
            bad = deepcopy(wrapper)
            bad['report']['reviewed'] = value
            self.assertEqual(self.row(self.view(bad), 'Senaste observation')['state'], 'unknown')
        _, incomplete = self.report(decision='insufficient', complete=False)
        self.assertEqual(self.row(self.view(incomplete), 'Senaste observation')['state'], 'waiting')
        for missing in ('sources', 'local', 'versions', 'fingerprint'):
            bad = deepcopy(wrapper)
            del bad['packet'][missing]
            self.assertEqual(self.row(self.view(bad), 'Senaste observation')['state'], 'unknown')

    def test_empty_packet_groups_preserve_documentary_validation(self):
        for groups in (('local',), ('sources',)):
            with self.subTest(empty_groups=groups):
                _, wrapper = self.report(empty_groups=groups)
                result = self.collect()
                self.assertEqual(result['latest'], wrapper)
                self.assertEqual(result['reviewed'], wrapper)
                self.assertEqual(self.row(self.view(wrapper, wrapper),
                                          'Senaste observation')['state'], 'finished')
        _, wrapper = self.report(reviewed=False, empty_groups=('sources', 'local'))
        self.assertEqual(self.collect()['latest'], wrapper)
        self.assertEqual(self.row(self.view(wrapper), 'Senaste observation')['state'], 'waiting')
        _, incomplete = self.report(decision='insufficient', complete=False, empty_groups=('local',))
        self.assertEqual(self.collect()['latest'], incomplete)
        self.assertEqual(self.row(self.view(incomplete), 'Senaste observation')['state'], 'waiting')
        for group in ('sources', 'local'):
            for value in (None, {}, '[]', [None], [dict(id='bad', status='available', sha256='bad')]):
                with self.subTest(group=group, value=value):
                    bad = deepcopy(wrapper)
                    bad['packet'][group] = value
                    self.assertEqual(self.row(self.view(bad), 'Senaste observation')['state'], 'unknown')
        bad = deepcopy(wrapper)
        bad['packet']['fingerprint'] = 'f' * 64
        self.assertEqual(self.row(self.view(bad), 'Senaste observation')['state'], 'unknown')

    def test_cron_exact_empty_forms_with_paused_and_stopped_daily_and_probe(self):
        for cron in ([], '[]', None, '[ ]', 'arbitrary', '0 9 * * *', ['0 9 * * *'], {}, 0):
            for control in ('enabled', 'paused', 'stopped'):
                for probe in (False, True):
                    with self.subTest(cron=cron, control=control, probe=probe):
                        status = native()
                        status['schedule']['cron_expressions'] = cron
                        status['paused'] = control != 'enabled'
                        status['note'] = 'STOPPED by operator' if control == 'stopped' else ''
                        if probe:
                            status['limited_actions'] = True
                            status['schedule']['calendars'][0]['year'] = ranges(2026)
                        row = self.row(self.view(status=status), 'Schema')
                        if cron == [] or cron == '[]':
                            self.assertNotEqual(row['state'], 'unknown')
                            self.assertIn('engångsprov' if probe else 'dygnsschema', row['text'])
                        else:
                            self.assertEqual(row['state'], 'unknown')
                        self.assertIn({'enabled': 'aktiverat', 'paused': 'pausat', 'stopped': 'stoppat'}[control], row['text'])
        status = native()
        del status['schedule']['cron_expressions']
        self.assertEqual(self.row(self.view(status=status), 'Schema')['state'], 'unknown')

    def test_wrong_calendar_old_policy_or_unknown_control(self):
        changes = [lambda n: n['schedule']['calendars'][0].update(hour=ranges(10)),
                   lambda n: n['schedule'].update(time_zone_name='UTC'),
                   lambda n: n['schedule']['calendars'][0].update(year=ranges(2026)),
                   lambda n: n['policy'].update(catchup_window='1 day, 0:00:00'),
                   lambda n: n.update(paused='false')]
        for change in changes:
            status = native()
            change(status)
            self.assertEqual(self.row(self.view(status=status), 'Schema')['state'], 'unknown')

    def test_age_future_invalid_time_and_paused_handling(self):
        _, wrapper = self.report()
        status = native()
        status['paused'] = True
        result = self.view(wrapper, wrapper, status, '2026-09-23T18:00:00Z')
        self.assertIn('inaktuell', agarbild.render(result))
        self.assertIn('Respektera', result['next_action']['text'])
        self.assertNotIn('missad omgång', agarbild.render(result))
        for date in ('2028-01-01T00:00:00Z', 'bad', '2026-09-21T09:00:00'):
            bad = deepcopy(wrapper)
            bad['packet']['observed_at'] = date
            result = self.view(bad)
            self.assertIsNone(self.row(result, 'Senaste observation')['observed_at'])
            agarbild.render(result)

    def test_later_native_start_is_gap_with_real_started_at_and_identity(self):
        _, wrapper = self.report()
        status = native()
        status['recent'] = [dict(scheduled_at='2026-09-21 11:00:00+00:00',
            started_at='2026-09-21 11:01:00+00:00',
            action=dict(workflow_id='other-workflow', first_execution_run_id='other-run'))]
        result = self.view(wrapper, wrapper, status)
        self.assertEqual(self.row(result, 'Aktuell rapportlucka')['state'], 'waiting')
        self.assertEqual(self.row(result, 'Senaste observation')['state'], 'waiting')
        self.assertEqual(self.row(result, 'Senaste observation')['observed_at'], wrapper['packet']['observed_at'])
        self.assertIn('saknar matchande', self.row(result, 'Senaste observation')['text'])
        self.assertEqual(self.row(result, 'Senast granskade besked')['observed_at'], wrapper['report']['reviewed_at'])
        self.assertIn('11:01:00', result['evidence'][0]['text'])
        self.assertIn('other-run', result['evidence'][0]['text'])
        status['recent'][0]['started_at'] = '2026-09-21 08:00:00+00:00'
        status['recent'][0]['action']['first_execution_run_id'] = wrapper['report']['run_id']
        result = self.view(wrapper, wrapper, status)
        self.assertFalse(any(w['title'] == 'Aktuell rapportlucka' for w in result['work']))
        self.assertEqual(self.row(result, 'Senaste observation')['state'], 'finished')
        status['running'] = [dict(workflow_id='new-workflow', first_execution_run_id='new-run')]
        result = self.view(wrapper, wrapper, status)
        self.assertEqual(self.row(result, 'Aktuell rapportlucka')['state'], 'waiting')
        self.assertEqual(self.row(result, 'Senaste observation')['state'], 'waiting')
        self.assertEqual(self.row(result, 'Senaste observation')['observed_at'], wrapper['packet']['observed_at'])

    def test_latest_proposal_remains_pending_when_stale_without_execution_authority(self):
        _, proposed = self.report(decision='propose_action')
        result = self.view(proposed, proposed)
        self.assertEqual(result['owner_decision']['needed'], 'yes')
        self.assertEqual(result['next_action']['authority'], 'proposed')
        result = self.view(proposed, proposed, generated='2026-09-24T00:00:00Z')
        self.assertEqual(result['owner_decision']['needed'], 'yes')
        self.assertEqual(result['next_action']['authority'], 'proposed')
        self.assertIn('inaktuell', self.row(result, 'Senaste observation')['text'])
        self.assertIn('Utred', result['next_action']['text'])
        _, failure = self.report(reviewed=False)
        for latest in (failure, dict(proposed, integrity='unavailable'), dict(proposed, packet=None)):
            result = self.view(latest, proposed)
            self.assertEqual(result['owner_decision']['needed'], 'no')
            self.assertEqual(result['next_action']['authority'], 'none')
        for group, entries in (
            ('running', [dict(workflow_id='new-workflow', first_execution_run_id='new-run')]),
            ('recent', [dict(started_at='2026-09-21 11:01:00+00:00',
                            scheduled_at='2026-09-21 11:00:00+00:00',
                            action=dict(workflow_id='new-workflow', first_execution_run_id='new-run'))])):
            status = native()
            status[group] = entries
            result = self.view(proposed, proposed, status)
            self.assertEqual(result['owner_decision']['needed'], 'no')
            self.assertEqual(result['next_action']['authority'], 'none')

    def draft_forms(self, proposed):
        full = deepcopy(proposed['report']['ap06'])
        full['package'].update(brief='Syntetiskt ogenomfört förslag.',
                               gaps=deepcopy(full['gaps']))
        compact = {key: deepcopy(full[key]) for key in ('status', 'mechanical_complete', 'package')}
        return full, compact

    def test_full_and_compact_ap06_are_unexecuted_owner_questions(self):
        home, proposed = self.report(decision='propose_action')
        full, compact = self.draft_forms(proposed)
        for draft in (full, compact, dict(compact, gaps=deepcopy(full['gaps']))):
            with self.subTest(draft=draft):
                wrapper = deepcopy(proposed)
                wrapper['report']['ap06'] = draft
                write(home / 'report/result.json', wrapper['report'])
                captured = self.collect()
                self.assertEqual(captured['latest'], wrapper)
                self.assertEqual(captured['reviewed'], wrapper)
                for generated in (GENERATED, '2026-09-23T18:00:00Z'):
                    result = picture.view(**captured, generated_at=generated)
                    self.assertEqual(self.row(result, 'Senaste observation')['state'], 'finished')
                    self.assertEqual(result['owner_decision']['needed'], 'yes')
                    self.assertEqual(result['next_action']['authority'], 'proposed')
                    self.assertFalse(captured['latest']['report']['action_executed'])
                    agarbild.render(result)

    def assert_invalid_draft(self, home, proposed, old, draft):
        bad = deepcopy(proposed)
        bad['report']['ap06'] = draft
        write(home / 'report/result.json', bad['report'])
        captured = self.collect()
        self.assertEqual(captured['latest']['integrity'], 'unavailable')
        self.assertEqual(captured['latest']['report'], bad['report'])
        self.assertEqual(captured['reviewed'], old)
        # Exercise the pure API too: a caller's available flag is not validation.
        for result in (self.view(bad, old), picture.view(**captured, generated_at=GENERATED)):
            self.assertEqual(self.row(result, 'Senaste observation')['state'], 'unknown')
            self.assertEqual(self.row(result, 'Senaste observation')['observed_at'],
                             proposed['report']['observed_at'])
            self.assertEqual(self.row(result, 'Senast granskade besked')['state'], 'superseded')
            self.assertEqual(self.row(result, 'Senast granskade besked')['observed_at'],
                             old['report']['reviewed_at'])
            self.assertEqual(result['owner_decision']['needed'], 'no')
            self.assertEqual(result['next_action']['authority'], 'none')
            agarbild.render(result)

    def test_every_present_ap06_gaps_list_is_validated_and_agrees(self):
        _, old = self.report()
        home, proposed = self.report(decision='propose_action')
        for form in self.draft_forms(proposed):
            for location in ('root', 'package'):
                for gaps in (None, {}, [], [None], [42], ['bad'], [{}],
                             [{'code': 'action_authority_missing'}],
                             [{'code': '', 'subject': 'brief'}],
                             [{'code': 'action_authority_missing', 'subject': ''}],
                             [{'code': 'another_gap', 'subject': 'brief'}],
                             form['package']['gaps'] + [None],
                             [{'code': 'action_authority_missing', 'subject': 'different'}]):
                    # A different valid list is only a mismatch when both exist.
                    draft = deepcopy(form)
                    draft['gaps'] = deepcopy(form['package']['gaps'])
                    target = draft if location == 'root' else draft['package']
                    target['gaps'] = gaps
                    with self.subTest(private='private' in form, location=location, gaps=gaps):
                        self.assert_invalid_draft(home, proposed, old, draft)

    def test_compact_ap06_requires_brief_gaps_and_no_executable_task(self):
        _, old = self.report()
        home, proposed = self.report(decision='propose_action')
        full, compact = self.draft_forms(proposed)
        mutations = [lambda d: d['package'].pop('brief'),
                     lambda d: d['package'].update(brief=' '),
                     lambda d: d['package'].update(brief=42),
                     lambda d: d['package'].pop('gaps'),
                     lambda d: d['package'].update(task_draft={'command': 'synthetic'}),
                     lambda d: d.update(private=None),
                     lambda d: d.update(private={}),
                     lambda d: d.update(private={'spec': None}),
                     lambda d: d.update(private={'spec': {'task': {'command': 'synthetic'}}})]
        for mutate in mutations:
            draft = deepcopy(compact)
            mutate(draft)
            with self.subTest(draft=draft):
                self.assert_invalid_draft(home, proposed, old, draft)
        for field in ('package', 'private'):
            draft = deepcopy(full)
            if field == 'package':
                draft['package']['task_draft'] = {'command': 'synthetic'}
            else:
                draft['private']['spec']['task'] = {'command': 'synthetic'}
            with self.subTest(field=field):
                self.assert_invalid_draft(home, proposed, old, draft)

    def test_malformed_ap06_never_finishes_or_creates_owner_question(self):
        _, old = self.report()
        _, proposed = self.report(decision='propose_action')
        draft = proposed['report']['ap06']
        invalid = [None, {}, {'invalid': True},
                   dict(draft, status='accepted'), dict(draft, mechanical_complete=True),
                   dict(draft, package=None), dict(draft, private={'spec': None}),
                   dict(draft, gaps=None), dict(draft, gaps={}), dict(draft, gaps=[]),
                   dict(draft, gaps=[None]), dict(draft, gaps=[42]),
                   dict(draft, gaps=[{}]), dict(draft, gaps=[{'code': 'action_authority_missing'}]),
                   dict(draft, gaps=draft['gaps'] + [None])]
        for ap06 in invalid:
            with self.subTest(ap06=ap06):
                bad = deepcopy(proposed)
                bad['report']['ap06'] = ap06
                result = self.view(bad, old)
                self.assertEqual(self.row(result, 'Senaste observation')['state'], 'unknown')
                self.assertEqual(result['owner_decision']['needed'], 'no')
                self.assertEqual(result['next_action']['authority'], 'none')
                self.assertEqual(self.row(result, 'Senast granskade besked')['state'], 'superseded')
                self.assertEqual(self.row(result, 'Senast granskade besked')['observed_at'],
                                 old['report']['reviewed_at'])
                agarbild.render(result)

    def test_malformed_ap06_collection_preserves_older_evidence(self):
        _, old = self.report()
        home, proposed = self.report(decision='propose_action')
        # The older round is read first; damage must not abort collection.
        for gaps in ([None], [42], ['bad'], [{}],
                     proposed['report']['ap06']['gaps'] + [None]):
            with self.subTest(gaps=gaps):
                bad = deepcopy(proposed['report'])
                bad['ap06']['gaps'] = gaps
                write(home / 'report/result.json', bad)
                result = self.collect()
                self.assertEqual(result['latest']['integrity'], 'unavailable')
                self.assertEqual(result['latest']['report'], bad)
                self.assertEqual(result['reviewed'], old)
                document = picture.view(**result, generated_at=GENERATED)
                self.assertEqual(self.row(document, 'Senaste observation')['state'], 'unknown')
                self.assertEqual(self.row(document, 'Senaste observation')['observed_at'],
                                 bad['observed_at'])
                self.assertEqual(document['owner_decision']['needed'], 'no')
                agarbild.render(document)

    def test_malformed_native_list_entries_are_unknown_preserving_controls(self):
        action = dict(workflow_id='synthetic-workflow', first_execution_run_id='synthetic-run')
        recent = dict(scheduled_at='2026-09-21 07:00:00+00:00',
                      started_at='2026-09-21 07:01:00+00:00', action=action)
        cases = [('next_action_times', ['not-a-time']), ('next_action_times', [None]),
                 ('next_action_times', ['2026-09-22T07:00:00']),
                 ('running', [42]), ('running', [{}]),
                 ('running', [dict(action, first_execution_run_id='')]),
                 ('recent', [42]), ('recent', [{}]),
                 ('recent', [dict(recent, action=None)]),
                 ('recent', [dict(recent, action={'workflow_id': 'synthetic-workflow'})]),
                 ('recent', [dict(recent, scheduled_at='not-a-time')]),
                 ('recent', [dict(recent, started_at='2026-09-21T07:01:00')])]
        for field, entries in cases:
            for control in ('enabled', 'paused', 'stopped'):
                with self.subTest(field=field, entries=entries, control=control):
                    status = native()
                    status[field] = entries
                    status['paused'] = control == 'paused'
                    status['note'] = 'STOPPED by operator' if control == 'stopped' else ''
                    result = self.view(status=status)
                    row = self.row(result, 'Schema')
                    self.assertEqual(row['state'], 'unknown')
                    self.assertIn({'enabled': 'aktiverat', 'paused': 'pausat',
                                   'stopped': 'stoppat'}[control], row['text'])
                    agarbild.render(result)

    def test_valid_native_list_entries_preserve_known_schema(self):
        for control in ('enabled', 'paused', 'stopped'):
            with self.subTest(control=control):
                status = native()
                status['paused'] = control == 'paused'
                status['note'] = 'STOPPED by operator' if control == 'stopped' else ''
                status['running'] = [dict(workflow_id='workflow', first_execution_run_id='run')]
                status['recent'] = [dict(scheduled_at='2026-09-21 07:00:00+00:00',
                                         started_at='2026-09-21T07:01:00Z',
                                         action=status['running'][0])]
                row = self.row(self.view(status=status), 'Schema')
                self.assertEqual(row['state'], 'accepted' if control == 'enabled' else 'waiting')

    def test_collector_binds_fresh_report_and_retains_older_review(self):
        _, old = self.report()
        _, latest = self.report(reviewed=False)
        result = self.collect()
        self.assertEqual(set(result), {'native', 'latest', 'reviewed'})
        self.assertEqual(result['latest'], latest)
        self.assertEqual(result['reviewed'], old)
        root, config = self.query.call_args.args
        self.assertEqual(root, self.root)
        self.assertEqual(config['directory'], str(self.release))
        self.assertEqual(config['config_sha256'], self.config_hash)

    def test_modified_summary_rejected_without_erasing_older_review(self):
        _, old = self.report()
        home, bad = self.report()
        bad['report']['reasoning']['judgment'] = 'Changed after review'
        write(home / 'report/result.json', bad['report'])
        result = self.collect()
        self.assertEqual(result['latest']['integrity'], 'unavailable')
        self.assertEqual(result['reviewed'], old)

    def test_original_review_binding_failures(self):
        home, wrapper = self.report()
        report = wrapper['report']
        path = home / 'review/result.json'
        original = json.loads(path.read_bytes())
        mutations = [lambda r: r.update(completed='true'), lambda r: r.update(process_group_removed=False),
            lambda r: r['provider'].update(valid_terminal=False),
            lambda r: r['provider'].update(thread_id='analysis-thread'),
            lambda r: r['answer'].update(verdict='rejected', blockers=['blocker']),
            lambda r: r['answer'].update(assessment_sha256='f' * 64)]
        for mutate in mutations:
            bad = deepcopy(original)
            mutate(bad)
            changed = deepcopy(report)
            changed['review']['review_result_sha256'] = write(path, bad)
            stamp = datetime.fromisoformat(report['reviewed_at']).timestamp()
            os.utime(path, (stamp, stamp))
            write(home / 'report/result.json', changed)
            self.assertEqual(self.collect()['latest']['integrity'], 'unavailable')

    def reused(self):
        origin, old = self.report()
        home, current = self.report()
        for key in ('review', 'review_origin', 'reviewed_at', 'decision', 'reasoning', 'evidence', 'ap06'):
            current['report'][key] = deepcopy(old['report'][key])
        current['report']['reused_from'] = str(origin)
        write(home / 'report/result.json', current['report'])
        return origin, old, home, current

    def test_reuse_retains_original_date_and_requires_original_bytes(self):
        origin, old, home, current = self.reused()
        collected = self.collect()
        self.assertEqual(collected['latest']['integrity'], 'available')
        self.assertEqual(collected['latest']['report']['reviewed_at'], old['report']['reviewed_at'])
        result = self.view(collected['latest'], collected['reviewed'])
        self.assertIn('Återanvänd granskning', agarbild.render(result))
        self.assertEqual(self.row(result, 'Senast granskade besked')['observed_at'], old['report']['reviewed_at'])
        self.assertEqual(result['evidence'][2]['observed_at'], old['report']['reviewed_at'])
        self.assertEqual(self.row(result, 'Senaste observation')['observed_at'], current['packet']['observed_at'])
        (origin / 'analysis/result.json').write_bytes(b'{}')
        self.assertEqual(self.collect()['latest']['integrity'], 'unavailable')

    def test_reuse_rejects_changed_fingerprint_metadata_and_reused_origin(self):
        origin, old, home, current = self.reused()
        for key, value in (('reviewed_at', current['report']['reported_at']),
                           ('review_origin', str(home)), ('context_sha256', 'f' * 64)):
            changed = deepcopy(current['report'])
            changed[key] = value
            write(home / 'report/result.json', changed)
            self.assertEqual(self.collect()['latest']['integrity'], 'unavailable')
        write(home / 'report/result.json', current['report'])
        older = deepcopy(old['report'])
        older['reused_from'] = str(home)
        write(origin / 'report/result.json', older)
        self.assertEqual(self.collect()['latest']['integrity'], 'unavailable')

    def test_invalid_pin_and_modified_frozen_code_prevent_query(self):
        path = self.release / 'runtime/runtime/obligation.py'
        path.write_bytes(b'changed')
        result = self.collect()
        self.query.assert_not_called()
        self.assertTrue(result['native']['unavailable'])

    def cached_obligation(self):
        source = self.release / 'runtime/runtime/obligation.py'
        info = source.stat()
        code = compile('cached_marker = True\n', str(source), 'exec')
        raw = (importlib.util.MAGIC_NUMBER + struct.pack('<III', 0, int(info.st_mtime), info.st_size)
               + marshal.dumps(code))
        cache = Path(importlib.util.cache_from_source(str(source)))
        cache.parent.mkdir()
        cache.write_bytes(raw)
        return source, cache, raw

    def test_unlisted_matching_bytecode_blocks_query_despite_no_write_flag(self):
        source, cache, _ = self.cached_obligation()
        # Select, but never execute, synthetic cached code under the -B setting.
        loader = importlib.machinery.SourceFileLoader('synthetic_obligation', str(source))
        with patch.object(sys, 'dont_write_bytecode', True):
            self.assertIn('cached_marker', loader.get_code('synthetic_obligation').co_names)
        self.assertTrue(cache.is_file())
        self.assertTrue(self.collect()['native']['unavailable'])
        self.query.assert_not_called()
        with patch.object(picture.subprocess, 'run') as launch:
            self.assertTrue(picture.collect(self.root)['native']['unavailable'])
        launch.assert_not_called()

    def test_cached_bytecode_requires_hash_and_no_symlink_leaf_or_ancestor(self):
        _, cache, raw = self.cached_obligation()
        name = cache.relative_to(self.release).as_posix()
        self.files[name] = sha256(raw).hexdigest()
        self.pin()
        self.assertEqual(self.collect()['native'], native())
        self.query.reset_mock()
        cache.write_bytes(raw + b'changed')
        self.assertTrue(self.collect()['native']['unavailable'])
        self.query.assert_not_called()
        cache.write_bytes(raw)
        outside = self.base / 'outside.pyc'
        cache.rename(outside)
        cache.symlink_to(outside)
        for listed in (True, False):
            with self.subTest(listed=listed):
                if not listed:
                    del self.files[name]
                    self.pin()
                self.assertTrue(self.collect()['native']['unavailable'])
                self.query.assert_not_called()
        cache.unlink()
        cache.write_bytes(raw)
        self.files[name] = sha256(raw).hexdigest()
        self.pin()
        moved = self.base / 'outside-cache'
        cache.parent.rename(moved)
        cache.parent.symlink_to(moved, target_is_directory=True)
        self.assertTrue(self.collect()['native']['unavailable'])
        self.query.assert_not_called()

    def test_other_unlisted_import_artifacts_block_query(self):
        for name in ('__init__.py', 'helper.pyc', 'helper' + importlib.machinery.EXTENSION_SUFFIXES[0]):
            with self.subTest(name=name):
                path = self.release / 'runtime/runtime' / name
                path.write_bytes(b'synthetic unlisted artifact')
                self.assertTrue(self.collect()['native']['unavailable'])
                self.query.assert_not_called()
                path.unlink()

    def test_missing_context_and_malformed_revisions_prevent_query(self):
        for mutate in (lambda c: c['files'].pop('context/watch.json'),
                       lambda c: c.update(runtime_revision='invented'),
                       lambda c: c.update(host_root=str(self.base)),
                       lambda c: c.update(database=str(self.base / 'outside.db'))):
            original = deepcopy(self.config)
            mutate(self.config)
            self.pin()
            self.collect()
            self.query.assert_not_called()
            self.config = original

    def test_exact_root_mapping_without_opening_unused_office(self):
        self.assertFalse(self.office.exists())
        directory = picture._directory
        def checked(path):
            self.assertNotEqual(path, self.office)
            return directory(path)
        with patch.object(picture, '_directory', side_effect=checked):
            self.assertEqual(self.collect()['native'], native())
        self.query.assert_called_once()

    def test_other_office_and_database_mappings_prevent_query(self):
        # A real sibling directory must not qualify merely by being accessible.
        (self.base / 'Office').mkdir()
        for key, path in (
            ('office_root', self.base / 'Office'),
            ('office_root', self.root),
            ('office_root', self.base / 'elsewhere/nortropic-projektkontor'),
            ('database', self.root / '.runtime/temporal.db'),
            ('database', self.root / '.runtime/other.sqlite'),
            ('database', self.root / '.runtime/subdir/runtime.sqlite')):
            with self.subTest(key=key, path=path):
                original = self.config[key]
                self.config[key] = str(path)
                self.pin()
                self.assertTrue(self.collect()['native']['unavailable'])
                self.query.assert_not_called()
                self.config[key] = original

    def test_active_change_invalidates_native_but_preserves_report(self):
        _, wrapper = self.report()
        def changed(root, config):
            write(root / '.runtime/ap10/active.json', dict(self.active, sha256='f' * 64))
            return native()
        self.query.side_effect = changed
        result = self.collect()
        self.assertTrue(result['native']['unavailable'])
        self.assertEqual(result['reviewed'], wrapper)

    def test_status_failures_preserve_readable_history_and_hide_error_contents(self):
        _, wrapper = self.report()
        for error in (TimeoutError('private token'), subprocess.TimeoutExpired('private command', 20),
                      ValueError('private body')):
            self.query.side_effect = error
            result = self.collect()
            self.assertEqual(result['reviewed'], wrapper)
            self.assertTrue(result['native']['unavailable'])
            self.assertNotIn('private', json.dumps(result['native']))

    def test_symlink_frozen_ancestor_and_report_leaf_are_rejected(self):
        home, _ = self.report()
        target = home / 'report/result.json'
        copy = self.base / 'copy.json'
        target.rename(copy)
        target.symlink_to(copy)
        self.assertEqual(self.collect()['latest']['integrity'], 'unavailable')
        self.query.reset_mock()
        code = self.release / 'runtime'
        moved = self.base / 'moved-runtime'
        code.rename(moved)
        code.symlink_to(moved, target_is_directory=True)
        self.assertTrue(self.collect()['native']['unavailable'])
        self.query.assert_not_called()

    def test_strict_json_and_nonregular_files(self):
        for raw in (b'{"config":1,"config":2}', b'{"x":NaN}', b'{"x":1e999}'):
            (self.root / '.runtime/ap10/active.json').write_bytes(raw)
            self.assertTrue(self.collect()['native']['unavailable'])
            self.query.assert_not_called()
        self.pin()
        home, _ = self.report()
        path = home / 'report/result.json'
        path.unlink()
        os.mkfifo(path)
        self.assertEqual(self.collect()['latest']['integrity'], 'unavailable')

    def test_read_limits_make_latest_unavailable_without_erasing_review(self):
        self.report()
        self.report()
        with patch.object(picture, 'ROUND_LIMIT', 1):
            result = self.collect()
            self.assertEqual(result['latest']['integrity'], 'unavailable')
            self.assertIsNotNone(result['reviewed'])
        with patch.object(picture, 'CODE_LIMIT', 1):
            self.query.reset_mock()
            self.assertTrue(self.collect()['native']['unavailable'])
            self.query.assert_not_called()
        home, _ = self.report()
        path = home / 'report/result.json'
        with path.open('wb') as stream:
            stream.truncate(picture.JSON_LIMIT + 1)
        self.assertEqual(self.collect()['latest']['integrity'], 'unavailable')

    def assert_incomplete_history(self, result, reviewed):
        self.assertEqual(set(result), {'native', 'latest', 'reviewed'})
        self.assertEqual(result['latest']['integrity'], 'unavailable')
        self.assertIn('Ofullständig läsning: gräns', result['latest']['locator'])
        self.assertEqual(result['reviewed'], reviewed)
        document = picture.view(**result, generated_at=GENERATED)
        self.assertEqual(self.row(document, 'Senaste observation')['state'], 'unknown')
        self.assertEqual(self.row(document, 'Senast granskade besked')['state'], 'superseded')
        self.assertEqual(document['owner_decision']['needed'], 'no')
        self.assertIn('Ofullständig läsning: gräns', agarbild.render(document))

    def test_oversized_older_documents_cannot_be_hidden_by_newer_valid_report(self):
        home, _ = self.report()
        _, newer = self.report(decision='propose_action')
        for name in ('report/result.json', 'intake/data/packet.json',
                     'analysis/result.json', 'review/result.json'):
            with self.subTest(name=name):
                path = home / name
                raw, info = path.read_bytes(), path.stat()
                with path.open('wb') as stream:
                    stream.truncate(picture.JSON_LIMIT + 1)
                self.assert_incomplete_history(self.collect(), newer)
                path.write_bytes(raw)
                os.utime(path, ns=(info.st_atime_ns, info.st_mtime_ns))

    def test_total_document_budget_failure_is_sticky_and_retains_readable_history(self):
        old_home, old = self.report()
        home, _ = self.report()
        newer_home, newer = self.report(decision='propose_action')
        pin_size = sum(path.stat().st_size for path in
                       (self.root / '.runtime/ap10/active.json', self.release / 'config.json')) * 2
        pin_size += (self.release / 'context/watch.json').stat().st_size
        old_size = sum(path.stat().st_size for path in old_home.rglob('*.json'))
        order = ('report/result.json', 'intake/data/packet.json',
                 'analysis/result.json', 'review/result.json')
        newer_size = sum(path.stat().st_size for path in newer_home.rglob('*.json'))
        for name in order[1:]:
            path = home / name
            raw, info = path.read_bytes(), path.stat()
            path.write_bytes(raw + b' ' * 65536)
            consumed = sum((home / preceding).stat().st_size for preceding in order[:order.index(name)])
            for allowance, history in ((consumed, old), (consumed + newer_size, newer)):
                with self.subTest(name=name, allowance=allowance):
                    with patch.object(picture, 'DOCUMENT_LIMIT', pin_size + old_size + allowance):
                        self.assert_incomplete_history(self.collect(), history)
            path.write_bytes(raw)
            os.utime(path, ns=(info.st_atime_ns, info.st_mtime_ns))

    def test_exact_subprocess_contract_and_environment_no_real_launch(self):
        (self.root / '.runtime/temporal-venv/bin').mkdir(parents=True)
        with patch.object(picture.subprocess, 'run', return_value=Mock(returncode=0, stdout=json.dumps(native()))) as run:
            with patch.dict(os.environ, {'PYTHONPATH': '/evil', 'PYTHONHOME': '/evil',
                                        'NR_HOST_ROOT': '/evil', 'NR_SECRET': 'secret'}):
                result = picture.collect(self.root)
        self.assertNotIn('unavailable', result['native'])
        args, kwargs = run.call_args
        self.assertEqual(args[0], [str(self.root / '.runtime/temporal-venv/bin/python'), '-B', '-m',
                                  'runtime.obligation', 'status'])
        self.assertEqual(kwargs['cwd'], str(self.release / 'runtime'))
        self.assertEqual(kwargs['timeout'], 20)
        self.assertFalse(kwargs['shell'])
        self.assertTrue(kwargs['capture_output'])
        self.assertTrue(kwargs['text'])
        self.assertFalse({'PYTHONPATH', 'PYTHONHOME', 'NR_SECRET'} & kwargs['env'].keys())
        self.assertEqual(kwargs['env']['NR_CONFIG_SHA256'], self.config_hash)

    def test_cli_private_files_rejects_existing_and_symlink_before_collection(self):
        output = self.base / 'picture'
        with patch.object(picture, 'collect', return_value=dict(native=native(), latest=None, reviewed=None)) as collect:
            self.assertEqual(picture.main([str(output)]), 0)
            self.assertEqual({p.name for p in output.iterdir()}, {'input.json', 'index.html'})
            self.assertEqual(stat.S_IMODE(output.stat().st_mode), 0o700)
            for path in output.iterdir():
                self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
            before = (output / 'index.html').read_bytes()
            collect.reset_mock()
            with patch('sys.stderr', new_callable=io.StringIO):
                self.assertEqual(picture.main([str(output)]), 2)
                alias = self.base / 'alias'
                alias.symlink_to(output, target_is_directory=True)
                self.assertEqual(picture.main([str(alias / 'new')]), 2)
                self.assertEqual(picture.main([]), 2)
                self.assertEqual(picture.main([str(output), 'extra']), 2)
            collect.assert_not_called()
            self.assertEqual((output / 'index.html').read_bytes(), before)

    def test_import_is_inert(self):
        with patch('os.open', side_effect=AssertionError('Import I/O')):
            importlib.reload(picture)

    def test_actual_bevakning_protocol_with_synthetic_intake(self):
        import test_bevakning
        fixture = test_bevakning.PolicyTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        for name in ('case.json', 'watch.json', 'authority.md', 'prior-decision.md'):
            raw = (fixture.context / name).read_bytes()
            (self.release / 'context' / name).write_bytes(raw)
            self.files['context/' + name] = sha256(raw).hexdigest()
        self.watch = deepcopy(fixture.watch)
        self.pin()
        fixture.base = self.rounds
        fixture.fixture.versions.update(runtime_revision='a' * 40, office_revision='b' * 40,
                                        active_config_sha256=self.config_hash)
        fixture.config.update(runtime_revision='a' * 40, office_revision='b' * 40,
                              config_sha256=self.config_hash)
        fixture.request.update(run_id='round-1', config_sha256=self.config_hash)
        _, prior = fixture.approved()
        result = self.collect()
        self.assertEqual(result['latest']['integrity'], 'available')
        self.assertEqual(result['latest']['report'], prior['report'])
        agarbild.render(picture.view(**result, generated_at=datetime.now(timezone.utc).isoformat()))

    def test_document_budget_and_duplicate_report_are_not_silent_absence(self):
        _, old = self.report()
        home, _ = self.report()
        path = home / 'report/result.json'
        path.write_bytes(b'{"observed_at":"2026-09-21T15:00:00Z","reviewed":true,"reviewed":false}')
        result = self.collect()
        self.assertEqual(result['latest']['integrity'], 'unavailable')
        self.assertEqual(result['reviewed'], old)
        # Account for the pin reads and recheck, then exhaust during round reads.
        pin_size = sum(len(p.read_bytes()) for p in
                       (self.root / '.runtime/ap10/active.json', self.release / 'config.json')) * 2
        with patch.object(picture, 'DOCUMENT_LIMIT', pin_size + 10):
            result = self.collect()
            self.assertEqual(result['latest']['integrity'], 'unavailable')

    def test_query_invalid_json_nonzero_and_timeout_have_fixed_diagnosis(self):
        (self.root / '.runtime/temporal-venv/bin').mkdir(parents=True)
        _, old = self.report()
        for outcome in (Mock(returncode=1, stdout='private error'),
                        Mock(returncode=0, stdout='not json'),
                        Mock(returncode=0, stdout='{"x":NaN}'),
                        subprocess.TimeoutExpired('private', 20)):
            kwargs = {'side_effect': outcome} if isinstance(outcome, Exception) else {'return_value': outcome}
            with patch.object(picture.subprocess, 'run', **kwargs):
                result = picture.collect(self.root)
            self.assertTrue(result['native']['unavailable'])
            self.assertEqual(result['reviewed'], old)
            self.assertNotIn('private', json.dumps(result['native']))

    def test_previous_frozen_revision_remains_readable_dated_history(self):
        _, old = self.report()
        self.config['runtime_revision'] = 'e' * 40
        self.pin()
        result = self.collect()
        self.assertEqual(result['reviewed'], old)
        self.assertNotEqual(result['reviewed']['report']['active_config_sha256'], self.config_hash)

    def test_missing_native_counts_are_unknown_and_pause_is_preserved(self):
        status = native()
        status['paused'] = True
        del status['missed_catchup']
        row = self.row(self.view(status=status), 'Schema')
        self.assertEqual(row['state'], 'unknown')
        self.assertIn('pausat', row['text'])


if __name__ == '__main__':
    unittest.main()
