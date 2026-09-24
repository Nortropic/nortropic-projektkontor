# AP10 — dated monitoring picture through existing AP08

Implement only `tools/bevakningsbild.py`, `tools/test_bevakningsbild.py` and
Swedish documentation `tools/BEVAKNINGSBILD.md`. Use Python standard library and
existing `agarbild.render` unchanged. No new renderer, scheduler, source intake,
models, notifications, commands for activation, publication or authority.
This is the needed AP04 build during the accepted monitoring obligation; its
actual coexistence and final evidence are checked by the host separately.
No real private fixtures, Runtime operations or network in candidate tests.
Import is inert. Synthetic tests use .scratch. Future base/Runtime identities
are supplied by the host's task JSON when known, never invented here.

## Public API and presentation

`view(native, latest, reviewed, generated_at)` is pure: no I/O, clock reads or
input mutation. Return exactly an AP08 schema-1 input accepted by agarbild.render.
native is the captured `runtime.obligation status` dictionary, or
`{obligation:'office-python-temporal', unavailable:true, reason:<fixed reason>,
observed_at:<aware ISO time of failed observation>}`. latest/reviewed are null or
`{report, packet, integrity, locator}`, where integrity is available/unavailable
and locator is a private report location displayed only as text. A malformed or
unavailable wrapper never produces a successful claim. Use the actual report
protocol in tools/BEVAKNING.md and tools/bevakning.py, not a newly invented outcome schema.

Keep distinct evidence entries with stable IDs `native`, `latest`, `reviewed`
(including explicit missing evidence) and work rows titled `Schema`,
`Senaste observation`, `Senast granskade besked`. Main text is Swedish.
Show an additional current gap when a later native recent/running action has no
matching readable report. Do not overwrite the last known observation date with
the current native query time. Never mark the latest observation successful
merely because an older reviewed report exists. In particular latest unreviewed,
incomplete, unavailable or damaged => its work state waiting/unknown, not finished;
the older valid review remains separately visible as dated history.

Actual native status fields: observed_at, obligation, paused, note,
limited_actions, remaining_actions, schedule (ScheduleSpec as dictionary),
policy, next_action_times, actions, missed_catchup, skipped_overlap, running,
recent, meaning. running entries contain workflow_id/first_execution_run_id.
recent entries contain `scheduled_at`, `started_at` and
`action:{workflow_id,first_execution_run_id}`. The SDK converts protobuf
actual_time into started_at; there is NO mode or actual_time field in this JSON.
Serialize/interpret timestamps with explicit timezone, including Python's space
separator from default=str. Future next_action_times are planned times in text,
never observations. A native action is a start, not a completed source intake.
The reviewed catchup policy is now22hours (native `22:00:00`), strictly below
Stockholm spring DST spacing. Do not label old24hour policy as the final frame.

