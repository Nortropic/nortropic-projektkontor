"""Synthetic contract tests. Run: python3 -B -m unittest discover -s tools -p test_agarbild.py"""

import copy
import datetime
import html
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

import agarbild


ROOT = Path(__file__).resolve().parents[1]
SCRATCH = ROOT / ".scratch"


def example():
    """Invented Swedish observations, never private production material."""
    return {
        "schema": 1, "generated_at": "2026-09-20T18:00:00+02:00",
        "title": "Kontoret · en samlad ägarbild",
        "summary": "Underlaget kan beredas lokalt. Leveransen är dokumenterad, men tillgängligheten behöver kontrolleras.",
        "scope": "Syntetiskt exempel för en lokal läsrapport; inga verkliga projektuppgifter.",
        "capabilities": [{
            "title": "Förbered ett avgränsat uppdrag", "use": "Samla bedömda krav och hänvisningar i ett utkast.",
            "limits": "Utkastet behöver sakgranskning och ger inget mandat.",
            "delivery": "En tidigare version är levererad enligt ett syntetiskt kvitto.",
            "availability": "Inte provad vid senaste observationen; åtkomst är okänd.", "evidence": ["e1", "e2"],
        }],
        "work": [
            {"title": "Granskning av nästa underlag", "state": "waiting", "text": "Teknisk väntan på granskarens jämförelse.",
             "observed_at": "2026-09-20T15:00:00Z", "evidence": ["e2"]},
            {"title": "Tidigare beredning", "state": "finished", "text": "Ett äldre underlag färdigställdes.",
             "observed_at": "2026-08-01T12:00:00Z", "evidence": ["e1"]},
            {"title": "Tidigare ersatt väntan", "state": "superseded", "text": "Den gamla körningen väntade. Den har ersatts och ska inte återupptas.",
             "observed_at": "2026-08-01T12:00:00Z", "evidence": ["e1"]},
            {"title": "Kompletterande kontroll", "state": "unknown", "text": "Ingen observation av utförandet finns i urvalet.",
             "observed_at": None, "evidence": ["e2"]},
        ],
        "next_action": {"text": "Jämför tillgänglighetsuppgifterna med det bevarade kvittot.",
                        "owner": "Kedjedrivaren", "authority": "accepted", "evidence": ["e1", "e2"]},
        "owner_decision": {"needed": "no", "question": "Ingen fråga till ägaren i detta underlag.",
                           "reason": "Jämförelsen ryms inom det angivna uppdraget; väntan är teknisk.", "evidence": ["e2"]},
        "issues": [{"text": "Uppgifterna motsäger varandra: tidigare kvitto anger åtkomst, senare observation kan inte bekräfta den.", "evidence": ["e1", "e2"]}],
        "evidence": [
            {"id": "e1", "title": "Tidigare syntetiskt leveranskvitto", "kind": "Kvitto", "observed_at": "2026-08-01T12:00:00Z",
             "revision": "syntetisk-version-1", "locator": "syntetiskt/kvitto.json", "sha256": "a" * 64,
             "text": "Kvitto: funktionen levererad och åtkomlig vid detta observationstillfälle."},
            {"id": "e2", "title": "Senare syntetisk observation", "kind": "Bedömning", "observed_at": None,
             "revision": "syntetisk-version-2", "locator": "syntetiskt/bedomning.txt", "sha256": None,
             "text": "Åtkomst kunde inte bekräftas. Observationstid för denna källuppgift saknas."},
        ],
    }


class Page(HTMLParser):
    def __init__(self, document):
        super().__init__(convert_charrefs=True)
        self.tags = []
        self.content = []
        self.feed(document)

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))

    def handle_data(self, data):
        self.content.append(data)


