"""Modellfri kontroll av tal och kvarstående lägestext i en kontorspost före granskning.

    python3 -B tools/postkontroll.py POST.md [FIL ...]
    python3 -B tools/postkontroll.py POST.md PLANBLOCK.md --plan PLAN-HELA.md --bas docs/plan.md
    python3 -B tools/postkontroll.py POST.md --json

Kontrollen kompletterar den separata granskningen och ersätter den inte: den avgör bara det som går att avgöra
mekaniskt ur texterna själva, och en post som passerar är inte granskad. Varje fynd är något att bemöta, inte en dom.
Har regeln fel om texten är svaret att skriva om raden så den inte är tvetydig, inte att tysta regeln.

Posterna och planen är hårdbrutna, så varje textregel läser stycken (rader fram till nästa tomrad) och inte rader;
en mening som "26 rundor …, varav 17 … och 8 …" bryts annars mitt itu och blir osynlig.

Reglerna är valda efter en genomgång av de 123 blockerande fynden i kontorets och Digitalas granskningsrundor
2026-09-24–29 (POSTKONTROLL-20260929). Var och en fångar en klass som faktiskt fällde en runda:

    SUMMA         `N X, varav A … och B …` där A + B inte blir N
    TALSPRIDNING  samma storhet bär olika tal på olika ställen i samma leverans
    PARENTES      stycke som stänger en parentes som aldrig öppnades — spåret av en halv omskrivning
    TURRADER      prosans antal öppna rader mot antalet rader i ÄGARENS TUR-blocket
    TURFORM       rad i ÄGARENS TUR utan `— sedan ÅÅÅÅ-MM-DD`, eller turrad efter blockslutet
    PLANBLOCK     rubrik som står två gånger i planen
    PLANFALL      stycke som fanns i basens plan och inte har någon motsvarighet i kandidatens
    TURBORT       rad som ändringen tar bort ur ÄGARENS TUR — bär planens prosa kvar den?

Textreglerna läser `filer` — postens text och planblocket, alltså det ändringen skriver. Ges både `--plan` och
`--bas` läser de dessutom de stycken i planen som ändringen lägger till eller skriver om, och bara dem: hela planen
bär dussintals historiska block vars tal inte hör ihop, medan de ändrade styckena är samma leverans som posten och
ska räkna likadant. Räckvidden är ändå den vanliga: bara tal som står med en storhet regeln känner igen jämförs.
Granskningens runda 2 fällde denna leverans på att posten sade "rundorna 3 och 4" medan raden i ÄGARENS TUR sade
"varav tre gällde räkningar" — samma sak sagd på två sätt, och ingen av reglerna når den motsägelsen.

Planreglerna läser `--plan`, den hela planen efter ändringen; PLANFALL och TURBORT kräver dessutom `--bas`.
Exitkoden är 1 när något fynd finns, annars 0; `--json` ger fynden som JSON på stdout.
"""
import argparse
import difflib
import json
import re
import sys
from pathlib import Path

TALORD = {
    'en': 1, 'ett': 1, 'två': 2, 'tre': 3, 'fyra': 4, 'fem': 5, 'sex': 6, 'sju': 7, 'åtta': 8, 'nio': 9,
    'tio': 10, 'elva': 11, 'tolv': 12, 'tretton': 13, 'fjorton': 14, 'femton': 15, 'sexton': 16,
    'sjutton': 17, 'arton': 18, 'aderton': 18, 'nitton': 19, 'tjugo': 20, 'tjugoen': 21, 'tjugoett': 21,
    'tjugotvå': 22, 'tjugotre': 23, 'tjugofyra': 24, 'tjugofem': 25, 'tjugosex': 26, 'tjugosju': 27,
    'tjugoåtta': 28, 'tjugonio': 29, 'trettio': 30, 'trettioen': 31, 'trettioett': 31, 'fyrtio': 40,
    'femtio': 50, 'sextio': 60, 'sjuttio': 70, 'åttio': 80, 'nittio': 90,
}
TAL = r'(?:\d+|' + '|'.join(sorted(TALORD, key=len, reverse=True)) + r')'

