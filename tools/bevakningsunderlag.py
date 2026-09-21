"""Bounded, host-owned observations. Source content is evidence, never instructions."""

from contextlib import contextmanager
from collections.abc import Mapping
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import stat
import urllib.request


LOCAL_FILES = (
    "runtime/worker.py", "runtime/workflow.py", "runtime/activities.py",
    "runtime/run.py", "runtime/service.py", "runtime/profile.py",
    "config/temporal-probe-requirements.lock", "docs/runtime-v0.1.md",
    "runtime/daemon.py", "runtime/shared.py", "runtime/release.py",
)
MAX_BYTES = 1024 * 1024
TIMEOUT = 10
USER_AGENT = "Nortropic-Office-Intake/1"
PYTHON_INDEX = "https://www.python.org/downloads/source/"
TEMPORAL_BASE = "https://api.github.com/repos/temporalio/sdk-python/releases"
TEMPORAL_INDEX = TEMPORAL_BASE + "?per_page=20"
VERSION = r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)"
COVERAGE = (
    "Python: vald installerad major/minor-linje samt installerad utgåva. "
    "Temporal: stabila utgåvor bland de första 20 indexposterna samt installerad "
    "utgåva via tagg. Namngivna lokala filer i active och working. "
    "Ingen garanti för fullständigt källurval, sakgodkännande eller befogenhet."
)


class IntakeError(ValueError):
    """Only fixed, non-sensitive diagnostic reasons cross this boundary."""


def _allowed(url):
    return isinstance(url, str) and (
        url in (PYTHON_INDEX, TEMPORAL_INDEX)
        or re.fullmatch(r"https://www\.python\.org/downloads/release/python-[0-9]+/", url)
        or re.fullmatch(re.escape(TEMPORAL_BASE) + r"/tags/" + VERSION, url)
    )


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise IntakeError("redirect_denied")


def fetch(url):
    """One allowlisted HTTPS GET; build_opener is the synthetic transport seam."""
    if not _allowed(url):
        raise IntakeError("url_denied")
    try:
        opener = urllib.request.build_opener(
            urllib.request.ProxyHandler({}), _NoRedirect()
        )
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT}, method="GET")
        with opener.open(request, timeout=TIMEOUT) as response:
            if response.status != 200 or response.geturl() != url:
                raise IntakeError("http_or_redirect_error")
            raw = response.read(MAX_BYTES + 1)
            if len(raw) > MAX_BYTES:
                raise IntakeError("source_oversize")
            return raw
    except IntakeError:
        raise
    except Exception:
        raise IntakeError("http_or_network_error") from None


def _now():
    return datetime.now(timezone.utc).isoformat()


def _absolute(path):
    path = Path(path)
    if ".." in path.parts:
        raise IntakeError("unsafe_path")
    return path.absolute()


@contextmanager
def _directory(path):
    """Walk from / with no-follow descriptors, including every ancestor."""
    fd = None
    try:
        path = _absolute(path)
        # Ancestors need traversal permission, not permission to list their contents.
        flags = getattr(os, "O_SEARCH", getattr(os, "O_PATH", os.O_RDONLY))
        flags |= os.O_DIRECTORY | os.O_NOFOLLOW
        fd = os.open(path.anchor, flags)
        for part in path.parts[1:]:
            child = os.open(part, flags, dir_fd=fd)
            os.close(fd)
            fd = child
        yield fd
    finally:
        if fd is not None:
            os.close(fd)


@contextmanager
def _new_output(path):
    fd = None
    try:
        path = _absolute(path)
        with _directory(path.parent) as parent:
            os.mkdir(path.name, mode=0o700, dir_fd=parent)
            fd = os.open(path.name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent)
        os.fchmod(fd, 0o700)
    except (OSError, ValueError, TypeError):
        if fd is not None:
            os.close(fd)
        raise IntakeError("output_unavailable_or_exists") from None
    try:
        yield fd
    finally:
        os.close(fd)


def _write(directory, name, raw):
    try:
        fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                     0o600, dir_fd=directory)
        with os.fdopen(fd, "wb") as stream:
            os.fchmod(stream.fileno(), 0o600)
            stream.write(raw)
    except OSError:
        raise IntakeError("output_write_failed") from None


