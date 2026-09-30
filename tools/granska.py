"""Kontorets separata granskning genom Runtimes läsarprofil, med läsarnas val i Flödet (LASARNAS-VAL-20260930).

    python3 -B tools/granska.py KATALOG [--modell MODELL] [--tid SEK]

KATALOG innehåller underlag.json i Runtimes manifestform, {"filer": [{"kalla": "/absolut/källa", "plats":
"RELATIV/PLATS", "vad": "vad filen är"}, ...]}, och fraga.md med granskningsfrågan. Verktyget kör den aktiva
Runtime-releasens egen kritikprofil (`runtime.web_critique`, Runtimes D034), samma läsare som Digitalas kritik. Den
kopierar underlaget till en arbetsyta utanför alla repon, läser bara, kör och hämtar ingenting och svarar i
granskningens schema (verdict, blocking_findings, summary, residual_notes). Claude eller Codex kör efter modellen.

Modellen är läsarnas val i Flödet, läst i processen med samma funktion som `partner.py lasare`. Finns ett val nekas en
annan --modell, och finns inget anger sessionen --modell. Ansträngningen följer Runtimes läsarprofil. Verktyget skriver
granskningens svarsform i KATALOG/schema.json. Utfallet skrivs i KATALOG/review.json, aldrig över ett tidigare. Det
innehåller modellen, utföraren och varifrån modellen kom, Runtimes körkatalog med kvittot (varje kopierad fil med
sha256) och svaret. Runtime hittas genom NR_HOST_ROOT eller kontorets Runtime-repo. Ett avbrott skickas vidare till
läsarprofilen, som avslutar sin modellsession och stänger sitt kvitto innan verktyget slutar.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import signal
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from partnern import konfig as kf  # noqa: E402
from partnern import modellkarta  # noqa: E402

# Runtimes schemadialekt (web_critique.check_schema): slutna objekt där varje egenskap krävs.
SCHEMA = {'type': 'object', 'additionalProperties': False,
          'required': ['verdict', 'blocking_findings', 'summary', 'residual_notes'],
          'properties': {'verdict': {'type': 'string', 'enum': ['approved', 'rejected', 'inconclusive']},
                         'blocking_findings': {'type': 'array', 'items': {'type': 'string'}},
                         'summary': {'type': 'string'},
                         'residual_notes': {'type': 'array', 'items': {'type': 'string'}}}}


class Nekad(Exception):
    pass


def modell_och_utforare(k, begard: str | None) -> tuple:
    """(modell, utförare, varifrån): läsarnas val går först och en annan begärd modell nekas; utan val krävs --modell."""
    try:
        val = modellkarta.lasarval(k)
    except ValueError as fel:
        raise Nekad(str(fel))
    if val['modell']:
        if begard and begard != val['modell']:
            raise Nekad('Läsarnas val i Flödet är %s, så en annan modell (%s) nekas. Ändra valet i Flödet eller ta bort '
                        'det, så väljer sessionen igen.' % (val['modell'], begard))
        return val['modell'], val['utforare'], 'readers'
    if not begard:
        raise Nekad('Läsarna har inget val i Flödet; ange --modell.')
    if begard.startswith('claude') and begard not in modellkarta.MODELL_ID:
        # utforare_for gör varje annat namn till Codex; ett felstavat Claude-namn får inte köras som Codex
        raise Nekad('Okänd Claude-modell: %s. Arbetsplatsens Claude-modeller: %s.'
                    % (begard, ', '.join(sorted(modellkarta.MODELL_ID))))
    utforare = modellkarta.utforare_for(begard)
    if utforare is None:
        raise Nekad('Okänd modell: %r' % begard)
    return begard, utforare, 'argument'


def runtime_rot(k) -> Path:
    rot = Path(os.environ.get('NR_HOST_ROOT') or (k.repon or {}).get('runtime') or '').resolve()
    if not (rot / '.runtime/ap10/active.json').is_file():
        raise Nekad('Runtime hittas inte (sätt NR_HOST_ROOT): %s' % rot)
    return rot


def aktiv_release(rot: Path) -> dict:
    """Den aktiva releasens egen kod, bunden till active.json:s sha256, som Digitalas kor_profil."""
    try:
        active = json.loads((rot / '.runtime/ap10/active.json').read_text())
        config = Path(active['config'])
        lika = hashlib.sha256(config.read_bytes()).hexdigest() == active['sha256']
    except (OSError, ValueError, KeyError, TypeError) as fel:
        raise Nekad('Runtimes aktiva release går inte att läsa: %s' % fel)
    if not lika:
        raise Nekad('active.json pekar på en konfiguration med annan sha256')
    kod = config.parent / 'runtime'
    if not (kod / 'runtime/web_critique.py').is_file():
        raise Nekad('Den aktiva releasen saknar läsarprofilen (runtime/web_critique.py): %s' % kod)
    return {'config': str(config), 'config_sha256': active['sha256'], 'code': str(kod),
            'python': str(rot / '.runtime/temporal-venv/bin/python')}


def miljo(rot: Path) -> dict:
    env = {n: v for n, v in os.environ.items() if n in ('PATH', 'HOME', 'USER', 'LOGNAME', 'TMPDIR')}
    env.update(NR_HOST_ROOT=str(rot), LC_ALL='C', LANG='C', PYTHONDONTWRITEBYTECODE='1')
    return env


def etikett(katalog: Path) -> str:
    """Runtimes etikettform (a-z, 0-9 och bindestreck, högst 40 tecken) ur katalogens namn."""
    namn = re.sub(r'[^a-z0-9]+', '-', katalog.name.lower()).strip('-')
    return ('granskning-' + namn)[:40].rstrip('-')


def kor(cmd: list, cwd: str, env: dict) -> tuple:
    """Kör läsarprofilen i en egen session: (utfall, stdout, stderr, avbruten). Ctrl-C, SIGTERM och SIGHUP skickas
    vidare en gång som SIGTERM, och verktyget väntar tills profilen har avslutat sin modellsession och sitt kvitto."""
    proc = subprocess.Popen(cmd, cwd=cwd, env=env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, text=True, start_new_session=True)
    avbrott = []

    def vidare(signum, frame):
        if not avbrott:
            avbrott.append(signum)
            try:
                proc.send_signal(signal.SIGTERM)
            except ProcessLookupError:
                pass

    fore = {s: signal.signal(s, vidare) for s in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP)}
    try:
        ut, fel = proc.communicate()
    finally:
        for s, h in fore.items():
            signal.signal(s, h)
    return proc.returncode, ut, fel, bool(avbrott)


def las_kvitto(run: Path, post: dict) -> None:
    """Runtimes kvitto, bara om det stämmer med sin sha256; svaret bara om kvittot säger giltigt och hashen stämmer."""
    try:
        data = (run / 'KVITTO.json').read_bytes()
        digest = (run / 'KVITTO.sha256').read_text().split()[0]
        kvitto = json.loads(data)
    except (OSError, ValueError, IndexError):
        post['problem'] = 'Runtimes kvitto saknas eller går inte att läsa'
        return
    if hashlib.sha256(data).hexdigest() != digest:
        post['problem'] = 'Runtimes kvitto stämmer inte med sin sha256'
        return
    session = kvitto.get('session') or {}
    post.update(receipt_sha256=digest, receipt_outcome=kvitto.get('outcome'), reported_model=session.get('reported_model'),
                active_release=kvitto.get('active_release'), workspace=str(run / 'arbetsyta'),
                files=len(kvitto.get('underlag') or []))
    if kvitto.get('outcome') != 'svar_giltigt':
        return
    try:
        svar = (run / 'svar.json').read_bytes()
    except OSError:
        post['problem'] = 'svar.json saknas trots ett giltigt svar i kvittot'
        return
    if hashlib.sha256(svar).hexdigest() != ((kvitto.get('outputs') or {}).get('svar.json') or {}).get('sha256'):
        post['problem'] = 'svar.json stämmer inte med kvittot'
        return
    try:
        post['answer'] = json.loads(svar)
    except ValueError:
        post['problem'] = 'svar.json går inte att läsa'


def granska(katalog: Path, begard: str | None, tid: int) -> int:
    underlag, fraga, schema, utfall = (katalog / n for n in ('underlag.json', 'fraga.md', 'schema.json', 'review.json'))
    for f in (underlag, fraga):
        if f.is_symlink() or not f.is_file():
            raise Nekad('%s saknas eller är en länk' % f)
    if utfall.exists() or utfall.is_symlink():
        raise Nekad('%s finns redan; en ny granskningsrunda får en egen katalog' % utfall)
    if schema.is_symlink():
        raise Nekad('%s är en länk' % schema)
    if not 60 <= tid <= 2700:
        raise Nekad('--tid är 60-2700 sekunder (Runtimes gräns för läsarprofilen)')
    k = kf.ladda()
    modell, utforare, ur = modell_och_utforare(k, begard)
    rot = runtime_rot(k)
    release = aktiv_release(rot)
    schema.write_text(json.dumps(SCHEMA, indent=1) + '\n')
    cmd = [release['python'], '-B', '-m', 'runtime.web_critique', '--underlag', str(underlag), '--fraga', str(fraga),
           '--schema', str(schema), '--utforare', utforare, '--modell', modell, '--etikett', etikett(katalog),
           '--tid', str(tid)]
    print('Granskar med %s (%s; %s) genom Runtimes läsarprofil.'
          % (modell, utforare, 'läsarnas val i Flödet' if ur == 'readers' else 'sessionens --modell'), flush=True)
    borjan = time.monotonic()
    kod, ut, fel, avbruten = kor(cmd, release['code'], miljo(rot))
    rad = {}
    try:
        rad = json.loads((ut.strip().splitlines() or [''])[-1])
    except ValueError:
        pass
    rad = rad if isinstance(rad, dict) else {}
    if rad.get('outcome') == 'vagrad' and not rad.get('run') and not avbruten:
        # Runtime nekade före körningen (till exempel underlagets form): ingen läsare startade och katalogen kan användas igen
        raise Nekad('Runtimes läsarprofil nekade: %s' % rad.get('reason'))
    post = {'schema': 'kontorsgranskning/1', 'model': modell, 'executor': utforare, 'model_from': ur,
            'runtime': {'host_root': str(rot), 'release_config_sha256': release['config_sha256'], 'code': release['code']},
            'argv': cmd, 'exit': kod, 'seconds': round(time.monotonic() - borjan, 1), 'interrupted': avbruten,
            'outcome': rad.get('outcome'), 'reason': rad.get('reason'), 'run': rad.get('run'), 'answer': None,
            'stderr_tail': fel.strip()[-500:]}
    if isinstance(post['run'], str):
        las_kvitto(Path(post['run']), post)
    with utfall.open('x', encoding='utf-8') as f:
        f.write(json.dumps(post, indent=1, ensure_ascii=False) + '\n')
    svar = post['answer']
    if svar:
        print('Dom: %s, %d blockerande fynd, %d anteckningar. Utfallet: %s'
              % (svar.get('verdict'), len(svar.get('blocking_findings') or []), len(svar.get('residual_notes') or []), utfall))
        return 0
    print('Inget giltigt svar (%s%s). Utfallet: %s' % (post['outcome'] or 'okänt utfall',
                                                      ': ' + post['problem'] if post.get('problem') else '', utfall))
    return 3 if avbruten else 1


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog='granska.py', description=__doc__.split('\n\n')[0])
    p.add_argument('katalog', help='katalogen med underlag.json och fraga.md; review.json skrivs där')
    p.add_argument('--modell', help='bara när läsarna inget val har i Flödet (annars måste den vara lika med valet)')
    p.add_argument('--tid', type=int, default=2700, help='sekunder för läsaren, 60-2700 (Runtimes gräns)')
    args = p.parse_args(argv)
    try:
        return granska(Path(args.katalog).resolve(), args.modell, args.tid)
    except Nekad as fel:
        print('Nekad: %s' % fel, file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
