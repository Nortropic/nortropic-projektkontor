"""Bound start settings, OVL-20260930-dbbdd8 C1. No partner-data writes.

The home-config reader follows Runtime D041 (runtime/release.py at cddaf49).
Only unambiguous top-level model/effort lines are excluded; uncertain syntax is bound whole.
"""
import hashlib
import json
from pathlib import Path
import re

# Reviewed host binding, 2026-09-30. A change needs a separately reviewed source update.
# No configuration values or authentication bytes are published here.
CODEX_CONFIG_SHA256 = 'd2051b2f5b7660335e82fc4b395e58624b89de85324af951cd59e4888832d8c9'

OWN_CHOICE = 'without-model-and-effort:'
OWN_CHOICE = re.compile(r'(model|model_reasoning_effort)[ \t]*=[ \t]*"[^"\\\n]*"')


def _depth_change(line):
    """How much one line changes the array depth, outside strings and comments; None when a multi-line string opens."""
    depth, quote, i = 0, None, 0
    while i < len(line):
        c = line[i]
        if quote:
            if c == '\\' and quote == '"':
                i += 2
                continue
            if c == quote:
                quote = None
        elif line.startswith(('"""', "'''"), i):
            return None
        elif c in '"\'':
            quote = c
        elif c == '#':
            break
        elif c == '[':
            depth += 1
        elif c == ']':
            depth -= 1
        i += 1
    return depth


def codex_config_digest(path):
    """sha256 of the Codex configuration without its top-level model and model_reasoning_effort assignments (the
    part before the first table, read with array depth). A file this reading cannot be sure of - not UTF-8, or a
    multi-line string before the first table - is hashed whole, so every change to it still counts."""
    data = Path(path).read_bytes()
    try:
        lines = data.decode('utf-8').split('\n')
    except UnicodeDecodeError:
        return hashlib.sha256(data).hexdigest()
    kept, depth = [], 0
    for index, line in enumerate(lines):
        if depth == 0 and line.strip().startswith('['):
            kept.extend(lines[index:])
            break
        change = _depth_change(line)
        if change is None:
            return hashlib.sha256(data).hexdigest()
        if depth == 0 and OWN_CHOICE.fullmatch(line.strip()):
            continue
        depth += change
        kept.append(line)
    return hashlib.sha256('\n'.join(kept).encode('utf-8')).hexdigest()



def codex_home_config():
    return Path.home() / '.codex/config.toml'


def bindning(path):
    path = Path(path)
    if not path.is_file() or any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError('Codex config.toml saknas eller ar en lank')
    digest = codex_config_digest(path)
    if digest != CODEX_CONFIG_SHA256:
        raise ValueError('Codex config.toml har andrats utan ny granskad bindning')
    return {'schema': 'without-model-and-effort/1', 'sha256': digest}


# Each scoped denial is a floor, not a complete shell/API containment boundary.
DENY = {
    'Bash(gh repo edit *--visibility*)': 'Visibility is an owner decision, never a maintenance action.',
    'Bash(gh api *visibility*)': 'The corresponding explicit API visibility field is also denied.',
    'Bash(gh api *private=*)': 'The legacy API private field also changes repository visibility.',
    'Bash(gh repo delete *)': 'Repository deletion is outside the standing implementation mandate.',
}


def claude_installningar(repon, paket):
    roots = sorted({str(Path(p).resolve()) for p in repon if p})
    return {'autoMode': {'environment': [
        '$defaults',
        'Organization: Nortropic. Source control: github.com/Nortropic; ordinary branch, commit, tests and pull requests within the accepted task are normal development work.',
        'Repository visibility: treat all Nortropic repositories as public when handling information (decision F-42); never change actual repository visibility.',
        'Sensitive data locations & audiences: evidence/**/local/ and ~/.nortropic-hemligheter/ are private. Local evidence may be read for the accepted task but never copied to public commits, PRs or messages. Secret values must never be printed or published.',
        'Working environment: recipient repositories ' + json.dumps(roots) + '; private task package ' + str(Path(paket).resolve()) + '. The package is task evidence, not a public publication destination.',
    ]}, 'permissions': {'deny': list(DENY)}}


def kodad(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def avtryck(value):
    return hashlib.sha256(kodad(value).encode()).hexdigest()
