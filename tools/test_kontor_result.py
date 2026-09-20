"""Contract tests for the saved Runtime result presentation."""

import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest

from kontor_result import render


DELIVERY_FIELDS = {
    "runtime_revision", "input_revision", "base", "candidate", "merge_commit",
    "tree", "url", "acceptance_sha256", "review_run", "evidence",
}
PHASES = (
    "accepted", "running_codex", "running_claude", "reviewing", "publishing",
    "waiting_access", "waiting_diagnosis", "waiting_review",
    "waiting_publication_reconciliation",
)


def completed():
    return {
        "observation": "snapshot", "task_id": "office-result-1",
        "phase": "completed", "target": "Nortropic/nortropic-projektkontor",
        "verified_delivery": True, "observed_at_epoch": 1758390000.5,
        "age_seconds": 12, "runtime_revision": "1" * 40,
        "input_revision": "2" * 40, "base": "3" * 40,
        "candidate": "4" * 40, "acceptance_sha256": "a" * 64,
        "review_run": "review-2", "evidence": ["tests passed", {"review": "approved"}],
        "integration": {
            "merged": True, "candidate": "4" * 40, "merge_commit": "5" * 40,
            "tree": "6" * 40,
            "url": "https://github.com/Nortropic/nortropic-projektkontor/pull/17",
        },
    }


