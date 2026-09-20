"""Synthetic AP05 contract tests; all temporary files stay under .scratch."""

import copy
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

import change_assessment as assessment


def synthetic_case():
    """Labels and repeated-digit hashes are invented bindings, not real evidence."""
    return {
        "schema": 1, "id": "synthetic-example", "created_at": "2026-01-02T09:00:00Z",
        "sources": [
            {"id": "design", "title": "Synthetic design", "version": "draft-1",
             "path": "z/design.txt", "sha256": "1" * 64, "size": 10},
            {"id": "budget", "title": "Synthetic budget", "version": "draft-2",
             "path": "a/budget.txt", "sha256": "2" * 64, "size": 0},
            {"id": "permission", "title": "Synthetic permission", "version": "record-1",
             "path": "m/permission.txt", "sha256": "3" * 64, "size": 30},
        ],
        "claims": [
            {"id": "chosen", "kind": "decision", "text": "Use the synthetic design.",
             "reason": "The synthetic example records this choice.",
             "standing": "  Authored decision remains in force.  ", "sources": ["design"]},
            {"id": "cost", "kind": "fact", "text": "The synthetic budget lists zero units.",
             "reason": "Recorded in the selected synthetic budget.",
             "standing": "Reported as fact by the author.", "sources": ["budget"]},
            {"id": "feasible", "kind": "judgment", "text": "The synthetic option seems feasible.",
             "reason": "The author considered these two sources.",
             "standing": "Tentative judgment.", "sources": ["budget", "design"]},
            {"id": "format", "kind": "fact", "text": "The design is a text example.",
             "reason": "The synthetic design label says so.",
             "standing": "Authored statement.", "sources": ["design"]},
        ],
        "actions": [
            {"id": "build", "text": "Build a synthetic prototype.",
             "reason": "Exercise the selected design.", "claims": ["chosen", "feasible"],
             "authority": {"status": "granted", "scope": "Synthetic prototype only.",
                           "sources": ["permission"]}},
            {"id": "inspect", "text": "Inspect the synthetic budget.",
             "reason": "Review the recorded amount.", "claims": ["cost"],
             "authority": {"status": "not_established", "scope": "No grant established.",
                           "sources": []}},
        ],
        "next_action": "build",
    }


def synthetic_check(case, overrides=None, omitted=()):
    overrides = overrides or {}
    files = [{"path": source["path"], "status": overrides.get(source["id"], "ok")}
             for source in case["sources"] if source["id"] not in omitted]
    return {"checked_at": "2026-01-02T10:00:00+00:00",
            "manifest": assessment.reference_manifest(case),
            "result": {"ok": all(entry["status"] == "ok" for entry in files), "files": files}}


def replace_at(obj, path, value):
    for key in path[:-1]:
        obj = obj[key]
    obj[path[-1]] = value


