"""Sökvägar, gränser och modellval för förbättringspartnern.

Allt som beror på just den här datorn samlas här och kan skrivas över med miljövariabler (prov) eller med
`installningar.json` i datakatalogen (ägarens val). Inga hemligheter ligger i koden: inloggningsnyckeln och
kaknyckeln läses ur en egen 0600-katalog.
"""
from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass, field, asdict
from pathlib import Path

HEM = Path.home()
PAKET = Path(__file__).resolve().parent
KONTOR = PAKET.parents[1]  # tools/partner -> tools -> repo


def kontorets_primar(rot: Path = KONTOR) -> Path:
    """Kontorets primärutcheckning, även när koden körs ur en worktree (samma Git-databas)."""
    try:
        common = subprocess.run(['git', '-C', str(rot), 'rev-parse', '--path-format=absolute', '--git-common-dir'],
                                capture_output=True, text=True, timeout=10, check=True).stdout.strip()
        if common.endswith('/.git'):
            return Path(common[:-5])
    except (OSError, subprocess.SubprocessError):
        pass
    return rot


@dataclass
class Gransar:
    """Verkställda gränser för modellarbete. Ägaren ändrar dem i installningar.json."""
    samtidiga_korningar: int = 2
    tur_max_sekunder: int = 900
    tur_max_steg: int = 40
    tur_max_listpris_usd: float = 8.0      # Claude Codes egen uppskattning (listpris), inte en faktura
    dygn_max_korningar: int = 150
    dygn_max_listpris_usd: float = 250.0
    jobb_max_sekunder: int = 1800
    jobb_max_steg: int = 150
    bilaga_max_byte: int = 40_000_000
    inspel_max_bilagor: int = 20
    inspel_max_tecken: int = 60_000


@dataclass
class Modell:
    huvud: str = 'claude-opus-5-5'
    anstrangning: str = 'high'
    utredare: str = 'sonnet'


@dataclass
class Konfig:
    data: Path
    hemligheter: Path
    port: int = 4760
    claude: str = ''
    modell: Modell = field(default_factory=Modell)
    gransar: Gransar = field(default_factory=Gransar)
    kontor: Path = KONTOR
    kontor_primar: Path = KONTOR
    improvements: Path = HEM / 'nortropic/intake-campaigns/improvements-preparation-2026-09/corpus/_projects/improvements'
    kampanj: Path = HEM / 'nortropic/intake-campaigns/improvements-preparation-2026-09'
    repon: dict = field(default_factory=dict)
    prov_dolj: tuple = ()   # bara provinstanser: källgrupper (t.ex. imp:CONV-064) som döljs så att inget facit läcker

    def till_json(self) -> dict:
        d = asdict(self)
        for k, v in list(d.items()):
            if isinstance(v, Path):
                d[k] = str(v)
        d['repon'] = {k: str(v) for k, v in self.repon.items()}
        return d


def _repon(primar: Path) -> dict:
    bas = HEM / 'nortropic-repos'
    return {
        'kontoret': primar,
        'runtime': bas / 'Nortropic Runtime',
        'digitala': bas / 'nortropic-digitala',
        'kundstart': bas / 'nortropic-kundstart',
    }


def ladda() -> Konfig:
    primar = Path(os.environ['PARTNER_KONTOR_PRIMAR']) if os.environ.get('PARTNER_KONTOR_PRIMAR') else kontorets_primar()
    data = Path(os.environ.get('PARTNER_DATA') or primar / 'evidence/partner/local')
    hemligheter = Path(os.environ.get('PARTNER_HEMLIGHETER') or HEM / '.nortropic-hemligheter/partner')
    k = Konfig(data=data, hemligheter=hemligheter, kontor_primar=primar, repon=_repon(primar))
    if os.environ.get('PARTNER_PORT'):
        k.port = int(os.environ['PARTNER_PORT'])
    k.claude = os.environ.get('PARTNER_CLAUDE', '') or _hitta_claude()
    if os.environ.get('PARTNER_IMPROVEMENTS'):
        k.improvements = Path(os.environ['PARTNER_IMPROVEMENTS'])
    if os.environ.get('PARTNER_KAMPANJ'):
        k.kampanj = Path(os.environ['PARTNER_KAMPANJ'])
    if os.environ.get('PARTNER_REPON'):
        k.repon = {n: Path(p) for n, p in json.loads(os.environ['PARTNER_REPON']).items()}
    if os.environ.get('PARTNER_PROV_DOLJ'):
        k.prov_dolj = tuple(x.strip() for x in os.environ['PARTNER_PROV_DOLJ'].split(',') if x.strip())
    installningar = data / 'installningar.json'
    if installningar.is_file():
        try:
            val = json.loads(installningar.read_text('utf-8'))
        except ValueError:
            val = {}
        for namn, varde in (val.get('modell') or {}).items():
            if hasattr(k.modell, namn) and isinstance(varde, str):
                setattr(k.modell, namn, varde)
        for namn, varde in (val.get('gransar') or {}).items():
            if hasattr(k.gransar, namn) and isinstance(varde, (int, float)) and not isinstance(varde, bool):
                setattr(k.gransar, namn, type(getattr(k.gransar, namn))(varde))
    return k


def _hitta_claude() -> str:
    for kandidat in ('/opt/homebrew/bin/claude', '/usr/local/bin/claude', str(HEM / '.local/bin/claude')):
        if os.path.isfile(kandidat) and os.access(kandidat, os.X_OK):
            return kandidat
    return 'claude'
