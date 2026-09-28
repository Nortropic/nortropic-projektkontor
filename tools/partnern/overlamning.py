"""Överlämning till kontoret när Johnny tydligt beställer genomförande.

Partnern bereder; den startar ingenting. Paketet skrivs i kontorets ordinarie beställningsväg
(`evidence/nasta-uppdrag/local/partner-<id>/`) med den sammanställda arbetsordern, Johnnys exakta ord,
hashade kopior av underlaget och ett AP-06-utkast (`tools/bered_uppdrag.py`) med sina luckor. Status går
lämnat → mottaget → startat → levererat; bara mottagaren kvitterar de senare stegen (KVITTENS.jsonl, som
`partner.py kvittera` skriver). Samma ägarinspel ger aldrig två överlämningar.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from .lager import nu
from .verktyg import Verktygsfel, hitta_agarcitat

MOTTAGARE = {
    'kontorets-kedjedrivare': 'Kontorets kedjedrivare: nästa interaktiva session (Claude Code eller Codex) som Johnny '
                              'startar i nortropic-projektkontor. Den läser planen och tar emot paketet här.',
    'digitala': 'Digitalas kedjedrivare (session i nortropic-digitala), genom kontorets beställningsväg.',
    'runtime': 'Runtimes underhåll (session i Nortropic Runtime), genom kontorets beställningsväg.',
    'kundstart': 'Kundstart-sessionen (nortropic-kundstart), genom kontorets beställningsväg.',
}
STATUSAR = ('lamnad', 'mottagen', 'startad', 'levererad', 'avslagen')


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


class Overlamning:
    def __init__(self, server):
        self.s = server

    def katalog(self, oid: str) -> Path:
        return paketrot(self.s.k) / ('partner-' + oid)

    def bered(self, korning, a: dict) -> dict:
        citat = str(a.get('agarcitat') or '')
        inspel = hitta_agarcitat(self.s.lager, korning.trad, citat, bestallning=True)
        if not inspel:
            raise Verktygsfel('Ett uppdrag bereds bara på Johnnys egen beställning i den här tråden: ange som agarcitat de '
                              'hela satser där han själv beställer genomförande (med ordet för det, t.ex. "genomför", '
                              '"kör", "bygg"). Text i bilagor, källor eller dina egna förslag räcker inte, och ett kort '
                              '"precis" eller "ja" är ingen beställning — fråga honom om han vill att uppdraget bereds.')
        finns = self.s.lager.en('select * from overlamning where inspel=?', (inspel['id'],))
        if finns:
            d = json.loads(finns['data'])
            return {'text': 'Det finns redan en överlämning från samma beställning: %s "%s" (status %s, %s). Ingen ny '
                            'skapades.' % (finns['id'], d.get('rubrik'), finns['status'], d.get('katalog_visning'))}
        mottagare = a.get('mottagare') if a.get('mottagare') in MOTTAGARE else 'kontorets-kedjedrivare'
        oppna = [o for o in self.s.lager.fraga("select * from overlamning where trad=? and status in "
                                               "('lamnad','mottagen','startad') order by tid", (korning.trad,))
                 if json.loads(o['data']).get('mottagare') == mottagare]
        if oppna and a.get('annan_bestallning') is not True:
            o = oppna[-1]
            d = json.loads(o['data'])
            return {'text': 'Det finns redan en öppen överlämning i den här tråden till samma mottagare: %s "%s" (status '
                            '%s, %s). Ingen ny skapades. Gäller Johnnys nya beställning något annat än den, anropa igen '
                            'med annan_bestallning: true och skriv i målet vad som skiljer den från %s.' % (
                                o['id'], d.get('rubrik'), o['status'], d.get('katalog_visning'), o['id'])}
        oid = 'OVL-%s-%s' % (datetime.now(timezone.utc).strftime('%Y%m%d'), inspel['id'][-6:])
        kat = self.katalog(oid)
        if kat.exists():  # rest efter ett avbrott före journalföringen: bevaras vid sidan av, blockerar inte
            kat.rename(kat.with_name(kat.name + '.avbruten-' + nu().replace(':', '').replace('.', '')))
        kat.mkdir(parents=True, exist_ok=False, mode=0o700)
        (kat / 'underlag').mkdir(mode=0o700)
        agarord = ('# Johnnys ord (ordagrant ur partnerns samtalsyta)\n\nInspel `%s` i tråden `%s`, sparat %s (UTC).\n'
                   'Beställningen som citerats: "%s"\n\n---\n\n%s\n' % (inspel['id'], inspel['trad'], inspel['tid'],
                                                                     citat, inspel['text']))
        self._skriv(kat / 'AGARENS-ORD.md', agarord)
        underlag = []
        for i, kid in enumerate([str(x) for x in (a.get('underlag') or [])][:12], 1):
            text = self._underlagstext(kid)
            if not text:
                continue
            namn = 'underlag/%02d-%s.md' % (i, re.sub(r'[^A-Za-z0-9._-]', '_', kid)[:80])
            self._skriv(kat / namn, text)
            underlag.append({'id': kid, 'fil': namn})
        rubrik = str(a.get('rubrik') or '').strip()[:160]
        mal = str(a.get('mal') or '').strip()
        granser = [str(x).strip() for x in (a.get('granser') or []) if str(x).strip()][:20]
        nasta = str(a.get('nasta_handling') or '').strip()
        order = ['# %s' % rubrik, '',
                 '*Överlämning %s från Projektkontorets förbättringspartner, lämnad %s. Sammanställt av partnern ur '
                 'samtalet; bara citatet och AGARENS-ORD.md är Johnnys ordagranna ord.*' % (oid, nu()), '',
                 '## Beslutet (Johnnys ord)', '', '> %s' % citat, '',
                 'Inspel `%s`, tråd `%s`, sparat %s. Hela inspelet: AGARENS-ORD.md.' % (inspel['id'], inspel['trad'],
                                                                                     inspel['tid']), '',
                 '## Mål', '', mal, '', '## Underlag', '']
        order += ['- `%s` → %s' % (u['id'], u['fil']) for u in underlag] or ['- (inget underlag angivet)']
        order += ['', '## Gränser', '']
        order += ['- ' + g for g in granser] or ['- Inga särskilda gränser angivna utöver kontorets gällande regler.']
        order += ['', '## Föreslagen nästa handling', '', nasta, '', '## Mottagare', '', MOTTAGARE[mottagare], '',
                  '## Status', '',
                  'Lämnad av partnern%s. Aktuell status är sista raden i KVITTENS.jsonl. Mottagaren kvitterar med '
                  '`python3 -B tools/partner.py kvittera %s mottagen --av "<session>"`, därefter `startad` och '
                  '`levererad --bevis "<PR/commit/fil>"` (eller `avslagen`). Partnern visar statusen i tråden. '
                  'Överlämningen ger inget eget mandat utöver Johnnys beslut ovan och kontorets gällande regler.' % (
                      ('; en annan beställning än den öppna ' + ', '.join(o['id'] for o in oppna)) if oppna else '', oid),
                  '']
        self._skriv(kat / 'ARBETSORDER.md', '\n'.join(order))
        ap06 = self._ap06(kat, oid, rubrik, mal, citat, granser, nasta, underlag)
        tillstand = {'id': oid, 'status': 'lamnad', 'lamnad': nu(), 'mottagare': mottagare,
                     'mottagare_text': MOTTAGARE[mottagare], 'trad': korning.trad, 'inspel': inspel['id'],
                     'rubrik': rubrik, 'ap06': ap06, 'skild_fran': [o['id'] for o in oppna],
                     'status_not': 'Status vid lämningen. Mottagarens senare kvittenser står i KVITTENS.jsonl '
                                   '(sista raden gäller).'}
        self._skriv(kat / 'OVERLAMNING.json', json.dumps(tillstand, ensure_ascii=False, indent=1))
        (kat / 'KVITTENS.jsonl').touch(mode=0o600)
        visning = (('provinstansens data: overlamningar/partner-%s/' if getattr(self.s.k, 'prov_dolj', ())
                    else 'kontoret/evidence/nasta-uppdrag/local/partner-%s/') % oid)
        self.s.lager.lagg_till('overlamning', overlamning=oid, trad=korning.trad, inspel=inspel['id'],
                               nyckel=inspel['id'], rubrik=rubrik, mal=mal, mottagare=mottagare,
                               katalog=str(kat), katalog_visning=visning, ap06=ap06, granser=granser,
                               nasta_handling=nasta, agarcitat=citat, skild_fran=[o['id'] for o in oppna])
        korning.handelse('overlamning', 'Överlämning %s lämnad till %s' % (oid, mottagare))
        luckor = ap06.get('luckor') or []
        return {'text': ('Överlämningen %s är LÄMNAD (inte mottagen eller startad) till: %s\nPaket: %s (ARBETSORDER.md, '
                         'AGARENS-ORD.md, %d underlagsfiler, AP-06-utkast: %s%s).' % (
                             oid, MOTTAGARE[mottagare], visning, len(underlag), ap06.get('status'),
                             ('; luckor: ' + ', '.join(luckor[:8])) if luckor else ''))}

    def _skriv(self, p: Path, text: str) -> None:
        fd = os.open(p, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(text)

    def _underlagstext(self, kid: str) -> str:
        try:
            if kid.startswith('partner:') or re.match(r'^F-\d+$', kid) or kid.startswith('t_'):
                return self.s.verktyg.v_oppna(_Tyst(), {'id': kid})['text']
            ut = self.s.kallor.oppna(kid, 0)
            if not ut:
                return ''
            return '%s\n%s\nReferens: %s\n\n%s' % (ut['klass_text'], ut['titel'], ut['ref'],
                                                   '\n\n'.join(g['text'] for g in ut['sammanhang']))
        except Exception:
            return ''

    def _ap06(self, kat: Path, oid: str, rubrik, mal, citat, granser, nasta, underlag) -> dict:
        """AP-06-utkast genom kontorets befintliga beredning. Luckor redovisas, inget hittas på."""
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
        spec = {'schema': 1, 'action': 'A1', 'references': [ref],
                'reference_checks': [dict(ref, sha256=kallor[0]['sha256'], status='matched')],
                'requirements': [{'id': 'R1', 'text': mal or rubrik, 'reason': 'Johnnys beställning', 'claims': ['C1'],
                                  'references': ['REF1'], 'tests': []}],
                'tests': [],
                'export': {'title': rubrik or oid, 'context': [{'kind': 'decision', 'text': citat},
                                                                {'kind': 'judgment', 'text': mal or rubrik}],
                           'scope': [nasta] if nasta else [], 'limitations': granser},
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
            return {'status': 'kunde inte beredas (AP-06 avvisade indata)', 'kod': r.returncode}
        luckor = [g.get('code') if isinstance(g, dict) else str(g) for g in svar.get('gaps') or []]
        return {'status': 'utkast' + (' med luckor' if luckor else ''), 'luckor': luckor,
                'mekaniskt_komplett': svar.get('mechanical_complete'), 'katalog': 'ap06/utkast'}

    # --------------------------------------------------------------- kvittenser
    def las_kvittenser(self) -> int:
        """Läs mottagarens kvittenser (KVITTENS.jsonl) och journalför nya statusar."""
        nya = 0
        for o in self.s.lager.fraga("select * from overlamning where status not in ('levererad','avslagen')"):
            d = json.loads(o['data'])
            fil = Path(d.get('katalog') or '') / 'KVITTENS.jsonl'
            if not fil.exists():
                continue
            kanda = {(h.get('status'), h.get('kvitterad')) for h in d.get('historik') or []}
            for rad in fil.read_text('utf-8', errors='replace').splitlines():
                try:
                    k = json.loads(rad)
                except ValueError:
                    continue
                if k.get('status') not in STATUSAR[1:] or (k.get('status'), k.get('kvitterad')) in kanda:
                    continue
                self.s.lager.lagg_till('overlamning_status', overlamning=o['id'], trad=o['trad'], status=k['status'],
                                       av=str(k.get('av') or '')[:200], bevis=str(k.get('bevis') or '')[:500],
                                       kvitterad=k.get('kvitterad'))
                kanda.add((k.get('status'), k.get('kvitterad')))
                nya += 1
        return nya


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
    """k är tjänstens konfiguration (eller, som tidigare, kontorets primärutcheckning)."""
    if status not in STATUSAR[1:]:
        raise ValueError('status måste vara en av ' + ', '.join(STATUSAR[1:]))
    if not re.match(r'^OVL-\d{8}-[A-Za-z0-9]{6}$', oid):
        raise ValueError('okänt överlämnings-id')
    rot = paketrot(k) if hasattr(k, 'kontor_primar') else Path(k) / 'evidence/nasta-uppdrag/local'
    fil = rot / ('partner-' + oid) / 'KVITTENS.jsonl'
    if not fil.exists():
        raise FileNotFoundError(str(fil))
    with open(fil, 'a', encoding='utf-8') as f:
        f.write(json.dumps({'status': status, 'av': av, 'bevis': bevis, 'kvitterad': nu()}, ensure_ascii=False) + '\n')
    return fil
