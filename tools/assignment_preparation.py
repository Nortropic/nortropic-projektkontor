"""Pure AP06 preparation of selected, host-authored material; never authority.

See ASSIGNMENT_PREPARATION.md for the schema and publication boundary.
"""

import copy
import re

import change_assessment


_TASK_FIELDS = (
    "id", "target", "base", "runtime_revision", "allowed_paths",
    "attempt_seconds", "automatic_retries", "steps", "acceptance",
    "acceptance_sha256", "brief",
)
# Explicit executor choice (owner decision AP11-UTFÖRARNEUTRAL): an absent reviewer
# choice is the original Codex reviewer, so it is never a gap and never defaulted here.
_OPTIONAL_TASK_FIELDS = ("review_provider",)
_EXECUTORS = ("codex", "claude")
_KINDS = ("fact", "judgment", "decision", "authority")
# OMBYGGNAD-20260927, etapp 3: the office's method competence in the preparation. A förvaltning's step, proportion,
# method with reason, the loading receipt that binds the professional underlag, the criteria and the assessment plan
# travel with the assignment. Optional: an absent object keeps every earlier spec valid and adds no gap.
_SPEC_FIELDS = "schema action references reference_checks requirements tests export task"
_FORVALTNING_FIELDS = "namn steg proportion metod underlag kriterier bedomning"
# HELHET-20260927, etapp 3: the problem formulation travels with the förvaltning. Optional `problem`: what the
# business wants, for whom, which user tasks matter, the offer and position, what material exists, what is
# uncertain, which channels the need motivates, how success is judged, where the user insight comes from and the
# intervention decision (a site is not always the answer). Absent for liten: no gap; absent otherwise: one gap.
_PROBLEM_LISTS = "verksamhetsmal malgrupper uppgifter erbjudande positionering befintligt_underlag osakerheter kanalbehov framgangskriterier"
_PROBLEM_FIELDS = _PROBLEM_LISTS + " anvandarinsikt interventionsbeslut"
_LITEN_PROBLEM = ("verksamhetsmal", "uppgifter", "framgangskriterier")
_ANVANDARINSIKT = ("intervjuer", "observationer", "data", "antaganden", "saknas")
_INTERVENTIONER = ("ny-sajt", "forbattra-befintlig", "annan-kanal", "ingen-atgard", "oavgjort")
_PROPORTIONER = ("liten", "mellan", "stor")
_NAMN = r"[a-z][a-z0-9-]{1,39}"
_LIMITATIONS = (
    "DRAFT only. Mechanical completeness is neither acceptance nor authority; "
    "this tool grants no permission and does not authenticate AP06-ACCEPT.",
    "Selected-source-only comparison at the supplied checked_at: no assurance "
    "of freshness or exhaustive discovery of later or relevant sources.",
    "Reference checks are host-supplied observations, not authenticated evidence. "
    "No sources, quotes, links or source hashes are independently verified here.",
    "Changed dependencies require reassessment, not automatic falsehood or "
    "revocation of recorded decisions or authority.",
    "Host review must assess requirements, contradictions, mandates and the "
    "substantive adequacy of test observables; nonempty text is not proof.",
    "Export review is required for every authored field, including IDs, reasons, "
    "test methods and task values. No string checker proves privacy or public safety.",
    "The host must use Runtime's actual validator, review and freeze file bytes, "
    "and obtain independent review and protected integration. This draft neither "
    "generates nor executes acceptance and never invokes Runtime.",
)


def _object(value, fields, label):
    if not isinstance(value, dict) or set(value) != set(fields.split()):
        raise ValueError(label + " must have exactly these fields: " + fields)


def _text(value, label, empty=False):
    if not isinstance(value, str) or (not empty and not value.strip()):
        raise ValueError(label + " must be a " + ("string" if empty else "nonempty string"))


def _list(value, label):
    if not isinstance(value, list):
        raise ValueError(label + " must be a list")


def _entries(value, fields, label):
    _list(value, label)
    indexed = {}
    for entry in value:
        _object(entry, fields, label + " entry")
        _text(entry["id"], label + " id")
        if entry["id"] in indexed:
            raise ValueError(label + " ids must be unique")
        indexed[entry["id"]] = entry
    return indexed


def _links(value, known, label):
    _list(value, label)
    seen = set()
    for identifier in value:
        _text(identifier, label + " id")
        if identifier not in known or identifier in seen:
            raise ValueError(label + " must contain unique known ids")
        seen.add(identifier)


