# Separately reviewed AP11 task

# DRAFT — AP11 handoff

DRAFT only. Mechanical completeness is neither acceptance nor authority; this tool grants no permission and does not authenticate AP06-ACCEPT.

## Context

### Fact

- Frozen host observation supplies actual integrated work

### Judgment

- CONTEXT.json integrated.reconciliation records requirement A (task ap11-step-5, candidate cd132fab1b2965ee57aea60c798c1a630eebf125) as merged with merge_commit dd866764a24ec4c0cff365a5479b059b88774daa, tree e32e1947, PR 28, with review 4 approved (run 9308cd4f, verdict approved, no blocking findings) and the frozen recipe acceptance PASS bound to tools/development_result.py 1e5108c8… — that merge commit is the value put in depends_on, because B may only be built on the A interface that actually exists in the base tree, and the delivered tools/development_result.py in this workspace matches that integrated hash. The actual reconciliation result (actual_reconciliation_result, and the identical observation.md) shows requirement A status delivery_supported and requirement B "AP11 överlämning genom befintlig AP08" still status missing with task null and problem "No task is bound to this requirement", and its own next_action, authority "accepted", is "Bereda återstående AP08-överlämning från faktisk A-integration". So B is the only accepted remaining work of G1 and it is not yet prepared. The frozen host recipe VERIFICATION_RECIPE.py (sha256 48a787bb…, matching CONTEXT acceptance_sha256) already fixes B's shape: it imports development_result, development_handoff and agarbild from tools/ and exercises m.present(goal, reports, picture), so the task is exactly the missing connection module, not a new platform. This stays inside G1/G4 and the owner's "Delmål 3 återanvänder AP-08 och befintliga resultatläsare. Bygg bara den saknade kopplingen": no new report engine, no trust semantics, no scheduler, no paid connection, no operator start, no publication and no execution of generated code — this answer only returns structured data. Whole-goal completion is not claimed and cannot be: the module is required to keep whole_goal_complete False and no task PASS establishes G10, which the separate final review judges. Hold would be wrong here: the sources verified ok (source_check.result.ok true), the authority (AP11-ACCEPT a2b3f143…) and amendment 1 are present and readable, the integrated A module is delivered and readable, and every file the task needs is in delivered_files.

### Decision


### Authority

- AP11 accepted scope only; draft still requires independent scope and verifier review

## Scope

- Add the missing AP11 handoff connection (requirement B) as one small pure module plus its unit tests, reusing the actually integrated A interface and the existing AP08 owner-view reader. Allowed paths, and nothing else: tools/development_handoff.py (new) and tools/test_development_handoff.py (new). Do not modify tools/development_result.py, tools/kontor_result.py or tools/agarbild.py, do not add dependencies, do not create a tests/ directory, and do not touch anything else in the tree.

tools/development_handoff.py defines exactly one public entry point:

    present(goal, reports, picture) -> {"reconciliation": ..., "picture": ..., "html": ...}

It must be a pure translation layer, in the same spirit as the integrated tools/development_result.py: it performs no I/O, reads no clock, starts nothing, grants no authority and creates no second reconciliation or rendering logic of its own.

Reconciliation comes from A. Import the module (`import development_result`) and call `development_result.reconcile(goal, reports)` through the module attribute at call time — exactly once per call, no from-import, no caching of the function object at import time — and return that returned object unchanged as value["reconciliation"]. The frozen recipe replaces the attribute with a wrapper and asserts both that the wrapper was reached and that the returned reconciliation equals development_result.reconcile(goal, reports); a reimplementation or a bound reference will fail.

HTML comes from AP08. Build value["picture"] as a report-picture dict that satisfies agarbild.validate, and produce value["html"] by calling `agarbild.render` through the module attribute at call time, exactly once, on that same picture, so that value["html"] == agarbild.render(value["picture"]). Do not emit HTML yourself and do not re-escape: agarbild owns the rendering and escaping.

The picture is derived from the supplied picture, never invented. Carry schema, generated_at, title, summary, scope, capabilities, owner_decision and issues over from the supplied picture (owner_decision must compare equal to the supplied one), and keep the supplied evidence list as the leading prefix of picture["evidence"], appending only new entries after it with fresh unique ids matching agarbild's [A-Za-z0-9-]+ rule. Every evidence reference used by work items, next_action, owner_decision and issues must resolve to an id that exists in the final evidence list.

Work items carry the reconciliation to the reader. Emit one work item per goal requirement, in goal order, whose title plus text contains that requirement's text verbatim (so the reader sees the named requirement, and agarbild does the escaping). Map status to state strictly: "delivery_supported" -> "finished"; every other status ("missing", "ambiguous", "not_supported") -> a non-finished state from agarbild.STATES, and include that requirement's recorded problems in the item text. With two named requirements there are at least two work items, and when nothing is supported no item may be "finished".

