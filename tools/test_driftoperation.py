"""Real loopback HTTP and crash-boundary checks, no external provider claims."""
import copy
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import tempfile
import sys
import threading
import time
import unittest
from unittest.mock import patch
import driftoperation as operation


class OperationTests(unittest.TestCase):
    def setUp(self):
        scratch = Path('.scratch'); scratch.mkdir(exist_ok=True)
        self.directory = tempfile.TemporaryDirectory(dir=scratch)
        self.addCleanup(self.directory.cleanup)
        self.home = Path(self.directory.name).absolute()
        self.http_status, self.calls, self.candidate = 200, 0, 'a' * 40
        owner = self
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_): pass
            def do_GET(self):
                owner.calls += 1
                self.send_response(owner.http_status); self.end_headers()
                self.wfile.write(json.dumps({'status': 'ok', 'candidate': owner.candidate,
                                             'storage': 'available'}).encode())
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True); self.thread.start()
        self.addCleanup(self.server.server_close); self.addCleanup(self.server.shutdown)
        self.config = {'schema': 'office-drift/1', 'state': str(self.home / 'state'),
            'monitor': {'url': 'http://127.0.0.1:%s/health' % self.server.server_port,
                        'candidate': 'a' * 40, 'isolated_test': True}}

    def test_incident_recovery_delivery_and_repeated_run(self):
        self.assertTrue(operation.run(self.config, 'first')['completed'])
        self.http_status = 503
        failed = operation.run(self.config, 'second')
        self.assertFalse(failed['completed']); self.assertEqual(len(failed['monitor']['attempts']), 2)
        self.assertEqual(failed['deliveries']['monitor']['receipts'][0]['recipient'], 'kontorets-privata-driftyta')
        calls = self.calls
        self.assertEqual(operation.run(self.config, 'second'), failed); self.assertEqual(self.calls, calls)
        self.http_status = 200
        self.assertTrue(operation.run(self.config, 'third')['completed'])
        inbox = self.home / 'state/inbox'
        events = [json.loads(p.read_text())['event']['kind'] for p in sorted(inbox.glob('*.json'))]
        self.assertCountEqual(events, ['incident', 'recovered'])

    def test_wrong_candidate_and_permanent_error_are_not_green(self):
        self.candidate = 'b' * 40
        self.assertFalse(operation.run(self.config, 'wrong')['completed'])
        self.http_status = 403
        result = operation.run(self.config, 'forbidden')
        self.assertEqual(result['monitor']['attempts'], [{'http': 403, 'healthy': False}])

    def test_pending_delivery_survives_crash_without_duplicate(self):
        self.http_status = 403
        actual = operation.deliver
        def interrupted(home, event):
            actual(home, event)
            raise InterruptedError('after receiver persisted, before sender ack')
        with patch.object(operation, 'deliver', interrupted):
            with self.assertRaises(InterruptedError): operation.run(self.config, 'crash')
        self.assertTrue((self.home / 'state/pending.json').exists())
        result = operation.run(self.config, 'crash')
        self.assertFalse(result['completed'])
        self.assertFalse((self.home / 'state/pending.json').exists())
        self.assertEqual(len(list((self.home / 'state/inbox').glob('*.json'))), 1)
        self.assertTrue(result['deliveries']['monitor']['receipts'][0]['resumed'])

    def test_http_and_symlink_refused(self):
        altered = copy.deepcopy(self.config); altered['monitor'].pop('isolated_test')
        with self.assertRaises(ValueError): operation.run(altered, 'http')
        link = self.home / 'link'; link.symlink_to(self.home / 'state', target_is_directory=True)
        altered['state'] = str(link)
        with self.assertRaises(ValueError): operation.run(altered, 'link')

    def test_changed_config_cannot_reuse_cached_run(self):
        operation.run(self.config, 'bound')
        other = copy.deepcopy(self.config); other['monitor']['candidate'] = 'b' * 40
        with self.assertRaisesRegex(ValueError, 'another configuration'):
            operation.run(other, 'bound')

    def test_intake_failure_does_not_suppress_monitor(self):
        self.config['intake'] = {'invalid': 'fixture'}
        self.http_status = 503
        result = operation.run(self.config, 'intake-failure')
        self.assertFalse(result['completed'])
        self.assertEqual(result['intake']['reason'], 'consumer_failed')
        self.assertEqual(result['deliveries']['monitor']['receipts'][0]['recipient'], 'kontorets-privata-driftyta')
        self.assertEqual(len(result['monitor']['attempts']), 2)

    def intake_fixture(self):
        root = self.home / 'digitala'; (root / 'verktyg').mkdir(parents=True)
        script = root / 'verktyg/kundstart.py'
        script.write_text("import sys, pathlib\n"
                          "p=pathlib.Path(sys.argv[sys.argv.index('--kund')+1])/'consumed'\n"
                          "p.write_text('one') if not p.exists() else None\n"
                          "print('fixture consumer completed')\n")
        customer = self.home / 'customer'; customer.mkdir()
        interpreter = Path(sys.executable).resolve()
        self.config['intake'] = {'digitala_root': str(root),
            'digitala_files': {'verktyg/kundstart.py': operation.digest(script.read_bytes())},
            'python_path': str(interpreter), 'python_sha256': operation.digest(interpreter.read_bytes()),
            'base_url': self.config['monitor']['url'], 'key_file': str(self.home / 'private-key'),
            'customer': str(customer), 'executor': 'isolated-fixture'}
        return customer

    def test_actual_subprocess_positive_replay_and_interpreter_tamper(self):
        customer = self.intake_fixture()
        result = operation.run(self.config, 'consumer')
        self.assertTrue(result['completed'])
        self.assertEqual((customer / 'consumed').read_text(), 'one')
        stamp = (customer / 'consumed').stat().st_mtime_ns
        self.assertEqual(operation.run(self.config, 'consumer'), result)
        self.assertEqual((customer / 'consumed').stat().st_mtime_ns, stamp)
        self.config['intake']['python_sha256'] = '0' * 64
        failed = operation.run(self.config, 'tampered-interpreter')
        self.assertFalse(failed['intake']['completed'])
        self.assertEqual(len(failed['deliveries']['intake']['receipts']), 1)
        self.assertTrue(failed['monitor']['healthy'])

    def test_intake_failure_and_recovery_have_independent_real_receipts(self):
        self.config['intake'] = {'invalid': 'fixture'}
        failed = operation.run(self.config, 'failed-intake')
        self.assertEqual(len(failed['deliveries']['intake']['receipts']), 1)
        self.assertEqual(failed['deliveries']['monitor']['receipts'], [])
        self.intake_fixture()
        recovered = operation.run(self.config, 'recovered-intake')
        self.assertTrue(recovered['completed'])
        events = [json.loads(p.read_text())['event'] for p in (self.home / 'state/inbox').glob('*.json')]
        self.assertEqual({e['channel'] for e in events}, {'intake'})
        self.assertCountEqual([e['kind'] for e in events], ['incident', 'recovered'])

    def test_corrupt_outbox_cannot_escape_and_next_run_recovers(self):
        operation.run(self.config, 'setup')
        (self.home / 'state/pending.json').write_text(json.dumps({'id': '../escape'}))
        failed = operation.run(self.config, 'corrupt')
        self.assertFalse(failed['completed'])
        self.assertEqual(failed['deliveries']['monitor']['state_error'], 'invalid_event_identity')
        self.assertFalse((self.home / 'state/escape.json').exists())
        self.assertEqual(len(list((self.home / 'state').glob('pending.json.invalid-*'))), 1)
        self.assertTrue(operation.run(self.config, 'after-corrupt')['completed'])

    def test_closed_state_shape_and_deleted_state_do_not_collide(self):
        for value in ({'healthy': 'false', 'sequence': 1, 'observed_at': operation.now()},
                      {'healthy': False, 'sequence': True, 'observed_at': operation.now()},
                      {'healthy': False, 'sequence': 1, 'observed_at': operation.now(), 'extra': 1}):
            with self.assertRaises(operation.StateError): operation.validate_state(value)
        self.http_status = 403
        operation.run(self.config, 'incident-before-loss')
        (self.home / 'state/monitor.json').unlink()
        operation.run(self.config, 'incident-after-loss')
        self.assertEqual(len(list((self.home / 'state/inbox').glob('*.json'))), 2)