def _local_read(root, relative):
    try:
        with _directory(_absolute(root) / Path(relative).parent) as parent:
            fd = os.open(Path(relative).name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                         dir_fd=parent)
        with os.fdopen(fd, "rb") as stream:
            info = os.fstat(stream.fileno())
            if not stat.S_ISREG(info.st_mode):
                raise IntakeError("local_not_regular")
            if info.st_size > MAX_BYTES:
                raise IntakeError("local_oversize")
            raw = stream.read(MAX_BYTES + 1)
            if len(raw) > MAX_BYTES:
                raise IntakeError("local_oversize")
            return raw
    except IntakeError:
        raise
    except (OSError, ValueError, TypeError):
        raise IntakeError("local_missing_or_unsafe") from None


class _HTML(HTMLParser):
    def __init__(self, raw):
        super().__init__(convert_charrefs=True)
        self.links = []
        self.headings = []
        self.text = []
        self.link = None
        self.heading = None
        self.feed(raw.decode("utf-8"))
        self.close()

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.link = [dict(attrs).get("href", ""), []]
        if tag == "h1":
            self.heading = []

    def handle_data(self, data):
        self.text.append(data)
        if self.link is not None:
            self.link[1].append(data)
        if self.heading is not None:
            self.heading.append(data)

    def handle_endtag(self, tag):
        if tag == "a" and self.link is not None:
            self.links.append((self.link[0], "".join(self.link[1]).strip()))
            self.link = None
        if tag == "h1" and self.heading is not None:
            self.headings.append(" ".join("".join(self.heading).split()))
            self.heading = None


def _python_url(version):
    return "https://www.python.org/downloads/release/python-" + version.replace(".", "") + "/"


def _version_key(version):
    return tuple(int(part) for part in version.split("."))


def _python_index(raw, installed):
    found = set()
    for href, label in _HTML(raw).links:
        match = re.fullmatch(r"Python (" + VERSION + r")", label)
        if match:
            version = match[1]
            url = _python_url(version)
            if href not in (url, url.removeprefix("https://www.python.org")):
                raise IntakeError("python_index_version_url_mismatch")
            found.add(version)
    matching = [v for v in found if _version_key(v)[:2] == _version_key(installed)[:2]]
    if not matching or installed not in found:
        raise IntakeError("python_index_missing_version")
    return max(matching, key=_version_key), None


def _python_notes(raw, version):
    page = _HTML(raw)
    if page.headings != ["Python " + version]:
        raise IntakeError("python_release_mismatch")
    # Preserve the upstream date text, without synthesizing a time or timezone.
    match = re.search(r"Release Date:\s*([A-Za-z]+\.?\s+[0-9]{1,2},\s+[0-9]{4})",
                      " ".join(page.text))
    return None, match[1] if match else None


def _stable_release(entry):
    if not isinstance(entry, dict) or not isinstance(entry.get("tag_name"), str):
        raise IntakeError("temporal_malformed")
    if type(entry.get("draft")) is not bool or type(entry.get("prerelease")) is not bool:
        raise IntakeError("temporal_malformed")
    return (not entry["draft"] and not entry["prerelease"]
            and re.fullmatch(VERSION, entry["tag_name"]) is not None)


def _temporal_index(raw):
    entries = json.loads(raw)
    if not isinstance(entries, list):
        raise IntakeError("temporal_malformed")
    versions = [entry["tag_name"] for entry in entries[:20] if _stable_release(entry)]
    if not versions:
        raise IntakeError("temporal_index_missing_version")
    return max(versions, key=_version_key), None


def _temporal_notes(raw, version):
    entry = json.loads(raw)
    if not _stable_release(entry) or entry["tag_name"] != version:
        raise IntakeError("temporal_release_mismatch")
    published = entry.get("published_at")
    if published is not None:
        if not isinstance(published, str):
            raise IntakeError("temporal_malformed_date")
        try:
            date = datetime.fromisoformat(published.replace("Z", "+00:00"))
            if date.tzinfo is None:
                raise ValueError
        except ValueError:
            raise IntakeError("temporal_malformed_date") from None
    return None, published


