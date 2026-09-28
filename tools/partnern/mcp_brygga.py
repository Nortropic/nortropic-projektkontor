"""MCP-brygga (stdio) mellan Claude Code och partnerns server.

Bryggan har ingen egen logik och ingen egen åtkomst: den vidarebefordrar verktygslistan och varje anrop till
servern på 127.0.0.1 med körningens nyckel (miljövariabeln PARTNER_KORNING). Nyckeln gäller bara den
körningen och upphör när den slutar. Går servern inte att nå blir verktygen tomma och anropen fel, aldrig
något annat.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

URL = os.environ.get('PARTNER_URL', 'http://127.0.0.1:4760')
NYCKEL = os.environ.get('PARTNER_KORNING', '')


def _anrop(metod: str, sokvag: str, data=None, timeout: int = 150):
    req = urllib.request.Request(URL + sokvag, method=metod, data=None if data is None else json.dumps(data).encode(),
                                 headers={'X-Partner-Korning': NYCKEL, 'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=timeout) as svar:
        return json.loads(svar.read().decode('utf-8'))


def _skicka(o: dict) -> None:
    sys.stdout.write(json.dumps(o, ensure_ascii=False) + '\n')
    sys.stdout.flush()


def main() -> int:
    for rad in sys.stdin:
        rad = rad.strip()
        if not rad:
            continue
        try:
            m = json.loads(rad)
        except ValueError:
            continue
        mid, metod = m.get('id'), m.get('method')
        if metod == 'initialize':
            _skicka({'jsonrpc': '2.0', 'id': mid, 'result': {
                'protocolVersion': (m.get('params') or {}).get('protocolVersion', '2025-06-18'),
                'capabilities': {'tools': {}}, 'serverInfo': {'name': 'partner', 'version': '1'}}})
        elif metod == 'tools/list':
            try:
                verktyg = _anrop('GET', '/intern/verktyg', timeout=20).get('verktyg', [])
            except (OSError, ValueError, urllib.error.URLError):
                verktyg = []
            _skicka({'jsonrpc': '2.0', 'id': mid, 'result': {'tools': verktyg}})
        elif metod == 'tools/call':
            p = m.get('params') or {}
            try:
                svar = _anrop('POST', '/intern/verktyg/' + str(p.get('name', '')), p.get('arguments') or {})
            except urllib.error.HTTPError as fel:
                try:
                    svar = json.loads(fel.read().decode('utf-8'))
                except ValueError:
                    svar = {'fel': 'Servern avvisade anropet (%d).' % fel.code}
            except (OSError, ValueError, urllib.error.URLError):
                svar = {'fel': 'Partnerns server gick inte att nå; verktyget kunde inte köras.'}
            innehall = []
            if svar.get('text'):
                innehall.append({'type': 'text', 'text': svar['text']})
            for b in svar.get('bilder') or []:
                innehall.append({'type': 'image', 'data': b['data'], 'mimeType': b['mime']})
            if svar.get('fel'):
                innehall.append({'type': 'text', 'text': svar['fel']})
            _skicka({'jsonrpc': '2.0', 'id': mid, 'result': {'content': innehall or [{'type': 'text', 'text': '(tomt)'}],
                                                             'isError': bool(svar.get('fel'))}})
        elif metod == 'ping':
            _skicka({'jsonrpc': '2.0', 'id': mid, 'result': {}})
        elif mid is not None:
            _skicka({'jsonrpc': '2.0', 'id': mid, 'error': {'code': -32601, 'message': 'okänd metod'}})
    return 0


if __name__ == '__main__':
    sys.exit(main())
