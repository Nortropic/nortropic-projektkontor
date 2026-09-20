import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
import kontor


class EntryTests(unittest.TestCase):
    def test_status_never_starts_worker_or_sends_signal(self):
        with patch.object(kontor, 'selected_task', return_value=(Path('tasks/x.json'), {'id':'x'})), patch.object(kontor, 'observation', return_value={'observation':'snapshot','live':False}) as read, patch.object(kontor.subprocess, 'run', side_effect=AssertionError('Mutation from read')), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(kontor.main(['status']), 0)
            read.assert_called_once()
            with self.assertRaises(SystemExit):kontor.main(['status','--diagnosis','anything'])
    def test_only_continuation_forwards_diagnosed_signal(self):
        with patch.object(kontor, 'selected_task', return_value=(Path('tasks/x.json'), {'id':'x'})), patch.object(kontor.subprocess, 'run') as run:
            run.return_value.returncode=1
            self.assertEqual(kontor.main(['fortsatt','--review-retry','New evidence']),1)
            command=run.call_args.args[0]
            self.assertIn('--resume',command)
            self.assertEqual(command[-2:],['--review-retry','New evidence'])
    def test_selection_rejects_wrong_target_traversal_and_symlink(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(kontor,'OFFICE',Path(directory)):
            (Path(directory)/'tasks').mkdir()
            (Path(directory)/'tasks/x.json').write_text(json.dumps({'target':'other/repo'}))
            for name in ('../x.json','/tmp/x.json','x.json'):
                with self.assertRaises(ValueError):kontor.selected_task(name)
            (Path(directory)/'tasks/link.json').symlink_to('x.json')
            with self.assertRaises(ValueError):kontor.selected_task('link.json')
