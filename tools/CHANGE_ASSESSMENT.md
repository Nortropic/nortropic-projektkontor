# AP05: decision-bound change assessment

This tool retains an authored assessment and marks which claims and actions need
reassessment after comparing selected, explicitly bound sources. It does not
decide truth, revoke decisions, grant permission, discover sources or claim an
exhaustive search. Runtime owns candidate startup, verification, separate review
and publication of synthetic office code. The host alone reads real private case
sources, preserves actual assessments and supervises the read-only verifier using
existing authorized access, outside the Runtime candidate sandbox and engine.

## APIs and CLI

`reference_manifest(case)` validates the **whole** case and returns
`{"version": 1, "files": [{"path": ..., "sha256": ..., "size": ...}]}` sorted by
path. `assess(case, check)` validates both inputs and returns the assessment.
Both functions raise `ValueError` on invalid input, leave inputs unchanged and
return independent JSON-serializable data. Import and API calls do not read files,
access the network, launch processes, hash sources or print. Dependencies are
Python standard library only.

From the office repository root, using an existing Python interpreter:

```sh
python3 -B tools/change_assessment.py manifest CASE.json
python3 -B tools/change_assessment.py report CASE.json CHECK.json
python3 -B -m unittest discover -s tools -p test_change_assessment.py -v
```

The CLI only reads the named JSON inputs and prints one JSON object to stdout.
It never writes files. Exit 0 means valid input, including observations of changed,
missing or unsafe files and incomplete observations. Exit 2 means invalid input,
unreadable input or invalid command; stdout then contains a nonempty `error`.
Duplicate keys at any JSON object depth and non-JSON constants are rejected.
There is no overall approved, authorized or go flag. Shell redirections in an
operator workflow are host writes, not actions performed by this CLI.

## Exact data contract

No specified object accepts extra or missing keys. All named textual fields are
nonempty strings (whitespace-only values are rejected). Text is preserved verbatim.
The schema is exactly integer 1, never a boolean or float.

| Object | Fields and constraints |
| --- | --- |
| Case | `schema`, `id`, `created_at`, nonempty `sources`, `claims`, `actions`, and `next_action` referencing an action id |
| Source | `id`, `title`, `version`, unique `path`, `sha256`, `size` |
| Claim | `id`, `kind` (`fact`, `judgment`, `decision`), `text`, `reason`, `standing`, nonempty `sources` referencing source ids |
| Action | `id`, `text`, `reason`, nonempty `claims` referencing claim ids, `authority` |
| Authority | `status` (`granted`, `not_granted`, `not_established`), `scope`, `sources` referencing source ids; `granted` requires at least one reference |
| Check | `checked_at`, `manifest`, `result` |
| Manifest | Integer `version: 1`, `files` with exactly `path`, `sha256`, `size` per entry; must equal the reference manifest, including order |
| Result | Boolean `ok`, `files` with exactly `path`, `status` per entry |

Ids are unique within each kind, and reference lists contain no duplicates or
unknown ids. Source title/version are supplied labels, not proof. Source paths are
safe POSIX relative paths: no absolute paths, drive prefixes, backslashes, NUL,
empty components, `.` or `..`. Hashes are exactly 64 lowercase hexadecimal
characters. Sizes are nonnegative integers, excluding booleans.

Timestamps use timezone-aware ISO8601 calendar date/time, for example
`2026-01-02T09:00:00Z`, `20260102T090000Z` or `2026-01-02T10:00:00+0100`.
Basic and extended calendar/time forms, compact and hour-only offsets, and fractions
of the smallest supplied time unit are supported in both timestamp fields and
retained verbatim. For example, `09.5Z` means 09:30 UTC and `09:30.5Z` means
09:30:30 UTC. Comparisons use exact integer arithmetic, including fractional
seconds beyond microsecond precision, without float rounding.
Invalid calendar dates, missing timezones and malformed offsets
are rejected. The comparison instant cannot precede creation, after accounting
for timezone offsets. Neither timestamp proves freshness at any other time.

Result paths must be unique and occur in the reference manifest. Result statuses
are exactly `ok`, `changed`, `missing`, `unsafe`. `result.ok` must equal “all
reported entries are ok”; for an empty list it is true. Omitted sources become
`not_checked`, including when `ok` is true. They are never silently treated as
unchanged. A mismatched manifest or contradictory flag is invalid input.