Authority and dating must not be smuggled. picture["next_action"]["text"] must equal goal["next_action"]["text"] and picture["next_action"]["authority"] must come from the goal's next_action, never from the supplied picture: if the supplied picture's next_action disagrees, fail closed — either raise ValueError or override with the goal's value, one deterministic documented behaviour. For a requirement whose reconciliation result carries observed_at_epoch, the appended evidence entry must carry observed_at as an ISO8601 UTC timestamp equal to that saved epoch (the saved observation's own time, never a render time or a clock reading), and must carry the saved observation's runtime_revision and integration merge_commit as evidence revision/locator/text so they reach the HTML. If a saved observation's time is later than the picture's generated_at, agarbild.validate would reject it: raise ValueError rather than returning an invalid or silently re-dated picture.

Nothing may claim completion. reconciliation["whole_goal_complete"] stays False and must never be presented as a finished whole goal; the reconciliation's limitations must be carried into the picture (picture["issues"]) so the reader sees that this is a dated reading of saved observations, not live or remote status and not activation.

Inputs are read-only: goal, reports and picture must compare equal to deep copies of themselves after present() returns, and the returned structures must not alias mutable parts of the inputs. Rejections from development_result.reconcile (non-dict or foreign goal, malformed requirements, non-list reports) must propagate unchanged, before any picture is built. No module-level side effects, no main(), no CLI, no argument parsing, and no import of os, open, subprocess, socket, ctypes, time or logging in the module: the recipe installs an audit hook around present() and any such effect fails the run.

tools/test_development_handoff.py is a unittest module next to it using only synthetic fixtures (no repository files, no network, no writes). Cover at minimum: the positive mixed case (one delivery_supported requirement plus one missing requirement in the same call); reuse of both existing readers through the module attributes; preservation of the supplied evidence prefix and owner_decision; authority taken from the goal and not from a conflicting picture; saved observation time retained; revisions and merge commit reaching the HTML; non-mutation of all three inputs; propagation of reconcile's ValueError for a foreign or malformed goal and a non-list reports; a saved observation newer than generated_at rejected with ValueError; and that no state is "finished" when no requirement is delivery_supported.

## Derived requirements

### R1

A new module tools/development_handoff.py is importable as `development_handoff` under `python -I -B` with tools/ on sys.path and defines present(goal, reports, picture) returning a dict whose keys are exactly 'reconciliation', 'picture' and 'html'; it imports only the standard library plus development_result and agarbild, has no module-level side effects, no main() and no CLI.

Reason: The frozen recipe imports development_handoff next to development_result and agarbild under `python -I` and reads exactly these three keys of m.present(...); an unimportable module or a different surface cannot be accepted, and a CLI or import-time effect would exceed the read-only handoff scope.

Tests: T1, T2, T3, T4, T5, T6, T7, T8, T9, T10

### R2

present() obtains the reconciliation by calling development_result.reconcile through the module attribute at call time, exactly once per call (module import, no from-import, no function object captured at import time), and returns that value unchanged as result['reconciliation'], which must equal development_result.reconcile(goal, reports); no reconciliation logic is reimplemented.

Reason: G1 and the owner mandate require B to use the ACTUALLY integrated A interface (merge commit dd866764…) and forbid a parallel reconciliation; the recipe swaps the attribute and asserts both that the wrapper was reached and that the returned value equals the real call, so only genuine attribute-time reuse passes.

Tests: T1, T2, T3, T4, T5, T6, T7, T8, T9, T10

### R3

present() obtains result['html'] by calling agarbild.render through the module attribute at call time, exactly once, on result['picture'], so that result['html'] == agarbild.render(result['picture']) and agarbild.validate(result['picture']) succeeds; no HTML is produced or escaped by the new module.

Reason: AP08 (tools/agarbild.py) is the existing owner-view reader that must be reused rather than re-created; letting agarbild own validation and escaping keeps the new module a thin connection and keeps the reader surface unchanged.

Tests: T1, T2, T3, T4, T5, T6, T7, T8, T9, T10

### R4

result['picture'] is derived from the supplied picture: schema, generated_at, title, summary, scope, capabilities and owner_decision are carried over (owner_decision compares equal to the supplied one) and the supplied evidence list is the leading prefix of picture['evidence'], with only appended entries after it, each having a unique id matching [A-Za-z0-9-]+; every evidence reference in work, next_action, owner_decision and issues resolves to an existing evidence id.

