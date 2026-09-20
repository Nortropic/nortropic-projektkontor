# AP06 host technical continuation: corrected probe, same CLI scope

AP06-ACCEPT covers this technical continuation. It may execute only after separately
recorded review and frozen host inputs. The prior office-assignment-cli-1 remains
preserved at waiting_diagnosis because its host probe changed normal script-import
semantics. Do not resume or change that verifier. No change of goal or authority.
The corrected verifier restores the controlled CLI directory to sys.path before
its isolated audited run; all sandbox/audit assertions and core bindings remain.

The generated draft below is retained verbatim. DRAFT labels describe mechanical
output, not the host's eventual reviewed/frozen task. R1-R7 are unchanged. Use the
qualified /opt/homebrew/bin/python3.12. Retained Runtime-authored reference files
follow the draft; restore them exactly unless a concrete R1-R7 violation is found.
They passed 12 candidate endpoint tests and the corrected diagnostic host probe,
but are NOT approved/integrated; this task requires fresh full tests and review.
Do not change product imports merely to work around the superseded host launcher.

---

# DRAFT — AP06 remaining task: private assignment preparation CLI

DRAFT only. Mechanical completeness is neither acceptance nor authority; this tool grants no permission and does not authenticate AP06-ACCEPT.

## Context

### Fact

- The core tools/assignment_preparation.py and its schema documentation are delivered on the exact task base; read them. AP05 is available read-only.
- The first CLI attempt stopped at an erroneous host import launcher. This separately frozen technical continuation preserves that failed task and corrects only host startup context. Retained Runtime-authored source is supplied as unapproved reference, not as acceptance evidence.

### Judgment

- The host chose a thin file interface and source-collision checks to make existing preparation usable without a second execution engine.

### Decision

- AP06 authorizes core first, then this real CLI task using it; earlier phases and map delivery remain closed.

### Authority

- Host reviewed/frozen task permits only the three listed tools files, synthetic tests and method. No Runtime/source/vault/host authority changes. Content-review all code/docs/test summaries before publication; no private data or absolute local paths.

## Scope

- Implement R1-R7 within the three listed files.
- tools/assignment_preparation.py, tools/change_assessment.py and tools/kontor.py are read-only.
- The host separately reviews and freezes acceptance; the worker must not generate or activate host acceptance.
- Reuse the three retained reference files supplied by the host; change only a concrete requirement defect, not the accepted scope or active core.

## Derived requirements

### R1

Thin private preparation command: Expose prepare(CASE,CHECK,SPEC) through: python3 -B tools/bered_uppdrag.py CASE CHECK SPEC --source-root ROOT --output NEWDIR. Read strict JSON, call the delivered core; no new assessment logic.

Reason: Derived bounded CLI work required to complete AP06 using the delivered core; host substantive choices are separately reviewed.

Tests: T1

### R2

Immutable private bundle: Create NEWDIR exclusively, mode0700, with private.json, package.json, task.draft.json, brief.draft.md as exclusive0600 files. Parent must already exist. Existing output refused unchanged; preserve partial output on failure for diagnosis.

Reason: Derived bounded CLI work required to complete AP06 using the delivered core; host substantive choices are separately reviewed.

Tests: T2

### R3

No source or input mutation: Before any mkdir refuse symlink output or ancestors and all overlap directions between output and three input files plus selected case source paths under ROOT, including missing sources. Use resolved paths and casefold for Mac aliases. Do not create missing output ancestors. Reject symlink JSON inputs. Trusted local use, no claim of hostile concurrent-filesystem safety.

Reason: Derived bounded CLI work required to complete AP06 using the delivered core; host substantive choices are separately reviewed.

Tests: T3

### R4

Explicit drafts and safe failures: Well-formed incomplete input writes marked draft, exit0. Malformed/duplicate-key/non-JSON constants or unreadable inputs return exit2 with one generic JSON error, no raw private input or path in stdout or stderr. Stdout success has status=draft, mechanical_complete, gaps and file names. No ready/approved/authorized assertion.

