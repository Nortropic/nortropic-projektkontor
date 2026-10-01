"""Fryst dokumentfall för tools/dokumentpost.py (DOKUMENTVAG-20261001). Körs bara i Runtimes utfärdares sandlåda på
kandidatens oföränderliga källkopia: argv[1] är källkatalogen, stdin ett falls indata {"filer": [docs/...md, ...]}.

Skriver den faktiska observationen som JSON och avgör ingenting; värden jämför med sin privata förväntan:
- varje namngiven fils sha256 och storlek, och att den är en vanlig fil under docs/ som slutar på .md;
- planens ÄGARENS TUR läst med Aquariums grammatik (tools/aquarium.py parse_owner_turn): radernas antal och sha256,
  och om varje radformad rad i planen ingår i det Aquarium läser;
- beslutsloggens sista rubrik och antalet rubriker.
Ingen modell, inget nät, ingen kandidatkod importeras: filerna läses som data. Inget som skrivs beror på arbetskatalogen.
"""
import hashlib
import json
from pathlib import Path
import re
import sys

KALLA = Path(sys.argv[1]).resolve()
FALL = json.loads(sys.stdin.read() or '{}')
RAD = ('- [beslut] ', '- [operatörshandling] ')
DOKUMENT = re.compile(r'\Adocs/(?:[A-Za-z0-9._-]+/)*[A-Za-z0-9._-]+\.md\Z')


def agarens_tur(plan):
    """tools/aquarium.py parse_owner_turn(raw=True), ordagrant i sin grammatik: varje rad som nämner ÄGARENS TUR öppnar
    ett block, och första rad som inte är en rad i ägarens tur stänger det."""
    rader, inne = [], False
    for line in plan.splitlines():
        stripped = line.strip()
        if 'ÄGARENS TUR' in stripped:
            inne = True
            continue
        if not inne:
            continue
        if not stripped.startswith(RAD):
            inne = False
            continue
        rader.append(stripped)
    return rader


def main():
    filer = {}
    for vag in FALL.get('filer') or []:
        delar = Path(vag).parts if isinstance(vag, str) else ()
        sti = KALLA.joinpath(*delar) if delar else KALLA
        regelratt = (bool(delar) and bool(DOKUMENT.match(vag)) and '..' not in delar
                     and not any(KALLA.joinpath(*delar[:i + 1]).is_symlink() for i in range(len(delar))) and sti.is_file())
        data = sti.read_bytes() if regelratt else b''
        filer[vag] = {'regelratt': regelratt, 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}
    plan = (KALLA / 'docs/plan.md').read_text(encoding='utf-8')
    rader = agarens_tur(plan)
    radformade = [line.strip() for line in plan.splitlines() if line.strip().startswith(RAD)]
    beslut = (KALLA / 'docs/decisions.md').read_text(encoding='utf-8')
    rubriker = [line[3:].split(' — ')[0].strip() for line in beslut.splitlines() if line.startswith('## ')]
    print(json.dumps({'filer': filer,
                      'agarens_tur': {'rader': len(rader), 'sha256': hashlib.sha256('\n'.join(rader).encode()).hexdigest(),
                                      'varje_radformad_rad_last': rader == radformade},
                      'beslut': {'rubriker': len(rubriker), 'sista': rubriker[-1] if rubriker else None}},
                     ensure_ascii=False, sort_keys=True))


main()
