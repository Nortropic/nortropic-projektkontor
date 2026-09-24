# AP10 — narrow provider output-schema compatibility repair

Change only tools/bevakning.py, tools/test_bevakning.py and tools/BEVAKNING.md.
A real private round completed external/local intake but its analysis request
received HTTP400 invalid_json_schema: uniqueItems is not permitted at
properties.evidence. No valid analysis or independent review was produced.
Repair this precise representation mismatch; do not broaden policy or authority.

The public schema(role) API supplies Runtime's provider OUTPUT_SCHEMA.json for
analysis and review. Return the same schema except recursively omit uniqueItems
from provider-facing schema objects, including nested proposal.claims under
anyOf. Preserve every other keyword/value: required, additionalProperties=false,
types, enum, pattern, minLength, minItems, nullable proposal and all bindings.
The observed rejection supports removing uniqueItems only. Do not speculate by
removing other constraints or claim full provider compatibility from local tests.
Keep each call independent: modifying a returned provider schema must not alter
later schemas or host validation. Retain both roles and invalid-role rejection.

Separate that provider representation from strict host answer validation.
Host validation must still reject duplicate evidence IDs and duplicate proposal
claim IDs, including when a synthetic independent review approves the exact
malformed answer with recomputed hashes. Reused origins must undergo the same
strict validation and require fresh assessment when invalid. Never silently
deduplicate. Existing nonempty/known IDs,
proposal/decision consistency, case/packet/assessment bindings, independent
threads, verdict/blocker consistency, contradictions/incomplete basis, private
copies, prior reuse, no execution/publication and old gaps all remain unchanged.
Use the smallest clear separation (for example a strict schema internally and
its provider projection); no new dependency, validation framework or Runtime API.
Prompt instructions must still require unique evidence and proposal claims.
Preserve existing public signatures and result protocol. Document explicitly
that provider formatting is narrower than strict host acceptance.

Retain all existing synthetic product tests and add tests for both provider
schemas and duplicate rejection at the host/report boundary. Local read/edit
and synthetic test commands are allowed, using .scratch. No actual network,
private corpus, model calls, installation, operational/activation/publication
commands or credentials. No intakes, previous reports or active configuration
may be changed; no candidate changes outside the three named files.

The frozen host verifier retains all original policy behavior checks. Its only
historical scope-guard adaptation replaces an obsolete interpreter-dependent
intake AST checksum with the exact bytes of the qualified current intake, which
this task cannot modify. It adds exact provider-schema projection checks and
malformed-answer report checks. The old acceptance file remains unchanged.
Host review, AP04 execution, independent candidate review and protected
integration are separate. A synthetic PASS neither resumes a spent round nor
proves a completed new business assessment. The approved AP08 presentation task
remains separate and needs its actual Office base rebound before execution.