Reason: Derived bounded CLI work required to complete AP06 using the delivered core; host substantive choices are separately reviewed.

Tests: T4

### R5

One engine, no activation: CLI does not hash or remeasure sources, refresh references, execute acceptance, start Runtime, signal, invoke models or publish. Do not edit tools/assignment_preparation.py, change_assessment.py, kontor.py, host tasks or acceptance.

Reason: Derived bounded CLI work required to complete AP06 using the delivered core; host substantive choices are separately reviewed.

Tests: T5

### R6

Usable method and endpoint examples: Write tools/BERED_UPPDRAG.md with complete reproducible synthetic example (or documented fixture in tools/test_bered_uppdrag.py), exact CLI command, AP05 measurement recipe pointer, host lookup/quote observations, real later decision IDs, explicit export review, immutable versions, host review/freezing and actual Runtime format. Explain meaning/verification adequacy remain host judgments. Clarify that the authorized chain driver and separate reviewer perform substantive review; the earlier core-method wording human substantive review creates no new owner gate. Only genuine goal/cost/authority changes return to owner. Use ignored evidence/**/local/ for real bundles and .scratch for isolated tests; arbitrary output path is not automatically private.

Reason: Derived bounded CLI work required to complete AP06 using the delivered core; host substantive choices are separately reviewed.

Tests: T6

### R7

Candidate endpoint regression: Add tools/test_bered_uppdrag.py with synthetic legitimate and negative CLI fixtures; reuse delivered core API instead of changing it. Include case aliases and source collisions in both directions; scope tests to this command.

Reason: Derived bounded CLI work required to complete AP06 using the delivered core; host substantive choices are separately reviewed.

Tests: T7

## Verification

### T1

Observable: Output exactly matches core private/package/task_draft/brief for a complete synthetic input; input bytes remain unchanged.

Method: Frozen host subprocess test compares actual CLI output files with core API.

### T2

Observable: Repeated output path returns exit2 without changing any existing byte; fresh directory/files have required modes.

Method: Host endpoint tests inspect modes and before/after bytes.

### T3

Observable: Equal/ancestor/descendant source and input collisions, symlink alias, absent parent all fail with no new source/output; separate output with missing selected source works.

Method: Isolated fixtures only; test negative paths and verify source remains missing. No original mutations.

### T4

Observable: Missing source creates gaps and stays draft; malformed/duplicate/NaN inputs create no bundle and report generic error without fixture secrets.

Method: Frozen host and candidate CLI tests exercise these cases.

### T5

Observable: Audited actual CLI invocation succeeds while process/network/ctypes execution are forbidden; active core hashes unchanged.

Method: Native host endpoint invocation with audit hook, exact core hash comparison, Runtime file grants and separate code review.

### T6

Observable: Fresh reader can reproduce legitimate and negative examples without private sources; no private or fictitiously accessible worker dependencies.

Method: Run documented synthetic example and independent method/content review.

### T7

Observable: Endpoint suite passes and demonstrates required behaviors against actual command.

Method: python3 -B -m unittest discover -s tools -p test_bered_uppdrag.py plus frozen host acceptance and independent Runtime review.

## Gaps

No mechanical gaps detected. Still DRAFT; host review is required.

## Limitations

- DRAFT only. Mechanical completeness is neither acceptance nor authority; this tool grants no permission and does not authenticate AP06-ACCEPT.
- Selected-source-only comparison at the supplied checked_at: no assurance of freshness or exhaustive discovery of later or relevant sources.
- Reference checks are host-supplied observations, not authenticated evidence. No sources, quotes, links or source hashes are independently verified here.
- Changed dependencies require reassessment, not automatic falsehood or revocation of recorded decisions or authority.
- Host review must assess requirements, contradictions, mandates and the substantive adequacy of test observables; nonempty text is not proof.
- Export review is required for every authored field, including IDs, reasons, test methods and task values. No string checker proves privacy or public safety.
- The host must use Runtime's actual validator, review and freeze file bytes, and obtain independent review and protected integration. This draft neither generates nor executes acceptance and never invokes Runtime.
- The preparation result is always a draft, never substantive approval, permission or evidence of complete source discovery.
- Sources and lookup observations are host-supplied; timestamps describe the supplied comparison only.
- Agent judgment selects requirements, authority scope, adequate observables and export content; no measured time saving is claimed.
- This exported brief is self-contained together with files on the accepted base. No private references must be fetched.