def _path(value, directory, label):
    _text(value, label)
    if (re.fullmatch(r"[A-Za-z0-9_./-]+", value) is None
            or not value.startswith(directory + "/")
            or any(part in ("", ".", "..") for part in value.split("/"))):
        raise ValueError(label + " must be an explicit safe relative file path")


def _hex(value, length, label):
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{%d}" % length, value) is None:
        raise ValueError(label + " must be full lowercase hexadecimal")


def _empty(value):
    return (value is None or isinstance(value, str) and not value.strip()
            or isinstance(value, (list, dict)) and not value)


def _validate_task(task, gap):
    if not isinstance(task, dict) or set(task) - set(_TASK_FIELDS) - set(_OPTIONAL_TASK_FIELDS):
        raise ValueError("task must be an object with only permitted fields")
    if "review_provider" in task and (not isinstance(task["review_provider"], str)
                                      or task["review_provider"] not in _EXECUTORS):
        raise ValueError("task review_provider must be codex or claude")
    for field in _TASK_FIELDS:
        if field not in task:
            gap("task_field_missing", field)
            continue
        value = task[field]
        if _empty(value):
            gap("task_field_empty", field)
            continue
        if field == "id":
            if not isinstance(value, str) or re.fullmatch(r"[a-z0-9][a-z0-9-]{0,79}", value) is None:
                raise ValueError("task id is invalid")
        elif field == "target":
            if value != "Nortropic/nortropic-projektkontor":
                raise ValueError("task target must be the office repo")
        elif field in ("base", "runtime_revision", "acceptance_sha256"):
            _hex(value, 64 if field == "acceptance_sha256" else 40, "task " + field)
        elif field == "allowed_paths":
            _list(value, "task allowed_paths")
            seen = set()
            forbidden = {"tools/kontor.py", "tools/assignment_preparation.py"}
            for path in value:
                _path(path, "tools", "task allowed_paths entry")
                folded = path.casefold()
                if folded in seen or folded in forbidden:
                    raise ValueError("task allowed_paths contain duplicates or active core")
                seen.add(folded)
        elif field == "attempt_seconds":
            if type(value) is not int or not 1 <= value <= 3600:
                raise ValueError("task attempt_seconds must be integer 1..3600")
        elif field == "automatic_retries":
            if type(value) is not int or value != 0:
                raise ValueError("task automatic_retries must be integer 0")
        elif field == "steps":
            _list(value, "task steps")
            for step in value:
                _object(step, "provider prompt", "task step")
                if not isinstance(step["provider"], str) or step["provider"] not in _EXECUTORS:
                    raise ValueError("task step provider must be codex or claude")
                _text(step["prompt"], "task step prompt")
        else:
            _path(value, "acceptance" if field == "acceptance" else "tasks", "task " + field)


def _validate_problem(value, liten, gap):
    """The problem formulation: exact shape, enumerated sources and decisions, missing substance as gaps by proportion."""
    _object(value, _PROBLEM_FIELDS, "forvaltning problem")
    for field in _PROBLEM_LISTS.split():
        _list(value[field], "forvaltning problem " + field)
        for entry in value[field]:
            _text(entry, "forvaltning problem " + field + " entry")
        if not value[field] and (not liten or field in _LITEN_PROBLEM):
            gap("forvaltning_problem_" + field + "_empty", "forvaltning")
    if value["anvandarinsikt"] not in _ANVANDARINSIKT:
        raise ValueError("forvaltning problem anvandarinsikt must be one of " + ", ".join(_ANVANDARINSIKT))
    _object(value["interventionsbeslut"], "val skal", "forvaltning problem interventionsbeslut")
    if value["interventionsbeslut"]["val"] not in _INTERVENTIONER:
        raise ValueError("forvaltning problem interventionsbeslut val must be one of " + ", ".join(_INTERVENTIONER))
    _text(value["interventionsbeslut"]["skal"], "forvaltning problem interventionsbeslut skal", empty=True)
    if not value["interventionsbeslut"]["skal"].strip():
        gap("forvaltning_problem_interventionsbeslut_skal_empty", "forvaltning")