Reason: The recipe asserts picture['evidence'][:len(P['evidence'])] == P['evidence'] and picture['owner_decision'] == P['owner_decision']; preserving the supplied surface and only appending prevents the handoff from rewriting or dropping the owner's existing dated material, and agarbild.validate rejects dangling references.

Tests: T1, T2, T3, T4, T5, T6, T7, T8, T9, T10

### R5

present() emits one work item per goal requirement, in goal order, whose title plus text contains that requirement's text verbatim and whose text includes that requirement's recorded problems; state is 'finished' if and only if the reconciliation status for that requirement is 'delivery_supported', and every other status maps to a non-finished state from agarbild.STATES.

Reason: The recipe requires each requirement text to appear in the HTML, at least two work items, a finished item for the supported requirement, a non-finished item for the missing one, and no finished item when nothing is supported; an always-missing or always-finished handoff would either hide real delivery evidence or fabricate completion.

Tests: T1, T2, T3, T4, T5, T6, T7, T8, T9, T10

### R6

picture['next_action']['text'] equals goal['next_action']['text'] and picture['next_action']['authority'] is taken from goal['next_action'], never from the supplied picture; if the supplied picture's next_action disagrees, present() fails closed in one deterministic documented way (raise ValueError, or override with the goal's value), and never reports a wider authority than the goal states.

Reason: G3/G9 and the owner mandate forbid a candidate surface from widening authority; the recipe explicitly feeds a picture whose next_action authority is 'accepted' while the goal says 'none' and accepts only ValueError or an authority that stays 'none'.

Tests: T1, T2, T3, T4, T5, T6, T7, T8, T9, T10

### R7

For each requirement whose reconciliation result carries observed_at_epoch, the appended evidence entry carries observed_at as an ISO8601 UTC timestamp equal to that saved epoch and carries the saved observation's runtime_revision and integration merge_commit in its revision/locator/text fields; no clock is read anywhere in the module; if a saved observation's time is later than the picture's generated_at, present() raises ValueError instead of returning a picture agarbild.validate would reject or silently re-dating it.

Reason: The recipe asserts an evidence timestamp equal to the report's observed_at_epoch and requires merge_commit and runtime_revision in the HTML; G9 requires dated, explicit readings, and agarbild.validate forbids an observation later than generated_at, so the only honest handling of that case is a fail-closed error.

Tests: T1, T2, T3, T4, T5, T6, T7, T8, T9, T10

### R8

result['reconciliation']['whole_goal_complete'] stays False and neither the picture nor the HTML presents the whole goal as complete; the reconciliation's limitations are carried into picture['issues'] so the reader sees that this is a dated reading of saved observations, not live or remote status and not activation.

Reason: G1/G4/G9 and the disposition state that whole-goal completion is judged only by the separate final review and never by a component result; carrying the limitations forward is what makes the handoff a truthful read-only surface rather than an implicit claim of success.

Tests: T1, T2, T3, T4, T5, T6, T7, T8, T9, T10

### R9

present() performs no I/O and no external effect (no use of open, os, subprocess, socket or ctypes during the call) and does not mutate its inputs: goal, reports and picture compare equal to deep copies taken before the call, and the returned structures alias no mutable part of the inputs; ValueError raised by development_result.reconcile for a non-dict or foreign goal, malformed requirements or non-list reports propagates unchanged and before any picture is built.

Reason: The recipe installs an audit hook that fails on any such effect and asserts input equality before and after both calls; propagating the reader's rejections unchanged keeps the single validation authority in the integrated A module and prevents the handoff from turning missing or malformed evidence into a rendered positive.

Tests: T1, T2, T3, T4, T5, T6, T7, T8, T9, T10

### R10

tools/test_development_handoff.py is a unittest module using only synthetic fixtures (no repository files, no network, no writes) covering at minimum: the mixed case with one delivery_supported and one missing requirement; reuse of both readers through the module attributes; evidence-prefix and owner_decision preservation; authority taken from the goal against a conflicting picture; the retained observation timestamp; merge_commit and runtime_revision reaching the HTML; non-mutation of all three inputs; propagated ValueError for a foreign goal, a malformed goal and a non-list reports; ValueError for an observation newer than generated_at; and no 'finished' state when nothing is supported.

Reason: Negative and mixed cases are what distinguish a real handoff from one that always reports missing or always reports success; the integrated A delivery set the same pattern (module plus test_ module on the host-populated allowed path), and the candidate tests are the finer-grained complement to the coarse frozen host recipe.

Tests: T1, T2, T3, T4, T5, T6, T7, T8, T9, T10

## Verification

### T1

Observable: Under the host recipe, `import development_handoff` succeeds in an isolated interpreter with tools/ on sys.path and m.present(G, [], P) returns a mapping with 'reconciliation', 'picture' and 'html'.

