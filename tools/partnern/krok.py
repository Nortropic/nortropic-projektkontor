"""PreToolUse-krok för WebFetch, WebSearch och underagenten (Agent) under Claude Code, och för varje verktyg under
Codex: servern bestämmer, kroken frågar.

Claude Code kör kroken före varje webbanrop (även i underagenter) och före varje anrop av en underagent; Codex kör
den före varje verktyg. Kroken skickar verktygets indata till partnerns server med körningens nyckel och återger
serverns beslut. Når den inte servern, eller svarar servern inte i tid, nekas anropet: en destination eller en annan
modell släpps aldrig igenom av misstag. Kroken svarar alltid själv före programmens tidsgräns (20 s): Codex kör
verktyget om en krok dör eller inte hinner svara (prövat 2026-09-30), och samma frist gäller kroken under Claude Code.
"""
from __future__ import annotations

import json
import os
import signal
import sys
import urllib.request

FRIST = 17  # sekunder; programmens tidsgräns för kroken är 20


def _svara(beslut: str, skal: str) -> None:
    utdata = {'hookSpecificOutput': {'hookEventName': 'PreToolUse', 'permissionDecision': beslut}}
    if skal:
        utdata['hookSpecificOutput']['permissionDecisionReason'] = skal
    print(json.dumps(utdata, ensure_ascii=False), flush=True)


def _for_sent(signum, frame) -> None:
    _svara('deny', 'Partnerns server svarade inte i tid; anropet nekas.')
    os._exit(0)


def main() -> int:
    signal.signal(signal.SIGALRM, _for_sent)
    signal.alarm(FRIST)
    try:
        data = json.load(sys.stdin)
    except ValueError:
        data = {}
    beslut, skal = 'deny', 'Partnerns server kunde inte pröva anropet; det nekas.'
    try:
        req = urllib.request.Request(
            os.environ.get('PARTNER_URL', 'http://127.0.0.1:4760') + '/intern/krok', method='POST',
            data=json.dumps({'verktyg': data.get('tool_name'), 'indata': data.get('tool_input') or {}}).encode(),
            headers={'X-Partner-Korning': os.environ.get('PARTNER_KORNING', ''), 'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=15) as svar:
            d = json.loads(svar.read().decode('utf-8'))
        if d.get('beslut') in ('allow', 'deny'):
            beslut, skal = d['beslut'], d.get('skal') or ''
    except Exception:
        pass
    signal.alarm(0)
    _svara(beslut, skal)
    return 0


if __name__ == '__main__':
    sys.exit(main())
