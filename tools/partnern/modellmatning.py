"""Vilka modeller och ansträngningsnivåer fungerar på Johnnys abonnemang? Ett kort anrop per modell och nivå.

Ägarens krav (MODELLKARTA-20260929, tillägget om Codex): kartan erbjuder bara modeller och nivåer som bevisligen
fungerar. Varje kombination prövas med programmet som faktiskt kör den:

- claude_egen: Johnnys Claude Code (partnern och Dina sessioner);
- claude_runtime: Runtimes fastlåsta Claude Code (Runtimes roller, läsarna, bevakningen och startvakten);
- codex_egen: Johnnys Codex (Dina sessioner, och partnern på Codex);
- codex_runtime: Runtimes fastlåsta Codex.

Claudes modeller är arbetsplatsens lista (konfig.MODELLER) med nivåerna i ANSTRANGNING. Codex modeller och nivåer är
de som Codex egen modellista visar (`~/.codex/models_cache.json`, synliga modeller). Varje anrop är en fråga utan
verktyg ("Svara bara med ordet ok."), utan MCP-servrar och tillägg, i en tom katalog. Resultatet skrivs i
`<data>/modellmatning.json` och är kvittot: tid, program med version, och varje kombinations utfall och felsvar.
"""
from __future__ import annotations

import concurrent.futures
import json
import os
import re
import subprocess
import tempfile
import time
from pathlib import Path

from .konfig import ANSTRANGNING, MODELLER, STARTVAKT_BINARER
from .lager import nu

FRAGA = 'Svara bara med ordet ok.'
KORTNAMN = ('opus', 'sonnet', 'haiku', 'fable')  # Claude Codes kortnamn prövas också; svaret visar vad de löses upp till
HJALPMODELL = 'claude-haiku-4-5-20251001'       # Claude Code använder den för småsysslor i varje anrop
SEKUNDER = 240
SAMTIDIGA = 4
OMPROV = 2          # ett fel som inte är ett tydligt nej prövas om, ett i taget, högst två gånger till
TYDLIGT_NEJ = re.compile(r'(?i)not supported|does not support|invalid_request_error|unknown model|model_not_found'
                         r'|not yet available')
CODEX_AVSTANGT = ('apps', 'computer_use', 'browser_use', 'browser_use_external', 'browser_use_full_cdp_access',
                  'in_app_browser', 'image_generation', 'multi_agent', 'plugins')  # samma som Runtimes Codex-väg


def codex_egen() -> str:
    for kandidat in ('/opt/homebrew/bin/codex', '/usr/local/bin/codex', str(Path.home() / '.local/bin/codex')):
        if os.path.isfile(kandidat) and os.access(kandidat, os.X_OK):
            return kandidat
    return 'codex'


def codex_modeller(cache: Path | None = None) -> list:
    """[(modell, [nivåer])] för Codex synliga modeller, i Codex egen ordning."""
    d = json.loads((cache or Path.home() / '.codex/models_cache.json').read_text('utf-8'))
    ut = []
    for m in sorted(d.get('models') or [], key=lambda x: x['priority'] if type(x.get('priority')) is int else 999):
        slug = m.get('slug')
        if m.get('visibility') != 'list' or not isinstance(slug, str) or not re.match(r'\A[a-z0-9][a-z0-9._-]{0,63}\Z', slug):
            continue
        nivaer = [x.get('effort') if isinstance(x, dict) else x for x in m.get('supported_reasoning_levels') or []]
        ut.append((slug, [n for n in nivaer if isinstance(n, str) and re.match(r'\A[a-z]{2,12}\Z', n)]))
    return ut


def _codex_avstangt_config() -> list:
    """Johnnys MCP-servrar och tillägg stängs av i mätningen, som i Runtimes Codex-väg: bara modellen prövas."""
    try:
        text = (Path.home() / '.codex/config.toml').read_text('utf-8')
    except OSError:
        return []
    ut = []
    for namn in re.findall(r'^\[mcp_servers\.([\w-]+)\]$', text, re.M):
        ut += ['-c', 'mcp_servers.' + namn + '.enabled=false']
    for namn in re.findall(r'^\[plugins\."([^"\n]+)"\]$', text, re.M):
        ut += ['-c', 'plugins.' + json.dumps(namn) + '.enabled=false']
    return ut


def version(binar: str) -> str | None:
    try:
        r = subprocess.run([binar, '--version'], capture_output=True, text=True, timeout=30)
        return (r.stdout or r.stderr).strip().splitlines()[0][:80] if r.returncode == 0 else None
    except (OSError, subprocess.SubprocessError, IndexError):
        return None


