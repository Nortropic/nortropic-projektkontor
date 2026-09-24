# AP10 — bounded HTTP content decoding for the existing intake

Fix only `tools/bevakningsunderlag.py`, its synthetic tests
`tools/test_bevakningsunderlag.py` and operator documentation
`tools/BEVAKNINGSUNDERLAG.md`. Current qualified code already owns URL selection,
private immutable collection and dated-label parsing. This task repairs one
observed transport gap: a gzip HTTP body must be decoded before the existing
HTML/JSON parsing and policy's readable evidence copies. No policy, scheduler,
model, deployment, Runtime, public-source fixture or live network changes.
Standard library only; no installation, operational/activation/publication
commands or credentials. Local read/edit and synthetic test commands are allowed.
Test in .scratch.

## Exact transport contract

Keep the `fetch(url) -> bytes` API and build_opener synthetic seam. Retain the
exact existing URL allowlist, reject URL before transport, GET, fixed User-Agent,
ProxyHandler({}), redirect denial even to allowed destinations, default TLS
verification, no auth/cookies/proxy, timeout10s and no retry. Add only the fixed
request header `Accept-Encoding: identity`. Servers may still return gzip.

Read at most 1MiB+1 encoded response bytes; reject if encoded length exceeds
1MiB. For absent Content-Encoding or `identity`, return bytes unchanged. For
`gzip`, return decoded bytes, with a separate 1MiB decoded cap. Accept ordinary
case-insensitive encoding tokens after surrounding whitespace removal.
Reject empty explicit header, unsupported tokens (including br/deflate/x-gzip),
stacked/list values and repeated Content-Encoding headers. Inspect HTTP headers
as metadata, never guess content encoding from body magic. Actual urllib
responses expose HTTPMessage headers; synthetic response headers must faithfully
support this. Missing header is identity, not a request to sniff compressed data.

Gzip decoding must be bounded during expansion, not an unbounded decompress
followed by a size check. Validate complete stream/trailer/checksum. Reject
truncated/corrupt streams and trailing data or concatenated members; this narrow
single-member transport contract is deliberate. Bound both read and expansion,
including exact-cap success and cap+1 failure. No content or private exception
text in errors; use existing IntakeError/fixed reasons. Do not weaken HTTP status,
final URL or other intake checks to work around decoding. Policy needs no change:
it already copies the bytes preserved by collect.

## Representation and preservation

After this repair `fetch` returns HTTP content-decoded body bytes, unchanged
within that representation (no charset conversion, HTML rewriting or JSON
reformatting). For identity this is byte-for-byte the received entity body;
for gzip it is the bounded decoded entity. `collect`'s existing `.raw` filename
means that unparsed body, not captured compressed wire bytes. Source SHA256 and
fingerprint bind those stored content-decoded bytes. Document this explicitly;
do not claim wire capture or backfill transport metadata not recorded.

Do not rewrite or decode any old packet in place. Old incomplete/compressed
evidence stays preserved with its original revision/meaning. Subsequent intake
is a new exclusive private observation; any changed hash remains changed, not
silently approved. Malformed/unsupported/oversize transport is unavailable and
incomplete; independent successful observations remain available. Existing
source selection, dates, complete/fingerprint semantics, no-secret diagnostics,
LOCAL_FILES, output/source symlink protection, modes and preservation all remain.

Retain all existing intake tests. Update their transport response fixture to
realistic headers and its exact header expectation for the added fixed identity
request, then add synthetic gzip/identity/invalid-encoding/boundary tests.
Retain the dated Python label and URL/version-mismatch regressions. Documentation
may correct its enumerated local-file list to the already implemented fifteen
entries; do not expand the actual list or other product scope.

The frozen host verifier carries the prior independent intake checks, with only
the already-qualified fifteen-file assertion adapted, plus targeted transport
and gzip-through-collect checks. No interpreter-version-dependent AST checksum
is used. The host separately reviews the exact narrow diff, freezes revisions,
and owns Runtime execution, independent review and protected integration.
Neither this build nor a synthetic PASS resumes a spent monitoring round or
activates changed code. No live source/private corpus reads in this candidate.
