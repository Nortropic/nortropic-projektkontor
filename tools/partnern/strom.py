"""Körningsström → körningshändelser (PARTNER-INSYN-20261001).

En tolk för två strömformat — Claude Codes stream-json (`claude -p --output-format stream-json --verbose
--include-partial-messages`) och Codex `exec --json` — till en gemensam, radbunden form som ytans arbetsvy visar som
en terminalutskrift: verktygsanrop med indata, deras resultat med tid och fel, faser (tänker, begär, komprimerar,
kvot, omförsök, kö) och löpande räknare. Samma tolk används för partnerns egna turer och utredningar (agent.py, rad
för rad medan processen kör) och för startvaktens mottagarsessioner (start.py, genom svansläsaren `Svans` av
`session/korning-NN.jsonl`).

"Körningshändelser" här är inte journalens tabell `handelse` (lager.py): de hör till en körning, ligger i minnet och
i `turer/<id>/handelser.jsonl` (bara tillägg, en rad per händelse) och journalförs aldrig i sin helhet; journalens
`tur_klar.steg` är som förut en kort sammanfattning (`Logg.steg`).

Gränser, som också står i beslutet:
- hjärtslag (thinking_delta, system/thinking_tokens, tool_progress, system/status) blir aldrig rader; de uppdaterar
  fasen, så att en lång tankepaus syns som "Tänker… ~1,2k" och inte som tusen rader;
- ett resultat sparas som en avgörande rad (första raden eller exit-koden, storlek, fel) och ett kort utdrag; Edits
  originalFile, oldString/newString och Reads filinnehåll läses aldrig, och okända fält krymps innan de sammanfattas;
- allt som visas tvättas från hemlighetsliknande värden (kallor.tvatta);
- en händelse som tolken inte känner räknas (`utan_tolkning`) men visas aldrig som brus, och ett fel i tolkningen ger
  en varningsrad och stoppar aldrig körningen;
- Codex item-typerna command_execution och file_change är byggda ur dokumentationen och fejken; ingen verklig
  Codex-ström från partnern finns sparad (2026-10-01), så de är inte prövade mot en riktig körning.
"""
from __future__ import annotations

import json
import os
import re
import stat
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

from .kallor import tvatta
from .lager import nu

TEXT_MAX = 400          # en rads text (rubrik, varning, mellanrad)
INDATA_MAX = 400        # kort indata (kommando, fråga, sökväg)
UTDRAG_KORT = 300       # den avgörande resultatraden
UTDRAG_LANG = 2000      # utdraget som fälls ut
FIL_MAX = 64 << 20      # handelser.jsonl och strömfiler läses aldrig förbi detta
SVANS_MAX = 8 << 20     # högst så mycket ny ström per svansläsning
# Fält som aldrig läses ur verktygens indata eller resultat: hela filer och innehåll som ytan inte ska bära.
ALDRIG = frozenset(('originalFile', 'oldString', 'newString', 'old_string', 'new_string', 'content', 'file', 'data',
                    'source', 'prompt', 'message'))
KVOT_GRANS = 0.75       # kvoten blir en rad först vid 75 % av ett fönster, eller när den inte längre är "allowed"
# Codex eget besked om att partnerns granskade krok körs utan tillit (agent.py startar den så); ingen varning för Johnny.
CODEX_VARNING = 'dangerously-bypass-hook-trust'
# Legacy-sammanfattningen (journalens tur_klar.steg) tar inte med resultat, mellanrader och bakgrundsuppgifter.
STEG_UTAN = frozenset(('resultat', 'text', 'uppgift'))
LAGE_FAS = ('start', 'tanker', 'begar', 'svarar', 'verktyg', 'komprimerar', 'omforsok', 'ko', 'klar')


# ------------------------------------------------------------------ hjälp
def _epoch(ts) -> float | None:
    """ISO-tidsstämpel (med Z) eller epok i ms/s → epoksekunder; None när inget går att läsa."""
    if isinstance(ts, (int, float)):
        return float(ts) / 1000.0 if ts > 1e11 else float(ts)
    if not isinstance(ts, str) or not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace('Z', '+00:00')).timestamp()
    except ValueError:
        return None


