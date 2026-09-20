# AP08: a private Swedish owner reading surface

Build only tools/agarbild.py, tools/test_agarbild.py, tools/AGARBILD.md.
Existing Runtime builds/tests/reviews/integrates this product. Do not modify any
other file, active execution, host acceptance or publication authority. No new
dependencies, services, model calls, scheduler, state or decision engine.

Outcome: a beautiful, calm, readable Swedish standalone local HTML report. Lead
with usable capabilities/limits, latest observed work, next justified action and
whether the owner has a real decision. Technical IDs/revisions/receipts go in
native details/summary sections, not as primary titles. Responsive layout,
readable typography, clear unknown/conflict notices, no traffic-light inference.
No JavaScript, forms, external assets/fonts, URLs, remote resources, refresh,
iframes or execution controls. Only fragment links to inline evidence details;
source locators are escaped plain text. Inline CSS with no url()/@import. Strong
meta CSP default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'.
Opening the file must need no server/network and cause no work or source reads.
The host supplies source-bound judgment; rendering never authenticates it.

Implement pure render(data) -> str and CLI:
  python3 -B tools/agarbild.py INPUT.json NEW.html
Only stdlib. Strict JSON decoding (duplicates/nonfinite rejected), schema validation,
UTF8, generic error to stderr/exit2 (no private values), success exit0. Never
execute data, follow its source locator, gather sources, invoke Runtime or refresh
source hashes. Input must be a regular nonsymlink file; output a NEW regular HTML
file mode0600 under existing nonsymlink parents, no overwrite or source mutation.
Read and validate fully before output creation. Reject input/output aliases and
symlink paths/ancestors. Exclusive nofollow creation. Document trusted local use,
not guarantees against hostile filesystem races. render has no IO/clock effects.

Exact schema1 (all listed keys required; no extras):
{
 "schema":1, "generated_at":"timezone-aware ISO8601", "title":"text",
 "summary":"text", "scope":"text",
 "capabilities":[{"title":"text","use":"text","limits":"text",
   "delivery":"text","availability":"text","evidence":["e1"]}],
 "work":[{"title":"text","state":"accepted|running|waiting|finished|superseded|unknown|proposed",
   "text":"text","observed_at":"aware ISO8601 or null","evidence":["e1"]}],
 "next_action":{"text":"text","owner":"text","authority":"accepted|proposed|none|unknown","evidence":["e1"]},
 "owner_decision":{"needed":"yes|no|unknown","question":"text","reason":"text","evidence":["e1"]},
 "issues":[{"text":"text","evidence":["e1"]}],
 "evidence":[{"id":"ASCII alnum/hyphen ID","title":"text","kind":"text",
    "observed_at":"aware ISO8601 or null","revision":"text","locator":"text",
    "sha256":"64 lowercase hex or null","text":"text"}]
}
All text nonempty strings; all evidence reference lists nonempty/unique, resolve
to unique IDs. capabilities/work/issues may be empty; evidence nonempty. Strict
integer schema1 (not bool). Dates real aware ISO8601, no future observation relative
to generated_at. No special inference from hashes, words or statuses. Null
observations visibly say observation missing, cannot infer nothing underway.
Always label generated_at as Framställd and source/work times as Observerad;
show age at generation (never claim current clock time or live monitoring).
Always explain dated projection, source review/authority limits. Delivery and
current availability separately labelled. Historical superseded work separately
labelled, never counted active or raised as an owner blocker. Technical waits
remain distinct from supplied owner_decision; don't derive decisions from waits.
Conflicting evidence/unknown issues stay visible, never pick greenest. Supplied
explicit no-owner-decision shows clearly. Proposed next action is not accepted.
Do not detect semantic truth: host substantive review remains necessary.

Tests: realistic positive Swedish synthetic report; missing, old and contradictory
observations; superseded wait; genuine owner question and no-owner-decision;
separate availability from delivery; arbitrary hostile strings escaped and no
active markup/remote links, timezone/future/strict structure/refs invalid inputs;
CLI actual offline output, preservation, existing paths/symlinks/aliases rejected.
No generic framework. Documentation gives exact schema, synthetic example and
host update recipe: read existing kontor status/result with appropriate task,
canonical plan/decisions/receipts, preserve exact snapshot/time/version, assess
meaning, author private input, render NEW version, independently compare main
claims; retain previous output and provide user opening point. No broad source
scan, old-task restart, new authority, auto freshening or public real reports.

Host separately performs real private application/browser/recipient review and
protected delivery verification. Renderer output alone is not delivery evidence.
AP07 is optional support, not a standard step; no repeat pilot. Old audit status
unchanged. No private production material has been provided to this candidate.