## Reading a report

The report contains `schema`, `case_id`, both timestamps, `structure_valid: true`,
`source_checks`, `coverage`, `facts`, `judgments`, `decisions`, `actions`, the fully
annotated `next_action`, and explicit `limitations`. Source checks and coverage
lists follow case source order. Claims are grouped by kind while preserving
their input order, and actions remain in input order.

Each claim/action retains **all** original fields and adds `source_check` and
`affected_sources`. A dependency whose status is anything except `ok` produces
`needs_reassessment`; otherwise the annotation is `unchanged`. Claim affected
sources follow their authored reference order. Action dependencies combine all
their claims' sources with their own authority sources, deduplicated and ordered
by the case source list. A change affecting only an authority source can therefore
flag an action while leaving its claims unchanged.

Structural validity/source integrity is neither substantive approval nor
authority. Unchanged selected sources do not establish exhaustive or necessarily
current knowledge; `coverage.complete_search` is always false. Changed, missing,
unsafe or not_checked sources require reassessment, not automatic falsehood or
revocation. The observation, authority and standing are supplied judgments, not
independently authenticated facts. Authored authority status and standing are
never rewritten, even when their bases change or all sources match. Timestamps
describe only this comparison.

Rerunning a case preserves its expected versions and hashes. Do not replace them
with whatever happens to exist now. Revise an assessment explicitly as a **new
file**, retaining its predecessor and recording the relationship in the host's
separate case records (the exact case schema has no predecessor field).

## Synthetic example

The fixture factory `synthetic_case()` in `test_change_assessment.py` contains an
entire valid case. Its labels, statements, paths and repeated-digit hashes are
invented. Those hashes are not measurements of real files. The synthetic check
factory builds observations without opening source paths or claiming verification.

In that case `build` depends on `design` and `budget` through claims, and on
`permission` through authority. `inspect` depends only on `budget`:

| Explicit observation | Claims | Actions |
| --- | --- | --- |
| All selected sources `ok` | All unchanged | Both unchanged; inspect authority remains `not_established` |
| Only design `changed` | Design-dependent claims need reassessment | Build needs reassessment; inspect unchanged |
| Only permission `changed` | All unchanged | Build needs reassessment; its authored `granted` status is retained |
| Budget omitted | Budget-dependent claims need reassessment | Both need reassessment; budget is `not_checked` |

## Host recipe: existing Runtime verifier, unchanged bindings

This recipe is **host operator work outside the module, Runtime candidate sandbox
and engine**, using existing authorized access. It is not an additional service,
source fetcher or hasher. The host keeps selected source **files** read-only and
preserves the original case. The host chooses an authorized private output
directory, newly created for each comparison, and never overwrites a selected
file. A broad common source root may span campaign and office sources; output
may be a new directory inside the office beneath that root. An ancestor root
does not grant write rights or make all its descendants a no-write area.

The candidate repository does not contain Runtime's `tools/evidence_index.py`.
The installed CLI is exactly `python -B path/to/evidence_index.py verify ROOT`,
reading the JSON manifest on **stdin**, with its JSON result on stdout. The host
supplies that existing verifier's file path as `AP05_VERIFIER`; the wrapper uses
the running Python interpreter without a shell. The manifest is never a positional
argument. Expected hashes come from the retained case, not a generation command.
No new executable or dependency is required.

Host inputs (all values refer to host-local resources, no private paths are
included in this document):

- `AP05_CASE`: the retained case JSON file.
- `AP05_SOURCE_ROOT`: the common root for selected files, read only by the verifier.
- `AP05_OUTPUT`: a fresh, private directory where the host is authorized to write.
- `AP05_VERIFIER`: file path to the installed Runtime `tools/evidence_index.py`.

Run from the office repository root using the existing Python. This emits the
manifest through the public API, runs the existing verifier, retains its result,
wraps the **unchanged** manifest and observation with `checked_at`, then creates
the report. Files use exclusive creation; predecessors are not overwritten.