# Storheter som är räknade och som samma leverans ska räkna likadant på varje ställe.
# Bara storheter som ett fynd i genomgången vilar på: krav (F116, F117), rundor (F017) och version (F003).
# "fynd" prövades och togs bort igen — tre nya falsklarm i mätningen, ingen ny träff — liksom "anmärkningar" och
# "mutationer", som bara bar falsklarm. "rundor" står kvar fast regeln inte når F017 (talet står i singular) och
# storheten bara bär falsklarm i mätningen: den är den vanligaste räknade storheten i kontorets poster, och ett
# fynd att bemöta kostar en mening.
#
# TALSPRIDNING är därmed den enda regeln vars ordlista är vidare än dess uppmätta träffar.
STORHETER = {'krav': 'krav', 'rundor': 'rundor', 'rundan': 'rundor'}
LIKHET = 0.6  # under detta liknar inget kandidatstycke basstycket tillräckligt för att vara samma stycke
TURRUBRIK = re.compile(r'^\s*ÄGARENS TUR\s*$')
TURRAD = re.compile(r'^- \[(beslut|operatörshandling)\]')
SEDAN = re.compile(r'— sedan \d{4}-\d{2}-\d{2}\s*$')
RUBRIK = re.compile(r'^(#{1,3})\s+(.+?)\s*$')
PARENTESPAR = re.compile(r'\([^()]*\)')
POSTNAMN = re.compile(r'\b[A-ZÅÄÖ][A-ZÅÄÖ0-9]*(?:-[A-ZÅÄÖ0-9]+){2,}\b')
STORHETSTAL = re.compile(r'\b(%s)\s+([a-zåäöé]+)\b' % TAL, re.I)
ENBART_TAL = re.compile(r'\b(%s)\b' % TAL, re.I)
KODCITAT = re.compile(r'`[^`]*`')
VERSIONSTAL = re.compile(r'\bversion(?:en)?\s+(%s)\b' % TAL, re.I)
TUROPPNA = re.compile(r'\b(%s)\s+rad(?:er)?\s+(?:är\s+)?öpp(?:na|en|et)\b' % TAL, re.I)


def tal(text):
    """Talet som ett heltal, oavsett om det står med siffror eller som svenskt talord."""
    text = text.strip().lower()
    return int(text) if text.isdigit() else TALORD.get(text)


def rader(vag):
    return Path(vag).read_text(encoding='utf-8').splitlines()


def stycken(text):
    """(första radnummer, styckets text med radbrytningar som blanksteg, radnummer per tecken)."""
    ut, nuvarande, start = [], [], None
    for nr, rad in enumerate(text, 1):
        if rad.strip():
            if start is None:
                start = nr
            nuvarande.append((nr, rad))
        elif nuvarande:
            ut.append(_stycke(start, nuvarande))
            nuvarande, start = [], None
    if nuvarande:
        ut.append(_stycke(start, nuvarande))
    return ut


def _stycke(start, poster):
    bitar, karta = [], []
    for nr, rad in poster:
        if bitar:
            bitar.append(' ')
            karta.append(nr)
        bitar.append(rad)
        karta.extend([nr] * len(rad))
    return start, ''.join(bitar), karta


def radnr(karta, start, offset):
    return karta[offset] if 0 <= offset < len(karta) else start


def fynd(regel, fil, rad, text):
    return {'regel': regel, 'fil': str(fil), 'rad': rad, 'text': text}


def maskera(text):
    """Texten med parentesuttryck och kodcitat utbytta mot blanksteg.

    Tal i en parentes är underuppgifter om ett led, inte egna led; tal i backticks är citerad text och inte
    styckets egen räkning.
    """
    text = KODCITAT.sub(lambda m: ' ' * len(m.group(0)), text)
    forra = None
    while forra != text:
        forra, text = text, PARENTESPAR.sub(lambda m: ' ' * len(m.group(0)), text)
    return text


