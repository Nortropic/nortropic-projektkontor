# AP-05 accepted build: reusable decision-bound change assessment

Owner AP05-ACCEPT authorizes this bounded office task. Read AGENTS for context;
this frozen TASK supersedes its older phase description for this task. Runtime
owns operator startup, frozen acceptance, independent review and publication.
Edit ONLY tools/change_assessment.py, tools/test_change_assessment.py and
 tools/CHANGE_ASSESSMENT.md. No installs, engine, source access, other writers,
authority changes or publishing. Use only Python standard library. All examples
and fixtures must be synthetic. The host alone reads real private case sources.
Review must also check no private source text, local paths, credentials, raw logs
or inferred private information is introduced; all new code/example content will
be public. The host preserves actual case assessments separately.

Purpose: retain an agent's traceable assessment and compare selected bound
sources, exposing which claims need human/agent judgment again. Never decide
truth, revoke owner decisions, grant permission or claim exhaustive source search.
Reuse Runtime tools/evidence_index.py for hashing/verification OUTSIDE this module;
do not implement a second hasher, fetcher, scheduler or engine. The host wraps
that existing tool's manifest and verification JSON in a timestamped check below.
This module consumes the explicit observation; it cannot authenticate its author.

Implement pure APIs reference_manifest(case) and assess(case, check). Both reject
invalid input with ValueError; neither mutates inputs or accesses files, network,
processes or prints during import/API use. CLI has only input JSON reads and stdout:
`python3 -B tools/change_assessment.py manifest CASE.json`
`python3 -B tools/change_assessment.py report CASE.json CHECK.json`
Return 0 valid, 2 invalid, one JSON object stdout including nonempty error on invalid.
Changed/missing/unobserved sources are valid report data, not a parsing error.
CLI rejects duplicate JSON keys and non-JSON constants. It never writes a file.
For the pure API import check the host preloads argparse, copy, datetime, io, json,
math, os, pathlib, re, sys and types. Keep API dependencies within these or built-ins.

Exact input schema (no extra/missing keys at any specified object):
case = {schema:1, id:nonempty string, created_at:timezone ISO8601 timestamp,
 sources:[{id,title,version,path,sha256,size}],
 claims:[{id,kind,text,reason,standing,sources:[source ids]}],
 actions:[{id,text,reason,claims:[claim ids],authority:{status,scope,sources:[source ids]}}],
 next_action:action id}.
Every sources/claims/actions list must be nonempty. Their ids unique within kind.
All named textual fields nonempty strings, except constrained enums. Lists of
references are unique. Every claim needs at least one valid source and reason;
every action needs at least one valid claim and reason. Source title/version are
agent-supplied labels, not proof. Path is a unique safe POSIX relative path:
reject absolute paths, drive prefixes, backslashes, NUL, empty/dot/dotdot components.
SHA256 64 lowercase hex, size nonnegative integer (not bool). schema exactly int1.
kind is fact, judgment or decision. standing is authored nonempty text retained
verbatim; code does not adjudicate it. authority.status is granted, not_granted or
not_established, scope nonempty. Every authority reference must exist. granted
requires a nonempty source list; other statuses may have an empty list to express
missing authority honestly. Claim/action/source ids must be nonempty strings.
created_at and checked_at must parse as valid timezone-aware calendar timestamps;
checked_at cannot precede created_at. Prefer simple stdlib datetime parsing.

reference_manifest returns the existing evidence_index format exactly:
{version:1,files:[{path,sha256,size}]} sorted by path. It validates the WHOLE case,
not merely sources, and never updates expected hashes.

check = {checked_at, manifest, result:{ok:bool,files:[{path,status}]}}.
manifest must equal reference_manifest(case) in structure/content including sorted
entries. result paths must be unique and present in the reference manifest.
status is ok, changed, missing or unsafe (the existing verifier's vocabulary).
result.ok must equal all reported entries having status ok; empty subset means
true, consistent with evidence_index, but all absent sources become not_checked.
Missing paths in result are not_checked, never silently ok. Unknown paths/status,
wrong manifest, contradictory ok flag, extra keys or malformed values reject.
Check is an explicitly supplied observation, not independently authenticated.

assess returns JSON-serializable:
{schema:1,case_id,created_at,checked_at,structure_valid:true,
 source_checks:[{id,status}], coverage:{checked:[ids],not_checked:[ids],complete_search:false},
 facts:[claim reports],judgments:[claim reports],decisions:[claim reports],
 actions:[action reports],next_action:the chosen action report,limitations:[strings]}.
Order reports by input order; coverage lists likewise. Claim report preserves ALL
original fields and adds source_check ('unchanged' or 'needs_reassessment') and
 affected_sources [dependency ids whose check is not ok]. Action report preserves
ALL original fields and adds same fields; its dependencies are union of its
claims' sources AND its own authority sources, ordered by case.sources. An
unauthenticated/unestablished authority remains so even when all sources match.
A changed authority basis marks applicability for reassessment; do not rewrite
reported authority status or claim standing. next_action MUST be the chosen
fully annotated action, not merely its id. No overall approved/authorized/go flag.

Limitations must explicitly say: structural validity/source integrity is neither
substantive approval nor authority; unchanged selected sources is not exhaustive
or necessarily current knowledge; changed/missing/unsafe/not_checked requires
reassessment, not automatic falsehood/revocation; observation/authority/standing
are supplied judgments, not independently authenticated facts; timestamps describe
only this comparison. Re-running with the same case must preserve its expected
versions; revise assessments explicitly as NEW files retaining predecessor.

Add meaningful unit tests for legitimate data and scoped affected-claim/action
propagation; missing, unsafe, not_checked, changed authority-only source; malformed
bindings/refs/reasons/authority; immutability; CLI duplicate keys; and no I/O in
pure import/APIs. Never alter original external files. Tests may use isolated
fixtures under .scratch (only writable place for review). Document both CLI
and an exact host recipe to reuse Runtime evidence_index.py: emit the manifest,
verify selected source root read-only, wrap unchanged manifest plus returned
result with checked_at, then report. Verifier exit1 is valid mismatch data to retain;
exit2/error is unavailable measurement and must never become successful check.
This wrapper may be ordinary operator Python in the method, not another service.
Report's source paths may be sensitive: keep actual cases/observations local;
publish only a separately content-reviewed redacted report, never a raw dump.

The frozen host acceptance runs candidate code in the existing native read-only
sandbox, including import/pure-call no-I/O tests and invalid cases. Independent
Runtime review sees this brief and all allowed files before protected integration.
