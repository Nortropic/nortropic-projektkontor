"""Candidate unit tests for development_result.reconcile (synthetic fixtures only).

These are candidate tests, not host acceptance. Host acceptance is the frozen
recipe VERIFICATION_RECIPE.py.
"""

import copy
import json
import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import development_result  # noqa: E402
import kontor_result  # noqa: E402


H40 = "0123456789abcdef0123456789abcdef01234567"
H40_OTHER = "fedcba9876543210fedcba9876543210fedcba98"
BASE = "a743f14970c3ff11952bf41592f05b5a5c13f986"
CANDIDATE = "1111111111111111111111111111111111111111"
MERGE = "2222222222222222222222222222222222222222"
TREE = "3333333333333333333333333333333333333333"
TASK_SHA = "a" * 64
ACCEPT_SHA = "b" * 64
OTHER_SHA = "c" * 64


def delivered_report(task_id="first"):
    return {
        "observation": "snapshot",
        "task_id": task_id,
        "phase": "completed",
        "target": "Nortropic/nortropic-projektkontor",
        "observed_at_epoch": 1758540000,
        "age_seconds": 12,
        "review_run": "review-run-1",
        "verified_delivery": True,
        "runtime_revision": H40,
        "input_revision": H40_OTHER,
        "base": BASE,
        "candidate": CANDIDATE,
        "acceptance_sha256": ACCEPT_SHA,
        "task_sha256": TASK_SHA,
        "evidence": {"pull_request": 28, "checks": ["scope", "recipe"]},
        "integration": {
            "merged": True,
            "merge_commit": MERGE,
            "tree": TREE,
            "candidate": CANDIDATE,
            "url": "https://github.com/Nortropic/nortropic-projektkontor/pull/28",
        },
    }


def goal(requirements=None, authority="owner"):
    if requirements is None:
        requirements = [
            {
                "id": "A",
                "text": "Office delivery reconciliation",
                "task": {
                    "id": "first",
                    "sha256": TASK_SHA,
                    "acceptance_sha256": ACCEPT_SHA,
                    "merge_commit": MERGE,
                },
            },
            {"id": "B", "text": "Handoff through AP08 readers", "task": None},
        ]
    return {
        "id": "office-ap11",
        "requirements": requirements,
        "next_action": {"text": "Draft B from the integrated A", "authority": authority},
    }


