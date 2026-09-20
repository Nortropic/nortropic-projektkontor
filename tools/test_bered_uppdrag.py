"""Synthetic endpoint fixtures only; no host tasks, acceptance or private sources."""

import contextlib
import io
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

import assignment_preparation
import bered_uppdrag
import change_assessment


REPO = Path(__file__).resolve().parents[1]
CLI = REPO / "tools" / "bered_uppdrag.py"
SCRATCH = REPO / ".scratch"


def fixture():
    """All bindings and observations are invented, including repeated-digit hashes."""
    source = {"id": "S1", "title": "Synthetic source", "version": "synthetic-v1",
              "path": "selected.txt", "sha256": "1" * 64, "size": 10}
    case = {
        "schema": 1, "id": "synthetic-case", "created_at": "2026-01-01T00:00:00Z",
        "sources": [source],
        "claims": [{"id": "C1", "kind": "decision", "text": "Synthetic choice",
                    "reason": "Exercise preparation", "standing": "Recorded synthetic choice",
                    "sources": ["S1"]}],
        "actions": [{"id": "A1", "text": "Prepare a synthetic task",
                     "reason": "Exercise the endpoint", "claims": ["C1"],
                     "authority": {"status": "granted", "scope": "Synthetic preparation only",
                                   "sources": ["S1"]}}],
        "next_action": "A1",
    }
    check = {"checked_at": "2026-01-02T00:00:00Z",
             "manifest": change_assessment.reference_manifest(case),
             "result": {"ok": True, "files": [{"path": source["path"], "status": "ok"}]} }
    ref = {"id": "REF1", "source": "S1", "version": "synthetic-v1", "quote": "Synthetic quote"}
    spec = {
        "schema": 1, "action": "A1", "references": [ref],
        "reference_checks": [dict(ref, sha256=source["sha256"], status="matched")],
        "requirements": [{"id": "R1", "text": "Return a synthetic value",
                          "reason": "Demonstrate a bounded task", "claims": ["C1"],
                          "references": ["REF1"], "tests": ["T1"]}],
        "tests": [{"id": "T1", "observable": "Synthetic input returns the expected value",
                   "method": "Compare the endpoint response with the expected fixture"}],
        "export": {"title": "Synthetic worker", "context": [
            {"kind": kind, "text": "Synthetic " + kind}
            for kind in ("fact", "judgment", "decision", "authority")],
            "scope": ["Implement the synthetic worker"],
            "limitations": ["Invented bindings; no real authority or measurement"]},
        "task": {"id": "synthetic-worker", "target": "Nortropic/nortropic-projektkontor",
                 "base": "a" * 40, "runtime_revision": "b" * 40,
                 "allowed_paths": ["tools/synthetic_worker.py"], "attempt_seconds": 120,
                 "automatic_retries": 0,
                 "steps": [{"provider": "codex", "prompt": "Implement the synthetic worker"}],
                 "acceptance": "acceptance/synthetic.py", "acceptance_sha256": "c" * 64,
                 "brief": "tasks/synthetic.md"},
    }
    return case, check, spec


def write_fixture(directory):
    """Create a NEW synthetic example directory; parent must already exist."""
    directory = Path(directory)
    directory.mkdir(mode=0o700)
    (directory / "sources").mkdir()
    (directory / "sources" / "selected.txt").write_text("synthetic\n", encoding="utf-8")
    values = fixture()
    for name, value in zip(("case", "check", "spec"), values):
        with (directory / (name + ".json")).open("x", encoding="utf-8") as stream:
            json.dump(value, stream)
    return values


