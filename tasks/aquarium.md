# Aquarium v0: read the office and Runtime, project them display-safe

Build only `tools/aquarium.py`, `tools/test_aquarium.py` and `tools/AQUARIUM.md`. Existing Runtime builds, tests,
reviews and integrates this product. Do not modify any other file, active execution, host acceptance or publication
authority. Standard library only (Python 3.11+). No new services, model calls, scheduler, database or state engine.

Aquarium is a calm read view of what the office has delivered, what is actually in progress or waiting, and what needs
the owner. Runtime and the office keep their own sources of truth; Aquarium only reads them and projects a
display-safe summary. It starts, approves, switches and changes nothing. This task builds the reading and the
projection; a later task renders it.

## 1. `project(readings, now) -> dict` (pure)

No file, clock, process or network access; `now` is an aware `datetime`; the input is never mutated. Raises
`ValueError` (without private values in the message) for invalid input. Input `readings` (all keys required):

```
{"schema": 1, "provdata": true|false, "read_started_at": "aware ISO8601",
 "sources": {"release": S, "staffing": S, "questions": S, "service": S, "engine": S, "watch": S, "office": S}}
S = {"status": "ok"|"unavailable", "read_at": "aware ISO8601"|null, "value": {...}|null}
```

`value` per source when `status` is `ok` (extra keys are ignored, never copied):

- `release`: `{"config_sha256": 64 hex, "runtime_revision": 40 hex, "office_revision": 40 hex}`
- `staffing`: `{"executors": {role: "claude"|"codex"}, "models_run": {"claude": name, "codex": name}, "watch_model": name}`
- `questions`: `{"items": [{"asked_at": iso, "executor": str, "model": str, "still_selected": bool}]}` (Runtime's newest D030
  questions; an unreadable question record makes the whole source unavailable, it is never skipped)
- `service`: `{"parts": {"daemon": {"identity_matches": bool}, "engine": {...}, "worker": {...}}}`
- `engine`: `{"executions": [{"type": str, "pending_activities": [activity type names], "pending_workflow_task": bool, "start": iso|null}]}`
- `watch`: `{"native": {"paused": bool, "note": str, "next_action_times": [iso], "running": [..], "recent": [{"started_at": str}]},
  "latest": {"reported_at": iso, "reviewed": bool, "decision": str}|null,
  "reviewed": {"reviewed_at": iso, "decision": str}|null, "refused_for_capacity": true|false|null,
  "owner_question": str|null}`
- `office`: `{"main": 40 hex, "main_date": iso, "entries": [{"id": str, "title": str, "text": str}],
  "notes": [{"ap": "AP04", "title": str, "text": str}], "plan_owner_turn": [{"kind": "beslut"|"operatörshandling", "text": str, "since": str|null}]}`