def _record(identity, url=None):
    record = dict(id=identity, status="unavailable", observed_at=_now(),
                  sha256=None, path=None, error=None)
    if url is not None:
        record.update(url=url, published_at=None)
    return record


def _fingerprint(packet):
    basis = {"versions": packet["versions"]}
    for group in ("sources", "local"):
        basis[group] = sorted(
            ({key: record[key] for key in ("id", "status", "sha256")}
             for record in packet[group]), key=lambda record: record["id"])
    return sha256(json.dumps(basis, sort_keys=True, separators=(",", ":"),
                             ensure_ascii=True, allow_nan=False).encode()).hexdigest()


def collect(output, local_roots, versions, previous=None, fetcher=None):
    """Create a new private packet. No source, previous packet or reference is updated."""
    if not isinstance(local_roots, Mapping) or set(local_roots) != {"active", "working"}:
        raise IntakeError("invalid_local_roots")
    required = ("python", "temporalio", "active_config_sha256", "runtime_revision", "office_revision")
    if not isinstance(versions, Mapping) or any(
        not isinstance(versions.get(key), str) or not versions[key].strip() for key in required
    ):
        raise IntakeError("invalid_versions")
    if any(not re.fullmatch(VERSION, versions[key]) for key in ("python", "temporalio")):
        raise IntakeError("invalid_installed_version")
    try:
        version_copy = deepcopy(dict(versions))
        json.dumps(version_copy, allow_nan=False)
    except (TypeError, ValueError):
        raise IntakeError("invalid_versions") from None
    packet = dict(schema=1, observed_at=_now(), sources=[], local=[], versions=version_copy,
                  complete=False, fingerprint=None, same_controlled_basis=False, coverage=COVERAGE)
    fetcher = fetch if fetcher is None else fetcher
    with _new_output(output) as destination:
        def source(identity, url, parser):
            record = _record(identity, url)
            packet["sources"].append(record)
            try:
                if not _allowed(url):
                    raise IntakeError("url_denied")
                raw = fetcher(url)
                if not isinstance(raw, bytes):
                    raise IntakeError("source_not_bytes")
                if len(raw) > MAX_BYTES:
                    raise IntakeError("source_oversize")
            except Exception:
                record["error"] = "source_retrieval_failed"
                return None
            # Even malformed successful responses remain available for private inspection.
            name = identity + ".raw"
            _write(destination, name, raw)
            try:
                value, published = parser(raw)
            except Exception:
                record["error"] = "source_malformed_or_missing_version"
                return None
            record.update(status="available", sha256=sha256(raw).hexdigest(),
                          path=name, published_at=published)
            return value

        python_latest = source("python-index", PYTHON_INDEX,
                               lambda raw: _python_index(raw, versions["python"]))
        temporal_latest = source("temporal-index", TEMPORAL_INDEX, _temporal_index)
        for version in dict.fromkeys(v for v in (python_latest, versions["python"]) if v):
            source("python-" + version, _python_url(version),
                   lambda raw, v=version: _python_notes(raw, v))
        for version in dict.fromkeys(v for v in (temporal_latest, versions["temporalio"]) if v):
            source("temporal-" + version, TEMPORAL_BASE + "/tags/" + version,
                   lambda raw, v=version: _temporal_notes(raw, v))
        for root_name in ("active", "working"):
            for relative in LOCAL_FILES:
                record = _record(root_name + ":" + relative)
                packet["local"].append(record)
                try:
                    raw = _local_read(local_roots[root_name], relative)
                except IntakeError as error:
                    record["error"] = str(error)
                    continue
                name = root_name + "-" + relative.replace("/", "_")
                _write(destination, name, raw)
                record.update(status="available", sha256=sha256(raw).hexdigest(), path=name)
        packet["complete"] = all(r["status"] == "available" for r in packet["sources"] + packet["local"])
        if packet["complete"]:
            packet["fingerprint"] = _fingerprint(packet)
            packet["same_controlled_basis"] = (
                isinstance(previous, dict) and previous.get("complete") is True
                and previous.get("fingerprint") == packet["fingerprint"]
            )
        _write(destination, "packet.json", (json.dumps(packet, indent=2, ensure_ascii=True,
                                                       allow_nan=False) + "\n").encode())
    return packet