if __name__ == '__main__': unittest.main()


class WeeklyDriftTests(unittest.TestCase):
    """The drift channel on Digitala's real drift_kontroll.py bytes, and dueness.

    The site is a loopback fixture, never a customer's real address. The checked
    tool is the actual frozen file from Digitala, so a passing check here is a pass
    of the bytes the release would schedule.
    """
    DIGITALA = Path(__file__).resolve().parents[2] / 'nortropic-digitala'

    def setUp(self):
        scratch = Path('.scratch'); scratch.mkdir(exist_ok=True)
        self.directory = tempfile.TemporaryDirectory(dir=scratch)
        self.addCleanup(self.directory.cleanup)
        self.home = Path(self.directory.name).absolute()
        self.site_status, self.sitemap_status, self.body, self.calls = 200, 200, 'Välkommen till provsajten', 0
        owner = self
        class Site(BaseHTTPRequestHandler):
            def log_message(self, *_): pass
            def do_GET(self):
                owner.calls += 1
                sitemap = self.path.endswith('/sitemap.xml')
                self.send_response(owner.sitemap_status if sitemap else owner.site_status)
                self.end_headers()
                self.wfile.write(('<urlset/>' if sitemap else owner.body).encode())
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), Site)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True); self.thread.start()
        self.addCleanup(self.server.server_close); self.addCleanup(self.server.shutdown)
        self.address = 'http://127.0.0.1:%s/' % self.server.server_port

        source = self.DIGITALA / 'verktyg/drift_kontroll.py'
        if not source.is_file():
            self.skipTest('Digitala checkout with verktyg/drift_kontroll.py is required')
        root = self.home / 'digitala'; (root / 'verktyg').mkdir(parents=True)
        frozen = root / 'verktyg/drift_kontroll.py'; frozen.write_bytes(source.read_bytes())
        self.customer = self.home / 'kund'; self.customer.mkdir()
        self.plan = self.home / 'DRIFT.json'
        self.write_plan({'schema': 1, 'kund': 'Provkund',
                         'sajter': [{'adress': self.address, 'forvantat': 'provsajten',
                                     'max_ms': 30000, 'sitemap': True}]})
        interpreter = Path(sys.executable).resolve()
        self.state = self.home / 'state'
        self.config = {'schema': 'office-drift/1', 'state': str(self.state),
            'drift': {'digitala_root': str(root),
                      'digitala_files': {'verktyg/drift_kontroll.py': operation.digest(frozen.read_bytes())},
                      'python_path': str(interpreter),
                      'python_sha256': operation.digest(interpreter.read_bytes()),
                      'plan': str(self.plan), 'plan_sha256': self.plan_sha,
                      'receipts': str(self.customer), 'isolated_test': True}}

    def write_plan(self, value):
        raw = (json.dumps(value, ensure_ascii=False) + '\n').encode()
        self.plan.write_bytes(raw); self.plan_sha = operation.digest(raw)
        if getattr(self, 'config', None):
            self.config['drift']['plan_sha256'] = self.plan_sha

    def receipts(self):
        return sorted(p.name for p in self.customer.glob('DRIFT-*.json'))

    def events(self):
        return [json.loads(p.read_text())['event']
                for p in sorted((self.state / 'inbox').glob('*.json'))]

    def test_clean_run_incident_and_recovery_land_in_the_customer_path(self):
        clean = operation.run(self.config, 'clean')
        self.assertTrue(clean['completed']); self.assertTrue(clean['performed'])
        self.assertTrue(clean['drift']['ran']); self.assertTrue(clean['drift']['healthy'])
        self.assertEqual(clean['drift']['incidents'], 0)
        self.assertEqual(clean['drift']['returncode'], 0)
        self.assertEqual(clean['deliveries']['drift']['receipts'], [])
        # The receipt is the DRIFT-<tid>.json artefact underhall.py besked reads.
        self.assertEqual(self.receipts(), [clean['drift']['receipt']])
        written = json.loads((self.customer / clean['drift']['receipt']).read_text(encoding='utf-8'))
        self.assertEqual(written['incidenter'], 0)
        self.assertEqual(operation.digest((self.customer / clean['drift']['receipt']).read_bytes()),
                         clean['drift']['receipt_sha256'])

        self.site_status = 503
        incident = operation.run(self.config, 'incident')
        self.assertTrue(incident['performed'], 'a check that found an incident still ran')
        self.assertFalse(incident['completed'])
        self.assertTrue(incident['drift']['ran']); self.assertFalse(incident['drift']['healthy'])
        self.assertEqual(incident['drift']['returncode'], 1)
        self.assertEqual(incident['drift']['incidents'], 1)
        self.assertEqual(incident['drift']['reason'], 'site_incident')
        self.assertIn('svarar 503', ' '.join(incident['drift']['findings'][0]['fynd']))
        self.assertEqual(incident['deliveries']['drift']['receipts'][0]['recipient'],
                         'kontorets-privata-driftyta')
        # The receipt the result names carries this run's own finding.
        named = json.loads((self.customer / incident['drift']['receipt']).read_text(encoding='utf-8'))
        self.assertEqual(named['incidenter'], 1)
        self.assertTrue(named['sajter'][0]['incident'])

        self.site_status = 200
        recovered = operation.run(self.config, 'recovered')
        self.assertTrue(recovered['completed'])
        self.assertEqual([(e['channel'], e['kind']) for e in self.events()],
                         [('drift', 'incident'), ('drift', 'recovered')]
                         if self.events()[0]['kind'] == 'incident' else
                         [('drift', 'recovered'), ('drift', 'incident')])
        self.assertCountEqual([e['kind'] for e in self.events()], ['incident', 'recovered'])
        self.assertEqual(json.loads((self.customer / recovered['drift']['receipt'])
                                    .read_text(encoding='utf-8'))['incidenter'], 0)

    def test_expected_text_and_sitemap_are_each_an_incident(self):
        self.body = 'helt annan text'
        first = operation.run(self.config, 'missing-text')
        self.assertEqual(first['drift']['findings'][0]['fynd'], ['förväntad text saknas'])
        self.body = 'Välkommen till provsajten'
        self.sitemap_status = 404
        second = operation.run(self.config, 'missing-sitemap')
        self.assertEqual(second['drift']['findings'][0]['fynd'], ['sitemap svarar 404'])

    def test_exit_code_must_agree_with_the_receipt_it_wrote(self):
        actual = operation.bounded_start
        def rewrite(argv, *args, **kwargs):
            status = actual(argv, *args, **kwargs)
            target = Path(argv[argv.index('--ut') + 1])
            for path in target.glob('DRIFT-*.json'):
                value = json.loads(path.read_text(encoding='utf-8'))
                value['incidenter'] = 3          # disagrees with both the rows and exit 0
                path.write_text(json.dumps(value) + '\n', encoding='utf-8')
            return status
        with patch.object(operation, 'bounded_start', rewrite):
            result = operation.run(self.config, 'disagreeing-receipt')
        self.assertFalse(result['drift']['ran']); self.assertFalse(result['performed'])
        self.assertEqual(result['drift']['reason'], 'drift_receipt_inconsistent')
        self.assertFalse(result['completed'])

    @staticmethod
    def stub(status, stdout=b''):
        """bounded_start always creates its two streams; a stub must do the same."""
        def started(argv, root, environment, bound, out, err):
            out.write_bytes(stdout); err.write_bytes(b'')
            return status
        return started

    def test_a_check_that_wrote_nothing_is_not_green(self):
        with patch.object(operation, 'bounded_start', self.stub(0)):
            result = operation.run(self.config, 'no-receipt')
        self.assertFalse(result['drift']['ran'])
        self.assertEqual(result['drift']['reason'], 'drift_receipt_unreadable')
        self.assertFalse(result['completed'])

    def test_a_receipt_claimed_outside_the_customer_path_is_refused(self):
        elsewhere = self.home / 'DRIFT-20260929T000000Z.json'
        elsewhere.write_text(json.dumps({'schema': 1, 'sajter': [{'adress': 'x', 'incident': False}],
                                         'incidenter': 0}))
        declared = json.dumps({'incidenter': 0, 'ut': str(elsewhere)}).encode()
        with patch.object(operation, 'bounded_start', self.stub(0, declared)):
            result = operation.run(self.config, 'escaped-receipt')
        self.assertFalse(result['drift']['ran'])
        self.assertEqual(result['drift']['reason'], 'drift_receipt_unreadable')

    def test_a_same_second_rerun_is_still_evidence_of_its_own_check(self):
        # drift_kontroll.py names its receipt to the whole second and overwrites a
        # same-second rerun, so a new filename cannot be what proves a check ran.
        first = operation.run(self.config, 'same-second-one')
        second = operation.run(self.config, 'same-second-two')
        self.assertTrue(first['drift']['ran']); self.assertTrue(second['drift']['ran'])
        self.assertTrue(first['performed']); self.assertTrue(second['performed'])
        if first['drift']['receipt'] == second['drift']['receipt']:
            # Recorded rather than hidden: the later check overwrote the earlier
            # receipt in the customer path. A weekly period cannot collide, and each
            # run's own result.json keeps the hash of the bytes that run read.
            self.assertEqual(len(self.receipts()), 1)
            self.assertEqual(operation.digest((self.customer / second['drift']['receipt']).read_bytes()),
                             second['drift']['receipt_sha256'])

    def test_the_tools_own_count_must_agree_with_the_receipt(self):
        actual = operation.bounded_start
        def miscount(argv, root, environment, bound, out, err):
            status = actual(argv, root, environment, bound, out, err)
            declared = json.loads(out.read_bytes().splitlines()[-1])
            declared['incidenter'] = 7
            out.write_bytes((json.dumps(declared) + '\n').encode())
            return status
        with patch.object(operation, 'bounded_start', miscount):
            result = operation.run(self.config, 'miscounted')
        self.assertFalse(result['drift']['ran'])
        self.assertEqual(result['drift']['reason'], 'drift_receipt_inconsistent')

    def test_timeout_refusal_and_failure_are_distinct_and_never_green(self):
        for status, reason in ((None, 'drift_timeout'), (2, 'drift_refused'), (9, 'drift_failed')):
            with patch.object(operation, 'bounded_start', self.stub(status)):
                result = operation.run(self.config, 'bounded-' + str(status))
            self.assertEqual(result['drift']['reason'], reason)
            self.assertFalse(result['drift']['ran']); self.assertFalse(result['completed'])

    def test_changed_plan_or_tool_bytes_refuse_the_channel(self):
        self.config['drift']['plan_sha256'] = '0' * 64
        result = operation.run(self.config, 'tampered-plan')
        self.assertEqual(result['drift']['reason'], 'drift_binding_failed')
        self.assertEqual(result['drift']['error_type'], 'ValueError')
        self.assertEqual(self.receipts(), [])
        self.config['drift']['plan_sha256'] = self.plan_sha
        self.config['drift']['digitala_files'] = {'verktyg/kundstart.py': '0' * 64}
        missing = operation.run(self.config, 'wrong-tool')
        self.assertEqual(missing['drift']['reason'], 'drift_binding_failed')
        self.config['drift']['digitala_files'] = {}
        empty = operation.run(self.config, 'no-tool')
        self.assertEqual(empty['drift']['reason'], 'drift_binding_failed')

    def test_http_site_needs_the_isolated_test_flag(self):
        # drift_kontroll.py itself refuses a non-https address without --tillat-http,
        # so the receipt exists but names the incident rather than passing quietly.
        del self.config['drift']['isolated_test']
        result = operation.run(self.config, 'plain-http')
        self.assertTrue(result['drift']['ran']); self.assertFalse(result['drift']['healthy'])
        self.assertEqual(result['drift']['findings'][0]['fynd'], ['adressen är inte https'])
        self.assertEqual(self.calls, 0, 'no request is made to a refused address')

    def test_bound_seconds_is_the_sum_of_its_named_channel_bounds(self):
        self.assertEqual(operation.BOUND_SECONDS,
                         operation.INTAKE_BOUND + operation.DRIFT_BOUND
                         + 2 * operation.TERMINATION_BOUND + operation.MONITOR_BOUND)
        # The monitor's ceiling is its own enforced wall clock plus one socket
        # operation that may already have been blocked when the deadline passed.
        self.assertEqual(operation.MONITOR_BOUND,
                         operation.MONITOR_DEADLINE + operation.MONITOR_TIMEOUT)
        self.assertGreater(operation.MONITOR_DEADLINE, 2 * operation.MONITOR_TIMEOUT)

    def test_an_operation_without_a_channel_is_refused(self):
        with self.assertRaises(ValueError):
            operation.run({'schema': 'office-drift/1', 'state': str(self.state)}, 'empty')

    # --- dueness: a missed period is performed, never skipped ---

    def week(self, **change):
        self.config['period_seconds'] = 604800
        self.config.update(change)

    def set_period(self, ago_seconds, sequence=1, run_id='tidigare-korning'):
        from datetime import datetime, timedelta, timezone
        stamp = (datetime.now(timezone.utc) - timedelta(seconds=ago_seconds)).isoformat()
        self.state.mkdir(mode=0o700, parents=True, exist_ok=True)
        (self.state / 'period.json').write_text(
            json.dumps({'completed_at': stamp, 'sequence': sequence, 'run_id': run_id}) + '\n')

    def test_first_run_is_due_and_a_wakeup_inside_the_period_reads_nothing(self):
        self.week()
        first = operation.run(self.config, 'week-one')
        self.assertTrue(first['performed'])
        self.assertEqual(first['period']['reason'], 'no_period_recorded')
        self.assertEqual(first['period_recorded']['sequence'], 1)
        self.assertEqual(first['period_recorded']['completed_at'], first['started_at'])
        self.assertEqual(first['period_recorded']['run_id'], 'week-one')
        calls, receipts = self.calls, self.receipts()

        inside = operation.run(self.config, 'week-one-tick-two')
        self.assertEqual(inside['skipped'], 'not_due')
        self.assertFalse(inside['performed']); self.assertTrue(inside['completed'])
        self.assertEqual(inside['period']['reason'], 'not_due')
        self.assertEqual(inside['period']['overdue_seconds'], 0)
        self.assertEqual(self.calls, calls, 'a wakeup inside the period makes no request')
        self.assertEqual(self.receipts(), receipts)
        self.assertFalse((self.state / 'week-one-tick-two').exists(),
                         'a tick that reads nothing writes no run record')

    def test_a_period_missed_while_the_host_slept_is_performed_on_the_next_wakeup(self):
        self.week()
        operation.run(self.config, 'week-one')
        # Nine days without a run: the Mac slept through the weekly time.
        self.set_period(9 * 86400)
        late = operation.run(self.config, 'after-sleep')
        self.assertTrue(late['performed'], 'the missed period is run, not skipped')
        self.assertEqual(late['period']['reason'], 'period_elapsed')
        self.assertGreaterEqual(late['period']['overdue_seconds'], 2 * 86400)
        self.assertEqual(late['period_recorded']['sequence'], 2)
        self.assertEqual(json.loads((self.customer / late['drift']['receipt'])
                                    .read_text(encoding='utf-8'))['incidenter'], 0)

    def test_a_period_that_did_not_actually_run_stays_due(self):
        self.week()
        with patch.object(operation, 'bounded_start', self.stub(None)):
            failed = operation.run(self.config, 'broken')
        self.assertFalse(failed['performed']); self.assertNotIn('period_recorded', failed)
        self.assertFalse((self.state / 'period.json').exists())
        retried = operation.run(self.config, 'retry')
        self.assertTrue(retried['performed'])
        self.assertEqual(retried['period']['reason'], 'no_period_recorded')

    def test_invalid_period_state_is_preserved_and_the_work_still_runs(self):
        self.week()
        operation.run(self.config, 'week-one')
        (self.state / 'period.json').write_text(
            json.dumps({'completed_at': 'inte en tid', 'sequence': 1, 'run_id': 'nagon'}))
        result = operation.run(self.config, 'after-corrupt-period')
        self.assertTrue(result['performed'])
        self.assertFalse(result['completed'], 'the corrupt period state is reported, not hidden')
        self.assertEqual(result['period']['reason'], 'invalid_period_state')
        self.assertEqual(len(list((self.state).glob('period.json.invalid-*'))), 1)
        self.assertEqual(result['period_recorded']['sequence'], 1)

    def test_closed_period_state_shapes_are_refused(self):
        self.week()
        now = operation.now()
        for value in ({'completed_at': now, 'sequence': 1},
                      {'completed_at': now, 'run_id': 'a'},
                      {'completed_at': now, 'sequence': 0, 'run_id': 'a'},
                      {'completed_at': now, 'sequence': True, 'run_id': 'a'},
                      {'completed_at': now, 'sequence': 1, 'run_id': '../escape'},
                      {'completed_at': now, 'sequence': 1, 'run_id': 1},
                      {'completed_at': now, 'sequence': 1, 'run_id': 'a', 'extra': 1}):
            self.state.mkdir(mode=0o700, parents=True, exist_ok=True)
            (self.state / 'period.json').write_text(json.dumps(value))
            self.assertEqual(operation.due(self.state, self.config, 'nu')['reason'],
                             'invalid_period_state')

    def test_a_future_or_overflowing_period_record_cannot_silence_the_work(self):
        # A stamp from the future would report every wakeup as a successful skip until
        # that date arrives, and year 9999 overflows the addition. Both must be caught.
        self.week()
        def plant(stamp):
            # due() quarantines the file it rejects, so each assertion needs its own.
            self.state.mkdir(mode=0o700, parents=True, exist_ok=True)
            (self.state / 'period.json').write_text(
                json.dumps({'completed_at': stamp, 'sequence': 1, 'run_id': 'framtiden'}))
        for stamp in ('2099-01-01T00:00:00+00:00', '9999-12-31T00:00:00+00:00'):
            plant(stamp)
            answer = operation.due(self.state, self.config, 'nu')
            self.assertTrue(answer['due']); self.assertEqual(answer['reason'], 'invalid_period_state')
            plant(stamp)
            result = operation.run(self.config, 'efter-' + stamp[:4])
            self.assertTrue(result['performed'], 'the work runs despite the bad record')
            self.assertFalse(result['completed'], 'the bad record is reported, not hidden')
            self.assertEqual(result['period']['reason'], 'invalid_period_state')
            for path in self.state.glob('period.json.invalid-*'):
                path.unlink()

    def test_a_record_is_not_due_only_a_moment_before_its_time(self):
        self.week()
        self.set_period(604800 - 1)
        self.assertFalse(operation.due(self.state, self.config, 'nu')['due'])
        self.set_period(604800)
        self.assertTrue(operation.due(self.state, self.config, 'nu')['due'])

    def test_period_outside_its_bounds_is_refused(self):
        for period in (60, 3599, 2678401, True, '604800'):
            self.config['period_seconds'] = period
            with self.assertRaises(ValueError):
                operation.run(self.config, 'bad-period-' + str(period))

    def test_a_run_interrupted_after_closing_its_period_does_not_close_it_twice(self):
        # The receipt is written after the period is closed, so a crash in between
        # leaves a record naming this run. Resuming must finish the receipt without
        # advancing the sequence again and without reporting the period as not due.
        self.week()
        first = operation.run(self.config, 'week-one')
        self.assertEqual(first['period_recorded']['sequence'], 1)
        (self.state / 'week-one/result.json').unlink()
        resumed = operation.run(self.config, 'week-one')
        self.assertNotIn('skipped', resumed)
        self.assertTrue(resumed['performed'])
        self.assertEqual(resumed['period']['reason'], 'own_period_record')
        self.assertEqual(resumed['period_recorded']['sequence'], 1, 'one period, one sequence step')
        self.assertEqual(json.loads((self.state / 'period.json').read_text())['run_id'], 'week-one')
        # The next period still advances normally for a different run.
        self.set_period(604800, sequence=1, run_id='week-one')
        later = operation.run(self.config, 'week-two')
        self.assertEqual(later['period_recorded']['sequence'], 2)

    def test_another_runs_record_does_not_make_this_run_due(self):
        self.week()
        self.set_period(60, sequence=4, run_id='nagon-annan')
        answer = operation.due(self.state, self.config, 'jag')
        self.assertFalse(answer['due']); self.assertEqual(answer['reason'], 'not_due')

    def test_a_cached_result_is_returned_before_dueness_is_consulted(self):
        self.week()
        first = operation.run(self.config, 'week-one')
        self.assertEqual(operation.run(self.config, 'week-one'), first)


