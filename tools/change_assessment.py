"""Pure AP05 assessment of explicitly supplied, selected-source observations.

No hashing or source discovery is performed here. The host supplies observations.
"""

import copy
import datetime
import json
import re
import sys


def _object(value, keys, label):
    if not isinstance(value, dict) or set(value) != set(keys.split()):
        raise ValueError(label + " must have exactly these keys: " + keys)


def _text(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(label + " must be a nonempty string")


def _list(value, label, nonempty=False):
    if not isinstance(value, list) or (nonempty and not value):
        raise ValueError(label + " must be " + ("a nonempty list" if nonempty else "a list"))


def _enum(value, choices, label):
    _text(value, label)
    if value not in choices:
        raise ValueError(label + " has an unknown value")


def _timestamp(value, label):
    _text(value, label)
    # Allow basic and extended calendar/time forms. Keep ISO separators and
    # offset ranges explicit; datetime validates the actual calendar and time.
    match = re.fullmatch(
        r"(?P<date>\d{4}-\d{2}-\d{2}|\d{8})[Tt]"
        r"(?P<clock>\d{2}(?::?\d{2})?(?::?\d{2})?)(?:[.,](?P<fraction>\d+))?"
        r"(?P<zone>[Zz]|[+-](?P<hour>\d{2})(?::?(?P<minute>\d{2}))?)",
        value, flags=re.ASCII,
    )
    if match is None:
        raise ValueError(label + " must be a timezone-aware ISO8601 timestamp")
    # Parse only whole units with datetime: fromisoformat treats every fraction
    # as seconds, even when ISO8601 attaches it to an hour or minute.
    normalized = match["date"] + "T" + match["clock"] + match["zone"].upper()
    # datetime normalizes overflow in offset minutes; reject that explicitly.
    if match["hour"] is not None and (
        int(match["hour"]) > 23 or int(match["minute"] or "0") > 59
    ):
        raise ValueError(label + " has an invalid timezone offset")
    try:
        parsed = datetime.datetime.fromisoformat(normalized.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(label + " must be a valid calendar timestamp") from exc
    if parsed.utcoffset() is None:
        raise ValueError(label + " must include a timezone")
    offset = parsed.utcoffset()
    seconds = (parsed.toordinal() * 86400 + parsed.hour * 3600
               + parsed.minute * 60 + parsed.second
               - offset.days * 86400 - offset.seconds)
    unit = {2: 3600, 4: 60, 6: 1}[len(match["clock"].replace(":", ""))]
    # Build exact integers digit by digit, also avoiding int(string)'s digit
    # limit. No float or datetime microsecond truncation can hide an earlier check.
    numerator, denominator = 0, 1
    for digit in match["fraction"] or "":
        numerator = numerator * 10 + int(digit)
        denominator *= 10
    return seconds * denominator + numerator * unit, denominator


def _path(value):
    _text(value, "source path")
    if (value.startswith("/") or re.match(r"^[A-Za-z]:", value)
            or "\\" in value or "\x00" in value
            or any(part in ("", ".", "..") for part in value.split("/"))):
        raise ValueError("source path must be a safe POSIX relative path")


def _binding(value):
    _path(value["path"])
    digest = value["sha256"]
    if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise ValueError("sha256 must contain 64 lowercase hexadecimal characters")
    if type(value["size"]) is not int or value["size"] < 0:
        raise ValueError("size must be a nonnegative integer, not a boolean")


def _ids(items, keys, label):
    _list(items, label, nonempty=True)
    ids = set()
    for item in items:
        _object(item, keys, label + " entry")
        _text(item["id"], label + " id")
        if item["id"] in ids:
            raise ValueError(label + " ids must be unique")
        ids.add(item["id"])
    return ids


def _refs(value, known, label, nonempty=True):
    _list(value, label, nonempty)
    seen = set()
    for ref in value:
        _text(ref, label + " reference")
        if ref not in known or ref in seen:
            raise ValueError(label + " must contain unique, known references")
        seen.add(ref)


def _validate_case(case):
    _object(case, "schema id created_at sources claims actions next_action", "case")
    if type(case["schema"]) is not int or case["schema"] != 1:
        raise ValueError("case schema must be integer 1")
    _text(case["id"], "case id")
    _timestamp(case["created_at"], "created_at")
    sources = _ids(case["sources"], "id title version path sha256 size", "sources")
    claims = _ids(case["claims"], "id kind text reason standing sources", "claims")
    actions = _ids(case["actions"], "id text reason claims authority", "actions")
    paths = set()
    for source in case["sources"]:
        _text(source["title"], "source title")
        _text(source["version"], "source version")
        _binding(source)
        if source["path"] in paths:
            raise ValueError("source paths must be unique")
        paths.add(source["path"])
    for claim in case["claims"]:
        _enum(claim["kind"], ("fact", "judgment", "decision"), "claim kind")
        for key in ("text", "reason", "standing"):
            _text(claim[key], "claim " + key)
        _refs(claim["sources"], sources, "claim sources")
    for action in case["actions"]:
        for key in ("text", "reason"):
            _text(action[key], "action " + key)
        _refs(action["claims"], claims, "action claims")
        authority = action["authority"]
        _object(authority, "status scope sources", "authority")
        _enum(authority["status"], ("granted", "not_granted", "not_established"),
              "authority status")
        _text(authority["scope"], "authority scope")
        _refs(authority["sources"], sources, "authority sources",
              nonempty=authority["status"] == "granted")
    _text(case["next_action"], "next_action")
    if case["next_action"] not in actions:
        raise ValueError("next_action must reference an existing action")


def reference_manifest(case):
    """Validate the whole case and return its unchanged expected bindings."""
    _validate_case(case)
    return {"version": 1, "files": [
        {key: source[key] for key in ("path", "sha256", "size")}
        for source in sorted(case["sources"], key=lambda source: source["path"])
    ]}


def _validate_check(case, check, expected):
    _object(check, "checked_at manifest result", "check")
    checked, checked_scale = _timestamp(check["checked_at"], "checked_at")
    created, created_scale = _timestamp(case["created_at"], "created_at")
    if checked * created_scale < created * checked_scale:
        raise ValueError("checked_at cannot precede created_at")
    manifest = check["manifest"]
    _object(manifest, "version files", "manifest")
    if type(manifest["version"]) is not int or manifest["version"] != 1:
        raise ValueError("manifest version must be integer 1")
    _list(manifest["files"], "manifest files")
    for entry in manifest["files"]:
        _object(entry, "path sha256 size", "manifest entry")
        _binding(entry)
    if manifest != expected:
        raise ValueError("check manifest must equal the sorted reference manifest")
    result = check["result"]
    _object(result, "ok files", "result")
    if type(result["ok"]) is not bool:
        raise ValueError("result.ok must be a boolean")
    _list(result["files"], "result files")
    paths = {entry["path"] for entry in expected["files"]}
    statuses = {}
    for entry in result["files"]:
        _object(entry, "path status", "result entry")
        _text(entry["path"], "result path")
        if entry["path"] not in paths or entry["path"] in statuses:
            raise ValueError("result paths must be unique and present in the manifest")
        _enum(entry["status"], ("ok", "changed", "missing", "unsafe"), "result status")
        statuses[entry["path"]] = entry["status"]
    if result["ok"] != all(status == "ok" for status in statuses.values()):
        raise ValueError("result.ok contradicts the reported statuses")
    return statuses


def _annotate(item, dependencies, statuses):
    report = copy.deepcopy(item)
    report["affected_sources"] = [ref for ref in dependencies if statuses[ref] != "ok"]
    report["source_check"] = "needs_reassessment" if report["affected_sources"] else "unchanged"
    return report


def assess(case, check):
    """Report scoped reassessment needs without deciding truth or authority."""
    expected = reference_manifest(case)
    observations = _validate_check(case, check, expected)
    statuses = {source["id"]: observations.get(source["path"], "not_checked")
                for source in case["sources"]}
    report = {
        "schema": 1, "case_id": case["id"], "created_at": case["created_at"],
        "checked_at": check["checked_at"], "structure_valid": True,
        "source_checks": [{"id": ref, "status": status} for ref, status in statuses.items()],
        "coverage": {
            "checked": [ref for ref, status in statuses.items() if status != "not_checked"],
            "not_checked": [ref for ref, status in statuses.items() if status == "not_checked"],
            "complete_search": False,
        },
        "facts": [], "judgments": [], "decisions": [], "actions": [],
    }
    claims = {claim["id"]: claim for claim in case["claims"]}
    for claim in case["claims"]:
        report[claim["kind"] + "s"].append(_annotate(claim, claim["sources"], statuses))
    for action in case["actions"]:
        dependencies = set(action["authority"]["sources"])
        for ref in action["claims"]:
            dependencies.update(claims[ref]["sources"])
        ordered = [ref for ref in statuses if ref in dependencies]
        annotated = _annotate(action, ordered, statuses)
        report["actions"].append(annotated)
        if action["id"] == case["next_action"]:
            report["next_action"] = copy.deepcopy(annotated)
    report["limitations"] = [
        "Structural validity and source integrity are neither substantive approval nor authority.",
        "Unchanged selected sources do not establish exhaustive or necessarily current knowledge.",
        "Changed, missing, unsafe or not_checked sources require reassessment, not automatic "
        "falsehood of claims or revocation of decisions or authority.",
        "Observation, authority and standing are supplied judgments, not independently "
        "authenticated facts; source titles and versions are supplied labels, not proof.",
        "Timestamps describe only this comparison, not continuing validity or freshness.",
        "Re-running the same case preserves its expected versions and bindings. Revise assessments "
        "explicitly as NEW files retaining the predecessor.",
    ]
    return report


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def _reject_constant(value):
    raise ValueError("non-JSON constant is not allowed")


def _read_json(path):
    with open(path, "r", encoding="utf-8") as stream:
        return json.load(stream, object_pairs_hook=_unique_object, parse_constant=_reject_constant)


def main(argv=None):
    """CLI: input JSON reads and exactly one stdout JSON object, including errors."""
    args = sys.argv[1:] if argv is None else argv
    try:
        if len(args) == 2 and args[0] == "manifest":
            result = reference_manifest(_read_json(args[1]))
        elif len(args) == 3 and args[0] == "report":
            result = assess(_read_json(args[1]), _read_json(args[2]))
        else:
            raise ValueError("usage: change_assessment.py manifest CASE.json | report CASE.json CHECK.json")
    except (ValueError, OSError, RecursionError):
        # Avoid echoing input or local paths in errors; raw reports are still private.
        result = {"error": "Invalid input, unreadable JSON, or invalid command. "
                  "Expected: manifest CASE.json | report CASE.json CHECK.json"}
        code = 2
    else:
        code = 0
    print(json.dumps(result, ensure_ascii=True, allow_nan=False))
    return code


if __name__ == "__main__":
    sys.exit(main())
