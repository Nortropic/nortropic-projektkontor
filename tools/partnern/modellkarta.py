"""Flödet: Nortropics flöde som en karta, med modell och ansträngning vid varje hållplats (MODELLKARTA-20260929).

Varje hållplats följer ett av fem val. Kartan läser varje val ur den källa som faktiskt styr det:

- Partnern: arbetsplatsens egen inställning (`installningar.json`, samma som samtalsytans /model).
- Dina sessioner: två program, båda Johnnys. Claude Codes inställningsfil (`~/.claude/settings.json`; ansträngningen
  för modellen i `modelSettings[<modell>].effortLevel` går före grundvärdet `effortLevel`, Claude Codes egen regel)
  och Codex inställningsfil (`~/.codex/config.toml`, `model` och `model_reasoning_effort` överst i filen).
- Runtime: den aktiva releasens konfiguration och kod, läst med releasens egen kod genom samma avgränsade väg som
  Aquarium (`.runtime/temporal-venv`, NR_HOST_ROOT och NR_CONFIG_SHA256, tidsgräns).
- Läsarna: arbetsplatsens inställning `lasare`; utan val väljer sessionen vid varje körning.
- Bevakningen: Runtimes Codex-profil i den aktiva releasen.

Kartan erbjuder bara modeller och nivåer som bevisligen fungerar i programmet som kör hållplatsen (ägarens krav):
senaste mätningen (`modellmatning.json`, se modellmatning.py). Samma prövning görs när ett val sparas. Johnny väljer här
för partnern, sina två program och läsarna; valet gäller direkt. Runtimes och bevakningens val görs i Runtimes release
och visas här tills Runtime tar emot dem (steg 2). Ingen modell anropas och inga andra filer än de namngivna skrivs.
Okänt blir aldrig ett påhittat värde.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import threading
import time
from pathlib import Path

from . import modellmatning as mm
from .konfig import _SPARLAS, ANSTRANGNING, MODELLER, spara_modellval
from .lager import nu

MODELL_ID = {m['id'] for m in MODELLER}
MODELLNAMN = {m['id']: m['namn'] for m in MODELLER}
CODEX_NIVAORDNING = ('minimal', 'low', 'medium', 'high', 'xhigh', 'max', 'ultra')
# Claude Codes kortnamn om ingen mätning finns: "opus[1m]" gav den här sessionens modell claude-opus-5-5[1m]
# (Claude Code 2.1.280, 2026-09-29). Mätningen (modellmatning.KORTNAMN) går före.
KORTNAMN = {'opus': 'claude-opus-5-5'}
LANG_KONTEXT = '[1m]'
# Mätt 2026-09-29 med ett anrop per modell: Opus 5.5, Opus 5, Sonnet 5 och Fable 5.1 tar emot [1m]; Haiku 4.5 svarar
# 400 "The long context beta is not yet available for this subscription". Suffixet skrivs därför aldrig för Haiku.
UTAN_LANG_KONTEXT = {'claude-haiku-4-5-20251001'}
RUNTIME_SEKUNDER = 60   # en läsning av Runtimes release gäller en minut
PROV_TID = 30
SLUG = re.compile(r'\A[A-Za-z0-9][A-Za-z0-9._-]{0,63}\Z')
CODEX_TOPP = re.compile(r'^\s*\[')   # första tabellrubriken avslutar filens översta del

# Läses med den aktiva releasens egen kod, en gång och avgränsat. Ansträngningen är i dag fast i profilernas kod
# (D028): Claude i kommandot, Codex som REASONING_EFFORT. Finns ett uttryckligt val i releasen (steg 2) går det före.
PROBE = r"""import inspect, json, re
out = {}
from runtime.release import installed
from runtime.development_model import executors, models
from runtime import claude_profile, profile
import runtime.development_model as dm
c = installed()
out['config_sha256'] = c['config_sha256']
out['executors'] = executors(c)
out['models_run'] = models(c)
if hasattr(dm, 'efforts'):
    out['efforts'] = dm.efforts(c); out['efforts_source'] = 'release'
