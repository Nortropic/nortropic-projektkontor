"""Synthetic pure policy tests; no model or publication effects."""
import copy
import unittest
import development_policy as policy


def context():
    sources = [{'id': name, 'title': name, 'version': 'fixture-v1',
                'path': name+'.md', 'sha256': char*64, 'size': 1}
               for name, char in [('authority', 'a'), ('goal', 'b'), ('observation', 'c')]]
    return {'task_id': 'fixture', 'observed_at': '2026-09-21T12:00:00Z',
            'base': 'd'*40, 'runtime_revision': 'e'*40, 'acceptance_sha256': 'f'*64,
            'integrated': {}, 'sources': sources,
            'source_check': {'checked_at': '2026-09-21T12:00:00Z',
                             'manifest': {'version': 1, 'files': [{k: s[k] for k in ('path', 'sha256', 'size')} for s in sources]},
                             'result': {'ok': True, 'files': [{'path': s['path'], 'status': 'ok'} for s in sources]}}}


def proposal():
    return {'action': 'task', 'work': 'reconciliation', 'reason': 'Actual named reconciliation missing',
            'brief': 'Implement the accepted reconciliation with existing result reader', 'depends_on': '',
            'requirements': [{'id': 'r1', 'text': 'Show missing requirements', 'reason': 'Useful continuation'}],
            'tests': [{'id': 't1', 'observable': 'Missing evidence remains missing', 'method': 'Use isolated synthetic input'}]}


class PolicyTests(unittest.TestCase):
    def test_uses_ap06_but_returns_draft_not_authority(self):
        c, p = context(), proposal(); original = copy.deepcopy((c, p))
        packet = policy.prepare(c, p)
        self.assertEqual((c, p), original)
        self.assertTrue(packet['preparation']['mechanical_complete'])
        self.assertEqual(packet['preparation']['status'], 'draft')
        self.assertEqual(packet['task']['allowed_paths'], policy.WORK['reconciliation'])
        self.assertEqual(packet['task']['acceptance'], policy.RECIPES['reconciliation'])
        packet['task']['allowed_paths'].append('tools/forbidden.py')
        self.assertNotIn('tools/forbidden.py', policy.WORK['reconciliation'])
        self.assertNotIn('tools/forbidden.py', policy.prepare(c, p)['task']['allowed_paths'])

    def test_child_executor_is_the_frozen_context_choice_never_the_model_answer(self):
        # Absent selection (older Runtime) and explicit Codex give the original task bytes.
        plain = policy.prepare(context(), proposal())['task']
        self.assertEqual(plain['steps'][0]['provider'], 'codex'); self.assertNotIn('review_provider', plain)
        c = context(); c['executors'] = {'implementation': 'codex', 'review': 'codex'}
        self.assertEqual(policy.prepare(c, proposal())['task'], plain)
        c['executors'] = {'implementation': 'claude', 'review': 'claude'}
        chosen = policy.prepare(c, proposal())['task']
        self.assertEqual((chosen['steps'][0]['provider'], chosen['review_provider']), ('claude', 'claude'))
        self.assertEqual({k: v for k, v in chosen.items() if k not in ('steps', 'review_provider')},
                         {k: v for k, v in plain.items() if k != 'steps'})
        c['executors'] = {'implementation': 'claude', 'review': 'codex'}
        mixed = policy.prepare(c, proposal())['task']
        self.assertEqual(mixed['steps'][0]['provider'], 'claude'); self.assertNotIn('review_provider', mixed)
        # The reviewer choice is independent of the author choice: Codex author, Claude reviewer.
        c['executors'] = {'implementation': 'codex', 'review': 'claude'}
        crossed = policy.prepare(c, proposal())['task']
        self.assertEqual((crossed['steps'][0]['provider'], crossed['review_provider']), ('codex', 'claude'))
        self.assertEqual({k: v for k, v in crossed.items() if k != 'review_provider'}, plain)
        # A model answer cannot even carry an executor: the strict answer shape refuses the extra field.
        for field in ('provider', 'executors', 'review_provider'):
            p = proposal(); p[field] = 'claude'
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, 'bounded necessary task proposal'):
                policy.prepare(context(), p)
        for bad in ({'implementation': 'gpt', 'review': 'codex'}, {'implementation': 'claude'}, {'implementation': 'claude', 'review': None},
                    {'implementation': 'claude', 'review': 'claude', 'driver': 'claude'}, ['claude'], 'claude', None):
            c = context(); c['executors'] = bad
            with self.subTest(bad=bad), self.assertRaisesRegex(ValueError, 'executor selection is invalid'):
                policy.prepare(c, proposal())

    def test_changed_source_blocks_preparation_not_erase_old_decision(self):
        c = context(); c['source_check']['result']['ok'] = False
        c['source_check']['result']['files'][0]['status'] = 'changed'
        with self.assertRaises(ValueError):
            policy.prepare(c, proposal())
        self.assertEqual(c['sources'][0]['sha256'], 'a'*64)

    def test_finished_or_unrelated_work_is_refused(self):
        c = context(); c['integrated']['reconciliation'] = {'merge_commit': '1'*40}
        with self.assertRaises(ValueError):
            policy.prepare(c, proposal())
        p = proposal(); p['work'] = 'unrelated'
        with self.assertRaises(ValueError):
            policy.prepare(context(), p)

    def test_handoff_requires_actual_predecessor_source_and_integration(self):
        c, p = context(), proposal(); p.update(work='handoff', depends_on='1'*40)
        with self.assertRaises(ValueError):
            policy.prepare(c, p)
        c['integrated']['reconciliation'] = {'merge_commit': '1'*40}
        with self.assertRaises(ValueError):
            policy.prepare(c, p)
        c['actual_reconciliation_source'] = 'Host bound exact integrated source'
        self.assertEqual(policy.prepare(c, p)['work'], 'handoff')
        p['depends_on'] = '2'*40
        with self.assertRaises(ValueError):
            policy.prepare(c, p)

    def test_review_cannot_approve_missing_or_conflicting_evidence(self):
        self.assertTrue(policy.review({'verdict': 'approved', 'summary': 'Substantive reviewed', 'blocking_findings': []}))
        self.assertFalse(policy.review({'verdict': 'approved', 'summary': 'Contradiction', 'blocking_findings': ['missing criterion']}))
        for result in ({}, {'verdict': 'approved', 'summary': '', 'blocking_findings': []}):
            with self.assertRaises(ValueError):
                policy.review(result)

    def test_roles_are_frozen_read_only_instructions_not_an_engine(self):
        for role in ('driver', 'preparation-review', 'diagnosis', 'final-review'):
            self.assertIn('structured data only', policy.instructions(role))
            # Every role reads through the same delivered inventory; the finding aid names the files a reader
            # without directory listing could not discover (measured 2026-09-22), and keeps hold permitted.
            text = policy.instructions(role)
            for needle in ('delivered_files', 'cannot list directories', 'never guess names', 'VERIFICATION_RECIPE.py',
                           'tools/kontor_result.py', 'tools/agarbild.py', 'tools/development_result.py', 'AGENTS.md',
                           'OUTPUT_SCHEMA.json', 'confers no authority', 'hold remains the right answer'):
                self.assertIn(needle, text, (role, needle))
            self.assertNotIn('always', text.split('hold remains')[0][-200:])
            self.assertFalse(policy.schema(role)['additionalProperties'])


if __name__ == '__main__':
    unittest.main()
