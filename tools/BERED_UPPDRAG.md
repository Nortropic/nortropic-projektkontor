# AP06: private assignment preparation command

From the office repository root:

```sh
python3 -B tools/bered_uppdrag.py CASE CHECK SPEC --source-root ROOT --output NEWDIR
```

The command reads three strict UTF-8 JSON files and calls the delivered
`assignment_preparation.prepare(case, check, spec)` once. The schemas and output
fields are defined in [ASSIGNMENT_PREPARATION.md](ASSIGNMENT_PREPARATION.md).
AP05 assessment is reused without new assessment logic. ROOT locates selected
case source paths for collision checks only: it is not scanned, hashed or measured.
Source contents are never opened. The command does not refresh expected hashes,
fetch references, generate or execute acceptance, invoke Runtime or models,
signal processes, or publish anything.

NEWDIR's parent must already exist. The command creates NEWDIR exclusively with
mode `0700` and these exclusive files with mode `0600`:

| File | Exact core value retained |
| --- | --- |
| `private.json` | `private`, including all inputs and traces |
| `package.json` | `package` |
| `task.draft.json` | `package.task_draft` |
| `brief.draft.md` | `package.brief`, as UTF-8 text |

JSON values are retained without new fields; JSON formatting is not input byte
preservation. Input file bytes remain unchanged. No predecessor is overwritten.
Any existing output is refused unchanged. A failed write leaves partial output
for diagnosis; that directory cannot be reused. Preserve it and choose a new
version only after diagnosing the failure. A partial directory is not a completed
bundle. Permissions restrict access but do not encrypt or prevent owner edits.

Before any mkdir, the command rejects output symlinks, symlink ancestors, missing
parents and equality/containment in either direction with any input or selected
source path, including missing sources. Comparisons use resolved paths and
casefolded path components to protect Mac aliases; lexical source names are also
protected when a source resolves through a symlink. Input JSON symlinks and
nonregular files are rejected. The source root itself is not a selected source:
an unrelated output beneath a broad root is permitted. These checks support
trusted local use, not hostile concurrent filesystem replacement.

Exit `0` emits one stdout JSON object with `status: "draft"`,
`mechanical_complete`, `gaps` and the four file names. Structurally valid but
incomplete inputs still produce a marked draft and exit `0`. The command relies
on supplied source observations: a missing file produces gaps when CHECK records
it as missing, not through a new filesystem measurement. Even a complete draft
is neither approved nor authorized. Stdout gap subjects contain authored public
IDs and must be treated as potential disclosure too.

Exit `2` emits exactly one generic JSON error on stdout, with no exception,
private text or input/output path echoed to stdout or stderr. This includes
malformed JSON, duplicate keys at any depth, NaN/Infinity, nonfinite parsed
numbers, invalid schema, unreadable inputs, invalid arguments and output failures.
`--help` displays static usage. There is no acceptance or execution mode.

## Reproducible synthetic example

The complete `fixture()` and `write_fixture()` in
[test_bered_uppdrag.py](test_bered_uppdrag.py) contain invented source metadata,
quotes, decisions, observations and Runtime bindings. Repeated-character hashes
are synthetic data, not measurements. No private source or host acceptance is
needed. Use an installed Python interpreter; the qualified environment uses
Python 3.12. Run these commands from the repository root, starting with an absent
`.scratch/bered-example-v1`:

```sh
mkdir -p .scratch
python3 -B - <<'PY'
import sys
from pathlib import Path
sys.path.insert(0, "tools")
from test_bered_uppdrag import write_fixture
write_fixture(Path(".scratch/bered-example-v1"))
PY
python3 -B tools/bered_uppdrag.py \
  .scratch/bered-example-v1/case.json \
  .scratch/bered-example-v1/check.json \
  .scratch/bered-example-v1/spec.json \
  --source-root .scratch/bered-example-v1/sources \
  --output .scratch/bered-example-v1/bundle-v1
```

Expect exit `0`, `status: "draft"`, `mechanical_complete: true`, empty gaps and
four files. The suite compares each file's content directly with the core API.
Repeat the exact CLI command to observe exit `2` and unchanged bundle bytes.

For a missing-source draft and a refused source collision, retain those inputs
and author a new synthetic version:

```sh
python3 -B - <<'PY'
import json
import sys
from pathlib import Path
sys.path.insert(0, "tools")
from test_bered_uppdrag import write_fixture
root = Path(".scratch/bered-missing-v1")
case, check, spec = write_fixture(root)
(root / "sources" / "selected.txt").unlink()  # Synthetic fixture only.
check["result"] = {"ok": False, "files": [{"path": "selected.txt", "status": "missing"}]}
with (root / "check-missing.json").open("x", encoding="utf-8") as stream:
    json.dump(check, stream)
PY
python3 -B tools/bered_uppdrag.py \
  .scratch/bered-missing-v1/case.json \
  .scratch/bered-missing-v1/check-missing.json \
  .scratch/bered-missing-v1/spec.json \
  --source-root .scratch/bered-missing-v1/sources \
  --output .scratch/bered-missing-v1/bundle-v1
python3 -B tools/bered_uppdrag.py \
  .scratch/bered-missing-v1/case.json \
  .scratch/bered-missing-v1/check-missing.json \
  .scratch/bered-missing-v1/spec.json \
  --source-root .scratch/bered-missing-v1/sources \
  --output .scratch/bered-missing-v1/sources/selected.txt
```

