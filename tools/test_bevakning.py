"""Synthetic policy tests. Every artifact is isolated beneath .scratch."""
from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
import stat
import unittest
from unittest.mock import patch

import bevakning as policy
import bevakningsunderlag as intake
import test_bevakningsunderlag as intake_tests


def write(path, value):
    path.write_bytes(policy._canonical(value))


class PolicyTests(unittest.TestCase):
    def setUp(self):
        self.fixture = intake_tests.CollectionTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.base = self.fixture.base
        self.context = self.base / 'context'
        self.context.mkdir()
        raw = self.fixture.responses[intake._python_url('3.12.1')]
        local = (self.fixture.roots['active'] / intake.LOCAL_FILES[0]).read_bytes()
        sources = [dict(id=identity, title='Synthetic source', version='baseline',
                        path='baseline/' + identity, sha256=sha256(data).hexdigest(), size=len(data))
                   for identity, data in (('vendor', raw), ('local', local), ('historic', b'old'))]
        self.case = dict(schema=1, id='synthetic-case', created_at='2026-01-01T00:00:00Z',
            sources=sources, claims=[dict(id='C1', kind='decision', text='Retain scoped use',
            reason='Synthetic qualified scope', standing='Historical decision', sources=['vendor', 'local'])],
            actions=[dict(id='A1', text='Keep existing scope', reason='Synthetic disposition', claims=['C1'],
            authority=dict(status='granted', scope='Scoped observation only', sources=['historic']))], next_action='A1')
        self.watch = dict(schema=1, case_id=self.case['id'], first_treated_at='2026-01-02T00:00:00Z',
            old_gaps=['Stronger graceful-drain guarantee remains unproved.'],
            source_map={'vendor': 'python-3.12.1', 'local': 'active:runtime/worker.py', 'historic': None})
        write(self.context / 'case.json', self.case)
        write(self.context / 'watch.json', self.watch)
        (self.context / 'authority.md').write_text('Synthetic current AP10: observation only; no upgrade authority.')
        (self.context / 'prior-decision.md').write_text('Synthetic reviewed AP09: retain scoped use, stronger drain gap stays.')
        self.counter = 0
        self.config = dict(runtime_revision=self.fixture.versions['runtime_revision'],
                           office_revision=self.fixture.versions['office_revision'],
                           config_sha256=self.fixture.versions['active_config_sha256'], directory='unused', files=[])
        self.request = dict(run_id='synthetic-run', workflow_id='synthetic-workflow',
            started_at='2026-01-02T00:00:00Z', obligation=policy.OBLIGATION,
            config_sha256=self.config['config_sha256'], role='report', seconds=60,
            outcomes={'analysis': 'success', 'review': 'success'})

    def round(self, prior=None):
        self.counter += 1
        home = self.base / ('round-' + str(self.counter))
        home.mkdir()
        for name in ('intake', 'analysis', 'review', 'report'):
            (home / name).mkdir()
        if prior is not None:
            write(home / 'intake' / 'previous.json', prior)
        with patch.object(intake, 'fetch', side_effect=self.fixture.fetcher), \
             patch.object(intake, 'collect', wraps=intake.collect) as collect:
            result = policy.prepare(home / 'intake' / 'data', self.fixture.roots,
                                    self.fixture.versions, prior, self.context)
            self.assertEqual(collect.call_count, 1)
        write(home / 'intake' / 'result.json', result)
        return home, result

    def answer(self, home, decision='retain'):
        packet_hash = sha256((home / 'intake/data/packet.json').read_bytes()).hexdigest()
        return dict(case_id=self.case['id'], packet_sha256=packet_hash, decision=decision,
                    vendor='Synthetic release claim within scope.',
                    local='Synthetic active use differs from working only when observed.',
                    judgment='Retain qualified scoped use; stronger historical gap stays.',
                    authority='Observation only; no change authorization.',
                    evidence=['python-3.12.1', 'active:runtime/worker.py'], contradictions=[], proposal=None)

    def stages(self, home, answer=None):
        answer = self.answer(home) if answer is None else answer
        review = dict(case_id=answer['case_id'], packet_sha256=answer['packet_sha256'],
                      assessment_sha256=sha256(policy._canonical(answer)).hexdigest(),
                      verdict='approved', reason='Synthetic independent source examination.', blockers=[])
        for role, value in (('analysis', answer), ('review', review)):
            write(home / role / 'result.json', dict(completed=True, answer=value,
                provider=dict(valid_terminal=True, thread_id=role + '-thread', usage={}),
                elapsed_seconds=1.0, process_group_removed=True))
        return answer

    def finish(self, home):
        return policy.finish(home, self.request, self.config)

    def prior(self, home, report=None):
        report = self.finish(home) if report is None else report
        write(home / 'report/result.json', report)  # Synthetic Runtime final writer.
        return dict(home=str(home), report=report,
                    packet=json.loads((home / 'intake/data/packet.json').read_bytes()))

    def approved(self):
        home, _ = self.round()
        self.stages(home)
        return home, self.prior(home)

    def mutate(self, home, relative, transform):
        path = home / relative
        value = json.loads(path.read_bytes())
        transform(value)
        write(path, value)

    def test_fresh_report_ap05_time_scope_and_no_final_write(self):
        home, status = self.round()
        self.assertEqual(status, dict(completed=True, needs_model=True, reason=policy.FRESH))
        answer = self.stages(home)
        before = {p: p.read_bytes() for p in home.rglob('*') if p.is_file()}
        report = self.finish(home)
        self.assertTrue(report['reviewed'])
        self.assertEqual(report['reasoning'], {k: answer[k] for k in ('vendor', 'local', 'judgment', 'authority')})
        self.assertEqual(report['first_treated_at'], self.watch['first_treated_at'])
        self.assertEqual(report['old_gaps'], self.watch['old_gaps'])
        self.assertEqual(report['review_origin'], str(home))
        self.assertEqual(report['ap05']['source_checks'], [dict(id='vendor', status='ok'),
            dict(id='local', status='ok'), dict(id='historic', status='not_checked')])
        self.assertFalse(report['action_executed'])
        self.assertFalse(report['publication'])
        self.assertIsNone(report['ap06'])
        self.assertFalse((home / 'report/result.json').exists())
        self.finish(home)
        self.assertEqual(before, {p: p.read_bytes() for p in home.rglob('*') if p.is_file()})
        self.assertAlmostEqual(policy._time(report['reviewed_at']).timestamp(),
                               (home / 'review/result.json').stat().st_mtime, places=5)

    def test_unchanged_reuse_chain_preserves_original_review(self):
        origin, prior = self.approved()
        initial = deepcopy(prior['report'])
        for _ in range(3):
            home, status = self.round(prior)
            self.assertFalse(status['needs_model'])
            report = self.finish(home)
            self.assertTrue(report['reviewed'])
            for field in ('review', 'review_origin', 'reviewed_at', 'reasoning', 'first_treated_at'):
                self.assertEqual(report[field], initial[field])
            self.assertEqual(report['reused_from'], prior['home'])
            self.assertNotEqual(report['packet_sha256'], prior['report']['packet_sha256'])
            self.assertNotEqual(report['observed_at'], prior['report']['observed_at'])
            self.assertEqual(report['ap05']['checked_at'], report['observed_at'])
            prior = self.prior(home, report)
        self.assertEqual(prior['report']['review_origin'], str(origin))

    def test_optional_usage_for_fresh_review_workspace_and_reuse(self):
        for usage in (None, 'absent'):
            with self.subTest(usage=usage):
                home, _ = self.round()
                self.stages(home)
                for role in ('analysis', 'review'):
                    def change(result):
                        if usage == 'absent':
                            result['provider'].pop('usage')
                        else:
                            result['provider']['usage'] = usage
                    self.mutate(home, role + '/result.json', change)
                dest = self.base / ('review-workspace-' + str(self.counter))
                dest.mkdir()
                policy.workspace(dest, home, self.context, 'review')
                prior = self.prior(home)
                self.assertTrue(prior['report']['reviewed'])
                current, status = self.round(prior)
                self.assertFalse(status['needs_model'])
                self.assertTrue(self.finish(current)['reviewed'])
                # Optional metrics never relax success, cleanup or independence.
                self.mutate(home, 'review/result.json',
                            lambda r: r['provider'].update(thread_id='analysis-thread'))
                self.assertFalse(self.finish(home)['reviewed'])
                self.assertFalse(self.finish(current)['reviewed'])

    def test_damaged_prior_intake_status_requires_fresh_assessment(self):
        home, prior = self.approved()
        path = home / 'intake/result.json'
        original = path.read_bytes()
        for value in (None, dict(completed=False, needs_model=True, reason=policy.FRESH),
                      dict(completed=1, needs_model=True, reason=policy.FRESH)):
            with self.subTest(value=value):
                if value is None:
                    path.unlink()
                else:
                    write(path, value)
                self.assertTrue(self.round(prior)[1]['needs_model'])
                path.write_bytes(original)

    def test_external_only_local_only_and_context_change_require_model(self):
        _, prior = self.approved()
        url = intake._python_url('3.12.1')
        old = self.fixture.responses[url]
        self.fixture.responses[url] += b'<p>new release statement</p>'
        home, status = self.round(prior)
        self.assertTrue(status['needs_model'])
        self.assertEqual(policy._bundle(home)['ap05']['source_checks'][0]['status'], 'changed')
        self.fixture.responses[url] = old
        path = self.fixture.roots['working'] / intake.LOCAL_FILES[0]
        old_local = path.read_bytes()
        path.write_bytes(b'changed working use')
        self.assertTrue(self.round(prior)[1]['needs_model'])
        path.write_bytes(old_local)
        (self.context / 'authority.md').write_text('Synthetic revised selected authority')
        self.assertTrue(self.round(prior)[1]['needs_model'])

    def test_unavailable_intake_requires_insufficient_but_can_be_reviewed(self):
        _, prior = self.approved()
        self.fixture.responses[intake._python_url('3.12.1')] = OSError('synthetic unavailable')
        home, status = self.round(prior)
        self.assertTrue(status['completed'])
        self.assertTrue(status['needs_model'])
        answer = self.answer(home)
        self.stages(home, answer)
        self.assertFalse(self.finish(home)['reviewed'])
        answer['decision'] = 'insufficient'
        self.stages(home, answer)
        report = self.finish(home)
        self.assertTrue(report['reviewed'])
        self.assertEqual(report['ap05']['source_checks'][0]['status'], 'missing')
        self.assertTrue(self.round(self.prior(home, report))[1]['needs_model'])

    def test_missing_rejected_failed_same_thread_and_tampered_review(self):
        home, _ = self.round()
        self.stages(home)
        valid = {role: (home / role / 'result.json').read_bytes() for role in ('analysis', 'review')}
        mutations = [
            ('review', lambda r: r['answer'].update(verdict='rejected', blockers=['Wrong applicability'])),
            ('review', lambda r: r['provider'].update(thread_id='analysis-thread')),
            ('analysis', lambda r: r.update(completed=1)),
            ('review', lambda r: r['provider'].update(valid_terminal=1)),
            ('analysis', lambda r: r.update(process_group_removed=False)),
            ('review', lambda r: r['answer'].update(assessment_sha256='0' * 64)),
            ('analysis', lambda r: r['answer'].update(judgment='tampered')),
            ('analysis', lambda r: r['answer'].update(evidence=['unknown-record'])),
            ('analysis', lambda r: r['answer'].update(evidence=['python-3.12.1'] * 2)),
            ('analysis', lambda r: r['answer'].update(contradictions=['unresolved'])),
            ('analysis', lambda r: r['answer'].update(extra='not allowed')),
            ('review', lambda r: r['answer'].update(packet_sha256='f' * 64)),
            ('review', lambda r: r['answer'].update(blockers=['Unresolved blocker'])),
        ]
        for role, mutate in mutations:
            with self.subTest(role=role, mutation=mutate):
                for name, raw in valid.items():
                    (home / name / 'result.json').write_bytes(raw)
                self.mutate(home, role + '/result.json', mutate)
                report = self.finish(home)
                self.assertFalse(report['reviewed'])
                self.assertEqual(report['decision'], 'insufficient')
                for field in ('review', 'reviewed_at', 'review_origin'):
                    self.assertIsNone(report[field])
                self.assertEqual(report['old_gaps'], self.watch['old_gaps'])
        for role in ('analysis', 'review'):
            for name, raw in valid.items():
                (home / name / 'result.json').write_bytes(raw)
            (home / role / 'result.json').unlink()
            self.assertFalse(self.finish(home)['reviewed'])

    def test_invalid_obligation_and_each_config_binding(self):
        home, _ = self.round()
        self.stages(home)
        for target, field in ((self.request, 'obligation'), (self.request, 'config_sha256'),
                              (self.config, 'runtime_revision'), (self.config, 'office_revision'),
                              (self.config, 'config_sha256')):
            original = target[field]
            target[field] = 'wrong'
            self.assertFalse(self.finish(home)['reviewed'])
            target[field] = original

    def test_prior_mismatches_bare_flag_damaged_evidence_and_cycle(self):
        origin, prior = self.approved()
        bad = deepcopy(prior)
        bad['report']['reviewed'] = 1
        self.assertTrue(self.round(bad)[1]['needs_model'])
        bad = deepcopy(prior)
        bad['packet']['complete'] = 1
        self.assertTrue(self.round(bad)[1]['needs_model'])
        for field in ('report', 'packet'):
            bad = deepcopy(prior)
            bad[field]['extra'] = 'tampered'
            self.assertTrue(self.round(bad)[1]['needs_model'])
        for mutate in (lambda r: r.update(reviewed=False),
                       lambda r: r.update(decision='insufficient'),
                       lambda r: r.update(packet_sha256='f' * 64),
                       lambda r: r.update(review_origin='wrong')):
            bad = deepcopy(prior)
            mutate(bad['report'])
            write(origin / 'report/result.json', bad['report'])
            self.assertTrue(self.round(bad)[1]['needs_model'])
        write(origin / 'report/result.json', prior['report'])
        self.mutate(origin, 'analysis/result.json', lambda r: r['answer'].update(judgment='later tamper'))
        self.assertTrue(self.round(prior)[1]['needs_model'])
        self.stages(origin)
        # Rebuild the legitimate original evidence hashes after synthetic replacement.
        prior = self.prior(origin)
        home, _ = self.round(prior)
        previous = self.prior(home)
        self.mutate(home, 'intake/data/prepared.json', lambda p: p.update(reused_from=str(home)))
        previous['report']['reused_from'] = str(home)
        write(home / 'report/result.json', previous['report'])
        self.assertTrue(self.round(previous)[1]['needs_model'])

    def test_reuse_rechecked_at_finish_not_trusted_from_prepare(self):
        origin, prior = self.approved()
        home, result = self.round(prior)
        self.assertFalse(result['needs_model'])
        (origin / 'review/result.json').unlink()
        report = self.finish(home)
        self.assertFalse(report['reviewed'])
        self.assertEqual(report['decision'], 'insufficient')

    def test_proposal_ap06_gaps_original_case_and_exclusive_artifact(self):
        home, _ = self.round()
        answer = self.answer(home, 'propose_action')
        answer['proposal'] = dict(text='Consider an upgrade outside current mandate',
            reason='Synthetic changed supplier scope', requirement='Preserve scoped behavior',
            observable='Scoped behavior is observed under the proposed release', claims=['C1'])
        self.stages(home, answer)
        original = (self.context / 'case.json').read_bytes()
        report = self.finish(home)
        self.assertTrue(report['reviewed'])
        draft = report['ap06']
        self.assertFalse(draft['mechanical_complete'])
        gaps = {g['code'] for g in draft['gaps']}
        self.assertTrue({'action_authority_missing', 'task_field_missing', 'requirement_references_empty'} <= gaps)
        case = draft['private']['case']
        self.assertEqual(case['sources'], self.case['sources'])
        self.assertEqual(case['claims'], self.case['claims'])
        self.assertEqual(case['actions'][:-1], self.case['actions'])
        self.assertEqual(case['actions'][-1]['authority'], dict(status='not_granted',
            scope='Separate action-specific owner mandate required', sources=[]))
        self.assertEqual(draft['private']['spec']['task'], {})
        self.assertEqual(draft['private']['spec']['references'], [])
        self.assertEqual(draft['private']['check'], policy._bundle(home)['check'])
        self.assertEqual((self.context / 'case.json').read_bytes(), original)
        artifact = (home / 'report/ap06.json').read_bytes()
        with self.assertRaises(ValueError):
            self.finish(home)
        self.assertEqual((home / 'report/ap06.json').read_bytes(), artifact)
        prior = self.prior(home, report)
        reused_home, status = self.round(prior)
        self.assertFalse(status['needs_model'])
        with patch.object(assignment := policy.assignment_preparation, 'prepare', wraps=assignment.prepare) as prep:
            reused = self.finish(reused_home)
        prep.assert_not_called()
        self.assertTrue(reused['reviewed'])
        self.assertEqual(reused['ap06'], draft)
        self.assertFalse((reused_home / 'report/ap06.json').exists())

    def test_workspace_selected_payloads_permissions_exact_review_answer(self):
        home, _ = self.round()
        answer = self.stages(home)
        (self.context / 'unselected.txt').write_text('Synthetic unrelated context')
        (home / 'analysis/credentials.json').write_text('Synthetic forbidden extra')
        before = {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in home.rglob('*') if p.is_file()}
        for role in ('analysis', 'review'):
            dest = self.base / ('workspace-' + role)
            dest.mkdir()
            policy.workspace(dest, home, self.context, role)
            info = json.loads((dest / 'INPUT.json').read_bytes())
            expected_names = set(policy.CONTEXT) | {'INPUT.json', 'packet.json', 'prepared.json', 'ap05.json', 'data'}
            if role == 'review':
                expected_names.add('assessment.json')
            self.assertEqual({p.name for p in dest.iterdir()}, expected_names)
            self.assertEqual(info['omitted_ids'], ['python-index', 'temporal-index'])
            self.assertNotIn('python-index', info['records'])
            self.assertEqual(info['old_gaps'], self.watch['old_gaps'])
            for identifier, relative in info['records'].items():
                self.assertTrue(relative.startswith('data/payload-') and relative.endswith('.txt'))
                self.assertEqual((dest / relative).read_bytes(), policy._bundle(home)['payloads'][identifier])
            for path in [dest, *dest.rglob('*')]:
                self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o700 if path.is_dir() else 0o600)
            self.assertEqual((dest / 'assessment.json').exists(), role == 'review')
            if role == 'review':
                self.assertEqual((dest / 'assessment.json').read_bytes(), policy._canonical(answer))
                self.assertEqual(info['assessment_sha256'], sha256(policy._canonical(answer)).hexdigest())
            with self.assertRaises(ValueError):
                policy.workspace(dest, home, self.context, role)
        self.assertEqual(before, {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in home.rglob('*') if p.is_file()})

    def test_reuse_rejects_corrupted_ap06_gaps_and_export(self):
        home, _ = self.round()
        answer = self.answer(home, 'propose_action')
        answer['proposal'] = dict(text='Consider a scoped change', reason='Synthetic reason',
            requirement='Preserve scoped behavior', observable='Scoped behavior is observed', claims=['C1'])
        self.stages(home, answer)
        prior = self.prior(home)
        for mutate in (lambda d: d.update(gaps=[]),
                       lambda d: d['package'].update(gaps=[]),
                       lambda d: d['package'].update(brief='Upgrade is authorized now.'),
                       lambda d: d['package'].update(tests=[]),
                       lambda d: d['private']['spec'].update(schema=True)):
            with self.subTest(mutation=mutate):
                bad = deepcopy(prior)
                mutate(bad['report']['ap06'])
                write(home / 'report/ap06.json', bad['report']['ap06'])
                write(home / 'report/result.json', bad['report'])
                with patch.object(policy.assignment_preparation, 'prepare',
                                  side_effect=AssertionError('reuse must not prepare again')):
                    self.assertTrue(self.round(bad)[1]['needs_model'])
                self.assertEqual(json.loads((home / 'report/ap06.json').read_bytes()),
                                 bad['report']['ap06'])

    def test_reuse_preserves_ap06_dependency_gaps_without_new_preparation(self):
        self.fixture.responses[intake._python_url('3.12.1')] += b'<p>Changed scoped claim</p>'
        self.watch['source_map']['local'] = None
        write(self.context / 'watch.json', self.watch)
        home, _ = self.round()
        answer = self.answer(home, 'propose_action')
        answer['proposal'] = dict(text='Consider a scoped change', reason='Synthetic reason',
            requirement='Preserve scoped behavior', observable='Scoped behavior is observed', claims=['C1'])
        self.stages(home, answer)
        prior = self.prior(home)
        self.assertTrue(prior['report']['reviewed'])
        self.assertIn('requirement_dependencies_need_reassessment',
                      {g['code'] for g in prior['report']['ap06']['gaps']})
        with patch.object(policy.assignment_preparation, 'prepare',
                          side_effect=AssertionError('reuse must not prepare again')):
            current, status = self.round(prior)
            self.assertFalse(status['needs_model'])
            report = self.finish(current)
        self.assertTrue(report['reviewed'])
        self.assertEqual(report['ap06'], prior['report']['ap06'])
        self.assertFalse((current / 'report/ap06.json').exists())

    def test_workspace_rejects_context_payload_hash_and_unsafe_paths(self):
        home, _ = self.round()
        dest = self.base / 'workspace'
        dest.mkdir()
        data = home / 'intake/data'
        packet = json.loads((data / 'packet.json').read_bytes())
        payload = data / packet['local'][0]['path']
        original = payload.read_bytes()
        payload.write_bytes(b'tamper')
        with self.assertRaises(ValueError):
            policy.workspace(dest, home, self.context, 'analysis')
        self.assertEqual(list(dest.iterdir()), [])
        payload.write_bytes(original)
        for relative in ('../secret', '/absolute/secret', 'data/../secret'):
            bad = deepcopy(packet)
            bad['local'][0]['path'] = relative
            write(data / 'packet.json', bad)
            with self.assertRaises(ValueError):
                policy.workspace(dest, home, self.context, 'analysis')
        write(data / 'packet.json', packet)
        payload.unlink()
        payload.symlink_to(self.context / 'authority.md')
        with self.assertRaises(ValueError):
            policy.workspace(dest, home, self.context, 'analysis')
        payload.unlink()
        os.mkfifo(payload)
        with self.assertRaises(ValueError):
            policy.workspace(dest, home, self.context, 'analysis')
        payload.unlink()
        payload.write_bytes(original)
        alias = self.base / 'alias'
        alias.symlink_to(self.base, target_is_directory=True)
        for destination, source in ((alias / 'workspace', home), (dest, alias / home.name)):
            with self.assertRaises(ValueError):
                policy.workspace(destination, source, self.context, 'analysis')
        (self.context / 'authority.md').write_text('changed')
        with self.assertRaises(ValueError):
            policy.workspace(dest, home, self.context, 'analysis')
        self.assertEqual(list(dest.iterdir()), [])

    def test_context_fails_closed_before_collection_and_no_disclosure(self):
        for value in ({**self.watch, 'extra': 1}, {**self.watch, 'first_treated_at': '2026-01-01'},
                      {**self.watch, 'source_map': {}}, {**self.watch, 'old_gaps': []}):
            write(self.context / 'watch.json', value)
            with patch.object(intake, 'collect') as collect, self.assertRaises(ValueError) as error:
                policy.prepare(self.base / 'new', self.fixture.roots, self.fixture.versions, None, self.context)
            collect.assert_not_called()
            self.assertEqual(str(error.exception), policy.ERROR)
        write(self.context / 'watch.json', self.watch)
        for raw in (b'', b'x' * policy.CONTEXT_LIMIT):
            (self.context / 'authority.md').write_bytes(raw)
            with patch.object(intake, 'collect') as collect, self.assertRaises(ValueError):
                policy.prepare(self.base / 'new', self.fixture.roots, self.fixture.versions, None, self.context)
            collect.assert_not_called()

    def test_role_schema_and_fixed_prompts(self):
        for role in ('analysis', 'review'):
            schema = policy.schema(role)
            self.assertFalse(schema['additionalProperties'])
            self.assertEqual(set(schema['properties']), set(schema['required']))
            prompt = policy.prompt(role)
            for text in ('INPUT.json', 'authority.md', 'prior-decision.md', 'untrusted evidence',
                         'graceful-drain', 'old decisions', 'Read-only file inspection'):
                self.assertIn(text, prompt)
        for fn in (policy.schema, policy.prompt):
            with self.assertRaises(ValueError):
                fn('host-operation')
        home, _ = self.round()
        with self.assertRaises(ValueError):
            policy.workspace(self.base, home, self.context, 'host-operation')

    def test_frozen_context_survives_original_removal_and_check_is_not_rebased(self):
        home, _ = self.round()
        self.stages(home)
        for path in self.context.iterdir():
            path.unlink()
        self.context.rmdir()
        report = self.finish(home)
        self.assertTrue(report['reviewed'])
        check = json.loads((home / 'intake/data/check.json').read_bytes())
        self.assertEqual(check['manifest'], policy.ap05.reference_manifest(self.case))
        self.mutate(home, 'intake/data/check.json', lambda c: c['manifest']['files'][0].update(sha256='0' * 64))
        with self.assertRaises(ValueError):
            self.finish(home)

    def test_unknown_mapping_is_noncomparison_and_early_observation_rejected(self):
        self.watch['source_map']['vendor'] = 'unresolvable-current-id'
        write(self.context / 'watch.json', self.watch)
        home, _ = self.round()
        self.assertEqual(policy._bundle(home)['ap05']['source_checks'][0]['status'], 'not_checked')
        self.case['created_at'] = '2999-01-01T00:00:00Z'
        write(self.context / 'case.json', self.case)
        with self.assertRaises(ValueError):
            self.round()

    def test_payload_caps_and_symlinked_context_rejected(self):
        home, _ = self.round()
        dest = self.base / 'limited-workspace'
        dest.mkdir()
        data = home / 'intake/data'
        packet = json.loads((data / 'packet.json').read_bytes())
        path = data / packet['local'][0]['path']
        original = path.read_bytes()
        path.write_bytes(b'x' * (intake.MAX_BYTES + 1))
        with self.assertRaises(ValueError):
            policy.workspace(dest, home, self.context, 'analysis')
        path.write_bytes(original)
        with patch.object(policy, 'PAYLOAD_LIMIT', 10), self.assertRaises(ValueError):
            policy.workspace(dest, home, self.context, 'analysis')
        alias = self.base / 'context-alias'
        alias.symlink_to(self.context, target_is_directory=True)
        with patch.object(intake, 'collect') as collect, self.assertRaises(ValueError):
            policy.prepare(self.base / 'new', self.fixture.roots, self.fixture.versions, None, alias)
        collect.assert_not_called()
        self.assertEqual(list(dest.iterdir()), [])

    def test_lineage_bound_accepts_366_nodes_and_rejects_367(self):
        origin, prior = self.approved()
        original_bundle = policy._bundle(origin)
        original_report = prior['report']
        current = dict(packet=prior['packet'], context_hash=original_report['context_sha256'], case=self.case)
        real_json = policy._json
        for count in (366, 367):
            homes = [str(self.base / ('lineage-' + str(i))) for i in range(count - 1)] + [str(origin)]
            reports, bundles = {}, {}
            for i, home in enumerate(homes):
                previous = homes[i + 1] if i + 1 < count else None
                report = deepcopy(original_report)
                report['reused_from'] = previous
                bundle = deepcopy(original_bundle)
                bundle['prepared'].update(reused_from=previous, needs_model=previous is None,
                    reason=policy.FRESH if previous is None else policy.REUSED)
                reports[home] = report
                bundles[home] = bundle

            def read(path):
                if path.name == 'result.json' and path.parent.name == 'intake':
                    prepared = bundles[str(path.parent.parent)]['prepared']
                    status = dict(completed=True, needs_model=prepared['needs_model'],
                                  reason=prepared['reason'])
                    return status, policy._canonical(status), None
                if path.name == 'result.json' and path.parent.name == 'report':
                    report = reports[str(path.parent.parent)]
                    return report, policy._canonical(report), None
                return real_json(path)

            chain = dict(home=homes[0], report=reports[homes[0]], packet=prior['packet'])
            with patch.object(policy, '_bundle', side_effect=lambda home: bundles[home]), \
                 patch.object(policy, '_json', side_effect=read) as reads:
                result = policy._reuse(chain, current)
            self.assertEqual(result is not None, count == 366)
            report_reads = [c for c in reads.call_args_list if c.args[0].parent.name == 'report']
            self.assertEqual(len(report_reads), 366)


if __name__ == '__main__':
    unittest.main()