def _validate_forvaltning(value, gap):
    """Exact schema, contradictions as errors, missing substance as gaps; proportion decides which gaps apply."""
    if not isinstance(value, dict) or set(value) - set(_FORVALTNING_FIELDS.split()) - {"problem"} \
            or set(_FORVALTNING_FIELDS.split()) - set(value):
        raise ValueError("forvaltning must have exactly these fields: " + _FORVALTNING_FIELDS + ", optionally problem")
    for field in ("namn", "steg"):
        _text(value[field], "forvaltning " + field)
        if re.fullmatch(_NAMN, value[field]) is None:
            raise ValueError("forvaltning " + field + " must match " + _NAMN)
    if value["proportion"] not in _PROPORTIONER:
        raise ValueError("forvaltning proportion must be liten, mellan or stor")
    liten = value["proportion"] == "liten"
    _object(value["metod"], "val skal", "forvaltning metod")
    for field in ("val", "skal"):
        _text(value["metod"][field], "forvaltning metod " + field, empty=True)
    if not value["metod"]["val"].strip():
        gap("forvaltning_metod_val_empty", "forvaltning")
    if not liten and not value["metod"]["skal"].strip():
        gap("forvaltning_metod_skal_empty", "forvaltning")
    _object(value["underlag"], "laddningskvitto_sha256 steg sha256_over_underlag", "forvaltning underlag")
    underlag = value["underlag"]
    _text(underlag["steg"], "forvaltning underlag steg")
    if underlag["steg"] != value["steg"]:
        raise ValueError("forvaltning underlag steg must equal the forvaltning step")
    for field, code in (("laddningskvitto_sha256", "forvaltning_underlag_missing"),
                        ("sha256_over_underlag", "forvaltning_underlag_unbound")):
        _text(underlag[field], "forvaltning underlag " + field, empty=True)
        if not underlag[field].strip():
            gap(code, "forvaltning")
        else:
            _hex(underlag[field], 64, "forvaltning underlag " + field)
    _list(value["kriterier"], "forvaltning kriterier")
    for entry in value["kriterier"]:
        _text(entry, "forvaltning kriterier entry")
    if not value["kriterier"]:
        gap("forvaltning_kriterier_empty", "forvaltning")
    _object(value["bedomning"], "tekniskt professionellt ej_observerat", "forvaltning bedomning")
    for field in ("tekniskt", "professionellt", "ej_observerat"):
        _list(value["bedomning"][field], "forvaltning bedomning " + field)
        for entry in value["bedomning"][field]:
            _text(entry, "forvaltning bedomning " + field + " entry")
        if not value["bedomning"][field] and not (liten and field == "professionellt"):
            gap("forvaltning_bedomning_" + field + "_empty", "forvaltning")
    if "problem" in value:
        _validate_problem(value["problem"], liten, gap)
    elif not liten:
        gap("forvaltning_problem_missing", "forvaltning")


def _validate_spec(spec, case, gap):
    if not isinstance(spec, dict) or set(spec) - set(_SPEC_FIELDS.split()) - {"forvaltning"} \
            or set(_SPEC_FIELDS.split()) - set(spec):
        raise ValueError("spec must have exactly these fields: " + _SPEC_FIELDS + ", optionally forvaltning")
    if type(spec["schema"]) is not int or spec["schema"] != 1:
        raise ValueError("spec schema must be integer 1")
    _text(spec["action"], "spec action")
    if spec["action"] not in {action["id"] for action in case["actions"]}:
        raise ValueError("spec action must select an existing action")
    sources = {source["id"]: source for source in case["sources"]}
    references = _entries(spec["references"], "id source version quote", "references")
    for ref in references.values():
        for field in ("source", "version", "quote"):
            _text(ref[field], "reference " + field, empty=field == "quote")
        if ref["source"] not in sources or ref["version"] != sources[ref["source"]]["version"]:
            raise ValueError("reference must bind a selected source and its pinned version")
    checks = _entries(spec["reference_checks"], "id source version sha256 quote status", "reference_checks")
    for identifier, observation in checks.items():
        if identifier not in references:
            raise ValueError("reference check must identify an existing reference")
        _text(observation["status"], "reference check status")
        if observation["status"] not in ("matched", "mismatch", "not_checked"):
            raise ValueError("reference check status is invalid")
        ref = references[identifier]
        # Bind the lookup target even when the host reports a failed lookup.
        # A mismatch is an observation of this target, not a replacement binding.
        if any(observation[field] != ref[field] for field in ("source", "version", "quote")):
            raise ValueError("reference check contradicts its reference binding")
        if observation["sha256"] != sources[ref["source"]]["sha256"]:
            raise ValueError("reference check contradicts the pinned source hash")
    tests = _entries(spec["tests"], "id observable method", "tests")
    for test in tests.values():
        for field in ("observable", "method"):
            _text(test[field], "test " + field, empty=True)
            if not test[field].strip():
                gap("test_" + field + "_empty", test["id"])
    requirements = _entries(spec["requirements"], "id text reason claims references tests", "requirements")
    for req in requirements.values():
        for field in ("text", "reason"):
            _text(req[field], "requirement " + field)
        for field, known in (("claims", {claim["id"] for claim in case["claims"]}),
                             ("references", references), ("tests", tests)):
            _links(req[field], known, "requirement " + field)
            if not req[field]:
                gap("requirement_" + field + "_empty", req["id"])
    if not requirements:
        gap("requirements_empty", "brief")
    if not tests:
        gap("tests_empty", "brief")
    export = spec["export"]
    _object(export, "title context scope limitations", "export")
    _text(export["title"], "export title")
    for field in ("context", "scope", "limitations"):
        _list(export[field], "export " + field)
        if not export[field]:
            gap("export_" + field + "_empty", "brief")
        for entry in export[field]:
            if field == "context":
                _object(entry, "kind text", "export context entry")
                _text(entry["kind"], "export context kind")
                if entry["kind"] not in _KINDS:
                    raise ValueError("export context kind is invalid")
                _text(entry["text"], "export context text")
            else:
                _text(entry, "export " + field + " entry")
    if "forvaltning" in spec:
        _validate_forvaltning(spec["forvaltning"], gap)
    _validate_task(spec["task"], gap)
    return references, checks, requirements, tests


