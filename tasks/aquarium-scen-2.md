# Aquarium v0: the work world — observed work and task names in the projection, and the renderer

Change `tools/aquarium.py` and `tools/test_aquarium.py` as sections 1 and 2 state, complete `tools/aquarium_vy.py` and
write `tools/test_aquarium_vy.py` as sections 3 to 5 state, and update `tools/AQUARIUM.md` as section 6 states. Existing
Runtime builds and tests this product; its review and integration follow the office's working form. Do not modify any
other file, active execution, host acceptance or publication authority. Standard library only (Python 3.11+). No new
services, model calls, scheduler, database, server or network access.

`tools/aquarium.py` (on main) reads the office and Runtime and writes a display-safe `projection.json`; its current
contract is schema 1. The owner approved a spatial work world for the view: persistent places, recognisable executors
at understandable workplaces, visible work objects and a clear difference between work, review, waiting, delivery and
owner needs. This task gives the projection what the view needs and the existing sources actually evidence, and adds the
renderer. Truth governs everything below: a figure appears only for work the engine reading evidences; configured
staffing is never shown as observed work; an identity the source does not evidence is shown as not evidenced; a source
that cannot be read is shown as unknown, never as empty.

## 1. The date rule in `tools/aquarium.py`

The first real reading showed three delivery notes dated `3510-18-24`, `0778-27-74` and `0151-71-43`: the current rule takes
the first eight-digit run, and those runs sat inside git commit hashes. Change how a date is found; it is the same rule for
the Arkivet `date` and the Ägarens bord `since` of an open proposal. A date is a real calendar date from 2000-01-01 to
2099-12-31, written either `YYYY-MM-DD` not directly preceded or followed by a digit, or as eight digits `YYYYMMDD` not
directly preceded or followed by a letter or a digit, so a digit run inside a commit hash, digest or other token is never a
date. A candidate that is not such a date (for example `2026-13-45`, `20260231`, `1999-01-01` or `2100-01-01`) is skipped
and the search goes on. The first valid date in the id is used, else the first in the text, else null.

## 2. Schema 2 in `tools/aquarium.py`

Everything of the current contract stays as it is unless this section changes it: the readers, the display safety, the
places Arkivet, Utkiken and Ägarens bord, the revisions, the command and its output form.

**Constants.** `SCHEMA = 2`. There are eight sources, in this order: `release`, `staffing`, `questions`, `service`,
`engine`, `tasks`, `watch`, `office`; the new `tasks` source has the title `Runtime · uppdragsfiler` and, like the other
Runtime sources, `stale_after_seconds` 300. A reading (the input of `project`) must carry all eight sources.