def prova_claude(binar: str, modell: str, niva: str | None, katalog: str) -> dict:
    argv = [binar, '-p', '--model', modell] + (['--effort', niva] if niva else []) + [
        '--output-format', 'json', '--setting-sources', 'user',
        '--strict-mcp-config', '--mcp-config', '{"mcpServers":{}}', '--no-session-persistence', '--tools', '']
    start = time.monotonic()
    try:
        r = subprocess.run(argv, input=FRAGA, capture_output=True, text=True, timeout=SEKUNDER, cwd=katalog)
    except subprocess.TimeoutExpired:
        return {'ok': False, 'fel': 'ingen svar inom %d s' % SEKUNDER, 'sekunder': SEKUNDER}
    sek = round(time.monotonic() - start, 1)
    try:
        d = json.loads(r.stdout)
    except ValueError:
        return {'ok': False, 'fel': ((r.stderr or r.stdout).strip() or 'kod %d' % r.returncode)[:300], 'sekunder': sek}
    ok = d.get('is_error') is False and d.get('subtype') == 'success' and bool(str(d.get('result') or '').strip())
    rapporterad = sorted((d.get('modelUsage') or {}).keys())
    egna = [m for m in rapporterad if m != HJALPMODELL] or rapporterad
    return {'ok': ok, 'fel': None if ok else str(d.get('result') or d.get('subtype'))[:300], 'sekunder': sek,
            'rapporterad': rapporterad, 'upplost': egna[0].replace('[1m]', '') if len(egna) == 1 else None}


def prova_codex(binar: str, modell: str, niva: str, katalog: str) -> dict:
    argv = [binar, '-c', 'model=' + json.dumps(modell), '-c', 'approval_policy="never"',
            '-c', 'model_reasoning_effort=' + json.dumps(niva), '-c', 'web_search="disabled"']
    for f in CODEX_AVSTANGT:
        argv += ['--disable', f]
    argv += _codex_avstangt_config() + ['-s', 'read-only', 'exec', '--json', '--ephemeral', '--skip-git-repo-check',
                                        '-C', katalog, '-']
    start = time.monotonic()
    try:
        r = subprocess.run(argv, input=FRAGA, capture_output=True, text=True, timeout=SEKUNDER, cwd=katalog)
    except subprocess.TimeoutExpired:
        return {'ok': False, 'fel': 'ingen svar inom %d s' % SEKUNDER, 'sekunder': SEKUNDER}
    sek = round(time.monotonic() - start, 1)
    svar, fel = None, None
    for rad in r.stdout.splitlines():
        try:
            h = json.loads(rad)
        except ValueError:
            continue
        typ = h.get('type') or h.get('msg', {}).get('type')
        item = h.get('item') or {}
        if typ == 'item.completed' and item.get('type') in ('agent_message', 'assistant_message'):
            svar = item.get('text') or svar
        elif typ in ('error', 'turn.failed'):
            fel = json.dumps(h.get('error') or h.get('message') or h, ensure_ascii=False)[:300]
    ok = r.returncode == 0 and fel is None and bool((svar or '').strip())
    return {'ok': ok, 'fel': None if ok else (fel or (r.stderr.strip()[-300:] if r.stderr else 'kod %d' % r.returncode)),
            'sekunder': sek}


