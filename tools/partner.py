"""Förbättringspartnern: starta, stoppa och läsa den lokala tjänsten.

    python3 -B tools/partner.py start        starta tjänsten i bakgrunden (127.0.0.1:4760)
    python3 -B tools/partner.py oppna        öppna samtalsytan i webbläsaren, inloggad
    python3 -B tools/partner.py status       visa om tjänsten kör, vilken kod och vilka data
    python3 -B tools/partner.py stopp        stoppa tjänsten (pågående arbete markeras avbrutet och återupptas)
    python3 -B tools/partner.py index        bygg om källindexet ur originalen
    python3 -B tools/partner.py overlamningar
    python3 -B tools/partner.py kvittera OVL-… mottagen|startad|levererad|avslagen --av "…" [--bevis "…"]

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


def start(k, args) -> int:
    if _halsa(k):
        print('Tjänsten kör redan på http://127.0.0.1:%d (pid %s).' % (k.port, _pid(k)))
        return 0
    Path(k.data).mkdir(parents=True, exist_ok=True)
    os.chmod(k.data, 0o700)
    logg = open(Path(k.data) / 'tjanst.log', 'ab')
    proc = subprocess.Popen([sys.executable, '-B', str(Path(__file__).resolve()), 'kor'], stdin=subprocess.DEVNULL,
                            stdout=logg, stderr=logg, start_new_session=True, cwd=str(Path(__file__).resolve().parents[1]))
    (Path(k.data) / 'tjanst.pid').write_text(str(proc.pid))
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
    starta(k, bygg_index=True)
    return 0


def stopp(k, args) -> int:
    pid = _pid(k)
    if not pid:
        print('Tjänsten kör inte.')
        return 0
    os.kill(pid, signal.SIGTERM)
    for _ in range(90):
        time.sleep(0.5)
        try:
            os.kill(pid, 0)
        except OSError:
            print('Tjänsten är stoppad.')
            return 0
    print('Tjänsten svarade inte på stopp inom 45 s (pid %d).' % pid, file=sys.stderr)
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
    print('Öppnade http://127.0.0.1:%d i webbläsaren (nyckeln följer bara med i adressens fragment och sparas '
          'som en kaka i 30 dagar).' % k.port)
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
    lager = Lager(k.data)
    rader = lager.fraga('select id, status, tid, uppdaterad, data from overlamning order by tid desc')
    if not rader:
        print('Inga överlämningar.')
    for r in rader:
        d = json.loads(r['data'])
        print('%s  %-9s  %s  → %s\n    %s' % (r['id'], r['status'], d.get('rubrik'), d.get('mottagare'), d.get('katalog')))
    return 0


def kvittera(k, args) -> int:
    from partnern.overlamning import kvittera as kv
    fil = kv(k.kontor_primar, args.id, args.status, args.av, args.bevis or '')
    print('Kvitterat %s som %s i %s. Partnern visar statusen i tråden (inom 30 s när tjänsten kör).' % (args.id, args.status, fil))
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog='partner.py', description='Projektkontorets förbättringspartner')
    sub = p.add_subparsers(dest='kommando', required=True)
    for namn in ('start', 'kor', 'stopp', 'status', 'oppna', 'index', 'overlamningar'):
        sub.add_parser(namn)
    kv = sub.add_parser('kvittera')
    kv.add_argument('id')
    kv.add_argument('status', choices=['mottagen', 'startad', 'levererad', 'avslagen'])
    kv.add_argument('--av', required=True)
    kv.add_argument('--bevis')
    args = p.parse_args(argv)
    k = kf.ladda()
    return {'start': start, 'kor': kor, 'stopp': stopp, 'status': status, 'oppna': oppna, 'index': index,
            'overlamningar': overlamningar, 'kvittera': kvittera}[args.kommando](k, args)


if __name__ == '__main__':
    sys.exit(main())