## Retained unapproved Runtime candidate reference

AP06-REFERENCE-BEGIN tools/bered_uppdrag.py
#!/usr/bin/env python3
"""Private file interface to the delivered preparation core; always a draft."""

import argparse
import json
import math
import os
from pathlib import Path
import stat
import sys

import assignment_preparation


FILES = ("private.json", "package.json", "task.draft.json", "brief.draft.md")
ERROR = {"error": "Preparation failed: invalid command, input, or output."}


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        # argparse's normal diagnostics echo arguments, which may be private.
        raise ValueError("invalid command")


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate key")
        result[key] = value
    return result


def _reject_constant(value):
    raise ValueError("non-JSON constant")


def _finite_float(value):
    number = float(value)
    if not math.isfinite(number):
        raise ValueError("nonfinite number")
    return number


def _read_json(path):
    if path.is_symlink() or not stat.S_ISREG(path.stat().st_mode):
        raise ValueError("input must be a regular non-symlink file")
    with path.open(encoding="utf-8") as stream:
        return json.load(stream, object_pairs_hook=_unique_object,
                         parse_constant=_reject_constant, parse_float=_finite_float)


def _path_keys(path):
    # Keep lexical aliases too: resolving a selected symlink must not discard
    # protection of its own name. Missing tails are deliberately retained.
    return {tuple(part.casefold() for part in variant.parts)
            for variant in (path.absolute(), path.resolve(strict=False))}


def _overlaps(left, right):
    return any(a[:len(b)] == b or b[:len(a)] == a
               for a in _path_keys(left) for b in _path_keys(right))


def _check_output(output, inputs, case, source_root):
    absolute = output.absolute()
    # Check before resolve, so symlink/../new cannot conceal a symlink ancestor.
    if any(path.is_symlink() for path in (absolute, *absolute.parents)):
        raise ValueError("symlink output or ancestor")
    if output.exists() or not output.parent.is_dir():
        raise ValueError("output exists or parent is absent")
    protected = list(inputs) + [source_root / s["path"] for s in case["sources"]]
    if any(_overlaps(output, path) for path in protected):
        raise ValueError("output overlaps selected input or source")


def _json_bytes(value):
    return (json.dumps(value, ensure_ascii=True, allow_nan=False, indent=2)
            + "\n").encode("utf-8")


