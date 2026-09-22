"""Hand the AP11 reconciliation over to the existing AP08 owner view.

Pure translation layer (AP11 delivery B). The reconciliation is produced by
``development_result.reconcile`` and the HTML by ``agarbild.render``; both are
reached through the module attribute at call time, exactly once per call. This
module reimplements neither. It performs no I/O, reads no clock, starts nothing
and grants no authority: it only rearranges supplied data into a report picture
that the existing reader already knows how to validate and escape.

Documented deterministic behaviours:

* ``next_action.authority`` is always taken from ``goal["next_action"]``. A
  supplied picture that states a different authority never widens the reported
  one; the conflict is overridden and recorded as an issue.
* A saved observation later than the picture's ``generated_at`` raises
  ``ValueError`` instead of returning a picture ``agarbild.validate`` rejects or
  silently re-dating the observation.
"""

import copy
import datetime as dt
import re

import agarbild
import development_result


_RECONCILIATION_ID = "ap11-handoff-reconciliation"
_OBSERVATION_ID = "ap11-handoff-observation"

# Only a supported delivery is finished; every other status stays non-finished.
_STATES = {
    "delivery_supported": "finished",
    "missing": "unknown",
    "ambiguous": "unknown",
    "not_supported": "unknown",
}
_STATUS_TEXT = {
    "delivery_supported": "leverans stöds av den sparade observationen",
    "missing": "ingen sparad observation binder kravet",
    "ambiguous": "flera sparade observationer, inget urval",
    "not_supported": "den sparade observationen stöder inte leverans",
}
_UNKNOWN_STATUS = "okänd status i avstämningen"
_NO_REVISION = "Revision saknas i den sparade observationen"
_NO_MERGE_COMMIT = "Integrationscommit saknas i den sparade observationen"
_READING_NOTE = ("Detta är en daterad läsning av sparat underlag, inte liveläge, "
                 "inte fjärrstatus och inte aktivering.")
_WHOLE_GOAL_NOTE = ("Avstämningen redovisar inget avslutat helmål "
                    "(whole_goal_complete är False); den separata slutgranskningen "
                    "avgör helmålet.")


def _text(value):
    return type(value) is str and bool(value.strip())


def _key(data, name, label):
    if name not in data:
        raise ValueError("%s saknar %r" % (label, name))
    return data[name]


def _iso(epoch):
    """ISO8601 UTC for a saved observation time; no clock is consulted."""
    try:
        return dt.datetime.fromtimestamp(epoch, dt.timezone.utc).isoformat()
    except (OverflowError, OSError, ValueError, TypeError):
        raise ValueError("observed_at_epoch kan inte uttryckas som ISO8601 UTC") from None