else:
    m = re.findall(r"'--effort',\s*'([a-z]+)'", inspect.getsource(claude_profile.command))
    out['efforts'] = {'claude': m[0] if len(set(m)) == 1 else None, 'codex': getattr(profile, 'REASONING_EFFORT', None)}
    out['efforts_source'] = 'code'
if hasattr(dm, 'watch'):
    out['watch'] = dm.watch(c); out['watch_source'] = 'release'
else:
    out['watch'] = {'executor': 'codex', 'model': getattr(profile, 'MODEL', None),
                    'effort': getattr(profile, 'REASONING_EFFORT', None)}
    out['watch_source'] = 'code'
print(json.dumps(out))
"""

_SKRIVLAS = threading.Lock()


# ------------------------------------------------------------------ mätningen: vad som bevisligen fungerar
def erbjud(k, program: str, niva: str | None = None) -> list:
    """[{id, namn, utforare, nivaer}] som fungerade i programmet enligt senaste mätningen, i fast ordning. Med `niva`
    bara modeller där just den nivån fungerade (för profiler vars ansträngning är fast)."""
    matning = mm.las(k.data)
    f = mm.fungerar(k.data).get(program, {})
    if program.startswith('claude'):
        ordning, namn, nivaordning, utforare = [m['id'] for m in MODELLER], MODELLNAMN, ANSTRANGNING, 'claude'
    else:
        ordning = [x.get('modell') for x in (matning.get('codex_modellista') or {}).get(program) or [] if isinstance(x, dict)]
        namn, nivaordning, utforare = mm.codex_namn(), CODEX_NIVAORDNING, 'codex'
    ut = []
    for m in ordning:
        if m in f and (niva is None or niva in f[m]):
            ut.append({'id': m, 'namn': namn.get(m, m), 'utforare': utforare,
                       'nivaer': [n for n in nivaordning if n in f[m]]})
    return ut


def bevisad(k, program: str, modell, niva) -> bool | None:
    """Om kombinationen fungerade i senaste mätningen; None om ingen mätning finns."""
    if not mm.las(k.data):
        return None
    return niva in mm.fungerar(k.data).get(program, {}).get(modell, [])


def _prova_erbjuden(k, program: str, modell, niva) -> None:
    if not mm.las(k.data):
        raise ValueError('Ingen mätning av modellerna finns ännu; kör python3 -B tools/partner.py matmodeller först.')
    if not bevisad(k, program, modell, niva):
        raise ValueError('%s med ansträngningen %s har inte fungerat i senaste mätningen och erbjuds inte.' % (modell, niva))


def _skriv_atomart(fil: Path, fore: bytes | None, text: bytes, prefix: str) -> bool:
    """Skriver filen atomärt om den fortfarande har innehållet `fore`; False om någon annan hann skriva. En länkad fil
    skrivs i länkens mål, så att länken står kvar. Mellan jämförelsen och namnbytet finns ett litet fönster där en
    samtidig skrivning (Claude Codes /effort) kan skrivas över; det går inte att stänga utan lås som programmen inte har."""
    fil = Path(os.path.realpath(fil))
    tmp = fil.with_name(prefix + str(os.getpid()))
    try:
        fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, 'wb') as f:
            f.write(text)
            f.flush()
            os.fsync(f.fileno())
        try:
            nu_data = fil.read_bytes()
        except FileNotFoundError:
            nu_data = None
        if nu_data != fore:
            return False
        if fore is not None:
            os.chmod(tmp, fil.stat().st_mode & 0o777)
        os.replace(tmp, fil)
        return True
    finally:
        if tmp.exists():
            tmp.unlink()


# ------------------------------------------------------------------ Dina sessioner: Claude Code
def _las_claude_code(fil: Path):
    """(innehåll, rådata) ur Claude Codes inställningsfil; ({}, None) om den saknas."""
    try:
        data = fil.read_bytes()
    except FileNotFoundError:
        return {}, None
    val = json.loads(data.decode('utf-8'))
    if not isinstance(val, dict):
        raise ValueError('Claude Codes inställningsfil har fel form.')
    return val, data


def upplost(k, modell) -> tuple:
    """(kanoniskt id eller None, med långt fönster) för Claude Codes modellvärde, t.ex. 'opus[1m]'."""
    if not isinstance(modell, str) or not modell:
        return None, False
    lang = modell.endswith(LANG_KONTEXT)
    bas = modell[:-len(LANG_KONTEXT)] if lang else modell
    if bas in MODELL_ID:
        return bas, lang
    matt = mm.kortnamn(k.data)
    return (matt.get(bas) if matt else KORTNAMN.get(bas)), lang


def las_claude_code(k) -> dict:
    fil = Path(k.claude_installningar)
    try:
        val, _ = _las_claude_code(fil)
    except (OSError, ValueError, UnicodeDecodeError):
        return {'status': 'olasbar', 'modell': None, 'anstrangning': None, 'varde': None,
                'skal': 'Claude Codes inställningsfil gick inte att läsa: läget är okänt.'}
    varde = val.get('model')
    modell, lang = upplost(k, varde)
    per_modell = ((val.get('modelSettings') or {}).get(modell) or {}) if modell else {}
    niva = per_modell.get('effortLevel') if isinstance(per_modell, dict) else None
    niva = niva if niva in ANSTRANGNING else (val.get('effortLevel') if val.get('effortLevel') in ANSTRANGNING else None)
    ut = {'status': 'ok' if modell and niva else 'ofullstandig', 'modell': modell, 'anstrangning': niva,
          'varde': varde if isinstance(varde, str) else None, 'langt_fonster': lang}
    if varde is None:
        ut['skal'] = 'Ingen modell står i Claude Codes inställningsfil; Claude Code väljer sin egen standard.'
    elif not modell:
        ut['skal'] = 'Claude Codes modellvärde %r är okänt för arbetsplatsen.' % str(varde)[:60]
    elif not niva:
        ut['skal'] = 'Ingen ansträngning står i Claude Codes inställningsfil för modellen; Claude Code väljer sin standard.'
    return ut


def spara_claude_code(k, modell: str, anstrangning: str) -> dict:
    """Johnnys val för sina Claude Code-sessioner (ägarens besked 2026-09-29: arbetsplatsen får skriva Claude Codes
    inställningar).

    Bara tre värden ändras: `model`, `effortLevel` och `modelSettings[<modell>].effortLevel`. Allt annat i filen står
    kvar i samma ordning. Filen skrivs atomärt och bara om den inte ändrats sedan den lästes (Claude Codes /effort
    skriver samma fil); annars prövas det om, högst tre gånger. Ett långt fönster ([1m]) behålls om det var valt."""
    _prova_erbjuden(k, 'claude_egen', modell, anstrangning)
    fil = Path(k.claude_installningar)
    with _SKRIVLAS:
        for _ in range(3):
            try:
                val, fore = _las_claude_code(fil)
            except (OSError, ValueError, UnicodeDecodeError):
                raise ValueError('Claude Codes inställningsfil går inte att läsa; inget ändrades.')
            if fore is not None and fore != (json.dumps(val, ensure_ascii=False, indent=2) + '\n').encode('utf-8'):
                raise ValueError('Claude Codes inställningsfil har en annan form än den arbetsplatsen skriver; inget ändrades. '
                                 'Välj i Claude Code i stället.')
            gammal = val.get('model') if isinstance(val.get('model'), str) else None
            _, lang = upplost(k, gammal)
            nytt = modell + (LANG_KONTEXT if lang and modell not in UTAN_LANG_KONTEXT else '')
            per = val.get('modelSettings') if isinstance(val.get('modelSettings'), dict) else {}
            egen = per.get(modell) if isinstance(per.get(modell), dict) else {}
            val['model'] = nytt
            val['effortLevel'] = anstrangning
            val['modelSettings'] = dict(per, **{modell: dict(egen, effortLevel=anstrangning)})
            text = (json.dumps(val, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
            if _skriv_atomart(fil, fore, text, '.settings.json.arbetsplatsen-'):
                return {'varde': nytt}
            time.sleep(0.2)
    raise ValueError('Claude Codes inställningsfil ändrades hela tiden medan den skrevs; inget ändrades. Försök igen.')


# ------------------------------------------------------------------ Dina sessioner: Codex
def _utan_strangar(rad: str) -> str:
    """Raden utan innehållet i enkla sträng­värden ("…" eller '…') och utan kommentar, för att räkna hakparenteser."""
    ut, i = [], 0
    while i < len(rad):
        c = rad[i]
        if c == '#':
            break
        if c in '"\'':
            j = rad.find(c, i + 1)
            while c == '"' and j > 0 and rad[j - 1] == '\\':
                j = rad.find(c, j + 1)
            if j < 0:
                return rad[:i] + c   # en sträng som inte slutar på raden: flerradig
            i = j + 1
            continue
        ut.append(c)
        i += 1
    return ''.join(ut)


def _codex_topp(text: str) -> int:
    """Antal rader i filens översta del, före första tabellrubriken. Hakparenteser följs genom filen, så att en rad inne
    i en lista över flera rader (som `notify = [ … ]`) aldrig tas för en rubrik. Står en sträng eller tabell över flera
    rader överst kastas ValueError: då skriver arbetsplatsen hellre ingenting än gissar var toppen slutar."""
    rader = text.split('\n')
    djup = 0
    for i, rad in enumerate(rader):
        ren = _utan_strangar(rad)
        if '"""' in rad or "\'\'\'" in rad or ren.endswith(('"', "'")) or ren.count('{') != ren.count('}'):
            raise ValueError('Codex inställningsfil har ett flerradigt värde överst; arbetsplatsen ändrar den inte.')
        if djup == 0 and CODEX_TOPP.match(rad):
            return i
        djup += ren.count('[') - ren.count(']')
        if djup < 0:
            raise ValueError('Codex inställningsfil har en lista överst som arbetsplatsen inte känner igen.')
    if djup:
        raise ValueError('Codex inställningsfil har en lista överst som inte slutar.')
    return len(rader)


