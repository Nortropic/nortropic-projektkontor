"""Synthetic AP06 tests. No real sources, host tasks or acceptance files are read."""

import copy
import contextlib
import io
import json
import unittest
from unittest import mock

import assignment_preparation as preparation
import change_assessment


def fixture():
    case = {
        "schema": 1, "id": "PRIVATE-CASE", "created_at": "2026-01-01T00:00:00Z",
        "sources": [
            {"id": "PRIVATE-SOURCE-" + str(i), "title": "PRIVATE-TITLE-" + str(i),
             "version": "PRIVATE-VERSION-" + str(i), "path": "private/source-" + str(i),
             "sha256": str(i) * 64, "size": i} for i in (1, 2, 3)
        ],
        "claims": [
            {"id": "PRIVATE-CLAIM-" + str(i), "kind": kind,
             "text": "PRIVATE-TEXT-" + str(i), "reason": "PRIVATE-REASON-" + str(i),
             "standing": "PRIVATE-STANDING-" + str(i), "sources": ["PRIVATE-SOURCE-" + str(i)]}
            for i, kind in ((1, "decision"), (2, "fact"))
        ],
        "actions": [{
            "id": "PRIVATE-ACTION", "text": "PRIVATE-ACTION-TEXT", "reason": "PRIVATE-ACTION-REASON",
            "claims": ["PRIVATE-CLAIM-1"],
            "authority": {"status": "granted", "scope": "PRIVATE-AUTHORITY-SCOPE",
                          "sources": ["PRIVATE-SOURCE-3"]},
        }],
        "next_action": "PRIVATE-ACTION",
    }
    check = {
        "checked_at": "2026-01-02T00:00:00Z", "manifest": change_assessment.reference_manifest(case),
        "result": {"ok": True, "files": [{"path": s["path"], "status": "ok"} for s in case["sources"]]},
    }
    references = [
        {"id": "PRIVATE-REF-" + str(i), "source": "PRIVATE-SOURCE-" + str(i),
         "version": "PRIVATE-VERSION-" + str(i), "quote": "PRIVATE-QUOTE-" + str(i)}
        for i in (1, 2)
    ]
    spec = {
        "schema": 1, "action": "PRIVATE-ACTION", "references": references,
        "reference_checks": [dict(ref, sha256=str(i) * 64, status="matched")
                             for i, ref in enumerate(references, 1)],
        "requirements": [
            {"id": "R" + str(i), "text": "Return synthetic result " + str(i),
             "reason": "Exercise a selected synthetic behavior.",
             "claims": ["PRIVATE-CLAIM-" + str(i)], "references": ["PRIVATE-REF-" + str(i)],
             "tests": ["T" + str(i)]} for i in (1, 2)
        ],
        "tests": [{"id": "T" + str(i), "observable": "Synthetic input returns result " + str(i),
                   "method": "Compare the returned value with the synthetic expected value."} for i in (1, 2)],
        "export": {
            "title": "Synthetic assignment", "context": [
                {"kind": kind, "text": "Authored synthetic " + kind}
                for kind in ("fact", "judgment", "decision", "authority")],
            "scope": ["Implement the synthetic behavior."],
            "limitations": ["The example has no real-world evidential value."],
        },
        "task": {
            "id": "synthetic-worker", "target": "Nortropic/nortropic-projektkontor",
            "base": "a" * 40, "runtime_revision": "b" * 40,
            "allowed_paths": ["tools/synthetic_worker.py", "tools/test_synthetic_worker.py"],
            "attempt_seconds": 120, "automatic_retries": 0,
            "steps": [{"provider": "codex", "prompt": "Implement the synthetic worker."}],
            "acceptance": "acceptance/synthetic.py", "acceptance_sha256": "c" * 64,
            "brief": "tasks/synthetic.md",
        },
    }
    return case, check, spec


def set_at(value, path, replacement):
    for key in path[:-1]:
        value = value[key]
    value[path[-1]] = replacement


