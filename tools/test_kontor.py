"""Kontorets ingång: granskningstiden för en fortsatt granskning (RUNTIME-GRANSKNINGSBUDGET-ACCEPT-20260925).

Ingången bygger bara Runtimes kommando; Runtime prövar själv gränserna 180-900 sekunder. Inget körs här: Runtimes
anrop ersätts av en inspelning.
"""
import contextlib
import io
from pathlib import Path
import unittest
from unittest import mock

import kontor

TASK = {'id': 'office-x', 'target': 'Nortropic/nortropic-projektkontor'}


class GranskningstidTests(unittest.TestCase):
    def entry(self, argv):
        calls = []

        def record(command, **options):
            calls.append(command)
            return mock.Mock(returncode=0)
        with mock.patch.object(kontor, 'selected_task', return_value=(Path('/kontor/tasks/x.json'), TASK)), \
             mock.patch.object(kontor.subprocess, 'run', side_effect=record):
            code = kontor.main(argv)
        return code, calls

    def test_granskningstiden_foljer_med_till_runtimes_fortsattning(self):
        code, (command,) = self.entry(['fortsatt', '--task', 'x.json', '--review-retry', 'skäl', '--granskningstid', '720'])
        self.assertEqual(code, 0)
        self.assertEqual(command[3:], ['runtime.run', '/kontor/tasks/x.json', '--resume', '--review-retry', 'skäl',
                                       '--review-seconds', '720'])

    def test_utan_granskningstid_ar_kommandot_som_forut(self):
        _, (command,) = self.entry(['fortsatt', '--task', 'x.json', '--review-retry', 'skäl'])
        self.assertEqual(command[3:], ['runtime.run', '/kontor/tasks/x.json', '--resume', '--review-retry', 'skäl'])
        _, (command,) = self.entry(['start', '--task', 'x.json'])
        self.assertEqual(command[3:], ['runtime.run', '/kontor/tasks/x.json'])

    def test_granskningstid_hor_bara_till_fortsatt_granskning(self):
        for argv in (['start', '--granskningstid', '720'], ['fortsatt', '--granskningstid', '720'],
                     ['fortsatt', '--review-repair', 'x', '--granskningstid', '720'],
                     ['status', '--granskningstid', '720']):
            with self.subTest(argv=argv), contextlib.redirect_stderr(io.StringIO()), \
                 mock.patch.object(kontor.subprocess, 'run') as started, self.assertRaises(SystemExit) as refused:
                kontor.main(argv)
            self.assertEqual(refused.exception.code, 2)
            started.assert_not_called()


if __name__ == '__main__':
    unittest.main()
