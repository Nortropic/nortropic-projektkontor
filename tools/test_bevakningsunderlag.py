"""Synthetic only; all filesystem fixtures live beneath the candidate's .scratch."""

from copy import deepcopy
from datetime import datetime
import io
import json
import os
from pathlib import Path
import stat
import tempfile
import unittest
from unittest.mock import patch
import urllib.error
import urllib.request

import bevakningsunderlag as intake


SCRATCH = Path(__file__).absolute().parents[1] / ".scratch"


def release(version, **overrides):
    return dict(tag_name=version, draft=False, prerelease=False,
                published_at="2026-01-02T03:04:05Z", **overrides)


def encoded(value):
    return json.dumps(value).encode()


def python_index(*versions):
    return ("<html>" + "".join(
        '<a href="' + intake._python_url(v) + '">Python ' + v + '</a>'
        for v in versions) + "</html>").encode()


class CollectionTests(unittest.TestCase):
    def setUp(self):
        SCRATCH.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=SCRATCH)
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.roots = {name: self.base / name for name in ("active", "working")}
        for root in self.roots.values():
            for name in intake.LOCAL_FILES:
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"synthetic source: " + name.encode())
        self.versions = dict(python="3.12.1", temporalio="1.8.0",
                             active_config_sha256="a" * 64, runtime_revision="synthetic-runtime",
                             office_revision="synthetic-office")
        self.responses = {
            intake.PYTHON_INDEX: python_index("3.12.1", "3.12.9", "3.12.10", "3.13.1"),
            intake.TEMPORAL_INDEX: encoded([
                release("1.9.0"), release("1.10.0"),
                dict(tag_name="9.0.0", draft=True, prerelease=False),
                dict(tag_name="8.0.0", draft=False, prerelease=True),
                dict(tag_name="7.0.0rc1", draft=False, prerelease=False),
            ]),
        }
        for v in ("3.12.1", "3.12.10"):
            self.responses[intake._python_url(v)] = (
                '<h1>Python ' + v + '</h1><p><strong>Release Date:</strong> Jan. 2, 2026</p>'
            ).encode()
        for v in ("1.8.0", "1.10.0"):
            self.responses[intake.TEMPORAL_BASE + "/tags/" + v] = encoded(release(v))
        self.calls = []
        self.counter = 0
        # Fail immediately if any collection test accidentally uses real transport.
        self.network = patch.object(urllib.request, "build_opener", side_effect=AssertionError("network forbidden"))
        self.network.start()
        self.addCleanup(self.network.stop)

    def fetcher(self, url):
        self.calls.append(url)
        value = self.responses[url]
        if isinstance(value, Exception):
            raise value
        return value

    def collect(self, previous=None):
        self.counter += 1
        self.output = self.base / ("packet-" + str(self.counter))
        return intake.collect(self.output, self.roots, self.versions, previous, self.fetcher)

    def assert_incomplete(self, packet):
        self.assertFalse(packet["complete"])
        self.assertIsNone(packet["fingerprint"])
        self.assertFalse(packet["same_controlled_basis"])
        for record in packet["sources"] + packet["local"]:
            if record["status"] == "unavailable":
                self.assertIsNone(record["sha256"])
                self.assertIsNone(record["path"])
                self.assertTrue(record["error"])
                self.assertNotIn(str(self.base), record["error"])

    def test_valid_selection_raw_bytes_permissions_and_no_original_writes(self):
        originals = {p: (p.read_bytes(), p.stat().st_mtime_ns, p.stat().st_mode)
                     for root in self.roots.values() for p in root.rglob("*") if p.is_file()}
        packet = self.collect()
        self.assertTrue(packet["complete"])
        self.assertEqual(packet["schema"], 1)
        self.assertEqual(len(self.calls), 6)
        self.assertEqual(len(packet["local"]), 22)
        self.assertEqual(len(packet["fingerprint"]), 64)
        self.assertFalse(packet["same_controlled_basis"])
        self.assertEqual(json.loads((self.output / "packet.json").read_bytes()), packet)
        for record in packet["sources"] + packet["local"]:
            self.assertIsNotNone(datetime.fromisoformat(record["observed_at"]).tzinfo)
            self.assertFalse(Path(record["path"]).is_absolute())
            raw = (self.output / record["path"]).read_bytes()
            self.assertEqual(intake.sha256(raw).hexdigest(), record["sha256"])
            if "url" in record:
                self.assertEqual(raw, self.responses[record["url"]])
        self.assertEqual(stat.S_IMODE(self.output.stat().st_mode), 0o700)
        for file in self.output.iterdir():
            self.assertEqual(stat.S_IMODE(file.stat().st_mode), 0o600)
        for p, expected in originals.items():
            self.assertEqual((p.read_bytes(), p.stat().st_mtime_ns, p.stat().st_mode), expected)
        notes = {r["id"]: r for r in packet["sources"]}
        self.assertEqual(notes["python-3.12.1"]["published_at"], "Jan. 2, 2026")
        self.assertEqual(notes["temporal-1.8.0"]["published_at"], "2026-01-02T03:04:05Z")

    def test_unchanged_previous_immutable_and_versions_copied(self):
        previous = self.collect()
        saved = deepcopy(previous)
        old_file = (self.output / "packet.json").read_bytes()
        old_output = self.output
        packet = self.collect(previous)
        self.assertTrue(packet["same_controlled_basis"])
        self.assertNotEqual(packet["observed_at"], previous["observed_at"])
        self.assertEqual(previous, saved)
        self.assertEqual((old_output / "packet.json").read_bytes(), old_file)
        self.versions["runtime_revision"] = "changed"
        self.assertNotEqual(packet["versions"], self.versions)
        self.assertFalse(self.collect(packet)["same_controlled_basis"])

    def test_external_and_each_local_root_changes(self):
        previous = self.collect()
        self.responses[intake._python_url("3.12.1")] += b"<p>changed</p>"
        external = self.collect(previous)
        self.assertTrue(external["complete"])
        self.assertFalse(external["same_controlled_basis"])
        for root in self.roots.values():
            (root / intake.LOCAL_FILES[0]).write_bytes(b"changed local source")
            changed = self.collect(external)
            self.assertFalse(changed["same_controlled_basis"])
            self.assertTrue(changed["complete"])
            external = changed

    def test_dedup_and_first_twenty_only(self):
        self.versions.update(python="3.12.10", temporalio="1.10.0")
        self.responses[intake.TEMPORAL_INDEX] = encoded([release("1.10.0")] * 20 + [release("99.0.0")])
        self.assertTrue(self.collect()["complete"])
        self.assertEqual(len(self.calls), 4)
        self.assertEqual(len(set(self.calls)), 4)

    def test_per_observation_clock_and_absent_publication_date(self):
        self.responses[intake._python_url("3.12.1")] = b"<h1>Python 3.12.1</h1>"
        detail = release("1.8.0")
        detail.pop("published_at")
        self.responses[intake.TEMPORAL_BASE + "/tags/1.8.0"] = encoded(detail)
        with patch.object(intake, "_now", side_effect=[str(i) for i in range(50)]):
            packet = self.collect()
        records = packet["sources"] + packet["local"]
        self.assertEqual(len({r["observed_at"] for r in records}), len(records))
        for identity in ("python-3.12.1", "temporal-1.8.0"):
            self.assertIsNone(next(r for r in records if r["id"] == identity)["published_at"])

    def test_external_failures_preserve_other_observations_and_raw_malformed(self):
        previous = self.collect()
        good = deepcopy(self.responses)
        cases = [
            (intake.PYTHON_INDEX, b"<html>no versions</html>"),
            (intake.PYTHON_INDEX, python_index("3.12.10")),
            (intake.PYTHON_INDEX, python_index("3.13.1")),
            (intake.PYTHON_INDEX, b"x" * (intake.MAX_BYTES + 1)),
            (intake.TEMPORAL_INDEX, b"not json"),
            (intake.TEMPORAL_INDEX, b"{}"),
            (intake.TEMPORAL_INDEX, b"[]"),
            (intake.TEMPORAL_INDEX, b"[{}]"),
            (intake.TEMPORAL_INDEX, OSError("private secret " + str(self.base))),
            (intake._python_url("3.12.1"), b"<h1>Python 3.12.2</h1>"),
            (intake._python_url("3.12.1"), b"\xff"),
            (intake.TEMPORAL_BASE + "/tags/1.8.0", encoded(release("1.8.1"))),
            (intake.TEMPORAL_BASE + "/tags/1.8.0", urllib.error.HTTPError("secret", 404, "missing", {}, None)),
            (intake.TEMPORAL_BASE + "/tags/1.8.0", "not bytes"),
        ]
        for url, value in cases:
            with self.subTest(url=url, kind=type(value).__name__):
                self.responses = dict(good, **{url: value})
                self.calls.clear()
                packet = self.collect(previous)
                self.assert_incomplete(packet)
                self.assertLessEqual(len(self.calls), 6)
                self.assertEqual(self.calls[:2], [intake.PYTHON_INDEX, intake.TEMPORAL_INDEX])
                self.assertTrue(all(r["status"] == "available" for r in packet["local"]))
                self.assertTrue(any(r["status"] == "available" for r in packet["sources"]))
                if isinstance(value, bytes) and len(value) <= intake.MAX_BYTES:
                    identity = next(r["id"] for r in packet["sources"] if r["url"] == url)
                    self.assertEqual((self.output / (identity + ".raw")).read_bytes(), value)
        self.responses = good
        self.assertFalse(self.collect(packet)["same_controlled_basis"])

    def test_python_index_version_url_mismatch_never_unchanged(self):
        previous = self.collect()
        for href in (intake._python_url("3.12.9"), "/downloads/release/python-3129/"):
            with self.subTest(href=href):
                raw = python_index("3.12.1").replace(
                    b"</html>",
                    ('<a href="' + href + '">Python 3.12.10</a></html>').encode(),
                )
                self.responses[intake.PYTHON_INDEX] = raw
                first = self.collect(previous)
                first_output = self.output
                saved = deepcopy(first)
                saved_files = {p: p.read_bytes() for p in first_output.iterdir()}
                repeated = self.collect(first)
                for packet, output in ((first, first_output), (repeated, self.output)):
                    self.assert_incomplete(packet)
                    index = next(r for r in packet["sources"] if r["id"] == "python-index")
                    self.assertEqual(index["status"], "unavailable")
                    self.assertEqual(index["error"], "source_malformed_or_missing_version")
                    self.assertEqual((output / "python-index.raw").read_bytes(), raw)
                    self.assertTrue(all(r["status"] == "available"
                                        for r in packet["sources"] + packet["local"]
                                        if r["id"] != "python-index"))
                    self.assertEqual(json.loads((output / "packet.json").read_bytes()), packet)
                self.assertEqual(first, saved)
                self.assertEqual({p: p.read_bytes() for p in first_output.iterdir()}, saved_files)

    def test_local_missing_oversize_and_exact_limit(self):
        target = self.roots["active"] / intake.LOCAL_FILES[0]
        target.unlink()
        self.assert_incomplete(self.collect())
        target.write_bytes(b"x" * (intake.MAX_BYTES + 1))
        self.assert_incomplete(self.collect())
        target.write_bytes(b"x" * intake.MAX_BYTES)
        self.assertTrue(self.collect()["complete"])

    def test_local_symlink_file_directory_root_and_ancestor(self):
        target = self.roots["active"] / intake.LOCAL_FILES[0]
        target.unlink()
        target.symlink_to(self.roots["working"] / intake.LOCAL_FILES[0])
        self.assert_incomplete(self.collect())
        target.unlink()
        target.write_bytes(b"restored")
        runtime = self.roots["active"] / "runtime"
        runtime.rename(runtime.with_name("saved-runtime"))
        runtime.symlink_to(self.roots["working"] / "runtime", target_is_directory=True)
        self.assert_incomplete(self.collect())
        for suffix in ("", "/runtime/.."):
            alias = self.base / ("root-link" + str(len(suffix)))
            alias.symlink_to(self.roots["working"], target_is_directory=True)
            self.roots["active"] = Path(str(alias) + suffix)
            self.assert_incomplete(self.collect())
        parent_alias = self.base / "parent-link"
        parent_alias.symlink_to(self.base, target_is_directory=True)
        self.roots["active"] = parent_alias / "working"
        self.assert_incomplete(self.collect())

    def test_local_directory_fifo_and_missing_root(self):
        target = self.roots["active"] / intake.LOCAL_FILES[0]
        target.unlink()
        target.mkdir()
        self.assert_incomplete(self.collect())
        target.rmdir()
        os.mkfifo(target)
        self.assert_incomplete(self.collect())
        self.roots["active"] = self.base / "missing"
        packet = self.collect()
        self.assert_incomplete(packet)
        self.assertEqual(sum(r["status"] == "unavailable" for r in packet["local"]), 11)

    def test_existing_output_and_symlink_ancestors_preserved_before_fetch(self):
        output = self.base / "existing"
        output.mkdir()
        sentinel = output / "sentinel"
        sentinel.write_bytes(b"unchanged")
        link = self.base / "link"
        link.symlink_to(output, target_is_directory=True)
        dangling = self.base / "dangling"
        dangling.symlink_to(self.base / "absent")
        for path in (output, sentinel, link, dangling, link / "new", link / ".." / "escaped"):
            with self.subTest(path=path.name), self.assertRaises(intake.IntakeError) as error:
                intake.collect(path, self.roots, self.versions, fetcher=self.fetcher)
            self.assertNotIn(str(self.base), str(error.exception))
        self.assertEqual(sentinel.read_bytes(), b"unchanged")
        self.assertEqual(list(output.iterdir()), [sentinel])
        self.assertEqual(self.calls, [])

    def test_input_validation_and_default_fetch_seam(self):
        for key in self.versions:
            invalid = dict(self.versions, **{key: ""})
            with self.assertRaises(intake.IntakeError):
                intake.collect(self.base / "invalid", self.roots, invalid, fetcher=self.fetcher)
        with self.assertRaises(intake.IntakeError):
            intake.collect(self.base / "invalid", {"working": self.roots["working"]}, self.versions)
        with patch.object(intake, "fetch", side_effect=self.fetcher):
            self.assertTrue(intake.collect(self.base / "default", self.roots, self.versions)["complete"])