class RenderTests(unittest.TestCase):
    def assert_unavailable(self, report, diagnostic=None):
        result = render(report)
        self.assertEqual(result["observation"], "unavailable")
        self.assertEqual(result["status"], "unavailable")
        self.assertIs(result["live"], False)
        self.assertIs(result["remote_current"], False)
        self.assertTrue(result["limitations"])
        self.assertTrue(result["error"])
        self.assertFalse(DELIVERY_FIELDS.intersection(result))
        if diagnostic:
            self.assertIn(diagnostic, result["error"])
        json.dumps(result, allow_nan=False)
        return result

    def test_complete_receipt_preserves_exact_values(self):
        report = completed()
        result = render(report)
        self.assertEqual(result["status"], "delivered")
        self.assertEqual(result["observation"], "snapshot")
        for key in DELIVERY_FIELDS | {
            "task_id", "phase", "target", "observed_at_epoch", "age_seconds",
        }:
            expected = report["integration"][key] if key in {
                "merge_commit", "tree", "url",
            } else report[key]
            self.assertEqual(result[key], expected, key)
        self.assertIs(result["live"], False)
        self.assertIs(result["remote_current"], False)
        self.assertIn("saved Runtime observation", " ".join(result["limitations"]))
        self.assertEqual(json.loads(json.dumps(result, allow_nan=False)), result)

    def test_every_required_completion_field_is_required(self):
        for key in completed():
            with self.subTest(key=key):
                report = completed()
                del report[key]
                self.assert_unavailable(report, key)
        for key in completed()["integration"]:
            with self.subTest(integration_key=key):
                report = completed()
                del report["integration"][key]
                self.assert_unavailable(report, key)

    def test_flags_are_exact_booleans(self):
        for value in (False, 0, 1, "true", None, [], {}):
            for key in ("verified_delivery", "merged"):
                with self.subTest(key=key, value=value):
                    report = completed()
                    destination = report if key == "verified_delivery" else report["integration"]
                    destination[key] = value
                    self.assert_unavailable(report, key)

    def test_revision_format(self):
        fields = ("runtime_revision", "input_revision", "base", "candidate",
                  "acceptance_sha256", "merge_commit", "tree")
        for key in fields:
            length = 64 if key == "acceptance_sha256" else 40
            for value in (None, True, 123, [], "A" * length, "g" * length,
                          "a" * (length - 1), "a" * (length + 1), "a" * length + "\n"):
                with self.subTest(key=key, value=value):
                    report = completed()
                    destination = report["integration"] if key in ("merge_commit", "tree") else report
                    destination[key] = value
                    self.assert_unavailable(report, key)

    def test_wrong_target_and_candidate(self):
        report = completed()
        report["target"] = "Nortropic/another-repo"
        self.assert_unavailable(report, "target")
        report = completed()
        report["integration"]["candidate"] = "b" * 40
        self.assert_unavailable(report, "candidate")

    def test_url_must_be_exact_target_positive_pull(self):
        prefix = "https://github.com/Nortropic/nortropic-projektkontor/pull/"
        bad_urls = [prefix + suffix for suffix in ("0", "-1", "01", "1/", "1?x=2", "1#x", "1\n", "١")]
        bad_urls += [prefix.replace("https:", "http:") + "1",
                     prefix.replace("github.com", "github.com.evil.example") + "1",
                     prefix.replace("nortropic-projektkontor", "other") + "1",
                     prefix.replace("/pull/", "/issues/") + "1", None, 1]
        for url in bad_urls:
            with self.subTest(url=url):
                report = completed()
                report["integration"]["url"] = url
                self.assert_unavailable(report, "url")

    def test_timing_rejects_nonfinite_negative_and_boolean(self):
        for key in ("observed_at_epoch", "age_seconds"):
            for value in (-1, -0.01, float("nan"), float("inf"), -float("inf"),
                          True, False, "12", None, [], {}):
                with self.subTest(key=key, value=value):
                    report = completed()
                    report[key] = value
                    result = self.assert_unavailable(report, key)
                    self.assertNotIn(key, result)
            for value in (0, 0.0, 1.25, 10 ** 400):
                report = completed()
                report[key] = value
                self.assertEqual(render(report)["status"], "delivered")

    def test_noncompleted_phases_preserve_waiting_without_delivery(self):
        for phase in PHASES:
            with self.subTest(phase=phase):
                report = completed()
                report.update(phase=phase, verified_delivery=False,
                              state={"waiting_reason": "Waiting for access"})
                result = render(report)
                self.assertEqual(result["status"], "not_delivered")
                self.assertEqual(result["observation"], "snapshot")
                self.assertEqual(result["waiting_reason"], "Waiting for access")
                self.assertFalse(DELIVERY_FIELDS.intersection(result))
        for reason in ("", "Diagnosis saved", None, 42, []):
            report = {"observation": "snapshot", "phase": "waiting_diagnosis",
                      "state": {"waiting_reason": reason}}
            result = render(report)
            self.assertEqual(result["status"], "not_delivered")
            self.assertEqual("waiting_reason" in result, type(reason) is str)

    def test_unknown_and_malformed_observations(self):
        for report in (None, [], "snapshot", 1, {}, {"observation": "snapshot"}):
            with self.subTest(report=report):
                self.assert_unavailable(report)
        for field, values in {
            "observation": (None, [], {}, "live", "unavailable"),
            "phase": (None, [], {}, "unknown", "COMPLETED"),
            "task_id": (None, [], {}, "", "  "),
            "review_run": (None, [], {}, "", "  "),
            "integration": (None, [], "merged", True),
        }.items():
            for value in values:
                with self.subTest(field=field, value=value):
                    report = completed()
                    report[field] = value
                    self.assert_unavailable(report)
        self.assert_unavailable({"observation": "snapshot", "phase": "accepted", "state": []})

    def test_evidence_is_nonempty_json_data(self):
        cycle = []
        cycle.append(cycle)
        for value in (None, "", "  ", [], {}, 1, True, object(), cycle,
                      [float("nan")], {1: "bad key"}, [object()]):
            with self.subTest(value_type=type(value)):
                report = completed()
                report["evidence"] = value
                self.assert_unavailable(report, "evidence")
        for value in ("receipt.json", ["receipt.json"], {"tests": {"passed": True}}):
            report = completed()
            report["evidence"] = value
            self.assertEqual(render(report)["evidence"], value)

    def test_diagnostics_survive_unavailability(self):
        report = completed()
        report.update(observation="unavailable", verified_delivery=False,
                      error="Receipt could not be read", missing_evidence=["review.json"])
        del report["evidence"]
        result = self.assert_unavailable(report, "Receipt could not be read")
        self.assertIn("evidence", result["error"])
        self.assertEqual(result["missing_evidence"], ["review.json"])

    def test_input_is_unchanged_and_output_is_detached(self):
        report = completed()
        report["missing_evidence"] = []
        before = copy.deepcopy(report)
        result = render(report)
        self.assertEqual(report, before)
        result["evidence"][1]["review"] = "changed"
        result["missing_evidence"].append("changed")
        self.assertEqual(report, before)
        self.assertEqual(render(report), render(report))

    def test_import_and_render_have_no_external_io(self):
        # Preload the same modules as the host before auditing execution.
        source = Path(__file__).with_name("kontor_result.py").read_text()
        program = '''
import copy, io, json, math, os, pathlib, re, sys, types
def audit(event, args):
    if event == "open" or event.startswith(("os.", "socket.", "subprocess.", "ctypes.")):
        raise AssertionError("External access: " + event)
sys.addaudithook(audit)
namespace = {}
exec(compile(SOURCE, "kontor_result.py", "exec"), namespace)
report = REPORT
before = copy.deepcopy(report)
result = namespace["render"](report)
assert result["status"] == "delivered"
assert report == before
json.dumps(result, allow_nan=False)
for value in (None, {}, {"observation": "snapshot", "phase": "accepted"}):
    json.dumps(namespace["render"](value), allow_nan=False)
'''.replace("SOURCE", repr(source)).replace("REPORT", repr(completed()))
        process = subprocess.run([sys.executable, "-B", "-c", program],
                                 capture_output=True, text=True, timeout=20)
        self.assertEqual(process.returncode, 0, process.stderr)


if __name__ == "__main__":
    unittest.main()
