"""Startkontroll för kontorets ingång (UNDERHALL-INGANGAR-20260924). Varnar; ändrar ingenting.

    python3 -B tools/ingang.py              hämtar origin och jämför
    python3 -B tools/ingang.py --no-fetch   jämför med senast hämtade läge

Primärutcheckningen ska stå på `main` lika med `origin/main`, utan egna commits och utan ändrade spårade filer, och
ingen lokal gren ska finnas bara här utan att planen på `origin/main` namnger den. Varje avvikelse blir en rad som börjar
med `VARNING:`; sista raden är `INGÅNG OK` eller `INGÅNG: n varningar`. Avviker ingången läses planen från `origin/main`
(`git show origin/main:docs/plan.md`) och avvikelsen rapporteras. Exitkoden är alltid 0. Kontrollen byter aldrig gren
och skriver inga filer, behörigheter eller inställningar; den enda skrivningen är `git fetch`, som uppdaterar
fjärrspårande referenser.
"""
import argparse
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MAIN = 'refs/remotes/origin/main'


def git(repo, *args):
    run = subprocess.run(['git', '-C', str(repo), *args], capture_output=True, text=True)
    return run.returncode, run.stdout.strip()


def check(repo=REPO, fetch=True):
    """Varningarna för ingången som text; en tom lista när ingången följer main."""
    warnings = []
    if fetch and git(repo, 'fetch', '--quiet', 'origin')[0]:
        warnings.append('origin kunde inte hämtas; jämförelsen gäller senast hämtade läge')
    code, main = git(repo, 'rev-parse', '--verify', '--quiet', MAIN)
    if code:
        return warnings + ['origin/main finns inte lokalt; ingången kan inte jämföras']
    branch = git(repo, 'rev-parse', '--abbrev-ref', 'HEAD')[1]
    if branch == 'HEAD':
        warnings.append('ingången står inte på en gren utan på en fristående commit')
    elif branch != 'main':
        warnings.append('ingången står på %s, inte på main' % branch)
    if git(repo, 'rev-parse', 'HEAD')[1] != main:
        ahead, behind = git(repo, 'rev-list', '--left-right', '--count', 'HEAD...' + MAIN)[1].split()
        warnings.append('ingången skiljer sig från origin/main (%s egna commits, %s bakom); läs planen med '
                        '`git show origin/main:docs/plan.md`' % (ahead, behind))
    changed = git(repo, 'status', '--porcelain', '--untracked-files=no')[1]
    if changed:
        warnings.append('%d spårade filer har ändringar som inte är committade' % len(changed.splitlines()))
    # A branch lives only here when its tip is reachable from no origin ref; the plan on origin/main may name it.
    local_only = set(git(repo, 'rev-list', '--branches', '--not', '--remotes=origin')[1].split())
    plan = git(repo, 'show', MAIN + ':docs/plan.md')[1]
    branches = [line.split() for line in git(repo, 'for-each-ref', 'refs/heads', '--format=%(refname:short) %(objectname)')[1].splitlines()]
    unnamed = sorted(name for name, tip in branches if tip in local_only and name not in plan)
    if unnamed:
        warnings.append('lokala grenar utan kopia på origin och utan namngivet skäl i planen: ' + ', '.join(unnamed))
    return warnings


def main(argv=None, repo=REPO):
    parser = argparse.ArgumentParser(description='Startkontroll för kontorets ingång; varnar, ändrar ingenting.')
    parser.add_argument('--no-fetch', action='store_true', help='jämför med senast hämtade läge')
    warnings = check(repo, fetch=not parser.parse_args(argv).no_fetch)
    for warning in warnings:
        print('VARNING: ' + warning)
    print('INGÅNG OK' if not warnings else 'INGÅNG: %d varningar' % len(warnings))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