def _codex_nyckel(text: str, nyckel: str):
    """(radindex, värde) för en nyckel i filens översta del (före första tabellen); (None, None) om den saknas.
    Står nyckeln där i en form som inte är ett enkelt strängvärde, eller står något flerradigt överst, kastas
    ValueError: då skrivs ingenting."""
    rad_for = re.compile(r'^\s*["\']?' + nyckel + r'["\']?\s*=')
    varde = re.compile(r'^\s*' + nyckel + r'\s*=\s*(?:"([^"\\\n]*)"|\'([^\'\n]*)\')\s*(?:#.*)?$')
    for i, rad in enumerate(text.split('\n')[:_codex_topp(text)]):
        if rad_for.match(rad):
            m = varde.match(rad)
            if not m:
                raise ValueError('Codex inställningsfil har %s i en form som arbetsplatsen inte känner igen; inget ändrades.'
                                 % nyckel)
            return i, m.group(1) if m.group(1) is not None else m.group(2)
    return None, None


def las_codex(k) -> dict:
    fil = Path(k.codex_installningar)
    try:
        text = fil.read_text('utf-8') if fil.exists() else ''
        _, modell = _codex_nyckel(text, 'model')
        _, niva = _codex_nyckel(text, 'model_reasoning_effort')
    except (OSError, UnicodeDecodeError, ValueError):
        return {'status': 'olasbar', 'modell': None, 'anstrangning': None,
                'skal': 'Codex inställningsfil gick inte att läsa: läget är okänt.'}
    ut = {'status': 'ok' if modell and niva else 'ofullstandig', 'modell': modell, 'anstrangning': niva}
    if not modell:
        ut['skal'] = 'Ingen modell står i Codex inställningsfil; Codex väljer sin egen standard.'
    elif not niva:
        ut['skal'] = 'Ingen ansträngning står i Codex inställningsfil; Codex väljer modellens standard.'
    return ut