def _brief(export, requirements, tests, gaps, limitations, forvaltning=None):
    lines = ["# DRAFT — " + export["title"], "", _LIMITATIONS[0], "", "## Context"]
    for kind in _KINDS:
        lines.extend(["", "### " + kind.capitalize(), ""])
        lines.extend("- " + entry["text"] for entry in export["context"] if entry["kind"] == kind)
    lines.extend(["", "## Scope", ""])
    lines.extend("- " + text for text in export["scope"])
    if forvaltning is not None:
        underlag = forvaltning["underlag"]
        lines.extend(["", "## Förvaltning", "",
                      "- Förvaltning: " + forvaltning["namn"] + "; steg: " + forvaltning["steg"]
                      + "; proportion: " + forvaltning["proportion"]])
        problem = forvaltning.get("problem")
        if problem is not None:
            lines.extend(["- Problem (verksamhetsmål): " + ("; ".join(problem["verksamhetsmal"]) or "(inga angivna)"),
                          "- Målgrupper: " + ("; ".join(problem["malgrupper"]) or "(inga angivna)"),
                          "- Viktigaste användaruppgifter: " + ("; ".join(problem["uppgifter"]) or "(inga angivna)"),
                          "- Erbjudande: " + ("; ".join(problem["erbjudande"]) or "(inget angivet)"),
                          "- Positionering: " + ("; ".join(problem["positionering"]) or "(ingen angiven)"),
                          "- Befintligt underlag: " + ("; ".join(problem["befintligt_underlag"]) or "(inget angivet)"),
                          "- Osäkerheter: " + ("; ".join(problem["osakerheter"]) or "(inga angivna)"),
                          "- Kanalbehov: " + ("; ".join(problem["kanalbehov"]) or "(inga angivna)"),
                          "- Framgångskriterier: " + ("; ".join(problem["framgangskriterier"]) or "(inga angivna)"),
                          "- Användarinsiktens källa: " + problem["anvandarinsikt"]
                          + (" — inga användarintervjuer eller observationer; insikterna är antaganden och redovisas så"
                             if problem["anvandarinsikt"] in ("antaganden", "saknas") else "")])
        elif forvaltning["proportion"] != "liten":
            lines.append("- Problem: (problemformuleringen saknas)")
        lines.extend(["- Underlag: laddningskvitto " + (underlag["laddningskvitto_sha256"].strip() or "(saknas)")
                      + "; underlagets hash " + (underlag["sha256_over_underlag"].strip() or "(saknas)"),
                      "- Metod: " + (forvaltning["metod"]["val"].strip() or "(inte angiven)")
                      + " — skäl: " + (forvaltning["metod"]["skal"].strip() or "(inte angivet)")])
        if problem is not None:
            lines.append("- Interventionsbeslut: " + problem["interventionsbeslut"]["val"] + " — skäl: "
                         + (problem["interventionsbeslut"]["skal"].strip() or "(inte angivet)"))
        lines.extend(["- Kriterier: " + (", ".join(forvaltning["kriterier"]) or "(inga)"),
                      "- Bedömning, tekniskt prövat: " + ("; ".join(forvaltning["bedomning"]["tekniskt"]) or "(inget)"),
                      "- Bedömning, professionellt bedömt: " + ("; ".join(forvaltning["bedomning"]["professionellt"]) or "(inget)"),
                      "- Ej observerat hos verkliga användare: " + ("; ".join(forvaltning["bedomning"]["ej_observerat"]) or "(inget angivet)")])
    lines.extend(["", "## Derived requirements", ""])
    for req in requirements:
        lines.extend(["### " + req["id"], "", req["text"], "",
                      "Reason: " + req["reason"], "",
                      "Tests: " + ", ".join(req["tests"]), ""])
    lines.extend(["## Verification", ""])
    for test in tests:
        lines.extend(["### " + test["id"], "", "Observable: " + test["observable"], "",
                      "Method: " + test["method"], ""])
    lines.extend(["## Gaps", ""])
    lines.extend("- " + entry["code"] + ": " + entry["subject"] for entry in gaps)
    if not gaps:
        lines.append("No mechanical gaps detected. Still DRAFT; host review is required.")
    lines.extend(["", "## Limitations", ""])
    lines.extend("- " + text for text in limitations)
    return "\n".join(lines) + "\n"