```python
import datetime
import json
import os
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, "tools")
from change_assessment import assess, reference_manifest

def unique_object(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("Duplicate JSON key")
        value[key] = item
    return value

def invalid_constant(value):
    raise ValueError("Non-JSON constant")

def decode(text):
    return json.loads(text, object_pairs_hook=unique_object,
                      parse_constant=invalid_constant)

def save_new(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=True, allow_nan=False, indent=2)
        stream.write("\n")

case_path = Path(os.environ["AP05_CASE"]).resolve(strict=True)
source_root = Path(os.environ["AP05_SOURCE_ROOT"]).resolve(strict=True)
output = Path(os.environ["AP05_OUTPUT"]).resolve()
if not source_root.is_dir():
    raise ValueError("Use a source directory")
case = decode(case_path.read_text(encoding="utf-8"))
manifest = reference_manifest(case)
# Protect even absent selected paths from being created as output artifacts.
# The host chooses this private location; this check grants no write authority.
protected = [case_path] + [(source_root / entry["path"]).resolve()
                           for entry in manifest["files"]]
if any(path == output or output in path.parents or path in output.parents
       for path in protected):
    raise ValueError("Output must not overlap the case or any selected source file")
verifier = os.environ["AP05_VERIFIER"]
if not verifier.strip():
    raise ValueError("Supply the installed verifier file path")
output.mkdir(parents=True, exist_ok=False)
manifest_path = output / "manifest.json"
save_new(manifest_path, manifest)
argv = [sys.executable, "-B", verifier, "verify", str(source_root)]
try:
    completed = subprocess.run(argv, input=json.dumps(manifest),
                               capture_output=True, text=True, check=False)
except OSError:
    save_new(output / "unavailable.json", {"measurement": "unavailable",
                                          "reason": "Verifier could not run"})
    raise SystemExit("Unavailable measurement; no check or report created")

# Preserve the existing tool's result locally, including mismatches/errors.
# These raw outputs may be sensitive and must never be published as-is.
save_new(output / "verifier-observation.json", {
    "exit_code": completed.returncode,
    "stdout": completed.stdout, "stderr": completed.stderr,
})
if completed.returncode not in (0, 1):
    save_new(output / "unavailable.json", {"measurement": "unavailable",
                                          "reason": "Verifier error", "exit_code": completed.returncode})
    raise SystemExit("Unavailable measurement; no check or report created")
try:
    result = decode(completed.stdout)
    if not isinstance(result, dict) or type(result.get("ok")) is not bool:
        raise ValueError("Missing boolean verifier outcome")
    if result["ok"] != (completed.returncode == 0):
        raise ValueError("Verifier exit status contradicts its result")
    if decode(manifest_path.read_text(encoding="utf-8")) != manifest:
        raise ValueError("Expected manifest was altered")
    if decode(case_path.read_text(encoding="utf-8")) != case:
        raise ValueError("Retained case was altered")
    check = {
        "checked_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "manifest": manifest,
        "result": result,
    }
    report = assess(case, check)
except (ValueError, OSError):
    save_new(output / "unavailable.json", {"measurement": "unavailable",
                                          "reason": "Invalid observation or changed input"})
    raise SystemExit("Unavailable measurement; no check or report created")
save_new(output / "check.json", check)
save_new(output / "report.json", report)
```

The host supervises this one read-only verifier process using existing authorized access;
on a hang, interrupt it and preserve diagnosis rather than blindly retrying. A
partial output directory is not proof that a measurement completed.

Verifier **exit 1 is valid mismatch data**: retain it and report reassessment.
Verifier exit 2, launch failure, invalid JSON or invalid result is an **unavailable
measurement**. Never turn those failures into `ok: true`, an empty successful
result, or fabricated per-source statuses. An explicitly supplied, valid empty
result remains a different situation: it reports all sources `not_checked`.
The wrapper cannot authenticate its author or the verifier and does not establish
substantive approval. The host must use the actual installed tool; this candidate
was tested only with synthetic fixtures and does not claim a real verification run.

Case bindings, source paths, observations and report prose can be sensitive.
Keep actual cases, manifests, observations and reports local. Publish only a
**separately content-reviewed, redacted report**, never a raw dump. Review must
exclude private source text, private local paths, credentials, raw logs and
inferred private information. The host preserves actual case assessments separately.
Runtime builds, tests, separately reviews and publishes only synthetic office code;
this method grants no new rights or Runtime access to internal sources.
