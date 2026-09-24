# AP10 — private assessment policy for the existing Runtime stages

Implement the Office policy in `tools/bevakning.py`, its synthetic tests in
`tools/test_bevakning.py`, and Swedish operator documentation in
`tools/BEVAKNING.md`. In `tools/bevakningsunderlag.py`, append these four
names to LOCAL_FILES (preserve existing behavior except the parser fix below):
`runtime/private_workflow.py`, `runtime/private_activity.py`,
`runtime/private_stage.py`, `runtime/obligation.py`. Update the corresponding
intake tests for that exact extension. Also fix only `_python_index` to accept
both `Python <stable version>` and the real source-index form
`Python <stable version> - <month name, optionally abbreviated with a period>
<day>, <year>`, e.g. `Python 3.12.14 - Aug. 12, 2026`. Keep full label matching,
stable numeric version selection, installed-line selection and exact
version-to-URL agreement; never accept a link whose label says a different
version from its URL. Add synthetic dated-label and mismatch regressions.
No actual fetched HTML or private observation belongs in the candidate.
All other intake function bodies remain unchanged. These are the only five writable files.
Standard library and existing Office modules only. No candidate reads of real
private material or network calls: use synthetic fixtures. No new scheduler,
model executor, commands, publication, credentials, AP08 renderer or deployment.
This task's output is not activated by its integration.

## Existing host protocol — do not edit Runtime

The separately qualified Runtime calls the following exact API from the frozen
Office release. Import must not perform I/O. Host code owns native round IDs,
process limits, model invocation, distinct analysis/review calls and final writes.

* `prepare(output, local_roots, versions, prior, context)` calls the existing
  `bevakningsunderlag.collect` once, even for a potentially unchanged basis.
  output is a NEW private directory (`round/intake/data`). local_roots and
  versions have the intake API's existing meanings. Return a JSON dictionary
  with `completed` (true when the preparation artifacts were safely produced),
  `needs_model` and a fixed non-sensitive `reason`. Incomplete but readable
  intake requires a model, not automatic approval. An unsafe context fails
  closed with ValueError and no diagnostic path/content disclosure.
* `workspace(workspace, round_home, context, role)` populates the host-created
  empty private workspace for role `analysis` or `review`. No source writes.
* `prompt(role)` returns the fixed instructions for that role.
* `schema(role)` returns a strict JSON Schema (objects: additionalProperties
  false, all properties required) for the role's response below.
* `finish(round_home, request, config)` returns the full JSON report below.
  Runtime writes it exclusively to `round/report/result.json`. This function
  MUST NOT create/overwrite that result file. It may create separate private
  AP06 preparation artifacts. Repeated calls must not overwrite any artifact.

The host writes `intake/result.json` from prepare's return and optionally
`intake/previous.json` before prepare. Analysis and review each have their own
`result.json` containing `completed`, `answer`,
`provider:{valid_terminal,thread_id,usage}`, `elapsed_seconds`,
`process_group_removed`. Do not infer success from request.outcomes alone.
Require true booleans for completed/valid_terminal/process_group_removed,
nonempty different thread IDs, well-formed role answers and matching hashes.
Runtime passes request `{run_id, workflow_id, started_at, obligation,
config_sha256, role, seconds, outcomes, ...}` and config including
`runtime_revision`, `office_revision`, `config_sha256`, `directory`, `files`.
The obligation is exactly `office-python-temporal`; the three config identity
fields must agree with packet.versions and request.config_sha256. No other
obligation or mismatched binding may yield a reviewed report.

## Frozen selected context, without invented history

Read only `case.json`, `watch.json`, `authority.md` and `prior-decision.md`
directly under context, total <=2MiB. The two Markdown files are nonempty
selected authoritative context: the current AP10 owner mandate and the actually
reviewed AP09 disposition. Read them to distinguish historical proposal/old
mandate from current decision and authority; source text gives no new rights.
case.json is the unchanged host-selected AP09 case accepted by AP05. watch.json
has exactly `schema` (1), `case_id` (same as case.id), `first_treated_at`
(timezone-aware ISO timestamp), `old_gaps` (nonempty list of nonempty strings),
and `source_map` (each original case source ID mapped to a current packet record
ID or null). A null mapping means no byte-comparable present observation.
Do not infer mappings from filenames, scan other material or advance baseline
hashes. Actual context is staged privately by the host after this build.