class PreparationTests(unittest.TestCase):
    def setUp(self):
        self.case, self.check, self.spec = fixture()

    def prepare(self):
        return preparation.prepare(self.case, self.check, self.spec)

    def gaps(self):
        return {(entry["code"], entry["subject"]) for entry in self.prepare()["gaps"]}

    def test_complete_draft_and_exact_public_schema(self):
        result = self.prepare()
        self.assertEqual(set(result), {"status", "mechanical_complete", "gaps", "private", "package"})
        self.assertEqual(result["status"], "draft")
        self.assertIs(result["mechanical_complete"], True)
        self.assertEqual(result["gaps"], [])
        package = result["package"]
        self.assertEqual(set(package), {"brief", "task_draft", "requirements", "tests", "gaps", "limitations"})
        self.assertEqual(package["task_draft"], self.spec["task"])
        self.assertEqual(package["tests"], self.spec["tests"])
        self.assertEqual(set(package["requirements"][0]), {"id", "text", "reason", "tests"})
        self.assertEqual(json.loads(json.dumps(result, allow_nan=False)), result)
        self.assertEqual(result, self.prepare())
        brief = package["brief"]
        for phrase in ("DRAFT", "neither acceptance nor authority", "Selected-source-only",
                       "checked_at", "freshness", "Export review", "freeze file bytes",
                       "not authenticated evidence", "### Fact", "### Judgment", "### Decision",
                       "### Authority", "## Scope", "## Derived requirements", "## Gaps"):
            self.assertIn(phrase, brief)
        for req in self.spec["requirements"]:
            self.assertIn(req["text"], brief)
            self.assertIn(req["reason"], brief)
        for test in self.spec["tests"]:
            self.assertIn(test["observable"], brief)
            self.assertIn(test["method"], brief)

    def test_scoped_source_changes_preserve_decisions_and_authority(self):
        for status in ("changed", "missing", "unsafe", "not_checked"):
            with self.subTest(status=status):
                self.setUp()
                if status == "not_checked":
                    self.check["result"]["files"].pop(0)
                else:
                    self.check["result"]["files"][0]["status"] = status
                    self.check["result"]["ok"] = False
                result = self.prepare()
                gaps = {(g["code"], g["subject"]) for g in result["gaps"]}
                self.assertIn(("requirement_dependencies_need_reassessment", "R1"), gaps)
                self.assertIn(("reference_source_needs_reassessment", "reference:1"), gaps)
                self.assertIn(("action_dependencies_need_reassessment", "brief"), gaps)
                self.assertFalse(any(g["subject"] in ("R2", "reference:2") for g in result["gaps"]))
                assessment = result["private"]["assessment"]
                self.assertEqual(assessment["decisions"][0]["standing"], self.case["claims"][0]["standing"])
                self.assertEqual(assessment["actions"][0]["authority"], self.case["actions"][0]["authority"])
                self.assertEqual(result["private"]["requirements"][0]["affected_sources"], ["PRIVATE-SOURCE-1"])
                self.assertFalse(result["private"]["references"][0]["current"])

    def test_both_claim_and_reference_dependencies_are_followed(self):
        self.spec["requirements"][0]["references"] = ["PRIVATE-REF-2"]
        self.check["result"]["files"][0]["status"] = "changed"
        self.check["result"]["ok"] = False
        self.assertIn(("requirement_dependencies_need_reassessment", "R1"), self.gaps())
        self.assertNotIn(("requirement_dependencies_need_reassessment", "R2"), self.gaps())
        self.spec["requirements"][0]["claims"] = ["PRIVATE-CLAIM-2"]
        self.spec["requirements"][0]["references"] = ["PRIVATE-REF-1"]
        self.assertIn(("requirement_dependencies_need_reassessment", "R1"), self.gaps())

    def test_authority_and_action_selection_are_scoped(self):
        for status in ("not_granted", "not_established"):
            self.case["actions"][0]["authority"].update(status=status, sources=[])
            self.assertIn(("action_authority_missing", "brief"), self.gaps())
        self.setUp()
        self.check["result"]["files"][2]["status"] = "changed"
        self.check["result"]["ok"] = False
        self.assertEqual(self.gaps(), {("action_dependencies_need_reassessment", "brief")})
        alternate = copy.deepcopy(self.case["actions"][0])
        alternate.update(id="PRIVATE-ALTERNATE", claims=["PRIVATE-CLAIM-2"])
        alternate["authority"]["sources"] = ["PRIVATE-SOURCE-2"]
        self.case["actions"].append(alternate)
        self.spec["action"] = alternate["id"]
        self.assertTrue(self.prepare()["mechanical_complete"])

    def test_lookup_gaps_are_concrete_and_propagate(self):
        for status in ("missing", "mismatch", "not_checked"):
            with self.subTest(status=status):
                self.setUp()
                if status == "missing":
                    self.spec["reference_checks"].pop(0)
                else:
                    self.spec["reference_checks"][0]["status"] = status
                gaps = self.gaps()
                self.assertIn(("reference_check_" + status, "reference:1"), gaps)
                self.assertIn(("requirement_references_unverified", "R1"), gaps)
                self.assertFalse(any(subject == "R2" for _, subject in gaps))

    def test_unused_supplied_reference_also_needs_a_check(self):
        self.spec["requirements"].pop()
        self.spec["reference_checks"].pop()
        self.assertIn(("reference_check_missing", "reference:2"), self.gaps())

    def test_empty_quote_is_a_valid_non_quote_locator(self):
        self.spec["references"][0]["quote"] = ""
        self.spec["reference_checks"][0]["quote"] = ""
        self.assertTrue(self.prepare()["mechanical_complete"])

    def test_empty_requirements_tests_links_and_export_are_gaps(self):
        for field in ("claims", "references", "tests"):
            self.spec["requirements"][0][field] = []
            self.assertIn(("requirement_" + field + "_empty", "R1"), self.gaps())
        for field in ("context", "scope", "limitations"):
            self.spec["export"][field] = []
            self.assertIn(("export_" + field + "_empty", "brief"), self.gaps())
        self.spec["requirements"] = []
        self.spec["tests"] = []
        self.assertIn(("requirements_empty", "brief"), self.gaps())
        self.assertIn(("tests_empty", "brief"), self.gaps())
        self.assertTrue(self.prepare()["package"]["limitations"])

    def test_empty_observable_and_method_are_verification_gaps(self):
        for field in ("observable", "method"):
            for value in ("", " \n\t"):
                with self.subTest(field=field, value=value):
                    self.setUp()
                    self.spec["tests"][0][field] = value
                    self.assertIn(("test_" + field + "_empty", "T1"), self.gaps())
                    self.assertIn(("requirement_verification_incomplete", "R1"), self.gaps())

    def test_missing_and_empty_task_values_are_retained_without_defaults(self):
        original = copy.deepcopy(self.spec["task"])
        for field in original:
            for empty in (None, "", " \t", [], {}):
                with self.subTest(field=field, empty=empty):
                    self.spec["task"] = dict(original, **{field: empty})
                    result = self.prepare()
                    self.assertIn({"code": "task_field_empty", "subject": field}, result["gaps"])
                    self.assertEqual(result["package"]["task_draft"], self.spec["task"])
            self.spec["task"] = copy.deepcopy(original)
            del self.spec["task"][field]
            result = self.prepare()
            self.assertIn({"code": "task_field_missing", "subject": field}, result["gaps"])
            self.assertNotIn(field, result["package"]["task_draft"])
        self.spec["task"] = {}
        result = self.prepare()
        self.assertEqual(result["package"]["task_draft"], {})
        self.assertEqual(len(result["gaps"]), len(original))

    def test_explicit_executor_fields(self):
        case, check, spec = fixture()
        baseline = preparation.prepare(case, check, spec)
        for provider in ("codex", "claude"):
            chosen = copy.deepcopy(spec); chosen["task"]["steps"][0]["provider"] = provider
            self.assertEqual(preparation.prepare(case, check, chosen)["gaps"], baseline["gaps"])
        # An absent reviewer choice is original Codex: never a gap, never written as a default.
        self.assertNotIn("review_provider", baseline["package"]["task_draft"])
        self.assertFalse([g for g in baseline["gaps"] if g["subject"] == "review_provider"])
        for reviewer in ("codex", "claude"):
            chosen = copy.deepcopy(spec); chosen["task"]["review_provider"] = reviewer
            result = preparation.prepare(case, check, chosen)
            self.assertEqual(result["package"]["task_draft"]["review_provider"], reviewer)
            self.assertEqual(result["gaps"], baseline["gaps"])
        for bad in ("gpt", "", None, ["claude"], True, "Claude"):
            chosen = copy.deepcopy(spec); chosen["task"]["review_provider"] = bad
            with self.subTest(bad=bad), self.assertRaisesRegex(ValueError, "review_provider"):
                preparation.prepare(case, check, chosen)
        extra = copy.deepcopy(spec); extra["task"]["publisher"] = "claude"
        with self.assertRaisesRegex(ValueError, "only permitted fields"):
            preparation.prepare(case, check, extra)

    def test_invalid_task_values(self):
        invalid = {
            "id": [True, 4, "Bad", "a_b", "-a", "a" * 81, "a\n"],
            "target": ["Nortropic/nortropic-runtime", "other/repo", [], False],
            "base": ["a" * 39, "A" * 40, 3],
            "runtime_revision": ["g" * 40, "b" * 41, True],
            "acceptance_sha256": ["C" * 64, "c" * 63, "c" * 65, False],
            "attempt_seconds": [True, False, 0, -1, 3601, 1.0, "1"],
            "automatic_retries": [True, False, 1, -1, 0.0, "0"],
            "steps": ["codex", [None], [{"provider": "gpt", "prompt": "Do it"}], [{"provider": None, "prompt": "Do it"}],
                      [{"provider": ["claude"], "prompt": "Do it"}],
                      [{"provider": "codex", "prompt": " "}], [{"provider": "codex"}],
                      [{"provider": "codex", "prompt": "Do it", "extra": 1}]],
            "allowed_paths": ["tools/x.py", [None], ["tools/a.py", "tools/A.py"]],
            "acceptance": ["tasks/x.py", "acceptance", "acceptance/", "acceptance/../x"],
            "brief": ["acceptance/x.md", "tasks", "/tasks/x.md", "tasks/./x.md"],
        }
        invalid["target"].remove([])  # An explicitly empty top-level value is a gap.
        bad_paths = ["/tools/x.py", "tools", "tools/", "tools//x.py", "tools/../x.py",
                     "tools/./x.py", "tools/a/../../x.py", "tools/x\\y.py", "tools/*.py",
                     "tools/a b.py", "tools/a\x00.py", "tools/é.py", "tools/kontor.py",
                     "tools/KONTOR.py", "tools/assignment_preparation.py",
                     "tools/Assignment_Preparation.py", "tasks/x.py", "Tools/x.py"]
        invalid["allowed_paths"].extend([[path] for path in bad_paths])
        for field, values in invalid.items():
            for value in values:
                with self.subTest(field=field, value=value):
                    self.setUp()
                    self.spec["task"][field] = value
                    with self.assertRaises(ValueError):
                        self.prepare()
        for seconds in (1, 3600):
            self.setUp()
            self.spec["task"]["attempt_seconds"] = seconds
            self.assertTrue(self.prepare()["mechanical_complete"])

    def test_invalid_ids_bindings_and_types(self):
        changes = [
            (("schema",), v) for v in (True, 1.0, "1", 2, None)
        ] + [
            (("action",), "unknown"), (("action",), []),
            (("references", 0, "id"), " "), (("references", 0, "source"), "unknown"),
            (("references", 0, "version"), "wrong"), (("references", 0, "quote"), None),
            (("reference_checks", 0, "id"), "unknown"),
            (("reference_checks", 0, "source"), "PRIVATE-SOURCE-2"),
            (("reference_checks", 0, "version"), "wrong"),
            (("reference_checks", 0, "sha256"), "9" * 64),
            (("reference_checks", 0, "quote"), "wrong"),
            (("reference_checks", 0, "status"), "approved"),
            (("reference_checks", 0, "status"), []),
            (("requirements", 0, "text"), ""), (("requirements", 0, "reason"), " "),
            (("requirements", 0, "claims"), ["unknown"]),
            (("requirements", 0, "references"), ["unknown"]),
            (("requirements", 0, "tests"), ["unknown"]),
            (("tests", 0, "observable"), None), (("tests", 0, "method"), 123),
            (("export", "title"), ""), (("export", "scope"), [""]),
            (("export", "context", 0, "kind"), "opinion"),
            (("export", "context", 0, "text"), " "), (("export", "limitations"), [None]),
            (("task",), None), (("task",), []),
        ]
        for field in ("references", "reference_checks", "requirements", "tests"):
            changes.extend([((field,), {}), ((field, 0, "id"), []),
                            ((field, 1, "id"), self.spec[field][0]["id"])])
        for field in ("claims", "references", "tests"):
            value = self.spec["requirements"][0][field][0]
            changes.extend([(("requirements", 0, field), [value, value]),
                            (("requirements", 0, field), [{}])])
        for path, value in changes:
            with self.subTest(path=path, value=value):
                self.setUp()
                set_at(self.spec, path, value)
                original = copy.deepcopy((self.case, self.check, self.spec))
                with self.assertRaises(ValueError):
                    self.prepare()
                self.assertEqual((self.case, self.check, self.spec), original)

    def test_exact_keys_on_all_spec_objects(self):
        paths = [(), ("references", 0), ("reference_checks", 0), ("requirements", 0),
                 ("tests", 0), ("export",), ("export", "context", 0), ("task",), ("task", "steps", 0)]
        for path in paths:
            self.setUp()
            obj = self.spec
            for key in path:
                obj = obj[key]
            keys = list(obj) if path != ("task",) else []
            for missing in [None] + keys:
                with self.subTest(path=path, missing=missing):
                    self.setUp()
                    obj = self.spec
                    for key in path:
                        obj = obj[key]
                    if missing is None:
                        obj["unknown"] = "invalid"
                    else:
                        del obj[missing]
                    with self.assertRaises(ValueError):
                        self.prepare()

    def test_ap05_validation_is_reused(self):
        with mock.patch.object(change_assessment, "assess", wraps=change_assessment.assess) as assess:
            result = self.prepare()
            assess.assert_called_once_with(self.case, self.check)
        self.assertEqual(result["private"]["assessment"], change_assessment.assess(self.case, self.check))
        self.check["checked_at"] = "2025-01-01T00:00:00Z"
        with self.assertRaises(ValueError):
            self.prepare()
        self.setUp()
        self.check["manifest"]["files"][0]["sha256"] = "f" * 64
        with self.assertRaises(ValueError):
            self.prepare()

    def test_private_data_never_copied_to_package_or_gaps(self):
        self.check["result"]["files"][0]["status"] = "missing"
        self.check["result"]["ok"] = False
        self.spec["reference_checks"].pop(0)
        result = self.prepare()
        public = json.dumps([result["package"], result["gaps"]])
        for private in ("PRIVATE-", "private/source", "1" * 64, "2" * 64, "3" * 64):
            self.assertNotIn(private, public)
        self.assertEqual(result["private"]["spec"], self.spec)
        self.assertEqual(result["private"]["case"], self.case)
        self.assertEqual(result["private"]["check"], self.check)
        # Authored public content is deliberately NOT redacted or certified safe.
        self.spec["export"]["context"][0]["text"] = "PRIVATE-authored-export"
        self.assertIn("PRIVATE-authored-export", self.prepare()["package"]["brief"])

    def test_no_input_mutation_output_aliases_or_side_effects(self):
        original = copy.deepcopy((self.case, self.check, self.spec))
        output = io.StringIO()
        with contextlib.ExitStack() as stack:
            stack.enter_context(contextlib.redirect_stdout(output))
            stack.enter_context(contextlib.redirect_stderr(output))
            for target in ("builtins.open", "io.open", "os.open", "os.listdir", "os.scandir",
                           "os.stat", "os.system", "subprocess.Popen", "socket.socket",
                           "hashlib.sha256", "hashlib.new"):
                stack.enter_context(mock.patch(target, side_effect=AssertionError("Unexpected side effect")))
            result = self.prepare()
        self.assertEqual(output.getvalue(), "")
        self.assertEqual((self.case, self.check, self.spec), original)
        result["package"]["task_draft"]["steps"][0]["prompt"] = "changed"
        result["package"]["requirements"][0]["tests"].clear()
        result["package"]["tests"][0]["observable"] = "changed"
        result["private"]["spec"]["references"].clear()
        result["private"]["assessment"]["decisions"][0]["standing"] = "changed"
        self.assertEqual((self.case, self.check, self.spec), original)
        self.spec["task"] = {}
        result = self.prepare()
        result["package"]["gaps"][0]["subject"] = "changed"
        self.assertNotEqual(result["package"]["gaps"], result["gaps"])


if __name__ == "__main__":
    unittest.main()