def r_summa(fil, text):
    """SUMMA: `N X, varav A … och B …` där delarna inte blir helheten."""
    ut = []
    for start, stycke, karta in stycken(text):
        ren = maskera(stycke)
        for m in re.finditer(r'\bvarav\b', ren, re.I):
            fore, efter = ren[:m.start()], ren[m.end():m.end() + 400]
            # Uppdelningen slutar där satsen gör det. Utan kolon, semikolon och tankstreck löper "varav A och B"
            # vidare in i nästa led och plockar upp tal som inte är delar av helheten.
            efter = re.split(r'(?<=[.!?])\s|[:;]|\s—\s', efter)[0]
            helhet = storhet = None
            for h in ENBART_TAL.finditer(fore):
                v = tal(h.group(1)) if h.group(1).lower() not in ('en', 'ett') else None
                if v is not None:
                    efterord = re.match(r'\s+([a-zåäöé]+)', fore[h.end():])
                    helhet, storhet = v, efterord.group(1) if efterord else 'stycken'
            if helhet is None:
                continue
            delar = [tal(d.group(1)) for d in STORHETSTAL.finditer(efter)
                     if d.group(1).lower() not in ('en', 'ett')]
            delar = [d for d in delar if d is not None]
            if len(delar) < 2 or sum(delar) == helhet:
                continue
            ut.append(fynd('SUMMA', fil, radnr(karta, start, m.start()),
                           'delarna efter "varav" (%s) blir %d, men helheten sägs vara %d %s'
                           % (' + '.join(str(d) for d in delar), sum(delar), helhet, storhet)))
    return ut


def r_parentes(fil, text):
    """PARENTES: stycke som stänger en parentes som aldrig öppnades — det spår en halv omskrivning lämnar."""
    ut = []
    for start, stycke, karta in stycken(text):
        if stycke.lstrip().startswith(('|', '```')):
            continue
        stycke = KODCITAT.sub(lambda m: ' ' * len(m.group(0)), stycke)
        djup, offset = 0, None
        for i, tecken in enumerate(stycke):
            if tecken == '(':
                djup += 1
            elif tecken == ')':
                djup -= 1
                if djup < 0 and offset is None:
                    offset, djup = i, 0
        if offset is not None:
            ut.append(fynd('PARENTES', fil, radnr(karta, start, offset),
                           'stycket stänger en parentes som aldrig öppnades — står en halv omskrivning kvar?'))
    return ut


def r_talspridning(lasta):
    """TALSPRIDNING: samma storhet bär olika tal på olika ställen i leveransen.

    "en" och "ett" räknas inte: på svenska är de nästan alltid obestämd artikel ("faller ett krav blir posten
    ett förslag"), och att läsa dem som talet 1 lade ett tredje, meningslöst tal i varje sådan jämförelse. Det
    stänger inte falsklarmen — det enda falsklarmet mot en godkänd post i mätningen står kvar efteråt — men det
    gör de fynd som blir kvar läsbara. Priset är att en räkning som verkligen står i singular ("i en runda") inte
    ses; fyndet F017 i genomgången är av det slaget och är därför klassat som ett bedömningsfynd.
    """
    setts = {}
    for fil, text in lasta:
        for start, stycke, karta in stycken(text):
            # Ett tal i backticks är citerad text — ofta en annan texts felräkning som posten redovisar att den
            # rättat — och inte styckets egen räkning. SUMMA och PARENTES maskerar det redan.
            stycke = KODCITAT.sub(lambda m: ' ' * len(m.group(0)), stycke)
            for m in STORHETSTAL.finditer(stycke):
                storhet = STORHETER.get(m.group(2).lower())
                v = tal(m.group(1)) if m.group(1).lower() not in ('en', 'ett') else None
                if storhet and v is not None:
                    setts.setdefault(storhet, {}).setdefault(v, []).append((fil, radnr(karta, start, m.start())))
            for m in VERSIONSTAL.finditer(stycke):
                v = tal(m.group(1))
                if v is not None:
                    setts.setdefault('version', {}).setdefault(v, []).append((fil, radnr(karta, start, m.start())))
    ut = []
    for storhet, per_tal in sorted(setts.items()):
        if len(per_tal) < 2:
            continue
        fil, nr = sorted(p[0] for p in per_tal.values())[0]
        var = '; '.join('%d på %s:%d' % (v, Path(p[0][0]).name, p[0][1]) for v, p in sorted(per_tal.items()))
        ut.append(fynd('TALSPRIDNING', fil, nr,
                       'storheten "%s" räknas olika på olika ställen (%s) — är det samma storhet?' % (storhet, var)))
    return ut