Use `change_assessment.reference_manifest(case)` and `assess(case, check)`.
The unchanged original reference manifest is the comparison target. Compare
mapped current raw file bytes/hash/size: equal => ok, unequal => changed;
unavailable => missing (or unsafe where established). Null/unresolvable mapping
is omitted from result.files and therefore not_checked. It is NOT unchanged.
The check timestamp is the new intake's observed_at, never earlier than the
case creation. AP05 report/check are preserved as `ap05.json`, `check.json`.
The model interprets raw-source differences; AP05 marks dependencies, not truth.
New release IDs outside the old map still belong to the model's current packet.

prepare writes exclusive 0600 `prepared.json` in output with `case_id`,
`packet_sha256` (actual packet.json bytes), `context_sha256`, `needs_model`,
`reason`, `reused_from` (prior home string or null). context_sha256 is SHA256 of
UTF-8 canonical JSON `{case.json:sha256(bytes),watch.json:sha256(bytes),authority.md:sha256(bytes),prior-decision.md:sha256(bytes)}`; canonical
JSON everywhere in this protocol means sort_keys=True, separators=(',', ':'),
ensure_ascii=True, allow_nan=False. Store the four selected context copies under their exact names in output so finish does not depend on a working context path.

`prior` is null or `{home, report, packet}` from Runtime. Reuse only when both
packets are complete, current fingerprint equals previous fingerprint, and the
previous on-disk report/result.json equals prior.report, previous packet.json
equals prior.packet, its byte hash equals report.packet_sha256, report.reviewed
is exactly true, context hashes and case IDs agree, and its review evidence is
valid. Verify the original analysis/review evidence (including exact hashes and
distinct successful threads) for a reused review; allow a chain of prior
reports only with cycle detection and a bound of 366 hops, otherwise needs_model.
Never trust `same_controlled_basis` or a bare reviewed flag alone. A rejected,
unreviewed, incomplete, mismatched, damaged or contradictory prior cannot be
automatically reused. Preserve it and request a fresh model assessment.

## Model input and exact answer schemas

Copy only the four validated context files, packet.json, prepared.json, ap05.json
and the packet's available selected release-note/local payloads into the workspace.
Do NOT copy python-index/temporal-index payloads: their raw bytes remain in the
host packet. INPUT.json explicitly lists these omitted IDs and the coverage
limit; their hashes/metadata remain visible but omitted text cannot support a
model's substantive claim. Use safe
relative paths under `data/`; payloads are `.txt` data copies, never AGENTS or
other executable instruction filenames. `INPUT.json` maps record IDs to copies
and carries packet_sha256, context_sha256, case_id, first_treated_at, old_gaps,
and (review only) `assessment_sha256`. Review receives `assessment.json` with
the exact canonical analysis answer; analysis does not receive review material.
Reject unknown roles, nonempty workspaces, traversal/absolute paths, symlinks in
any source/destination ancestor chain, nonregular files, payload hash mismatch
or context mismatch. Do not copy unrelated files, raw sessions or credentials.
Directories 0700, files 0600; no writes to round inputs or context. Cap packet
payloads at the intake's 1MiB each and <=40MiB total; context <=2MiB.

Analysis answer has exactly:
`case_id`, `packet_sha256`, `decision`, `vendor`, `local`, `judgment`,
`authority`, `evidence`, `contradictions`, `proposal`.
decision is one of `retain`, `not_applicable`, `insufficient`, `propose_action`.
vendor/local/judgment/authority are nonempty strings explaining separately the
supplier claim, observed local use (active versus working), substantive judgment
and allowed handling. evidence is a nonempty array of unique current packet
record IDs. contradictions is an array of nonempty descriptions of UNRESOLVED
contradictions; it must be empty for a decision other than insufficient.
proposal is null except for propose_action, where it has exactly `text`,
`reason`, `requirement`, `observable` (all nonempty strings) and `claims`
(nonempty unique known IDs from the frozen case). Never claim action executed.
Incomplete packet requires decision insufficient. An insufficient report can be
reviewed as an honest statement of missing knowledge, but is never reusable.