def spara_codex(k, modell: str, anstrangning: str) -> dict:
    """Johnnys val för sina Codex-sessioner: bara raderna `model` och `model_reasoning_effort` överst i
    `config.toml` ändras (eller läggs först i filen om de saknas). Allt annat står kvar tecken för tecken. Samma
    atomära skrivning som för Claude Code, bara om filen inte ändrats sedan den lästes."""
    _prova_erbjuden(k, 'codex_egen', modell, anstrangning)
    if not SLUG.match(modell) or not re.match(r'\A[a-z]{2,12}\Z', anstrangning):
        raise ValueError('Ogiltigt värde.')
    fil = Path(k.codex_installningar)
    with _SKRIVLAS:
        for _ in range(3):
            try:
                fore = fil.read_bytes() if fil.exists() else None
                text = fore.decode('utf-8') if fore is not None else ''
            except (OSError, UnicodeDecodeError):
                raise ValueError('Codex inställningsfil går inte att läsa; inget ändrades.')
            rader = text.split('\n') if text else []
            nya = []
            for nyckel, varde in (('model', modell), ('model_reasoning_effort', anstrangning)):
                i, _ = _codex_nyckel('\n'.join(rader), nyckel)
                if i is None:
                    nya.append('%s = "%s"' % (nyckel, varde))
                else:
                    rader[i] = '%s = "%s"' % (nyckel, varde)
            ny_text = '\n'.join(nya + rader) if rader else '\n'.join(nya) + '\n'
            _prova_codex_resultat(text, ny_text, modell, anstrangning)
            if _skriv_atomart(fil, fore, ny_text.encode('utf-8'), '.config.toml.arbetsplatsen-'):
                return {'modell': modell, 'anstrangning': anstrangning}
            time.sleep(0.2)
    raise ValueError('Codex inställningsfil ändrades hela tiden medan den skrevs; inget ändrades. Försök igen.')