The first command exits `0` with reassessment gaps and mechanical completeness
false. The second exits `2` before mkdir; the selected source stays missing.
Other endpoint regressions cover case aliases, both containment directions,
symlinks, missing parents, unreadable inputs, duplicate keys, malformed JSON,
private error markers, exact modes under a restrictive umask, preserved partial
output, and absence of process/network/source-content access.

Runtime runs the candidate suite and its separate frozen acceptance:

```sh
python3 -B -m unittest discover -s tools -p test_bered_uppdrag.py -v
```

Tests allocate isolated temporary fixtures under `.scratch` and remove their own
temporary directories. Manual example versions are retained. Never use the test
fixture builder on real source material. Synthetic test success does not establish
real source observations, independent approval or protected integration.

## Host preparation and review

1. The authorized chain driver selects the actual case, action and source
   versions within AP06. Preserve previous cases and observations. Read the real
   later decisions and record their **actual decision IDs**, source versions and
   scoped effects in the private case/reference trace; do not manufacture IDs,
   substitute a draft label for acceptance, or treat old choices as new authority.
   AP06-ACCEPT is the accepted host mandate referred to by this task, not a record
   authenticated by the compiler. Historical I-11 and FINAL-CHECK-1 retain their
   own scope; they do not authorize a new map delivery. Private later decision
   records must be looked up by the host, never fetched by the worker candidate.
2. Follow [the AP05 measurement recipe](CHANGE_ASSESSMENT.md#host-recipe-existing-runtime-verifier-unchanged-bindings)
   outside the candidate sandbox. It uses the existing Runtime evidence_index
   verifier with the unchanged reference manifest on stdin and wraps the real
   result with `checked_at`. Exit `1` is mismatch data; exit `2`, launch failure
   or invalid output is unavailable measurement, never invented success. This
   CLI accepts the resulting CASE/CHECK; it does not perform that measurement.
3. Use the host's existing lookup/quote tools to check each selected reference.
   Record the actual lookup ID, selected source/version, expected SHA-256 and
   exact quote in SPEC; supply a bound `matched`, `mismatch` or `not_checked`
   observation. Do not assert `matched` because the text fields are nonempty.
   These remain host observations, not authenticated evidence from this tool.
4. Author requirements, reasons, claim/reference dependencies, tests and export
   context. Keep fact, judgment, decision and handlingsspecifik befogenhet
   (action-specific authority) distinct. The authorized chain driver and separate
   reviewer assess meaning, contradictions, mandate scope and verification
   adequacy. The earlier core-method phrase “human substantive review” creates
   no new owner gate: these authorized agents perform substantive review. Only
   genuine goal, cost or authority changes return to the owner.
5. Keep real inputs and bundles in an authorized, ignored `evidence/**/local/`
   location. Ensure the existing parent is private and confirm Git ignores the
   chosen path before writing. An arbitrary `--output` path is not automatically
   private; `.scratch` is for synthetic isolated tests, not real evidence.
   Use a new directory for every version and retain predecessor relationships in
   host records. Changes trigger scoped reassessment, not automatic reversal of
   decisions or authority. Unchanged selected sources prove neither exhaustive
   discovery of later sources nor freshness beyond the supplied comparison.
6. Review every export field before moving anything into publication or a worker
   task: requirement/test IDs, prose, reasons, methods, gaps, task values, prompts,
   paths and limitations. Package field selection is not sanitization. Summaries
   can disclose private information. Never export `private.json`, raw private
   inputs, source collections or raw sessions. Review the code, method and test
   summaries as well. No string filter proves publication safety.

## From reviewed draft to Runtime

The CLI leaves a draft only. The host supplies the actual task bindings; it does
not ask this command to invent a task, acceptance module, digest or permission.
The actual office Runtime format uses exactly the following supplied fields:

| Field | Host binding |
| --- | --- |
| `id`, `target` | Actual task ID and `Nortropic/nortropic-projektkontor` |
| `base`, `runtime_revision` | Actual full 40-character revisions |
| `allowed_paths` | Explicit permitted `tools/` files |
| `attempt_seconds`, `automatic_retries` | Accepted per-attempt seconds and zero automatic retries |
| `steps` | Objects with the explicit accepted `provider` (`codex` or `claude`) and the reviewed `prompt` |
| `review_provider` | Optional explicit reviewer executor (`codex` or `claude`); absent means Codex |
| `acceptance`, `acceptance_sha256` | Host-controlled `acceptance/` module and its actual 64-character digest |
| `brief` | Reviewed brief under `tasks/` |

See the existing [method task](../tasks/andringsbedomning-metod.json) for a real
format example, not an instruction to restart that completed task. Synthetic
fixture revisions and hashes must never be used as actual host bindings.

The host uses Runtime's actual validator, obtains independent review and freezes
the reviewed task/brief/acceptance bytes in committed inputs through the existing
route. Frozen acceptance and the active execution path stay outside candidate
write access. After that host review/freezing, the office interface is
`python3 -B tools/kontor.py start --task NAME.json`, where NAME.json is the actual
accepted file directly under `tasks/`. It hands execution to the existing
`runtime.run` route. This is a host endpoint description, not a step performed
by preparation or by the synthetic example. No synthetic task should be started.

Runtime owns tests, independent review and protected integration of the exact
candidate, and the host retains their real evidence. Preparation does not assert
those gates passed and grants no source access, host authority or publication
rights. No Runtime, core, acceptance, host task or source changes belong to this
three-file CLI implementation.
