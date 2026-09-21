"""Synthetic only; all filesystem fixtures live beneath the candidate's .scratch."""

from copy import deepcopy
from datetime import datetime
import gzip
from http.client import HTTPMessage
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
    def test_exact_local_file_extension(self):
        self.assertEqual(intake.LOCAL_FILES, (
            'runtime/worker.py', 'runtime/workflow.py', 'runtime/activities.py',
            'runtime/run.py', 'runtime/service.py', 'runtime/profile.py',
            'config/temporal-probe-requirements.lock', 'docs/runtime-v0.1.md',
            'runtime/daemon.py', 'runtime/shared.py', 'runtime/release.py',
            'runtime/private_workflow.py', 'runtime/private_activity.py',
            'runtime/private_stage.py', 'runtime/obligation.py',
        ))

    def test_dated_python_index_stable_numeric_and_installed_line_selection(self):
        for month in ('Aug.', 'August', 'Aug', 'Sep.', 'September', 'May', 'May.'):
            raw = (python_index('3.12.1') + (
                '<a href="/downloads/release/python-3129/">Python 3.12.9 - ' + month + ' 2, 2026</a>'
                '<a href="/downloads/release/python-31214/">Python 3.12.14 - ' + month + ' 12, 2026</a>'
                '<a href="/downloads/release/python-31399/">Python 3.13.99 - ' + month + ' 12, 2026</a>'
                '<a href="/downloads/release/python-31299/">Python 3.12.99rc1 - ' + month + ' 12, 2026</a>'
            ).encode())
            self.assertEqual(intake._python_index(raw, '3.12.1'), ('3.12.14', None))
        self.responses[intake.PYTHON_INDEX] = (
            '<a href="/downloads/release/python-3121/">Python 3.12.1 - Jan. 2, 2026</a>'
            '<a href="/downloads/release/python-31210/">Python 3.12.10 - August 12, 2026</a>'
        ).encode()
        self.assertTrue(self.collect()['complete'])

    def test_dated_python_label_mismatch_and_full_matching(self):
        for label in ('Python 3.12.14', 'Python 3.12.14 - Aug. 12, 2026'):
            raw = python_index('3.12.1') + (
                '<a href="/downloads/release/python-31213/">' + label + '</a>').encode()
            with self.assertRaises(intake.IntakeError):
                intake._python_index(raw, '3.12.1')
        for label in ('Python 3.12.1 - Aug. 12, 2026 extra', 'prefix Python 3.12.1',
                      'Python 3.12.1 - Nonsense 12, 2026', 'Python 3.12.1rc1',
                      'Python 03.12.1 - Aug. 12, 2026'):
            with self.assertRaises(intake.IntakeError):
                intake._python_index(('<a href="/downloads/release/python-3121/">'
                                     + label + '</a>').encode(), '3.12.1')

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
        self.assertEqual(len(packet["local"]), 30)
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
        self.assertEqual(sum(r["status"] == "unavailable" for r in packet["local"]), 15)

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

    def collect_via_transport(self, name, previous=None, overrides=None):
        responses = []

        def open_response(request, timeout):
            url = request.full_url
            body, headers = (overrides or {}).get(url, (
                gzip.compress(self.responses[url], mtime=0), (("Content-Encoding", "gzip"),)))
            response = Response(body, headers, url)
            responses.append(response)
            return response

        self.output = self.base / name
        with patch.object(urllib.request, "build_opener") as build:
            build.return_value.open.side_effect = open_response
            packet = intake.collect(self.output, self.roots, self.versions, previous)
        self.assertLessEqual(len(responses), 6)
        self.assertTrue(all(response.closed for response in responses))
        return packet

    def test_gzip_through_collect_preserves_decoded_representation_and_hashes(self):
        previous = self.collect()
        saved_previous = deepcopy(previous)
        saved_files = {p: p.read_bytes() for p in self.output.iterdir()}
        packet = self.collect_via_transport("gzip", previous)
        self.assertTrue(packet["complete"])
        self.assertTrue(packet["same_controlled_basis"])
        self.assertEqual(packet["fingerprint"], previous["fingerprint"])
        for record in packet["sources"]:
            raw = self.responses[record["url"]]
            self.assertEqual((self.output / record["path"]).read_bytes(), raw)
            self.assertEqual(record["sha256"], intake.sha256(raw).hexdigest())
            self.assertEqual(record["published_at"], next(
                r["published_at"] for r in previous["sources"] if r["id"] == record["id"]))
        self.assertEqual(json.loads((self.output / "packet.json").read_bytes()), packet)
        self.responses[intake._python_url("3.12.1")] += b"<p>new observation</p>"
        changed = self.collect_via_transport("changed-gzip", packet)
        self.assertTrue(changed["complete"])
        self.assertFalse(changed["same_controlled_basis"])
        self.assertNotEqual(changed["fingerprint"], packet["fingerprint"])
        self.assertEqual(previous, saved_previous)
        self.assertEqual({p: p.read_bytes() for p in saved_files}, saved_files)

    def test_old_compressed_packet_stays_immutable_after_repaired_intake(self):
        good = self.responses[intake.PYTHON_INDEX]
        self.responses[intake.PYTHON_INDEX] = gzip.compress(good, mtime=0)
        previous = self.collect()
        self.assert_incomplete(previous)
        saved_previous = deepcopy(previous)
        saved_files = {p: p.read_bytes() for p in self.output.iterdir()}
        self.responses[intake.PYTHON_INDEX] = good
        repaired = self.collect_via_transport("new-observation", previous)
        self.assertTrue(repaired["complete"])
        self.assertFalse(repaired["same_controlled_basis"])
        self.assertEqual(previous, saved_previous)
        self.assertEqual({p: p.read_bytes() for p in saved_files}, saved_files)

    def test_bad_transport_is_incomplete_with_independent_observations_preserved(self):
        previous = self.collect()
        good = gzip.compress(self.responses[intake.PYTHON_INDEX], mtime=0)
        cases = [
            (good[:-1], (("Content-Encoding", "gzip"),)),
            (good, (("Content-Encoding", "br"),)),
            (b"x" * (intake.MAX_BYTES + 1), (("Content-Encoding", "identity"),)),
            (gzip.compress(b"x" * (intake.MAX_BYTES + 1), mtime=0),
             (("Content-Encoding", "gzip"),)),
        ]
        for index, value in enumerate(cases):
            with self.subTest(index=index):
                packet = self.collect_via_transport("bad-transport-" + str(index), previous,
                                                    {intake.PYTHON_INDEX: value})
                self.assert_incomplete(packet)
                failed = next(r for r in packet["sources"] if r["id"] == "python-index")
                self.assertEqual(failed["error"], "source_retrieval_failed")
                self.assertFalse((self.output / "python-index.raw").exists())
                self.assertTrue(all(r["status"] == "available"
                                    for r in packet["sources"] + packet["local"]
                                    if r["id"] != "python-index"))