def _prova_codex_resultat(fore: str, efter: str, modell: str, anstrangning: str) -> None:
    """Innan något skrivs: den nya filen har exakt en rad för varje nyckel överst med det valda värdet, och allt från
    första tabellen och framåt är tecken för tecken detsamma som förut."""
    for nyckel, varde in (('model', modell), ('model_reasoning_effort', anstrangning)):
        topp = efter.split('\n')[:_codex_topp(efter)]
        traffar = [r for r in topp if re.match(r'^\s*["\']?' + nyckel + r'["\']?\s*=', r)]
        if len(traffar) != 1 or _codex_nyckel(efter, nyckel)[1] != varde:
            raise ValueError('Den nya Codex-filen blev inte som väntat; inget ändrades.')
    rest = lambda text: '\n'.join(text.split('\n')[_codex_topp(text):])
    if rest(fore) != rest(efter):
        raise ValueError('Den nya Codex-filen skulle ändra mer än de två raderna; inget ändrades.')


# ------------------------------------------------------------------ Läsarna
def _installningar(k) -> dict:
    fil = Path(k.data) / 'installningar.json'
    if not fil.is_file():
        return {}
    try:
        val = json.loads(fil.read_text('utf-8'))
    except ValueError:
        return {}
    return val if isinstance(val, dict) else {}


def utforare_for(modell) -> str | None:
    if modell in MODELL_ID:
        return 'claude'
    return 'codex' if isinstance(modell, str) and SLUG.match(modell) else None


def las_lasare(k) -> dict:
    """Läsarnas val (granskning, kritik och provare); modell None när sessionen väljer vid varje körning."""
    v = _installningar(k).get('lasare')
    modell = v.get('modell') if isinstance(v, dict) else None
    if not isinstance(modell, str) or not SLUG.match(modell):
        return {'modell': None, 'utforare': None}
    return {'modell': modell, 'utforare': utforare_for(modell)}


def lasarnas_erbjudande(k, rt: dict) -> list:
    """Läsarna kör genom Runtimes profiler, vars ansträngning i dag är fast: bara modeller som fungerade med just den
    nivån i Runtimes egna program."""
    niva = (rt.get('anstrangning') or {}) if rt.get('status') == 'ok' else {}
    ut = []
    for program, utf in (('claude_runtime', 'claude'), ('codex_runtime', 'codex')):
        if niva.get(utf):
            ut += [dict(m, nivaer=[niva[utf]]) for m in erbjud(k, program, niva[utf])]
    return ut


