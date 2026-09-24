# Separately reviewed AP11 task

# DRAFT — AP11 reconciliation

DRAFT only. Mechanical completeness is neither acceptance nor authority; this tool grants no permission and does not authenticate AP06-ACCEPT.

## Context

### Fact

- Frozen host observation supplies actual integrated work

### Judgment

- The accepted mandate (AP11-ACCEPT, authority.md, sha256 a2b3f143...) and frozen goal G1 (goal.md, sha256 21cff4b7..., read together with GOAL_AMENDMENT_1.md, which changes only executor wording in G4/G5 and nothing about A or B) name exactly two deliveries: A, the Office delivery reconciliation relating the named accepted requirements, actual task reports and independently reviewed remote integration, and B, its handoff through the existing AP08/result readers. The observation delivered with this workspace (observation.md and CONTEXT.json, observed 2026-09-22T11:26:24Z) shows integrated = {}, reports = {} and actual_reconciliation_result = null at base a743f14970c3ff11952bf41592f05b5a5c13f986: nothing of A has been integrated and no delivery report exists. A is therefore the genuinely remaining first work and has no delivered predecessor, which is why depends_on is exactly the empty string. B is not prepared here: it must be drafted only from the actually integrated A. The gap is concrete: the Office repo has tools/kontor_result.py (interprets one saved Runtime delivery observation) and tools/agarbild.py (renders a dated owner view from supplied data) but no component that ties a named requirement of the accepted goal to the exact task, frozen acceptance and merge commit that delivered it and reports what is still missing plus the next permitted action. The frozen host recipe VERIFICATION_RECIPE.py (sha256 1ff7338e..., equal to CONTEXT.acceptance_sha256) fixes the interface: a module tools/development_result.py importable as development_result next to kontor_result, exposing reconcile(goal, reports) as a pure function that reuses kontor_result.render through the module attribute at call time, never mutates its inputs, performs no open/os/subprocess/socket/ctypes access, never reports whole-goal completion, passes next_action through unchanged, and fails closed on identity mismatch, missing report fields, duplicate observations and malformed or foreign goal structure. Changed prerequisite for this retry, from the separately reviewed PREPARATION_REJECTION.json of the previous draft (step-4): that review found need, dependency, scope and recipe alignment sound and rejected only an internal path inconsistency, because the host-populated task.allowed_paths listed tools/test_development_result.py while the brief, R8 and T8 required tests/test_development_result.py, making the task unpassable. This draft names the candidate test file as tools/test_development_result.py everywhere (brief, requirements, tests) so that it coincides with the path the host populated, and the frozen recipe is unaffected. The task is scoped to exactly A: no report engine, no new trust rule, no scheduler, no CLI, no publishing, no live remote checks, no change to kontor_result.py, agarbild.py, the recipe, the goal or the mandate, and no executor named in this answer (executors come from the frozen release configuration). A task PASS on this recipe verifies synthetic behaviour only and does not establish the AP11 whole goal, which the separate final review judges.

### Decision


### Authority

- AP11 accepted scope only; draft still requires independent scope and verifier review

## Scope

