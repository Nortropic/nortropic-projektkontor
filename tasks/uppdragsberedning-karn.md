# AP06 core: source-bound assignment preparation

Build only tools/assignment_preparation.py, tools/test_assignment_preparation.py,
and tools/ASSIGNMENT_PREPARATION.md. No CLI yet. Reuse existing change_assessment.py
(read-only), with a normal import from sibling tools. Implement pure, silent
prepare(case, check, spec) -> JSON-compatible dict. No filesystem/network/process,
hashing, discovery, Runtime invocation, acceptance execution/generation or mutation.
Use Python stdlib only. Tests synthetic. Document exact schema and trust boundary.

AP06-ACCEPT authorizes the host to choose technical tasks within this phase; it
is not data that this function can authenticate. AP05 assesses source applicability;
agent chooses requirements, assesses contradictions and mandates, reviews exports
and sufficiency of observable tests. Tool is a mechanical compiler of selected
material, NEVER a permission engine. All output is DRAFT even with no gaps.

INPUT CONTRACT (case/check exactly existing AP05 schema):
spec has exactly schema (integer 1), action (case action id), references,
reference_checks, requirements, tests, export, task. Unknown fields are errors.
References are explicit selected source lookups, not fabricated RND identities:
 {id,source,version,quote}, all nonempty strings except quote may be empty for a
 non-quote locator. source must be a case source; version equals its pinned label.
reference_checks entries have exactly {id,source,version,sha256,quote,status};
 status matched/mismatch/not_checked. A matched check must bind ALL reference
 fields and the selected source's sha256. These are host-supplied observations of
 existing lookup/quote tools, NOT authenticated evidence from this pure function.
 Never execute code or fetch links to establish a reference. Unknown/duplicate
 IDs or contradictory bindings ValueError; missing/mismatch/not_checked become
 concrete gaps. A source changed/missing/unsafe/not_checked in AP05 means dependent
 claims/requirements/reference checks need reassessment even if a lookup matched.
requirements entries exactly {id,text,reason,claims,references,tests}:
 unique nonempty id,text,reason. claims reference existing case claim ids;
 references select reference ids; tests select test ids. Lists unique, empty
 lists allowed as explicit gaps, unknown identifiers are errors. These are derived
 requirements, not verbatim source facts. Author-authored text/reason/IDs ARE
 EXPORT FIELDS and require content review; raw claim text/source metadata is private.
tests entries exactly {id,observable,method}: unique nonempty id, strings for
 observable and method; empty/whitespace means a concrete verification gap.
 A test link is not enough: observable must describe behavior/result. Function
 checks nonempty only; human substantive review checks its adequacy.
export exactly {title,context,scope,limitations}: title nonempty; scope and
 limitations lists of nonempty strings; context list of {kind,text} where kind
 fact/judgment/decision/authority, text nonempty. These fields are authored for
 the worker, not automatic copying/redaction of private sources. No claim of
 public safety or complete source discovery. Empty context/scope/limitations gap.
task is a DRAFT of Runtime's current office format. Permitted keys ONLY id,target,
base,runtime_revision,allowed_paths,attempt_seconds,automatic_retries,steps,
acceptance,acceptance_sha256,brief. Missing keys or null/empty value => specific gap,
retain exactly supplied values; NEVER defaults/placeholders. Nonempty invalid
values => ValueError. Mirror reviewed runtime/task.py profile: office target only;
full lowercase hex40 base/runtime_revision, hex64 acceptance_sha256; id regex
[a-z0-9][a-z0-9-]{0,79}; unique explicit safe regular tools/ paths matching
[A-Za-z0-9_./-]+ with no empty/dot/dotdot parts, forbid tools/kontor.py and
 tools/assignment_preparation.py (active core), comparing both forbidden names
 and duplicate paths with casefold because the qualified Mac filesystem accepts
 case aliases (e.g. tools/KONTOR.py). No Runtime change is needed.
 integer attempt_seconds1..3600,
integer automatic_retries=0; steps list of exactly {provider,prompt}, codex only,
nonempty prompt. acceptance and brief must be safe relative explicit paths under
acceptance/ and tasks/ respectively. No acceptance source/code in inputs/output.
Host later uses Runtime's actual validator and freezes reviewed file bytes.

OUTPUT CONTRACT:
exact top keys status='draft', mechanical_complete (not gaps), gaps (list of
{code,subject} nonempty strings), private, package. Use stable gap codes documenting
relevant fields. subject exported only public requirement/test/task field id or
reference ordinal (never private source/ref identifiers or path).
private retains AP05 report under assessment and full reference/requirement
trace plus spec as needed (private values never copied into package).
package exactly brief (Markdown), task_draft (deep copy of supplied task),
requirements (list only id,text,reason,tests), tests (copy), gaps (copy), limitations
(nonempty list). brief renders export title/context separated by kind, scope,
requirements/test observables, gaps and limitations. Include unmistakable draft,
no authority, selected-source-only, host review/freezing and export-review caveats.
Do NOT render raw AP05 facts/decisions/authority/source IDs/paths, private claim ids,
reference ids/quotes or checks into package. Explicit export fields remain the
host's publication responsibility; a string checker cannot prove privacy.

Use change_assessment.assess(case,check), do not duplicate its hash/time/check
semantics. Preserve decisions/statuses even when applicability changes. Selected
action must have authored granted authority with sources and unchanged dependency
coverage, else specific gap, not permission. Each selected requirement needs
claims/references/tests and current dependencies, each supplied reference needs a
matched bound observation. Do not mutate inputs; earlier versions preserved by
caller. Malformed structures raise ValueError, known incomplete meaning gives
marked draft. Empty requirements/tests => gap. Always explain that mechanical
completeness is neither acceptance nor authority and comparisons are only at
supplied checked_at, not assurance of freshness or exhaustive later-source search.

Test legitimate case; changed/missing/not_checked source only affecting dependent
requirements; invalid/unknown/duplicate IDs, wrong lookup version/hash/quote,
missing authority and verification; missing task bindings never invented; invalid
repo/paths/host core; private fields absent from package; no input mutation or
side effects. Frozen host tests run separately in native read-only sandbox.
The next Runtime candidate uses this integrated core to prepare the actual CLI
assignment and cannot edit this core or its own host inputs/acceptance.
