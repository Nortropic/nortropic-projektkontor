"""PreToolUse-krok för WebFetch och WebSearch: servern bestämmer, kroken frågar.

Claude Code kör kroken före varje webbanrop (även i underagenter). Kroken skickar verktygets indata till
partnerns server med körningens nyckel och återger serverns beslut. Når den inte servern nekas anropet:
en destination släpps aldrig igenom av misstag.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.request


def main() -> int:
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
    utdata = {'hookSpecificOutput': {'hookEventName': 'PreToolUse', 'permissionDecision': beslut}}
    if skal:
        utdata['hookSpecificOutput']['permissionDecisionReason'] = skal
    print(json.dumps(utdata, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
