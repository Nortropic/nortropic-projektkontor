"""Överlämning till kontoret: vilande beställningar i backloggen och beställningar lämnade för genomförande.

Partnern bereder. Paketet skrivs i kontorets ordinarie beställningsväg (`evidence/nasta-uppdrag/local/partner-<id>/`)
med den sammanställda arbetsordern, Johnnys exakta ord, underlaget löst till hashade filer, kraven med ett prov per
krav och ett AP-06-utkast (`tools/bered_uppdrag.py`) med sina luckor. En beställning är vilande (i backloggen) eller
lämnad. Johnnys "beställ" räcker för en vilande beställning; för genomförande lämnas den bara när han uttryckligen
säger det (FORBATTRINGSPARTNER-BACKLOG-20260929). Startvakten (start.py) startar aldrig en vilande överlämning; den
startar mottagarens session när överlämningen är lämnad.

Status går vilande → lämnad → mottagen → startad → levererad, eller avslagen. Läget vid lämningen står i
OVERLAMNING.json; varje senare övergång är en rad i paketets KVITTENS.jsonl, och den sista gällande raden gäller.
Johnnys släpp eller avslag av en vilande överlämning bokför partnern på hans ord i tråden, med orden sparade ordagrant
i en egen fil i paketet; paketet i övrigt lämnas orört. Mottagaren kvitterar de senare stegen (`partner.py kvittera`),
men aldrig en vilande överlämning: en kvittens väcker den inte. Samma beställning ger högst en överlämning per
mottagare, och varje överlämning får ett eget id; ett befintligt paket flyttas eller skrivs aldrig över.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path

from .lager import nu
from .verktyg import (AVSLAGSORD, SKAL, SLAPPORD, Verktygsfel, genomforandehinder, ovl_i_citat,
                      prova_agarcitat)

MOTTAGARE = {
    'kontorets-kedjedrivare': 'Kontorets kedjedrivare: en session i nortropic-projektkontor som startvakten startar när '
                              'överlämningen är lämnad (eller som Johnny startar). Den läser planen och tar emot paketet här.',
    'digitala': 'Digitalas kedjedrivare: en session i nortropic-digitala som startvakten startar, genom kontorets '
                'beställningsväg.',
    'runtime': 'Runtimes underhåll: en session i Nortropic Runtime som startvakten startar, genom kontorets beställningsväg.',
    'kundstart': 'Kundstart: en session i nortropic-kundstart som startvakten startar, genom kontorets beställningsväg.',
}
STATUSAR = ('vilande', 'lamnad', 'mottagen', 'startad', 'levererad', 'avslagen')
KVITTENSER = ('mottagen', 'startad', 'levererad', 'avslagen')   # mottagarens steg
OPPNA = ('vilande', 'lamnad', 'mottagen', 'startad')             # räknas av regeln om en öppen överlämning i tråden
KORTNAMN = {'kontorets-kedjedrivare': 'kontoret', 'digitala': 'digitala', 'runtime': 'runtime', 'kundstart': 'kundstart'}
OVL_ID = re.compile(r'^OVL-\d{8}-[A-Za-z0-9]{6}(-(kontoret|digitala|runtime|kundstart)\d*)?$')
REPON = ('kontoret', 'runtime', 'digitala', 'kundstart')
MAX_UNDERLAG = 20
MAX_KRAV = 30
MAX_FILER = 40
# Johnnys beslut om en vilande överlämning: ordlistan hans ord ska bära och statusen det ger.
BESLUT = {'slapp': ('lamnad', SLAPPORD, 'SLAPP', 'släpp', '"släpp OVL-…" eller "genomför OVL-…"'),
          'avslag': ('avslagen', AVSLAGSORD, 'AVSLAG', 'avslag', '"avslå OVL-…" eller "stryk OVL-…"')}
# Runtime-uppgiftens tekniska fält: mottagaren fyller i dem mot aktuell main när beställningen släpps.
VANTANDE_KODER = ('task_field_missing', 'task_field_empty')
TESTMETOD_VANTAR = 'Väljs av mottagaren i acceptansen när beställningen släpps (partnern har angett det observerbara provet).'


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _text(varde, langd: int = 4000) -> str:
    return re.sub(r'[ \t]+\n', '\n', str(varde or '')).strip()[:langd]


def _en_rad(varde, langd: int = 400) -> str:
    return ' '.join(str(varde or '').split())[:langd]


def _krav(varde) -> list:
    """Kraven i beställningen: [{id, text, prov, metod}]. Fel form vägras; ett krav utan prov gör den ofullständig."""
    if varde in (None, '', []):
        return []
    if not isinstance(varde, list):
        raise Verktygsfel('krav ska vara en lista med {id, text, prov}.')
    if len(varde) > MAX_KRAV:
        raise Verktygsfel('Högst %d krav i en beställning; dela upp den.' % MAX_KRAV)
    ut, sedda = [], set()
    for nr, k in enumerate(varde, 1):
        if not isinstance(k, dict):
            raise Verktygsfel('Varje krav ska vara ett objekt {id, text, prov}.')
        kid = _en_rad(k.get('id'), 20) or 'K%d' % nr
        if not re.fullmatch(r'[A-Za-z0-9._-]{1,20}', kid) or kid in sedda:
            raise Verktygsfel('Kravets id "%s" är ogiltigt eller upprepat.' % kid)
        sedda.add(kid)
        text = _text(k.get('text'), 2000)
        if not text:
            raise Verktygsfel('Krav %s saknar text.' % kid)
        ut.append({'id': kid, 'text': text, 'prov': _text(k.get('prov'), 2000), 'metod': _text(k.get('metod'), 1000)})
    return ut


def _filer(varde) -> list:
    if varde in (None, '', []):
        return []
    if not isinstance(varde, list) or len(varde) > MAX_FILER:
        raise Verktygsfel('berorda_filer ska vara en lista (högst %d) med {repo, sokvag}.' % MAX_FILER)
    ut = []
    for f in varde:
        repo = str((f or {}).get('repo') or '') if isinstance(f, dict) else ''
        sokvag = _en_rad((f or {}).get('sokvag'), 300).lstrip('/') if isinstance(f, dict) else ''
        if repo not in REPON or not sokvag or '..' in sokvag.split('/'):
            raise Verktygsfel('Varje berörd fil anges som {repo: kontoret|runtime|digitala|kundstart, sokvag: …}.')
        ut.append({'repo': repo, 'sokvag': sokvag})
    return ut


def _rader(fil: Path) -> list:
    ut = []
    try:
        text = fil.read_text('utf-8', errors='replace')
    except OSError:
        return ut
    for rad in text.splitlines():
        try:
            k = json.loads(rad)
        except ValueError:
            continue
        if isinstance(k, dict):
            ut.append(k)
    return ut


def paketlage(kat: Path) -> dict | None:
    """Överlämningens läge ur paketet, eller None när OVERLAMNING.json inte går att läsa.

    {'paket': OVERLAMNING.json, 'status': gällande status, 'overgangar': raderna i KVITTENS.jsonl som faktiskt ändrade
    status, i ordning}. En vilande överlämning flyttas bara av Johnnys släpp eller avslag (bokförda av partnern med
    beslut och hans ord); en mottagares kvittens väcker den aldrig. En lämnad överlämning flyttas bara av mottagarens
    kvittenser, som tidigare (sista gällande raden gäller)."""
    try:
        paket = json.loads((kat / 'OVERLAMNING.json').read_text('utf-8'))
    except (OSError, ValueError):
        return None
    if not isinstance(paket, dict):
        return None
    status = paket.get('status') if paket.get('status') in ('vilande', 'lamnad') else 'lamnad'
    overgangar = []
    for k in _rader(kat / 'KVITTENS.jsonl'):
        s = k.get('status')
        if status == 'vilande':
            if (k.get('beslut'), s) not in (('slapp', 'lamnad'), ('avslag', 'avslagen')) or not _agarord_i_paketet(kat, k):
                continue
        elif k.get('beslut') or s not in KVITTENSER:
            continue
        status = s
        overgangar.append(k)
    return {'paket': paket, 'status': status, 'overgangar': overgangar}


def _agarord_i_paketet(kat: Path, k: dict) -> bool:
    """Ett släpp eller avslag gäller bara med Johnnys ord i paketet: filen som raden pekar ut, med samma hash."""
    fil = str(k.get('agarord') or '')
    if not re.fullmatch(r'AGARENS-ORD-(SLAPP|AVSLAG)-\d{8}T\d{6}Z\.md', fil):
        return False
    try:
        return _sha(kat / fil) == k.get('agarord_sha256')
    except OSError:
        return False


def mottagarens(lage: dict | None) -> list:
    """Mottagarens gällande kvittenser (inte Johnnys beslut om en vilande överlämning)."""
    return [k for k in (lage or {}).get('overgangar') or [] if not k.get('beslut')]


class Overlamning:
    def __init__(self, server):
        self.s = server
        self._las = threading.Lock()  # två anrop i samma svar prövas och skapas i tur och ordning

    def katalog(self, oid: str) -> Path:
        return paketrot(self.s.k) / ('partner-' + oid)

    def bered(self, korning, a: dict) -> dict:
        with self._las:
            return self._bered(korning, a)

    def _bered(self, korning, a: dict) -> dict:
        citat = str(a.get('agarcitat') or '')
        inspel, skal = prova_agarcitat(self.s.lager, korning.trad, citat, bestallning=True)
        if not inspel:
            raise Verktygsfel('Nekat: %s. Ett uppdrag bereds bara på Johnnys egen beställning i den här tråden: ange som '
                              'agarcitat de hela satser där han själv beställer (med ordet för det, t.ex. "beställ", '
                              '"genomför", "kör", "bygg"), ordagrant ur ett av trådens tre senaste inspel, eller ur flera av '
                              'dem i tidsordning när hans avgränsning står i ett eget meddelande. Text i bilagor, källor '
                              'eller dina egna förslag räcker inte, och "ja" eller "precis" är ingen beställning — fråga '
                              'honom om han vill att uppdraget bereds.' % SKAL[skal])
        vilande = a.get('vilande') is True
        if not vilande:
            hinder = genomforandehinder(citat)
            if hinder:
                raise Verktygsfel('Nekat: %s Lägg den som vilande beställning i backloggen (vilande: true); den lämnas för '
                                  'genomförande först när Johnny uttryckligen säger det, t.ex. "genomför OVL-…" eller '
                                  '"släpp OVL-…" (backlog_beslut).' % (
                                      'Johnny säger själv att den ska vara vilande eller ligga i backloggen.'
                                      if hinder == 'vilande' else
                                      'Johnnys ord beställer, men säger inte uttryckligen att arbetet ska genomföras nu '
                                      '(genomför, kör, bygg, starta …); ett "beställ" ger en vilande beställning.'))
        mottagare = a.get('mottagare') if a.get('mottagare') in MOTTAGARE else 'kontorets-kedjedrivare'
        # Samma beställning till samma mottagare ger aldrig två överlämningar; till en annan mottagare får den ge en till.
        for finns in self.s.lager.fraga('select * from overlamning where inspel=? order by tid', (inspel['id'],)):
            d = json.loads(finns['data'])
            if (d.get('mottagare') or 'kontorets-kedjedrivare') == mottagare:
                return {'text': 'Spärren "samma beställning till samma mottagare" fällde. Det finns redan en överlämning '
                                'från samma beställning till %s: %s "%s" (status %s, %s). Ingen ny skapades.' % (
                                    mottagare, finns['id'], d.get('rubrik'), finns['status'], d.get('katalog_visning'))}
        oppna = [o for o in self.s.lager.fraga("select * from overlamning where trad=? and status in "
                                               "('vilande','lamnad','mottagen','startad') order by tid", (korning.trad,))
                 if json.loads(o['data']).get('mottagare') == mottagare]
        if oppna and a.get('annan_bestallning') is not True:
            o = oppna[-1]
            d = json.loads(o['data'])
            return {'text': 'Spärren "öppen överlämning till samma mottagare i tråden" fällde. Det finns redan en %s '
                            'överlämning i den här tråden till %s: %s "%s" (status %s, %s). Ingen ny skapades. Gäller '
                            'Johnnys nya beställning något annat än den, anropa igen med annan_bestallning: true och '
                            'skriv i målet vad som skiljer den från %s.' % (
                                'vilande' if o['status'] == 'vilande' else 'öppen', mottagare, o['id'], d.get('rubrik'),
                                o['status'], d.get('katalog_visning'), o['id'])}
        # Innehållet prövas innan något skrivs: fel form vägras, och underlag som inte kan öppnas tappas aldrig tyst.
        krav = _krav(a.get('krav'))
        filer = _filer(a.get('berorda_filer'))
        underlag_id = [str(x).strip() for x in (a.get('underlag') or []) if str(x).strip()]
        if len(underlag_id) > MAX_UNDERLAG:
            raise Verktygsfel('Högst %d underlag i en beställning (angivna: %d); välj de som bär beställningen.' % (
                MAX_UNDERLAG, len(underlag_id)))
        losta, olosta = [], []
        for kid in underlag_id:
            text, fel = self._underlag(kid)
            (losta if text else olosta).append((kid, text) if text else {'id': kid, 'skal': fel or 'tomt innehåll'})
        if olosta and a.get('godta_olost_underlag') is not True:
            raise Verktygsfel('Nekat: underlag som inte går att öppna tappas inte tyst, och ingen beställning skapades. '
                              'Går inte att öppna: %s. Underlag anges som id som går att öppna: F-…, partner:…, t_…, en '
                              'sökträffs id, repo:<repo>[@ref]:<sökväg> eller github:<API-sökväg>. Beskriv fri text i '
                              'målet, fyndet eller kraven i stället, eller anropa igen med godta_olost_underlag: true, så '
                              'står posterna kvar ordagrant och beställningen märks ofullständig.' % '; '.join(
                                  '"%s" (%s)' % (u['id'], u['skal']) for u in olosta))
        rubrik = _en_rad(a.get('rubrik'), 160)
        mal = _text(a.get('mal'))
        granser = [_en_rad(x, 1000) for x in (a.get('granser') or []) if _en_rad(x)][:20]
        nasta = _text(a.get('nasta_handling'), 2000)
        klart_nar = _text(a.get('klart_nar'), 2000)
        ordning = _text(a.get('ordning_och_beroenden'), 2000)
        resursram = _text(a.get('resursram'), 1000)
        fynd = _text(a.get('fynd'), 1000)
        motivering = _text(a.get('motivering'), 1000)
        oid, kat = self._nytt_id(inspel['id'], mottagare)
        kat.mkdir(parents=True, exist_ok=False, mode=0o700)
        (kat / 'underlag').mkdir(mode=0o700)
        citerade = [self.s.lager.en('select * from inspel where id=?', (x,)) for x in inspel.get('citerade') or [inspel['id']]]
        agarord = ('# Johnnys ord (ordagrant ur partnerns samtalsyta)\n\nBeställningen som citerats: "%s"\n' % citat
                   + ''.join('\n---\n\nInspel `%s` i tråden `%s`, sparat %s (UTC)%s:\n\n%s\n' % (
                       c['id'], c['trad'], c['tid'], ', bär beställningen' if c['id'] == inspel['id'] else '', c['text'])
                       for c in citerade if c))
        self._skriv(kat / 'AGARENS-ORD.md', agarord)
        underlag = []
        for i, (kid, text) in enumerate(losta, 1):
            namn = 'underlag/%02d-%s.md' % (i, re.sub(r'[^A-Za-z0-9._-]', '_', kid)[:80])
            self._skriv(kat / namn, text)
            underlag.append({'id': kid, 'fil': namn, 'sha256': _sha(kat / namn)})
        tid = nu()
        trad = self.s.lager.trad(korning.trad) or {}
        ap06 = self._ap06(kat, oid, rubrik, mal, citat, granser, nasta, underlag, krav, klart_nar, filer, ordning,
                          resursram, motivering)
        markning = _markning(krav, klart_nar, olosta, ap06)
        order = ['# %s' % rubrik, '',
                 '*Överlämning %s från Projektkontorets förbättringspartner, %s %s. Sammanställt av partnern ur '
                 'samtalet; bara citatet och AGARENS-ORD.md är Johnnys ordagranna ord.*' % (
                     oid, 'lagd som vilande beställning i backloggen' if vilande else 'lämnad', tid), '',
                 '## Beslutet (Johnnys ord)', '', '> %s' % citat, '',
                 'Inspel `%s`, tråd `%s`, sparat %s. Hela %s: AGARENS-ORD.md.' % (
                     inspel['id'], inspel['trad'], inspel['tid'],
                     'inspelet' if len([c for c in citerade if c]) == 1 else 'inspelen'), '',
                 '## Märkning', '', _markningstext(markning), '',
                 '## Mål', '', mal, '',
                 '## Krav och prov', '']
        order += ['- **%s** %s\n  Prov: %s%s' % (k['id'], k['text'], k['prov'] or '(inget prov angivet)',
                                                ('\n  Metod: ' + k['metod']) if k['metod'] else '') for k in krav] \
            or ['- (inga krav angivna)']
        order += ['', '## Klart när', '', klart_nar or '(inte angivet)', '',
                  '## Berörda filer', '']
        order += ['- %s: `%s`' % (f['repo'], f['sokvag']) for f in filer] or ['- (inga angivna)']
        order += ['', '## Ordning och beroenden', '', ordning or '(inte angivet)', '',
                  '## Resursram', '', resursram or '(inte angiven)', '',
                  '## Ursprung', '', 'Tråd `%s`%s. Fynd: %s' % (
                      korning.trad, (' ("%s")' % trad.get('titel')) if trad.get('titel') else '', fynd or '(inte angivet)'), '',
                  '## Motivering', '', motivering or '(inte angiven)', '',
                  '## Underlag', '']
        order += ['- `%s` → %s' % (u['id'], u['fil']) for u in underlag] or ['- (inget underlag angivet)']
        if olosta:
            order += ['', 'Underlag som inte kunde lösas upp (står kvar ordagrant; beställningen är ofullständig):']
            order += ['- "%s": %s' % (u['id'], u['skal']) for u in olosta]
        order += ['', '## Gränser', '']
        order += ['- ' + g for g in granser] or ['- Inga särskilda gränser angivna utöver kontorets gällande regler.']
        order += ['', '## Föreslagen nästa handling', '', nasta, '',
                  '## Runtime-uppgiftens tekniska fält', '',
                  'Väntande: %s. Mottagaren fyller i dem mot aktuell main när beställningen släpps; de är inte fel.' % (
                      ', '.join(markning['vantande']) or '(inga)'), '',
                  '## Mottagare', '', MOTTAGARE[mottagare], '', '## Status', '']
        if vilande:
            order.append('Vilande i backloggen: startvakten startar den inte, och mottagaren kvitterar den inte. Johnny '
                         'släpper den i partnertråden ("släpp %s" eller "genomför %s") eller avslår den där; partnern '
                         'bokför övergången som en rad i KVITTENS.jsonl och sparar hans ord ordagrant i en egen fil '
                         '(AGARENS-ORD-SLAPP-… eller AGARENS-ORD-AVSLAG-…). Efter ett släpp gäller det som för en lämnad '
                         'överlämning: aktuell status är sista gällande raden i KVITTENS.jsonl, och mottagaren kvitterar '
                         'med `python3 -B tools/partner.py kvittera %s mottagen --av "<session>"`, därefter `startad` och '
                         '`levererad --bevis "<PR/commit/fil>"` (eller `avslagen`). Överlämningen ger inget eget mandat '
                         'utöver Johnnys beslut och kontorets gällande regler.%s' % (
                             oid, oid, oid, ('; en annan beställning än den öppna ' + ', '.join(o['id'] for o in oppna))
                             if oppna else ''))
        else:
            order.append('Lämnad av partnern%s. Aktuell status är sista raden i KVITTENS.jsonl. Mottagaren kvitterar med '
                         '`python3 -B tools/partner.py kvittera %s mottagen --av "<session>"`, därefter `startad` och '
                         '`levererad --bevis "<PR/commit/fil>"` (eller `avslagen`). Partnern visar statusen i tråden. '
                         'Överlämningen ger inget eget mandat utöver Johnnys beslut ovan och kontorets gällande regler.' % (
                             ('; en annan beställning än den öppna ' + ', '.join(o['id'] for o in oppna)) if oppna else '',
                             oid))
        order.append('')
        self._skriv(kat / 'ARBETSORDER.md', '\n'.join(order))
        status = 'vilande' if vilande else 'lamnad'
        tillstand = {'id': oid, 'status': status, 'lamnad': tid, 'mottagare': mottagare,
                     'mottagare_text': MOTTAGARE[mottagare], 'trad': korning.trad, 'trad_titel': trad.get('titel'),
                     'inspel': inspel['id'], 'citerade_inspel': [c['id'] for c in citerade if c],
                     'rubrik': rubrik, 'fynd': fynd, 'motivering': motivering, 'krav': krav, 'klart_nar': klart_nar,
                     'berorda_filer': filer, 'ordning_och_beroenden': ordning, 'resursram': resursram,
                     'underlag': underlag, 'underlag_olosta': olosta, 'markning': markning, 'ap06': ap06,
                     'skild_fran': [o['id'] for o in oppna],
                     'status_not': 'Status när paketet skrevs (vilande eller lamnad). Senare övergångar står i '
                                   'KVITTENS.jsonl (sista gällande raden gäller): Johnnys släpp eller avslag av en vilande '
                                   'överlämning, bokförda av partnern med hans ord i paketet, och mottagarens kvittenser.'}
        self._skriv(kat / 'OVERLAMNING.json', json.dumps(tillstand, ensure_ascii=False, indent=1))
        (kat / 'KVITTENS.jsonl').touch(mode=0o600)
        visning = (('provinstansens data: overlamningar/partner-%s/' if getattr(self.s.k, 'prov_dolj', ())
                    else 'kontoret/evidence/nasta-uppdrag/local/partner-%s/') % oid)
        self.s.lager.lagg_till('overlamning', overlamning=oid, status=status, trad=korning.trad, inspel=inspel['id'],
                               nyckel='%s:%s' % (inspel['id'], mottagare), rubrik=rubrik, mal=mal, mottagare=mottagare,
                               katalog=str(kat), katalog_visning=visning, ap06=ap06, granser=granser,
                               nasta_handling=nasta, agarcitat=citat, skild_fran=[o['id'] for o in oppna],
                               markning=markning, fynd=fynd, motivering=motivering)
        korning.handelse('overlamning', 'Överlämning %s %s till %s' % (oid, 'lagd som vilande' if vilande else 'lämnad',
                                                                       mottagare))
        lage = ('VILANDE i backloggen (inte lämnad och inte startad; startvakten startar den inte förrän Johnny släpper '
                'den med sina egna ord, t.ex. "släpp %s")' % oid) if vilande else 'LÄMNAD (inte mottagen eller startad)'
        rader = ['Överlämningen %s är %s till: %s' % (oid, lage, MOTTAGARE[mottagare]),
                 'Paket: %s (ARBETSORDER.md, AGARENS-ORD.md, %d underlagsfiler, %d krav, AP-06-utkast: %s).' % (
                     visning, len(underlag), len(krav), ap06.get('status')),
                 'Märkning: ' + _markningstext(markning)]
        if olosta:
            rader.append('VARNING: underlag som inte kunde öppnas står kvar ordagrant i ARBETSORDER.md: %s.' % '; '.join(
                '"%s" (%s)' % (u['id'], u['skal']) for u in olosta))
        return {'text': '\n'.join(rader)}

    def _nytt_id(self, inspel_id: str, mottagare: str) -> tuple:
        """Ett id som ingen överlämning eller katalog har: OVL-<datum>-<inspel>, för fler mottagare ur samma inspel med
        mottagarens kortnamn, och vid en kvarlämnad katalog med löpnummer. Ett befintligt paket flyttas eller skrivs
        aldrig över."""
        bas = 'OVL-%s-%s' % (datetime.now(timezone.utc).strftime('%Y%m%d'), inspel_id[-6:])
        kort = KORTNAMN.get(mottagare, 'kontoret')
        for n in range(1, 50):
            oid = bas if n == 1 else ('%s-%s' % (bas, kort) if n == 2 else '%s-%s%d' % (bas, kort, n - 1))
            kat = self.katalog(oid)
            if not kat.exists() and not os.path.lexists(kat) and \
                    not self.s.lager.en('select id from overlamning where id=?', (oid,)):
                return oid, kat
        raise Verktygsfel('Hittar inget ledigt överlämnings-id; inget skapades.')

    def _skriv(self, p: Path, text: str) -> None:
        fd = os.open(p, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(text)

    def _underlag(self, kid: str) -> tuple:
        """(text, fel): underlaget i sin helhet, eller varför det inte gick att öppna."""
        try:
            if kid.startswith('partner:') or re.match(r'^F-\d+$', kid) or kid.startswith('t_'):
                return self.s.verktyg.v_oppna(_Tyst(), {'id': kid})['text'], ''
            m = re.match(r'^repo:(kontoret|runtime|digitala|kundstart)(?:@([^:]+))?:(.+)$', kid)
            if m:
                return self.s.verktyg.repo_fil(m.group(1), m.group(2), m.group(3)), ''
            if kid.startswith('github:'):
                return self.s.verktyg.github_underlag(kid[len('github:'):]), ''
            ut = self.s.kallor.oppna(kid, 0)
            if not ut:
                return '', 'inget sådant id i partnerns källor (fri text är inget underlag)'
            return ('%s\n%s\nReferens: %s\n\n%s' % (ut['klass_text'], ut['titel'], ut['ref'],
                                                   '\n\n'.join(g['text'] for g in ut['sammanhang']))), ''
        except Verktygsfel as fel:
            return '', str(fel)
        except Exception as fel:
            return '', 'kunde inte öppnas (%s)' % type(fel).__name__

    def _ap06(self, kat: Path, oid: str, rubrik, mal, citat, granser, nasta, underlag, krav, klart_nar, filer, ordning,
              resursram, motivering) -> dict:
        """AP-06-utkast genom kontorets befintliga beredning: kraven och deras prov blir requirements och tests. Luckor
        redovisas, inget hittas på; Runtime-uppgiftens tekniska fält är väntande."""
        tools = Path(__file__).resolve().parents[1]
        rot = kat
        kallor = [{'id': 'S1', 'title': 'Johnnys beställning i partnerns samtalsyta', 'version': oid,
                   'path': 'AGARENS-ORD.md', 'sha256': _sha(kat / 'AGARENS-ORD.md'),
                   'size': (kat / 'AGARENS-ORD.md').stat().st_size}]
        for i, u in enumerate(underlag, 2):
            p = kat / u['fil']
            kallor.append({'id': 'S%d' % i, 'title': u['id'], 'version': oid, 'path': u['fil'], 'sha256': _sha(p),
                           'size': p.stat().st_size})
        case = {'schema': 1, 'id': oid.lower(), 'created_at': nu()[:19] + 'Z', 'sources': kallor,
                'claims': [{'id': 'C1', 'kind': 'decision', 'text': citat, 'reason': 'Johnnys beställning',
                            'standing': 'Johnnys ord i samtalsytan', 'sources': ['S1']}],
                'actions': [{'id': 'A1', 'text': rubrik, 'reason': mal, 'claims': ['C1'],
                             'authority': {'status': 'granted', 'scope': mal[:400] or rubrik, 'sources': ['S1']}}],
                'next_action': 'A1'}
        sys.path.insert(0, str(tools))
        try:
            import change_assessment
            manifest = change_assessment.reference_manifest(case)
        finally:
            sys.path.remove(str(tools))
        check = {'checked_at': nu()[:19] + 'Z', 'manifest': manifest,
                 'result': {'ok': True, 'files': [{'path': k['path'], 'status': 'ok'} for k in kallor]}}
        ref = {'id': 'REF1', 'source': 'S1', 'version': oid, 'quote': citat}
        skal = motivering or 'Johnnys beställning'
        tests = [{'id': 'T-' + k['id'], 'observable': k['prov'], 'method': k['metod'] or (TESTMETOD_VANTAR if k['prov'] else '')}
                 for k in krav]
        requirements = [{'id': k['id'], 'text': k['text'], 'reason': skal, 'claims': ['C1'], 'references': ['REF1'],
                         'tests': ['T-' + k['id']]} for k in krav]
        scope = [x for x in [nasta, ('Klart när: ' + klart_nar) if klart_nar else '']
                 + ['Berörd fil: %s:%s' % (f['repo'], f['sokvag']) for f in filer] if x]
        limitations = list(granser) + (['Resursram: ' + resursram] if resursram else [])
        context = [{'kind': 'decision', 'text': citat}, {'kind': 'judgment', 'text': mal or rubrik}]
        if ordning:
            context.append({'kind': 'judgment', 'text': 'Ordning och beroenden: ' + ordning})
        spec = {'schema': 1, 'action': 'A1', 'references': [ref],
                'reference_checks': [dict(ref, sha256=kallor[0]['sha256'], status='matched')],
                'requirements': requirements, 'tests': tests,
                'export': {'title': rubrik or oid, 'context': context, 'scope': scope,
                           'limitations': limitations or ['Kontorets gällande regler; inga särskilda gränser angivna.']},
                'task': {}}
        ap = kat / 'ap06'
        ap.mkdir(mode=0o700)
        for namn, varde in (('case', case), ('check', check), ('spec', spec)):
            self._skriv(ap / (namn + '.json'), json.dumps(varde, ensure_ascii=False, indent=1))
        r = subprocess.run([sys.executable, '-B', str(tools / 'bered_uppdrag.py'), str(ap / 'case.json'),
                            str(ap / 'check.json'), str(ap / 'spec.json'), '--source-root', str(rot),
                            '--output', str(ap / 'utkast')], capture_output=True, text=True, timeout=60)
        try:
            svar = json.loads(r.stdout.strip().splitlines()[-1]) if r.stdout.strip() else {}
        except ValueError:
            svar = {}
        if r.returncode != 0:
            return {'status': 'kunde inte beredas (AP-06 avvisade indata)', 'kod': r.returncode, 'luckor': [],
                    'vantande': [], 'avvisad': True}
        luckor, vantande = [], []
        for g in svar.get('gaps') or []:
            kod = g.get('code') if isinstance(g, dict) else str(g)
            if kod in VANTANDE_KODER:
                vantande.append(g.get('subject') if isinstance(g, dict) else kod)
            else:
                luckor.append('%s (%s)' % (kod, g.get('subject')) if isinstance(g, dict) else kod)
        return {'status': 'utkast' + (' med luckor' if luckor else '') + (' och väntande tekniska fält' if vantande else ''),
                'luckor': luckor, 'vantande': vantande, 'mekaniskt_komplett': svar.get('mechanical_complete'),
                'katalog': 'ap06/utkast'}

    # --------------------------------------------------------------- Johnnys släpp och avslag
    def besluta(self, korning, a: dict) -> dict:
        with self._las:
            return self._besluta(korning, a)

    def _besluta(self, korning, a: dict) -> dict:
        oid = str(a.get('id') or '').strip()
        beslut = a.get('beslut')
        if beslut not in BESLUT or not OVL_ID.match(oid):
            raise Verktygsfel('Ange id (OVL-…) och beslut: slapp eller avslag.')
        ny_status, ordlista, filord, namn, exempel = BESLUT[beslut]
        rad = self.s.lager.en('select * from overlamning where id=?', (oid,))
        if not rad:
            raise Verktygsfel('Överlämningen %s finns inte bland partnerns överlämningar.' % oid)
        d = json.loads(rad['data'])
        kat = Path(d.get('katalog') or '')
        lage = paketlage(kat)
        if lage is None:
            raise Verktygsfel('Paketet för %s går inte att läsa; inget ändrades.' % oid)
        citat = str(a.get('agarcitat') or '')
        inspel, skal = prova_agarcitat(self.s.lager, korning.trad, citat, bestallning=True, ordlista=ordlista)
        if not inspel:
            raise Verktygsfel('Nekat: %s. Ett %s kräver Johnnys egna ord i den här tråden, ordagrant ur ett av trådens tre '
                              'senaste inspel, med ordet för beslutet (t.ex. %s), varken negerat eller som fråga. Fråga '
                              'honom kort om det behövs.' % (
                                  'citatet saknar ordet för beslutet' if skal == 'inget_bestallningsord' else SKAL[skal],
                                  namn, exempel))
        if oid.casefold() not in ovl_i_citat(citat):
            raise Verktygsfel('Nekat: Johnnys ord nämner inte %s. Ett %s gäller en namngiven överlämning; fråga honom '
                              'kort vilken, t.ex. %s.' % (oid, namn, exempel.replace('OVL-…', oid)))
        # Samma beslut på samma ord en gång till (t.ex. efter ett avbrott mellan paket och journal) fullbordas bara.
        tidigare = [k for k in lage['overgangar'] if k.get('beslut') == beslut and k.get('inspel') == inspel['id']]
        if rad['status'] != 'vilande' or lage['status'] != 'vilande':
            if not (tidigare and rad['status'] == 'vilande' and lage['status'] == ny_status):
                raise Verktygsfel('%s är inte vilande (status %s); bara en vilande beställning släpps eller avslås här. '
                                  'En lämnad överlämning avslutas av mottagaren med en kvittens.' % (oid, lage['status']))
        if tidigare:
            post = tidigare[-1]
        else:
            stampel = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
            fil = 'AGARENS-ORD-%s-%s.md' % (filord, stampel)
            citerade = [self.s.lager.en('select * from inspel where id=?', (x,)) for x in inspel.get('citerade') or [inspel['id']]]
            try:
                self._skriv(kat / fil, '# Johnnys ord om %s (ordagrant ur partnerns samtalsyta): %s\n\nCiterat: "%s"\n' % (
                    oid, 'släpp' if beslut == 'slapp' else 'avslag', citat) + ''.join(
                    '\n---\n\nInspel `%s` i tråden `%s`, sparat %s (UTC)%s:\n\n%s\n' % (
                        c['id'], c['trad'], c['tid'], ', bär beslutet' if c['id'] == inspel['id'] else '', c['text'])
                    for c in citerade if c))
            except FileExistsError:  # ett annat beslut om samma paket skrevs samma sekund; inget har skrivits här
                raise Verktygsfel('Ett annat beslut om %s skrevs just nu; inget ändrades. Försök igen om en sekund.' % oid)
            post = {'status': ny_status, 'beslut': beslut,
                    'av': 'förbättringspartnern på Johnnys ord i tråden %s' % korning.trad,
                    'bevis': 'Johnnys ord (inspel %s): "%s" — ordagrant i %s' % (inspel['id'], citat[:300], fil),
                    'inspel': inspel['id'], 'citerade_inspel': [c['id'] for c in citerade if c], 'trad': korning.trad,
                    'agarord': fil, 'agarord_sha256': _sha(kat / fil), 'kvitterad': nu()}
            with open(kat / 'KVITTENS.jsonl', 'a', encoding='utf-8') as f:
                f.write(json.dumps(post, ensure_ascii=False) + '\n')
        self.s.lager.lagg_till('overlamning_status', overlamning=oid, trad=rad['trad'], status=ny_status, beslut=beslut,
                               av=post['av'], bevis=post['bevis'][:500], kvitterad=post['kvitterad'],
                               inspel=post['inspel'], beslutstrad=korning.trad, agarord=post['agarord'])
        korning.handelse('overlamning', 'Överlämning %s %s på Johnnys ord' % (oid, 'släppt' if beslut == 'slapp' else 'avslagen'))
        if beslut == 'slapp':
            text = ('Överlämningen %s är SLÄPPT på Johnnys ord och nu LÄMNAD till %s (inte mottagen eller startad). '
                    'Startvakten startar mottagarens session när skrivplatsen är ledig; mottagaren fyller i Runtime-'
                    'uppgiftens tekniska fält mot aktuell main. Hans ord står ordagrant i %s i paketet.' % (
                        oid, d.get('mottagare'), post['agarord']))
        else:
            text = ('Överlämningen %s är AVSLAGEN på Johnnys ord, direkt ur backloggen; den startas aldrig och står kvar som '
                    'historik. Hans ord står ordagrant i %s i paketet.' % (oid, post['agarord']))
        return {'text': text}

    # --------------------------------------------------------------- kvittenser
    def las_kvittenser(self) -> int:
        """Läs mottagarens kvittenser (KVITTENS.jsonl) och journalför nya statusar. En vilande överlämning läses inte
        här: den flyttas bara av Johnnys släpp eller avslag, som partnern journalför själv när det sker."""
        nya = 0
        for o in self.s.lager.fraga("select * from overlamning where status not in ('levererad','avslagen','vilande')"):
            d = json.loads(o['data'])
            kat = Path(d.get('katalog') or '')
            if not (kat / 'KVITTENS.jsonl').exists():
                continue
            kanda = {(h.get('status'), h.get('kvitterad')) for h in d.get('historik') or []}
            for k in mottagarens(paketlage(kat)):
                if (k.get('status'), k.get('kvitterad')) in kanda:
                    continue
                self.s.lager.lagg_till('overlamning_status', overlamning=o['id'], trad=o['trad'], status=k['status'],
                                       av=str(k.get('av') or '')[:200], bevis=str(k.get('bevis') or '')[:500],
                                       kvitterad=k.get('kvitterad'))
                kanda.add((k.get('status'), k.get('kvitterad')))
                nya += 1
        return nya


def _markning(krav: list, klart_nar: str, olosta: list, ap06: dict) -> dict:
    """Byggklar när varje krav har ett prov, klart-när finns och allt underlag är löst till filer (och AP-06 inte har
    någon annan lucka); annars ofullständig med luckorna uppräknade. Runtime-uppgiftens tekniska fält är väntande."""
    luckor = []
    if not krav:
        luckor.append('inga krav')
    luckor += ['krav %s saknar prov' % k['id'] for k in krav if not k['prov']]
    if not klart_nar:
        luckor.append('klart-när saknas')
    luckor += ['underlaget "%s" är inte löst till en fil' % u['id'] for u in olosta]
    if ap06.get('avvisad'):
        luckor.append('AP-06-beredningen avvisade indata')
    luckor += ['AP-06: ' + x for x in ap06.get('luckor') or []
               if not x.startswith(('requirements_empty', 'tests_empty', 'test_observable_empty', 'test_method_empty',
                                    'requirement_verification_incomplete'))]
    return {'varde': 'ofullständig' if luckor else 'byggklar', 'luckor': luckor, 'vantande': list(ap06.get('vantande') or [])}


def _markningstext(m: dict) -> str:
    text = m['varde'] + (' — luckor: ' + '; '.join(m['luckor']) if m['luckor'] else '')
    if m.get('vantande'):
        text += '. Väntande tekniska fält (mottagaren fyller i dem när beställningen släpps): ' + ', '.join(m['vantande'])
    return text


class _Tyst:
    typ = 'tur'
    trad = ''
    id = ''

    def logga_kallor(self, *a):
        pass

    def handelse(self, *a):
        pass


def paketrot(k) -> Path:
    """Kontorets beställningsväg. En provinstans (PARTNER_PROV_DOLJ) skriver i sin egen data: den vanliga tjänsten
    indexerar AGARENS-ORD.md i beställningsvägen som Johnnys ord, och provtext i hans namn får aldrig hamna där."""
    if getattr(k, 'prov_dolj', ()):
        return Path(k.data) / 'overlamningar'
    return Path(k.kontor_primar) / 'evidence/nasta-uppdrag/local'


def kvittera(k, oid: str, status: str, av: str, bevis: str = '') -> Path:
    """Mottagarens kvittens. k är tjänstens konfiguration (eller, som tidigare, kontorets primärutcheckning). En vilande
    överlämning kvitteras aldrig: den släpps eller avslås bara på Johnnys ord i partnertråden."""
    if status not in KVITTENSER:
        raise ValueError('status måste vara en av ' + ', '.join(KVITTENSER))
    if not OVL_ID.match(oid):
        raise ValueError('okänt överlämnings-id')
    rot = paketrot(k) if hasattr(k, 'kontor_primar') else Path(k) / 'evidence/nasta-uppdrag/local'
    kat = rot / ('partner-' + oid)
    fil = kat / 'KVITTENS.jsonl'
    if not fil.exists():
        raise FileNotFoundError(str(fil))
    lage = paketlage(kat)
    if lage is None:
        raise ValueError('paketet för %s går inte att läsa (OVERLAMNING.json); ingen kvittens skrevs' % oid)
    if lage['status'] == 'vilande':
        raise ValueError('%s är vilande i backloggen: en mottagare kvitterar den inte. Den släpps eller avslås bara på '
                         'Johnnys ord i partnertråden.' % oid)
    with open(fil, 'a', encoding='utf-8') as f:
        f.write(json.dumps({'status': status, 'av': av, 'bevis': bevis, 'kvitterad': nu()}, ensure_ascii=False) + '\n')
    return fil


# ------------------------------------------------------------------- backloggen
def backlog(k, alla: bool = False) -> dict:
    """De vilande beställningarna, lästa ur paketen i beställningsvägen (bara läsning, ingen modell).

    {'status': 'ok' | 'ofullstandig' | 'okand', 'poster': [...], 'olasbara': [...], 'rot', 'last', 'skal'?}. Går
    beställningsvägen inte att läsa är backloggen okänd, aldrig tom; ett paket som inte går att läsa räknas upp, och då
    är backloggen inte känd i sin helhet."""
    rot = paketrot(k)
    ut = {'status': 'ok', 'poster': [], 'olasbara': [], 'rot': str(rot), 'last': nu(), 'alla': bool(alla)}
    try:
        namn = sorted(os.listdir(rot))
    except OSError as fel:
        ut.update(status='okand', skal='beställningsvägen %s gick inte att läsa (%s)' % (rot, type(fel).__name__))
        return ut
    for n in namn:
        oid = n[len('partner-'):]
        if not n.startswith('partner-') or not OVL_ID.match(oid):
            continue
        kat = rot / n
        if os.path.islink(kat) or not kat.is_dir():
            continue
        lage = paketlage(kat)
        if lage is None or lage['paket'].get('id') != oid:
            ut['olasbara'].append({'id': oid, 'skal': 'OVERLAMNING.json går inte att läsa'})
            continue
        p = lage['paket']
        if p.get('status') != 'vilande' or (lage['status'] != 'vilande' and not alla):
            continue
        m = p.get('markning') if isinstance(p.get('markning'), dict) else {}
        ut['poster'].append({'id': oid, 'status': lage['status'], 'mottagare': p.get('mottagare'),
                             'rubrik': p.get('rubrik'), 'datum': p.get('lamnad'), 'trad': p.get('trad'),
                             'trad_titel': p.get('trad_titel'), 'fynd': p.get('fynd'), 'motivering': p.get('motivering'),
                             'markning': m.get('varde') or 'okänd', 'luckor': m.get('luckor') or [],
                             'vantande': m.get('vantande') or [],
                             'beslut': (lage['overgangar'][0] if lage['overgangar'] else None)})
    if ut['olasbara']:
        ut['status'] = 'ofullstandig'
    ut['poster'].sort(key=lambda x: str(x.get('datum') or ''))
    return ut


def backlogtext(b: dict) -> str:
    if b['status'] == 'okand':
        return 'Backloggen är OKÄND, inte tom: %s.' % b.get('skal')
    vilande = [p for p in b['poster'] if p['status'] == 'vilande']
    rader = ['Backloggen (vilande beställningar, läst %sZ ur %s): %d vilande%s.' % (
        b['last'][:16], b['rot'], len(vilande),
        (', %d släppta eller avslagna visas också' % (len(b['poster']) - len(vilande))) if b.get('alla') else '')]
    if b['olasbara']:
        rader.append('OBS: backloggen är inte känd i sin helhet: %d paket gick inte att läsa (%s).' % (
            len(b['olasbara']), ', '.join('%s: %s' % (o['id'], o['skal']) for o in b['olasbara'])))
    for p in b['poster']:
        rader.append('- %s · %s · till %s · "%s" · %s · %s%s' % (
            p['id'], p['status'], KORTNAMN.get(p.get('mottagare'), p.get('mottagare')), p.get('rubrik'),
            str(p.get('datum') or '')[:10], p['markning'], (' (luckor: %s)' % '; '.join(p['luckor'])) if p['luckor'] else ''))
        rader.append('  Ursprung: tråd %s%s; fynd: %s' % (p.get('trad'), (' "%s"' % p['trad_titel']) if p.get('trad_titel') else '',
                                                          p.get('fynd') or '(inte angivet)'))
        rader.append('  Motivering: %s' % (p.get('motivering') or '(inte angiven)'))
        if p.get('beslut'):
            rader.append('  %s %s: %s' % ('Släppt' if p['beslut'].get('beslut') == 'slapp' else 'Avslagen',
                                          str(p['beslut'].get('kvitterad') or '')[:16], p['beslut'].get('bevis')))
    if not b['poster'] and b['status'] == 'ok':
        rader.append('Inga vilande beställningar.')
    rader.append('Johnny släpper en vilande beställning i partnertråden ("släpp OVL-…" eller "genomför OVL-…") eller '
                 'avslår den där; utan hans egna ord ändras inget.')
    return '\n'.join(rader)