class ReportTests(unittest.TestCase):
    def test_swedish_report_and_separate_meanings(self):
        document = agarbild.render(example())
        page = Page(document)
        self.assertIn(('html', {'lang': 'sv'}), page.tags)
        for text in ["Det här kan användas", "Begränsningar", "Leverans", "Aktuell tillgänglighet enligt underlaget",
                     "Senast observerade arbete", "Nästa motiverade handling", "Inget ägarbeslut behövs enligt underlaget",
                     "Teknisk väntan", "Framställd:", "Observerad:", "observation saknas", "Ålder vid framställning: 50 dygn",
                     "detta visar inte att inget arbete pågår", "Uppgifterna motsäger varandra", "inte en livebild",
                     "Renderingen autentiserar inte", "inte leveransbevis"]:
            self.assertIn(text, document)
        history = document.index('id="history"')
        self.assertGreater(document.index("Tidigare ersatt väntan"), history)
        self.assertNotIn("Tidigare ersatt väntan", document[:history])
        self.assertLess(document.index("Granskning av nästa underlag"), document.index("Tidigare beredning"))
        evidence = document.index('<details id="evidence-1">')
        self.assertGreater(document.index("syntetisk-version-1"), evidence)
        self.assertGreater(document.index("a" * 64), evidence)
        self.assertNotIn("syntetiskt/kvitto.json", document[:evidence])

    def test_owner_question_and_proposed_action(self):
        data = example()
        data["owner_decision"] = {"needed": "yes", "question": "Ska omfattningen utökas?", "reason": "Det föreslagna steget går utanför uppdraget.", "evidence": ["e2"]}
        data["next_action"]["authority"] = "proposed"
        document = agarbild.render(data)
        self.assertIn("Ett ägarbeslut behövs enligt underlaget", document)
        self.assertIn("Ska omfattningen utökas?", document)
        self.assertIn("Föreslagen — inte accepterad", document)
        data["owner_decision"]["needed"] = "unknown"
        data["next_action"]["authority"] = "unknown"
        self.assertIn("Behovet av ägarbeslut är okänt", agarbild.render(data))
        self.assertIn("Befogenhet okänd", agarbild.render(data))
        data["next_action"]["authority"] = "none"
        self.assertIn("Ingen befogenhet angiven som given", agarbild.render(data))

    def test_no_decision_is_not_derived_from_waits(self):
        data = example()
        for state in agarbild.STATES:
            with self.subTest(state=state):
                data["work"][0]["state"] = state
                document = agarbild.render(data)
                self.assertIn("Inget ägarbeslut behövs enligt underlaget", document)
                self.assertIn(agarbild.STATES[state], document)

    def test_empty_optional_lists_are_not_absence_claims(self):
        data = example()
        for key in ("capabilities", "work", "issues"):
            data[key] = []
        document = agarbild.render(data)
        self.assertIn("Inga förmågor redovisade", document)
        self.assertIn("Det visar inte att inget arbete pågår", document)
        self.assertIn("Det bevisar inte att underlaget är fullständigt", document)

    def test_conflicting_source_statements_preserved(self):
        data = example()
        data["issues"] = []  # The renderer does not discover semantic conflicts.
        document = agarbild.render(data)
        for source in data["evidence"]:
            self.assertIn(source["text"], document)
        self.assertIn("Inga osäkerheter redovisade av författaren", document)

    def test_timezone_comparison_and_age_use_snapshot_only(self):
        data = example()
        data["work"][0]["observed_at"] = "2026-09-20T19:00:00+03:00"
        self.assertIn("Ålder vid framställning: 0 dygn, 0 timmar, 0 minuter, 0 sekunder", agarbild.render(data))
        data["work"][0]["observed_at"] = "2026-09-20T15:59:59.750000Z"
        self.assertIn("250000 mikrosekunder", agarbild.render(data))
        data["generated_at"] = "2026-09-20T18:00+02:00"
        agarbild.render(data)
        data["generated_at"] = "20260920T180000+0200"
        agarbild.render(data)
        data["generated_at"] = "2026-09-20T18:00:00,0000001+02"
        data["work"][0]["observed_at"] = "2026-09-20T16:00:00Z"
        self.assertIn("1/10000000 sekund", agarbild.render(data))

    def test_documented_example_renders(self):
        documentation = (ROOT / "tools/AGARBILD.md").read_text(encoding="utf-8")
        raw = documentation.split("```json\n", 1)[1].split("```", 1)[0]
        self.assertIn("Kontoret · syntetisk ägarbild", agarbild.render(json.loads(raw)))

    def test_pure_deterministic_render(self):
        data = example()
        original = copy.deepcopy(data)
        class NoClock(datetime.datetime):
            @classmethod
            def now(cls, *args, **kwargs):
                raise AssertionError("Clock accessed")
            @classmethod
            def today(cls):
                raise AssertionError("Clock accessed")
        with mock.patch("builtins.open", side_effect=AssertionError("IO")), \
             mock.patch("agarbild.os.open", side_effect=AssertionError("IO")), \
             mock.patch("agarbild.dt.datetime", NoClock), \
             mock.patch("subprocess.run", side_effect=AssertionError("Execution")):
            first = agarbild.render(data)
            self.assertEqual(first, agarbild.render(data))
        self.assertEqual(original, data)

    def test_hostile_strings_never_become_markup_or_resources(self):
        attack = '</style></title><script>alert("x")</script><img src="https://invalid.example/x" onerror="x"><a href="javascript:x">x</a><iframe src="file:///secret"></iframe>&\' ${x} `x`'
        data = example()
        # Put hostile data in every free-text field, including locators and titles.
        data["title"] = data["summary"] = data["scope"] = attack
        for item in data["capabilities"]:
            for key in ("title", "use", "limits", "delivery", "availability"):
                item[key] = attack
        for item in data["work"]:
            item["title"] = item["text"] = attack
        for key in ("text", "owner"):
            data["next_action"][key] = attack
        for key in ("question", "reason"):
            data["owner_decision"][key] = attack
        data["issues"][0]["text"] = attack
        for item in data["evidence"]:
            for key in ("title", "kind", "revision", "locator", "text"):
                item[key] = attack
        document = agarbild.render(data)
        self.assertIn(html.escape(attack), document)
        self.assertNotIn(attack, document)
        page = Page(document)
        self.assertIn(attack, ''.join(page.content))
        forbidden = {"script", "img", "iframe", "link", "base", "form", "input", "button", "object", "embed", "svg", "audio", "video"}
        for tag, attrs in page.tags:
            self.assertNotIn(tag, forbidden)
            self.assertFalse(any(key.startswith("on") for key in attrs))
            self.assertNotIn("src", attrs)
            if "href" in attrs:
                self.assertEqual(tag, "a")
                self.assertRegex(attrs["href"], r"^#evidence-[0-9]+$")
            if tag == "meta":
                self.assertNotEqual(attrs.get("http-equiv", "").lower(), "refresh")
        csp = [attrs["content"] for tag, attrs in page.tags if attrs.get("http-equiv") == "Content-Security-Policy"]
        self.assertEqual(csp, ["default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'"])
        css = document.split("<style>")[1].split("</style>")[0]
        self.assertNotIn("url(", css.lower())
        self.assertNotIn("@import", css.lower())
        ids = {attrs["id"] for _, attrs in page.tags if "id" in attrs}
        for _, attrs in page.tags:
            if "href" in attrs:
                self.assertIn(attrs["href"][1:], ids)

    def test_exact_object_shapes_at_every_level(self):
        paths = [(), ("capabilities", 0), ("work", 0), ("next_action",), ("owner_decision",), ("issues", 0), ("evidence", 0)]
        for path in paths:
            target = example()
            for key in path:
                target = target[key]
            for missing in list(target) + [None]:
                with self.subTest(path=path, missing=missing):
                    data = example()
                    item = data
                    for key in path:
                        item = item[key]
                    if missing is None:
                        item["unexpected"] = "secret"
                    else:
                        del item[missing]
                    with self.assertRaises(agarbild.ValidationError):
                        agarbild.render(data)

    def test_invalid_types_values_and_refs(self):
        cases = [
            (("schema",), True), (("schema",), 1.0), (("schema",), 2),
            (("title",), ""), (("summary",), " \n"), (("scope",), None), (("title",), "\ud800"),
            (("capabilities",), {}), (("work",), None), (("issues",), "x"), (("evidence",), []),
            (("work", 0, "state"), "green"), (("next_action", "authority"), []),
            (("owner_decision", "needed"), False), (("evidence", 0, "id"), "å"),
            (("evidence", 1, "id"), "e1"), (("evidence", 0, "id"), 'x" onclick="x'),
            (("evidence", 0, "sha256"), "A" * 64), (("evidence", 0, "sha256"), "0" * 63),
            (("evidence", 0, "sha256"), 3), (("capabilities", 0, "use"), False),
            (("next_action", "evidence"), ["missing"]), (("issues", 0, "evidence"), ["e1", "e1"]),
            (("work", 0, "evidence"), []), (("owner_decision", "evidence"), "e1"),
            (("capabilities", 0, "evidence"), [{}]), (("evidence", 0), []),
        ]
        for path, value in cases:
            with self.subTest(path=path, value=repr(value)):
                data = example()
                target = data
                for key in path[:-1]:
                    target = target[key]
                target[path[-1]] = value
                with self.assertRaises(agarbild.ValidationError):
                    agarbild.render(data)
        for data in [None, [], "x", 1]:
            with self.assertRaises(agarbild.ValidationError):
                agarbild.render(data)

    def test_invalid_dates_and_future_observations(self):
        for value in ["2026-02-30T12:00:00Z", "2026-09-20", "2026-09-20T12:00:00",
                      "2026-09-20X12:00:00Z", "2026-09-20T24:00:00Z", "2026-09-20T12:00:00+00:99",
                      "2026-09-20T12:00:00+24:00", "2026-09-20T12:60:00Z", None, 3, "yesterday"]:
            with self.subTest(value=value):
                data = example()
                data["generated_at"] = value
                with self.assertRaises(agarbild.ValidationError):
                    agarbild.render(data)
        for key in ("work", "evidence"):
            for value in ["2026-09-20T16:00:00.000001Z", "2026-09-20T16:00:00.0000001Z", "2026-09-20T17:00:00+00:00", "invalid", False]:
                with self.subTest(key=key, value=value):
                    data = example()
                    data[key][0]["observed_at"] = value
                    with self.assertRaises(agarbild.ValidationError):
                        agarbild.render(data)


