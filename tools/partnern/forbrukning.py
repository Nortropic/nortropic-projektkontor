"""Modellfri, källbunden förbrukning ur mottagarens sparade JSONL-strömmar.

Claude usage avser huvudloopen per tur. Codex 0.155.1 skriver trådens
kumulativa usage.total; fortsättningar får därför inte summeras en gång till.
Inga kostnader beräknas. Oredovisade underagenters kvot är inte känd.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import tempfile
from datetime import datetime
from pathlib import Path

SCHEMA = 'overlamningsforbrukning/1'
MAX_BYTES = 64 * 1024 * 1024
FALT = ('tokens_in', 'tokens_ut', 'cache_lasta', 'cache_skrivna', 'modellsvar', 'komprimeringar', 'vaggsekunder')


def las_fil(path: Path) -> bytes:
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError('länk vägras')
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as f:
        st = os.fstat(f.fileno())
        if not stat.S_ISREG(st.st_mode) or st.st_size > MAX_BYTES:
            raise ValueError('inte en begränsad vanlig fil')
        raw = f.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError('filen överstiger läsgränsen')
    return raw


def tal(value, sources, reason=None):
    return {'varde': value, 'kallor': sources, 'skal': reason}


def _rows(path, relative):
    raw = las_fil(path)
    digest = hashlib.sha256(raw).hexdigest()
    rows = []
    for nr, line in enumerate(raw.decode('utf-8').splitlines(), 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except ValueError:
            value = None
        rows.append((value, {'fil': relative, 'rad': nr, 'sha256': digest}))
    return rows, {'fil': relative, 'sha256': digest}


def _number(value):
    return type(value) is int and value >= 0


def _sum(values):
    sources = [s for v in values for s in v['kallor']]
    if not values or any(v['varde'] is None for v in values):
        return tal(None, sources, 'minst en uppgift saknas eller är okänd')
    return tal(sum(v['varde'] for v in values), sources)


def _usage(rows, key, closed):
    values = []
    for row, source in rows:
        usage = row.get('usage')
        value = usage.get(key) if isinstance(usage, dict) else None
        values.append(tal(value if _number(value) else None, [dict(source, falt='usage.'+key)]))
    return _sum(values) if closed else tal(None, [s for _, s in rows], 'strömmen saknar giltigt avslut')


def _run(path, relative, starts):
    rows, source = _rows(path, relative)
    events = [(e, s) for e, s in rows if isinstance(e, dict)]
    valid = bool(rows) and len(events) == len(rows)
    claude = any(e.get('type') == 'result' or (e.get('type') == 'system' and e.get('subtype') == 'init') for e, _ in events)
    codex = any(e.get('type') in ('thread.started', 'turn.completed', 'turn.failed') for e, _ in events)
    provider = 'claude' if claude and not codex else 'codex' if codex and not claude else None
    endings = [(e, s) for e, s in events if e.get('type') == ('result' if provider == 'claude' else 'turn.completed')]
    closed = valid and bool(endings) and events[-1][0].get('type') == ('result' if provider == 'claude' else 'turn.completed')
    fields = {k: tal(None, [source], 'okänd strömform') for k in FALT}
    thread_ids = {e.get('thread_id') for e, _ in events if e.get('type') == 'thread.started'}
    thread = next(iter(thread_ids)) if len(thread_ids) == 1 else None
    thread = thread if isinstance(thread, str) and thread.strip() else None
    if provider:
        # Codex totals are cumulative within this stream as well as on resume.
        usage_rows = endings[-1:] if provider == 'codex' else endings
        mapping = {'tokens_in':'input_tokens', 'tokens_ut':'output_tokens',
                   'cache_lasta':'cached_input_tokens' if provider == 'codex' else 'cache_read_input_tokens',
                   'cache_skrivna':'cache_write_input_tokens' if provider == 'codex' else 'cache_creation_input_tokens'}
        fields.update({k:_usage(usage_rows, key, closed) for k, key in mapping.items()})
        if provider == 'codex':
            inp, cache = fields['tokens_in'], fields['cache_lasta']
            fields['tokens_in'] = tal(inp['varde']-cache['varde'] if inp['varde'] is not None and cache['varde'] is not None and inp['varde']>=cache['varde'] else None,
                                     inp['kallor']+cache['kallor'], 'input_tokens minus cached_input_tokens; cache separat')
        messages = [(e.get('message'), s) for e, s in events if e.get('type') == 'assistant' and not e.get('parent_tool_use_id')] if provider == 'claude' else [
            (e.get('item'), s) for e, s in events if e.get('type') == 'item.completed' and isinstance(e.get('item'), dict) and e['item'].get('type') == 'agent_message']
        ids = [m.get('id') if isinstance(m, dict) else None for m, _ in messages]
        fields['modellsvar'] = tal(len(set(ids)) if closed and all(isinstance(i,str) and i for i in ids) else None,
                                  [s for _,s in messages] or [source], 'unika huvudloopsvar i strömmen; inte alla interna modellanrop')
        compact = [s for e,s in events if e.get('type') == 'system' and e.get('subtype') == 'compact_boundary']
        fields['komprimeringar'] = tal(len(compact) if provider == 'claude' and closed else None,
                                      compact or [source], None if provider == 'claude' and closed else 'Codex exec-strömmen redovisar inte komprimeringar, eller avslut saknas')
    nr = int(re.fullmatch(r'korning-(\d+)\.jsonl', path.name)[1])
    matched = [(i,e,s) for i,(e,s) in enumerate(starts) if isinstance(e,dict) and e.get('typ')=='startad' and e.get('nr')==nr]
    fields['vaggsekunder'] = tal(None, [source], 'start och avslut saknas i START.jsonl')
    if len(matched)==1:
        index, begin, begin_source = matched[0]
        if index+1<len(starts):
            end,end_source=starts[index+1]
            if isinstance(end,dict) and end.get('typ') in ('klar','avslutad','misslyckad','avbruten','vantar'):
                try:
                    a,b=(datetime.fromisoformat(e['tid'].replace('Z','+00:00')) for e in (begin,end))
                    seconds=(b-a).total_seconds()
                    if a.tzinfo is None or b.tzinfo is None or seconds<0:raise ValueError()
                    fields['vaggsekunder']=tal(round(seconds,3),[begin_source,end_source], 'startvaktens observationstid; kan inkludera väntan till uppföljning')
                except (KeyError,TypeError,ValueError,AttributeError):pass
    return {'fil':relative, 'utforare':provider, 'trad':thread, 'slutford':closed, 'kalla':source, 'tal':fields}


def rakna(kat: Path) -> dict:
    session = kat/'session'
    if any(p.is_symlink() for p in (session,*session.parents)):
        raise ValueError('sessionsvägen är en länk')
    files = sorted((p for p in session.iterdir() if re.fullmatch(r'korning-\d+\.jsonl',p.name)),
                   key=lambda p:int(p.stem.split('-')[1]))
    if not files:raise ValueError('ingen sparad körningsström')
    try:starts,_ = _rows(kat/'START.jsonl','START.jsonl')
    except (OSError,ValueError,UnicodeError):starts=[]
    runs=[]
    for path in files:
        try:runs.append(_run(path,'session/'+path.name,starts))
        except (OSError,ValueError,UnicodeError):
            source={'fil':'session/'+path.name}
            runs.append({'fil':source['fil'],'utforare':None,'trad':None,'slutford':False,'kalla':source,
                         'tal':{k:tal(None,[source],'strömmen går inte att läsa') for k in FALT}})
    # Preserve all streams in the report. Select only the latest cumulative
    # Codex totals per thread for aggregation; never sum repeated resume totals.
    selected=[];latest={}; reset=set()
    for run in runs:
        if run['utforare']=='codex' and run['trad']:
            previous=latest.get(run['trad'])
            if previous:
                for key in ('tokens_in','tokens_ut','cache_lasta','cache_skrivna'):
                    before,after=previous['tal'][key]['varde'],run['tal'][key]['varde']
                    if before is not None and after is not None and after<before:reset.add(key)
            latest[run['trad']]=run
        else:selected.append(run)
    selected+=list(latest.values())
    totals={k:_sum([r['tal'][k] for r in (selected if k.startswith(('tokens','cache')) else runs)]) for k in FALT}
    for key in reset:totals[key]=tal(None,totals[key]['kallor'],'kumulativt Codex-tal minskade; återställningens omfattning okänd')
    expected={e.get('nr') for e,_ in starts if isinstance(e,dict) and e.get('typ')=='startad' and type(e.get('nr')) is int}
    present={int(p.stem.split('-')[1]) for p in files}
    missing=sorted(expected-present)
    if missing or any(r['utforare']=='codex' and not r['trad'] for r in runs):
        totals={k:tal(None,v['kallor'],'körningsström eller Codex-trådbindning saknas') for k,v in totals.items()}
    totals['korningar']=tal(len(runs) if not missing else None,[r['kalla'] for r in runs], 'antal sparade körningsströmmar')
    return {'schema':SCHEMA,'omfattning':'sparad huvudloop; inte abonnemangets återstående kvot eller oredovisade underagenter',
            'korningar':runs,'saknade_strommar':missing,'tal':totals}


def spara(kat: Path) -> dict:
    result=rakna(kat)
    fd,name=tempfile.mkstemp(prefix='.forbrukning-',dir=kat)
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as f:
            json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
        target=kat/'FORBRUKNING.json'
        if target.is_symlink():raise ValueError('förbrukningsfilen är en länk')
        os.replace(name,target)
    finally:
        if os.path.exists(name):os.unlink(name)
    return result


def text(result):
    if not isinstance(result,dict) or result.get('schema')!=SCHEMA:return 'inte räknad'
    def value(key):
        v=result.get('tal',{}).get(key,{}).get('varde')
        return 'okänt' if v is None else str(v)
    return ', '.join(label+' '+value(key) for key,label in (
        ('tokens_in','tokens in (cache separat)'),('tokens_ut','tokens ut'),('cache_lasta','cache lästa'),
        ('cache_skrivna','cache skrivna'),('modellsvar','synliga modellsvar'),('komprimeringar','komprimeringar'),
        ('vaggsekunder','väggsekunder'),('korningar','körningar')))


def las_sparad(kat: Path):
    """A stale or malformed saved measurement is not presented as current usage."""
    try:
        result=json.loads(las_fil(kat/'FORBRUKNING.json'))
        if not isinstance(result,dict) or result.get('schema')!=SCHEMA:return None
        runs=result['korningar']
        if not isinstance(runs,list) or not runs:return None
        actual={'session/'+p.name for p in (kat/'session').iterdir() if re.fullmatch(r'korning-\d+\.jsonl',p.name)}
        if actual!={r['fil'] for r in runs}:return None
        sources=[r['kalla'] for r in runs]+[s for v in result['tal'].values() for s in v['kallor']]
        for source in sources:
            name=source['fil']
            if name!='START.jsonl' and name not in actual:return None
            if hashlib.sha256(las_fil(kat/name)).hexdigest()!=source.get('sha256'):return None
        return result
    except (OSError,ValueError,TypeError,KeyError,AttributeError):return None
