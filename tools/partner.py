"""Förbättringspartnern: starta, stoppa och läsa den lokala tjänsten.

    python3 -B tools/partner.py start        starta tjänsten i bakgrunden (127.0.0.1:4760)
    python3 -B tools/partner.py oppna        öppna samtalsytan i webbläsaren, inloggad
    python3 -B tools/partner.py status       visa om tjänsten kör, vilken kod och vilka data
    python3 -B tools/partner.py stopp        stoppa tjänsten (pågående arbete markeras avbrutet och återupptas)
    python3 -B tools/partner.py index        bygg om källindexet ur originalen
    python3 -B tools/partner.py overlamningar  visa överlämningar: mottagare, status, session och startvaktens läge
    python3 -B tools/partner.py backlog [--alla]  visa backloggen: vilande beställningar (bara läsning, ingen modell)
    python3 -B tools/partner.py kvittera OVL-… mottagen|startad|levererad|avslagen --av "…" [--bevis "…"]
    python3 -B tools/partner.py autostart    visa hur ägaren gör tjänsten bestående (skriver ingenting)
    python3 -B tools/partner.py app          skapa Nortropic.app i ~/Applications: ett klick startar och öppnar arbetsplatsen

Se tools/PARTNER.md.
"""
from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from partnern import konfig as kf  # noqa: E402


def _halsa(k) -> dict | None:
    try:
        with urllib.request.urlopen('http://127.0.0.1:%d/halsa' % k.port, timeout=3) as r:
            return json.loads(r.read().decode())
    except Exception:
        return None


def _pid(k) -> int | None:
    fil = Path(k.data) / 'tjanst.pid'
    try:
        pid = int(fil.read_text().strip())
        os.kill(pid, 0)
        return pid
    except (OSError, ValueError):
        return None


def _privat_fil(p: Path, lage: int):
    """Öppna för skrivning med rättigheterna 0600, även om filen redan fanns med vidare rättigheter."""
    fd = os.open(p, os.O_WRONLY | os.O_CREAT | lage, 0o600)
    os.fchmod(fd, 0o600)
    return os.fdopen(fd, 'ab' if lage & os.O_APPEND else 'wb')


def start(k, args) -> int:
    if _halsa(k):
        print('Tjänsten kör redan på http://127.0.0.1:%d (pid %s).' % (k.port, _pid(k)))
        return 0
    Path(k.data).mkdir(parents=True, exist_ok=True)
    os.chmod(k.data, 0o700)
    logg = _privat_fil(Path(k.data) / 'tjanst.log', os.O_APPEND)
    proc = subprocess.Popen([sys.executable, '-B', str(Path(__file__).resolve()), 'kor'], stdin=subprocess.DEVNULL,
                            stdout=logg, stderr=logg, start_new_session=True, cwd=str(Path(__file__).resolve().parents[1]))
    for _ in range(120):
        time.sleep(0.5)
        if _halsa(k):
            print('Tjänsten kör på http://127.0.0.1:%d (pid %d). Öppna med: python3 -B tools/partner.py oppna' % (k.port, proc.pid))
            return 0
        if proc.poll() is not None:
            break
    print('Tjänsten startade inte; se %s' % (Path(k.data) / 'tjanst.log'), file=sys.stderr)
    return 1


def kor(k, args) -> int:
    from partnern.server import starta
    Path(k.data).mkdir(parents=True, exist_ok=True)
    os.chmod(k.data, 0o700)
    logg = Path(k.data) / 'tjanst.log'
    if logg.exists():  # launchd skapar loggen med sina egna rättigheter
        os.chmod(logg, 0o600)
    starta(k, bygg_index=True, pidfil=Path(k.data) / 'tjanst.pid')  # pid skrivs när porten är bunden
    return 0


def stopp(k, args) -> int:
    pid = _pid(k)
    if not pid:
        print('Tjänsten kör inte.')
        return 0
    os.kill(pid, signal.SIGTERM)
    for _ in range(130):  # tjänsten väntar själv upp till 45 s på att pågående körningar journalförs
        time.sleep(0.5)
        try:
            os.kill(pid, 0)
        except OSError:
            print('Tjänsten är stoppad.')
            return 0
    print('Tjänsten svarade inte på stopp inom 65 s (pid %d).' % pid, file=sys.stderr)
    return 1


