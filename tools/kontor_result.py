"""Present a saved Runtime inspection without performing external access."""

import math
import re


_TARGET = "Nortropic/nortropic-projektkontor"
_PENDING_PHASES = frozenset({
    "accepted", "running_codex", "running_claude", "reviewing", "publishing",
    "waiting_access", "waiting_diagnosis", "waiting_review",
    "waiting_publication_reconciliation",
})
_REVISIONS = ("runtime_revision", "input_revision", "base", "candidate")


def _text(value):
    return type(value) is str and bool(value.strip())


def _timing(value):
    # Integers are finite without conversion to a potentially overflowing float.
    return ((type(value) is int and value >= 0)
            or (type(value) is float and math.isfinite(value) and value >= 0))


def _hex(value, length):
    return type(value) is str and re.fullmatch(r"[0-9a-f]{%d}" % length, value) is not None


def _json_copy(value, ancestors=None):
    """Copy JSON data, rejecting nonfinite numbers, objects and cycles."""
    if value is None or type(value) in (str, bool, int):
        return value
    if type(value) is float and math.isfinite(value):
        return value
    if type(value) not in (list, dict):
        raise ValueError("Not JSON data")
    ancestors = set() if ancestors is None else ancestors
    if id(value) in ancestors:
        raise ValueError("Cyclic data")
    ancestors.add(id(value))
    try:
        if type(value) is list:
            return [_json_copy(item, ancestors) for item in value]
        if any(type(key) is not str for key in value):
            raise ValueError("Nonstring JSON key")
        return {key: _json_copy(item, ancestors) for key, item in value.items()}
    finally:
        ancestors.remove(id(value))


def render(report):
    """Return a JSON-safe summary; Runtime owns verification and publication."""
    result = {
        "observation": "unavailable",
        "status": "unavailable",
        "live": False,
        "remote_current": False,
        "limitations": [
            "This is a saved Runtime observation, not current engine or remote "
            "status. No live GitHub verification is performed; the snapshot "
            "may be stale and this presentation is not independent delivery evidence."
        ],
    }
    if type(report) is not dict:
        result["error"] = "Runtime report is missing or malformed; expected a dictionary."
        return result

    problems = []
    for key in ("task_id", "phase", "target"):
        if key in report:
            if _text(report[key]):
                result[key] = report[key]
            else:
                problems.append("Missing or invalid " + key)

    for key in ("observed_at_epoch", "age_seconds"):
        if key in report:
            if _timing(report[key]):
                result[key] = report[key]
            else:
                problems.append("Invalid " + key)

    if type(report.get("error")) is str:
        result["error"] = report["error"]
    if "missing_evidence" in report:
        try:
            result["missing_evidence"] = _json_copy(report["missing_evidence"])
        except (ValueError, RecursionError):
            problems.append("Malformed missing_evidence")

    if report.get("observation") != "snapshot":
        problems.append("Saved Runtime observation unavailable or invalid; expected snapshot")

    phase = result.get("phase")
    if phase in _PENDING_PHASES:
        state = report.get("state")
        if state is not None and type(state) is not dict:
            problems.append("Malformed state")
        elif type(state) is dict and type(state.get("waiting_reason")) is str:
            result["waiting_reason"] = state["waiting_reason"]
        if not problems:
            result.update(observation="snapshot", status="not_delivered")
    elif phase == "completed":
        for key in ("task_id", "review_run"):
            if not _text(report.get(key)):
                problems.append("Missing or invalid " + key)
        if report.get("verified_delivery") is not True:
            problems.append("verified_delivery must be exactly true")
        if report.get("target") != _TARGET:
            problems.append("Missing or incorrect target")
        for key in ("observed_at_epoch", "age_seconds"):
            if key not in result:
                problems.append("Missing or invalid " + key)
        for key in _REVISIONS:
            if not _hex(report.get(key), 40):
                problems.append("Missing or invalid " + key)
        if not _hex(report.get("acceptance_sha256"), 64):
            problems.append("Missing or invalid acceptance_sha256")

        evidence = report.get("evidence")
        copied_evidence = None
        if (type(evidence) not in (str, list, dict) or not evidence
                or (type(evidence) is str and not _text(evidence))):
            problems.append("Missing or invalid evidence")
        else:
            try:
                copied_evidence = _json_copy(evidence)
            except (ValueError, RecursionError):
                problems.append("Malformed evidence: expected JSON data")

        integration = report.get("integration")
        if type(integration) is not dict:
            problems.append("Missing or malformed integration")
            integration = {}
        if integration.get("merged") is not True:
            problems.append("integration.merged must be exactly true")
        for key in ("merge_commit", "tree"):
            if not _hex(integration.get(key), 40):
                problems.append("Missing or invalid integration." + key)
        if integration.get("candidate") != report.get("candidate"):
            problems.append("integration.candidate does not match candidate")
        url = integration.get("url")
        if (type(url) is not str or re.fullmatch(
                r"https://github\.com/Nortropic/nortropic-projektkontor/pull/[1-9][0-9]*",
                url) is None):
            problems.append("Missing or invalid integration.url for the target pull request")

        if not problems:
            result.update(observation="snapshot", status="delivered")
            for key in _REVISIONS + ("acceptance_sha256", "review_run"):
                result[key] = report[key]
            for key in ("merge_commit", "tree", "url"):
                result[key] = integration[key]
            result["evidence"] = copied_evidence
    else:
        problems.append("Missing or unsupported phase")

    if problems:
        detail = "; ".join(problems)
        result["error"] = (result["error"] + "; " + detail
                           if result.get("error") else detail)
    return result