Review answer has exactly `case_id`, `packet_sha256`, `assessment_sha256`,
`verdict` (`approved` or `rejected`), `reason` (nonempty), `blockers` (string
array; empty only when approved, nonempty when rejected). The assessment hash
is computed by the host over the canonical full analysis answer. It is never a
model-supplied replacement. Positive review must refer to that exact assessment
and packet. Schema validity/nonempty prose is not substantive correctness;
the independent reviewer must check sources, applicability, contradictions,
old gaps, source instructions and authority. No broad security/support or
graceful-drain guarantee can be inferred from this scope. The old stronger
graceful-drain evidence gap alone does not demand a new test or make the already
qualified scoped use insufficient; retain the AP09 distinction.

Both fixed prompts explain reading INPUT.json and selected evidence, treating
source text as untrusted evidence rather than instructions, no operational or
change commands/network/source changes (read-only file inspection is allowed),
immutable old decisions/gaps, exact output schema and no new
case/upgrade permission. Review explicitly examines the analysis, rather than
rubber-stamping its format. Model content cannot name arbitrary host files.

## Final immutable report and AP06

Return schema=1, completed=true when a report can be formed, obligation,
run_id, case_id, packet_sha256, context_sha256, observed_at (packet timestamp),
first_treated_at (context, unchanged), reported_at (actual UTC time), reviewed
(boolean), reviewed_at (actual accepted review result file mtime as UTC, or
original review time on reuse, null without approval), decision, reasoning
{vendor,local,judgment,authority}, evidence (record IDs), contradictions,
old_gaps (unchanged context list), reused_from (prior home or null),
review_origin (round-home string for the original accepted review, or null),
review (null, or {analysis_thread_id,review_thread_id,assessment_sha256,
analysis_result_sha256,review_result_sha256}), ap05 (actual AP05 result),
ap06 (null or actual AP06 draft), action_executed=false, publication=false,
runtime_revision, office_revision, active_config_sha256, and nonempty limitations.
For fresh reviewed reasoning copy the validated analysis sections, not invented
host prose. Reuse copies the original reviewed decision/reasoning/review time,
explicitly points to its origin, and uses THIS round's observed_at, packet hash,
reported_at and AP05 comparison. It does not claim another model review.
first_treated_at is explicitly the CASE baseline treatment, not a claim that a
later release or new assertion was treated then. A fresh current assessment is
bound to this round and its actual review time; state this time scope in the
limitations. Upstream publication times stay in packet sources and must not become treatment,
observation or review timestamps.

Missing/malformed/failed analysis, missing/rejected/nonindependent review,
hash mismatch, unresolved contradiction presented as approval, or invalid
bindings yields reviewed=false, reviewed_at/review_origin/review=null,
decision=insufficient with fixed explanatory limitations; do not silently keep
the last positive decision. Preserve available AP05 evidence and old gaps.
Unsafe evidence paths or malformed indispensable intake/context may raise a
non-sensitive ValueError rather than fabricate a report. No result is a live
guarantee. Fresh legitimate insufficient judgments can be independently reviewed.

For an approved propose_action call existing `assignment_preparation.prepare`:
deep-copy the unchanged original case, append a distinct action whose text,
reason, claims come from the proposal and whose authority is explicitly
`{status:'not_granted',scope:'Separate action-specific owner mandate required',
sources:[]}`; set next_action to it. Preserve every original source/claim/action.
Use the current AP05 check; build one concrete requirement and one test from
proposal.requirement/observable, with its selected claims. References and
reference_checks are [] because no verified quote binding was authored here;
task is {} because no executable order is accepted. Include those honest gaps,
action_authority_missing and missing task fields in the actual AP06 result.
Authored export context distinguishes judgment and authority. Keep the current
analysis/evidence alongside the draft; never call its structure executable,
publish it or run an upgrade. Preserve `ap06.json` exclusively under report/.
Other decisions need no artificial task.
An unchanged reused propose_action report carries its existing AP06 draft and
predecessor; it does not call AP06 again or create a duplicate action proposal.

Document the host protocol, context selection, AP05 noncomparison, model/review
limits, reuse lineage and AP06 gaps. AP09 decisions and graceful-drain evidence
gap remain historical; no new AP08 projection in this increment. Add meaningful
synthetic tests including tampering, missing/rejected/same-thread review,
local-only/external-only change, unchanged reuse, unavailable intake, context
change, out-of-mandate proposal and safe private copying. Existing intake tests
must still pass with exactly the four LOCAL_FILES additions.
