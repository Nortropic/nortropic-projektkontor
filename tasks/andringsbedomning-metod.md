# AP05 bounded follow-up: keep missing selected sources untouched

This is a technical correction inside AP05-ACCEPT, not another business phase.
Runtime already built the core helper; do not rework it, the engine, authority,
case schema or timestamp scope. Runtime owns process checks, frozen acceptance,
review and protected publication. Only edit tools/CHANGE_ASSESSMENT.md and
 tools/test_change_assessment.py. All examples/fixtures must remain synthetic.

Independent method review of prior candidate 627bfac found one remaining blocker:
the host recipe checks whether output equals or contains a selected source/case,
but fails to reject output UNDER a missing selected source path. With a missing
selected source office/pending.txt and output office/pending.txt/run, mkdir(parents=True)
creates the source path as a directory, changing missing to unsafe. The measurement
workflow must never create or alter selected source paths as a side effect.

Fix the existing collision condition to reject BOTH containment directions for
every selected source path and the case file, before mkdir or invoking a verifier.
Retain a legitimate fresh private output directory below a broad common source
root when it is separate from every selected file. Keep exclusive writes and
all existing stdin/host-role/error-handling corrections. Add a meaningful
regression test executing the documented recipe against a missing synthetic
selected source and nested output; show selected path and output remain absent.
Also retain/prove the legitimate broad-root output case. No original source access,
new dependencies, new authority, or new engine. Core tools/change_assessment.py is
not writable. Review only this change and its regression, reusing prior core proofs.

The external frozen acceptance executes the actual documented Python recipe in
a native sandbox with isolated synthetic data under .scratch, and checks both
negative containment cases and legitimate output. It also runs existing unit tests.
Check that all content is public-safe before approval. No internal case sources,
private paths, credentials or raw sessions are available or to be introduced.