def turblock(text):
    """(radnummer för rubriken, [(radnummer, rad)]) — blocket slutar vid första rad som inte är en turrad."""
    for nr, rad in enumerate(text, 1):
        if TURRUBRIK.match(rad):
            block = []
            for i in range(nr, len(text)):
                # Läsaren slutar vid första rad som inte är en turrad — också vid en tom rad
                # (RUNTIME-PROFILER-AGARTUR-RATTELSE-20260927).
                if not TURRAD.match(text[i]):
                    break
                block.append((i + 1, text[i]))
            return nr, block
    return None, []


def r_turrader(fil, text):
    """TURRADER: prosans antal öppna rader mot blockets faktiska antal."""
    rubrik, block = turblock(text)
    if rubrik is None:
        return []
    ut = []
    for start, stycke, karta in stycken(text):
        if start > rubrik:
            break
        for m in TUROPPNA.finditer(stycke):
            sagt = tal(m.group(1))
            if sagt is not None and sagt != len(block):
                ut.append(fynd('TURRADER', fil, radnr(karta, start, m.start()),
                               'prosan säger %d öppna rader; ÄGARENS TUR-blocket (rad %d) har %d rader'
                               % (sagt, rubrik, len(block))))
    return ut


def r_turform(fil, text):
    """TURFORM: rad utan `— sedan ÅÅÅÅ-MM-DD`, och turrad som hamnat efter blockslutet."""
    rubrik, block = turblock(text)
    if rubrik is None:
        return []
    ut = [fynd('TURFORM', fil, nr, 'raden saknar `— sedan ÅÅÅÅ-MM-DD` sist; Aquarium-läsaren ger den inget datum')
          for nr, rad in block if not SEDAN.search(rad)]
    inne = {nr for nr, _ in block}
    for nr, rad in enumerate(text, 1):
        if nr > rubrik and nr not in inne and TURRAD.match(rad):
            ut.append(fynd('TURFORM', fil, nr,
                           'raden har turradens form men ligger utanför blocket; Aquarium-läsaren når den inte'))
    return ut


def r_planblock(fil, text):
    """PLANBLOCK: rubrik som står två gånger i planen."""
    ut, settes = [], {}
    for nr, rad in enumerate(text, 1):
        m = RUBRIK.match(rad)
        if m:
            settes.setdefault(m.group(2).strip(), []).append(nr)
    for namn, nummer in sorted(settes.items(), key=lambda p: p[1]):
        if len(nummer) > 1:
            ut.append(fynd('PLANBLOCK', fil, nummer[1], 'rubriken "%s" står %d gånger (rad %s)'
                           % (namn, len(nummer), ', '.join(str(n) for n in nummer))))
    return ut


def r_planfall(fil, text, bas):
    """PLANFALL: stycke i basens plan utan motsvarighet i kandidatens — ett block som fallit bort.

    Planen ändras styckevis, så jämförelsen går på stycken och inte på rader. Ett ändrat stycke har en
    efterföljare som liknar det; ett raderat block har ingen, och det är det fallet regeln rapporterar.
    """
    basstycken, kandstycken = stycken(bas), stycken(text)
    b = [s[1] for s in basstycken]
    k = [s[1] for s in kandstycken]
    ut = []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, b, k, autojunk=False).get_opcodes():
        if tag not in ('delete', 'replace') or (i2 - i1) <= (j2 - j1):
            continue
        for i in range(i1, i2):
            narmast = max((difflib.SequenceMatcher(None, b[i], k[j]).ratio() for j in range(j1, j2)), default=0.0)
            if narmast < LIKHET:
                ut.append(fynd('PLANFALL', fil, 0,
                               'stycket på basens rad %d har ingen motsvarighet i kandidaten: "%s…"'
                               % (basstycken[i][0], b[i][:80])))
    return ut


