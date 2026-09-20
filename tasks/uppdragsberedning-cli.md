# Host execution wrapper — AP06 CLI technical task

The owner accepted AP06, including this remaining CLI task. The host selects this
exact technical scope, supplied task bindings and separate acceptance module for
review and freezing through the existing Runtime route. Execution requires the
host's recorded independent approval and committed frozen inputs; this wrapper
and the generated DRAFT labels do not themselves create authority.

The generated draft below is retained verbatim so the preparation chain remains
visible. Its mechanical-completeness caveats describe the compiler output. After
host review/freezing, implement its R1–R7 only, in the accepted task's three files.
Use installed /opt/homebrew/bin/python3.12 for tests in the qualified environment.

---

# DRAFT — AP06 remaining task: private assignment preparation CLI

DRAFT only. Mechanical completeness is neither acceptance nor authority; this tool grants no permission and does not authenticate AP06-ACCEPT.

## Context

### Fact

- The core tools/assignment_preparation.py and its schema documentation are delivered on the exact task base; read them. AP05 is available read-only.

### Judgment

- The host chose a thin file interface and source-collision checks to make existing preparation usable without a second execution engine.

### Decision

- AP06 authorizes core first, then this real CLI task using it; earlier phases and map delivery remain closed.

### Authority

- Host reviewed/frozen task permits only the three listed tools files, synthetic tests and method. No Runtime/source/vault/host authority changes. Content-review all code/docs/test summaries before publication; no private data or absolute local paths.

## Scope

- Implement R1-R7 within the three listed files.
- tools/assignment_preparation.py, tools/change_assessment.py and tools/kontor.py are read-only.
- The host separately reviews and freezes acceptance; the worker must not generate or activate host acceptance.

## Derived requirements

### R1

Thin private preparation command: Expose prepare(CASE,CHECK,SPEC) through: python3 -B tools/bered_uppdrag.py CASE CHECK SPEC --source-root ROOT --output NEWDIR. Read strict JSON, call the delivered core; no new assessment logic.

Reason: Derived bounded CLI work required to complete AP06 using the delivered core; host substantive choices are separately reviewed.

Tests: T1

### R2

Immutable private bundle: Create NEWDIR exclusively, mode0700, with private.json, package.json, task.draft.json, brief.draft.md as exclusive0600 files. Parent must already exist. Existing output refused unchanged; preserve partial output on failure for diagnosis.

Reason: Derived bounded CLI work required to complete AP06 using the delivered core; host substantive choices are separately reviewed.

Tests: T2

### R3

No source or input mutation: Before any mkdir refuse symlink output or ancestors and all overlap directions between output and three input files plus selected case source paths under ROOT, including missing sources. Use resolved paths and casefold for Mac aliases. Do not create missing output ancestors. Reject symlink JSON inputs. Trusted local use, no claim of hostile concurrent-filesystem safety.

Reason: Derived bounded CLI work required to complete AP06 using the delivered core; host substantive choices are separately reviewed.

Tests: T3

### R4

Explicit drafts and safe failures: Well-formed incomplete input writes marked draft, exit0. Malformed/duplicate-key/non-JSON constants or unreadable inputs return exit2 with one generic JSON error, no raw private input or path in stdout or stderr. Stdout success has status=draft, mechanical_complete, gaps and file names. No ready/approved/authorized assertion.

Reason: Derived bounded CLI work required to complete AP06 using the delivered core; host substantive choices are separately reviewed.

Tests: T4

### R5

One engine, no activation: CLI does not hash or remeasure sources, refresh references, execute acceptance, start Runtime, signal, invoke models or publish. Do not edit tools/assignment_preparation.py, change_assessment.py, kontor.py, host tasks or acceptance.

Reason: Derived bounded CLI work required to complete AP06 using the delivered core; host substantive choices are separately reviewed.

Tests: T5

### R6

Usable method and endpoint examples: Write tools/BERED_UPPDRAG.md with complete reproducible synthetic example (or documented fixture in tools/test_bered_uppdrag.py), exact CLI command, AP05 measurement recipe pointer, host lookup/quote observations, real later decision IDs, explicit export review, immutable versions, host review/freezing and actual Runtime format. Explain meaning/verification adequacy remain host judgments. Clarify that the authorized chain driver and separate reviewer perform substantive review; the earlier core-method wording human substantive review creates no new owner gate. Only genuine goal/cost/authority changes return to owner. Use ignored evidence/**/local/ for real bundles and .scratch for isolated tests; arbitrary output path is not automatically private.

Reason: Derived bounded CLI work required to complete AP06 using the delivered core; host substantive choices are separately reviewed.

Tests: T6

### R7

Candidate endpoint regression: Add tools/test_bered_uppdrag.py with synthetic legitimate and negative CLI fixtures; reuse delivered core API instead of changing it. Include case aliases and source collisions in both directions; scope tests to this command.

Reason: Derived bounded CLI work required to complete AP06 using the delivered core; host substantive choices are separately reviewed.

Tests: T7

## Verification

### T1

Observable: Output exactly matches core private/package/task_draft/brief for a complete synthetic input; input bytes remain unchanged.

Method: Frozen host subprocess test compares actual CLI output files with core API.

### T2

Observable: Repeated output path returns exit2 without changing any existing byte; fresh directory/files have required modes.

Method: Host endpoint tests inspect modes and before/after bytes.

### T3

Observable: Equal/ancestor/descendant source and input collisions, symlink alias, absent parent all fail with no new source/output; separate output with missing selected source works.

Method: Isolated fixtures only; test negative paths and verify source remains missing. No original mutations.

### T4

Observable: Missing source creates gaps and stays draft; malformed/duplicate/NaN inputs create no bundle and report generic error without fixture secrets.

Method: Frozen host and candidate CLI tests exercise these cases.

### T5

Observable: Audited actual CLI invocation succeeds while process/network/ctypes execution are forbidden; active core hashes unchanged.

Method: Native host endpoint invocation with audit hook, exact core hash comparison, Runtime file grants and separate code review.

### T6

Observable: Fresh reader can reproduce legitimate and negative examples without private sources; no private or fictitiously accessible worker dependencies.

Method: Run documented synthetic example and independent method/content review.

### T7

Observable: Endpoint suite passes and demonstrates required behaviors against actual command.

Method: python3 -B -m unittest discover -s tools -p test_bered_uppdrag.py plus frozen host acceptance and independent Runtime review.

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
- The preparation result is always a draft, never substantive approval, permission or evidence of complete source discovery.
- Sources and lookup observations are host-supplied; timestamps describe the supplied comparison only.
- Agent judgment selects requirements, authority scope, adequate observables and export content; no measured time saving is claimed.
- This exported brief is self-contained together with files on the accepted base. No private references must be fetched.