class CLITests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=SCRATCH)
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.source = self.base / "input.json"
        self.source.write_text(json.dumps(example(), ensure_ascii=False), encoding="utf-8")
        self.output = self.base / "new.html"
        self.before = self.source.read_bytes()

    def run_cli(self, source=None, output=None, args=None):
        command = [sys.executable, "-B", str(ROOT / "tools/agarbild.py")]
        command.extend(args if args is not None else [str(source or self.source), str(output or self.output)])
        return subprocess.run(command, capture_output=True, cwd=ROOT, timeout=10)

    def assert_rejected(self, result):
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertEqual(result.stdout, b"")
        self.assertEqual(result.stderr.decode("utf-8"), "Kunde inte skapa ägarbilden. Kontrollera underlag och nya lokala filsökvägar.\n")

    def test_real_cli_utf8_private_new_file_and_preservation(self):
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, b"")
        self.assertEqual(result.stderr, b"")
        self.assertEqual(self.output.read_text(encoding="utf-8"), agarbild.render(example()))
        self.assertEqual(stat.S_IMODE(self.output.stat().st_mode), 0o600)
        self.assertTrue(stat.S_ISREG(self.output.lstat().st_mode))
        self.assertEqual(self.source.read_bytes(), self.before)
        saved = self.output.read_bytes()
        self.assert_rejected(self.run_cli())
        self.assertEqual(self.output.read_bytes(), saved)
        newer = self.base / "newer.html"
        self.assertEqual(self.run_cli(output=newer).returncode, 0)
        self.assertEqual(self.output.read_bytes(), saved)

    def test_strict_json_and_validation_before_creation(self):
        valid = json.dumps(example())
        invalid = [valid.replace('"schema": 1', '"schema": 1, "schema": 1'),
                   valid.replace('"needed": "no"', '"needed": "no", "needed": "no"'),
                   *[valid.replace('"schema": 1', '"schema": ' + value) for value in ['NaN', 'Infinity', '-Infinity', '1e999', 'true']],
                   valid + '{}', '{', '[]', valid.replace('"schema": 1', '"schema": 2'),
                   valid.replace('"evidence": ["e2"]', '"evidence": []')]
        for raw in invalid:
            with self.subTest(raw=raw[:50]):
                self.source.write_text(raw, encoding="utf-8")
                snapshot = self.source.read_bytes()
                self.assert_rejected(self.run_cli())
                self.assertFalse(self.output.exists())
                self.assertEqual(self.source.read_bytes(), snapshot)
        self.source.write_bytes(b'\xff private-value')
        self.assert_rejected(self.run_cli())
        self.assertFalse(self.output.exists())

    def test_missing_input_directory_and_fifo_rejected(self):
        for path in [self.base / "missing.json", self.base]:
            self.assert_rejected(self.run_cli(source=path))
        fifo = self.base / "fifo.json"
        os.mkfifo(fifo)
        self.assert_rejected(self.run_cli(source=fifo))
        self.assertFalse(self.output.exists())

    def test_output_existing_objects_and_aliases_rejected(self):
        self.output.write_bytes(b"preserved")
        self.assert_rejected(self.run_cli())
        self.assertEqual(self.output.read_bytes(), b"preserved")
        self.assert_rejected(self.run_cli(output=self.source))
        alias = self.base / "alias.html"
        os.link(self.source, alias)
        self.assert_rejected(self.run_cli(output=alias))
        self.assertEqual(alias.read_bytes(), self.before)
        directory = self.base / "directory.html"
        directory.mkdir()
        self.assert_rejected(self.run_cli(output=directory))
        fifo = self.base / "fifo.html"
        os.mkfifo(fifo)
        self.assert_rejected(self.run_cli(output=fifo))
        self.assertEqual(self.source.read_bytes(), self.before)

    def test_symlink_files_and_ancestors_rejected(self):
        linked_input = self.base / "linked.json"
        linked_input.symlink_to(self.source)
        self.assert_rejected(self.run_cli(source=linked_input))
        self.output.symlink_to(self.source)
        self.assert_rejected(self.run_cli())
        self.assertEqual(self.source.read_bytes(), self.before)
        self.output.unlink()
        self.output.symlink_to(self.base / "absent")
        self.assert_rejected(self.run_cli())
        self.assertFalse((self.base / "absent").exists())
        self.output.unlink()
        directory = self.base / "real"
        directory.mkdir()
        (directory / "input.json").write_bytes(self.before)
        link = self.base / "linked"
        link.symlink_to(directory, target_is_directory=True)
        self.assert_rejected(self.run_cli(source=link / "input.json"))
        self.assert_rejected(self.run_cli(output=link / "out.html"))
        self.assert_rejected(self.run_cli(source=link / ".." / "input.json"))
        self.assert_rejected(self.run_cli(output=link / ".." / "out.html"))
        self.assertFalse((directory / "out.html").exists())
        self.assertFalse(self.output.exists())

    def test_missing_parents_and_bad_arguments_rejected(self):
        self.assert_rejected(self.run_cli(output=self.base / "missing" / "out.html"))
        self.assertFalse((self.base / "missing").exists())
        self.assert_rejected(self.run_cli(output=self.base / "input.json" / "out.html"))
        for args in [[], [str(self.source)], [str(self.source), str(self.output), "extra"]]:
            self.assert_rejected(self.run_cli(args=args))
        for tail in ("/", "/."):
            self.assert_rejected(self.run_cli(args=[str(self.source) + tail, str(self.output)]))
            self.assert_rejected(self.run_cli(args=[str(self.source), str(self.output) + tail]))
        self.assertFalse(self.output.exists())

    def test_exclusive_creation_if_file_appears_after_check(self):
        real_open = os.open
        def competing_open(path, flags, *args, **kwargs):
            if flags & os.O_CREAT:
                self.output.write_bytes(b"competing content")
                self.assertTrue(flags & os.O_EXCL)
                self.assertTrue(flags & os.O_NOFOLLOW)
            return real_open(path, flags, *args, **kwargs)
        with mock.patch("agarbild.os.open", side_effect=competing_open), mock.patch("sys.stderr"):
            self.assertEqual(agarbild.main([str(self.source), str(self.output)]), 2)
        self.assertEqual(self.output.read_bytes(), b"competing content")
        self.assertEqual(self.source.read_bytes(), self.before)


if __name__ == "__main__":
    unittest.main()