def _parsed(value):
    """Best-effort aware datetime, or None when agarbild must judge the value."""
    if type(value) is not str:
        return None
    text = value.strip()
    if text[-1:] in ("Z", "z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = dt.datetime.fromisoformat(text)
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else None


def _fresh_id(base, used):
    identifier = base
    suffix = 2
    while identifier in used:
        identifier = "%s-%d" % (base, suffix)
        suffix += 1
    used.add(identifier)
    return identifier


def _digest(value):
    return value if type(value) is str and re.fullmatch(r"[0-9a-f]{64}", value) else None


def _observation_evidence(entry, index, used, generated):
    """Append-only evidence for a requirement whose result carries a saved time."""
    result = entry.get("result")
    if type(result) is not dict or "observed_at_epoch" not in result:
        return None
    observed_at = _iso(result["observed_at_epoch"])
    observed = _parsed(observed_at)
    if generated is not None and observed is not None and observed > generated:
        raise ValueError(
            "Den sparade observationen för krav %r är senare än generated_at; "
            "ägarbilden får varken bli ogiltig eller omdateras" % entry.get("id"))
    revision = result.get("runtime_revision")
    revision = revision if _text(revision) else _NO_REVISION
    merge_commit = result.get("merge_commit")
    merge_commit = merge_commit if _text(merge_commit) else _NO_MERGE_COMMIT
    return {
        "id": _fresh_id("%s-%d" % (_OBSERVATION_ID, index), used),
        "title": "Sparad Runtime-observation för krav %s" % entry.get("id"),
        "kind": "Sparad Runtime-observation (ej verifierad här)",
        "observed_at": observed_at,
        "revision": revision,
        "locator": merge_commit,
        "sha256": _digest(result.get("acceptance_sha256")),
        "text": ("Runtime-revision: %s. Integrationscommit: %s. Observationens "
                 "status enligt den sparade läsningen: %s. %s"
                 % (revision, merge_commit, result.get("status"), _READING_NOTE)),
    }


def _work_item(entry, evidence_ids, observed_at):
    status = entry.get("status")
    problems = entry.get("problems")
    problems = [item for item in problems if _text(item)] if type(problems) is list else []
    lines = ["Status enligt avstämningen: %s (%s)."
             % (status, _STATUS_TEXT.get(status, _UNKNOWN_STATUS))]
    lines.append("Registrerade problem: " + "; ".join(problems) if problems
                 else "Inga problem registrerade i avstämningen.")
    lines.append(_READING_NOTE)
    return {
        # The requirement text is carried verbatim; agarbild does the escaping.
        "title": "Krav %s: %s" % (entry.get("id"), entry.get("text")),
        "state": _STATES.get(status, "unknown"),
        "text": "\n".join(lines),
        # The saved observation's own time, never a render time.
        "observed_at": observed_at,
        "evidence": list(evidence_ids),
    }


def present(goal, reports, picture):
    """Return the reconciliation, a derived report picture and its AP08 HTML.

    ``goal`` and ``reports`` are handed to ``development_result.reconcile``
    unchanged and its rejections propagate before any picture is built. The
    picture is derived from ``picture``: its evidence list stays the leading
    prefix, ``owner_decision`` is carried over and only new entries are added.
    """
    reconciliation = development_result.reconcile(goal, reports)
    if type(reconciliation) is not dict or type(reconciliation.get("requirements")) is not list:
        raise ValueError("avstämningen har inte det förväntade svaret")
    if reconciliation.get("whole_goal_complete") is not False:
        raise ValueError("avstämningen får inte redovisa ett avslutat helmål")
    if type(picture) is not dict:
        raise ValueError("picture måste vara en dict")

    goal_action = goal["next_action"]
    authority = goal_action["authority"]
    if authority not in agarbild.AUTHORITIES:
        raise ValueError("goal.next_action.authority är inte en känd befogenhet")

    supplied_evidence = _key(picture, "evidence", "picture")
    if type(supplied_evidence) is not list:
        raise ValueError("picture.evidence måste vara en lista")
    supplied_action = _key(picture, "next_action", "picture")
    if type(supplied_action) is not dict:
        raise ValueError("picture.next_action måste vara en dict")
    supplied_issues = _key(picture, "issues", "picture")
    if type(supplied_issues) is not list:
        raise ValueError("picture.issues måste vara en lista")

    generated_at = _key(picture, "generated_at", "picture")
    generated = _parsed(generated_at)
    used = {item["id"] for item in supplied_evidence
            if type(item) is dict and type(item.get("id")) is str}

    evidence = copy.deepcopy(supplied_evidence)
    reconciliation_id = _fresh_id(_RECONCILIATION_ID, used)
    evidence.append({
        "id": reconciliation_id,
        "title": "Avstämning av målets krav mot sparade observationer",
        "kind": "Avstämning i minnet (development_result.reconcile)",
        "observed_at": None,
        "revision": str(reconciliation.get("goal_id")),
        "locator": "development_result.reconcile(goal, reports)",
        "sha256": None,
        "text": ("Avstämningen jämför målets namngivna krav med sparade "
                 "Runtime-observationer. live=%s, remote_current=%s, "
                 "whole_goal_complete=%s. %s"
                 % (reconciliation.get("live"), reconciliation.get("remote_current"),
                    reconciliation.get("whole_goal_complete"), _READING_NOTE)),
    })

    work = []
    for index, entry in enumerate(reconciliation["requirements"], 1):
        if type(entry) is not dict:
            raise ValueError("avstämningens krav måste vara dictar")
        observation = _observation_evidence(entry, index, used, generated)
        references = [reconciliation_id]
        observed_at = None
        if observation is not None:
            evidence.append(observation)
            references.append(observation["id"])
            observed_at = observation["observed_at"]
        work.append(_work_item(entry, references, observed_at))

    issues = copy.deepcopy(supplied_issues)
    limitations = reconciliation.get("limitations")
    for limitation in (limitations if type(limitations) is list else []):
        issues.append({"text": limitation, "evidence": [reconciliation_id]})
    issues.append({"text": _WHOLE_GOAL_NOTE, "evidence": [reconciliation_id]})
    if supplied_action.get("authority") != authority:
        issues.append({
            "text": ("Den tillförda ägarbilden angav befogenheten %r för nästa "
                     "handling. Befogenheten tas alltid från målet och redovisas "
                     "som %r; ingen vidare befogenhet härleds här."
                     % (supplied_action.get("authority"), authority)),
            "evidence": [reconciliation_id],
        })

    owner = goal_action.get("owner")
    if not _text(owner):
        owner = supplied_action.get("owner")
    if not _text(owner):
        raise ValueError("ingen ansvarig för nästa handling finns i målet eller bilden")

    value = {
        "schema": _key(picture, "schema", "picture"),
        "generated_at": generated_at,
        "title": copy.deepcopy(_key(picture, "title", "picture")),
        "summary": copy.deepcopy(_key(picture, "summary", "picture")),
        "scope": copy.deepcopy(_key(picture, "scope", "picture")),
        "capabilities": copy.deepcopy(_key(picture, "capabilities", "picture")),
        "work": work,
        "next_action": {
            "text": goal_action["text"],
            "owner": owner,
            "authority": authority,
            "evidence": [reconciliation_id],
        },
        "owner_decision": copy.deepcopy(_key(picture, "owner_decision", "picture")),
        "issues": issues,
        "evidence": evidence,
    }
    return {"reconciliation": reconciliation, "picture": value,
            "html": agarbild.render(value)}