def _iso(t: float) -> str:
    return datetime.fromtimestamp(t, timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'


def _s(v, n: int = TEXT_MAX) -> str:
    return re.sub(r'\s+', ' ', str(v if v is not None else '')).strip()[:n]


def kortsokvag(p, delar: int = 2) -> str:
    """De sista segmenten av en sökväg: `…/verktyg/underhall.py`. Hela sökvägen står i det utfällda blocket."""
    p = str(p or '')
    bitar = [b for b in p.split('/') if b]
    if len(bitar) <= delar:
        return p[:160]
    return '…/' + '/'.join(bitar[-delar:])[:160]


def _krymp(v, strang: int = 300, lista: int = 20, djup: int = 4):
    """Rekursiv trunkering före sammanfattning: inga hela filer, inga oändliga listor, aldrig fälten i ALDRIG."""
    if djup < 0:
        return '…'
    if isinstance(v, dict):
        return {str(k)[:60]: _krymp(x, strang, lista, djup - 1) for k, x in list(v.items())[:lista] if k not in ALDRIG}
    if isinstance(v, (list, tuple)):
        return [_krymp(x, strang, lista, djup - 1) for x in v[:lista]]
    if isinstance(v, str):
        return v[:strang]
    return v


def _forsta_rad(text: str) -> str:
    for rad in (text or '').splitlines():
        if rad.strip():
            return rad.strip()[:UTDRAG_KORT]
    return ''


def _blocktext(innehall) -> str:
    """Texten i ett tool_result-block: en sträng eller en lista innehållsblock (MCP-verktyg)."""
    if isinstance(innehall, list):
        return '\n'.join(str(x.get('text') or '') for x in innehall if isinstance(x, dict) and x.get('type') == 'text')
    return str(innehall or '')


def _tid(ms) -> str:
    if ms is None:
        return ''
    s = ms / 1000.0
    if s < 10:
        return ('%.1f s' % s).replace('.', ',')
    if s < 3600:
        return '%d min %02d s' % (s // 60, s % 60) if s >= 60 else '%d s' % s
    return '%d h %02d min' % (s // 3600, (s % 3600) // 60)


def _k(n) -> str:
    try:
        n = int(n or 0)
    except (TypeError, ValueError):
        return '?'
    return ('%.1fk' % (n / 1000.0)).replace('.', ',') if n >= 1000 else str(n)


# ------------------------------------------------------------------ beskrivning av anrop
def beskriv(namn: str, indata) -> str:
    """Anropsraden i arbetsvyn: `Verb(objekt)`. Partnerns egna verktyg på svenska; Claude Codes inbyggda med sitt eget
    namn, eftersom Johnny läser Bash, Edit och Read dagligen i terminalen och en översättning skulle dölja vad som
    kördes. Aldrig hela filer eller kommandon: bara det som behövs för att känna igen anropet."""
    indata = indata if isinstance(indata, dict) else {}
    kort = (namn or '').replace('mcp__partner__', '')
    g = lambda *k: next((_s(indata.get(x), 160) for x in k if indata.get(x) not in (None, '')), '')
    if kort == 'sok':
        omfang = indata.get('omfang')
        omfang = ', '.join(str(x) for x in omfang) if isinstance(omfang, list) else _s(omfang, 60)
        return 'Söker("%s"%s)' % (_s(indata.get('fraga'), 120), ', ' + omfang if omfang else '')
    if kort == 'oppna':
        return 'Öppnar(%s)' % g('id')
    if kort == 'bilaga':
        return 'Läser bilaga(%s%s)' % (g('id'), ', sidor ' + _s(indata['sidor'], 40) if indata.get('sidor') else '')
    if kort == 'systemlage':
        delar = indata.get('delar') or ['repon', 'plan', 'drift']
        return 'Systemläge(%s)' % ', '.join(str(d) for d in delar)[:120]
    if kort == 'repo_las':
        return 'Läser(%s: %s)' % (g('repo'), g('sokvag'))
    if kort == 'repo_sok':
        return 'Söker i repot(%s: "%s")' % (g('repo'), g('monster', 'fraga'))
    if kort == 'repo_historik':
        return 'Historik(%s%s)' % (g('repo'), ': ' + g('sokvag') if g('sokvag') else '')
    if kort == 'github':
        return 'GitHub(%s)' % _s(indata.get('sokvag'), 140)
    if kort == 'forstaelse':
        return 'Sparar förståelse(%s, %s)' % (g('slag'), g('auktoritet'))
    if kort == 'resonemang':
        return 'Uppdaterar läget'
    if kort == 'trad':
        return 'Tråd(%s)' % g('atgard')
    if kort == 'bered_uppdrag':
        return 'Bereder uppdrag(%s)' % _s(indata.get('rubrik'), 100)
    if kort == 'backlog_beslut':
        return 'Backlogbeslut(%s %s)' % (g('beslut'), g('overlamning'))
    if kort == 'backlog':
        return 'Backlog(%s)' % ('alla' if indata.get('alla') else '')
    if kort == 'utred':
        return 'Registrerar utredning(%s)' % _s(indata.get('rubrik'), 100)
    if namn == 'WebSearch':
        return 'Webbsökning("%s")' % _s(indata.get('query'), 120)
    if namn == 'WebFetch':
        return 'Hämtar(%s)' % _s(indata.get('url'), 160)
    if namn in ('Agent', 'Task'):
        typ = _s(indata.get('subagent_type'), 40)
        besk = _s(indata.get('description'), 120)
        return ('Utredaren(%s)' % besk) if typ in ('', 'utredare') else 'Agent(%s: %s)' % (typ, besk)
    if namn == 'Bash':
        return 'Bash(%s)' % _s(indata.get('command'), 120)
    if namn in ('Read', 'Edit', 'MultiEdit', 'Write', 'NotebookEdit'):
        extra = ''
        if namn == 'Read' and (indata.get('offset') or indata.get('limit')):
            extra = ', rad %s%s' % (indata.get('offset') or 1, ' +%s' % indata['limit'] if indata.get('limit') else '')
        return '%s(%s%s)' % (namn, kortsokvag(indata.get('file_path') or indata.get('notebook_path')), extra)
    if namn in ('Grep', 'Glob'):
        return '%s("%s"%s)' % (namn, _s(indata.get('pattern'), 80), ', ' + kortsokvag(indata['path']) if indata.get('path') else '')
    if namn == 'SendMessage':
        return 'SendMessage(→ %s)' % g('to', 'recipient')
    if namn == 'ToolSearch':
        return 'ToolSearch("%s")' % _s(indata.get('query'), 80)
    if namn == 'TodoWrite':
        return 'TodoWrite(%d punkter)' % len(indata.get('todos') or [])
    if namn == 'Skill':
        return 'Skill(%s)' % g('skill')
    if namn in ('ListAgents', 'ListMcpResourcesTool'):
        return '%s()' % namn
    return '%s(%s)' % (namn or 'verktyg', _s(json.dumps(_krymp(indata, 60, 4), ensure_ascii=False), 100) if indata else '')


def beskrivning(namn: str, indata) -> str:
    """Modellens egen förklaring när verktyget bär en (Bash description, SendMessage summary, Agent description)."""
    indata = indata if isinstance(indata, dict) else {}
    if namn == 'Bash':
        return _s(indata.get('description'), 200)
    if namn == 'SendMessage':
        return _s(indata.get('summary'), 200)
    return ''


def indata_text(namn: str, indata) -> str:
    """Kort indata att fälla ut: hela kommandot, frågan eller sökvägen, aldrig filinnehåll eller prompter."""
    indata = indata if isinstance(indata, dict) else {}
    kort = (namn or '').replace('mcp__partner__', '')
    for nyckel in ('command', 'query', 'url', 'fraga', 'monster', 'pattern', 'sokvag', 'file_path', 'notebook_path', 'id'):
        if indata.get(nyckel) not in (None, ''):
            v = _s(indata[nyckel], INDATA_MAX)
            if kort in ('repo_las', 'repo_sok', 'repo_historik') and indata.get('repo'):
                v = '%s: %s' % (_s(indata['repo'], 40), v)
            if namn in ('Grep', 'Glob') and indata.get('path'):
                v = '%s i %s' % (v, _s(indata['path'], 200))
            return tvatta(v)
    return tvatta(_s(json.dumps(_krymp(indata, 120, 8), ensure_ascii=False), INDATA_MAX)) if indata else ''


# ------------------------------------------------------------------ sammanfattning av resultat
def sammanfatta_resultat(namn: str, block: dict, tur) -> tuple:
    """(resultat, data) ur ett tool_result-block och Claude Codes `tool_use_result`, som är en dict för inbyggda
    verktyg (Bash: stdout/stderr/interrupted; Edit: filePath/structuredPatch/originalFile; Read: file.content), en
    lista innehållsblock för MCP-verktyg och saknas för ren text. Hela filer läses aldrig."""
    fel = bool(block.get('is_error'))
    text = _blocktext(block.get('content'))
    data = {}
    utdrag = None
    if not namn:  # ett resultat vars anrop tolken aldrig såg: bara första raden, aldrig ett längre utdrag
        tur, text = None, _forsta_rad(text)
    if isinstance(tur, dict):
        if namn == 'Bash':
            ut, err = str(tur.get('stdout') or ''), str(tur.get('stderr') or '')
            data = {'avbruten': bool(tur.get('interrupted')), 'stderr_rader': len([r for r in err.splitlines() if r.strip()])}
            text = err if (fel and err.strip()) or not ut.strip() else ut
            if data['avbruten']:
                utdrag = 'Avbrutet'
        elif namn in ('Edit', 'MultiEdit', 'Write', 'NotebookEdit'):
            plus = minus = hunkar = 0
            for h in tur.get('structuredPatch') or []:
                if not isinstance(h, dict):
                    continue
                hunkar += 1
                for rad in h.get('lines') or []:
                    if isinstance(rad, str):
                        plus += rad.startswith('+')
                        minus += rad.startswith('-')
            fil = kortsokvag(tur.get('filePath'))
            data = {'fil': fil, 'plus': plus, 'minus': minus, 'hunkar': hunkar}
            utdrag = '%s: +%d −%d' % (fil, plus, minus) if hunkar else ('%s skriven' % fil if fil else 'skriven')
            text = ''  # aldrig originalFile, oldString, newString eller innehållet
        elif namn == 'Read':
            f = tur.get('file') if isinstance(tur.get('file'), dict) else {}
            n, start = f.get('numLines'), f.get('startLine')
            utdrag = '%s rader' % n if n is not None else 'läst'
            if start and f.get('totalLines') and n:
                utdrag = 'rader %s–%s av %s' % (start, int(start) + int(n) - 1, f['totalLines'])
            data = {'fil': kortsokvag(f.get('filePath')), 'rader': n}
            text = ''
        elif namn == 'WebSearch':
            traffar = 0
            for r in tur.get('results') or []:
                if isinstance(r, dict):
                    traffar += len([c for c in (r.get('content') or []) if isinstance(c, dict) and c.get('url')])
            data = {'traffar': traffar, 'sekunder': tur.get('durationSeconds')}
            utdrag = '%d träffar' % traffar
        else:
            text = text or _s(json.dumps(_krymp(tur, 200, 10), ensure_ascii=False), UTDRAG_LANG)
    elif isinstance(tur, list) and not text:
        text = _blocktext(tur)
    if utdrag is None:
        utdrag = _forsta_rad(text)
    if fel and utdrag and not utdrag.lower().startswith(('fel', 'error', 'exit')):
        utdrag = 'Fel: ' + utdrag
    resultat = {'utdrag': tvatta(utdrag)[:UTDRAG_KORT], 'utdrag_lang': tvatta(text[:UTDRAG_LANG]) if text.strip() else '',
                'storlek': len(text), 'rader': len(text.splitlines()) if text.strip() else 0, 'fel': fel}
    return resultat, data


# ------------------------------------------------------------------ tolken
class Tolk:
    """Händelser ur en ström → rader (utan n och tid; Logg stämplar), en fas och räknare. En tolk per körning."""

    def __init__(self, utforare: str = 'claude', egen_start: bool = False):
        self.utforare = utforare
        self.egen_start = egen_start  # mottagarsessioner: system/init blir en startrad (partnerns turer har redan en)
        self.fas = {'lage': 'start', 'sedan': time.time(), 'tankt_tokens': 0, 'verktyg': None, 'forsok': None}
        self.raknare = {'meddelanden': 0, 'verktyg': 0, 'fel': 0, 'underagent': {'meddelanden': 0, 'verktyg': 0},
                        'tokens_in': 0, 'cache_lasta': 0, 'cache_skrivna': 0, 'tokens_ut': 0, 'tankt_tokens': 0,
                        'kontext': None, 'komprimeringar': 0, 'omforsok': 0, 'kvot': None, 'modell': None, 'cli': None,
                        'varv': None, 'kostnad_usd': None, 'utan_tolkning': 0, 'session': None}
        self._oppna = {}      # verktygets id → {'namn', 't0', 'ts', 'huvud'}
        self._medd = set()    # sedda meddelande-id: message_start finns bara med --include-partial-messages
        self._kvot_nyckel = None
        self._las = threading.Lock()
        self.slut = False

    # -- läsning
    def lage(self) -> dict:
        with self._las:
            f = dict(self.fas)
            r = json.loads(json.dumps(self.raknare))
        sedan = f.pop('sedan', time.time())
        f['sedan'] = _iso(sedan)
        f['sekunder'] = max(0, int(time.time() - sedan))
        v = f.get('verktyg')
        if isinstance(v, dict) and 'sedan' in v:
            v = dict(v)
            v['sekunder'] = max(v.get('sekunder') or 0, int(time.time() - v.pop('sedan')))
            f['verktyg'] = v
        f['utan_tolkning'] = r['utan_tolkning']
        return {'fas': f, 'raknare': r}

    def mata(self, ev) -> list:
        """En händelse → noll eller flera rader. Fel i tolkningen blir en varningsrad; de stoppar aldrig något."""
        if not isinstance(ev, dict):
            return []
        with self._las:
            try:
                return self._claude(ev) if self.utforare == 'claude' else self._codex(ev)
            except Exception as fel:  # en okänd form får inte stoppa körningen
                self.raknare['utan_tolkning'] += 1
                return [{'typ': 'varning', 'text': 'tolkningsfel (%s) för %s' % (type(fel).__name__, _s(ev.get('type'), 40))}]

    # -- fas
    def _fas(self, lage: str, **extra) -> None:
        if lage not in LAGE_FAS:
            lage = 'svarar'
        if lage != self.fas['lage']:
            self.fas['lage'] = lage
            self.fas['sedan'] = time.time()
        if lage not in ('verktyg',):
            self.fas['verktyg'] = None
        if lage not in ('omforsok',):
            self.fas['forsok'] = None
        self.fas.update(extra)

    def _oppna_verktyg(self, vid: str, namn: str, ts, huvud: bool) -> None:
        if vid:
            self._oppna[vid] = {'namn': namn, 't0': time.time(), 'ts': _epoch(ts), 'huvud': huvud}
            if len(self._oppna) > 500:  # ett resultat som aldrig kom; glöm det äldsta
                self._oppna.pop(next(iter(self._oppna)))
        if huvud:
            self._fas('verktyg', verktyg={'id': vid, 'namn': namn, 'sedan': time.time(), 'sekunder': 0})

    def _stang_verktyg(self, vid: str, ts) -> tuple:
        """(öppnad post eller None, ms eller None)"""
        post = self._oppna.pop(vid, None) if vid else None
        ms = None
        if post:
            t1 = _epoch(ts)
            if post.get('ts') is not None and t1 is not None and t1 >= post['ts']:
                ms = int(round((t1 - post['ts']) * 1000))
            else:
                ms = int(round((time.time() - post['t0']) * 1000))
        if (self.fas.get('verktyg') or {}).get('id') == vid or not self._oppna:
            self._fas('svarar')
        return post, ms

    def _verktygsrad(self, vid: str, namn: str, indata, huvud: bool, foralder=None) -> dict:
        rad = {'typ': 'verktyg' if huvud else 'utredare', 'id': vid or None, 'foralder': foralder or None, 'verktyg': namn,
               'text': tvatta(beskriv(namn, indata))[:TEXT_MAX], 'indata': indata_text(namn, indata), 'status': 'pagar'}
        besk = beskrivning(namn, indata)
        if besk:
            rad['beskrivning'] = tvatta(besk)
        (self.raknare if huvud else self.raknare['underagent'])['verktyg'] += 1
        return rad

    def _resultatrad(self, vid: str, namn: str, block: dict, tur, ms) -> dict:
        resultat, data = sammanfatta_resultat(namn, block, tur)
        if resultat['fel']:
            self.raknare['fel'] += 1
        return {'typ': 'resultat', 'id': vid or None, 'status': 'fel' if resultat['fel'] else 'klar', 'ms': ms,
                'resultat': resultat, 'data': data}

    # -- Claude Code
    def _claude(self, ev: dict) -> list:
        typ = ev.get('type')
        foralder = ev.get('parent_tool_use_id') or None
        huvud = foralder is None
        ts = ev.get('timestamp')
        if typ == 'system':
            return self._claude_system(ev)
        if typ == 'stream_event':
            e = ev.get('event') if isinstance(ev.get('event'), dict) else {}
            et = e.get('type')
            if et == 'message_start' and huvud:
                m = e.get('message') if isinstance(e.get('message'), dict) else {}
                self._meddelande(m.get('id'), m.get('usage'))
                self.fas['tankt_tokens'] = 0
                self._fas('svarar')
            elif et == 'message_start':
                self.raknare['underagent']['meddelanden'] += 1
            elif et == 'message_delta' and huvud:
                u = e.get('usage') if isinstance(e.get('usage'), dict) else {}
                self.raknare['tokens_ut'] += int(u.get('output_tokens') or 0)
            elif et == 'content_block_start' and huvud:
                b = e.get('content_block') if isinstance(e.get('content_block'), dict) else {}
                if b.get('type') == 'thinking':
                    self._fas('tanker')
                elif b.get('type') == 'tool_use':
                    self._fas('verktyg', verktyg={'id': b.get('id'), 'namn': b.get('name'), 'sedan': time.time(), 'sekunder': 0})
                elif b.get('type') == 'text':
                    self._fas('svarar')
            elif et == 'content_block_delta' and huvud:
                d = e.get('delta') if isinstance(e.get('delta'), dict) else {}
                if d.get('type') == 'thinking_delta':
                    n = d.get('estimated_tokens')
                    self._fas('tanker', tankt_tokens=int(n) if isinstance(n, (int, float)) else self.fas['tankt_tokens'])
                elif d.get('type') == 'text_delta':
                    self._fas('svarar')
            return []
        if typ == 'assistant':
            rader = []
            msg = ev.get('message') if isinstance(ev.get('message'), dict) else {}
            if huvud:  # utan partiella meddelanden är detta enda stället där meddelandet och dess usage syns
                self._meddelande(msg.get('id'), msg.get('usage'))
            for b in msg.get('content') or []:
                if not isinstance(b, dict):
                    continue
                if b.get('type') == 'tool_use':
                    vid, namn = str(b.get('id') or ''), str(b.get('name') or 'verktyg')
                    self._oppna_verktyg(vid, namn, ts, huvud)
                    rader.append(self._verktygsrad(vid, namn, b.get('input'), huvud, foralder))
                elif b.get('type') == 'text' and huvud and str(b.get('text') or '').strip():
                    rader.append({'typ': 'text', 'text': tvatta(_s(b['text'], TEXT_MAX))})
            return rader
        if typ == 'user':
            rader = []
            msg = ev.get('message') if isinstance(ev.get('message'), dict) else {}
            innehall = msg.get('content')
            if not isinstance(innehall, list):
                return []
            block = [b for b in innehall if isinstance(b, dict) and b.get('type') == 'tool_result']
            tur = ev.get('tool_use_result') if len(block) == 1 else None  # ett tool_use_result hör till exakt ett resultat
            for b in block:
                vid = str(b.get('tool_use_id') or '')
                post, ms = self._stang_verktyg(vid, ts)
                namn = (post or {}).get('namn') or ''
                rader.append(self._resultatrad(vid, namn, b, tur, ms))
            return rader
        if typ == 'rate_limit_event':
            return self._kvot(ev.get('rate_limit_info') if isinstance(ev.get('rate_limit_info'), dict) else {})
        if typ == 'tool_progress':
            v = self.fas.get('verktyg')
            if isinstance(v, dict) and v.get('id') == ev.get('tool_use_id') and isinstance(ev.get('elapsed_time_seconds'), (int, float)):
                v['sekunder'] = int(ev['elapsed_time_seconds'])
            return []
        if typ == 'result':
            return [self._claude_slut(ev)]
        if typ in ('command_lifecycle',):
            return []
        self.raknare['utan_tolkning'] += 1
        return []

    def _claude_system(self, ev: dict) -> list:
        st = ev.get('subtype')
        if st == 'init':
            self.raknare['modell'] = _s(ev.get('model'), 80) or self.raknare['modell']
            self.raknare['cli'] = _s(ev.get('claude_code_version'), 40) or None
            self.raknare['session'] = _s(ev.get('session_id'), 80) or None
            self._fas('begar')
            if self.egen_start:
                return [{'typ': 'start', 'text': 'Sessionen startade (%s%s)' % (
                    self.raknare['modell'] or 'okänd modell', ', Claude Code ' + self.raknare['cli'] if self.raknare['cli'] else ''),
                    'data': {'modell': self.raknare['modell'], 'cli': self.raknare['cli'],
                             'permission': _s(ev.get('permissionMode'), 20) or None}}]
            return []
        if st == 'status':
            s = ev.get('status')
            if s == 'requesting':
                self._fas('begar')
            elif s == 'compacting':
                self._fas('komprimerar')
            elif s is None:
                self._fas('verktyg' if self.fas.get('verktyg') else 'svarar', verktyg=self.fas.get('verktyg'))
            return []
        if st == 'thinking_tokens':
            n = ev.get('estimated_tokens_delta')
            if isinstance(n, (int, float)):
                self.raknare['tankt_tokens'] += int(n)
            tot = ev.get('estimated_tokens')
            self._fas('tanker', tankt_tokens=int(tot) if isinstance(tot, (int, float)) else self.fas['tankt_tokens'])
            return []
        if st == 'compact_boundary':
            m = ev.get('compact_metadata') if isinstance(ev.get('compact_metadata'), dict) else {}
            self.raknare['komprimeringar'] += 1
            self._fas('svarar')
            fore, efter = m.get('pre_tokens'), m.get('post_tokens')
            return [{'typ': 'komprimering', 'text': 'Komprimerade sammanhanget%s%s' % (
                ' · %s → %s tokens' % (_k(fore), _k(efter)) if fore is not None and efter is not None else '',
                ' · ' + _tid(m['duration_ms']) if isinstance(m.get('duration_ms'), (int, float)) else ''),
                'data': {'utlosare': _s(m.get('trigger'), 20) or None, 'fore': fore, 'efter': efter, 'ms': m.get('duration_ms')}}]
        if st == 'api_retry':
            self.raknare['omforsok'] += 1
            forsok = ev.get('attempt')
            self._fas('omforsok', forsok=forsok)
            return [{'typ': 'omforsok', 'text': 'Modelltjänsten svarade inte (%s); nytt försök %s.' % (
                _s(ev.get('error') or ev.get('error_status'), 120), forsok)}]
        if st == 'vcs_state_changed':
            if ev.get('kind') == 'push':
                gren = _s(ev.get('branch'), 120)
                return [{'typ': 'push', 'text': 'Push · %s' % gren, 'data': {'gren': gren}}]
            return []
        if st == 'code_change_published':
            url = _s(ev.get('url'), 300)
            m = re.search(r'/pull/(\d+)', url)
            return [{'typ': 'pr', 'text': 'PR%s %s · %s' % (' #' + m.group(1) if m else '',
                                                           {'created': 'skapad', 'updated': 'uppdaterad'}.get(ev.get('action'), _s(ev.get('action'), 20)), url),
                     'data': {'url': url, 'leverantor': _s(ev.get('provider'), 20) or None, 'atgard': _s(ev.get('action'), 20) or None,
                              'nummer': int(m.group(1)) if m else None}}]
        if st == 'task_started':
            return [{'typ': 'uppgift', 'text': 'Bakgrund: %s' % (_s(ev.get('description'), 200) or _s(ev.get('task_type'), 40)),
                     'data': {'uppgift': _s(ev.get('task_id'), 80) or None, 'status': 'startad'}}]
        if st == 'task_notification':
            return [{'typ': 'uppgift', 'text': 'Bakgrund %s: %s' % ({'completed': 'klar', 'failed': 'misslyckad'}.get(ev.get('status'), _s(ev.get('status'), 20)),
                                                                    _s(ev.get('summary') or ev.get('description'), 200)),
                     'data': {'uppgift': _s(ev.get('task_id'), 80) or None, 'status': _s(ev.get('status'), 20) or None}}]
        if st in ('background_tasks_changed', 'task_updated', 'commands_changed', 'hook_started', 'hook_response'):
            return []
        self.raknare['utan_tolkning'] += 1
        return []

    def _meddelande(self, mid, usage) -> None:
        """Ett huvudagentmeddelande räknas en gång, vare sig det syns i message_start, i assistant-händelsen eller båda
        (Claude Code skriver en assistant-händelse per innehållsblock, alla med samma message.id)."""
        nyckel = str(mid or '')
        if nyckel and nyckel in self._medd:
            return
        if nyckel:
            self._medd.add(nyckel)
            if len(self._medd) > 5000:
                self._medd.clear()
        self.raknare['meddelanden'] += 1
        self._tokens_in(usage if isinstance(usage, dict) else {})

    def _tokens_in(self, u: dict) -> None:
        inn, cl, cs = (int(u.get(k) or 0) for k in ('input_tokens', 'cache_read_input_tokens', 'cache_creation_input_tokens'))
        self.raknare['tokens_in'] += inn
        self.raknare['cache_lasta'] += cl
        self.raknare['cache_skrivna'] += cs
        if inn or cl or cs:
            self.raknare['kontext'] = inn + cl + cs

    def _kvot(self, info: dict) -> list:
        f = info.get('unifiedWindows') if isinstance(info.get('unifiedWindows'), dict) else {}
        andel = lambda n: (f.get(n) or {}).get('utilization') if isinstance(f.get(n), dict) else None
        fem, sju = andel('five_hour'), andel('seven_day')
        status = _s(info.get('status'), 20) or None
        aterstalls = info.get('resetsAt') if isinstance(info.get('resetsAt'), (int, float)) else None
        kvot = {'status': status, 'typ': _s(info.get('rateLimitType'), 20) or None, 'fem_timmar': fem, 'sju_dagar': sju,
                'aterstalls': aterstalls}
        self.raknare['kvot'] = kvot
        storst = max([x for x in (fem, sju) if isinstance(x, (int, float))] or [0])
        nyckel = (status, int(storst * 20))
        if nyckel == self._kvot_nyckel or (status in (None, 'allowed') and storst < KVOT_GRANS):
            return []
        self._kvot_nyckel = nyckel
        fonster = 'veckofönstret' if (sju or 0) >= (fem or 0) else 'femtimmarsfönstret'
        text = 'Kvot %d %% av %s' % (round(storst * 100), fonster)
        if status and status != 'allowed':
            text += ' · ' + {'allowed_warning': 'varning', 'rejected': 'stoppad'}.get(status, status)
        if aterstalls:
            text += ' · återställs ' + datetime.fromtimestamp(aterstalls, timezone.utc).strftime('%d/%m %H:%M') + ' UTC'
        return [{'typ': 'kvot', 'text': text, 'data': kvot}]

    def _claude_slut(self, ev: dict) -> dict:
        self.slut = True
        u = ev.get('usage') if isinstance(ev.get('usage'), dict) else {}
        if u:  # resultatets summa är exaktare än de löpande talen
            self.raknare['tokens_in'] = int(u.get('input_tokens') or 0)
            self.raknare['cache_lasta'] = int(u.get('cache_read_input_tokens') or 0)
            self.raknare['cache_skrivna'] = int(u.get('cache_creation_input_tokens') or 0)
            self.raknare['tokens_ut'] = int(u.get('output_tokens') or 0)
        varv = ev.get('num_turns') if isinstance(ev.get('num_turns'), int) else None
        ms = ev.get('duration_ms') if isinstance(ev.get('duration_ms'), (int, float)) else None
        kostnad = ev.get('total_cost_usd') if isinstance(ev.get('total_cost_usd'), (int, float)) else None
        self.raknare.update(varv=varv, kostnad_usd=kostnad)
        subtype = _s(ev.get('subtype'), 40)
        fel = bool(ev.get('is_error')) or subtype != 'success'
        for vid in list(self._oppna):  # verktyg utan resultat vid slutet
            self._oppna.pop(vid, None)
        self._fas('klar')
        delar = []
        if varv is not None:
            delar.append('%d varv' % varv)
        if ms is not None:
            delar.append(_tid(ms))
        text = ('Klart' if not fel else 'Slutade med fel (%s)' % (subtype or 'okänt')) + (' · ' + ' · '.join(delar) if delar else '')
        return {'typ': 'slut', 'text': text, 'status': 'fel' if fel else 'klar',
                'data': {'subtype': subtype or None, 'varv': varv, 'ms': ms, 'kostnad_usd': kostnad, 'is_error': bool(ev.get('is_error')),
                         'stopp': _s(ev.get('terminal_reason') or ev.get('stop_reason'), 40) or None}}

    # -- Codex exec --json
    def _codex(self, ev: dict) -> list:
        typ = ev.get('type')
        item = ev.get('item') if isinstance(ev.get('item'), dict) else {}
        slag = item.get('type')
        iid = str(item.get('id') or '')
        if typ == 'thread.started':
            self.raknare['session'] = _s(ev.get('thread_id'), 80) or None
            self._fas('begar')
            if self.egen_start:
                return [{'typ': 'start', 'text': 'Sessionen startade (Codex)', 'data': {'modell': self.raknare['modell']}}]
            return []
        if typ == 'turn.started':
            self._fas('begar')
            return []
        if typ == 'item.started':
            if slag == 'reasoning':
                self._fas('tanker')
                return []
            if slag == 'agent_message':
                self._fas('svarar')
                return []
            rad = self._codex_verktygsrad(item)
            if rad is None:
                self.raknare['utan_tolkning'] += 1
                return []
            self._oppna_verktyg(iid, rad['verktyg'], None, True)
            return [rad]
        if typ == 'item.updated':
            return []
        if typ == 'item.completed':
            if slag == 'reasoning':
                self._fas('svarar')
                return []
            if slag == 'agent_message':
                text = _s(item.get('text'), TEXT_MAX)
                return [{'typ': 'text', 'text': tvatta(text)}] if text else []
            if slag == 'error':
                text = _s(item.get('message'), 300)
                if CODEX_VARNING in text:
                    return []
                return [{'typ': 'varning', 'text': tvatta(text or 'fel')}]
            if slag in ('todo_list',):
                return []
            rader = []
            if iid not in self._oppna:  # avslutades utan started (t.ex. web_search): båda raderna nu
                rad = self._codex_verktygsrad(item)
                if rad is None:
                    self.raknare['utan_tolkning'] += 1
                    return []
                self._oppna_verktyg(iid, rad['verktyg'], None, True)
                rader.append(rad)
            post, ms = self._stang_verktyg(iid, None)
            rader.append(self._codex_resultatrad(iid, item, ms))
            return rader
        if typ == 'turn.completed':
            u = ev.get('usage') if isinstance(ev.get('usage'), dict) else {}
            inn, cached = int(u.get('input_tokens') or 0), int(u.get('cached_input_tokens') or 0)
            self.raknare.update(tokens_in=max(0, inn - cached), cache_lasta=cached,
                                tokens_ut=int(u.get('output_tokens') or 0) + int(u.get('reasoning_output_tokens') or 0))
            self.slut = True
            self._fas('klar')
            return [{'typ': 'slut', 'text': 'Klart', 'status': 'klar', 'data': {'subtype': 'success', 'is_error': False}}]
        if typ == 'turn.failed':
            fel = ev.get('error') if isinstance(ev.get('error'), dict) else {}
            self.slut = True
            self._fas('klar')
            text = tvatta(_s(fel.get('message'), 300) or 'okänt fel')
            return [{'typ': 'slut', 'text': 'Slutade med fel: ' + text, 'status': 'fel', 'data': {'subtype': 'failed', 'is_error': True}}]
        if typ == 'error':
            self.raknare['omforsok'] += 1
            self._fas('omforsok', forsok=self.raknare['omforsok'])
            return [{'typ': 'omforsok', 'text': 'Codex: ' + tvatta(_s(ev.get('message'), 300) or 'fel')}]
        if typ in ('thread.ended', 'turn.diff'):
            return []
        self.raknare['utan_tolkning'] += 1
        return []

    def _codex_verktygsrad(self, item: dict):
        slag = item.get('type')
        if slag == 'command_execution':  # OVERIFIERAT mot verklig ström: fälten ur Codex SDK:s events.ts
            indata = {'command': item.get('command')}
            return self._verktygsrad(str(item.get('id') or ''), 'Bash', indata, True)
        if slag == 'file_change':  # OVERIFIERAT mot verklig ström
            andringar = [c for c in (item.get('changes') or []) if isinstance(c, dict)]
            rad = self._verktygsrad(str(item.get('id') or ''), 'Edit', {'file_path': (andringar[0].get('path') if andringar else '')}, True)
            if len(andringar) > 1:
                rad['text'] = 'Edit(%d filer)' % len(andringar)
            return rad
        if slag == 'mcp_tool_call':
            namn = 'mcp__%s__%s' % (_s(item.get('server'), 40) or 'partner', _s(item.get('tool'), 60))
            return self._verktygsrad(str(item.get('id') or ''), namn, item.get('arguments') or {}, True)
        if slag == 'web_search':
            handling = item.get('action') if isinstance(item.get('action'), dict) else {}
            if handling.get('type') == 'open_page':
                return self._verktygsrad(str(item.get('id') or ''), 'WebFetch', {'url': handling.get('url')}, True)
            return self._verktygsrad(str(item.get('id') or ''), 'WebSearch', {'query': item.get('query')}, True)
        return None

    def _codex_resultatrad(self, iid: str, item: dict, ms) -> dict:
        slag = item.get('type')
        fel = item.get('status') == 'failed'
        text, utdrag, data = '', None, {}
        if slag == 'command_execution':
            kod = item.get('exit_code')
            text = str(item.get('aggregated_output') or '')
            data = {'exit': kod}
            utdrag = ('exit %s' % kod if kod is not None else '') + (' · ' + _forsta_rad(text) if text.strip() else '')
            fel = fel or (isinstance(kod, int) and kod != 0)
        elif slag == 'file_change':
            andringar = [c for c in (item.get('changes') or []) if isinstance(c, dict)]
            utdrag = ', '.join('%s %s' % (_s(c.get('kind'), 10), kortsokvag(c.get('path'))) for c in andringar[:6])[:UTDRAG_KORT] or 'ändrad'
            data = {'filer': len(andringar)}
        elif slag == 'mcp_tool_call':
            r = item.get('result')
            text = _blocktext(r.get('content')) if isinstance(r, dict) else (str(r) if isinstance(r, str) else '')
            if fel:
                f = item.get('error') if isinstance(item.get('error'), dict) else {}
                text = _s(f.get('message'), UTDRAG_LANG) or text or 'verktyget gav ett fel'
        elif slag == 'web_search':
            resultat = [r for r in (item.get('results') or []) if isinstance(r, dict)]
            utdrag = '%d träffar' % len(resultat)
            data = {'traffar': len(resultat)}
        else:
            text = _s(json.dumps(_krymp(item, 200, 10), ensure_ascii=False), UTDRAG_LANG)
        if utdrag is None:
            utdrag = _forsta_rad(text)
        if fel and utdrag and not utdrag.lower().startswith(('fel', 'error', 'exit')):
            utdrag = 'Fel: ' + utdrag
        if fel:
            self.raknare['fel'] += 1
        return {'typ': 'resultat', 'id': iid or None, 'status': 'fel' if fel else 'klar', 'ms': ms, 'data': data,
                'resultat': {'utdrag': tvatta(utdrag)[:UTDRAG_KORT], 'utdrag_lang': tvatta(text[:UTDRAG_LANG]) if text.strip() else '',
                             'storlek': len(text), 'rader': len(text.splitlines()) if text.strip() else 0, 'fel': fel}}


# ------------------------------------------------------------------ loggen
class Logg:
    """Körningshändelserna i ordning: minne (hela loggen; tak per rad, inte per logg) och, när `fil` anges, en rad
    per händelse i `handelser.jsonl` (0600, bara tillägg, ingen långlivad fildeskriptor). Filen är sanningen efter en
    krasch; minnet är det servern svarar ur medan körningen pågår."""

    def __init__(self, fil: Path | None = None):
        self.fil = Path(fil) if fil else None
        self._rader = []
        self._las = threading.Lock()
        self.filfel = None

    @property
    def nasta(self) -> int:
        with self._las:
            return len(self._rader)

    def lagg(self, rad: dict) -> dict:
        return self.lagg_flera([rad])[0]

    def lagg_flera(self, rader: list) -> list:
        ut = []
        with self._las:
            for rad in rader:
                if not isinstance(rad, dict) or not rad.get('typ'):
                    continue
                r = dict(rad)
                r['n'] = len(self._rader)
                r.setdefault('tid', nu())
                if isinstance(r.get('text'), str):
                    r['text'] = r['text'][:TEXT_MAX]
                self._rader.append(r)
                ut.append(r)
                self._skriv(r)
        return ut

    def _skriv(self, r: dict) -> None:
        if not self.fil:
            return
        try:
            fd = os.open(self.fil, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
            try:
                os.write(fd, (json.dumps(r, ensure_ascii=False, separators=(',', ':')) + '\n').encode('utf-8'))
            finally:
                os.close(fd)
        except OSError as fel:
            self.filfel = type(fel).__name__

    def fran(self, n: int = 0, max_: int = 500) -> tuple:
        """(rader från och med n, nästa n). n bortom slutet ger tomt; n under noll räknas som noll."""
        with self._las:
            n = max(0, int(n or 0))
            return [dict(r) for r in self._rader[n:n + max_]], len(self._rader)

    def alla(self) -> list:
        with self._las:
            return [dict(r) for r in self._rader]

    def steg(self, max_: int = 60) -> list:
        with self._las:
            return steg_ur(self._rader, max_)


def steg_ur(rader: list, max_: int = 60) -> list:
    """Journalens korta form `{tid, typ, text}` ur händelseraderna: anrop med sitt utfall ihopvikt, utan resultat-,
    mellanrads- och bakgrundsrader. Samma form som före PARTNER-INSYN-20261001, så äldre läsare fungerar."""
    ut, per_id = [], {}
    for r in rader:
        typ = r.get('typ')
        if typ == 'resultat':
            s = per_id.get(r.get('id'))
            if s is not None:
                res = r.get('resultat') or {}
                if res.get('fel') or r.get('status') == 'fel':
                    s['text'] = (s['text'] + ' · fel')[:TEXT_MAX]
                elif isinstance(r.get('ms'), (int, float)) and r['ms'] >= 2000:
                    s['text'] = (s['text'] + ' · ' + _tid(r['ms']))[:TEXT_MAX]
            continue
        if typ in STEG_UTAN or not typ:
            continue
        s = {'tid': r.get('tid'), 'typ': typ, 'text': str(r.get('text') or '')[:TEXT_MAX]}
        if typ in ('verktyg', 'utredare') and r.get('id'):
            per_id[r['id']] = s
        ut.append(s)
    return ut[-max_:]


def sammanfatta(rader: list) -> dict:
    """Räknare ur sparade händelserader, för en avslutad körning eller en milstolpsremsa: antal anrop, fel, nekade,
    komprimeringar, omförsök, push och PR, samt sista slutraden."""
    s = {'verktyg': 0, 'utredare': 0, 'fel': 0, 'nekat': 0, 'komprimeringar': 0, 'omforsok': 0, 'push': 0, 'pr': 0,
         'andringar': 0, 'slut': None}
    for r in rader:
        typ = r.get('typ')
        if typ in ('verktyg', 'utredare'):
            s[typ] += 1
            if r.get('verktyg') in ('Edit', 'MultiEdit', 'Write', 'NotebookEdit'):
                s['andringar'] += 1
        elif typ == 'resultat':
            if (r.get('resultat') or {}).get('fel') or r.get('status') == 'fel':
                s['fel'] += 1
        elif typ == 'nekat':
            s['nekat'] += 1
        elif typ == 'komprimering':
            s['komprimeringar'] += 1
        elif typ == 'omforsok':
            s['omforsok'] += 1
        elif typ in ('push', 'pr'):
            s[typ] += 1
        elif typ == 'slut':
            s['slut'] = {'text': r.get('text'), 'status': r.get('status'), 'data': r.get('data')}
    return s


def las_handelser(fil: Path, fran: int = 0, max_: int = 2000) -> tuple:
    """Filreserv för en avslutad körning: (rader från n, totalt antal). En ofullständig sista rad hoppas över, som i
    journalen. Saknas filen är svaret ([], 0)."""
    fil = Path(fil)
    try:
        if fil.is_symlink() or not fil.is_file():
            return [], 0
        fd = os.open(fil, os.O_RDONLY | os.O_NOFOLLOW)
        with os.fdopen(fd, 'rb') as f:
            if os.fstat(f.fileno()).st_size > FIL_MAX:
                return [], 0
            data = f.read(FIL_MAX)
    except OSError:
        return [], 0
    rader = []
    for linje in data.split(b'\n'):
        if not linje.strip():
            continue
        try:
            r = json.loads(linje.decode('utf-8'))
        except ValueError:
            continue
        if isinstance(r, dict) and r.get('typ'):
            rader.append(r)
    fran = max(0, int(fran or 0))
    return rader[fran:fran + max_], len(rader)


# ------------------------------------------------------------------ svansläsning av en ström som någon annan skriver
class Svans:
    """Läser nya rader ur en JSONL-fil som en annan process skriver (mottagarsessionens `korning-NN.jsonl`): byteoffset,
    en ofullständig sista rad hålls tillbaka tills radslutet kommit, filen prövas som vanlig fil utan länk, och ett
    inode-byte eller en krympning börjar om från början."""

    def __init__(self, fil: Path):
        self.fil = Path(fil)
        self.offset = 0
        self.rest = b''
        self.inode = None
        self.ogiltiga = 0

    def las(self) -> list:
        if self.fil.is_symlink():
            raise ValueError('länk vägras')
        try:
            fd = os.open(self.fil, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        except FileNotFoundError:
            return []
        try:
            st = os.fstat(fd)
            if not stat.S_ISREG(st.st_mode):
                raise ValueError('inte en vanlig fil')
            if self.inode is not None and (st.st_ino != self.inode or st.st_size < self.offset):
                self.offset, self.rest = 0, b''
            self.inode = st.st_ino
            if st.st_size <= self.offset:
                return []
            os.lseek(fd, self.offset, os.SEEK_SET)
            data = os.read(fd, min(SVANS_MAX, st.st_size - self.offset))
        finally:
            os.close(fd)
        self.offset += len(data)
        buf = self.rest + data
        linjer = buf.split(b'\n')
        self.rest = linjer[-1]
        ut = []
        for linje in linjer[:-1]:
            if not linje.strip():
                continue
            try:
                ev = json.loads(linje.decode('utf-8'))
            except ValueError:
                self.ogiltiga += 1
                continue
            if isinstance(ev, dict):
                ut.append(ev)
        return ut
