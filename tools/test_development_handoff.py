"""Unit tests for the AP11 handoff connection, on synthetic fixtures only."""

import copy
import datetime as dt
import os
import re
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import agarbild
import development_handoff
import development_result


EPOCH = 1700000000
LATE_EPOCH = 1900000000
TASK_SHA = "a" * 64
ACCEPTANCE_SHA = "b" * 64
MERGE_COMMIT = "c" * 40
TREE = "d" * 40
RUNTIME_REVISION = "e" * 40
INPUT_REVISION = "f" * 40
BASE = "1" * 40
CANDIDATE = "2" * 40
TEXT_A = "AP11 avstämning av målets krav mot sparade observationer"
TEXT_B = "AP11 överlämning genom befintlig AP08"


def delivered_report(**overrides):
    report = {
        "observation": "snapshot",
        "task_id": "ap11-step-5",
        "phase": "completed",
        "target": "Nortropic/nortropic-projektkontor",
        "observed_at_epoch": EPOCH,
        "age_seconds": 120,
        "verified_delivery": True,
        "review_run": "9308cd4f",
        "runtime_revision": RUNTIME_REVISION,
        "input_revision": INPUT_REVISION,
        "base": BASE,
        "candidate": CANDIDATE,
        "task_sha256": TASK_SHA,
        "acceptance_sha256": ACCEPTANCE_SHA,
        "evidence": ["observation.md"],
        "integration": {
            "merged": True,
            "merge_commit": MERGE_COMMIT,
            "tree": TREE,
            "candidate": CANDIDATE,
            "url": "https://github.com/Nortropic/nortropic-projektkontor/pull/28",
        },
    }
    report.update(overrides)
    return report


def goal(text_a=TEXT_A, text_b=TEXT_B, authority="none"):
    return {
        "id": "office-ap11",
        "requirements": [
            {"id": "A", "text": text_a,
             "task": {"id": "ap11-step-5", "sha256": TASK_SHA,
                      "acceptance_sha256": ACCEPTANCE_SHA, "merge_commit": MERGE_COMMIT}},
            {"id": "B", "text": text_b, "task": None},
        ],
        "next_action": {
            "text": "Bereda återstående AP08-överlämning från faktisk A-integration",
            "owner": "Värden",
            "authority": authority,
        },
    }


def picture(generated_at="2026-09-20T12:00:00Z", authority="none"):
    return {
        "schema": 1,
        "generated_at": generated_at,
        "title": "Ägarbild AP11",
        "summary": "Daterad läsning av sparat underlag.",
        "scope": "Endast tillfört underlag.",
        "capabilities": [{
            "title": "Avstämning", "use": "Läsning", "limits": "Ingen livebild",
            "delivery": "Lokal", "availability": "Enligt underlaget",
            "evidence": ["underlag-1"],
        }],
        "work": [],
        "next_action": {"text": "Något annat", "owner": "Någon annan",
                        "authority": authority, "evidence": ["underlag-1"]},
        "owner_decision": {"needed": "no", "question": "Behövs beslut?",
                           "reason": "Inget nytt vägval.", "evidence": ["underlag-1"]},
        "issues": [{"text": "Tillfört underlag är daterat.", "evidence": ["underlag-1"]}],
        "evidence": [{
            "id": "underlag-1", "title": "Tillfört underlag", "kind": "Anteckning",
            "observed_at": "2026-09-19T08:00:00Z", "revision": "saknas",
            "locator": "docs/plan.md", "sha256": None, "text": "Tillförd text.",
        }],
    }


