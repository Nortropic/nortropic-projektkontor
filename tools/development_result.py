"""Relate the named requirements of the accepted AP11 goal to saved Runtime observations.

Pure, read-only reconciliation (AP11 delivery A). Every per-report interpretation
is delegated to kontor_result.render through the module attribute at call time.
Nothing here performs I/O, infers completion or grants authority.
"""

import copy
import json
import re

import kontor_result


_GOAL_ID = "office-ap11"
_TASK_KEYS = ("id", "sha256", "acceptance_sha256", "merge_commit")
_LIMITATIONS = (
    "This is a reconciliation of saved Runtime observations, not current engine "
    "or remote status. No live GitHub or remote verification is performed and the "
    "observations may be stale.",
    "No whole-goal completion and no authority is inferred from requirement "
    "statuses; a supported delivery is a reading of saved evidence, not activation.",
    "The separate final review judges the whole goal; this result is input to "
    "that review, not a substitute for it.",
)


def _text(value):
    return type(value) is str and bool(value.strip())


def _hex(value, length):
    return type(value) is str and re.fullmatch(r"[0-9a-f]{%d}" % length, value) is not None


def _json_safe(value):
    try:
        json.dumps(value, allow_nan=False)
    except (TypeError, ValueError, RecursionError):
        return False
    return True


def _validate_task(task, requirement_id):
    if task is None:
        return
    if type(task) is not dict:
        raise ValueError("Requirement %r: task must be None or a dict" % requirement_id)
    if not _text(task.get("id")):
        raise ValueError("Requirement %r: task.id must be a non-empty string" % requirement_id)
    for key in ("sha256", "acceptance_sha256"):
        if not _hex(task.get(key), 64):
            raise ValueError("Requirement %r: task.%s must be 64 lowercase hex"
                             % (requirement_id, key))
    if not _hex(task.get("merge_commit"), 40):
        raise ValueError("Requirement %r: task.merge_commit must be 40 lowercase hex"
                         % requirement_id)


def _validate_goal(goal):
    if type(goal) is not dict:
        raise ValueError("goal must be a dict")
    if goal.get("id") != _GOAL_ID:
        raise ValueError("goal.id must be exactly %r" % _GOAL_ID)
    requirements = goal.get("requirements")
    if type(requirements) is not list or not requirements:
        raise ValueError("goal.requirements must be a non-empty list")
    seen = set()
    for item in requirements:
        if type(item) is not dict:
            raise ValueError("goal.requirements items must be dicts")
        requirement_id = item.get("id")
        if not _text(requirement_id):
            raise ValueError("requirement id must be a non-empty string")
        if requirement_id in seen:
            raise ValueError("requirement id %r is not unique" % requirement_id)
        seen.add(requirement_id)
        if not _text(item.get("text")):
            raise ValueError("Requirement %r: text must be a non-empty string" % requirement_id)
        if "task" not in item:
            raise ValueError("Requirement %r: task must be present (None or a dict)"
                             % requirement_id)
        _validate_task(item["task"], requirement_id)
    next_action = goal.get("next_action")
    if type(next_action) is not dict:
        raise ValueError("goal.next_action must be a dict")
    for key in ("text", "authority"):
        if not _text(next_action.get(key)):
            raise ValueError("goal.next_action.%s must be a non-empty string" % key)
    if not _json_safe(next_action):
        raise ValueError("goal.next_action must be JSON data")


def _report_task_id(report):
    if type(report) is not dict:
        return None
    task_id = report.get("task_id")
    return task_id if type(task_id) is str else None


def _reconcile_requirement(requirement, reports, index):
    task = requirement["task"]
    entry = {
        "id": requirement["id"],
        "text": requirement["text"],
        "task": None if task is None else {key: task[key] for key in _TASK_KEYS},
        "status": "missing",
        "result": None,
        "problems": [],
    }
    if task is None:
        entry["problems"].append("No task is bound to this requirement")
        return entry

    positions = index.get(task["id"], [])
    if not positions:
        entry["problems"].append("No saved report carries task_id %r" % task["id"])
        return entry
    if len(positions) > 1:
        entry["status"] = "ambiguous"
        entry["problems"].append("%d saved reports carry task_id %r; none is selected"
                                 % (len(positions), task["id"]))
        return entry

    report = reports[positions[0]]
    rendered = kontor_result.render(report)
    entry["result"] = rendered
    problems = entry["problems"]
    if rendered.get("status") != "delivered":
        problems.append("Saved observation does not show a delivered task (status %r)"
                        % rendered.get("status"))
    if report.get("task_sha256") != task["sha256"]:
        problems.append("Report task_sha256 differs from the requirement's task sha256")
    if report.get("acceptance_sha256") != task["acceptance_sha256"]:
        problems.append("Report acceptance_sha256 differs from the requirement's "
                        "acceptance_sha256")
    integration = report.get("integration")
    merge_commit = integration.get("merge_commit") if type(integration) is dict else None
    if merge_commit != task["merge_commit"]:
        problems.append("Report integration.merge_commit differs from the requirement's "
                        "merge_commit")
    entry["status"] = "delivery_supported" if not problems else "not_supported"
    return entry


def reconcile(goal, reports):
    """Relate each named requirement of the goal to at most one saved report.

    Returns a fresh JSON-safe dict. Inputs are treated as read-only. Whole-goal
    completion is never derived, and next_action is passed through unchanged.
    """
    _validate_goal(goal)
    if type(reports) is not list:
        raise ValueError("reports must be a list")

    index = {}
    for position, report in enumerate(reports):
        task_id = _report_task_id(report)
        if task_id is not None:
            index.setdefault(task_id, []).append(position)

    named_task_ids = {
        item["task"]["id"] for item in goal["requirements"] if item["task"] is not None
    }
    requirements = [
        _reconcile_requirement(item, reports, index) for item in goal["requirements"]
    ]
    unmatched = [
        _report_task_id(report) for report in reports
        if _report_task_id(report) not in named_task_ids
    ]

    return {
        "goal_id": goal["id"],
        "live": False,
        "remote_current": False,
        "whole_goal_complete": False,
        "limitations": list(_LIMITATIONS),
        "next_action": copy.deepcopy(goal["next_action"]),
        "requirements": requirements,
        "unmatched_reports": unmatched,
    }
