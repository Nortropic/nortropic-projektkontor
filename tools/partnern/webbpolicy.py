"""Serverns beslut om webbsökning och webbhämtning.

WebFetch tillåts bara till publika värdar som Johnny själv har länkat i tråden, som finns i resultatet av en
webbsökning (WebSearch) under samma körning, eller som står i en kort lista över exakta dokumentationsvärdar där
ingen utomstående kan publicera innehåll eller läsa loggar (dem hämtas utan frågedel). Länkar i bilagor, hämtade
sidor eller andra verktygssvar gör aldrig en värd tillåten, och en adress som bär en annan adress (validerare,
arkiv, proxy) hämtas aldrig. En sökning med site: görs bara mot dokumentationsvärdar och Johnnys länkar.
Det gör att text i ett dokument eller på en webbsida inte kan få partnern att skicka data till en godtycklig
adress. Sökfrågor och adresser som innehåller hemlighetsliknande värden eller personuppgifter nekas.
"""
from __future__ import annotations

import ipaddress
import re
from urllib.parse import urlparse

from .kallor import HEMLIGT, HEMLIGT_TILLDELNING

# Dokumentationsvärdar som modellen själv får navigera till, som EXAKTA värdnamn (ingen suffixmatchning): bara
# dokumentation där utomstående varken kan publicera eget innehåll eller läsa förfrågningsloggar, och utan tjänster
# som hämtar andra adresser åt en (validerare, arkiv, översättare). Frågedelar hämtas inte från dessa värdar.
# GitHub läses med verktyget github (API, endast GET), inte med WebFetch.
DOKUMENTATION = frozenset((
    'docs.anthropic.com', 'code.claude.com', 'platform.claude.com', 'www.anthropic.com', 'anthropic.com',
    'www.claude.com', 'claude.com', 'platform.openai.com', 'developers.openai.com', 'openai.com', 'www.openai.com',
    'vercel.com', 'nextjs.org', 'ai-sdk.dev', 'docs.python.org', 'www.python.org', 'nodejs.org',
    'developer.mozilla.org', 'web.dev', 'www.w3.org', 'html.spec.whatwg.org', 'arxiv.org', 'en.wikipedia.org',
    'sv.wikipedia.org', 'docs.temporal.io', 'modelcontextprotocol.io', 'www.sqlite.org', 'sqlite.org',
    'www.typescriptlang.org', 'react.dev', 'playwright.dev', 'doc.rust-lang.org', 'learn.microsoft.com',
    'developers.google.com', 'ai.google.dev', 'developers.cloudflare.com', 'docs.stripe.com', 'docs.railway.com',
    'developer.apple.com', 'tailwindcss.com'))
MAX_URL = 400
MAX_SEGMENT = 100
# En adress som bär en annan adress (vidarebefordran genom validerare, arkiv, proxyer) hämtas aldrig.
INBADDAD_ADRESS = re.compile(r'(?i)(https?:|://|%3a%2f%2f|%253a%252f%252f|\bwww\.)')
DOMANVARDE = re.compile(r'(?i)(^|[=&])[a-z0-9-]+(\.[a-z0-9-]+)*\.[a-z]{2,}(/|&|$)')
SITE = re.compile(r'(?i)\bsite:([^\s/]+)')

PERSONUPPGIFT = [
    re.compile(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}'),
    re.compile(r'\b(19|20)?\d{6}[-+]?\d{4}\b'),            # personnummer
    re.compile(r'(\+46|\b0)7\d[\s-]?\d{3}[\s-]?\d{2}[\s-]?\d{2}\b'),  # mobilnummer
]


def _hemligt(text: str, extra: tuple = ()) -> bool:
    if any(m.search(text) for m in HEMLIGT) or HEMLIGT_TILLDELNING.search(text):
        return True
    return any(e and e in text for e in extra)


def _privat_vard(vard: str) -> bool:
    vard = (vard or '').lower().strip('.')
    if not vard or '.' not in vard or vard in ('localhost',) or vard.endswith(('.local', '.internal', '.lan', '.home',
                                                                                 '.localhost', '.arpa')):
        return True
    try:
        ip = ipaddress.ip_address(vard.strip('[]'))
        return not ip.is_global
    except ValueError:
        return False


def _matchar(vard: str, domaner) -> bool:
    """Värd som Johnny länkat eller som en webbsökning returnerat: exakt värd eller dess underdomän."""
    return any(vard == d or vard.endswith('.' + d) for d in domaner)


def prova(korning, verktyg: str, indata: dict, hemligheter: tuple = ()) -> tuple:
    if verktyg == 'WebSearch':
        fraga = str(indata.get('query') or '')
        if len(fraga) > 300:
            return 'deny', 'Sökfrågan är för lång; håll den allmän och kort.'
        if _hemligt(fraga, hemligheter):
            return 'deny', 'Sökfrågan innehåller något som liknar en hemlighet; formulera om utan den.'
        if any(m.search(fraga) for m in PERSONUPPGIFT):
            return 'deny', 'Sökfrågan innehåller något som liknar en personuppgift; formulera om utan den.'
        for vard in SITE.findall(fraga):
            vard = vard.lower().strip('.')
            if vard not in DOKUMENTATION and not _matchar(vard, korning.url_varder):
                return 'deny', ('En sökning begränsad till %s görs inte: värden varken står bland dokumentationskällorna '
                                'eller finns bland Johnnys länkar i tråden.' % vard)
        return 'allow', ''
    if verktyg == 'WebFetch':
        url = str(indata.get('url') or '')
        try:
            p = urlparse(url)
        except ValueError:
            return 'deny', 'Ogiltig adress.'
        if p.scheme not in ('http', 'https') or not p.hostname or p.username or p.password:
            return 'deny', 'Bara publika http(s)-adresser utan inloggningsuppgifter hämtas.'
        vard = p.hostname.lower()
        if _privat_vard(vard):
            return 'deny', 'Lokala och interna adresser hämtas inte.'
        if (len(url) > MAX_URL or len(p.query) > 300 or any(len(s) > MAX_SEGMENT for s in p.path.split('/'))
                or _hemligt(url, hemligheter) or any(m.search(p.query) for m in PERSONUPPGIFT)):
            return 'deny', 'Adressen bär mer data än en vanlig länk (lång sökväg eller frågedel, hemlighets- eller personuppgiftsliknande värden).'
        if INBADDAD_ADRESS.search(p.path + '?' + p.query + '#' + p.fragment) or DOMANVARDE.search(p.query):
            return 'deny', 'Adressen bär en annan adress (vidarebefordran genom validerare, arkiv eller proxy) och hämtas inte.'
        if _matchar(vard, korning.url_varder) or _matchar(vard, korning.sokvardar):
            return 'allow', ''
        if vard in DOKUMENTATION:
            if p.query:
                return 'deny', 'Dokumentationssidor hämtas utan frågedel.'
            return 'allow', ''
        return 'deny', ('Värden %s kommer varken från Johnnys länkar i tråden, en webbsökning i den här körningen '
                        'eller listan över dokumentationskällor. Be Johnny om länken om den behövs.' % vard)
    return 'deny', 'Okänt verktyg.'