Derive stopped from note beginning STOPPED; otherwise paused=true is paused,
false is enabled according to that observation. Running actions are reported
separately; paused does not mean an in-flight round was cancelled. Missing or
malformed fields => unknown. No inference from an alive process. limited_actions
true plus a year-bounded calendar denotes the labeled one-shot qualification
test. The reviewed daily configuration is limited_actions=false, calendar 09:00
Europe/Stockholm with no year restriction; unknown/different specs are reported
as other/unknown, never silently as qualified daily operation. Treat the
native field `schedule.cron_expressions` as empty only for the exact string
`'[]'` (the actual serializer's empty Sequence) or the empty list `[]`.
No eval or broad JSON/string coercion: arbitrary/nonempty strings, nonempty
lists, null and missing values make the qualified schedule unknown (Schema work
state unknown), even if other calendar fields look daily. Preserve known
paused/STOPPED information separately in its text. Both accepted empty forms
must still recognize the same daily/probe calendar under paused and STOPPED.
Show the next
native action time, counts of missed catchup/overlap and actual recent start
time/run identity in evidence. No test interval becomes several days of operation.

Display packet observed_at, case-baseline first_treated_at, actual reported_at
and original reviewed_at distinctly. Reused review preserves its old review date
and indicates reuse; it is not another independent review. Show old_gaps and
report limitations. An observation older than one day at generated_at is labeled
`inaktuell` with its dated scope, without alleging a missed round while paused.
Unknown/future/invalid observation times become explicit gaps (do not feed a
future observed_at into AP08). Every picture says dated, not live or notification.

Next handling belongs to the chain driver: diagnose unknown or failed evidence,
respect paused/stopped state, or await the named planned round within existing
mandate. Do not instruct an automatic restart, upgrade or new phase. A latest
bound reviewed propose_action with an AP06 draft is an unexecuted owner question:
owner_decision.needed=yes and next_action.authority=proposed. A missing/rejected
review or technical waiting alone gives no owner approval and is not a routine
owner task. An older proposal stays historical if a later failure blocks current
assessment; do not present it as a new accepted action. No stale report creates
new authority. Technical identifiers belong primarily in evidence details.

## Bounded read-only collection

`collect(runtime_root, status_reader=None)` returns exactly `{native,latest,reviewed}`.
The Python API root is a test/operator seam, not an arbitrary CLI target option.
CLI derives sibling `Nortropic Runtime` from this Office repository. Read only
`.runtime/ap10/active.json`, its exact pinned release/config, and immediate
rounds/*/report/result.json with specifically bound intake/data/packet.json and
original analysis/result.json and review/result.json. Read no events, stderr,
credentials, arbitrary source paths or raw sessions. No artifact writes/repairs.
JSON is strict (duplicate keys and nonfinite values rejected); max 8MiB per JSON,
512 immediate round directories, 64MiB total documentary reads. Hitting a limit
is an explicit incomplete/unavailable observation, not proof that no newer work
exists. Use regular no-follow files; reject symlinks in every ancestor, traversal,
out-of-root pointers and nonregular objects. Exceptions expose fixed reasons,
not private content. A bad record must not erase readable older evidence.

Before ANY process launch, validate active.json `{config,sha256}`, the actual
config bytes, canonical host_root/office_root/database mapping, 40hex revisions
and safe release directory under runtime_root/.runtime/ap10/releases/. Verify
config.files hashes for all selected frozen regular files under that release,
bounded separately by 512MiB total. Do not import working-checkout Runtime.
No symlink code/config path may become executable. The already qualified venv's
Python launcher is the fixed executable; its ordinary venv interpreter symlink
is not a new target selector. Require the frozen runtime/obligation.py binding.

Only allowed Office subprocess is
`[runtime_root/'.runtime/temporal-venv/bin/python', '-B', '-m',
'runtime.obligation', 'status']`, cwd=<pinned-release>/runtime, shell=False,
capture_output=True, text=True, timeout=20. Use a minimal env with ordinary
PATH/HOME/USER/LOGNAME/LANG/TMPDIR plus PYTHONDONTWRITEBYTECODE=1,
NR_HOST_ROOT=canonical root and NR_CONFIG_SHA256=the checked config hash;
do not inherit PYTHONPATH/PYTHONHOME or arbitrary NR overrides. Never fallback
to working code, install/start/run/resume/pause/stop/test/daily/trigger, engine
or worker creation. The existing frozen status command only verifies/attaches
to its shared service and queries native status. Timeout, absent service,
nonzero exit or invalid JSON => native unavailable, preserve readable reports.
Recheck active pointer/config binding after the query; a concurrent change
invalidates this native observation rather than selecting a different version.
When provided, `status_reader(runtime_root, config)` replaces ONLY this query
(config includes verified directory and config_sha256). It must not bypass
file/config validation; do not expose arbitrary command/URL arguments. The named
case_id comes from the pinned, hash-verified context/watch.json, not whichever
report happens to be discovered first; require that context binding.

For report integrity bind obligation, case_id, safe locator and run_id to its
round, packet file SHA256 and valid report/packet timestamps. For claimed reviewed
evidence require original successful analysis/review result bytes matching the
reported hashes, true completed/valid_terminal/process_group_removed flags,
distinct nonempty thread IDs matching the report, approved verdict with no
blockers, and the SHA256 of canonical full analysis answer matching review and
report. Canonical JSON: sort_keys=True, separators=(',', ':'), ensure_ascii=True,
allow_nan=False. Compare case_id, packet_sha256, decision, reasoning, evidence
and contradictions against the bound answer; a modified summary is not reviewed.
No executable action/publication flag may be true. All this is documentary
verification, not a new substantive review or authentication guarantee.

For reuse, review_origin must name the original fresh report directly within
the same rounds directory, not arbitrary paths or another reused report. Verify
that origin and its packet/results; require same case/context, complete equal
fingerprints, same reviewed decision/reasoning and original review metadata/date.
Current observation/report timestamps and packet hash remain current. A newer
integrity-available report with reviewed=false can be the latest observation but
never the latest reviewed result. Damaged records can be latest unavailable with
safely readable time, never silently replaced by an older positive result. Native
recent/running actions later than any readable report remain explicit gaps.
Do not turn null packet, reviewed='true', or incomplete input into success.

## CLI and private output

`main(argv=None)` accepts exactly one argument, NEW_OUTPUT_DIRECTORY. On success
return 0, create only input.json and index.html with agarbild.render(view(...)),
files0600 and directory0700. The parent must already exist; reject existing output
and symlink ancestors before collection. No source, active pointer or previous
picture is modified. Opening HTML is inert; no auto-open/browser/server.
Failure returns 2 with a fixed non-sensitive stderr diagnostic and no overwrite.
A native status failure still creates a useful dated picture of unavailable
schedule and available older evidence. Never publish the picture or its inputs.
Document boundaries, age, pauses/stops, one-shot tests, explicit review reuse,
owner questions and the separation from AP10's real final qualification.