Method: The frozen host recipe VERIFICATION_RECIPE.py imports the module in a sandboxed `python3.12 -I -B -c` run and immediately reads all three keys; the candidate unittest additionally asserts set(result) == {'reconciliation','picture','html'} and that importing the module executes no effect.

### T2

Observable: Replacing development_result.reconcile and agarbild.render with recording wrappers shows both wrappers were reached, and result['reconciliation'] equals the unwrapped development_result.reconcile(goal, reports) for both the empty-reports case and the mixed case.

Method: The host recipe patches both module attributes, asserts 'result' and 'ap08' are in the seen list and compares value['reconciliation'] to expected / actual_result(g,[R]); the candidate tests repeat this with unittest.mock.patch.object and a sentinel return to prove the call goes through the attribute at call time rather than a captured reference.

### T3

Observable: result['html'] is byte-identical to agarbild.render(result['picture']) and agarbild.validate(result['picture']) raises nothing, for both the empty and the mixed fixture.

Method: The host recipe asserts value['html'] == actual_render(value['picture']) and calls agarbild.validate(value['picture']); the candidate tests assert the same equality and that the module contains no HTML string construction of its own.

### T4

Observable: picture['owner_decision'] equals the supplied owner_decision and picture['evidence'][:len(P['evidence'])] equals the supplied evidence list, with appended entries having unique valid ids and every reference resolving.

Method: The host recipe asserts both equalities directly; the candidate tests additionally check that appended evidence ids are unique, match [A-Za-z0-9-]+, and that every evidence reference in work, next_action, owner_decision and issues is present in picture['evidence'].

### T5

Observable: With a goal whose requirement A is bound to a saved delivered report and requirement B is unbound, the picture has a 'finished' work item carrying requirement A's text and a non-finished work item carrying requirement B's text, statuses are delivery_supported and missing, and with no reports at all no work item is 'finished' while there are at least two of them.

Method: The host recipe runs exactly these two fixtures and asserts the per-requirement statuses, the finished/non-finished title+text matches, len(work) >= 2 and all(state != 'finished') for the empty case; the candidate tests add 'ambiguous' and 'not_supported' fixtures and assert those also map to non-finished states and that the recorded problems appear in the item text.

### T6

Observable: For a goal whose next_action authority is 'none' and a supplied picture whose next_action authority is 'accepted', present() either raises ValueError or returns a picture whose next_action authority is 'none'; in the normal case picture['next_action']['text'] equals the goal's next_action text.

Method: The host recipe wraps the conflicting call in try/except and accepts only ValueError or authority 'none', and separately asserts the text equality and authority 'none' for both non-conflicting fixtures; the candidate tests assert the chosen behaviour is the documented deterministic one and that no fixture can produce an authority the goal does not state.

### T7

Observable: Some evidence entry of the picture has observed_at parsing to exactly the UTC datetime of the report's observed_at_epoch, and the report's integration merge_commit and runtime_revision appear in the HTML.

Method: The host recipe converts R['observed_at_epoch'] with datetime.fromtimestamp(..., timezone.utc) and asserts an evidence observed_at equals it, plus `R['integration']['merge_commit'] in v['html']` and `R['runtime_revision'] in v['html']`; the candidate tests add a report whose observed_at_epoch is later than the picture's generated_at and assert ValueError, and grep the module for absence of any clock call.

### T8

Observable: result['reconciliation']['whole_goal_complete'] is False in every fixture, and the reconciliation's limitation strings appear among picture['issues'] texts.

Method: The host recipe asserts `is False` for both the empty and the mixed fixture; the candidate tests assert each string of result['reconciliation']['limitations'] occurs in some picture issue text and that no work item or picture field asserts overall completion.

### T9

Observable: No audit event for open, socket.*, subprocess.*, os.* or ctypes.* is raised while present() runs; goal, reports and picture compare equal to deep copies taken before the call; and a foreign goal, a malformed goal or a non-list reports raises ValueError before any rendering happens.

Method: The host recipe installs sys.addaudithook around both present() calls and asserts (G,P) == original and (g,[R],P) == before; the candidate tests deep-copy all three inputs, assert equality after the call, assertRaises(ValueError) for a goal with the wrong id, a goal with duplicate/empty requirement ids and reports passed as a dict, and assert agarbild.render was never reached in those failing cases.

### T10

Observable: A requirement text of '<script>fixture()</script>' yields HTML that contains '&lt;script&gt;' and not the raw '<script>'.

Method: The host recipe runs exactly this fixture and asserts both conditions; the candidate tests repeat it and confirm the escaping comes from agarbild.render rather than from any escaping in the new module.

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