def spara_lasare(k, modell, rt: dict) -> dict:
    """Johnnys val för läsarna, i installningar.json under 'lasare' (övriga inställningar orörda). None tar bort valet,
    så att sessionen åter väljer. Ansträngningen följer Runtimes läsarprofil tills Runtime tar emot ett val (steg 2)."""
    if modell is not None and modell not in {m['id'] for m in lasarnas_erbjudande(k, rt)}:
        raise ValueError('%s har inte fungerat i Runtimes program i senaste mätningen och erbjuds inte för läsarna.' % modell)
    fil = Path(k.data) / 'installningar.json'
    with _SPARLAS:
        val = {}
        if fil.is_file():
            try:
                val = json.loads(fil.read_text('utf-8'))
            except ValueError:
                raise ValueError('installningar.json går inte att läsa; rätta filen först.')
            if not isinstance(val, dict):
                raise ValueError('installningar.json har fel form; rätta filen först.')
        if modell is None:
            val.pop('lasare', None)
        else:
            val['lasare'] = {'modell': modell}
        tmp = fil.with_name('.installningar.json.tmp')
        fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(json.dumps(val, ensure_ascii=False, indent=1) + '\n')
            f.flush()
            os.fsync(f.fileno())
        os.chmod(tmp, 0o600)
        os.replace(tmp, fil)
    return las_lasare(k)


# ------------------------------------------------------------------ Runtime
class RuntimeLasning:
    """Runtimes val ur den aktiva releasen, läst med releasens egen kod och sparat en minut."""

    def __init__(self, k, korare=None):
        self.k = k
        self._korare = korare or self._kor
        self._las = threading.Lock()
        self._senast = (0.0, None)

    def _kor(self) -> dict:
        import aquarium  # samma avgränsade läsväg som Aquarium: releasens egen kod, egen miljö, tidsgräns
        rot = Path((self.k.repon or {}).get('runtime') or '').absolute()
        aktiv = json.loads(aquarium._read_file(rot / '.runtime/ap10/active.json').decode('utf-8'))
        pekare = aktiv['config']
        if type(pekare) is not str or not pekare:
            raise ValueError('den aktiva releasen går inte att läsa')
        sok = Path(pekare) if pekare.startswith('/') else rot / pekare
        r = subprocess.run([str(rot / '.runtime/temporal-venv/bin/python'), '-B', '-c', PROBE],
                           cwd=str(sok.parent / 'runtime'), shell=False, capture_output=True, text=True,
                           encoding='utf-8', errors='replace', timeout=PROV_TID,
                           env=aquarium._environment(NR_HOST_ROOT=str(rot), NR_CONFIG_SHA256=str(aktiv['sha256'])))
        if r.returncode != 0:
            raise ValueError('releasens egen kod kunde inte läsa valen')
        return json.loads(r.stdout.strip().splitlines()[-1])

    def las(self) -> dict:
        with self._las:
            tid, varde = self._senast
            if varde is not None and time.monotonic() - tid < RUNTIME_SEKUNDER:
                return varde
        try:
            v = self._korare()
            ut = {'status': 'ok', 'lasttid': nu(), **_runtime_varden(v)}
        except Exception:
            ut = {'status': 'olasbar', 'lasttid': nu()}
        with self._las:
            self._senast = (time.monotonic(), ut)
        return ut


def _runtime_varden(v: dict) -> dict:
    """Bara de fält kartan visar, med typer prövade; ett värde som inte går att pröva blir None."""
    def text(x):
        return x if isinstance(x, str) and SLUG.match(x) else None
    alla_nivaer = set(ANSTRANGNING) | set(CODEX_NIVAORDNING)
    utforare = v.get('executors') if isinstance(v.get('executors'), dict) else {}
    modeller = v.get('models_run') if isinstance(v.get('models_run'), dict) else {}
    niva = v.get('efforts') if isinstance(v.get('efforts'), dict) else {}
    vakt = v.get('watch') if isinstance(v.get('watch'), dict) else {}
    roller = {r: u for r, u in utforare.items() if isinstance(r, str) and u in ('claude', 'codex')}
    ensam = set(roller.values())
    return {'config': (text(v.get('config_sha256')) or '')[:8] or None,
            'roller': roller,
            'utforare': ensam.pop() if len(ensam) == 1 else None,
            'modeller': {u: text(m) for u, m in modeller.items() if u in ('claude', 'codex')},
            'anstrangning': {u: n for u, n in niva.items() if u in ('claude', 'codex') and n in alla_nivaer},
            'anstrangning_ur': 'release' if v.get('efforts_source') == 'release' else 'kod',
            'bevakning': {'utforare': vakt.get('executor') if vakt.get('executor') in ('claude', 'codex') else None,
                          'modell': text(vakt.get('model')),
                          'anstrangning': vakt.get('effort') if vakt.get('effort') in alla_nivaer else None,
                          'ur': 'release' if v.get('watch_source') == 'release' else 'kod'}}