- Add tools/development_result.py to the Office repo (Nortropic/nortropic-projektkontor, base a743f14970c3ff11952bf41592f05b5a5c13f986) as the AP11 delivery reconciliation A. It is a pure, read-only data module with one public function reconcile(goal, reports) that relates the named requirements of the accepted goal to saved Runtime delivery observations and returns a JSON-safe dict for later handoff through the existing AP08 owner view. Reuse tools/kontor_result.py for every per-report interpretation by calling kontor_result.render through the module attribute at call time (import kontor_result as a top-level module; do not copy or reimplement its checks; do not from-import render). Do not modify kontor_result.py, agarbild.py or any existing file. Input goal: dict with id (must be exactly 'office-ap11'), requirements (non-empty list of dicts with unique non-empty string id, non-empty string text, and task that is either None or a dict with id (non-empty string), sha256 (64 lowercase hex), acceptance_sha256 (64 lowercase hex), merge_commit (40 lowercase hex)), and next_action (dict with non-empty string text and non-empty string authority). Any other goal shape raises ValueError. Input reports: a list of saved observations in the kontor_result shape plus task_sha256 (64 hex); a non-list raises ValueError; a malformed report item is not an error but can never support a requirement. Output dict keys: goal_id; live (always False); remote_current (always False); whole_goal_complete (always False); limitations (non-empty list of strings stating that this is a saved observation without live remote verification, that no completion or authority is inferred, and that the separate final review judges the whole goal); next_action (an equal copy of goal['next_action'], unchanged including authority); requirements (same order as the goal; each with id, text, task copy, status, result, problems); unmatched_reports (task_id or None for each report that matches no named requirement, in input order). Requirement status vocabulary, exactly: 'missing' (task is None, or no report has task_id equal to task.id); 'ambiguous' (two or more reports carry that task_id, even if byte-identical: never select the positive one); 'not_supported' (exactly one report matched but kontor_result.render(report)['status'] is not 'delivered', or report task_sha256 != task.sha256, or report acceptance_sha256 != task.acceptance_sha256, or report integration.merge_commit != task.merge_commit); 'delivery_supported' (exactly one report matched, rendered status 'delivered' and all three identities equal). result is exactly the unmodified dict returned by kontor_result.render for the single matched report, else None; problems is a list of short strings explaining any status other than delivery_supported. Whole-goal completion is never derived from requirement statuses, even when every requirement is delivery_supported. The function must not mutate goal or reports (build fresh structures; treat inputs as read-only), must return only JSON-serialisable data with finite numbers, and must use no I/O: no open, os.*, subprocess, socket, ctypes, network, clock, environment or logging; only stdlib helpers such as re, copy, math and json. No CLI, no main, no file reading and no writing, no import-time side effects beyond importing kontor_result and stdlib. Add a unittest module at exactly tools/test_development_result.py (in the tools directory next to the module, NOT under a tests/ directory; the task's allowed paths are only tools/development_result.py and tools/test_development_result.py) with synthetic fixtures covering the positive case, each identity mismatch, each missing report field, verified_delivery False, the empty report list, identical and differing duplicates, malformed and foreign goals, non-list reports, input non-mutation and reuse of kontor_result.render; these are candidate tests, not host acceptance. Host acceptance is the frozen recipe VERIFICATION_RECIPE.py (sha256 1ff7338eff202ff3d70a858ab42f9e4e313c35dce5b3dff4016bb823e10e1a96), unchanged. Write nothing outside the two allowed paths.

## Derived requirements

### R1-interface

tools/development_result.py exists, is importable as development_result when tools/ is on sys.path under python -I, and exposes reconcile(goal, reports) returning a dict with keys goal_id, live, remote_current, whole_goal_complete, limitations, next_action, requirements and unmatched_reports; json.dumps(result, allow_nan=False) succeeds.

Reason: The frozen recipe imports the module by that name and reads exactly these fields; a JSON-safe result is what the later AP08 handoff (B) can consume.

Tests: T1-positive-binding, T2-identity-mismatch, T3-reader-rejects, T4-missing-and-ambiguous, T5-never-complete-authority-passthrough, T6-invalid-goal, T7-reuse-and-purity, T8-scope-diff

### R2-reuse-reader

Every per-report interpretation is obtained by calling kontor_result.render through the imported module attribute at call time, and a delivery_supported requirement's result field is exactly the unmodified dict that call returned; no delivery check of kontor_result is duplicated in the new module.

Reason: The mandate requires reusing existing result readers rather than re-creating them; the recipe verifies actual reuse by tracing the module attribute and by equality of result.

Tests: T1-positive-binding, T2-identity-mismatch, T3-reader-rejects, T4-missing-and-ambiguous, T5-never-complete-authority-passthrough, T6-invalid-goal, T7-reuse-and-purity, T8-scope-diff

### R3-named-goal-validation

reconcile raises ValueError when goal is not a dict, goal id is not exactly 'office-ap11', requirements is empty or contains non-dict items, requirement ids are not unique non-empty strings, text is empty, a non-None task lacks id, sha256, acceptance_sha256 or merge_commit in the stated hex formats, next_action is not a dict with non-empty text and authority, or reports is not a list.

Reason: Reconciliation must be bound to the one named accepted goal; a malformed or foreign goal structure must fail closed rather than yield a plausible report.

Tests: T1-positive-binding, T2-identity-mismatch, T3-reader-rejects, T4-missing-and-ambiguous, T5-never-complete-authority-passthrough, T6-invalid-goal, T7-reuse-and-purity, T8-scope-diff

### R4-exact-binding

A requirement is 'delivery_supported' only when exactly one report has task_id equal to task.id, kontor_result.render of that report has status 'delivered', and the report's task_sha256, acceptance_sha256 and integration.merge_commit equal the task's sha256, acceptance_sha256 and merge_commit; any single mismatch yields 'not_supported' with a problem text.

Reason: G1 relates requirements to the actual task, frozen acceptance and reviewed remote integration; a different task, changed acceptance or different merge commit must never count as delivery.

Tests: T1-positive-binding, T2-identity-mismatch, T3-reader-rejects, T4-missing-and-ambiguous, T5-never-complete-authority-passthrough, T6-invalid-goal, T7-reuse-and-purity, T8-scope-diff

### R5-fail-closed

With task None or no matching report the status is 'missing'; with two or more reports carrying the same task_id, even identical ones, the status is 'ambiguous' and never 'delivery_supported'; a matched report missing review_run, integration or observed_at_epoch, or with verified_delivery not exactly True, yields 'not_supported'; reports matching no requirement are listed in unmatched_reports and never counted.

Reason: G8 requires that missing, changed or ambiguous evidence never becomes success; the recipe checks each of these negative cases.

Tests: T1-positive-binding, T2-identity-mismatch, T3-reader-rejects, T4-missing-and-ambiguous, T5-never-complete-authority-passthrough, T6-invalid-goal, T7-reuse-and-purity, T8-scope-diff

### R6-no-completion-no-authority

whole_goal_complete is always False regardless of requirement statuses, limitations is a non-empty list of strings with the saved-observation, no-live-remote and separate-final-review caveats, live and remote_current are always False, and next_action is returned as an equal copy of goal['next_action'] with its authority value unchanged (including 'none').

Reason: Individual PASS may not establish the whole goal (G4, G8), status readings are not activation (G9), and the module must not invent or upgrade authority for the next action.

Tests: T1-positive-binding, T2-identity-mismatch, T3-reader-rejects, T4-missing-and-ambiguous, T5-never-complete-authority-passthrough, T6-invalid-goal, T7-reuse-and-purity, T8-scope-diff

### R7-pure-and-non-mutating

reconcile performs no file, network, process, foreign-function, clock or environment access (no open, os.*, subprocess.*, socket.*, ctypes.*), leaves goal and reports deeply equal to their pre-call values, and the module has no CLI, main or import-time side effects beyond importing kontor_result and stdlib helpers.

Reason: The recipe installs an audit hook that fails on any such event and asserts input equality; read-only reconciliation is what the mandate permits and what makes the later handoff safe.

Tests: T1-positive-binding, T2-identity-mismatch, T3-reader-rejects, T4-missing-and-ambiguous, T5-never-complete-authority-passthrough, T6-invalid-goal, T7-reuse-and-purity, T8-scope-diff

### R8-candidate-tests-and-scope

The candidate diff against base adds exactly two files, tools/development_result.py and tools/test_development_result.py (a unittest module with synthetic fixtures exercising R1 to R7 including every negative case), changes no existing file, adds no dependency, creates no tests/ directory, and does not touch the frozen recipe, goal, mandate, kontor_result.py or agarbild.py.

Reason: The task's allowed paths are exactly these two files, so the test path must match to pass the scope gate; generated tests are untrusted proposals reviewed separately, and the scope limit keeps A from becoming a report engine or altering reviewed components.

Tests: T1-positive-binding, T2-identity-mismatch, T3-reader-rejects, T4-missing-and-ambiguous, T5-never-complete-authority-passthrough, T6-invalid-goal, T7-reuse-and-purity, T8-scope-diff

## Verification

### T1-positive-binding

Observable: For the named goal with requirement A bound to task 'first' and a single delivered synthetic report whose task_sha256, acceptance_sha256 and merge_commit match, requirement A has status 'delivery_supported' and result equal to kontor_result.render(report); requirement B (task None) has status 'missing'; requirement ids come back in goal order.

Method: Host recipe invokes reconcile(G,[R]) and compares status, result and id order; candidate unittest in tools/test_development_result.py replicates with its own fixture.

### T2-identity-mismatch

Observable: Changing task_sha256, acceptance_sha256 or integration.merge_commit in the report makes requirement A 'not_supported' with a problem text; changing task_id makes it 'missing' and lists the report in unmatched_reports; none of the four is 'delivery_supported'.

Method: Host recipe loops over the four altered copies asserting status != 'delivery_supported'; candidate unittest asserts the exact status and problem text per case.

### T3-reader-rejects

Observable: Deleting review_run, integration or observed_at_epoch from the report, or setting verified_delivery to False, makes requirement A 'not_supported' because kontor_result.render no longer reports 'delivered'.

Method: Host recipe deletes each field and flips verified_delivery, asserting status != 'delivery_supported'; candidate unittest asserts that result carries the reader's error text.

### T4-missing-and-ambiguous

Observable: An empty report list gives status 'missing'; two byte-identical copies of the delivered report give status 'ambiguous' (or ValueError), never 'delivery_supported'; a differing duplicate pair is also 'ambiguous'.

Method: Host recipe invokes reconcile(G,[]) and reconcile(g,[R,R]) accepting non-delivery_supported or ValueError; candidate unittest adds the differing duplicate pair.

### T5-never-complete-authority-passthrough

Observable: A goal reduced to only the delivered requirement still returns whole_goal_complete False with non-empty limitations; a goal whose next_action.authority is 'none' returns next_action equal to the input with authority 'none'; live and remote_current are False and goal_id is 'office-ap11' in every call.

Method: Host recipe asserts these on every invoke, on the single-requirement goal and on the 'none' authority goal; candidate unittest asserts the flags in every case.

### T6-invalid-goal

Observable: reconcile({},[R]), reconcile with goal id 'other-goal', and reconcile with duplicated requirement ids each raise ValueError; a non-list reports argument and a task with malformed hex also raise ValueError.

Method: Host recipe expects ValueError for the three goal shapes and fails if any is accepted; candidate unittest adds the non-list reports and malformed hex cases.

### T7-reuse-and-purity

Observable: Replacing kontor_result.render with a tracing wrapper before reconcile(G,[R]) records at least one call; during reconcile no open, os.*, subprocess.*, socket.* or ctypes.* audit event fires; goal and reports compare deeply equal before and after every call; json.dumps(result, allow_nan=False) succeeds.

Method: Host recipe installs sys.addaudithook, deep-copies inputs and traces the module attribute; candidate unittest patches kontor_result.render with unittest.mock and compares deep copies.

### T8-scope-diff

Observable: The candidate diff against base a743f149... adds only tools/development_result.py and tools/test_development_result.py; kontor_result.py, agarbild.py and all other files are byte-unchanged, no tests/ directory appears and no dependency files change.

Method: Host scope gate compares changed paths with the task's allowed paths; the separate reviewer inspects the candidate diff; not part of the host recipe script.

## Gaps

No mechanical gaps detected. Still DRAFT; host review is required.

## Limitations

- DRAFT only. Mechanical completeness is neither acceptance nor authority; this tool grants no permission and does not authenticate AP06-ACCEPT.
- Selected-source-only comparison at the supplied checked_at: no assurance of freshness or exhaustive discovery of later or relevant sources.
- Reference checks are host-supplied observations, not authenticated evidence. No sources, quotes, links or source hashes are independently verified here.
- Changed dependencies require reassessment, not automatic falsehood or revocation of recorded decisions or authority.
- Host review must assess requirements, contradictions, mandates and the substantive adequacy of test observables; nonempty text is not proof.
- Export review is required for every authored field, including IDs, reasons, test methods and task values. No string checker proves privacy or public safety.
- The host must use Runtime's actual validator, review and freeze file bytes, and obtain independent review and protected integration. This draft neither generates nor executes acceptance and never invokes Runtime.
- No new authority, active driver change or whole-goal success from task PASS.
- Input snapshots are dated, not a completeness guarantee.


Approval binds this draft and its frozen host recipe; AP06 draft labels are preserved as history.
