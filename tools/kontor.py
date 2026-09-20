#!/usr/bin/env python3
"""Kontorets ingång. Runtime alone owns execution and publication."""
import argparse
import importlib
import json
from pathlib import Path
import subprocess
import sys

OFFICE = Path(__file__).resolve().parents[1]
RUNTIME = OFFICE.parent / 'Nortropic Runtime'


def selected_task(name):
    path = OFFICE / 'tasks' / name
    if path.parent != OFFICE / 'tasks' or path.suffix != '.json' or path.is_symlink():
        raise ValueError('Välj en uppdragsfil direkt under tasks/')
    task = json.loads(path.read_text())
    if task.get('target') != 'Nortropic/nortropic-projektkontor':
        raise ValueError('Fel målrepo')
    return path, task


def observation(task):
    sys.path.insert(0, str(RUNTIME))
    from runtime.inspection import inspect
    report = inspect(task['id'])
    # The selected accepted input must match the frozen running task.
    from runtime.integration import digest
    if report.get('task_sha256') != digest(task):
        report.update(observation='unavailable', verified_delivery=False,
                      error='Valt uppdrag matchar inte fryst körning')
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['start', 'status', 'fortsatt', 'resultat'])
    parser.add_argument('--task', default='resultat.json', help='Accepterad fil under tasks/')
    reasons = parser.add_mutually_exclusive_group()
    reasons.add_argument('--diagnosis')
    reasons.add_argument('--reconcile')
    reasons.add_argument('--review-repair')
    reasons.add_argument('--review-retry')
    args = parser.parse_args(argv)
    signals = {k:getattr(args,k.replace('-','_')) for k in ('diagnosis','reconcile','review-repair','review-retry')}
    if any(signals.values()) and args.action != 'fortsatt':
        parser.error('Fortsättningsskäl får bara användas med fortsatt')
    try:
        path, task = selected_task(args.task)
        if args.action in ('status','resultat'):
            report = observation(task)
            if args.action == 'resultat':
                try:
                    renderer = importlib.import_module('kontor_result')
                except ModuleNotFoundError:
                    raise ValueError('Resultatfunktionen är ännu inte levererad')
                report = renderer.render(report)
            print(json.dumps(report, ensure_ascii=False, indent=2))
            return 0 if report.get('observation') != 'unavailable' else 2
        argv = [str(RUNTIME/'.runtime/temporal-venv/bin/python'), '-B', '-m', 'runtime.run', str(path)]
        if args.action == 'fortsatt':
            argv.append('--resume')
            for key, value in signals.items():
                if value: argv += ['--'+key, value]
        return subprocess.run(argv, cwd=RUNTIME, check=False).returncode
    except (OSError, ValueError, KeyError) as error:
        print(json.dumps({'observation':'unavailable','error':str(error)},ensure_ascii=False))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