def status(k, args) -> int:
    h = _halsa(k)
    print('Tjänst: %s' % ('kör (startad %s, pid %s)' % (h['startad'], _pid(k)) if h else 'kör inte'))
    print('Adress: http://127.0.0.1:%d' % k.port)
    print('Data:   %s' % k.data)
    rot = Path(__file__).resolve().parents[1]
    head = subprocess.run(['git', '-C', str(rot), 'rev-parse', '--short', 'HEAD'], capture_output=True, text=True).stdout.strip()
    main = subprocess.run(['git', '-C', str(rot), 'rev-parse', '--short', 'origin/main'], capture_output=True, text=True).stdout.strip()
    print('Kod:    %s i %s (%s)' % (head, rot, 'samma som origin/main' if head == main else 'origin/main är ' + main))
    print('Modell: %s (%s) genom %s' % (k.modell.huvud, k.modell.anstrangning, k.claude))
    return 0 if h else 3


def oppna(k, args) -> int:
    if not _halsa(k):
        print('Tjänsten kör inte; starta med: python3 -B tools/partner.py start', file=sys.stderr)
        return 3
    from partnern.server import las_hemlighet
    nyckel = las_hemlighet(Path(k.hemligheter), 'inloggning.secret')
    url = 'http://127.0.0.1:%d/#nyckel=%s' % (k.port, nyckel)
    subprocess.run(['open', url], check=False)
    print('Öppnade Nortropic, http://127.0.0.1:%d, i webbläsaren (nyckeln följer bara med i adressens fragment och '
          'sparas som en kaka i 30 dagar).' % k.port)
    return 0


def index(k, args) -> int:
    from partnern.kallor import Kallindex
    from partnern.lager import Lager
    lager = Lager(k.data)
    ut = Kallindex(lager, k).bygg()
    print(json.dumps(ut, ensure_ascii=False, indent=1))
    return 0


def overlamningar(k, args) -> int:
    from partnern.lager import Lager
    from partnern.overlamning import paketlage
    from partnern.start import handelser
    lager = Lager(k.data)
    rader = lager.fraga('select id, status, tid, uppdaterad, data from overlamning order by tid desc')
    if not rader:
        print('Inga överlämningar.')
    for r in rader:
        d = json.loads(r['data'])
        kat = Path(d.get('katalog') or '')
        lage = paketlage(kat)  # paketets gällande status, även när tjänsten inte har läst kvittensen ännu
        kv = lage['overgangar'] if lage else []
        status = lage['status'] if lage else r['status']
        print('%s  %-9s  %s\n    mottagare: %s\n    %s %s%s\n    %s' % (
            r['id'], status, d.get('rubrik'), d.get('mottagare') or 'kontorets-kedjedrivare',
            'lagd som vilande' if d.get('status') == 'vilande' else 'lämnad', r['tid'][:19] + 'Z',
            ('; senaste %s %s %s av %s' % ('beslut' if kv[-1].get('beslut') else 'kvittens', kv[-1].get('status'),
                                           str(kv[-1].get('kvitterad'))[:19] + 'Z', kv[-1].get('av'))) if kv else '', kat))
        hist = handelser(kat)
        starter = [h for h in hist if h.get('typ') == 'startad']
        if starter:
            s = starter[0]
            print('    session: %s startad %s i %s (%s, %s %s)%s' % (
                s.get('session'), s['tid'][:19] + 'Z', s.get('repo'), s.get('cli'), s.get('modell'), s.get('anstrangning'),
                (', fortsatt %d gånger' % (len(starter) - 1)) if len(starter) > 1 else ''))
        if hist and hist[-1].get('typ') != 'startad':
            h = hist[-1]
            print('    startvakten: %s %s%s' % (h['typ'], h['tid'][:19] + 'Z', (': ' + h['skal']) if h.get('skal') else ''))
        elif not hist and status == 'lamnad':
            print('    startvakten: ingen start ännu')
    return 0


def backlog(k, args) -> int:
    """Backloggen ur paketen i beställningsvägen; en backlog som inte kan läsas är okänd (kod 4), aldrig tom."""
    from partnern.overlamning import backlog as las, backlogtext
    b = las(k, alla=args.alla)
    print(backlogtext(b))
    return 4 if b['status'] == 'okand' else 0


