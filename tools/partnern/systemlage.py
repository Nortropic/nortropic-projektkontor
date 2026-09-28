"""Aktuellt systemläge genom redan tillåtna läsvägar, alltid med lästid.

Git läses med plumbing (ingen fetch, ingen skrivning), GitHub genom `gh` med GET, och Runtimes drift genom
Aquariums befintliga, avgränsade läsning (`aquarium.collect`). Går något inte att nå visas senast kända
observation med sin ålder, aldrig en gissning.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

from .lager import nu

CACHE_SEKUNDER = 300


def _git(repo: Path, *args, timeout: int = 15) -> str | None:
    try:
        r = subprocess.run(['git', '-C', str(repo)] + list(args), capture_output=True, text=True, timeout=timeout,
                           check=False)
    except (OSError, subprocess.SubprocessError):
        return None
    return r.stdout if r.returncode == 0 else None


def _alder(tid: str) -> str:
    try:
        t = datetime.strptime(tid[:19], '%Y-%m-%dT%H:%M:%S').replace(tzinfo=timezone.utc)
    except ValueError:
        return 'okänd ålder'
    s = int((datetime.now(timezone.utc) - t).total_seconds())
    if s < 90:
        return '%d s' % s
    if s < 5400:
        return '%d min' % (s // 60)
    if s < 172800:
        return '%.1f h' % (s / 3600)
    return '%d dygn' % (s // 86400)


class Systemlage:
    def __init__(self, konfig, lager):
        self.k = konfig
        self.lager = lager
        self._las = threading.Lock()
        self._cache = {}
        self._fil = Path(self.lager.data) / 'systemlage-senast.json'
        if self._fil.exists():
            try:
                self._cache = json.loads(self._fil.read_text('utf-8'))
            except ValueError:
                self._cache = {}

    def las(self, delar: list | None = None, farsk: bool = False) -> dict:
        delar = delar or ['repon', 'plan', 'drift']
        ut = {}
        for del_ in delar:
            fn = {'repon': self._repon, 'plan': self._plan, 'drift': self._drift, 'pr': self._pr}.get(del_)
            if not fn:
                continue
            with self._las:
                gammal = self._cache.get(del_)
            if gammal and not farsk and time.time() - gammal.get('_epoch', 0) < CACHE_SEKUNDER:
                ut[del_] = dict(gammal, alder=_alder(gammal['last']))
                continue
            try:
                varde = fn()
                varde.update(last=nu(), _epoch=time.time(), status='läst')
            except Exception as fel:  # en läsare som fallerar gör bara sin egen del otillgänglig
                if gammal:
                    varde = dict(gammal, status='kunde inte läsas nu (%s); visar senast kända' % type(fel).__name__)
                else:
                    varde = {'status': 'otillgänglig (%s)' % type(fel).__name__, 'last': nu(), '_epoch': time.time()}
            with self._las:
                self._cache[del_] = varde
                try:
                    self.lager.spara_privat_fil(self._fil, json.dumps(self._cache, ensure_ascii=False).encode())
                except OSError:
                    pass
            ut[del_] = dict(varde, alder=_alder(varde['last']))
        for v in ut.values():
            v.pop('_epoch', None)
        return ut

    def _repon(self) -> dict:
        ut = {}
        for namn, rot in self.k.repon.items():
            rot = Path(rot)
            if not rot.exists():
                ut[namn] = {'status': 'saknas lokalt'}
                continue
            main = (_git(rot, 'log', '-1', '--format=%H%x09%cI%x09%s', 'origin/main') or '').strip().split('\t')
            gren = (_git(rot, 'rev-parse', '--abbrev-ref', 'HEAD') or '').strip()
            head = (_git(rot, 'rev-parse', 'HEAD') or '').strip()
            smutsig = [r for r in (_git(rot, 'status', '--porcelain=v1', '--untracked-files=no') or '').splitlines() if r]
            hamtad = None
            fh = rot / '.git' / 'FETCH_HEAD'
            if fh.exists():
                hamtad = datetime.fromtimestamp(fh.stat().st_mtime, timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
            grenar = [g.strip() for g in (_git(rot, 'for-each-ref', '--format=%(refname:short)', 'refs/heads') or '').splitlines()]
            wt = (_git(rot, 'worktree', 'list', '--porcelain') or '').count('worktree ')
            ut[namn] = {
                'origin_main': main[0][:12] if main and main[0] else None,
                'origin_main_tid': main[1] if len(main) > 1 else None,
                'origin_main_rubrik': main[2][:140] if len(main) > 2 else None,
                'primar_gren': gren, 'primar_foljer_main': bool(main and main[0] and head == main[0]),
                'andrade_sparade_filer': len(smutsig), 'lokala_grenar': len(grenar), 'worktrees': wt,
                'senast_hamtat_fran_github': hamtad,
                'not': 'origin/main är den senast hämtade kopian, inte en live-läsning av GitHub.'}
        return {'repon': ut}

    def _plan(self) -> dict:
        text = _git(Path(self.k.kontor_primar), 'show', 'origin/main:docs/plan.md') or ''
        block = text.split('\n---\n')[0][:3500]
        tur = ''
        m = re.search(r'(^#+ .*ÄGARENS TUR.*$)([\s\S]{0,2500})', text, re.M)
        if m:
            tur = (m.group(1) + m.group(2)).split('\n#')[0][:2000]
        return {'planens_oversta_block': block, 'agarens_tur': tur,
                'not': 'Planen på kontorets origin/main. Planen ensam äger nästa handling i kontoret.'}

    def _pr(self) -> dict:
        ut = {}
        for namn, rot in self.k.repon.items():
            try:
                r = subprocess.run(['gh', 'pr', 'list', '--state', 'open', '--limit', '10', '--json',
                                    'number,title,headRefName,updatedAt,isDraft'], cwd=str(rot), capture_output=True,
                                   text=True, timeout=20, check=False)
                ut[namn] = json.loads(r.stdout) if r.returncode == 0 else {'status': 'gick inte att läsa'}
            except (OSError, subprocess.SubprocessError, ValueError):
                ut[namn] = {'status': 'gick inte att läsa'}
        return {'oppna_pr': ut, 'not': 'Läst från GitHub med ägarens gh-inloggning (endast läsning).'}

    def _drift(self) -> dict:
        """Runtimes drift genom Aquariums befintliga, avgränsade läsning."""
        runtime = Path(self.k.repon.get('runtime', ''))
        kontor = Path(self.k.kontor_primar)
        tools = str(kontor / 'tools')
        kod = ('import sys, json; from datetime import datetime, timezone; sys.path.insert(0, %r); import aquarium; '
               'r = aquarium.collect(%r, %r); '
               'print(json.dumps(aquarium.project(r, datetime.now(timezone.utc)), default=str, ensure_ascii=False))'
               % (tools, str(runtime), str(kontor)))
        r = subprocess.run([sys.executable, '-B', '-c', kod], capture_output=True, text=True, timeout=90, check=False)
        if r.returncode != 0:
            raise RuntimeError('aquarium-läsningen misslyckades')
        data = json.loads(r.stdout)
        return {'aquarium': _komprimera(data),
                'not': 'Genom Aquariums avgränsade läsning av Runtimes aktiva release, motor och bevakning.'}


def _komprimera(x, djup: int = 0):
    if djup > 5:
        return '…'
    if isinstance(x, dict):
        return {k: _komprimera(v, djup + 1) for k, v in list(x.items())[:40]}
    if isinstance(x, list):
        return [_komprimera(v, djup + 1) for v in x[:25]]
    if isinstance(x, str) and len(x) > 400:
        return x[:400] + '…'
    return x