# ------------------------------------------------------------------ kartan
def karta(server) -> dict:
    """De fem valen och startvakten, var och en ur sin källa, med det som bevisligen fungerar. Hållplatserna står i
    ytan (karta.js)."""
    k = server.k
    rt = server.runtime_val.las()
    matning = mm.las(k.data)
    ut = {'lasttid': nu(), 'val': {},
          'matning': {'matt': matning.get('matt'), 'program': {n: (b or {}).get('version') for n, b in
                                                                (matning.get('binarer') or {}).items()}}
          if matning else None}
    ingen_matning = (None if matning else
                     'Ingen mätning av modellerna finns ännu, så inget erbjuds: kör python3 -B tools/partner.py matmodeller.')
    ut['val']['partner'] = {
        'namn': 'Partnern', 'modell': k.modell.huvud, 'anstrangning': k.modell.anstrangning, 'utforare': 'claude',
        'status': 'ok', 'valbar': bool(matning), 'kalla': 'arbetsplatsen', 'erbjud': erbjud(k, 'claude_egen'),
        'bevisad': bevisad(k, 'claude_egen', k.modell.huvud, k.modell.anstrangning),
        'kommer': erbjud(k, 'codex_egen'), 'skal': ingen_matning,
        'var': 'Gäller direkt, från nästa svar.',
        'kraver': 'Codex kräver partnerns Codex-drivare, som byggs härnäst.'}
    cc, cx = las_claude_code(k), las_codex(k)
    ut['val']['sessioner'] = {
        'namn': 'Dina sessioner', 'valbar': bool(matning), 'kalla': 'program', 'skal': ingen_matning,
        'var': 'Programmens egna inställningar. Nya sessioner får valet direkt.',
        'program': {
            'claude_code': dict(cc, namn='Claude Code', utforare='claude', erbjud=erbjud(k, 'claude_egen'),
                                bevisad=bevisad(k, 'claude_egen', cc['modell'], cc['anstrangning'])),
            'codex': dict(cx, namn='Codex', utforare='codex', erbjud=erbjud(k, 'codex_egen'),
                          bevisad=bevisad(k, 'codex_egen', cx['modell'], cx['anstrangning']))}}
    niva = rt.get('anstrangning', {}) if rt['status'] == 'ok' else {}
    if rt['status'] == 'ok':
        u = rt['utforare']
        modell = rt['modeller'].get(u) if u else None
        ut['val']['runtime'] = {
            'namn': 'Runtime', 'status': 'ok' if u else 'blandad', 'utforare': u, 'modell': modell,
            'anstrangning': niva.get(u) if u else None, 'roller': rt['roller'], 'config': rt['config'],
            'valbar': False, 'kalla': 'runtime',
            'bevisad': bevisad(k, u + '_runtime', modell, niva.get(u)) if u else None,
            'var': 'Väljs i Runtimes release; ansträngningen är %s.' % (
                'releasens val' if rt['anstrangning_ur'] == 'release' else 'fast i koden'),
            'varfor_inte': 'Blir valbart här i steg 2 och aktiveras då av sig självt när Runtime är ledig.'}
        b = rt['bevakning']
        ut['val']['bevakning'] = {
            'namn': 'Bevakningen', 'status': 'ok' if b['modell'] else 'ofullstandig', 'utforare': b['utforare'],
            'modell': b['modell'], 'anstrangning': b['anstrangning'], 'valbar': False, 'kalla': 'runtime',
            'bevisad': bevisad(k, b['utforare'] + '_runtime', b['modell'], b['anstrangning']) if b['utforare'] else None,
            'var': 'Fast i Runtimes kod.' if b['ur'] == 'kod' else 'Väljs i Runtimes release.',
            'varfor_inte': 'Blir valbart här i steg 2, med Claude eller Codex.'}
    else:
        for namn, rubrik in (('runtime', 'Runtime'), ('bevakning', 'Bevakningen')):
            ut['val'][namn] = {'namn': rubrik, 'status': 'olasbar', 'modell': None, 'anstrangning': None,
                               'valbar': False, 'kalla': 'runtime',
                               'var': 'Runtimes aktiva release gick inte att läsa just nu: läget är okänt.'}
    la = las_lasare(k)
    ut['val']['lasare'] = {
        'namn': 'Läsarna', 'status': 'ok' if la['modell'] else 'sessionen', 'modell': la['modell'],
        'utforare': la['utforare'], 'anstrangning': niva.get(la['utforare']) if la['modell'] else None,
        'valbar': bool(matning) and rt['status'] == 'ok', 'kalla': 'arbetsplatsen', 'erbjud': lasarnas_erbjudande(k, rt),
        'bevisad': (bevisad(k, la['utforare'] + '_runtime', la['modell'], niva.get(la['utforare']))
                    if la['modell'] and rt['status'] == 'ok' else None),
        'skal': ingen_matning,
        'var': ('Granskningen, kritiken och provarna hämtar valet. Ansträngningen följer Runtimes läsarprofil.')
               if la['modell'] else 'Sessionen väljer vid varje körning.'}
    # Startvakten tar Runtimes drivande roll (utförare och modell) och har i dag en egen ansträngning.
    driver = rt.get('roller', {}).get('driver') if rt['status'] == 'ok' else None
    smodell = rt['modeller'].get(driver) if driver else None
    ut['startvakt'] = {'pa': server.startvakt.paslagen(), 'utforare': driver, 'modell': smodell,
                       'anstrangning': k.startvakt_anstrangning,
                       'bevisad': bevisad(k, driver + '_runtime', smodell, k.startvakt_anstrangning) if driver else None}
    return ut


