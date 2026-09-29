"""Nortropic.app: en klickbar ingång till arbetsplatsen på ägarens Mac.

Appen är ett litet programpaket vars enda program är ett skalskript med fasta sökvägar. Ett klick startar tjänsten om den
inte kör (`partner.py start`) och öppnar arbetsplatsen inloggad (`partner.py oppna`). Appen innehåller ingen nyckel,
startar inget vid inloggning och ändrar inga systeminställningar; nyckeln stannar i hemlighetsmappen och läses av
`partner.py oppna` som förut. Ikonen ritas ur en SVG med macOS egna verktyg (qlmanage, sips, iconutil); saknas de eller
misslyckas något blir appen utan egen ikon men fungerar ändå.
"""
from __future__ import annotations

import json
import os
import plistlib
import shlex
import shutil
import subprocess
import tempfile
from pathlib import Path

NAMN = 'Nortropic'
ID = 'se.nortropic.arbetsplats'
MARKOR = 'nortropic-app.json'  # bara ett paket med denna fil får ersättas
PATH = '/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin'
IKON_SVG = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1024 1024">'
            '<rect x="100" y="100" width="824" height="824" rx="185" fill="#17211f"/>'
            '<g transform="translate(256 256) scale(16)" stroke="#e8875f" stroke-width="3" stroke-linecap="round" fill="none">'
            '<path d="M16 3.5v8.5M16 20v8.5M3.5 16H12M20 16h8.5M7.2 7.2l5.9 5.9M18.9 18.9l5.9 5.9M7.2 24.8l5.9-5.9M18.9 13.1l5.9-5.9"/>'
            '</g></svg>')
STORLEKAR = ((16, 1), (16, 2), (32, 1), (32, 2), (128, 1), (128, 2), (256, 1), (256, 2), (512, 1), (512, 2))


def skript(kontor: Path, python: str) -> str:
    k, py = shlex.quote(str(kontor)), shlex.quote(python)
    return ('#!/bin/sh\n'
            '# Nortropic: startar arbetsplatsen om den inte kör och öppnar den inloggad. Skapad av tools/partner.py app.\n'
            'export PATH=%s\n'
            'unset PARTNER_DATA PARTNER_PORT PARTNER_HEMLIGHETER PARTNER_PROV_DOLJ PARTNER_STARTVAKT\n'
            'cd %s || exit 1\n'
            '%s -B tools/partner.py start >/dev/null 2>&1\n'
            'if ! %s -B tools/partner.py oppna >/dev/null 2>&1; then\n'
            '  /usr/bin/osascript -e \'display alert "Nortropic kunde inte startas" message '
            '"Kör python3 -B tools/partner.py status i Terminal i kontorets repo för att se varför."\' >/dev/null 2>&1\n'
            '  exit 1\n'
            'fi\n' % (PATH, k, py, py))


def _ikon(resurser: Path) -> bool:
    """Ritar Nortropic.icns ur IKON_SVG. Sant om ikonen blev av."""
    with tempfile.TemporaryDirectory(prefix='nortropic-ikon-') as t:
        t = Path(t)
        svg = t / 'ikon.svg'
        svg.write_text(IKON_SVG)
        try:
            subprocess.run(['qlmanage', '-t', '-s', '1024', '-o', str(t), str(svg)], capture_output=True, timeout=60)
            png = t / 'ikon.svg.png'
            if not png.exists():
                return False
            ikonset = t / 'Nortropic.iconset'
            ikonset.mkdir()
            for storlek, skala in STORLEKAR:
                namn = 'icon_%dx%d%s.png' % (storlek, storlek, '@2x' if skala == 2 else '')
                r = subprocess.run(['sips', '-z', str(storlek * skala), str(storlek * skala), str(png), '--out',
                                    str(ikonset / namn)], capture_output=True, timeout=60)
                if r.returncode != 0:
                    return False
            r = subprocess.run(['iconutil', '-c', 'icns', str(ikonset), '-o', str(resurser / (NAMN + '.icns'))],
                               capture_output=True, timeout=60)
            return r.returncode == 0
        except (OSError, subprocess.SubprocessError):
            return False


def bygg(mal: Path, kontor: Path, python: str, ikon: bool = True) -> dict:
    """Skapar (eller ersätter ett tidigare skapat) Nortropic.app i mal. Ett främmande paket rörs aldrig."""
    mal = Path(mal)
    if mal.is_symlink() or (mal.exists() and not (mal / 'Contents' / 'Resources' / MARKOR).is_file()):
        raise ValueError('%s finns redan och är inte skapad av partner.py app; den rörs inte.' % mal)
    mal.parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix='.nortropic-app-', dir=str(mal.parent)))
    try:
        paket = tmp / (NAMN + '.app')
        macos, resurser = paket / 'Contents' / 'MacOS', paket / 'Contents' / 'Resources'
        macos.mkdir(parents=True)
        resurser.mkdir()
        prog = macos / NAMN
        prog.write_text(skript(kontor, python))
        prog.chmod(0o755)
        fick_ikon = bool(ikon) and _ikon(resurser)
        info = {'CFBundleName': NAMN, 'CFBundleDisplayName': NAMN, 'CFBundleIdentifier': ID,
                'CFBundleExecutable': NAMN, 'CFBundlePackageType': 'APPL', 'CFBundleShortVersionString': '1.0',
                'CFBundleVersion': '1', 'LSMinimumSystemVersion': '11.0', 'NSHighResolutionCapable': True}
        if fick_ikon:
            info['CFBundleIconFile'] = NAMN
        with open(paket / 'Contents' / 'Info.plist', 'wb') as f:
            plistlib.dump(info, f)
        (resurser / MARKOR).write_text(json.dumps({'skapad_av': 'tools/partner.py app', 'kontor': str(kontor),
                                                    'python': python, 'ikon': fick_ikon}, ensure_ascii=False) + '\n')
        if mal.exists():
            shutil.rmtree(mal)
        os.replace(paket, mal)
        os.utime(mal)  # Finder och Dock läser om paketet
        return {'app': str(mal), 'ikon': fick_ikon, 'kontor': str(kontor), 'python': python}
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