**The probe.** `PROBE` changes in exactly one place: each row that `engine_part` appends begins with the execution's
workflow id, so the line reads
`            rows.append({'id': e.id, 'type': e.workflow_type, 'pending_activities': [a.activity_type.name for a in raw.pending_activities],`
and every other character of `PROBE` stays as it is. (Runtime starts each task's workflow with the task id as its
workflow id, so this is the task's name as the engine reading holds it.)

**Input shapes.** An engine execution carries `id`, a string, beside its current keys. The `tasks` source value is
`{"items": [{"id": <string>, "title": <string or null>, "status": "läst" | "saknas" | "oläslig"}, ...]}`, where `title`
is a string exactly when `status` is `läst`; any other shape makes the value invalid, exactly as for the other sources.

**Work and parked tasks** (inside `project`, pure). An execution of type `ServiceIdentity` (a technical identity
record) or `PrivateAssessment` (the watch's own round, which Utkiken shows from the watch reading) is neither work nor a
parked task. Every other execution with at least one pending activity or a pending workflow task is a work item; every
other execution with neither is a parked task. Engine order is kept in both lists. For both, `short` is the execution id
without a leading `office-` when the id is longer than `office-`, else the id itself. A work item's step, state and
executor come from its pending activity names only, never from configuration, by the first rule that applies:
1. a name containing `review` (in any letter case): step `granskning`, state `granskas`, executor null;
2. a name `execute_claude` or `execute_codex`: step `utförande`, state `pågår`, and executor `claude` or `codex` when
   exactly one of these two executors is named among the pending names, else null;
3. a name `publish_candidate`: step `integration`, state `integreras`, executor null;
4. any other pending name: step `steg`, state `pågår`, executor null;
5. no pending name (only a pending workflow task): step `arbetsflödessteg`, state `pågår`, executor null.

`executor_basis` is `motorns steg execute_claude` or `motorns steg execute_codex` when the executor is set (after the
activity name that evidences it), else null. A work item has exactly the keys `task` (the id), `short`, `type`, `since`
(the execution's `start` as given), `step`, `state`, `executor`, `executor_basis` and `activities` (the pending names as
given, in order). A parked task has exactly the keys `task`, `short`, `type`, `since`, `title` and `title_status`: when
the `tasks` source is unavailable, `title` is null and `title_status` is `okänd`; when it is available, the first item of
its value with the same `id` gives `title` and `title_status` (its `status`), and with no such item `title` is null and
`title_status` is `oläslig`.

**Places.** `verkstaden` becomes exactly `{"status": ..., "items": [work items], "parked": [parked tasks], "titles":
...}`: `status` is `ok` when the engine source was read, else `otillgänglig` (and then both lists are empty); `titles` is
`ok` when the `tasks` source was read, else `otillgänglig`. There is no `model_evidence` key any more. In `sockeln`,
`busy` is the number of work items, `idle_tasks` the number of parked tasks and `identity_records` the number of
`ServiceIdentity` executions (all three null when the engine source is unavailable); the rest of `sockeln` is unchanged.
`headline.pagar` is the number of work items (null when the engine source is unavailable), and `lugnt` requires, as
today, every source to be read, now all eight. `sources` has the eight entries, each with `title`, `status`, `read_at`
and `stale_after_seconds`.

**Reading the task files.** Add the default reader `task_reader(runtime_root, identities)` and a keyword argument
`task_reader=None` to `collect` (the default reader is used when it is None, as for the other readers). `collect` reads
the probe as today; then, only when the engine source is read, it takes the ids of the parked tasks (the rule above) in
engine order without repetition, at most the first 32, records the `tasks` source's `read_at`, calls the reader with the
runtime root and these ids (also when there are none), and validates the result by the input shape above: valid makes the
source `ok`, any exception makes only this source unavailable, keeping nothing of the error. When the engine source is
unavailable the reader is not called and the `tasks` source is unavailable. The default reader returns `{"items": [...]}`
with one item per given id, in order, for at most the first 32 ids:
- an id that does not match `[a-z0-9][a-z0-9-]{0,79}` in full gives status `oläslig` without touching any file;
- otherwise the file `.runtime/tasks/<id>/brief.md` below `Path(runtime_root).absolute()` is opened component by
  component: the root directory is opened, then `.runtime`, `tasks` and `<id>` each as a directory relative to the
  previous descriptor with `O_NOFOLLOW`, then `brief.md` relative to the last with `O_RDONLY | O_NOFOLLOW | O_NONBLOCK`;
  a missing component (`FileNotFoundError`) gives `saknas`, any other `OSError` gives `oläslig`, and so does a `brief.md`
  that is not a regular file (checked with `os.fstat` on the open descriptor before anything is read or wrapped, since
  a directory opens but cannot be read as a file); every descriptor is closed;
- at most 512 bytes are read; the first line is the bytes before the first newline byte (all bytes when there is none),
  decoded as strict UTF-8 (a failure gives `oläslig`), with one trailing carriage return removed; it must start with
  `# ` and the rest after `# ` must not be empty after Python's `str.strip()`, else `oläslig`;
- the title is the rest of that line after `# `, every run of whitespace replaced by one space and stripped; a title
  longer than 120 characters becomes its first 119 characters followed by `…` (U+2026). The item is then `läst` with
  that title.

The reader lists no directory, opens no other file and keeps nothing else of the file: a brief is a task's prompt, and only
its title line is display metadata. Titles pass the projection's display safety like every other text.

## 3. `tools/aquarium_vy.py`: constants and formats

- `SCEN` and `SKRIPT` stay exactly as they are in `tools/aquarium_vy.py` at the base, byte for byte; the acceptance
  compares their SHA-256. Neither is edited, re-indented or rebuilt; the module's docstring may be rewritten, and then it
  says precisely that a bench or review figure follows the class `aq-figur` and the watch figure the class `aq-kor`. `SCEN` is the
  page with `{{AQ_NAME}}` placeholders and `<!--AQ:LISTA:name-->` slots; one placeholder, `AQ_SENAST`, occurs more than
  once, and every occurrence gets the same value.
- `ZONE = ZoneInfo('Europe/Stockholm')` is created at import, so `render` touches no file.
- `csp()` returns exactly `default-src 'none'; style-src 'unsafe-inline'; script-src 'sha256-<B64>'; base-uri 'none';
  form-action 'none'`, where `<B64>` is the standard base64 of the SHA-256 of `SKRIPT` encoded as UTF-8.
- `TID(t)` for an aware ISO time is its Stockholm local time as `<day> <mon> <HH>:<MM>` (day without a leading zero,
  `mon` from `jan feb mar apr maj jun jul aug sep okt nov dec`), for example `24 sep 14:52`. `DATUM(x)` is `<day> <mon>`
  for a `YYYY-MM-DD` date or, for an ISO time, its Stockholm local date. `NÄR(x)` is `DATUM(x)` for a `YYYY-MM-DD` date and
  `TID(x)` otherwise. No label is relative ("i dag", "i går").
- `NAMN(x)` is `x` when it has at most 22 characters, else its first 21 characters followed by `…`.
- `EXEC(name)` is `Claude` for `claude`, `Codex` for `codex` and any other name as given. `MODELL(executor, model)` is
  `EXEC(executor) + ' ' + model`, or `EXEC(executor) + ' · modell okänd'` when the model is null.
- `SEDAN(item)` is `sedan <TID(since)>`, or `starttid okänd` when `since` is null.
- A count `n` with a singular and a plural form (`1 leverans` / `%d leveranser`) uses the singular for exactly 1.
- `SOURCES` below is the order of section 2; `title(id)`, `ok(id)` and `read_at(id)` are that source's `title`,
  `status == "ok"` and `read_at`. `KÄLLA(ids)` is `Källa: ` for one id and `Källor: ` for several, followed by the parts
  joined with `; `: for each id `<title> · läst <TID(read_at)>` when `ok`, else `<title> · otillgänglig`.

## 4. `render(projection) -> str` (pure)

No file, clock, process or network access; the input is never mutated; the same input gives the same page. Raise
`ValueError` (without private values in the message) unless the projection has exactly the top-level keys `schema`,
`provdata`, `read_at`, `sources`, `revisions`, `headline`, `arkivet`, `verkstaden`, `utkiken`, `agarens_bord`, `sockeln`;
`schema` is the integer 2; `provdata` is a boolean; `read_at` is an aware time; `sources` has exactly the eight ids, each
with status `ok` or `otillgänglig`, and every `ok` source has an aware `read_at` and an integer `stale_after_seconds`; and
`headline.pagar`, `headline.vantar` and `headline.behover_dig` are each an integer or null.

Fill `SCEN` in three passes: first every `{{AQ_NAME}}` with its value escaped by `html.escape(value, quote=True)` in one
substitution over `SCEN`; then each `<!--AQ:LISTA:name-->` with its rows; then `<!--AQ:SKRIPT-->` with `<script>` +
`SKRIPT` + `</script>`. Every placeholder in `SCEN` gets a value and every value has a placeholder; the page contains no
`{{AQ_` and no `<!--AQ:` afterwards. A list row is `<li><span class="aq-etikett">LABEL</span>TEXT</li>` with LABEL and
TEXT escaped the same way. Below, `h`, `A`, `V`, `U`, `B`, `S` and `R` are the projection's `headline`, `arkivet`,
`verkstaden`, `utkiken`, `agarens_bord`, `sockeln` and `revisions`.

### Top and freshness

- `AQ_CSP` = `csp()`. `AQ_BODY_CLASS` = `aq-provdata` when `provdata`, else empty. `AQ_READ_AT` = `read_at` as given.
  `AQ_STALE_AFTER` = the smallest `stale_after_seconds` of the `ok` sources as a decimal string, or `0` when none is `ok`.
- `AQ_OBSERVERAT` = `AQ_SENAST` = `TID(read_at)`. `AQ_ALDER_UTAN_SKRIPT` = `ålder okänd`.
- `AQ_RUBRIK` joins three phrases with ` · `:
  - work: `motorn kunde inte läsas` when `h.pagar` is null; `inget uppdrag arbetar i Runtime` for 0; `ett uppdrag
    arbetar i Runtime` for 1; `<n> uppdrag arbetar i Runtime` otherwise.
  - watch, the first that applies: `U.status` is not `ok` → `bevakningen kunde inte läsas`; `U.schedule` `stoppat` →
    `bevakningen stoppad`; `pausat` → `bevakningen pausad`; `U.running` above 0 → `bevakningen kör en omgång`;
    `U.latest` with a non-null `cause` → `bevakningens senaste omgång otillräcklig`; `U.waiting` → `bevakningens besked
    väntar på granskning`; otherwise `bevakningen i vila`.
  - owner (`ÄGARE`, also used below): with `k = B.items`, `KÄND` is `ett beslut väntar på dig`, `en operatörshandling
    väntar på dig` or `en modellfråga väntar på dig` for one item of kind `beslut`, `operatörshandling` or `modellfråga`
    (`ett ärende väntar på dig` for another kind), and `<n> ärenden väntar på dig` for more. When `B.status` is `ok`:
    `inget väntar på dig` without items, else `KÄND`. Otherwise: `okänt om något väntar på dig` without items, else
    `KÄND` + ` · fler kan finnas`.
  Then `Lugnt · ` is put in front when `h.lugnt` is true, and `PROVDATA · ` in front of that when `provdata`; finally the
  first character is made upper case.
- `AQ_ARIA` = `Aquarium` + (` med PROVDATA` when `provdata`) + `: ` + `AQ_RUBRIK` + `, läst ` + `TID(read_at)`.

### Arkivet (`A`, items as given)

- `AQ_ARKIV_STATUS` = `aq-otillganglig` when `A.status` is not `ok`, else empty.
- For n = 1..16, `AQ_VOL_<n>_CLASS` / `AQ_VOL_<n>_TITEL`: item n gives `aq-pa aq-ny` when its `date` equals the
  Stockholm local date of `read_at` (as `YYYY-MM-DD`), else `aq-pa`, and `<key> · <title> · <DATUM(date) or odaterad>`;
  a missing item gives `aq-av` and empty. `AQ_ARKIV_FLER` = `+<items − 16>` when there are more than 16, else empty.
- `AQ_ARKIV_UNDER`: `kontorets källa kunde inte läsas` when unavailable; `inga leveranser registrerade` without items;
  else `1 leverans` / `<n> leveranser`, followed by ` · senast <DATUM>` of the first item that has a date (nothing when
  none has one).
- Rows `arkivet`: unavailable → (`Läge`, `Kontorets källa kunde inte läsas; inget visas som tomt`); no items → (`Läge`,
  `Inga leveranser registrerade`); else per item (`<DATUM(date) or odaterad>`, `<key> · <title> — <basis>`).
- `AQ_KALLA_ARKIVET` = `KÄLLA(office)` + (` · main <R.office_main>` when it is not null).

### Verkstaden (`V`)

The benches take the work items in state `pågår`, in order; the review desk takes those in state `granskas` or
`integreras`, in order. `VEM(item)`: step `utförande` → `EXEC(executor) + ' · utförare'` when the executor is set, else
`utförare ej belagd`; `granskning` → `granskare ej belagd`; `integration` → `värdens integration`; `steg` → `steg
pågår`; `arbetsflödessteg` → `arbetsflödessteg`. `STEG(item)` is the activities joined with `, `, or
`arbetsflödessteg` when there are none. `TEKNISK(item)` = `<task> · <type> · <STEG> · <SEDAN>`.

- `AQ_VERK_STATUS` = `AQ_GRANSK_STATUS` = `aq-otillganglig` when `V.status` is not `ok`, else empty.
- For n = 1..3, bench n: with bench item n, `AQ_BANK_<n>_CLASS` is `aq-pagar`, followed for step `utförande` by
  ` aq-figur aq-claude`, ` aq-figur aq-codex` or ` aq-figur aq-okand` (executor `claude`, `codex`, else); `_NAMN` =
  `NAMN(short)`, `_VEM` = `VEM`, `_VAD` = `SEDAN`, `_TITEL` = `TEKNISK`. Without one: `aq-vilar`, empty, empty, empty and
  `ledig bänk`. `AQ_VERK_FLER` = `+<bench items − 3>` when there are more than 3, else empty.
- For n = 1..8, card n of the board: with parked task n, `AQ_PARK_<n>_CLASS` is `aq-pa` when its `title_status` is
  `läst`, else `aq-pa aq-titel-saknas`; `_NAMN` = `NAMN(short)`; `_TITEL` = `<T> · <task> · <SEDAN>` where `T` is the
  title when `läst`, `titel saknas i uppdragsfilen` for `saknas`, `titeln kunde inte läsas` for `oläslig` and
  `uppdragsfilerna kunde inte läsas` for `okänd`. Without one: `aq-av`, empty and empty. `AQ_PARK_FLER` = `+<parked −
  8>` when there are more than 8, else empty.
- When `V.status` is not `ok`: `AQ_TAVLA_UNDER` = `okänt`, `AQ_VERK_UNDER` = `motorn kunde inte läsas`, rows
  `verkstaden` = (`Läge`, `Motorn kunde inte läsas; inget visas som noll`). Otherwise `AQ_TAVLA_UNDER` = `inga` without
  parked tasks, else `1 uppdrag` / `<n> uppdrag`; `AQ_VERK_UNDER` = (`inget arbete observerat i motorn` without bench
  items, else `1 i arbete` / `<n> i arbete`) + ` · ` + `1 uppdrag arbetar inte` / `<n> uppdrag arbetar inte` (the number
  of parked tasks, also for 0); rows `verkstaden`: per bench item (`Pågår`, `<task> · <VEM> · <SEDAN> · steg <STEG>`), or
  (`Läge`, `Inget arbete pågår i motorn`) when there is none; then per parked task (`Arbetar inte`, `<task> · <T> ·
  <SEDAN>`), or (`Arbetar inte`, `inga uppdrag`) when there is none; then, when `V.titles` is not `ok`,
  (`Uppdragsfiler`, `kunde inte läsas; titlarna är okända men uppdragen visas`).
- `AQ_KALLA_VERKSTADEN` = `KÄLLA(engine, tasks)`.

### Granskningen (the review desk)

- With a first review item: `AQ_GRANSK_CLASS` = `aq-granskas aq-figur aq-okand` for state `granskas`, `aq-integreras`
  for `integreras`; `AQ_GRANSK_NAMN` = `NAMN(short)`, `_VEM` = `VEM`, `_VAD` = `SEDAN`, `_TITEL` = `TEKNISK`. Without one:
  `aq-vilar`, empty, empty, empty and `ingen granskning`. `AQ_GRANSK_FLER` = `+<review items − 1>` when there is more
  than one, else empty.
- `AQ_GRANSK_UNDER` and rows `granskningen`: unavailable (`V.status` not `ok`) → `motorn kunde inte läsas` and (`Läge`,
  `Motorn kunde inte läsas; inget visas som noll`); no review item → `ingen granskning observerad` and (`Läge`, `Ingen
  granskning eller integration pågår i motorn`); else `<g> granskas` and `<i> integreras` for the counts of each state,
  leaving out a zero part and joining with ` · `, and per review item (`Granskas` or `Integreras`, `<task> · <VEM> ·
  <SEDAN> · steg <STEG>`).
- `AQ_KALLA_GRANSKNINGEN` = `KÄLLA(engine)`.

### Utkiken (`U`)

- `AQ_UTK_PLATS` = `bevakningens plats · konfigurerad: ` + `MODELL(U.model.executor, U.model.model)`.
- When `U.status` is not `ok`: `AQ_UTK_STATUS` = `aq-otillganglig`, `AQ_UTK_CLASS` empty, `AQ_UTK_DAG` = `–` (U+2013),
  `AQ_UTK_DAG_TITEL` = `bevakningen kunde inte läsas`, `AQ_UTK_GRANSKAT` = `–`, `AQ_UTK_GRANSKAT_TITEL` = `bevakningen
  kunde inte läsas`, `AQ_UTK_RAPPORT_TITEL` = `bevakningen kunde inte läsas`, `AQ_UTK_NAMN`, `_VEM` and `_VAD` empty,
  `AQ_UTK_UNDER` = `bevakningen kunde inte läsas`, and rows `utkiken` = (`Läge`, `Bevakningen kunde inte läsas; inget
  visas som lugnt`), (`Konfigurerad utförare`, `MODELL(...) + ' · följer inte modellvalet'`).
- Otherwise `AQ_UTK_STATUS` is empty and `AQ_UTK_CLASS` is `aq-kor` when `U.running` is above 0, else `aq-vantar` when
  `U.waiting`, else `aq-lugn`.
  - `AQ_UTK_DAG` = the day number of `DATUM(next_planned)` (the part before the space), or `–` without `next_planned`;
    `AQ_UTK_DAG_TITEL` = `nästa omgång planerad <TID(next_planned)> · inte genomförd`, or `ingen planerad omgång känd`.
  - `BESLUT` is `reviewed.decision`, or `beslut okänt` when it is null. `AQ_UTK_GRANSKAT` = `DATUM(reviewed.at)` or
    `inget` without `reviewed`; `AQ_UTK_GRANSKAT_TITEL` = `senast granskade besked <TID(reviewed.at)> · <BESLUT>` plus
    ` · äldre än ett dygn` when `older_than_a_day`, or `inget granskat besked`.
  - `RAPPORT` = `<TID(latest.at) or tid okänd> · <outcome>` plus ` · <cause>` when there is a cause;
    `AQ_UTK_RAPPORT_TITEL` = `senaste rapport ` + `RAPPORT`, or `ingen rapport` without `latest`.
  - When `U.running` is above 0: `AQ_UTK_NAMN` = `Bevakningen`, `AQ_UTK_VEM` = `utförare ej belagd`, `AQ_UTK_VAD` =
    `omgång startad <TID(starts[0])>`, or `omgång pågår · starttid okänd` without starts; otherwise all three empty.
  - `AQ_UTK_UNDER`, the first that applies: schedule `stoppat` → `stoppad`; `pausat` → `pausad`; `okänt` → `schemat är
    okänt`; running above 0 → `omgång pågår`; `latest` with a cause → `senaste omgången otillräcklig`, followed by
    ` · nästa <TID(next_planned)>` when there is one; `waiting` → `besked väntar på granskning`; a `next_planned` →
    `nästa omgång <TID(next_planned)>`; else `ingen planerad omgång känd`.
  - Rows `utkiken`, in order: (`Schema`, `<schedule>`); (`Nästa omgång`, `planerad <TID> · inte genomförd` or `ingen
    planerad tid känd`); (`Senaste starter`, the starts as `TID` joined with `, `, or `inga kända`); only when running is
    above 0 (`Igång vid läsningen`, `1 omgång` / `<n> omgångar`); (`Senaste rapport`, `RAPPORT` or `ingen rapport`);
    (`Senast granskade besked`, `<TID(reviewed.at)> · <BESLUT>` plus ` · äldre än ett dygn` when `older_than_a_day`, or
    `inget granskat besked`); (`Konfigurerad utförare`, `MODELL(...) + ' · följer inte modellvalet'`).
- `AQ_KALLA_UTKIKEN` = `KÄLLA(watch, staffing)`.

### Ägarens bord (`B`)

- `AQ_BORD_STATUS`: `aq-harbord` when there are items and `aq-ofullstandig` when `B.status` is not `ok`, joined with one
  space when both apply, empty when neither.
- For n = 1..4, `AQ_BREV_<n>_CLASS` / `_TITEL`: item n gives `aq-pa` and `<Kind>: <text>` followed by ` · sedan
  <NÄR(since)>` when `since` is set (`Beslut`, `Operatörshandling`, `Modellfråga` for `beslut`, `operatörshandling`,
  `modellfråga`, another kind as given); a missing item gives `aq-av` and empty.
- `AQ_BORD_ANTAL` = the number of items as a decimal string, or empty without items. `AQ_BORD_FLER` = `+<items − 4>` when
  there are more than 4, else empty. `AQ_BORD_UNDER` = `ÄGARE`.
- Rows `bordet`: per item (`<Kind>` followed by ` · sedan <NÄR(since)>` when `since` is set, `<text> — <basis>`); then,
  when `B.status` is not `ok`, (`Läge`, `En källa kunde inte läsas; fler ärenden kan finnas`); when it is `ok` without
  items, only (`Läge`, `Inga ärenden väntar på dig`).
- `AQ_KALLA_BORDET` = `KÄLLA(office, questions, watch)`.

### Maskinrummet (`S`)

- `TJÄNST`: service state `igång` → `tjänsten igång · <verified> av 3 verifierade`; `delvis` → `tjänsten delvis igång ·
  <verified> av 3 verifierade`; otherwise `tjänsten okänd · ingen verifierad` when `verified` is 0, else `tjänsten kunde
  inte läsas`. `TEKNISKT`: `tekniska poster okända` when `identity_records` is null, else `1 teknisk post, inte en
  agent` / `<n> tekniska poster, inte agenter`.
- `AQ_SOCKEL_CLASS` = `aq-igang` for `igång`, `aq-delvis` for `delvis`, else `aq-okand`. `AQ_SOCKEL_UNDER` = `TJÄNST`
  + ` · ` + `TEKNISKT`. `AQ_SOCKEL_TITEL` = `TEKNISKT`.
- Rows `maskinrummet`, in order: (`Tjänsten`, `TJÄNST` plus ` · konfiguration <config>` when `config` is set); per
  staffing entry in the given order (`Konfigurerad · <role>`, `MODELL(executor, model)`), or (`Konfigurerad bemanning`,
  `okänd`) when there is none; (`Konfigurerad · bevakningen`, `MODELL(watch_staffing...) + ' · följer inte
  modellvalet'`); (`Arbetar inte`, `okänt` when `idle_tasks` is null, else `1 uppdrag` / `<n> uppdrag`); (`Pågår`,
  `okänt` when `busy` is null, `inget` for 0, else `1 uppdrag` / `<n> uppdrag`); (`Identitetsposter`, `TEKNISKT`);
  (`Revision`, `Runtime <R.runtime> · konfiguration <R.config>`, or `okänd` when `R.runtime` is null).
- `AQ_KALLA_MASKINRUMMET` = `KÄLLA(service, staffing, engine, release)`.

### Källor

Rows `kallor`, per source in `SOURCES` order: an `ok` source is
`<li data-read-at="R" data-stale-after="N"><span class="aq-etikett">TITLE</span>läst <TID(R)> · inaktuell efter <N/60> min</li>`
(R its escaped `read_at`, N its `stale_after_seconds`, N/60 in whole minutes); an unavailable one is
`<li class="aq-otillganglig-kalla"><span class="aq-etikett">TITLE</span>otillgänglig vid läsningen</li>`. Then two
ordinary rows: (`Kontoret · revision`, `main <office_main> · <TID(office_main_date)>`, or `okänd` when `office_main` is
null) and (`Runtime · revision`, `Runtime <runtime> · konfiguration <config>`, or `okänd` when `runtime` is null).

## 5. Command

```
python3 -B tools/aquarium_vy.py PROJECTION.json NEW.html
```

`PROJECTION.json` must be a regular file (not a symlink), at most 1 000 000 bytes, read through a no-follow open and
decoded as UTF-8 JSON. `NEW.html` must not exist; its parent must exist and not be a symlink; write exactly
`render(projection)` as UTF-8 through an exclusive, no-follow open with mode 0600. Exit 0 on success without printing; on
any failure exit 2 printing only `Kunde inte skapa Aquariums vy.` to stderr, with nothing private. The command reads only
the given file and never collects, serves, starts or changes anything.

## 6. Tests and documentation

`tools/test_aquarium.py` keeps its existing tests passing, adjusted only where schema 2 changes the contract, and gains
tests for sections 1 and 2: the date rule (including a commit hash that holds an eight-digit run), work and parked tasks
with every step rule, the watch's round and technical records kept out, parked titles in each `title_status`, `collect`
with an injected task reader (valid, raising, and not called when the engine is unavailable), and the default task reader
on a temporary runtime root under `.scratch` (a title, a missing brief, a symlinked brief, a symlinked directory
component, a brief that is a directory, no heading, invalid UTF-8, a long title, an invalid id, and a second line that
never leaves the reader). `tools/test_aquarium_vy.py` uses only synthetic projections (with `provdata` true) and
temporary files under `.scratch` (cleaned up) and covers sections 3 to 5, including an unavailable source beside working
ones, null counts, an old reviewed decision, planned against started rounds, figures only for evidenced work, escaping of
hostile text, a winter and a summer time, and the command's exclusive private output. Neither reads real sources or uses
the network.

`tools/AQUARIUM.md` is updated to describe schema 2 truthfully (the eight sources, work and parked tasks, the task-file
titles, `sockeln` and the headline) and gains a Swedish section `## Scenen` that explains the page: the places and what
each shows, that a figure appears only for work the engine reading evidences and that an identity it does not evidence is
shown as not evidenced (`ej belagd`), that configured staffing is not observed work, that the page is a snapshot that
starts stale and is only shown fresh by its script while the reading is younger than the smallest source limit, that a
stale page shows the last known state and does not mean that work, service or owner items have ended, that an unread
source is shown as fog and not as emptiness, that interactive work is not observed, that PROVDATA pages are synthetic,
what the page never does, and the command. The file is at least 3 000 characters long, contains word for word
`## Scenen`, `aquarium_vy.py`, `uppdragsfiler`, `ej belagd`, `inaktuell`, `PROVDATA` and `senast kända läge` (any run of
whitespace, line breaks included, counts as one space), and no longer contains `model_evidence`.

How the host verifies, as measured: it copies only the five files above into a fresh clone of the repository at the base
(no `TASK.md` and nothing else uncommitted is there) and runs its frozen acceptance in that clone inside a sandbox. There
the repository is read-only except the existing `.scratch` directory: files, directories and symlinks may be created and
removed inside it, but `.scratch` itself must never be removed, replaced or recreated. There is no network. The
environment is minimal: rely on nothing beyond `PATH`, `HOME` and `LANG`, and `TMPDIR` may not be writable, so every
temporary file goes under `.scratch` (for example `tempfile.TemporaryDirectory(dir=<repository>/.scratch)`). Python runs
with `-I -B`. The host audits `render` and `project` themselves for any file, process, socket, `os` or `ctypes` event:
inside them nothing is imported, opened, read or run (note that `datetime.strptime` imports a module on its first use), so
the modules they use are imported at module level, and `ZONE` is created at import; `bevakningsbild` is still imported
only inside the default `watch_reader`. The host runs `python3 -I -B -m unittest discover -s tools -p test_aquarium.py`
and `... -p test_aquarium_vy.py`, each of which must pass and leave `.scratch` exactly as it found it, it runs the default
task reader on its own temporary runtime roots under `.scratch`, and it runs both commands with new paths under
`.scratch`.

## 7. Design notes (for understanding; the rules above govern)

The page is one continuous workshop floor seen from above. Arkivet holds delivered volumes; Verkstaden has a board of
tasks that do not work and three benches where a figure sits only while the engine shows an executor step; the review
desk shows a review or an integration; Utkiken is the watch at the big window, with its report, its next planned day and
the date of the latest reviewed decision; Ägarens bord gets letters and a mark only when something waits for the owner;
Maskinrummet and the frosted room for interactive work are deliberately quiet. Each place links to a panel (`:target`)
with its rows and its source line. The world moves (daylight, plants, a working figure's arms) only in the fresh look and
never with reduced motion; in the stale look it stands still, fades, and marks figures as last known.