def mat(data: Path, claude_egen: str, logg=print, forsok: bool = False, binarer: dict | None = None) -> dict:
    """Mäter alla kombinationer och skriver <data>/modellmatning.json (utom med forsok, som prövar en kombination per
    program och inte skriver något). Returnerar kvittot.

    Codex modellista beror på versionen: varje Codex skriver om den delade `models_cache.json` med sin egen lista vid
    varje anrop (mätt 2026-09-29: 0.159.0 visar gpt-6.1-sol, 0.155.1 inte). Därför får varje Codex-program ett eget
    uppvärmningsanrop, och dess lista läses direkt efteråt."""
    binarer = binarer or {'claude_egen': claude_egen, 'claude_runtime': STARTVAKT_BINARER['claude'][0],
                          'codex_egen': codex_egen(), 'codex_runtime': STARTVAKT_BINARER['codex'][0]}
    kvitto = {'schema': 'modellmatning/2', 'matt': nu(), 'fraga': FRAGA,
              'binarer': {k: {'sokvag': v, 'version': version(v)} for k, v in binarer.items()},
              'codex_modellista': {}, 'resultat': []}
    with tempfile.TemporaryDirectory(prefix='modellmatning-') as katalog:
        for namn, binar in binarer.items():
            if namn.startswith('codex'):
                try:
                    kanda = codex_modeller()
                except (OSError, ValueError):
                    kanda = []
                prova_codex(binar, kanda[0][0] if kanda else 'gpt-6-astra', 'low', katalog)  # programmet skriver sin lista
                try:
                    kvitto['codex_modellista'][namn] = [{'modell': m, 'nivaer': n} for m, n in codex_modeller()]
                except (OSError, ValueError):
                    kvitto['codex_modellista'][namn] = []
        jobb = []
        for namn, binar in binarer.items():
            lista = [(x['modell'], x['nivaer']) for x in kvitto['codex_modellista'].get(namn, [])]
            if forsok:
                jobb.append((namn, binar, MODELLER[0]['id'], 'low') if namn.startswith('claude') else (namn, binar, lista[0][0], 'low'))
            elif namn.startswith('claude'):
                jobb += [(namn, binar, m['id'], n) for m in MODELLER for n in ANSTRANGNING]
                jobb += [(namn, binar, kort, None) for kort in KORTNAMN]
            else:
                jobb += [(namn, binar, m, n) for m, nivaer in lista for n in nivaer]

        def kor(j):
            namn, binar, modell, niva = j
            ut = (prova_claude if namn.startswith('claude') else prova_codex)(binar, modell, niva, katalog)
            logg('%-15s %-28s %-7s %s %s %s' % (namn, modell, niva or '-', 'ok ' if ut['ok'] else 'FEL', ut.get('sekunder'),
                                                (ut.get('fel') or '') + (' -> ' + ut['upplost'] if niva is None and ut.get('upplost') else '')))
            return dict({'program': namn, 'modell': modell, 'niva': niva}, **ut)
        with concurrent.futures.ThreadPoolExecutor(max_workers=SAMTIDIGA) as pool:
            resultat = list(pool.map(kor, jobb))
        # Ett fel som kan vara tillfälligt (t.ex. 403 medan förbindelsen återupptas) prövas om ett i taget; bara ett
        # anrop som till slut lyckas räknas som bevis. Alla försök står i kvittot.
        for i, r in enumerate(resultat):
            forsoken = [{k2: v for k2, v in r.items() if k2 in ('ok', 'fel', 'sekunder')}]
            while not resultat[i]['ok'] and not TYDLIGT_NEJ.search(resultat[i].get('fel') or '') and len(forsoken) <= OMPROV:
                time.sleep(3)
                resultat[i] = kor((r['program'], binarer[r['program']], r['modell'], r['niva']))
                forsoken.append({k2: v for k2, v in resultat[i].items() if k2 in ('ok', 'fel', 'sekunder')})
            resultat[i]['forsok'] = forsoken
        kvitto['resultat'] = resultat
    kvitto['klar'] = nu()
    if forsok:
        return kvitto
    fil = Path(data) / 'modellmatning.json'
    tmp = fil.with_name('.modellmatning.json.tmp')
    tmp.write_text(json.dumps(kvitto, ensure_ascii=False, indent=1) + '\n', 'utf-8')
    os.replace(tmp, fil)
    return kvitto


def las(data: Path) -> dict:
    """Senaste mätningens kvitto, eller {} om ingen mätning finns."""
    try:
        d = json.loads((Path(data) / 'modellmatning.json').read_text('utf-8'))
    except (OSError, ValueError):
        return {}
    return d if isinstance(d, dict) and d.get('schema') == 'modellmatning/2' else {}


def codex_namn(cache: Path | None = None) -> dict:
    """{modell: visningsnamn} ur Codex egen modellista; tomt om den inte går att läsa."""
    try:
        d = json.loads((cache or Path.home() / '.codex/models_cache.json').read_text('utf-8'))
    except (OSError, ValueError):
        return {}
    return {m['slug']: m['display_name'] for m in d.get('models') or []
            if isinstance(m.get('slug'), str) and isinstance(m.get('display_name'), str)}


def fungerar(data: Path) -> dict:
    """{program: {modell: [nivåer som fungerade]}} ur senaste mätningen; tomt om ingen mätning finns."""
    ut = {}
    for r in las(data).get('resultat') or []:
        if r.get('ok') is True and isinstance(r.get('program'), str) and r.get('niva'):
            ut.setdefault(r['program'], {}).setdefault(r['modell'], []).append(r['niva'])
    return ut


def kortnamn(data: Path, program: str = 'claude_egen') -> dict:
    """{kortnamn: modell} så som Claude Code löste upp dem i senaste mätningen; tomt om ingen mätning finns."""
    return {r['modell']: r['upplost'] for r in las(data).get('resultat') or []
            if r.get('program') == program and r.get('niva') is None and r.get('ok') is True and r.get('upplost')}