class PresentTests(unittest.TestCase):

    def mixed(self):
        return goal(), [delivered_report()], picture()

    def test_surface_is_exactly_the_three_keys(self):
        g, reports, p = self.mixed()
        value = development_handoff.present(g, reports, p)
        self.assertEqual(set(value), {"reconciliation", "picture", "html"})
        self.assertFalse(hasattr(development_handoff, "main"))
        self.assertEqual(
            [name for name in vars(development_handoff) if not name.startswith("_")
             and name not in ("copy", "dt", "re", "agarbild", "development_result")],
            ["present"])

    def test_module_imports_no_effectful_stdlib(self):
        namespace = vars(development_handoff)
        for name in ("os", "open", "subprocess", "socket", "ctypes", "time", "logging"):
            self.assertNotIn(name, namespace)

    def test_mixed_case_statuses_and_states(self):
        g, reports, p = self.mixed()
        value = development_handoff.present(g, reports, p)
        statuses = [item["status"] for item in value["reconciliation"]["requirements"]]
        self.assertEqual(statuses, ["delivery_supported", "missing"])
        work = value["picture"]["work"]
        self.assertEqual(len(work), 2)
        self.assertEqual(work[0]["state"], "finished")
        self.assertIn(TEXT_A, work[0]["title"] + work[0]["text"])
        self.assertNotEqual(work[1]["state"], "finished")
        self.assertIn(work[1]["state"], agarbild.STATES)
        self.assertIn(TEXT_B, work[1]["title"] + work[1]["text"])
        self.assertIn("No task is bound to this requirement", work[1]["text"])

    def test_reconciliation_comes_from_the_module_attribute(self):
        g, reports, p = self.mixed()
        real = development_result.reconcile
        seen = []

        def wrapper(passed_goal, passed_reports):
            seen.append((passed_goal, passed_reports))
            return real(passed_goal, passed_reports)

        with mock.patch.object(development_result, "reconcile", wrapper):
            value = development_handoff.present(g, reports, p)
        self.assertEqual(len(seen), 1)
        self.assertIs(seen[0][0], g)
        self.assertIs(seen[0][1], reports)
        self.assertEqual(value["reconciliation"], real(g, reports))

    def test_html_comes_from_the_agarbild_attribute(self):
        g, reports, p = self.mixed()
        real = agarbild.render
        seen = []

        def wrapper(data):
            seen.append(data)
            return "RENDERED"

        with mock.patch.object(agarbild, "render", wrapper):
            value = development_handoff.present(g, reports, p)
        self.assertEqual(len(seen), 1)
        self.assertIs(seen[0], value["picture"])
        self.assertEqual(value["html"], "RENDERED")
        self.assertEqual(real(value["picture"]),
                         development_handoff.present(g, reports, p)["html"])

    def test_picture_validates_and_html_matches_render(self):
        g, reports, p = self.mixed()
        value = development_handoff.present(g, reports, p)
        agarbild.validate(value["picture"])
        self.assertEqual(value["html"], agarbild.render(value["picture"]))

    def test_supplied_evidence_prefix_and_owner_decision_preserved(self):
        g, reports, p = self.mixed()
        value = development_handoff.present(g, reports, p)
        evidence = value["picture"]["evidence"]
        self.assertEqual(evidence[:len(p["evidence"])], p["evidence"])
        self.assertGreater(len(evidence), len(p["evidence"]))
        self.assertEqual(value["picture"]["owner_decision"], p["owner_decision"])
        ids = [item["id"] for item in evidence]
        self.assertEqual(len(ids), len(set(ids)))
        for identifier in ids:
            self.assertIsNotNone(re.fullmatch(r"[A-Za-z0-9-]+", identifier))

    def test_every_evidence_reference_resolves(self):
        g, reports, p = self.mixed()
        value = development_handoff.present(g, reports, p)
        built = value["picture"]
        ids = {item["id"] for item in built["evidence"]}
        holders = (built["work"] + built["capabilities"] + built["issues"]
                   + [built["next_action"], built["owner_decision"]])
        for holder in holders:
            for reference in holder["evidence"]:
                self.assertIn(reference, ids)

    def test_appended_ids_do_not_collide_with_supplied_ids(self):
        g, reports, p = self.mixed()
        taken = copy.deepcopy(p["evidence"][0])
        taken["id"] = "ap11-handoff-reconciliation"
        p["evidence"].append(taken)
        value = development_handoff.present(g, reports, p)
        ids = [item["id"] for item in value["picture"]["evidence"]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(value["picture"]["evidence"][:2], p["evidence"])

    def test_authority_and_text_come_from_the_goal(self):
        g, reports, p = self.mixed()
        value = development_handoff.present(g, reports, p)
        self.assertEqual(value["picture"]["next_action"]["text"], g["next_action"]["text"])
        self.assertEqual(value["picture"]["next_action"]["authority"], "none")

    def test_conflicting_picture_authority_is_overridden_not_widened(self):
        g, reports, _ = self.mixed()
        p = picture(authority="accepted")
        value = development_handoff.present(g, reports, p)
        # Documented deterministic behaviour: the goal's authority always wins.
        self.assertEqual(value["picture"]["next_action"]["authority"], "none")
        self.assertTrue(any("accepted" in issue["text"]
                            for issue in value["picture"]["issues"]))
        self.assertIn(agarbild.AUTHORITIES["none"], value["html"])

    def test_unknown_goal_authority_is_rejected(self):
        g, reports, p = self.mixed()
        g["next_action"]["authority"] = "granted"
        with self.assertRaises(ValueError):
            development_handoff.present(g, reports, p)

    def test_saved_observation_time_is_retained(self):
        g, reports, p = self.mixed()
        value = development_handoff.present(g, reports, p)
        expected = dt.datetime.fromtimestamp(EPOCH, dt.timezone.utc)
        stamps = [dt.datetime.fromisoformat(item["observed_at"].replace("Z", "+00:00"))
                  for item in value["picture"]["evidence"] if item["observed_at"]]
        self.assertIn(expected, stamps)

    def test_revisions_and_merge_commit_reach_the_html(self):
        g, reports, p = self.mixed()
        value = development_handoff.present(g, reports, p)
        self.assertIn(MERGE_COMMIT, value["html"])
        self.assertIn(RUNTIME_REVISION, value["html"])

    def test_observation_newer_than_generated_at_is_rejected(self):
        g = goal()
        reports = [delivered_report(observed_at_epoch=LATE_EPOCH)]
        with mock.patch.object(agarbild, "render", side_effect=AssertionError("render")):
            with self.assertRaises(ValueError):
                development_handoff.present(g, reports, picture())

    def test_missing_runtime_revision_falls_back_without_inventing(self):
        g = goal()
        reports = [delivered_report(phase="accepted")]
        value = development_handoff.present(g, reports, picture())
        self.assertEqual(value["reconciliation"]["requirements"][0]["status"],
                         "not_supported")
        self.assertNotIn(RUNTIME_REVISION, value["html"])
        self.assertIn("Revision saknas i den sparade observationen", value["html"])

    def test_ambiguous_status_is_not_finished(self):
        g = goal()
        reports = [delivered_report(), delivered_report()]
        value = development_handoff.present(g, reports, picture())
        self.assertEqual(value["reconciliation"]["requirements"][0]["status"], "ambiguous")
        work = value["picture"]["work"]
        self.assertTrue(all(item["state"] != "finished" for item in work))
        self.assertIn("none is selected", work[0]["text"])

    def test_no_finished_state_when_nothing_is_supported(self):
        g, _, p = self.mixed()
        value = development_handoff.present(g, [], p)
        work = value["picture"]["work"]
        self.assertGreaterEqual(len(work), 2)
        self.assertTrue(all(item["state"] != "finished" for item in work))
        agarbild.validate(value["picture"])

    def test_whole_goal_completion_is_never_claimed(self):
        g, reports, p = self.mixed()
        value = development_handoff.present(g, reports, p)
        self.assertIs(value["reconciliation"]["whole_goal_complete"], False)
        texts = [issue["text"] for issue in value["picture"]["issues"]]
        for limitation in value["reconciliation"]["limitations"]:
            self.assertTrue(any(limitation in text for text in texts))
        self.assertTrue(any("whole_goal_complete" in text for text in texts))

    def test_inputs_are_not_mutated_and_not_aliased(self):
        g, reports, p = self.mixed()
        before = copy.deepcopy((g, reports, p))
        value = development_handoff.present(g, reports, p)
        self.assertEqual((g, reports, p), before)
        built = value["picture"]
        self.assertIsNot(built["evidence"][0], p["evidence"][0])
        self.assertIsNot(built["owner_decision"], p["owner_decision"])
        self.assertIsNot(built["capabilities"][0], p["capabilities"][0])
        self.assertIsNot(built["issues"][0], p["issues"][0])
        built["evidence"][0]["text"] = "mutated"
        built["owner_decision"]["reason"] = "mutated"
        self.assertEqual((g, reports, p), before)

    def test_reconcile_rejections_propagate_before_rendering(self):
        cases = [
            ({"id": "other-goal", "requirements": goal()["requirements"],
              "next_action": goal()["next_action"]}, []),
            ({"id": "office-ap11", "requirements": [], "next_action": goal()["next_action"]}, []),
            (goal(), {"not": "a list"}),
            ("not a goal", []),
        ]
        for bad_goal, bad_reports in cases:
            with self.subTest(goal=bad_goal, reports=bad_reports):
                with mock.patch.object(agarbild, "render",
                                       side_effect=AssertionError("render reached")):
                    with self.assertRaises(ValueError):
                        development_handoff.present(bad_goal, bad_reports, picture())

    def test_duplicate_requirement_ids_propagate(self):
        g = goal()
        g["requirements"][1]["id"] = "A"
        with mock.patch.object(agarbild, "render", side_effect=AssertionError("render")):
            with self.assertRaises(ValueError):
                development_handoff.present(g, [], picture())

    def test_escaping_is_left_to_agarbild(self):
        g = goal(text_b="<script>fixture()</script>")
        value = development_handoff.present(g, [delivered_report()], picture())
        self.assertIn("&lt;script&gt;", value["html"])
        self.assertNotIn("<script>", value["html"])
        self.assertIn("<script>fixture()</script>", value["picture"]["work"][1]["title"])


if __name__ == "__main__":
    unittest.main()
