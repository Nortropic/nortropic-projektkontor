"""Startkontrollen för ingången (UNDERHALL-INGANGAR-20260924), prövad mot riktiga Git-förråd i `.scratch`.

Varje prov bygger ett eget litet ursprung och en klon av det; inget verkligt förråd, ingen verklig Git-inställning och
inget nät används.
"""
import contextlib
import io
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock

import ingang


ROOT = Path(__file__).resolve().parents[1]
SCRATCH = ROOT / ".scratch"


class EntryCheckTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=SCRATCH)
        base = Path(self.temp.name)
        (base / "gitconfig").write_text("")
        environment = mock.patch.dict(os.environ, {
            "GIT_CONFIG_GLOBAL": str(base / "gitconfig"), "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_AUTHOR_NAME": "Prov", "GIT_AUTHOR_EMAIL": "prov@example.invalid",
            "GIT_COMMITTER_NAME": "Prov", "GIT_COMMITTER_EMAIL": "prov@example.invalid"})
        environment.start()
        self.addCleanup(environment.stop)
        self.seed, self.origin, self.entry = base / "seed", base / "origin.git", base / "ingang"
        self.git(base, "init", "--quiet", "-b", "main", str(self.seed))
        self.commit(self.seed, "docs/plan.md", "# Plan\n\nIngen gren namngiven.\n")
        self.git(base, "clone", "--quiet", "--bare", str(self.seed), str(self.origin))
        self.git(self.seed, "remote", "add", "origin", str(self.origin))
        self.git(base, "clone", "--quiet", str(self.origin), str(self.entry))

    def tearDown(self):
        self.temp.cleanup()

    def git(self, repo, *args):
        return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True).stdout.strip()

    def commit(self, repo, name, text):
        path = Path(repo) / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        self.git(repo, "add", name)
        self.git(repo, "commit", "--quiet", "-m", "prov: " + name)

    def publish_plan(self, text):
        self.commit(self.seed, "docs/plan.md", text)
        self.git(self.seed, "push", "--quiet", "origin", "main")

    def test_an_entry_on_main_equal_to_origin_has_no_warnings(self):
        self.assertEqual(ingang.check(self.entry), [])

    def test_another_branch_is_named(self):
        self.git(self.entry, "switch", "--quiet", "-c", "arbete/annan")
        self.git(self.entry, "push", "--quiet", "origin", "arbete/annan")
        self.assertEqual(ingang.check(self.entry), ["ingången står på arbete/annan, inte på main"])

    def test_a_detached_entry_is_named(self):
        self.git(self.entry, "switch", "--quiet", "--detach")
        self.assertEqual(ingang.check(self.entry), ["ingången står inte på en gren utan på en fristående commit"])

    def test_own_commits_and_lag_are_counted_and_point_to_the_plan_on_origin(self):
        self.commit(self.entry, "lokal.txt", "lokal\n")
        self.publish_plan("# Plan\n\nNy version på origin.\n")
        warnings = ingang.check(self.entry)
        self.assertEqual(len(warnings), 2, warnings)
        self.assertIn("(1 egna commits, 1 bakom)", warnings[0])
        self.assertIn("git show origin/main:docs/plan.md", warnings[0])
        self.assertTrue(warnings[1].startswith("lokala grenar utan kopia på origin"), warnings)

    def test_uncommitted_tracked_changes_are_counted_and_untracked_files_are_not(self):
        (self.entry / "docs/plan.md").write_text("ändrad lokalt\n")
        (self.entry / "ospårad.txt").write_text("ospårad\n")
        self.assertEqual(ingang.check(self.entry), ["1 spårade filer har ändringar som inte är committade"])

    def test_a_local_only_branch_warns_until_the_plan_on_origin_names_it(self):
        self.git(self.entry, "branch", "arbete/lokal")
        self.git(self.entry, "switch", "--quiet", "arbete/lokal")
        self.commit(self.entry, "lokal.txt", "lokal\n")
        self.git(self.entry, "switch", "--quiet", "main")
        self.assertEqual(ingang.check(self.entry),
                         ["lokala grenar utan kopia på origin och utan namngivet skäl i planen: arbete/lokal"])
        self.publish_plan("# Plan\n\nGrenen arbete/lokal är arkiverad; skäl namngivet.\n")
        warnings = ingang.check(self.entry)
        self.assertEqual(len(warnings), 1, warnings)
        self.assertIn("0 egna commits, 1 bakom", warnings[0])

    def test_a_failed_fetch_is_a_warning_and_the_comparison_still_runs(self):
        self.git(self.entry, "remote", "set-url", "origin", str(Path(self.temp.name) / "saknas.git"))
        self.assertEqual(ingang.check(self.entry), ["origin kunde inte hämtas; jämförelsen gäller senast hämtade läge"])

    def test_without_origin_main_the_entry_cannot_be_compared(self):
        self.git(self.entry, "update-ref", "-d", "refs/remotes/origin/main")
        self.assertEqual(ingang.check(self.entry, fetch=False), ["origin/main finns inte lokalt; ingången kan inte jämföras"])

    def test_the_check_changes_no_branch_file_or_configuration(self):
        self.commit(self.entry, "lokal.txt", "lokal\n")
        (self.entry / "docs/plan.md").write_text("ändrad lokalt\n")
        before = (self.git(self.entry, "rev-parse", "HEAD"), self.git(self.entry, "rev-parse", "--abbrev-ref", "HEAD"),
                  self.git(self.entry, "status", "--porcelain"), (self.entry / ".git/config").read_bytes())
        ingang.check(self.entry)
        after = (self.git(self.entry, "rev-parse", "HEAD"), self.git(self.entry, "rev-parse", "--abbrev-ref", "HEAD"),
                 self.git(self.entry, "status", "--porcelain"), (self.entry / ".git/config").read_bytes())
        self.assertEqual(before, after)

    def test_the_command_prints_each_warning_and_a_summary_and_always_exits_zero(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(ingang.main(["--no-fetch"], repo=self.entry), 0)
        self.assertEqual(out.getvalue(), "INGÅNG OK\n")
        self.git(self.entry, "switch", "--quiet", "--detach")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(ingang.main(["--no-fetch"], repo=self.entry), 0)
        self.assertEqual(out.getvalue(), "VARNING: ingången står inte på en gren utan på en fristående commit\n"
                                         "INGÅNG: 1 varningar\n")


if __name__ == "__main__":
    unittest.main()