Output, exactly these keys (the renderer's contract):

```
{"schema": 1, "provdata": bool, "read_at": iso (read_started_at),
 "sources": {id: {"title": str, "status": "ok"|"otillgänglig", "read_at": iso|null, "stale_after_seconds": int}},
 "revisions": {"office_main": 8 hex|null, "office_main_date": iso|null, "runtime": 8 hex|null, "config": 8 hex|null},
 "headline": {"pagar": int|null, "vantar": int|null, "behover_dig": int|null, "lugnt": bool},
 "arkivet": {"status": "ok"|"otillgänglig", "items": [{"key": "AP10", "title": str, "date": "YYYY-MM-DD"|null, "basis": str}]},
 "verkstaden": {"status": ..., "items": [{"state": "pågår"|"granskas", "what": str, "since": iso|null}], "model_evidence": false},
 "utkiken": {"status": ..., "schedule": "aktiverat"|"pausat"|"stoppat"|"okänt", "next_planned": iso|null,
             "running": int, "starts": [iso], "latest": {"at": iso|null, "outcome": str, "cause": str|null}|null,
             "reviewed": {"at": iso, "decision": str, "older_than_a_day": bool}|null, "waiting": bool,
             "model": {"executor": "codex", "model": str|null, "follows_model_choice": false}},
 "agarens_bord": {"status": ..., "items": [{"kind": "beslut"|"operatörshandling"|"modellfråga", "text": str, "since": str|null, "basis": str}]},
 "sockeln": {"service": {"state": "igång"|"delvis"|"okänt", "verified": int, "of": 3, "config": str|null},
             "staffing": [{"role": str, "executor": str, "model": str}], "watch_staffing": {"executor": "codex", "model": str|null},
             "idle_tasks": int, "identity_records": int, "busy": int}}
```

Rules, each one tested:

1. Sources: titles `release` "Runtime · aktiv release", `staffing` "Runtime · bemanning", `questions` "Runtime · modellfrågor",
   `service` "Runtime · tjänsten", `engine` "Runtime · motorn", `watch` "Runtime · bevakningen", `office` "Kontoret · beslut och
   leveranser". `stale_after_seconds` is 300 for every Runtime source and 3600 for `office`. A source that is not `ok` is
   `otillgänglig`, and no value is taken from it: Arkivet depends on `office`; Verkstaden on `engine`; Utkiken on `watch`;
   Ägarens bord on `office`, `questions` and `watch`. A place whose source is unavailable has `status` `otillgänglig`;
   Arkivet and Verkstaden then have empty items; Utkiken then has `schedule` `okänt`, `next_planned` null, `running` null,
   `starts` [], `latest` null, `reviewed` null and `waiting` false; Ägarens bord keeps the items from its available sources
   and is `otillgänglig` when any of its sources is. The watch's model alone comes from `staffing`: an unavailable
   `staffing` leaves Utkiken `ok` with `model.model` null. In Sockeln a field from an unavailable source is `okänt`
   (service state) or null (`config`, `verified`, counts, `watch_staffing.model`), and `staffing` is []. `revisions` takes
   the first 8 characters of `office.main` and `office.main_date` as given, and the first 8 characters of
   `release.runtime_revision` and `release.config_sha256`; each is null when its source is unavailable. Numbers from an
   unavailable source are never presented as zero work, and `lugnt` is then false. One unavailable source never makes
   another source unavailable.
2. Arkivet: one item per delivered or closed commitment. An entry is a delivery when its id ends with `-LEVERANS`,
   contains `-LEVERANS-` or contains `-AVSLUT`; its `key` is the part of the id before that marker (so `AP10-LEVERANS` is
   `AP10`, `AP10-SIGNALRATTNING-LEVERANS-20260924` is `AP10-SIGNALRATTNING` and `AP11-AVSLUT-20260924` is `AP11`); a
   note's `key` is its `ap`. A note (`evidence/APnn/leverans.md`) counts only when no delivery entry has the same key. `title` is the
   entry title or the note's title, `date` the first `YYYY-MM-DD` or eight-digit `YYYYMMDD` in the id, else in the text,
   else null. `basis` is `beslutsloggen <id>` or `leveransbesked <APnn>`. Order: newest date first, undated last.
   Nothing is invented; the count equals the number of such entries and notes.
3. Verkstaden: an engine execution of type `ServiceIdentity` is never work. An execution with at least one pending
   activity, or with `pending_workflow_task` true, is `pågår`, or `granskas` when any pending activity name contains
   `review`; `what` is exactly `<type> · <activity names joined by ", ">`, or `<type> · arbetsflödessteg` when only a
   workflow task is pending (the ordinary state of a running execution between two activities), and `since` is the
   execution's `start`. An execution with neither is idle and is not an item. `model_evidence` is always false in v0: a
   pending activity or a running execution is never presented as a model working.
4. Utkiken: `schedule` is `stoppat` when `note` is a string starting with `STOPPED`, else `pausat` when `paused` is true,
   `aktiverat` when `paused` is false, and `okänt` otherwise (the watch view's own rule). `next_planned` is the earliest
   next action time later than `now`, else null (a plan, never a performed round). `starts` are the recent actions' start
   times, newest first, at most three. `latest` comes from the latest report: `outcome` is `genomförd, granskad` when
   reviewed, else `genomförd, otillräcklig`; `cause` is `leverantören tog inte emot analysen (kapacitet)` only when
   `refused_for_capacity` is true, and null when it is false or null. `reviewed` keeps its own `reviewed_at` and a Swedish
   decision (`retain` → `behåll`, `not_applicable` → `inte tillämpligt`, `insufficient` → `otillräcklig`,
   `propose_action` → `förslag till åtgärd`, other → the word unchanged); `older_than_a_day` compares `reviewed_at` with
   `now`. A fresh reading never makes an old reviewed decision current. `waiting` is true when the latest report is not
   reviewed. The watch's model is `watch_model` with `follows_model_choice` false; no model question is ever created for
   the watch.
5. Ägarens bord: (a) each office entry whose id contains `-BEREDNING` and whose text contains the word `förslag`
   (any case) within its first 600 characters, unless a later entry id starts with the same prefix followed by `-ACCEPT`
   (the prefix is the id up to `-BEREDNING`), is a `beslut` with `text` `Ta ställning till <title>`, `since` the entry's
   date as in Arkivet and `basis` `beslutsloggen <id>`; (b) each `plan_owner_turn` item as given, with `basis` `planens
   ägartur`; (c) one `modellfråga` per distinct executor and model among the D030 questions with `still_selected` true,
   with `text` `Vald modell <model> för <executor> tog inte emot anrop: vänta eller byt modell`, `since` the newest
   `asked_at` of that pair and `basis` `Runtimes modellfråga`; (d) a watch `owner_question` is a `beslut` with that text,
   `since` the latest report's `reported_at` (null without one) and `basis` `bevakningens förslag`. Nothing else becomes an
   owner item.
6. Sockeln: service `igång` when all three parts' identities match, `delvis` when one or two do, `okänt` when none does
   (then `verified` is 0) or the source is unavailable (then `verified` is null); `verified` counts matches; `config` is
   the first 8 characters of `config_sha256`. `staffing` lists each role with its executor and that executor's
   `models_run` model, sorted by role. `idle_tasks` counts non-identity executions without pending work,
   `identity_records` the `ServiceIdentity` executions, `busy` the rest.
7. Headline: `pagar` is the number of Verkstaden items, `vantar` is 1 when Utkiken is `waiting` plus the number of
   `modellfråga` items, `behover_dig` the number of owner items. Each is null when a source it depends on
   is unavailable (`pagar`: `engine`; `vantar`: `watch`, `questions`; `behover_dig`: `office`, `questions`, `watch`), so an
   unknown count is never shown as zero. `lugnt` is true only when all three are 0 and every source is `ok`.
8. Display safety: the output never contains a path (`/Users/`, `/private/`, `/home/`, `.runtime`, `evidence/`
   followed by `local`), a run or thread identifier (a UUID-like value), provider text, an e-mail address or any input
   key not listed above. Office texts are reduced to titles and dates; they are never copied whole.

## 2. `collect(runtime_root, office_root, runtime_probe=None, watch_reader=None, office_reader=None) -> readings`

Real reading, bounded and read-only; each part is a replaceable reader so tests use synthetic ones. A reader that raises
or returns malformed data makes only its own source(s) `unavailable`, with `read_at` still set and no private text kept.
`provdata` is false. `read_started_at` and each `read_at` are aware UTC ISO times taken from the clock.

Import the existing `bevakningsbild` only inside the default `watch_reader`, so importing `aquarium` has no side
effects.

- `runtime_probe(runtime_root)` default: read `runtime_root/.runtime/ap10/active.json` (regular file, no symlink), take the
  release directory from its `config`, and run `runtime_root/.runtime/temporal-venv/bin/python -B -c PROBE` with cwd the
  release's `runtime` directory, `shell=False`, a 30 s timeout, captured text, and an environment of only PATH, HOME,
  USER, LOGNAME, LANG, TMPDIR plus `PYTHONDONTWRITEBYTECODE=1`, `NR_HOST_ROOT=<runtime_root>`, `NR_CONFIG_SHA256=<the
  pointer's sha256>` and `LC_ALL=C`. `PROBE` is the constant in section 4, used exactly. Its JSON output has one key per
  Runtime source (`release`, `staffing`, `questions`, `service`, `engine`, `refusal`), each `{"ok": true, "value": ...}` or
  `{"ok": false}`.
- `watch_reader(runtime_root)` default: `bevakningsbild.collect(runtime_root)` from the existing office tool. It does not
  raise: the watch is `unavailable` when its `native` is the explicit unavailable observation (`unavailable` is true) or
  `latest` is a wrapper whose `integrity` is not `available`. Otherwise take `native`; from `latest` and `reviewed` (each
  `None` or a wrapper holding a `report`) keep only the report fields `reported_at`, `reviewed`, `reviewed_at`, `decision`;
  `owner_question` is the `question` of `bevakningsbild.view(native, latest, reviewed, <read time>)` when its
  `owner_decision.needed` is `yes`, else null. `refused_for_capacity` is the probe's `refusal` `capacity` when that part is
  ok, else null.
- `office_reader(office_root)` default: read with `git -C office_root show refs/remotes/origin/main:<path>` only (never the
  working tree): `docs/decisions.md` split into entries at lines starting `## ` (id before ` — `, title after it, text up
  to the next entry), `evidence/APnn/leverans.md` for the paths `git ls-tree` lists (title = first `# ` line), and the
  plan's `ÄGARENS TUR` block: lines starting `- [beslut] ` or `- [operatörshandling] ` that directly follow a line
  `ÄGARENS TUR` in `docs/plan.md` (optional `— sedan YYYY-MM-DD` at the end sets `since`). `main` and `main_date` come
  from `git rev-parse` and `git log -1 --format=%cI` on the same ref.

## 3. Command

```
python3 -B tools/aquarium.py NEW_DIR
```

Collect with `office_root` = the repository that holds `tools/` and `runtime_root` = its sibling directory `Nortropic
Runtime` (as `tools/bevakningsbild.py` does), project with the clock's `now`, and write `NEW_DIR/projection.json` as UTF-8
text exactly `json.dumps(projection, ensure_ascii=False, indent=1, sort_keys=True)` followed by one newline. Unavailable
sources are not a failure: the projection then says so. `NEW_DIR` must not exist; its parent
must exist and not be a symlink; create it with mode 0700 and the file with mode 0600 through an exclusive, no-follow
open. Exit 0 on success without printing; on any failure exit 2 printing only `Kunde inte skapa Aquariums projektion.` to
stderr, with nothing private. The command never renders, serves, starts or changes anything.

## 4. `PROBE` (use exactly; it runs inside the active release with the release's own code)

```python
import asyncio, json
from pathlib import Path
out = {}
def part(name, fn):
    try:
        out[name] = {'ok': True, 'value': fn()}
    except Exception:
        out[name] = {'ok': False}
def release_part():
    from runtime.release import installed
    c = installed()
    return {'config_sha256': c['config_sha256'], 'runtime_revision': c['runtime_revision'], 'office_revision': c['office_revision']}
def staffing_part():
    from runtime.release import installed
    from runtime.development_model import executors, models
    from runtime import profile
    c = installed()
    return {'executors': executors(c), 'models_run': models(c), 'watch_model': getattr(profile, 'MODEL', None)}
def questions_part():
    from runtime.release import installed
    from runtime.development_model import models
    from runtime import model_question
    running = models(installed())
    found = model_question.recent()
    if any(q.get('unreadable') for q in found):
        raise ValueError('unreadable question record')
    return {'items': [{'asked_at': q.get('asked_at'), 'executor': q.get('executor'), 'model': q.get('model'),
                       'still_selected': q.get('model') is not None and running.get(q.get('executor')) == q.get('model')}
                      for q in found]}
def service_part():
    from runtime.release import ROOT
    from runtime.shared import process_identity
    s = json.loads((ROOT / '.runtime/ap10/service.json').read_text())
    return {'parts': {k: {'identity_matches': bool(s[k].get('identity')) and process_identity(s[k]['pid']) == s[k]['identity']}
                      for k in ('daemon', 'engine', 'worker')}}
def engine_part():
    from temporalio.client import Client
    async def run():
        client = await Client.connect('127.0.0.1:7339', namespace='nortropic-runtime')
        rows = []
        async for e in client.list_workflows('ExecutionStatus = "Running"'):
            raw = (await client.get_workflow_handle(e.id, run_id=e.run_id).describe()).raw_description
            rows.append({'type': e.workflow_type, 'pending_activities': [a.activity_type.name for a in raw.pending_activities],
                         'pending_workflow_task': raw.HasField('pending_workflow_task'),
                         'start': e.start_time.isoformat() if e.start_time else None})
        return {'executions': rows}
    return asyncio.run(run())
def refusal_part():
    from runtime.release import ROOT
    from runtime.development_model import capacity_lost
    rounds = [p for p in (ROOT / '.runtime/ap10/rounds').iterdir() if (p / 'report/result.json').is_file()]
    latest = max(rounds, key=lambda p: json.loads((p / 'report/result.json').read_text()).get('reported_at') or '')
    events = latest / 'analysis/events.jsonl'
    rows = [json.loads(l) for l in events.read_text().splitlines() if l.strip()] if events.is_file() else []
    return {'capacity': bool(capacity_lost('codex', rows))}
for name, fn in (('release', release_part), ('staffing', staffing_part), ('questions', questions_part),
                 ('service', service_part), ('engine', engine_part), ('refusal', refusal_part)):
    part(name, fn)
print(json.dumps(out))
```

## 5. Tests and documentation

`tools/test_aquarium.py` uses only synthetic data and temporary files under the repository's existing `.scratch`
(cleaned up); it never reads real sources, runs the probe, calls git on a real repository or uses the network. Cover
every rule above, including an unavailable source beside working ones, an old reviewed decision under a fresh reading,
identities that are technical records, idle and busy executions (also one with only a pending workflow task), a service
with no verified identity, proposals with and without a later accept, D030 questions, display safety with
private-looking input values, and the command's exclusive private output.
`tools/AQUARIUM.md` documents in Swedish what is read, how, what is never read or kept, the projection's meaning and
limits (a reading is not live, a scheduled round is not a performed one, no model evidence in v0), and the command.