def r_turbort(fil, text, bas):
    """TURBORT: rad som ändringen tar bort ur ÄGARENS TUR.

    Prosan ovanför rubriken beskriver vad som är öppet, och när en rad försvinner blir den beskrivningen osann om
    den inte skrivs om samtidigt. Raderna är få, så regeln rapporterar varje borttagning att kvittera; bär raden ett
    postnamn som prosan fortfarande nämner pekas den prosaraden ut.
    """
    rubrik, nu = turblock(text)
    _, forr = turblock(bas)
    kvar = {rad.strip() for _, rad in nu}
    ut = []
    for _, rad in forr:
        if rad.strip() in kvar:
            continue
        ut.append(fynd('TURBORT', fil, rubrik or 0,
                       'ändringen tar bort raden "%s…" ur ÄGARENS TUR; säger planens prosa fortfarande att den är öppen?'
                       % rad.strip()[:90]))
        for namn in sorted(set(POSTNAMN.findall(rad)) - {n for r in kvar for n in POSTNAMN.findall(r)}):
            for start, stycke, karta in stycken(text):
                if rubrik and start > rubrik:
                    break
                i = stycke.find(namn)
                if i >= 0:
                    ut.append(fynd('TURBORT', fil, radnr(karta, start, i),
                                   'prosan namnger %s, vars enda rad ändringen tar bort ur ÄGARENS TUR' % namn))
    return ut


def andrade_stycken(text, bas):
    """Planens rader, men bara de stycken ändringen lägger till eller skriver om; övriga rader blir tomma.

    Radnumren bevaras, så ett fynd pekar på rätt rad i planen. Resten av planen tas bort eftersom den bär
    historiska block vars tal inte hör ihop med leveransens.
    """
    behall = set()
    b = [s[1] for s in stycken(bas)]
    kand = stycken(text)
    k = [s[1] for s in kand]
    for tag, _, _, j1, j2 in difflib.SequenceMatcher(None, b, k, autojunk=False).get_opcodes():
        if tag in ('insert', 'replace'):
            for j in range(j1, j2):
                behall.update(kand[j][2])
    return [rad if nr in behall else '' for nr, rad in enumerate(text, 1)]


def kontrollera(filer, plan=None, bas=None):
    """Fynden för en leverans. `filer` är postens text; `plan` är den hela planen efter ändringen."""
    lasta = [(f, rader(f)) for f in filer]
    basrader = rader(bas) if bas else None
    if plan and basrader is not None:
        lasta.append((plan, andrade_stycken(rader(plan), basrader)))
    ut = []
    for f, text in lasta:
        ut += r_summa(f, text)
        ut += r_parentes(f, text)
    ut += r_talspridning(lasta)
    if plan:
        plantext = rader(plan)
        ut += r_turrader(plan, plantext)
        ut += r_turform(plan, plantext)
        ut += r_planblock(plan, plantext)
        if basrader is not None:
            ut += r_planfall(plan, plantext, basrader)
            ut += r_turbort(plan, plantext, basrader)
    return sorted(ut, key=lambda f: (f['fil'], f['rad'], f['regel']))


def main(argv=None):
    parser = argparse.ArgumentParser(
        description='Modellfri kontroll av tal och kvarstående lägestext i en kontorspost före granskning.')
    parser.add_argument('filer', nargs='+', help='postens text och planblocket — det ändringen skriver')
    parser.add_argument('--plan', help='den hela planen efter ändringen (ÄGARENS TUR, rubrikblock)')
    parser.add_argument('--bas', help='planen före ändringen, för bortfall och kvarstående prosa')
    parser.add_argument('--json', action='store_true', help='skriv fynden som JSON')
    args = parser.parse_args(argv)
    if args.bas and not args.plan:
        parser.error('--bas kräver --plan')
    ut = kontrollera(args.filer, args.plan, args.bas)
    if args.json:
        print(json.dumps(ut, ensure_ascii=False, indent=1))
    else:
        for f in ut:
            print('%-13s %s  %s' % (f['regel'], '%s:%d' % (f['fil'], f['rad']) if f['rad'] else f['fil'], f['text']))
        print('POSTKONTROLL OK' if not ut else 'POSTKONTROLL: %d fynd att bemöta' % len(ut))
    return 1 if ut else 0


if __name__ == '__main__':
    sys.exit(main())