def prepare(case, check, spec):
    """Return an isolated JSON-compatible draft; invalid structures raise ValueError.

    No I/O, execution, hashing, source discovery or input mutation occurs.
    Observations and all authored export strings remain the host's responsibility.
    """
    report = change_assessment.assess(case, check)
    gaps = []

    def gap(code, subject):
        gaps.append({"code": code, "subject": subject})

    references, checks, requirements, tests = _validate_spec(spec, case, gap)
    statuses = {entry["id"]: entry["status"] for entry in report["source_checks"]}
    claims = {entry["id"]: entry for group in ("facts", "judgments", "decisions")
              for entry in report[group]}
    action = next(entry for entry in report["actions"] if entry["id"] == spec["action"])
    if action["authority"]["status"] != "granted" or not action["authority"]["sources"]:
        gap("action_authority_missing", "brief")
    if action["source_check"] != "unchanged":
        gap("action_dependencies_need_reassessment", "brief")

    reference_trace = []
    reference_current = {}
    for ordinal, (identifier, ref) in enumerate(references.items(), 1):
        observation = checks.get(identifier)
        status = observation["status"] if observation is not None else "missing"
        subject = "reference:" + str(ordinal)
        if status != "matched":
            gap("reference_check_" + status, subject)
        current = statuses[ref["source"]] == "ok"
        if not current:
            gap("reference_source_needs_reassessment", subject)
        reference_current[identifier] = current and status == "matched"
        reference_trace.append({
            "ordinal": ordinal, "reference": copy.deepcopy(ref),
            "check": copy.deepcopy(observation), "source_status": statuses[ref["source"]],
            "current": reference_current[identifier],
        })

    requirement_trace = []
    for req in requirements.values():
        dependencies = {source for identifier in req["claims"] for source in claims[identifier]["sources"]}
        dependencies.update(references[identifier]["source"] for identifier in req["references"])
        ordered = [identifier for identifier in statuses if identifier in dependencies]
        affected = [identifier for identifier in ordered if statuses[identifier] != "ok"]
        unverified = [identifier for identifier in req["references"] if not reference_current[identifier]]
        incomplete_tests = [identifier for identifier in req["tests"]
                            if not tests[identifier]["observable"].strip() or not tests[identifier]["method"].strip()]
        if affected:
            gap("requirement_dependencies_need_reassessment", req["id"])
        if unverified:
            gap("requirement_references_unverified", req["id"])
        if incomplete_tests:
            gap("requirement_verification_incomplete", req["id"])
        requirement_trace.append({
            "requirement": copy.deepcopy(req), "sources": ordered, "affected_sources": affected,
            "unverified_references": unverified, "incomplete_tests": incomplete_tests,
        })

    public_requirements = [{field: copy.deepcopy(req[field]) for field in ("id", "text", "reason", "tests")}
                           for req in requirements.values()]
    public_tests = copy.deepcopy(spec["tests"])
    limitations = list(_LIMITATIONS) + copy.deepcopy(spec["export"]["limitations"])
    forvaltning = copy.deepcopy(spec.get("forvaltning"))
    return {
        "status": "draft", "mechanical_complete": not gaps, "gaps": gaps,
        "private": {
            "assessment": report, "case": copy.deepcopy(case), "check": copy.deepcopy(check),
            "spec": copy.deepcopy(spec), "references": reference_trace, "requirements": requirement_trace,
        },
        "package": {
            "brief": _brief(spec["export"], public_requirements, public_tests, gaps, limitations, forvaltning),
            "task_draft": copy.deepcopy(spec["task"]), "requirements": public_requirements,
            "tests": public_tests, "gaps": copy.deepcopy(gaps), "limitations": limitations,
            **({"forvaltning": copy.deepcopy(forvaltning)} if forvaltning is not None else {}),
        },
    }