class AssessmentTests(unittest.TestCase):
    def setUp(self):
        self.case = synthetic_case()
        self.check = synthetic_check(self.case)

    def test_exact_manifest_and_legitimate_report(self):
        expected = {"version": 1, "files": [
            {"path": "a/budget.txt", "sha256": "2" * 64, "size": 0},
            {"path": "m/permission.txt", "sha256": "3" * 64, "size": 30},
            {"path": "z/design.txt", "sha256": "1" * 64, "size": 10},
        ]}
        self.assertEqual(assessment.reference_manifest(self.case), expected)
        report = assessment.assess(self.case, self.check)
        self.assertEqual(set(report), {
            "schema", "case_id", "created_at", "checked_at", "structure_valid", "source_checks",
            "coverage", "facts", "judgments", "decisions", "actions", "next_action", "limitations",
        })
        self.assertEqual(report["source_checks"], [
            {"id": ref, "status": "ok"} for ref in ("design", "budget", "permission")])
        self.assertEqual(report["coverage"], {
            "checked": ["design", "budget", "permission"], "not_checked": [], "complete_search": False})
        self.assertEqual([claim["id"] for claim in report["facts"]], ["cost", "format"])
        self.assertEqual(report["case_id"], self.case["id"])
        self.assertEqual(report["created_at"], self.case["created_at"])
        self.assertEqual(report["checked_at"], self.check["checked_at"])
        self.assertIs(report["structure_valid"], True)
        originals = {item["id"]: item for item in self.case["claims"] + self.case["actions"]}
        for item in report["facts"] + report["judgments"] + report["decisions"] + report["actions"]:
            self.assertEqual(item["source_check"], "unchanged")
            self.assertEqual(item["affected_sources"], [])
            self.assertEqual({key: item[key] for key in originals[item["id"]]}, originals[item["id"]])
            self.assertEqual(set(item), set(originals[item["id"]]) | {"source_check", "affected_sources"})
        self.assertEqual(report["next_action"], report["actions"][0])
        self.assertEqual(json.loads(json.dumps(report)), report)
        limitations = " ".join(report["limitations"]).lower()
        for phrase in ("neither substantive approval nor authority", "exhaustive", "current knowledge",
                       "not_checked", "reassessment", "revocation", "supplied judgments",
                       "not independently authenticated", "timestamps", "new files", "predecessor"):
            self.assertIn(phrase, limitations)

    def test_scoped_propagation_for_each_non_ok_status(self):
        for status in ("changed", "missing", "unsafe", "not_checked"):
            with self.subTest(status=status):
                check = (synthetic_check(self.case, omitted=("design",)) if status == "not_checked"
                         else synthetic_check(self.case, {"design": status}))
                report = assessment.assess(self.case, check)
                self.assertEqual(report["source_checks"][0], {"id": "design", "status": status})
                for item in (report["decisions"][0], report["judgments"][0], report["facts"][1],
                             report["actions"][0], report["next_action"]):
                    self.assertEqual(item["affected_sources"], ["design"])
                    self.assertEqual(item["source_check"], "needs_reassessment")
                for item in (report["facts"][0], report["actions"][1]):
                    self.assertEqual(item["affected_sources"], [])
                    self.assertEqual(item["source_check"], "unchanged")
                self.assertEqual(report["decisions"][0]["standing"], self.case["claims"][0]["standing"])
                self.assertEqual(report["actions"][0]["authority"], self.case["actions"][0]["authority"])

    def test_authority_only_change_and_unestablished_authority(self):
        report = assessment.assess(self.case, synthetic_check(self.case, {"permission": "changed"}))
        self.assertEqual(report["actions"][0]["affected_sources"], ["permission"])
        self.assertEqual(report["actions"][0]["authority"]["status"], "granted")
        for group in ("facts", "judgments", "decisions"):
            self.assertTrue(all(item["source_check"] == "unchanged" for item in report[group]))
        for status in ("not_granted", "not_established"):
            self.case["actions"][1]["authority"]["status"] = status
            report = assessment.assess(self.case, self.check)
            self.assertEqual(report["actions"][1]["authority"]["status"], status)
            self.assertEqual(report["actions"][1]["source_check"], "unchanged")

    def test_dependency_union_order_subset_and_chosen_action(self):
        self.case["actions"][0]["authority"]["sources"] = ["permission", "budget"]
        report = assessment.assess(self.case, synthetic_check(self.case, omitted=("design", "budget", "permission")))
        self.assertEqual(report["actions"][0]["affected_sources"], ["design", "budget", "permission"])
        self.assertEqual(report["judgments"][0]["affected_sources"], ["budget", "design"])
        self.assertEqual(report["coverage"], {
            "checked": [], "not_checked": ["design", "budget", "permission"], "complete_search": False})
        self.case["next_action"] = "inspect"
        check = synthetic_check(self.case, omitted=("design",))
        check["result"]["files"].reverse()
        report = assessment.assess(self.case, check)
        self.assertEqual(report["next_action"], report["actions"][1])
        self.assertEqual(report["coverage"]["checked"], ["budget", "permission"])

    def test_inputs_and_expected_bindings_are_immutable(self):
        original_case, original_check = copy.deepcopy(self.case), copy.deepcopy(self.check)
        assessment.assess(self.case, self.check)
        changed = synthetic_check(self.case, {"budget": "changed"})
        report = assessment.assess(self.case, changed)
        manifest = assessment.reference_manifest(self.case)
        manifest["files"][0]["sha256"] = "9" * 64
        report["judgments"][0]["sources"].append("invented")
        report["next_action"]["authority"]["sources"].clear()
        report["actions"][0]["claims"].clear()
        self.assertEqual(self.case, original_case)
        self.assertEqual(self.check, original_check)
        self.assertEqual(assessment.reference_manifest(self.case), original_check["manifest"])
        invalid = copy.deepcopy(changed)
        invalid["result"]["ok"] = True
        snapshot = copy.deepcopy(invalid)
        with self.assertRaises(ValueError):
            assessment.assess(self.case, invalid)
        self.assertEqual(invalid, snapshot)

    def test_invalid_case_values_rejected_by_both_apis(self):
        changes = [
            (("schema",), value) for value in (True, 1.0, "1", 2, None)
        ] + [
            (("sources", 0, "path"), value) for value in
            ("/absolute", "C:relative", "d:/drive", "a\\b", "a\x00b", "a//b", "a/./b",
             "a/../b", "../a", "./a", "a/", "", "a/budget.txt")
        ] + [
            (("sources", 0, "sha256"), value) for value in ("A" * 64, "1" * 63, "g" * 64, 123, None)
        ] + [
            (("sources", 0, "size"), value) for value in (-1, True, 0.0, "0", None)
        ] + [
            (("created_at",), value) for value in
            ("2026-02-30T09:00:00Z", "2026-01-02", "2026-01-02T09:00:00", "today",
             "2026-01-02T25:00:00Z", "2026-01-02T09:00:00+00:99", "2026-01-02X09:00:00Z")
        ] + [
            (("id",), " "), (("sources",), []), (("claims",), []), (("actions",), []),
            (("sources",), {}), (("claims", 0, "id"), []), (("claims", 0, "id"), "cost"),
            (("sources", 0, "id"), "budget"), (("actions", 0, "id"), "inspect"),
            (("sources", 0, "title"), ""), (("sources", 0, "version"), None),
            (("claims", 0, "kind"), "opinion"), (("claims", 0, "kind"), []),
            (("claims", 0, "text"), ""), (("claims", 0, "standing"), ""),
            (("claims", 0, "reason"), "  "), (("actions", 0, "reason"), None),
            (("actions", 0, "text"), ""), (("claims", 0, "sources"), []),
            (("claims", 0, "sources"), ["unknown"]), (("claims", 0, "sources"), ["design", "design"]),
            (("claims", 0, "sources"), [{}]), (("claims", 0, "sources"), "design"),
            (("actions", 0, "claims"), []), (("actions", 0, "claims"), ["unknown"]),
            (("actions", 0, "claims"), ["chosen", "chosen"]), (("actions", 0, "authority"), []),
            (("actions", 0, "authority", "status"), "approved"),
            (("actions", 0, "authority", "scope"), ""),
            (("actions", 0, "authority", "sources"), []),
            (("actions", 0, "authority", "sources"), ["unknown"]),
            (("actions", 0, "authority", "sources"), ["permission", "permission"]),
            (("next_action",), "unknown"), (("next_action",), []),
        ]
        for path, value in changes:
            with self.subTest(path=path, value=value):
                case = copy.deepcopy(self.case)
                replace_at(case, path, value)
                before = copy.deepcopy(case)
                with self.assertRaises(ValueError):
                    assessment.reference_manifest(case)
                with self.assertRaises(ValueError):
                    assessment.assess(case, self.check)
                self.assertEqual(case, before)
        for value in (None, [], "case", 1):
            with self.assertRaises(ValueError):
                assessment.reference_manifest(value)

    def test_exact_keys_at_every_object(self):
        case_objects = [(), ("sources", 0), ("claims", 0), ("actions", 0), ("actions", 0, "authority")]
        check_objects = [(), ("manifest",), ("manifest", "files", 0), ("result",), ("result", "files", 0)]
        for kind, paths in (("case", case_objects), ("check", check_objects)):
            for path in paths:
                original = self.case if kind == "case" else self.check
                obj = original
                for key in path:
                    obj = obj[key]
                for key in [None] + list(obj):
                    with self.subTest(kind=kind, path=path, missing=key):
                        modified = copy.deepcopy(original)
                        target = modified
                        for component in path:
                            target = target[component]
                        if key is None:
                            target["extra"] = "not allowed"
                        else:
                            del target[key]
                        if kind == "case":
                            with self.assertRaises(ValueError):
                                assessment.reference_manifest(modified)
                            with self.assertRaises(ValueError):
                                assessment.assess(modified, self.check)
                        else:
                            with self.assertRaises(ValueError):
                                assessment.assess(self.case, modified)

    def test_invalid_check_bindings_statuses_and_timestamps(self):
        changes = [
            (("checked_at",), "2026-01-02T08:59:59Z"), (("checked_at",), "2026-02-30T10:00:00Z"),
            (("checked_at",), "2026-01-02T10:00:00"), (("checked_at",), None),
            (("manifest", "version"), True), (("manifest", "version"), 1.0),
            (("manifest", "files", 0, "size"), True), (("manifest", "files", 0, "size"), 0.0),
            (("manifest", "files", 0, "sha256"), "9" * 64),
            (("manifest", "files", 0, "path"), "other.txt"),
            (("manifest", "files"), list(reversed(self.check["manifest"]["files"]))),
            (("manifest", "files"), self.check["manifest"]["files"][:-1]),
            (("manifest", "files"), {}), (("result", "ok"), False), (("result", "ok"), 1),
            (("result", "files"), None),
            (("result", "files"), self.check["result"]["files"] * 2),
            (("result", "files", 0, "path"), "unknown.txt"),
            (("result", "files", 0, "path"), []),
            (("result", "files", 0, "status"), "not_checked"),
            (("result", "files", 0, "status"), []),
            (("result", "files", 0, "status"), "changed"),
        ]
        for path, value in changes:
            with self.subTest(path=path, value=value):
                check = copy.deepcopy(self.check)
                replace_at(check, path, value)
                with self.assertRaises(ValueError):
                    assessment.assess(self.case, check)
        for value in (None, [], 0):
            with self.assertRaises(ValueError):
                assessment.assess(self.case, value)
        empty = synthetic_check(self.case, omitted=("design", "budget", "permission"))
        empty["result"]["ok"] = False
        with self.assertRaises(ValueError):
            assessment.assess(self.case, empty)

    def test_calendar_offsets_and_same_instant(self):
        self.case["created_at"] = "2024-02-29T09:00:00.125+02:00"
        self.check["checked_at"] = "2024-02-29T07:00:00.125Z"
        assessment.assess(self.case, self.check)
        self.check["checked_at"] = "2024-02-29T08:00:00+02:00"
        with self.assertRaises(ValueError):
            assessment.assess(self.case, self.check)

    def test_iso8601_calendar_forms_in_both_timestamp_fields(self):
        # All representations denote the same instant, including the review's
        # compact date and compact offset regressions, independently in each field.
        forms = (
            "2026-01-02T09:00:00Z", "20260102T090000Z",
            "2026-01-02T09:00:00+0000", "20260102T090000+0000",
            "20260102T09:00:00Z", "2026-01-02T090000Z",
            "2026-01-02T10:30:00+0130", "20260102T033000-0530",
            "2026-01-02T10:00:00+01", "20260102T0900Z",
            "2026-01-02T09Z", "20260102T090000,000Z",
        )
        expected = assessment.reference_manifest(self.case)
        for created_at in forms:
            for checked_at in forms:
                with self.subTest(created_at=created_at, checked_at=checked_at):
                    self.case["created_at"] = created_at
                    self.check["checked_at"] = checked_at
                    self.assertEqual(assessment.reference_manifest(self.case), expected)
                    report = assessment.assess(self.case, self.check)
                    self.assertEqual(report["created_at"], created_at)
                    self.assertEqual(report["checked_at"], checked_at)

    def test_compact_timestamps_reject_invalid_values_and_earlier_checks(self):
        for timestamp in (
            "20260230T090000Z", "20260102T250000Z", "20260102T090000",
            "20260102T090000+0099", "20260102T090000-0160",
            "20260102T090000+2400", "20260102X090000Z",
        ):
            with self.subTest(timestamp=timestamp):
                case = copy.deepcopy(self.case)
                case["created_at"] = timestamp
                with self.assertRaises(ValueError):
                    assessment.reference_manifest(case)
                with self.assertRaises(ValueError):
                    assessment.assess(case, self.check)
                check = copy.deepcopy(self.check)
                check["checked_at"] = timestamp
                with self.assertRaises(ValueError):
                    assessment.assess(self.case, check)
        self.case["created_at"] = "20260102T090000Z"
        self.check["checked_at"] = "2026-01-02T09:59:59+0100"
        with self.assertRaises(ValueError):
            assessment.assess(self.case, self.check)

    def test_fractional_units_equal_instants_in_both_fields(self):
        groups = (
            ("2026-01-02T09.5Z", "20260102T09,5Z", "2026-01-02T09:30:00Z",
             "20260102T1030+0100", "2026-01-02T04.5-05"),
            ("2026-01-02T09:30.5Z", "20260102T0930,5Z", "2026-01-02T09:30:30Z",
             "20260102T1500.5+0530", "2026-01-02T04:30:30-0500"),
            ("2026-01-02T09.000000001Z", "20260102T090000.0000036Z",
             "2026-01-02T10:00:00.0000036000+01"),
            ("2026-01-02T09:30.000000001Z", "20260102T093000.00000006Z"),
        )
        for forms in groups:
            for created in forms:
                for checked in forms:
                    with self.subTest(created=created, checked=checked):
                        self.case["created_at"] = created
                        self.check["checked_at"] = checked
                        report = assessment.assess(self.case, self.check)
                        self.assertTrue(report["structure_valid"])
                        self.assertEqual(report["created_at"], created)
                        self.assertEqual(report["checked_at"], checked)

    def test_fractional_units_reject_earlier_instants_exactly(self):
        pairs = (
            ("2026-01-02T09.5Z", "2026-01-02T09:15:00Z"),
            ("2026-01-02T09:30.5Z", "2026-01-02T09:30:15Z"),
            ("20260102T09,5Z", "20260102T101500+0100"),
            ("20260102T0930,5Z", "20260102T150029+0530"),
            ("2026-01-02T00.5+01", "20260101T232959Z"),
            ("2026-01-02T09.000000001Z", "2026-01-02T09:00:00.0000035999999999Z"),
            ("2026-01-02T09:30.000000001Z", "2026-01-02T10:30:00.0000000599999999+01"),
            ("2026-01-02T09:30:00.123456789012345679Z",
             "2026-01-02T09:30:00.123456789012345678Z"),
            ("2026-01-02T09:30:00." + "0" * 4500 + "1Z", "2026-01-02T09:30:00Z"),
        )
        for later, earlier in pairs:
            with self.subTest(later=later, earlier=earlier):
                self.case["created_at"] = later
                self.check["checked_at"] = earlier
                with self.assertRaisesRegex(ValueError, "cannot precede"):
                    assessment.assess(self.case, self.check)
                self.case["created_at"] = earlier
                self.check["checked_at"] = later
                self.assertTrue(assessment.assess(self.case, self.check)["structure_valid"])

    def test_pure_import_and_calls_without_io(self):
        # A fresh process preloads only the host's allowed dependencies. Compile
        # before installing the audit guard so module loading itself is measured.
        script = r'''
import argparse, copy, datetime, io, json, math, os, pathlib, re, sys, types
code = compile(pathlib.Path(sys.argv[1]).read_text(), "assessment-under-test", "exec")
case, check = json.loads(sys.stdin.read())
module = types.ModuleType("pure_assessment")
events = []
def forbidden(*args, **kwargs):
    events.append("filesystem metadata access")
    raise AssertionError("Unexpected filesystem metadata access")
# These metadata operations do not all emit Python audit events.
os.stat = os.lstat = os.access = os.readlink = os.getcwd = forbidden
def guard(event, args):
    if (event == "open" or event.startswith(("os.", "socket.", "subprocess.", "ctypes."))):
        events.append(event)
        raise AssertionError("Unexpected I/O: " + event)
sys.addaudithook(guard)
output = io.StringIO()
sys.stdout = output
sys.stderr = output
exec(code, module.__dict__)
manifest = module.reference_manifest(case)
report = module.assess(case, check)
assert manifest == check["manifest"]
assert report["structure_valid"] is True
try:
    module.assess({}, check)
except ValueError:
    pass
else:
    raise AssertionError("Invalid case accepted")
assert output.getvalue() == "", "Pure calls printed output"
assert events == [], events
'''
        result = subprocess.run(
            [sys.executable, "-B", "-c", script, str(Path(assessment.__file__).resolve())],
            input=json.dumps([self.case, self.check]), capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")


class CLITests(unittest.TestCase):
    def setUp(self):
        scratch = Path(__file__).resolve().parents[1] / ".scratch"
        scratch.mkdir(exist_ok=True)
        self.directory = tempfile.TemporaryDirectory(prefix="synthetic-ap05-", dir=scratch)
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.case = synthetic_case()
        self.case_file = self.root / "case.json"
        self.check_file = self.root / "check.json"
        self.case_file.write_text(json.dumps(self.case), encoding="utf-8")
        self.check_file.write_text(json.dumps(synthetic_check(self.case)), encoding="utf-8")

    def cli(self, *args):
        result = subprocess.run([sys.executable, "-B", assessment.__file__, *map(str, args)],
                                capture_output=True, text=True, timeout=20)
        self.assertEqual(result.stderr, "")
        self.assertEqual(len(result.stdout.splitlines()), 1)
        data = json.loads(result.stdout)
        self.assertIsInstance(data, dict)
        if result.returncode == 2:
            self.assertTrue(data["error"])
        return result.returncode, data

    def test_valid_commands_and_mismatch_return_zero_without_writes(self):
        before = {p.name: p.read_bytes() for p in self.root.iterdir()}
        code, manifest = self.cli("manifest", self.case_file)
        self.assertEqual(code, 0)
        self.assertEqual(manifest, assessment.reference_manifest(self.case))
        code, report = self.cli("report", self.case_file, self.check_file)
        self.assertEqual(code, 0)
        self.assertEqual(report, assessment.assess(self.case, synthetic_check(self.case)))
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.root.iterdir()})
        for status in ("changed", "missing", "unsafe", "not_checked"):
            check = (synthetic_check(self.case, omitted=("design",)) if status == "not_checked"
                     else synthetic_check(self.case, {"design": status}))
            self.check_file.write_text(json.dumps(check), encoding="utf-8")
            self.assertEqual(self.cli("report", self.case_file, self.check_file)[0], 0)

    def test_duplicate_keys_and_non_json_constants_in_either_input(self):
        valid_case = json.dumps(self.case)
        valid_check = json.dumps(synthetic_check(self.case))
        cases = [valid_case.replace('"schema": 1', '"schema": 1, "schema": 1'),
                 valid_case.replace('"size": 10', '"size": 10, "size": 10')]
        cases.extend(valid_case.replace('"size": 10', '"size": ' + value)
                     for value in ("NaN", "Infinity", "-Infinity", "1e999"))
        for payload in cases:
            with self.subTest(payload=payload):
                self.case_file.write_text(payload, encoding="utf-8")
                self.assertEqual(self.cli("manifest", self.case_file)[0], 2)
        self.case_file.write_text(valid_case, encoding="utf-8")
        for payload in (valid_check.replace('"ok": true', '"ok": true, "ok": true'),
                        valid_check.replace('"ok": true', '"ok": NaN')):
            self.check_file.write_text(payload, encoding="utf-8")
            self.assertEqual(self.cli("report", self.case_file, self.check_file)[0], 2)

    def test_usage_unreadable_and_malformed_json(self):
        for args in ((), ("--help",), ("other", self.case_file), ("manifest",),
                     ("manifest", self.case_file, self.check_file), ("report", self.case_file),
                     ("manifest", self.root / "missing.json"), ("manifest", self.root)):
            with self.subTest(args=args):
                self.assertEqual(self.cli(*args)[0], 2)
        for payload in (b"{", b"[]", b"null", b"{} {}", b"\xff"):
            self.case_file.write_bytes(payload)
            self.assertEqual(self.cli("manifest", self.case_file)[0], 2)

    def test_cli_only_opens_requested_inputs_for_reading(self):
        actual_open = open
        allowed = {str(self.case_file), str(self.check_file)}
        reads = []

        def read_only(path, mode="r", **kwargs):
            self.assertIn(str(path), allowed)
            self.assertEqual(mode, "r")
            reads.append(str(path))
            return actual_open(path, mode, **kwargs)

        with mock.patch("builtins.open", side_effect=read_only), mock.patch("sys.stdout", new_callable=io.StringIO) as out:
            self.assertEqual(assessment.main(["report", str(self.case_file), str(self.check_file)]), 0)
        self.assertEqual(reads, [str(self.case_file), str(self.check_file)])
        self.assertTrue(json.loads(out.getvalue())["structure_valid"])

    def test_documented_host_recipe_with_synthetic_verifier_observations(self):
        document = Path(assessment.__file__).with_name("CHANGE_ASSESSMENT.md").read_text(encoding="utf-8")
        recipe = document.split("```python\n", 1)[1].split("\n```", 1)[0]
        source_root = self.root / "synthetic-sources"
        source_root.mkdir()
        # A common root spans synthetic campaign and office files. The output
        # is authorized inside the office, while every selected file is retained.
        selected = {}
        for source, path in zip(self.case["sources"],
                                ("campaign/design.txt", "office/budget.txt", "office/permission.txt")):
            source["path"] = path
            target = source_root / path
            target.parent.mkdir(exist_ok=True)
            target.write_text("Synthetic source: " + source["id"], encoding="utf-8")
            selected[target] = (target.read_bytes(), target.stat().st_mtime_ns)
        self.case_file.write_text(json.dumps(self.case), encoding="utf-8")
        # Exercise the documented command and stdin transport with a synthetic
        # CLI fixture. It never reads sources or implements a second hasher.
        verifier = self.root / "synthetic_evidence_index.py"
        verifier.write_text('''
import json
import os
import sys
assert sys.flags.dont_write_bytecode
assert sys.argv[1:] == ["verify", os.environ["AP05_SOURCE_ROOT"]]
assert json.loads(sys.stdin.read()) == json.loads(os.environ["AP05_TEST_MANIFEST"])
print(os.environ["AP05_TEST_STDOUT"])
sys.exit(int(os.environ["AP05_TEST_EXIT"]))
''', encoding="utf-8")
        mismatched = synthetic_check(self.case, {"permission": "changed"})["result"]
        scenarios = [
            (0, json.dumps({"ok": True, "files": []}), True),
            (1, json.dumps(mismatched), True),
            (2, json.dumps({"ok": True, "files": []}), False),
            (1, json.dumps({"ok": True, "files": []}), False),
            (0, json.dumps(mismatched), False),
            (2, json.dumps({"error": "Synthetic unavailable measurement"}), False),
            (0, "not JSON", False),
        ]
        original = self.case_file.read_bytes()
        for number, (exit_code, stdout, available) in enumerate(scenarios * 2):
            with self.subTest(exit_code=exit_code, stdout=stdout):
                output_parent = self.root if number < len(scenarios) else source_root / "office"
                output = output_parent / ("comparison-" + str(number))
                env = dict(os.environ, AP05_CASE=str(self.case_file),
                           AP05_SOURCE_ROOT=str(source_root), AP05_OUTPUT=str(output),
                           AP05_VERIFIER=str(verifier),
                           AP05_TEST_MANIFEST=json.dumps(assessment.reference_manifest(self.case)),
                           AP05_TEST_STDOUT=stdout, AP05_TEST_EXIT=str(exit_code))
                result = subprocess.run([sys.executable, "-B", "-c", recipe], env=env,
                                        cwd=Path(__file__).resolve().parents[1],
                                        capture_output=True, text=True, timeout=20)
                self.assertEqual(result.returncode, 0 if available else 1, result.stderr)
                self.assertEqual(json.loads((output / "manifest.json").read_text()),
                                 assessment.reference_manifest(self.case))
                observed = json.loads((output / "verifier-observation.json").read_text())
                self.assertEqual(observed["exit_code"], exit_code)
                self.assertEqual(observed["stdout"], stdout + "\n")
                self.assertEqual(observed["stderr"], "")
                self.assertEqual((output / "check.json").exists(), available)
                self.assertEqual((output / "report.json").exists(), available)
                self.assertEqual((output / "unavailable.json").exists(), not available)
                if available:
                    check = json.loads((output / "check.json").read_text())
                    self.assertEqual(check["manifest"], assessment.reference_manifest(self.case))
                    self.assertEqual(check["result"], json.loads(stdout))
                    report = json.loads((output / "report.json").read_text())
                    if exit_code == 1:
                        self.assertEqual(report["actions"][0]["affected_sources"], ["permission"])
                    else:
                        self.assertEqual(report["coverage"]["not_checked"],
                                         ["design", "budget", "permission"])
                # A second invocation cannot reuse a directory or overwrite its
                # artifacts, even after an unavailable observation.
                artifacts = {p.name: p.read_bytes() for p in output.iterdir()}
                repeated = subprocess.run([sys.executable, "-B", "-c", recipe], env=env,
                                          cwd=Path(__file__).resolve().parents[1],
                                          capture_output=True, text=True, timeout=20)
                self.assertNotEqual(repeated.returncode, 0)
                self.assertEqual(artifacts, {p.name: p.read_bytes() for p in output.iterdir()})
        self.assertEqual(self.case_file.read_bytes(), original)
        self.assertEqual(selected, {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in selected})

        # Even a missing selected file must not become a new report artifact.
        collision = source_root / "office" / "pending"
        collision_case = copy.deepcopy(self.case)
        collision_case["sources"][0]["path"] = "office/pending/report.json"
        collision_file = self.root / "collision-case.json"
        collision_file.write_text(json.dumps(collision_case), encoding="utf-8")
        env.update(AP05_CASE=str(collision_file), AP05_OUTPUT=str(collision))
        rejected = subprocess.run([sys.executable, "-B", "-c", recipe], env=env,
                                  cwd=Path(__file__).resolve().parents[1],
                                  capture_output=True, text=True, timeout=20)
        self.assertNotEqual(rejected.returncode, 0)
        self.assertFalse(collision.exists())
        self.assertEqual(selected, {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in selected})


if __name__ == "__main__":
    unittest.main()