class MonitorWallClockTests(unittest.TestCase):
    """A trickling server must not outlast the monitor's own declared ceiling.

    urlopen's timeout bounds each blocking socket operation, not the whole attempt, so
    without its own wall clock the monitor could read for as long as a server keeps
    sending a byte just inside the timeout - holding the state lock past the workflow's
    own bound and blocking later periods.
    """

    def setUp(self):
        self.chunks, self.gap = 40, 0.25
        owner = self
        class Trickle(BaseHTTPRequestHandler):
            protocol_version = 'HTTP/1.1'
            def log_message(self, *_): pass
            def do_GET(self):
                self.send_response(200)
                self.send_header('Content-Length', str(owner.chunks))
                self.end_headers()
                for _ in range(owner.chunks):
                    try:
                        self.wfile.write(b' '); self.wfile.flush()
                    except (BrokenPipeError, ConnectionResetError, OSError):
                        return
                    time.sleep(owner.gap)
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), Trickle)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.server.server_close); self.addCleanup(self.server.shutdown)
        self.config = {'url': 'http://127.0.0.1:%s/health' % self.server.server_port,
                       'candidate': 'a' * 40, 'isolated_test': True}

    def test_a_trickling_endpoint_is_cut_at_the_monitor_deadline(self):
        # Shortened only to keep the test quick; the enforced relationship is the same.
        with patch.object(operation, 'MONITOR_DEADLINE', 2), \
             patch.object(operation, 'MONITOR_TIMEOUT', 5):
            started = time.monotonic()
            result = operation.monitor(self.config)
            elapsed = time.monotonic() - started
        self.assertFalse(result['healthy'])
        self.assertEqual(result['reason'], 'endpoint_unavailable')
        self.assertLess(elapsed, 2 + 5, 'the deadline plus one blocked operation is the ceiling')
        self.assertGreaterEqual(len(result['attempts']), 1)
        self.assertTrue(any(a.get('error') in ('transport_unavailable', 'monitor_bound_exceeded')
                            for a in result['attempts']), result['attempts'])

    def test_a_prompt_endpoint_is_unaffected_by_the_deadline(self):
        self.chunks, self.gap = 1, 0
        result = operation.monitor(self.config)
        self.assertFalse(result['healthy'])          # a space is not the health body
        self.assertEqual(result['attempts'][0]['error'], 'invalid_health_response')
