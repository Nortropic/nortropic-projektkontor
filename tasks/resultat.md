# Accepted AP04 task: retrieve the verified office delivery

Owner AP04-ACCEPT authorizes this bounded task. Work only on
`tools/kontor_result.py` and `tools/test_kontor_result.py` in the candidate.
Runtime owns process checks, tests, review and publication. Do not run operator
commands, edit the CLI/mandate/acceptance, start other writers, or publish.
Read AGENTS.md for project context and this TASK.md for the actual task.

Implement `render(report)` in tools/kontor_result.py. The existing host-owned
`tools/kontor.py resultat` invokes it with the dictionary returned by Runtime's
read-only inspection. The module must be a pure presentation function: no file,
network, subprocess or other external access during import or rendering; do not
mutate the input. Use Python standard library only. The verifier preloads copy, io, json, math,
os, pathlib, re, sys and types before installing its I/O audit hook; your simple
renderer should need only re/math and built-ins. Add useful unit tests in the
second allowed file. The existing CLI must work without modifications.

Return a JSON-serializable dictionary with keys:
- `observation`: snapshot or unavailable; unknown/malformed input is unavailable.
- `task_id`, `phase`, `target` when provided safely by the report.
- `status`: delivered only for a structurally valid verified completion below;
  not_delivered for a valid saved noncompleted observation; unavailable otherwise.
- `live`: false, `remote_current`: false, `limitations`: a nonempty list explicitly
  explaining this is a saved Runtime observation, not current engine/remote status.
- `observed_at_epoch` and `age_seconds` when valid nonnegative finite numeric
  values (booleans are not numbers for this contract).
- for delivered only: `runtime_revision`, `input_revision`, `base`, `candidate`,
  `merge_commit`, `tree`, `url`, `acceptance_sha256`, `review_run`, `evidence`.
- for a noncompleted snapshot: preserve `waiting_reason` from report.state if
  it is a string. Missing evidence/error text must remain clear on unavailable.

A verified completion requires observation=snapshot, phase=completed,
verified_delivery exactly true, target=Nortropic/nortropic-projektkontor,
nonempty task_id/review_run/evidence, valid timing above, 40 lowercase hex digits
for runtime_revision/input_revision/base/candidate and integration.merge_commit/
tree, 64 for acceptance_sha256, integration.merged exactly true,
integration.candidate equal to report.candidate, and a GitHub pull URL for this
exact target ending in a positive integer. Any missing/inconsistent field makes
completion unavailable, never delivered. Only the following noncompleted phases
are supported: accepted, running_codex, running_claude, reviewing, publishing,
waiting_access, waiting_diagnosis, waiting_review, waiting_publication_reconciliation.
Unknown phases are unavailable. Do not expose an integration/commit as delivered
when verified_delivery is false or any required evidence is missing.

The host independently binds Runtime input, acceptance, review and integration
before presentation. This renderer must not claim to verify GitHub live. The host
will compare your real output to actual Runtime receipts and protected remote
integration after this task finishes. Your output alone is not delivery evidence.

Acceptance runs the host-frozen verifier outside candidate write access, executing
your code in a read-only native sandbox with only scratch writable. Independent
review sees this entire brief and the two allowed files. Import/run tests using
existing Python if useful; do not install dependencies.