class Response(io.BytesIO):
    status = 200

    def geturl(self):
        return intake.PYTHON_INDEX


class TransportTests(unittest.TestCase):
    def test_transport_controls_and_exact_bytes(self):
        with patch.object(urllib.request, "build_opener") as build:
            build.return_value.open.return_value = Response(b"\xff\x00raw bytes")
            self.assertEqual(intake.fetch(intake.PYTHON_INDEX), b"\xff\x00raw bytes")
            handlers = build.call_args.args
            self.assertEqual(handlers[0].proxies, {})
            self.assertIsInstance(handlers[1], urllib.request.HTTPRedirectHandler)
            request = build.return_value.open.call_args.args[0]
            self.assertEqual(request.get_method(), "GET")
            self.assertEqual(request.header_items(), [("User-agent", intake.USER_AGENT)])
            self.assertEqual(build.return_value.open.call_args.kwargs, {"timeout": 10})

    def test_unknown_urls_denied_before_transport(self):
        urls = ["http://www.python.org/downloads/source/", intake.PYTHON_INDEX + "?x=1",
                "https://user:pass@www.python.org/downloads/source/",
                "https://www.python.org:443/downloads/source/", intake.PYTHON_INDEX + "#x",
                "https://evil.invalid/", intake.TEMPORAL_BASE + "?per_page=21",
                intake.TEMPORAL_BASE + "/tags/1.2.3rc1", intake.TEMPORAL_BASE + "/tags/1.2.3/../x",
                intake.PYTHON_INDEX + "\n", " https://www.python.org/downloads/source/"]
        with patch.object(urllib.request, "build_opener") as build:
            for url in urls:
                with self.subTest(url=url), self.assertRaises(intake.IntakeError):
                    intake.fetch(url)
            build.assert_not_called()

    def test_redirect_handler_never_follows_even_allowed_destination(self):
        # Exercise urllib's real redirect dispatch without a socket.
        handler = intake._NoRedirect()
        request = urllib.request.Request(intake.PYTHON_INDEX)
        for code in (301, 302, 303, 307, 308):
            with self.subTest(code=code), self.assertRaises(intake.IntakeError):
                getattr(handler, "http_error_" + str(code))(
                    request, io.BytesIO(), code, "redirect", {"location": intake._python_url("3.12.1")})

    def test_oversize_http_and_network_errors_are_safe(self):
        with patch.object(urllib.request, "build_opener") as build:
            for size in (intake.MAX_BYTES, intake.MAX_BYTES + 1):
                build.return_value.open.return_value = Response(b"x" * size)
                if size == intake.MAX_BYTES:
                    self.assertEqual(len(intake.fetch(intake.PYTHON_INDEX)), size)
                else:
                    with self.assertRaises(intake.IntakeError):
                        intake.fetch(intake.PYTHON_INDEX)
            bad = Response(b"error")
            bad.status = 302
            build.return_value.open.return_value = bad
            with self.assertRaises(intake.IntakeError):
                intake.fetch(intake.PYTHON_INDEX)
            build.return_value.open.side_effect = OSError("secret private path")
            with self.assertRaises(intake.IntakeError) as error:
                intake.fetch(intake.PYTHON_INDEX)
            self.assertNotIn("secret", str(error.exception))


if __name__ == "__main__":
    unittest.main()