class EndpointTests(unittest.TestCase):
    def setUp(self):
        SCRATCH.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix="bered-", dir=SCRATCH)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.inputs = self.root / "inputs"
        self.case, self.check, self.spec = write_fixture(self.inputs)
        self.paths = [self.inputs / (name + ".json") for name in ("case", "check", "spec")]
        self.sources = self.inputs / "sources"
        self.output = self.root / "bundle"

    def save(self):
        for path, value in zip(self.paths, (self.case, self.check, self.spec)):
            path.write_text(json.dumps(value), encoding="utf-8")

    def args(self, output=None):
        return [str(p) for p in self.paths] + ["--source-root", str(self.sources),
                                               "--output", str(output or self.output)]

    def run_cli(self, output=None, prefix=None):
        command = prefix or [sys.executable, "-B", str(CLI)]
        return subprocess.run(command + self.args(output), cwd=REPO, capture_output=True,
                              text=True, timeout=20, check=False)

    def assert_error(self, result):
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertEqual(result.stderr, "")
        self.assertEqual(json.loads(result.stdout), bered_uppdrag.ERROR)
        self.assertEqual(len(result.stdout.splitlines()), 1)

    def change_source(self, path, status="missing"):
        self.case["sources"][0]["path"] = path
        self.check["manifest"] = change_assessment.reference_manifest(self.case)
        self.check["result"] = {"ok": status == "ok", "files": [{"path": path, "status": status}]}
        self.save()

    def test_exact_core_output_modes_and_unchanged_inputs(self):
        protected = self.paths + [self.sources / "selected.txt"]
        before = {p: p.read_bytes() for p in protected}
        # Even an unusually restrictive umask must result in exactly 0700/0600.
        prefix = [sys.executable, "-B", "-c",
                  "import os,runpy,sys; os.umask(0o777); "
                  "sys.argv=sys.argv[1:]; sys.path.insert(0,os.path.dirname(sys.argv[0])); "
                  "runpy.run_path(sys.argv[0],run_name='__main__')", str(CLI)]
        result = self.run_cli(prefix=prefix)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stderr, "")
        expected = assignment_preparation.prepare(self.case, self.check, self.spec)
        self.assertEqual(json.loads(result.stdout), {
            "status": "draft", "mechanical_complete": True, "gaps": [],
            "files": list(bered_uppdrag.FILES)})
        for name, content in (("private.json", expected["private"]),
                              ("package.json", expected["package"]),
                              ("task.draft.json", expected["package"]["task_draft"])):
            self.assertEqual(json.loads((self.output / name).read_text()), content)
        self.assertEqual((self.output / "brief.draft.md").read_text(), expected["package"]["brief"])
        self.assertEqual(set(p.name for p in self.output.iterdir()), set(bered_uppdrag.FILES))
        self.assertEqual(stat.S_IMODE(self.output.stat().st_mode), 0o700)
        for path in self.output.iterdir():
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
        self.assertEqual(before, {p: p.read_bytes() for p in protected})

    def test_existing_bundle_is_immutable(self):
        self.assertEqual(self.run_cli().returncode, 0)
        before = {p: (p.read_bytes(), p.stat().st_mode, p.stat().st_mtime_ns)
                  for p in self.output.iterdir()}
        self.assert_error(self.run_cli())
        self.assertEqual(before, {p: (p.read_bytes(), p.stat().st_mode, p.stat().st_mtime_ns)
                                  for p in self.output.iterdir()})

    def test_missing_source_and_incomplete_spec_are_drafts(self):
        (self.sources / "selected.txt").unlink()
        self.change_source("selected.txt")
        self.spec["task"] = {}
        self.save()
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        summary = json.loads(result.stdout)
        self.assertEqual(summary["status"], "draft")
        self.assertFalse(summary["mechanical_complete"])
        self.assertIn("reference_source_needs_reassessment", {g["code"] for g in summary["gaps"]})
        self.assertFalse((self.sources / "selected.txt").exists())
        self.assertIn("DRAFT", (self.output / "brief.draft.md").read_text())

    def test_bad_json_all_three_inputs_is_generic_and_creates_nothing(self):
        invalid = ['{"secret":"DO-NOT-ECHO",', '{"secret":1,"secret":2}',
                   '{"nested":{"secret":1,"secret":2}}', 'NaN', 'Infinity', '-Infinity',
                   '1e999', 'null', '[]', '"DO-NOT-ECHO"', '{"schema":true}']
        for path in self.paths:
            original = path.read_bytes()
            for content in invalid:
                with self.subTest(input=path.name, content=content):
                    path.write_text(content)
                    self.assert_error(self.run_cli())
                    self.assertFalse(self.output.exists())
            path.write_bytes(b'\xffDO-NOT-ECHO')
            self.assert_error(self.run_cli())
            path.write_bytes(original)

    def test_unreadable_nonregular_and_symlink_inputs(self):
        for i in range(3):
            original = self.paths[i]
            for name in ("absent-secret.json", "directory-secret.json", "link-secret.json", "fifo-secret"):
                path = self.root / (str(i) + name)
                if name.startswith("directory"):
                    path.mkdir()
                elif name.startswith("link"):
                    path.symlink_to(original)
                elif name.startswith("fifo"):
                    os.mkfifo(path)
                self.paths[i] = path
                self.assert_error(self.run_cli())
                self.assertFalse(self.output.exists())
            self.paths[i] = original
        if os.geteuid() != 0:
            self.paths[0].chmod(0)
            try:
                self.assert_error(self.run_cli())
            finally:
                self.paths[0].chmod(0o600)

    def test_source_collisions_both_directions_and_case_aliases(self):
        for source, output in (("future", "future"), ("future/leaf", "future"),
                               ("future", "future/child"), ("FUTURE/leaf", "future"),
                               ("FUTURE", "future/child"), ("FUTURE", "future")):
            with self.subTest(source=source, output=output):
                self.change_source(source)
                self.assert_error(self.run_cli(self.sources / output))
                self.assertFalse((self.sources / "future").exists())
                self.assertFalse((self.sources / "FUTURE").exists())
        # A selected path that exists as a directory must remain untouched too.
        (self.sources / "future").mkdir()
        self.change_source("FUTURE")
        self.assert_error(self.run_cli(self.sources / "future" / "child"))
        self.assertEqual(list((self.sources / "future").iterdir()), [])

    def test_input_collisions_both_directions_and_case_aliases(self):
        before = {p: p.read_bytes() for p in self.paths}
        for path in self.paths:
            for output in (path, path.parent, path / "child", path.with_name(path.name.upper()),
                           path.with_name(path.name.upper()) / "child"):
                self.assert_error(self.run_cli(output))
        self.assertEqual(before, {p: p.read_bytes() for p in self.paths})

    def test_symlink_outputs_ancestors_and_resolved_source_aliases(self):
        link = self.root / "output-link"
        link.symlink_to(self.output)
        self.assert_error(self.run_cli(link))
        self.assertFalse(self.output.exists())
        alias = self.root / "alias"
        alias.symlink_to(self.sources, target_is_directory=True)
        self.assert_error(self.run_cli(alias / "new"))
        self.assert_error(self.run_cli(alias / ".." / "new"))
        self.assertFalse((self.sources / "new").exists())
        # The selected source's symlink targets a not-yet-existing output.
        (self.sources / "source-link").symlink_to(self.output / "leaf")
        self.change_source("source-link")
        self.assert_error(self.run_cli())
        self.assertFalse(self.output.exists())
        self.change_source("selected.txt", "ok")
        self.sources = alias
        self.assert_error(self.run_cli(alias.resolve() / "SELECTED.TXT"))

    def test_missing_parent_is_not_created_and_sibling_prefix_is_allowed(self):
        self.assert_error(self.run_cli(self.root / "absent" / "bundle"))
        self.assertFalse((self.root / "absent").exists())
        self.change_source("future/leaf")
        self.assertEqual(self.run_cli(self.sources / "future-other").returncode, 0)
        self.assertFalse((self.sources / "future").exists())

    def test_partial_failure_is_preserved_and_not_reused(self):
        original_open = os.open

        def fail_second(path, *args, **kwargs):
            if Path(path).name == "package.json":
                raise OSError("DO-NOT-ECHO partial failure")
            return original_open(path, *args, **kwargs)

        stdout, stderr = io.StringIO(), io.StringIO()
        with mock.patch.object(bered_uppdrag.os, "open", side_effect=fail_second), \
                contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = bered_uppdrag.main(self.args())
        self.assertEqual(code, 2)
        self.assertEqual(json.loads(stdout.getvalue()), bered_uppdrag.ERROR)
        self.assertEqual(stderr.getvalue(), "")
        self.assertEqual([p.name for p in self.output.iterdir()], ["private.json"])
        before = (self.output / "private.json").read_bytes()
        self.assert_error(self.run_cli())
        self.assertEqual((self.output / "private.json").read_bytes(), before)

    def test_invalid_arguments_do_not_echo_paths(self):
        result = subprocess.run([sys.executable, "-B", str(CLI), "--DO-NOT-ECHO"],
                                capture_output=True, text=True, timeout=20)
        self.assert_error(result)

    def test_no_execution_network_or_source_reads(self):
        script = '''import os, runpy, sys
cli, source_root = sys.argv[1:3]
sys.argv = [cli] + sys.argv[3:]
sys.path.insert(0, os.path.dirname(cli))
def audit(event, args):
    if event.startswith(('subprocess.', 'socket.', 'ctypes.', 'os.exec', 'os.spawn')) or event in ('os.system', 'os.fork', 'os.posix_spawn'):
        raise RuntimeError('Forbidden execution')
    if event == 'open' and isinstance(args[0], str) and os.path.commonpath([os.path.abspath(args[0]), source_root]) == source_root:
        raise RuntimeError('Forbidden source read')
sys.addaudithook(audit)
runpy.run_path(cli, run_name='__main__')
'''
        protected = [REPO / "tools" / name for name in
                     ("assignment_preparation.py", "change_assessment.py", "kontor.py")]
        before = {p: p.read_bytes() for p in protected}
        prefix = [sys.executable, "-B", "-c", script, str(CLI), str(self.sources)]
        result = self.run_cli(prefix=prefix)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stderr, "")
        self.assertEqual(before, {p: p.read_bytes() for p in protected})


if __name__ == "__main__":
    unittest.main()