def spara(server, val: str, modell, anstrangning) -> tuple:
    """Johnnys val på kartan. Returnerar (före, efter) för journalen; kastar ValueError med ett läsbart skäl."""
    k = server.k
    if val == 'partner':
        fore = {'modell': k.modell.huvud, 'anstrangning': k.modell.anstrangning}
        if modell not in MODELL_ID:
            raise ValueError('Partnern kör i dag bara på Claude; Codex kräver partnerns Codex-drivare.')
        _prova_erbjuden(k, 'claude_egen', modell, anstrangning)
        ny = spara_modellval(k, str(modell), str(anstrangning))
        return fore, {'modell': ny['huvud'], 'anstrangning': ny['anstrangning']}
    if val == 'claude_code':
        fore = las_claude_code(k)
        ny = spara_claude_code(k, str(modell or ''), str(anstrangning or ''))
        return ({'modell': fore.get('modell'), 'anstrangning': fore.get('anstrangning'), 'varde': fore.get('varde')},
                {'modell': modell, 'anstrangning': anstrangning, 'varde': ny['varde']})
    if val == 'codex':
        fore = las_codex(k)
        spara_codex(k, str(modell or ''), str(anstrangning or ''))
        return ({'modell': fore.get('modell'), 'anstrangning': fore.get('anstrangning')},
                {'modell': modell, 'anstrangning': anstrangning})
    if val == 'lasare':
        fore = las_lasare(k)
        ny = spara_lasare(k, modell if modell else None, server.runtime_val.las())
        return {'modell': fore['modell']}, {'modell': ny['modell']}
    if val in ('runtime', 'bevakning'):
        raise ValueError('Runtimes val görs i Runtimes release; det blir valbart här när Runtime tar emot valet.')
    raise ValueError('Okänt val.')
