#!/usr/bin/env python3
"""Private file interface to the delivered preparation core; always a draft."""

import argparse
import json
import math
import os
from pathlib import Path
import stat
import sys

import assignment_preparation


FILES = ("private.json", "package.json", "task.draft.json", "brief.draft.md")
ERROR = {"error": "Preparation failed: invalid command, input, or output."}


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        # argparse's normal diagnostics echo arguments, which may be private.
        raise ValueError("invalid command")


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate key")
        result[key] = value
    return result


def _reject_constant(value):
    raise ValueError("non-JSON constant")


def _finite_float(value):
    number = float(value)
    if not math.isfinite(number):
        raise ValueError("nonfinite number")
    return number


def _read_json(path):
    if path.is_symlink() or not stat.S_ISREG(path.stat().st_mode):
        raise ValueError("input must be a regular non-symlink file")
    with path.open(encoding="utf-8") as stream:
        return json.load(stream, object_pairs_hook=_unique_object,
                         parse_constant=_reject_constant, parse_float=_finite_float)


def _path_keys(path):
    # Keep lexical aliases too: resolving a selected symlink must not discard
    # protection of its own name. Missing tails are deliberately retained.
    return {tuple(part.casefold() for part in variant.parts)
            for variant in (path.absolute(), path.resolve(strict=False))}


def _overlaps(left, right):
    return any(a[:len(b)] == b or b[:len(a)] == a
               for a in _path_keys(left) for b in _path_keys(right))


def _check_output(output, inputs, case, source_root):
    absolute = output.absolute()
    # Check before resolve, so symlink/../new cannot conceal a symlink ancestor.
    if any(path.is_symlink() for path in (absolute, *absolute.parents)):
        raise ValueError("symlink output or ancestor")
    if output.exists() or not output.parent.is_dir():
        raise ValueError("output exists or parent is absent")
    protected = list(inputs) + [source_root / s["path"] for s in case["sources"]]
    if any(_overlaps(output, path) for path in protected):
        raise ValueError("output overlaps selected input or source")


def _json_bytes(value):
    return (json.dumps(value, ensure_ascii=True, allow_nan=False, indent=2)
            + "\n").encode("utf-8")


def _write_bundle(output, contents):
    # No parents=True, cleanup, replacement or retry: preserve any partial bundle.
    output.mkdir(mode=0o700)
    output.chmod(0o700)
    for name, content in zip(FILES, contents):
        descriptor = os.open(output / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            os.fchmod(descriptor, 0o600)
            with os.fdopen(descriptor, "wb", closefd=False) as stream:
                stream.write(content)
        finally:
            os.close(descriptor)


def main(argv=None):
    parser = _Parser(prog="bered_uppdrag.py", allow_abbrev=False,
                     description=__doc__)
    parser.add_argument("case", type=Path)
    parser.add_argument("check", type=Path)
    parser.add_argument("spec", type=Path)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    try:
        args = parser.parse_args(argv)
        inputs = (args.case, args.check, args.spec)
        case, check, spec = (_read_json(path) for path in inputs)
        result = assignment_preparation.prepare(case, check, spec)
        _check_output(args.output, inputs, case, args.source_root)
        package = result["package"]
        # Serialize everything before mkdir, including UTF-8 validation of prose.
        contents = (_json_bytes(result["private"]), _json_bytes(package),
                    _json_bytes(package["task_draft"]), package["brief"].encode("utf-8"))
        summary = json.dumps({"status": "draft",
                              "mechanical_complete": result["mechanical_complete"],
                              "gaps": result["gaps"], "files": list(FILES)},
                             ensure_ascii=True, allow_nan=False)
        _write_bundle(args.output, contents)
    except (ValueError, OSError, TypeError, RuntimeError, OverflowError):
        print(json.dumps(ERROR))
        return 2
    print(summary)
    return 0


if __name__ == "__main__":
    sys.exit(main())