def _write_bundle(output, contents):
    # No parents=True, cleanup, replacement or retry: preserve any partial bundle.
    output.mkdir(mode=0o700)
    output.chmod(0o700)
    for name, content in zip(FILES, contents):
        descriptor = os.open(output / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            os.fchmod(descriptor, 0o600)
            with os.fdopen(descriptor, "wb", closefd=False) as stream:
                stream.write(content)
        finally:
            os.close(descriptor)


def main(argv=None):
    parser = _Parser(prog="bered_uppdrag.py", allow_abbrev=False,
                     description=__doc__)
    parser.add_argument("case", type=Path)
    parser.add_argument("check", type=Path)
    parser.add_argument("spec", type=Path)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    try:
        args = parser.parse_args(argv)
        inputs = (args.case, args.check, args.spec)
        case, check, spec = (_read_json(path) for path in inputs)
        result = assignment_preparation.prepare(case, check, spec)
        _check_output(args.output, inputs, case, args.source_root)
        package = result["package"]
        # Serialize everything before mkdir, including UTF-8 validation of prose.
        contents = (_json_bytes(result["private"]), _json_bytes(package),
                    _json_bytes(package["task_draft"]), package["brief"].encode("utf-8"))
        summary = json.dumps({"status": "draft",
                              "mechanical_complete": result["mechanical_complete"],
                              "gaps": result["gaps"], "files": list(FILES)},
                             ensure_ascii=True, allow_nan=False)
        _write_bundle(args.output, contents)
    except (ValueError, OSError, TypeError, RuntimeError, OverflowError):
        print(json.dumps(ERROR))
        return 2
    print(summary)
    return 0


if __name__ == "__main__":
    sys.exit(main())
AP06-REFERENCE-END tools/bered_uppdrag.py

AP06-REFERENCE-BEGIN tools/test_bered_uppdrag.py
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
AP06-REFERENCE-END tools/test_bered_uppdrag.py

AP06-REFERENCE-BEGIN tools/BERED_UPPDRAG.md
# AP06: private assignment preparation command

From the office repository root:

```sh
python3 -B tools/bered_uppdrag.py CASE CHECK SPEC --source-root ROOT --output NEWDIR
```

The command reads three strict UTF-8 JSON files and calls the delivered
`assignment_preparation.prepare(case, check, spec)` once. The schemas and output
fields are defined in [ASSIGNMENT_PREPARATION.md](ASSIGNMENT_PREPARATION.md).
AP05 assessment is reused without new assessment logic. ROOT locates selected
case source paths for collision checks only: it is not scanned, hashed or measured.
Source contents are never opened. The command does not refresh expected hashes,
fetch references, generate or execute acceptance, invoke Runtime or models,
signal processes, or publish anything.

NEWDIR's parent must already exist. The command creates NEWDIR exclusively with
mode `0700` and these exclusive files with mode `0600`:

| File | Exact core value retained |
| --- | --- |
| `private.json` | `private`, including all inputs and traces |
| `package.json` | `package` |
| `task.draft.json` | `package.task_draft` |
| `brief.draft.md` | `package.brief`, as UTF-8 text |

JSON values are retained without new fields; JSON formatting is not input byte
preservation. Input file bytes remain unchanged. No predecessor is overwritten.
Any existing output is refused unchanged. A failed write leaves partial output
for diagnosis; that directory cannot be reused. Preserve it and choose a new
version only after diagnosing the failure. A partial directory is not a completed
bundle. Permissions restrict access but do not encrypt or prevent owner edits.

Before any mkdir, the command rejects output symlinks, symlink ancestors, missing
parents and equality/containment in either direction with any input or selected
source path, including missing sources. Comparisons use resolved paths and
casefolded path components to protect Mac aliases; lexical source names are also
protected when a source resolves through a symlink. Input JSON symlinks and
nonregular files are rejected. The source root itself is not a selected source:
an unrelated output beneath a broad root is permitted. These checks support
trusted local use, not hostile concurrent filesystem replacement.

Exit `0` emits one stdout JSON object with `status: "draft"`,
`mechanical_complete`, `gaps` and the four file names. Structurally valid but
incomplete inputs still produce a marked draft and exit `0`. The command relies
on supplied source observations: a missing file produces gaps when CHECK records
it as missing, not through a new filesystem measurement. Even a complete draft
is neither approved nor authorized. Stdout gap subjects contain authored public
IDs and must be treated as potential disclosure too.

Exit `2` emits exactly one generic JSON error on stdout, with no exception,
private text or input/output path echoed to stdout or stderr. This includes
malformed JSON, duplicate keys at any depth, NaN/Infinity, nonfinite parsed
numbers, invalid schema, unreadable inputs, invalid arguments and output failures.
`--help` displays static usage. There is no acceptance or execution mode.

## Reproducible synthetic example

The complete `fixture()` and `write_fixture()` in
[test_bered_uppdrag.py](test_bered_uppdrag.py) contain invented source metadata,
quotes, decisions, observations and Runtime bindings. Repeated-character hashes
are synthetic data, not measurements. No private source or host acceptance is
needed. Use an installed Python interpreter; the qualified environment uses
Python 3.12. Run these commands from the repository root, starting with an absent
`.scratch/bered-example-v1`:

```sh
mkdir -p .scratch
python3 -B - <<'PY'
import sys
from pathlib import Path
sys.path.insert(0, "tools")
from test_bered_uppdrag import write_fixture
write_fixture(Path(".scratch/bered-example-v1"))
PY
python3 -B tools/bered_uppdrag.py \
  .scratch/bered-example-v1/case.json \
  .scratch/bered-example-v1/check.json \
  .scratch/bered-example-v1/spec.json \
  --source-root .scratch/bered-example-v1/sources \
  --output .scratch/bered-example-v1/bundle-v1
```

Expect exit `0`, `status: "draft"`, `mechanical_complete: true`, empty gaps and
four files. The suite compares each file's content directly with the core API.
Repeat the exact CLI command to observe exit `2` and unchanged bundle bytes.

For a missing-source draft and a refused source collision, retain those inputs
and author a new synthetic version:

```sh
python3 -B - <<'PY'
import json
import sys
from pathlib import Path
sys.path.insert(0, "tools")
from test_bered_uppdrag import write_fixture
root = Path(".scratch/bered-missing-v1")
case, check, spec = write_fixture(root)
(root / "sources" / "selected.txt").unlink()  # Synthetic fixture only.
check["result"] = {"ok": False, "files": [{"path": "selected.txt", "status": "missing"}]}
with (root / "check-missing.json").open("x", encoding="utf-8") as stream:
    json.dump(check, stream)
PY
python3 -B tools/bered_uppdrag.py \
  .scratch/bered-missing-v1/case.json \
  .scratch/bered-missing-v1/check-missing.json \
  .scratch/bered-missing-v1/spec.json \
  --source-root .scratch/bered-missing-v1/sources \
  --output .scratch/bered-missing-v1/bundle-v1
python3 -B tools/bered_uppdrag.py \
  .scratch/bered-missing-v1/case.json \
  .scratch/bered-missing-v1/check-missing.json \
  .scratch/bered-missing-v1/spec.json \
  --source-root .scratch/bered-missing-v1/sources \
  --output .scratch/bered-missing-v1/sources/selected.txt
```

The first command exits `0` with reassessment gaps and mechanical completeness
false. The second exits `2` before mkdir; the selected source stays missing.
Other endpoint regressions cover case aliases, both containment directions,
symlinks, missing parents, unreadable inputs, duplicate keys, malformed JSON,
private error markers, exact modes under a restrictive umask, preserved partial
output, and absence of process/network/source-content access.

Runtime runs the candidate suite and its separate frozen acceptance:

```sh
python3 -B -m unittest discover -s tools -p test_bered_uppdrag.py -v
```

Tests allocate isolated temporary fixtures under `.scratch` and remove their own
temporary directories. Manual example versions are retained. Never use the test
fixture builder on real source material. Synthetic test success does not establish
real source observations, independent approval or protected integration.

## Host preparation and review

1. The authorized chain driver selects the actual case, action and source
   versions within AP06. Preserve previous cases and observations. Read the real
   later decisions and record their **actual decision IDs**, source versions and
   scoped effects in the private case/reference trace; do not manufacture IDs,
   substitute a draft label for acceptance, or treat old choices as new authority.
   AP06-ACCEPT is the accepted host mandate referred to by this task, not a record
   authenticated by the compiler. Historical I-11 and FINAL-CHECK-1 retain their
   own scope; they do not authorize a new map delivery. Private later decision
   records must be looked up by the host, never fetched by the worker candidate.
2. Follow [the AP05 measurement recipe](CHANGE_ASSESSMENT.md#host-recipe-existing-runtime-verifier-unchanged-bindings)
   outside the candidate sandbox. It uses the existing Runtime evidence_index
   verifier with the unchanged reference manifest on stdin and wraps the real
   result with `checked_at`. Exit `1` is mismatch data; exit `2`, launch failure
   or invalid output is unavailable measurement, never invented success. This
   CLI accepts the resulting CASE/CHECK; it does not perform that measurement.
3. Use the host's existing lookup/quote tools to check each selected reference.
   Record the actual lookup ID, selected source/version, expected SHA-256 and
   exact quote in SPEC; supply a bound `matched`, `mismatch` or `not_checked`
   observation. Do not assert `matched` because the text fields are nonempty.
   These remain host observations, not authenticated evidence from this tool.
4. Author requirements, reasons, claim/reference dependencies, tests and export
   context. Keep fact, judgment, decision and handlingsspecifik befogenhet
   (action-specific authority) distinct. The authorized chain driver and separate
   reviewer assess meaning, contradictions, mandate scope and verification
   adequacy. The earlier core-method phrase “human substantive review” creates
   no new owner gate: these authorized agents perform substantive review. Only
   genuine goal, cost or authority changes return to the owner.
5. Keep real inputs and bundles in an authorized, ignored `evidence/**/local/`
   location. Ensure the existing parent is private and confirm Git ignores the
   chosen path before writing. An arbitrary `--output` path is not automatically
   private; `.scratch` is for synthetic isolated tests, not real evidence.
   Use a new directory for every version and retain predecessor relationships in
   host records. Changes trigger scoped reassessment, not automatic reversal of
   decisions or authority. Unchanged selected sources prove neither exhaustive
   discovery of later sources nor freshness beyond the supplied comparison.
6. Review every export field before moving anything into publication or a worker
   task: requirement/test IDs, prose, reasons, methods, gaps, task values, prompts,
   paths and limitations. Package field selection is not sanitization. Summaries
   can disclose private information. Never export `private.json`, raw private
   inputs, source collections or raw sessions. Review the code, method and test
   summaries as well. No string filter proves publication safety.

## From reviewed draft to Runtime

The CLI leaves a draft only. The host supplies the actual task bindings; it does
not ask this command to invent a task, acceptance module, digest or permission.
The actual office Runtime format uses exactly the following supplied fields:

| Field | Host binding |
| --- | --- |
| `id`, `target` | Actual task ID and `Nortropic/nortropic-projektkontor` |
| `base`, `runtime_revision` | Actual full 40-character revisions |
| `allowed_paths` | Explicit permitted `tools/` files |
| `attempt_seconds`, `automatic_retries` | Accepted per-attempt seconds and zero automatic retries |
| `steps` | Objects with `provider: "codex"` and the reviewed `prompt` |
| `acceptance`, `acceptance_sha256` | Host-controlled `acceptance/` module and its actual 64-character digest |
| `brief` | Reviewed brief under `tasks/` |

See the existing [method task](../tasks/andringsbedomning-metod.json) for a real
format example, not an instruction to restart that completed task. Synthetic
fixture revisions and hashes must never be used as actual host bindings.

The host uses Runtime's actual validator, obtains independent review and freezes
the reviewed task/brief/acceptance bytes in committed inputs through the existing
route. Frozen acceptance and the active execution path stay outside candidate
write access. After that host review/freezing, the office interface is
`python3 -B tools/kontor.py start --task NAME.json`, where NAME.json is the actual
accepted file directly under `tasks/`. It hands execution to the existing
`runtime.run` route. This is a host endpoint description, not a step performed
by preparation or by the synthetic example. No synthetic task should be started.

Runtime owns tests, independent review and protected integration of the exact
candidate, and the host retains their real evidence. Preparation does not assert
those gates passed and grants no source access, host authority or publication
rights. No Runtime, core, acceptance, host task or source changes belong to this
three-file CLI implementation.
AP06-REFERENCE-END tools/BERED_UPPDRAG.md
