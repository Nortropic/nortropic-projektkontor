"""Sökvägar, gränser och modellval för förbättringspartnern.

Allt som beror på just den här datorn samlas här och kan skrivas över med miljövariabler (prov) eller med
`installningar.json` i datakatalogen (ägarens val). Inga hemligheter ligger i koden: inloggningsnyckeln och
kaknyckeln läses ur en egen 0600-katalog.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
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
    """Ägaren har bestämt att förbättringspartnern inte ska ha någon användningsgräns (2026-09-29): inget dygnstak,
    inget stegtak, ingen kostnadsspärr. tur_max_sekunder/jobb_max_sekunder är alltså inte en användningsgräns utan
    en ren hangvakt (se agent.py _vakt): den fångar bara en process som blivit hängande, satt långt bortom vad ett
    verkligt, aktivt arbete tar. Ägaren ändrar allt i installningar.json."""
    samtidiga_korningar: int = 2
    tur_max_sekunder: int = 14_400          # 4 h — hangvakt, inte en användningsgräns
    jobb_max_sekunder: int = 43_200         # 12 h — hangvakt, inte en användningsgräns
    bilaga_max_byte: int = 40_000_000
    inspel_max_bilagor: int = 20
    inspel_max_tecken: int = 60_000
    startvakt_per_dygn: int = 6            # nya mottagarsessioner som startvakten får starta per dygn (UTC)


@dataclass
class Modell:
    """En modell till allt (Johnnys besked 2026-09-29): huvud och anstrangning gäller svaret, utredaren och de
    registrerade utredningarna. Det finns ingen egen utredarmodell; ett äldre 'utredare' i installningar.json läses inte."""
    huvud: str = 'claude-opus-5-5'
    anstrangning: str = 'high'


# Startvaktens utförare: Runtimes fastlåsta binärer med de kontrollsummor Runtime själv binder (claude_profile.py och
# evidence/v0.1/dependencies.json). Vilken som startar, och med vilken modell, väljs i Runtimes bemanning (rollen driver).
RUNTIME = HEM / 'nortropic-repos/Nortropic Runtime'
RUNTIME_BIN = RUNTIME / '.runtime/bin'
# Senast kända Claude-pinne (Runtime D046), när den aktiva releasen inte går att läsa.
RUNTIME_CLAUDE_SENAST = ('2.1.285', '51f09bd1e021d9fa8a1864c179799bd37cb39962a937935c5cf6823398e86db4')


def runtime_claude_pinne(runtime: Path = RUNTIME) -> tuple:
    """(sökväg, sha256) för Runtimes fästa Claude Code, läst ur den aktiva releasens egen runtime/claude_profile.py
    (VERSION och BINARY_SHA256), så att startvakten och modellmätningen följer Runtimes pinne utan en kontorsändring
    när agenten aktiverar en ny (RUNTIME-BINARER-20260930): startvakten från partnerns nästa start, modellmätningen vid
    varje körning. Går releasen inte att läsa, eller stämmer konfigurationen inte med pekarens sha256, gäller den senast
    kända."""
    try:
        pekare = json.loads((runtime / '.runtime/ap10/active.json').read_text('utf-8'))
        config = Path(pekare['config'])
        if hashlib.sha256(config.read_bytes()).hexdigest() != pekare['sha256']:   # som kontorets andra releaseläsningar
            raise ValueError('active.json pekar på en konfiguration med annan sha256')
        text = (config.parent / 'runtime/runtime/claude_profile.py').read_text('utf-8')
        version = re.search(r"^VERSION = '([0-9][0-9.]{0,15})'$", text, re.M).group(1)
        sha = re.search(r"^BINARY_SHA256 = '([0-9a-f]{64})'$", text, re.M).group(1)
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        version, sha = RUNTIME_CLAUDE_SENAST
    return str(runtime / '.runtime/bin' / ('claude-' + version)), sha


STARTVAKT_BINARER = {
    'claude': runtime_claude_pinne(),
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
# Codex egna ansträngningsnivåer (model_reasoning_effort), i Codex ordning. Vilka en viss modell tar står i mätningen.
CODEX_ANSTRANGNING = ('minimal', 'low', 'medium', 'high', 'xhigh', 'max', 'ultra')
MODELLNAMN_FORM = re.compile(r'\A[A-Za-z0-9][A-Za-z0-9._-]{0,63}\Z')


def ar_claude(modell) -> bool:
    """En modell i arbetsplatsens Claude-lista körs av Claude Code; varje annan (uppmätt) modell körs av Codex."""
    return modell in {m['id'] for m in MODELLER}
_SPARLAS = threading.Lock()


@dataclass
class Konfig:
    data: Path
    hemligheter: Path
    port: int = 4760
    claude: str = ''
    codex: str = ''          # Johnnys Codex, för partnern när han valt en Codex-modell (MODELLKARTA-20260929 steg 1b)
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
    # Claude Codes och Codex inställningsfiler, som Johnnys val för sina sessioner skrivs i (ägarens besked 2026-09-29).
    # En prov- eller utvecklingsinstans får egna filer i sin datakatalog och rör aldrig de riktiga (se ladda).
    claude_installningar: Path = field(default_factory=lambda: Path.home() / '.claude/settings.json')
    codex_installningar: Path = field(default_factory=lambda: Path.home() / '.codex/config.toml')
    # Runtimes inkorg för arbetsplatsens val och Runtimes status för den automatiska aktiveringen (D040). None: okänd,
    # och då skrivs inget val. ladda() pekar den ordinarie tjänsten på Runtimes egna filer och en prov- eller
    # utvecklingsinstans med egen datakatalog på den, så att ett prov aldrig kan utlösa ett verkligt byte; en instans
    # utan egen datakatalog som inte är den ordinarie har ingen inkorg.
    runtime_onskemal: Path | None = None
    runtime_status: Path | None = None
    runtime_kodstatus: Path | None = None

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
    k.codex = os.environ.get('PARTNER_CODEX', '') or _hitta_codex()
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
    if os.environ.get('PARTNER_CLAUDE_INSTALLNINGAR'):
        k.claude_installningar = Path(os.environ['PARTNER_CLAUDE_INSTALLNINGAR'])
    elif not ordinarie:
        k.claude_installningar = data / 'claude-code-installningar.json'
    if os.environ.get('PARTNER_CODEX_INSTALLNINGAR'):
        k.codex_installningar = Path(os.environ['PARTNER_CODEX_INSTALLNINGAR'])
    elif not ordinarie:
        k.codex_installningar = data / 'codex-installningar.toml'
    runtime = (k.repon or {}).get('runtime')
    if ordinarie and runtime:
        k.runtime_onskemal = Path(runtime) / '.runtime/ap10/workplace-choice.json'
        k.runtime_status = Path(runtime) / '.runtime/ap10/automatic-choice-status.json'
        k.runtime_kodstatus = Path(runtime) / '.runtime/ap10/automatic-code-status.json'
    elif os.environ.get('PARTNER_DATA'):
        k.runtime_onskemal = data / 'runtime-workplace-choice.json'
        k.runtime_status = data / 'runtime-automatic-choice-status.json'
        k.runtime_kodstatus = data / 'runtime-automatic-code-status.json'
    # En instans som varken är den ordinarie eller har egen datakatalog (till exempel bara PARTNER_PROV_DOLJ) har
    # ingen inkorg: den skriver inget önskemål för Runtime, varken i Runtimes inkorg eller i den ordinarie tjänstens
    # datakatalog.
    installningar = data / 'installningar.json'
    if installningar.is_file():
        try:
            val = json.loads(installningar.read_text('utf-8'))
        except ValueError:
            val = {}
        if not isinstance(val, dict):   # en fil med fel form ger standardvärdena, som en fil som inte går att läsa
            val = {}
        for namn, varde in (val.get('modell') if isinstance(val.get('modell'), dict) else {}).items():
            if hasattr(k.modell, namn) and isinstance(varde, str):
                setattr(k.modell, namn, varde)
        for namn, varde in (val.get('gransar') if isinstance(val.get('gransar'), dict) else {}).items():
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
    modellkörning i alla trådar. En pågående körning påverkas inte. Här prövas bara formen och nivån för programmet;
    prövningen mot mätningen görs av anroparna (/api/installningar och Flödet), och en ny anropare måste göra den själv."""
    if not isinstance(huvud, str) or not MODELLNAMN_FORM.match(huvud):
        raise ValueError('Okänd modell.')
    if anstrangning not in (ANSTRANGNING if ar_claude(huvud) else CODEX_ANSTRANGNING):
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


def _hitta_codex() -> str:
    for kandidat in ('/opt/homebrew/bin/codex', '/usr/local/bin/codex', str(HEM / '.local/bin/codex')):
        if os.path.isfile(kandidat) and os.access(kandidat, os.X_OK):
            return kandidat
    return 'codex'


def _hitta_claude() -> str:
    for kandidat in ('/opt/homebrew/bin/claude', '/usr/local/bin/claude', str(HEM / '.local/bin/claude')):
        if os.path.isfile(kandidat) and os.access(kandidat, os.X_OK):
            return kandidat
    return 'claude'
