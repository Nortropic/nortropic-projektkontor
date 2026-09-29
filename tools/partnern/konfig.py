"""Sökvägar, gränser och modellval för förbättringspartnern.

Allt som beror på just den här datorn samlas här och kan skrivas över med miljövariabler (prov) eller med
`installningar.json` i datakatalogen (ägarens val). Inga hemligheter ligger i koden: inloggningsnyckeln och
kaknyckeln läses ur en egen 0600-katalog.
"""
from __future__ import annotations

import json
import os
import subprocess
import threading
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
    jobb_max_sekunder: int = 1800
    jobb_max_steg: int = 150
    bilaga_max_byte: int = 40_000_000
    inspel_max_bilagor: int = 20
    inspel_max_tecken: int = 60_000
    startvakt_per_dygn: int = 6            # nya mottagarsessioner som startvakten får starta per dygn (UTC)


@dataclass
class Modell:
    huvud: str = 'claude-opus-5-5'
    anstrangning: str = 'high'
    utredare: str = 'sonnet'


# Startvaktens utförare: Runtimes fastlåsta binärer med de kontrollsummor Runtime själv binder (claude_profile.py och
# evidence/v0.1/dependencies.json). Vilken som startar, och med vilken modell, väljs i Runtimes bemanning (rollen driver).
RUNTIME_BIN = HEM / 'nortropic-repos/Nortropic Runtime/.runtime/bin'
STARTVAKT_BINARER = {
    'claude': (str(RUNTIME_BIN / 'claude-2.1.257'), '64590d7d9d9c189d33fb3dfa58c5408eaf2a10fe556bd84155d95efaab46b60e'),
    'codex': (str(RUNTIME_BIN / 'codex-0.155.1'), '8eaf1ad12fe6bf89b1710330f58900014322c7c5af677e43be116d8ac5fc0a9e'),
}

# Valbara i samtalsytan (/model), prövade med Claude Code 2.1.280 på ägarens inloggning 2026-09-29. Fable har egen kvot
# i abonnemanget; är den slut stoppas svaret med ett besked om kvoten.
MODELLER = (
    {'id': 'claude-opus-5-5', 'namn': 'Opus 5.5', 'om': 'standard, djupast förståelse'},
    {'id': 'claude-fable-5-1', 'namn': 'Fable 5.1', 'om': 'egen kvot; tar den slut stoppas svaret med ett besked'},
    {'id': 'claude-sonnet-5', 'namn': 'Sonnet 5', 'om': 'snabbare, något grundare'},
    {'id': 'claude-opus-5', 'namn': 'Opus 5', 'om': 'föregående Opus'},
    {'id': 'claude-haiku-4-5-20251001', 'namn': 'Haiku 4.5', 'om': 'snabbast, svagast på djup förståelse'},
)
ANSTRANGNING = ('low', 'medium', 'high', 'xhigh', 'max')
_SPARLAS = threading.Lock()


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
    startvakt: bool = False  # på bara i den ordinarie tjänsten (se ladda)
    startvakt_binarer: dict = field(default_factory=lambda: dict(STARTVAKT_BINARER))
    startvakt_anstrangning: str = 'high'

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
    # Startvakten startar sessioner bara ur den ordinarie tjänsten (egen data och port ej angivna), aldrig ur en prov-
    # eller utvecklingsinstans.
    ordinarie = not (os.environ.get('PARTNER_DATA') or os.environ.get('PARTNER_PORT') or k.prov_dolj)
    k.startvakt = os.environ.get('PARTNER_STARTVAKT', '1' if ordinarie else '0') == '1'
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
        start = val.get('startvakt') if isinstance(val.get('startvakt'), dict) else {}
        if start.get('pa') is False:  # Johnny stänger av startvakten i installningar.json
            k.startvakt = False
        if start.get('anstrangning') in ANSTRANGNING:
            k.startvakt_anstrangning = start['anstrangning']
    return k


def spara_modellval(k: Konfig, huvud: str, anstrangning: str) -> dict:
    """Johnnys val i samtalsytan: skrivs i installningar.json (övriga inställningar orörda) och gäller från nästa
    modellkörning i alla trådar. En pågående körning påverkas inte."""
    if huvud not in {m['id'] for m in MODELLER}:
        raise ValueError('Okänd modell.')
    if anstrangning not in ANSTRANGNING:
        raise ValueError('Okänd ansträngningsnivå.')
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
        modell = val.get('modell') if isinstance(val.get('modell'), dict) else {}
        val['modell'] = dict(modell, huvud=huvud, anstrangning=anstrangning)
        tmp = fil.with_name('.installningar.json.tmp')
        fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(json.dumps(val, ensure_ascii=False, indent=1) + '\n')
            f.flush()
            os.fsync(f.fileno())
        os.chmod(tmp, 0o600)
        os.replace(tmp, fil)
        k.modell.huvud, k.modell.anstrangning = huvud, anstrangning
    return {'huvud': huvud, 'anstrangning': anstrangning}


def _hitta_claude() -> str:
    for kandidat in ('/opt/homebrew/bin/claude', '/usr/local/bin/claude', str(HEM / '.local/bin/claude')):
        if os.path.isfile(kandidat) and os.access(kandidat, os.X_OK):
            return kandidat
    return 'claude'