class ReconcileTestCase(unittest.TestCase):

    def call(self, g, reports):
        g_before = copy.deepcopy(g)
        r_before = copy.deepcopy(reports)
        result = development_result.reconcile(g, reports)
        self.assertEqual(g, g_before)
        self.assertEqual(reports, r_before)
        self.assertCommonShape(result, g)
        return result

    def assertCommonShape(self, result, g):
        self.assertEqual(
            set(result),
            {"goal_id", "live", "remote_current", "whole_goal_complete",
             "limitations", "next_action", "requirements", "unmatched_reports"})
        self.assertEqual(result["goal_id"], "office-ap11")
        self.assertIs(result["live"], False)
        self.assertIs(result["remote_current"], False)
        self.assertIs(result["whole_goal_complete"], False)
        self.assertIsInstance(result["limitations"], list)
        self.assertTrue(result["limitations"])
        self.assertTrue(all(type(s) is str and s for s in result["limitations"]))
        text = " ".join(result["limitations"]).lower()
        self.assertIn("saved", text)
        self.assertIn("live", text)
        self.assertIn("final review", text)
        self.assertEqual(result["next_action"], g["next_action"])
        self.assertIsNot(result["next_action"], g["next_action"])
        self.assertEqual([r["id"] for r in result["requirements"]],
                         [r["id"] for r in g["requirements"]])
        for entry in result["requirements"]:
            self.assertEqual(set(entry), {"id", "text", "task", "status", "result", "problems"})
            self.assertIn(entry["status"],
                          {"missing", "ambiguous", "not_supported", "delivery_supported"})
            self.assertIsInstance(entry["problems"], list)
            if entry["status"] == "delivery_supported":
                self.assertEqual(entry["problems"], [])
            else:
                self.assertTrue(entry["problems"])
        json.dumps(result, allow_nan=False)

    # T1 -------------------------------------------------------------------

    def test_positive_binding(self):
        report = delivered_report()
        result = self.call(goal(), [report])
        a, b = result["requirements"]
        self.assertEqual(a["status"], "delivery_supported")
        self.assertEqual(a["result"], kontor_result.render(report))
        self.assertEqual(a["result"]["status"], "delivered")
        self.assertEqual(a["task"], goal()["requirements"][0]["task"])
        self.assertEqual(b["status"], "missing")
        self.assertIsNone(b["result"])
        self.assertIsNone(b["task"])
        self.assertEqual(result["unmatched_reports"], [])

    def test_whole_goal_never_complete_even_when_all_supported(self):
        only_a = goal([goal()["requirements"][0]])
        result = self.call(only_a, [delivered_report()])
        self.assertEqual(result["requirements"][0]["status"], "delivery_supported")
        self.assertIs(result["whole_goal_complete"], False)

    # T2 -------------------------------------------------------------------

    def test_task_sha256_mismatch(self):
        report = delivered_report()
        report["task_sha256"] = OTHER_SHA
        a = self.call(goal(), [report])["requirements"][0]
        self.assertEqual(a["status"], "not_supported")
        self.assertTrue(any("task_sha256" in p for p in a["problems"]))
        self.assertEqual(a["result"], kontor_result.render(report))

    def test_acceptance_sha256_mismatch(self):
        report = delivered_report()
        report["acceptance_sha256"] = OTHER_SHA
        a = self.call(goal(), [report])["requirements"][0]
        self.assertEqual(a["status"], "not_supported")
        self.assertTrue(any("acceptance_sha256" in p for p in a["problems"]))

    def test_merge_commit_mismatch(self):
        report = delivered_report()
        report["integration"]["merge_commit"] = H40_OTHER
        a = self.call(goal(), [report])["requirements"][0]
        self.assertEqual(a["status"], "not_supported")
        self.assertTrue(any("merge_commit" in p for p in a["problems"]))

    def test_task_id_mismatch_is_missing_and_unmatched(self):
        report = delivered_report(task_id="other-task")
        result = self.call(goal(), [report])
        a = result["requirements"][0]
        self.assertEqual(a["status"], "missing")
        self.assertIsNone(a["result"])
        self.assertEqual(result["unmatched_reports"], ["other-task"])

    # T3 -------------------------------------------------------------------

    def assertReaderRejects(self, report, expected_fragment):
        a = self.call(goal(), [report])["requirements"][0]
        self.assertEqual(a["status"], "not_supported")
        self.assertEqual(a["result"], kontor_result.render(report))
        self.assertNotEqual(a["result"]["status"], "delivered")
        self.assertIn(expected_fragment, a["result"]["error"])

    def test_missing_review_run(self):
        report = delivered_report()
        del report["review_run"]
        self.assertReaderRejects(report, "review_run")

    def test_missing_integration(self):
        report = delivered_report()
        del report["integration"]
        self.assertReaderRejects(report, "integration")

    def test_missing_observed_at_epoch(self):
        report = delivered_report()
        del report["observed_at_epoch"]
        self.assertReaderRejects(report, "observed_at_epoch")

    def test_verified_delivery_false(self):
        report = delivered_report()
        report["verified_delivery"] = False
        self.assertReaderRejects(report, "verified_delivery")

    def test_malformed_report_item_is_not_an_error(self):
        result = self.call(goal(), [None, "text", 7, {"task_id": "first"}])
        a = result["requirements"][0]
        self.assertEqual(a["status"], "not_supported")
        self.assertEqual(result["unmatched_reports"], [None, None, None])

    # T4 -------------------------------------------------------------------

    def test_empty_report_list(self):
        result = self.call(goal(), [])
        self.assertEqual([r["status"] for r in result["requirements"]],
                         ["missing", "missing"])
        self.assertEqual(result["unmatched_reports"], [])

    def test_identical_duplicates_are_ambiguous(self):
        report = delivered_report()
        a = self.call(goal(), [report, copy.deepcopy(report)])["requirements"][0]
        self.assertEqual(a["status"], "ambiguous")
        self.assertIsNone(a["result"])

    def test_same_object_twice_is_ambiguous(self):
        report = delivered_report()
        a = self.call(goal(), [report, report])["requirements"][0]
        self.assertEqual(a["status"], "ambiguous")

    def test_differing_duplicates_are_ambiguous(self):
        good = delivered_report()
        bad = delivered_report()
        bad["task_sha256"] = OTHER_SHA
        for pair in ([good, bad], [bad, good]):
            a = self.call(goal(), pair)["requirements"][0]
            self.assertEqual(a["status"], "ambiguous")
            self.assertIsNone(a["result"])

    # T5 -------------------------------------------------------------------

    def test_authority_none_passes_through(self):
        g = goal(authority="none")
        result = self.call(g, [delivered_report()])
        self.assertEqual(result["next_action"], {"text": g["next_action"]["text"],
                                                 "authority": "none"})

    # T6 -------------------------------------------------------------------

    def test_invalid_goals_raise(self):
        base = goal()
        variants = [
            {},
            None,
            [],
            dict(base, id="other-goal"),
            dict(base, id=None),
            dict(base, requirements=[]),
            dict(base, requirements="A"),
            dict(base, requirements=[None]),
            dict(base, requirements=base["requirements"] + [base["requirements"][0]]),
            dict(base, requirements=[dict(base["requirements"][0], id="")]),
            dict(base, requirements=[dict(base["requirements"][0], id=3)]),
            dict(base, requirements=[dict(base["requirements"][0], text="")]),
            dict(base, requirements=[{"id": "A", "text": "no task key"}]),
            dict(base, requirements=[dict(base["requirements"][0], task="first")]),
            dict(base, next_action=None),
            dict(base, next_action={"text": "x"}),
            dict(base, next_action={"text": "", "authority": "owner"}),
            dict(base, next_action={"text": "x", "authority": ""}),
        ]
        for key in ("id", "requirements", "next_action"):
            missing = dict(base)
            del missing[key]
            variants.append(missing)
        for variant in variants:
            with self.subTest(variant=variant):
                with self.assertRaises(ValueError):
                    development_result.reconcile(variant, [delivered_report()])

    def test_malformed_task_hex_raises(self):
        task = goal()["requirements"][0]["task"]
        bad_tasks = [
            dict(task, id=""),
            dict(task, sha256="A" * 64),
            dict(task, sha256="a" * 63),
            dict(task, acceptance_sha256="zz" * 32),
            dict(task, merge_commit="a" * 64),
            dict(task, merge_commit="A" * 40),     # uppercase hex; MERGE is all digits, so MERGE.upper() was MERGE
            {k: v for k, v in task.items() if k != "merge_commit"},
        ]
        for bad in bad_tasks:
            with self.subTest(task=bad):
                g = goal([{"id": "A", "text": "t", "task": bad}])
                with self.assertRaises(ValueError):
                    development_result.reconcile(g, [delivered_report()])

    def test_non_list_reports_raise(self):
        for reports in (None, {}, "report", (delivered_report(),), 5):
            with self.subTest(reports=reports):
                with self.assertRaises(ValueError):
                    development_result.reconcile(goal(), reports)

    # T7 -------------------------------------------------------------------

    def test_reuses_kontor_result_render_via_module_attribute(self):
        report = delivered_report()
        with mock.patch.object(kontor_result, "render",
                               wraps=kontor_result.render) as traced:
            result = development_result.reconcile(goal(), [report])
        self.assertGreaterEqual(traced.call_count, 1)
        self.assertIs(traced.call_args[0][0], report)
        self.assertEqual(result["requirements"][0]["status"], "delivery_supported")

    def test_render_result_is_returned_unmodified(self):
        report = delivered_report()
        sentinel = {"status": "delivered", "marker": "from-stub"}
        with mock.patch.object(kontor_result, "render", return_value=sentinel):
            result = development_result.reconcile(goal(), [report])
        self.assertIs(result["requirements"][0]["result"], sentinel)
        self.assertEqual(sentinel, {"status": "delivered", "marker": "from-stub"})

    def test_inputs_not_mutated_and_result_is_fresh(self):
        g = goal()
        report = delivered_report()
        result = self.call(g, [report])
        result["next_action"]["authority"] = "changed"
        result["requirements"][0]["task"]["id"] = "changed"
        result["limitations"].append("x")
        self.assertEqual(g, goal())
        self.assertEqual(report, delivered_report())

    def test_module_has_no_cli_or_io(self):
        self.assertFalse(hasattr(development_result, "main"))
        for name in ("os", "subprocess", "socket", "ctypes", "sys", "time",
                     "logging", "open"):
            self.assertFalse(hasattr(development_result, name), name)
        self.assertIs(development_result.kontor_result, kontor_result)


if __name__ == "__main__":
    unittest.main()