class Response(io.BytesIO):
    status = 200

    def __init__(self, body, headers=(), url=intake.PYTHON_INDEX):
        super().__init__(body)
        self.headers = HTTPMessage()
        for name, value in headers:
            self.headers.add_header(name, value)
        self.url = url
        self.read_sizes = []

    def read(self, size=-1):
        self.read_sizes.append(size)
        return super().read(size)

    def geturl(self):
        return self.url


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
            self.assertEqual(request.header_items(), [
                ("User-agent", intake.USER_AGENT), ("Accept-encoding", "identity")])
            self.assertEqual(build.return_value.open.call_args.kwargs, {"timeout": 10})

    def fetch_response(self, response):
        with patch.object(urllib.request, "build_opener") as build:
            build.return_value.open.return_value = response
            try:
                return intake.fetch(intake.PYTHON_INDEX)
            finally:
                build.return_value.open.assert_called_once()
                self.assertTrue(response.closed)
                self.assertTrue(all(size == intake.MAX_BYTES + 1 for size in response.read_sizes))
                self.assertLessEqual(len(response.read_sizes), 1)

    def test_identity_and_missing_encoding_preserve_bytes_without_sniffing(self):
        for raw in (b"", b"\xff\x00unchanged\r\n", gzip.compress(b"do not sniff", mtime=0)):
            for headers in ((), (("Content-Encoding", "identity"),),
                            (("content-encoding", " \tIdEnTiTy\t "),)):
                with self.subTest(raw=raw, headers=headers):
                    self.assertEqual(self.fetch_response(Response(raw, headers)), raw)

    def test_gzip_decodes_exact_bytes_and_empty_body(self):
        for raw in (b"", b"\xff\x00unchanged\r\n", b"<h1>synthetic</h1>", b'{ "synthetic": true }\n'):
            for token in ("gzip", "GZIP", " \tgZiP\t "):
                with self.subTest(raw=raw, token=token):
                    response = Response(gzip.compress(raw, mtime=0), (("cOnTeNt-EnCoDiNg", token),))
                    self.assertEqual(self.fetch_response(response), raw)

    def test_unsupported_empty_stacked_and_repeated_encodings(self):
        headers = [(("Content-Encoding", value),) for value in (
            "", " \t ", "br", "deflate", "x-gzip", "gzip, identity", "gzip,gzip",
            "identity, gzip", "gzip; secret=private", "secret private path")]
        headers += [(("Content-Encoding", first), ("content-encoding", second))
                    for first, second in (("gzip", "gzip"), ("identity", "identity"),
                                          ("identity", "gzip"), ("", "gzip"))]
        for values in headers:
            with self.subTest(headers=values), self.assertRaises(intake.IntakeError) as error:
                self.fetch_response(Response(gzip.compress(b"secret body", mtime=0), values))
            self.assertEqual(str(error.exception), "content_encoding_unsupported")

    def test_gzip_rejects_truncation_corruption_trailing_data_and_members(self):
        member = gzip.compress(b"secret body", mtime=0)
        bad_crc = member[:-8] + bytes([member[-8] ^ 1]) + member[-7:]
        bad_size = member[:-1] + bytes([member[-1] ^ 1])
        invalid = [member[:size] for size in range(len(member))]
        invalid += [b"secret private path", bad_crc, bad_size,
                    member + b"\x00", member + b"secret trailing data",
                    member + member, member + gzip.compress(b"", mtime=0)]
        for raw in invalid:
            with self.subTest(size=len(raw)), self.assertRaises(intake.IntakeError) as error:
                self.fetch_response(Response(raw, (("Content-Encoding", "gzip"),)))
            self.assertEqual(str(error.exception), "gzip_invalid")

    def test_separate_encoded_and_decoded_limits(self):
        for size in (intake.MAX_BYTES, intake.MAX_BYTES + 1):
            member = gzip.compress(b"small decoded body", mtime=0)
            # FCOMMENT pads a valid single member to an exact encoded size.
            padded = (member[:3] + bytes([member[3] | 16]) + member[4:10]
                      + b"c" * (size - len(member) - 1) + b"\x00" + member[10:])
            self.assertEqual(len(padded), size)
            cases = [
                (Response(b"x" * size), b"x" * size),
                (Response(b"x" * size, (("Content-Encoding", "identity"),)), b"x" * size),
                (Response(padded, (("Content-Encoding", "gzip"),)), b"small decoded body"),
                (Response(gzip.compress(b"x" * size, mtime=0),
                          (("Content-Encoding", "gzip"),)), b"x" * size),
            ]
            for response, expected in cases:
                with self.subTest(size=size, headers=list(response.headers.items()),
                                  encoded_size=len(response.getvalue())):
                    if size == intake.MAX_BYTES:
                        self.assertEqual(self.fetch_response(response), expected)
                    else:
                        with self.assertRaises(intake.IntakeError) as error:
                            self.fetch_response(response)
                        self.assertEqual(str(error.exception), "source_oversize")

    def test_gzip_large_expansion_is_bounded_before_allocation(self):
        raw = gzip.compress(b"x" * (intake.MAX_BYTES * 8), mtime=0)
        original = intake.zlib.decompressobj
        limits = []

        def bounded_decoder(*args):
            decoder = original(*args)

            class Guard:
                def decompress(self, data, max_length=0):
                    self.assert_limit(max_length)
                    return decoder.decompress(data, max_length)

                @staticmethod
                def assert_limit(limit):
                    if not 0 < limit <= intake.MAX_BYTES + 1:
                        raise AssertionError("unbounded expansion")
                    limits.append(limit)

            return Guard()

        with patch.object(intake.zlib, "decompressobj", side_effect=bounded_decoder):
            with self.assertRaises(intake.IntakeError) as error:
                self.fetch_response(Response(raw, (("Content-Encoding", "gzip"),)))
        self.assertEqual(str(error.exception), "source_oversize")
        self.assertTrue(limits)

    def test_gzip_does_not_bypass_status_or_final_url_checks(self):
        for status, url in ((404, intake.PYTHON_INDEX), (302, intake.PYTHON_INDEX),
                            (200, intake._python_url("3.12.1")), (200, "https://evil.invalid/")):
            response = Response(gzip.compress(b"body", mtime=0),
                                (("Content-Encoding", "gzip"),), url)
            response.status = status
            with self.subTest(status=status, url=url), self.assertRaises(intake.IntakeError) as error:
                self.fetch_response(response)
            self.assertEqual(str(error.exception), "http_or_redirect_error")
            self.assertEqual(response.read_sizes, [])

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
