"""Real loopback HTTP and crash-boundary checks, no external provider claims."""
import copy
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import tempfile
import threading
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
        self.assertEqual(failed['delivery']['recipient'], 'kontorets-privata-driftyta')
        calls = self.calls
        self.assertEqual(operation.run(self.config, 'second'), failed); self.assertEqual(self.calls, calls)
        self.http_status = 200
        self.assertTrue(operation.run(self.config, 'third')['completed'])
        inbox = self.home / 'state/inbox'
        events = [json.loads(p.read_text())['event']['kind'] for p in sorted(inbox.glob('*.json'))]
        self.assertEqual(events, ['incident', 'recovered'])

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
        self.assertEqual(result['delivery']['recipient'], 'kontorets-privata-driftyta')
        self.assertEqual(len(result['monitor']['attempts']), 2)


if __name__ == '__main__': unittest.main()