def kvittera(k, args) -> int:
    from partnern.overlamning import kvittera as kv
    try:
        fil = kv(k, args.id, args.status, args.av, args.bevis or '')
    except (ValueError, FileNotFoundError) as fel:
        print('Ingen kvittens skrevs: %s' % fel, file=sys.stderr)
        return 2
    print('Kvitterat %s som %s i %s. Partnern visar statusen i tråden (inom 30 s när tjänsten kör).' % (args.id, args.status, fil))
    return 0


def autostart(k, args) -> int:
    """Skriver ingenting: visar en LaunchAgent och ägarens två kommandon. Hanterad policy nekar sessioner launchctl."""
    etikett = 'se.nortropic.partner'
    plist = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n'
        '<plist version="1.0"><dict>\n'
        '  <key>Label</key><string>%s</string>\n'
        '  <key>ProgramArguments</key><array><string>%s</string><string>-B</string><string>%s</string>'
        '<string>kor</string></array>\n'
        '  <key>WorkingDirectory</key><string>%s</string>\n'
        '  <key>EnvironmentVariables</key><dict><key>PATH</key>'
        '<string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string></dict>\n'
        '  <key>RunAtLoad</key><true/>\n'
        '  <key>StandardOutPath</key><string>%s</string>\n'
        '  <key>StandardErrorPath</key><string>%s</string>\n'
        '</dict></plist>\n' % (etikett, sys.executable, Path(__file__).resolve(), Path(__file__).resolve().parents[1],
                                Path(k.data) / 'tjanst.log', Path(k.data) / 'tjanst.log'))
    mal = Path.home() / 'Library/LaunchAgents' / (etikett + '.plist')
    print('Ägarsteg (skriver ingenting här). Spara texten nedan som %s och kör sedan i din egen Terminal:\n'
          '  launchctl bootstrap gui/$(id -u) %s\n'
          'Tjänsten startar då vid varje inloggning ur kontorets primärutcheckning (starta inte samtidigt med\n'
          'partner.py start). partner.py stopp stoppar den till nästa inloggning; den bestående starten tas bort med\n'
          '  launchctl bootout gui/$(id -u)/%s\n'
          % (mal, mal, etikett))
    print(plist)
    return 0


def app(k, args) -> int:
    """Skapar Nortropic.app, som startar tjänsten ur kontorets primärutcheckning och öppnar den inloggad."""
    from partnern import macapp
    mal = Path(args.mal).expanduser() if args.mal else Path.home() / 'Applications' / (macapp.NAMN + '.app')
    try:
        ut = macapp.bygg(mal, Path(k.kontor_primar), sys.executable, ikon=not args.utan_ikon)
    except (OSError, ValueError) as fel:
        print('Kunde inte skapa appen: %s' % fel, file=sys.stderr)
        return 1
    print('Skapade %s%s. Den startar tjänsten ur %s med %s och öppnar Nortropic inloggad.\n'
          'Dra den till Dock för ett klick. Den startar inget vid inloggning och innehåller ingen nyckel.'
          % (ut['app'], '' if ut['ikon'] else ' (utan egen ikon: macOS ikonverktyg misslyckades)', ut['kontor'], ut['python']))
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog='partner.py', description='Projektkontorets förbättringspartner')
    sub = p.add_subparsers(dest='kommando', required=True)
    for namn in ('start', 'kor', 'stopp', 'status', 'oppna', 'index', 'overlamningar', 'autostart'):
        sub.add_parser(namn)
    ap = sub.add_parser('app')
    ap.add_argument('--mal', help='var appen skapas (standard ~/Applications/Nortropic.app)')
    ap.add_argument('--utan-ikon', action='store_true')
    bl = sub.add_parser('backlog')
    bl.add_argument('--alla', action='store_true', help='visa också släppta och avslagna beställningar ur backloggen')
    kv = sub.add_parser('kvittera')
    kv.add_argument('id')
    kv.add_argument('status', choices=['mottagen', 'startad', 'levererad', 'avslagen'])
    kv.add_argument('--av', required=True)
    kv.add_argument('--bevis')
    args = p.parse_args(argv)
    k = kf.ladda()
    return {'start': start, 'kor': kor, 'stopp': stopp, 'status': status, 'oppna': oppna, 'index': index,
            'overlamningar': overlamningar, 'backlog': backlog, 'kvittera': kvittera, 'autostart': autostart,
            'app': app}[args.kommando](k, args)


if __name__ == '__main__':
    sys.exit(main())
