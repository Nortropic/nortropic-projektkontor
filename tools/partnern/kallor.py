"""Källor: anslut befintligt underlag till ett återbyggbart sökindex och öppna träffar i sitt sammanhang.

Indexet är härlett och byggs om ur originalen med `partner.py index`. Varje post bär sin källklass så att
skillnaden syns mellan original (Improvements-samtalens användar- och assistentturer, ägarens ordagranna
beställningar), register (kontorets beslutslogg och plan på main), härledd syntes (förberedelsekampanjens
leveranser) och partnerns egna anteckningar. Privata filer genomgår hemlighetstvätt innan de indexeras;
modellen får aldrig råa filvägar till privata kataloger.
"""
from __future__ import annotations

import glob
import hashlib
import json
import os
import re
import subprocess
import threading
from pathlib import Path

from .lager import nu

KLASSER = {
    'imp:samtal': 'Improvements-samtal (original, fångat)',
    'imp:dokument': 'Improvements-projektfil (original, fångad)',
    'imp:intervju': 'Ägarintervjun 2026-09-20 (förberedelsekampanjen)',
    'imp:direktiv': 'Ägardirektiv under förberedelsen (ordagrant)',
    'harledd:syntes': 'Härledd syntes 2026-09-20 (förberedelsekampanjen, inte original)',
    'kontor:beslut': 'Kontorets beslutslogg (main)',
    'kontor:plan': 'Kontorets plan (main)',
    'kontor:uppdrag': 'Kontorets uppdragstext (main)',
    'kontor:dokument': 'Kontorets dokument (main)',
    'privat:agarens-ord': 'Ägarens ord, ordagrant sparade av sessioner (privat)',
    'privat:bestallning': 'Beställning/arbetsorder som ägaren lämnat (privat, ordagrann kopia)',
    'privat:lage': 'Sessionernas lägesloggar (privat, daterade)',
    'repo:dokument': 'Dokument i andra Nortropic-repon (main)',
}

HEMLIGT = [
    re.compile(r'-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----'),
    re.compile(r'\bgh[pousr]_[A-Za-z0-9]{20,}'),
    re.compile(r'\bgithub_pat_[A-Za-z0-9_]{20,}'),
    re.compile(r'\bsk-(?:ant-)?[A-Za-z0-9_-]{20,}'),
    re.compile(r'\bxox[abprs]-[A-Za-z0-9-]{10,}'),
    re.compile(r'\bAKIA[0-9A-Z]{16}\b'),
    re.compile(r'\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{8,}'),
    re.compile(r'(?<=#)[A-Za-z0-9_-]{40,}'),
    re.compile(r'(?i)(?<=bypass=)[A-Za-z0-9]{16,}'),
    re.compile(r'(?i)(?<=x-vercel-protection-bypass: )[A-Za-z0-9]{16,}'),
]
HEMLIGT_TILLDELNING = re.compile(
    r'(?i)([A-Za-z0-9_]*(?:secret|token|nyckel|password|lösenord|api[_-]?key|bypass|hemlighet)[A-Za-z0-9_]*)'
    r'(\s*[:=]\s*["\']?)([A-Za-z0-9_\-+/=.]{24,})')


BILAGESTATUS = {'CAPTURED_CONTENT': 'fångad', 'RECOVERED_EXACT': 'återvunnen exakt',
                'RECOVERED_DUPLICATE': 'återvunnen (samma innehåll som en annan bilaga)',
                'UNAVAILABLE': 'otillgänglig: fångades aldrig, innehållet finns inte i korpusen'}


def bilagestatus(b: dict) -> str:
    text = BILAGESTATUS.get(b.get('status'), b.get('status') or 'okänd')
    if not b.get('fil') and b.get('status') != 'UNAVAILABLE':
        text += '; filen saknas i korpusen'
    return text


def tvatta(text: str) -> str:
    """Ta bort hemlighetsliknande värden. Ersättningen syns som [DOLT] så att ingen tror att texten är hel."""
    for m in HEMLIGT:
        text = m.sub('[DOLT]', text)
    return HEMLIGT_TILLDELNING.sub(lambda m: m.group(1) + m.group(2) + '[DOLT]', text)


def _git_show(repo: Path, sokvag: str, ref: str = 'origin/main') -> str | None:
    try:
        r = subprocess.run(['git', '-C', str(repo), 'show', '%s:%s' % (ref, sokvag)], capture_output=True,
                           timeout=30, check=False)
    except (OSError, subprocess.SubprocessError):
        return None
    if r.returncode != 0:
        return None
    return r.stdout.decode('utf-8', errors='replace')


def _datum_ur_id(text: str) -> str:
    m = re.search(r'(20\d\d)(\d\d)(\d\d)', text)
    return '%s-%s-%s' % m.groups() if m else ''


def _delar(text: str, max_tecken: int = 7000) -> list:
    if len(text) <= max_tecken:
        return [text]
    delar, bit = [], []
    langd = 0
    for stycke in re.split(r'(\n\s*\n)', text):
        if langd + len(stycke) > max_tecken and bit:
            delar.append(''.join(bit))
            bit, langd = [], 0
        while len(stycke) > max_tecken:
            delar.append(stycke[:max_tecken])
            stycke = stycke[max_tecken:]
        bit.append(stycke)
        langd += len(stycke)
    if bit:
        delar.append(''.join(bit))
    return delar


def _rubrikdelar(text: str, niva: str = r'#{1,3} ') -> list:
    """[(rubrik, text)] uppdelat vid markdownrubriker."""
    delar, rubrik, rader = [], '', []
    for rad in text.split('\n'):
        if re.match(niva, rad):
            if rader and ''.join(rader).strip():
                delar.append((rubrik, '\n'.join(rader)))
            rubrik, rader = rad.lstrip('#').strip(), [rad]
        else:
            rader.append(rad)
    if rader and ''.join(rader).strip():
        delar.append((rubrik, '\n'.join(rader)))
    return delar


PRIVATA_MONSTER = [(re.compile(r'^owner-words.*\.md$'), 'privat:agarens-ord'),
                   (re.compile(r'^.*agarens-ord.*\.md$', re.I), 'privat:agarens-ord'),
                   (re.compile(r'^owner-directive.*\.md$'), 'privat:agarens-ord'),
                   (re.compile(r'^ARBETSORDER-ORIGINAL.*\.md$'), 'privat:bestallning'),
                   (re.compile(r'^BESTALLNING.*\.md$'), 'privat:bestallning'),
                   (re.compile(r'^tillagg-.*\.md$'), 'privat:bestallning'),
                   (re.compile(r'^LAGE\.md$'), 'privat:lage')]
HOPPA = re.compile(r'^(\.git|node_modules|\.scratch|arbetsyta|arbetsytor|integration-.*|review.*|granskning.*|'
                   r'worktrees?|blobs|harlett|turer|journal|tmp|partner)$')
MEDDELANDE = re.compile(r'^## Meddelande (\d+) — (.+?) \((användare|assistent|system|verktyg)\)\s*$', re.M)

# Delord (PARTNER-SOK-DELORD-20260930): indexet delar texten i hela ord, så första passet hittar ett sökord bara som
# eget ord eller ordbörjan. Svenskan lägger det allmänna begreppet sist (omvärldsbevakning, startvakten), så ett andra
# pass söker sökord med minst DELORD_MIN tecken inuti längre ord i samma tabell. Sökverktyget och urvalet av egna
# bedömningar prövar högst DELORD_TERMER sådana ord per fråga/inspel, så att en lång text inte håller låset länge.
DELORD_MIN = 5
DELORD_TERMER = 10


def delordstermer(fraga: str) -> list:
    """Sökorden som också prövas inuti längre ord: ord utanför citattecken med minst DELORD_MIN tecken, i gemener. Ett
    bindestreck i kanterna tas bort före längdprövningen. Ord med bindestreck inuti eller understreck prövas inte:
    indexet delar redan där, så delarna hittas av första passet."""
    ut = []
    for o in re.findall(r'[\w\-]+', re.sub(r'"[^"]*"', ' ', fraga), re.UNICODE):
        o = o.strip('-').lower()
        if len(o) >= DELORD_MIN and o not in ut and re.fullmatch(r'[^\W_]+', o):
            ut.append(o)
    return ut


def svensk_stam(ord_: str) -> str | None:
    """Snowball Swedish step 1 only (read 2026-09-30); query >=5, resulting stem >=4.
    https://snowballstem.org/algorithms/swedish/stemmer.html
    Region R1 and the conditional s/et rules apply; steps 2 and 3 are not used.
    """
    word = ord_.lower()
    if len(word) < 5:
        return None
    vowels = 'aeiouyäåö'
    r1 = next((max(3, i + 1) for i in range(1, len(word))
               if word[i - 1] in vowels and word[i] not in vowels), len(word))
    suffixes = ('a arna erna heterna orna ad e ade ande arne are aste en anden aren heten ern ar er heter or '
                'as arnas ernas ornas es ades andes ens arens hetens erns at andet het ast s et').split()
    suffix = next((s for s in sorted(suffixes, key=lambda s: (-len(s), s))
                   if word.endswith(s) and len(word) - len(s) >= r1), None)
    if suffix is None:
        return None
    stem = word[:-len(suffix)]
    def et_ending(s):
        exceptions = ('h iet uit fab cit dit alit ilit mit nit pit rit sit tit ivit kvit xit kom rak pak stak').split()
        return (len(s) >= 3 and s[-2] in vowels and s[-1] not in vowels
                and not any(s.endswith(x) for x in exceptions))
    if suffix == 'et' and not et_ending(stem):
        return None
    if suffix == 's':
        if stem.endswith('et') and et_ending(stem[:-2]):
            stem = stem[:-2]
        elif not stem or stem[-1] not in 'bcdfghjklmnoprtvy':
            return None
    return stem if len(stem) >= 4 else None


def stamtermer(fraga: str) -> list:
    # The same query-word cap and phrase/hyphen exclusions as the second pass.
    return list(dict.fromkeys(s for o in delordstermer(fraga)[:DELORD_TERMER]
                              if (s := svensk_stam(o)) is not None))


def _inuti(text: str, term: str) -> int:
    """Hur många gånger term (gemener) står inuti ett ord i text, alltså direkt efter en bokstav eller siffra. Övriga
    tecken (också _ och -) skiljer ord åt, som i indexets tokenisering (unicode61), och täcks av första passet."""
    n, i = 0, text.find(term, 1)
    while i > 0:
        if text[i - 1].isalnum():
            n += 1
        i = text.find(term, i + 1)
    return n


def delordsrang(termer: list, alla_ord: list, titel: str, text: str):
    """Rangnyckel för en post som delordsträff, eller None om inget av termerna står inuti ett ord i den. Ordningen:
    fler av sökordets ord i posten (i vilken form som helst), träff i titeln, fler förekomster inuti ord."""
    titel, text = (titel or '').lower(), (text or '').lower()
    i_titel = sum(_inuti(titel, t) for t in termer)
    i_text = sum(_inuti(text, t) for t in termer)
    if not i_titel and not i_text:
        return None
    tackning = sum(1 for o in alla_ord if o in titel or o in text)
    return (-tackning, -bool(i_titel), -(i_titel + i_text))


def delordsutdrag(text: str, termer: list, ord_: int = 28) -> str:
    """Utdrag kring första ordet där ett sökord står inuti, med de ord som har det märkta «så» (som FTS-utdragen)."""
    orden = list(re.finditer(r'[^\W_]+', text or ''))
    har = lambda o: any(o.group().lower().find(t, 1) > 0 for t in termer)  # noqa: E731
    forsta = next((i for i, o in enumerate(orden) if len(o.group()) > DELORD_MIN and har(o)), None)
    if forsta is None:
        return ''
    start = max(0, min(forsta - ord_ // 2, len(orden) - ord_))
    slut = min(len(orden), start + ord_)
    delar, pos = [], orden[start].start()
    for o in orden[start:slut]:
        delar.append(text[pos:o.start()])
        delar.append('«%s»' % o.group() if har(o) else o.group())
        pos = o.end()
    return (' … ' if start > 0 else '') + ''.join(delar) + (' … ' if slut < len(orden) else '')


def fordela(helord: list, delord: list, antal: int) -> list:
    """Helordsträffarna först i sin ordning, sedan delordsträffarna. Fyller helordsträffarna taket hålls ändå en
    tredjedel av platserna (minst en) för delordsträffar; annars får delordsträffarna de platser som blir över. Med
    antal 1 hålls ingen plats, eftersom den enda platsen då skulle gå till en delordsträff före en helordsträff."""
    if len(helord) >= antal:
        plats = min(len(delord), max(1, antal // 3) if antal >= 2 else 0)
    else:
        plats = min(len(delord), antal - len(helord))
    return helord[:antal - plats] + delord[:plats]


class Kallindex:
    def __init__(self, lager, konfig):
        self.lager = lager
        self.k = konfig
        self.dolda = tuple(getattr(konfig, 'prov_dolj', ()) or ())
        self._bygglas = threading.Lock()

    def dold(self, kid: str) -> bool:
        if not self.dolda:
            return False
        m = re.match(r'imp:ATT-(\d{3})-', kid or '')
        if m:
            kid = 'imp:CONV-%s' % m.group(1)
        return any(kid == d or kid.startswith(d + ':') for d in self.dolda)

    # --------------------------------------------------------------- bygg
    def bygg(self) -> dict:
        avtryck = self.fingeravtryck()  # före läsningen: en ändring under bygget ger ett nytt bygge nästa gång
        poster = []
        tackning = {}
        for namn, fn in (('improvements', self._improvements), ('kampanj', self._kampanj),
                         ('kontoret', self._kontoret), ('privat', self._privat), ('repon', self._repon)):
            try:
                nya, t = fn()
            except Exception as fel:  # en källa som fallerar gör bara sin egen del otillgänglig
                nya, t = [], {'fel': '%s: %s' % (type(fel).__name__, str(fel)[:200])}
            poster.extend(nya)
            tackning[namn] = t
        with self.lager.skrivning() as db:
            db.execute("delete from kalla")
            db.execute("delete from sok where klass not like 'partner:%'")
            for p in poster:
                db.execute('insert or replace into kalla values(?,?,?,?,?,?,?,?,?,?)',
                           (p['id'], p['klass'], p['titel'], p['talare'], p['datum'], p['ref'], p['text'],
                            p['grupp'], p['ordning'], json.dumps(p.get('data') or {}, ensure_ascii=False)))
                for i, bit in enumerate(_delar(p['text'])):
                    db.execute('insert into sok values(?,?,?,?,?,?)',
                               (p['id'] if i == 0 else '%s~%d' % (p['id'], i), p['klass'], p['titel'], p['talare'],
                                p['datum'], bit))
            db.execute("insert or replace into meta values('kalltackning', ?)",
                       (json.dumps(tackning, ensure_ascii=False),))
            db.execute("insert or replace into meta values('kallavtryck', ?)", (json.dumps(avtryck, sort_keys=True),))
            db.execute("insert or replace into meta values('kallindex_byggt', ?)", (nu(),))
        return {'poster': len(poster), 'tackning': tackning}

    # --------------------------------------------------------------- färskhet
    def fingeravtryck(self) -> dict:
        """Billigt avtryck av det källindexet byggs ur: repons origin/main, de privata ägarord-, beställnings- och
        lägesfilerna (sökväg, storlek, ändringstid) och korpusens manifest. Ändras det byggs indexet om."""
        def main(rot) -> str | None:
            try:
                r = subprocess.run(['git', '-C', str(rot), 'rev-parse', '--verify', '-q', 'origin/main'],
                                   capture_output=True, text=True, timeout=10)
            except (OSError, subprocess.SubprocessError):
                return None
            return r.stdout.strip() or None

        def stat(p: Path):
            try:
                st = p.stat()
                return [st.st_size, st.st_mtime_ns]
            except OSError:
                return None
        repon = {'kontoret': main(self.k.kontor_primar)}
        for namn, rot in sorted((self.k.repon or {}).items()):
            if namn != 'kontoret':
                repon[namn] = main(rot)
        privata = hashlib.sha256()
        for p, _ in self._privata_filer():
            privata.update(json.dumps([str(p), stat(p)]).encode())
        return {'repon': repon, 'privata': privata.hexdigest(),
                'korpus': stat(Path(self.k.improvements) / 'project-manifest.json'),
                'kampanj': stat(Path(self.k.kampanj) / 'evidence/source-boundary-20260919.json')}

    def inaktuellt(self) -> bool:
        r = self.lager.en("select varde from meta where nyckel='kallavtryck'")
        return not r or json.loads(r['varde']) != json.loads(json.dumps(self.fingeravtryck(), sort_keys=True))

    def uppdatera_om_inaktuellt(self) -> bool:
        """Bygg om källindexet om något av det det byggs ur har ändrats. Returnerar om det byggdes om."""
        with self._bygglas:
            if not self.inaktuellt():
                return False
            self.bygg()
            return True

    def byggt(self) -> str | None:
        r = self.lager.en("select varde from meta where nyckel='kallindex_byggt'")
        return r['varde'] if r else None

    def tackning(self) -> dict:
        r = self.lager.en("select varde from meta where nyckel='kalltackning'")
        return json.loads(r['varde']) if r else {}

    def _improvements(self):
        rot = Path(self.k.improvements)
        manifest = json.loads((rot / 'project-manifest.json').read_text('utf-8'))
        uppdaterad = self._uppdaterad_tider()
        poster = []
        bilagor_tot = {'fangade': 0, 'saknade': 0, 'registreringar': 0}
        unika_bilagor = set()
        antal = {'samtal': 0, 'dokument': 0, 'meddelanden': 0}
        for kalla in manifest['sources']:
            sid = kalla['source_id']
            rev = kalla['revisions'][-1] if kalla.get('revisions') else None
            if not rev:
                continue
            fil = rot.parents[1] / rev['path']
            if not fil.exists():
                continue
            text = fil.read_text('utf-8', errors='replace')
            titel = kalla.get('title') or sid
            nyckel = kalla.get('conversation_key', '')
            data = {'url': kalla.get('url'), 'fangad': rev.get('captured_at'), 'revision': rev.get('revision'),
                    'sha256': rev.get('sha256'), 'meddelanden': rev.get('message_count'),
                    'uppdaterad': uppdaterad.get(nyckel), 'kalla': sid}
            bilagor = self._imp_bilagor(rot, sid)
            data['bilagor'] = bilagor
            for b in bilagor:
                if b.get('fil'):
                    unika_bilagor.add(b.get('sha256') or b['fil'])
                else:
                    bilagor_tot['saknade'] += 1
                bilagor_tot['registreringar'] += 1
            if sid.startswith('DOC-'):
                antal['dokument'] += 1
                for i, (rubrik, bit) in enumerate(_rubrikdelar(text) or [('', text)]):
                    poster.append(self._post('imp:%s:s%d' % (sid, i + 1), 'imp:dokument', titel, 'projektfil',
                                             (rev.get('captured_at') or ''), '%s#%d' % (rev['path'], i + 1), bit,
                                             'imp:' + sid, i + 1, dict(data, avsnitt=rubrik)))
                continue
            antal['samtal'] += 1
            traffar = list(MEDDELANDE.finditer(text))
            for j, m in enumerate(traffar):
                slut = traffar[j + 1].start() if j + 1 < len(traffar) else len(text)
                kropp = text[m.end():slut].strip().rstrip('-').strip()
                nr = int(m.group(1))
                roll = m.group(3)
                talare = 'Johnny' if roll == 'användare' else ('ChatGPT (assistent)' if roll == 'assistent' else roll)
                bundna = [b['id'] for b in bilagor if b.get('meddelande') == nr]
                antal['meddelanden'] += 1
                poster.append(self._post('imp:%s:m%d' % (sid, nr), 'imp:samtal', titel, talare,
                                         data.get('uppdaterad') or rev.get('captured_at') or '',
                                         '%s (meddelande %d)' % (kalla.get('url') or rev['path'], nr), kropp,
                                         'imp:' + sid, nr, dict(data, roll=roll, bilagor_har=bundna)))
        bilagor_tot['fangade'] = len(unika_bilagor)
        grans = self._kallgrans()
        t = {'korpus': str(rot), 'inventering': manifest.get('inventory_revision'),
             'status': manifest.get('project_status'), 'kallgrans': grans, **antal, 'bilagor': bilagor_tot}
        return poster, t

    def _uppdaterad_tider(self) -> dict:
        tider = {}
        for p in glob.glob(str(Path(self.k.kampanj) / 'evidence/live-capture/*/source-export.json')):
            try:
                item = json.loads(Path(p).read_text('utf-8')).get('item') or {}
            except (OSError, ValueError):
                continue
            if item.get('key') and item.get('updated'):
                tider[item['key']] = item['updated'][:10]
        return tider

    def _kallgrans(self) -> dict:
        p = Path(self.k.kampanj) / 'evidence/source-boundary-20260919.json'
        try:
            d = json.loads(p.read_text('utf-8'))
        except (OSError, ValueError):
            return {}
        def antal(v):
            return v if isinstance(v, int) else len(v or [])
        return {'fryst': d.get('frozen_at'), 'observation_slut': d.get('observation_end'),
                'kallor': antal(d.get('sources')), 'bilage_id': antal(d.get('attachment_ids')),
                'historiskt_otillgangliga': antal(d.get('historical_unavailable')),
                'begransningar': d.get('limits') or []}

    def _imp_bilagor(self, rot: Path, sid: str) -> list:
        ut = []
        filer = sorted((rot / 'sources' / sid).glob('attachments-r*.json'))
        if not filer:
            return ut
        try:
            d = json.loads(filer[-1].read_text('utf-8'))
        except ValueError:
            return ut
        for a in d.get('attachments') or []:
            nr = None
            m = re.search(r'Meddelande (\d+)', a.get('message_binding') or '')
            if m:
                nr = int(m.group(1))
            fil = a.get('artifact_path')
            finns = bool(fil) and (rot.parents[1] / fil).exists()
            ut.append({'id': 'imp:' + a['attachment_id'], 'namn': a.get('original_filename') or a['attachment_id'],
                       'mime': a.get('media_type'), 'status': a.get('capture_status'), 'meddelande': nr,
                       'fil': str(rot.parents[1] / fil) if finns else None, 'storlek': a.get('byte_length'),
                       'sha256': a.get('content_sha256')})
        return ut

    def _kampanj(self):
        rot = Path(self.k.kampanj)
        poster = []
        filer = {'delivery/INTERVJU.md': ('imp:intervju', 'Johnny (intervjusvar, återgivna)'),
                 'delivery/HELHETSBILD.md': ('harledd:syntes', 'förberedelsekampanjen'),
                 'delivery/BYGGFORSLAG.md': ('harledd:syntes', 'förberedelsekampanjen'),
                 'delivery/ERRATA.md': ('harledd:syntes', 'förberedelsekampanjen'),
                 'delivery/KVARSTAENDE-OSAKERHETER.md': ('harledd:syntes', 'förberedelsekampanjen'),
                 'delivery/SOURCE-BASE.md': ('harledd:syntes', 'förberedelsekampanjen'),
                 'delivery/AGARFRAGOR.md': ('harledd:syntes', 'förberedelsekampanjen')}
        for p in sorted(rot.glob('inputs/owner-directive-*.md')):
            filer[str(p.relative_to(rot))] = ('imp:direktiv', 'Johnny (ordagrant)')
        for rel, (klass, talare) in filer.items():
            p = rot / rel
            if not p.exists():
                continue
            text = tvatta(p.read_text('utf-8', errors='replace'))
            datum = _datum_ur_id(rel) or '2026-09-20'
            for i, (rubrik, bit) in enumerate(_rubrikdelar(text) or [('', text)]):
                poster.append(self._post('kampanj:%s:%d' % (rel, i + 1), klass, '%s — %s' % (Path(rel).name, rubrik),
                                         talare, datum, 'förberedelsekampanjen/%s#%d' % (rel, i + 1), bit,
                                         'kampanj:' + rel, i + 1, {}))
        return poster, {'filer': len(filer)}

    def _kontoret(self):
        repo = Path(self.k.kontor_primar)
        poster = []
        beslut = _git_show(repo, 'docs/decisions.md') or ''
        ids = []
        for i, (rubrik, bit) in enumerate(_rubrikdelar(beslut, r'## ')):
            bid = rubrik.split(' ')[0] if rubrik else 'inledning'
            ids.append(bid)
            ersatt = 'SUPERSEDED' in bit[:4000]
            poster.append(self._post('kontor:beslut:%s' % bid, 'kontor:beslut', rubrik, 'kontorets beslutslogg',
                                     _datum_ur_id(bid), 'nortropic-projektkontor/docs/decisions.md (main) §%s' % bid,
                                     bit, 'kontor:beslut', i + 1, {'ersatt_markerad': ersatt}))
        for sokvag, klass, namn in (('docs/plan.md', 'kontor:plan', 'plan'), ('docs/uppdrag.md', 'kontor:uppdrag', 'uppdrag'),
                                    ('DEFINITION.md', 'kontor:dokument', 'definition'), ('AGENTS.md', 'kontor:dokument', 'agents'),
                                    ('README.md', 'kontor:dokument', 'readme')):
            text = _git_show(repo, sokvag) or ''
            for i, (rubrik, bit) in enumerate(_rubrikdelar(text, r'#{1,2} ') or [('', text)]):
                if not bit.strip():
                    continue
                poster.append(self._post('kontor:%s:%d' % (namn, i + 1), klass, rubrik or sokvag, 'kontoret',
                                         _datum_ur_id(rubrik), 'nortropic-projektkontor/%s (main) #%d' % (sokvag, i + 1),
                                         bit, 'kontor:' + namn, i + 1, {}))
        main = subprocess.run(['git', '-C', str(repo), 'log', '-1', '--format=%H %cI', 'origin/main'],
                              capture_output=True, text=True, timeout=10).stdout.strip()
        return poster, {'beslut': len(ids), 'main': main}

    def _privata_filer(self):
        """Ägarord, beställningar och lägesloggar under kontorets evidence/**/local, som (sökväg, klass)."""
        rot = Path(self.k.kontor_primar) / 'evidence'
        for mapp, kataloger, filer in os.walk(rot):
            kataloger[:] = sorted(d for d in kataloger if not HOPPA.match(d)
                                  and not os.path.exists(os.path.join(mapp, d, '.git')))
            if '/local' not in mapp.replace(str(rot), ''):
                continue
            for namn in sorted(filer):
                klass = next((k for m, k in PRIVATA_MONSTER if m.match(namn)), None)
                p = Path(mapp) / namn
                try:  # en annan session kan flytta eller ta bort filen under vandringen
                    ok = bool(klass) and p.is_file() and p.stat().st_size <= 400_000
                except OSError:
                    ok = False
                if ok:
                    yield p, klass

    def _privat(self):
        rot = Path(self.k.kontor_primar) / 'evidence'
        sedda, innehall, poster = set(), set(), []
        talare = {'privat:agarens-ord': 'Johnny (ordagrant, sparat av session)',
                  'privat:bestallning': 'Johnny lämnade (sammanställt underlag, inte ordagranna ägarord)',
                  'privat:lage': 'arbetande session (lägeslogg)'}
        for p, klass in self._privata_filer():
            try:
                data = p.read_bytes()
            except OSError:
                continue
            h = hashlib.sha256(data).hexdigest()
            if h in innehall:
                continue
            innehall.add(h)
            sedda.add(p)
            rel = str(p.relative_to(rot))
            text = tvatta(data.decode('utf-8', errors='replace'))
            datum = _datum_ur_id(rel)
            for i, (rubrik, bit) in enumerate(_rubrikdelar(text) or [('', text)]):
                if not bit.strip():
                    continue
                poster.append(self._post('privat:%s:%d' % (rel, i + 1), klass, '%s — %s' % (rel, rubrik),
                                         talare[klass], datum, 'kontoret/evidence/%s#%d' % (rel, i + 1), bit,
                                         'privat:' + rel, i + 1, {}))
        return poster, {'filer': len(sedda)}

    def _repon(self):
        poster = []
        urval = {'runtime': ['README.md', 'docs/plan.md', 'docs/decisions.md', 'docs/runbook.md'],
                 'digitala': ['README.md', 'AGENTS.md', 'OVERSIKT.md', 'KEDJA.md', 'ARBETSSATT.md', 'REGISTER.md'],
                 'kundstart': ['README.md', 'DRIFT.md']}
        antal = {}
        for repo, filer in urval.items():
            rot = self.k.repon.get(repo)
            if not rot:
                continue
            antal[repo] = 0
            for sokvag in filer:
                text = _git_show(Path(rot), sokvag)
                if not text:
                    continue
                antal[repo] += 1
                niva = r'## ' if sokvag.endswith('decisions.md') else r'#{1,2} '
                for i, (rubrik, bit) in enumerate(_rubrikdelar(text, niva) or [('', text)]):
                    if not bit.strip():
                        continue
                    poster.append(self._post('repo:%s:%s:%d' % (repo, sokvag, i + 1), 'repo:dokument',
                                             '%s/%s — %s' % (repo, sokvag, rubrik), repo, _datum_ur_id(rubrik),
                                             '%s/%s (main) #%d' % (repo, sokvag, i + 1), bit,
                                             'repo:%s:%s' % (repo, sokvag), i + 1, {}))
        return poster, antal

    @staticmethod
    def _post(pid, klass, titel, talare, datum, ref, text, grupp, ordning, data) -> dict:
        return {'id': pid, 'klass': klass, 'titel': titel, 'talare': talare, 'datum': datum or '', 'ref': ref,
                'text': text, 'grupp': grupp, 'ordning': ordning, 'data': data}

    # --------------------------------------------------------------- sök
    @staticmethod
    def _fts_fraga(fraga: str, eller: bool) -> str:
        fraser = re.findall(r'"([^"]+)"', fraga)
        rest = re.sub(r'"[^"]*"', ' ', fraga)
        ord_ = [o for o in re.findall(r'[\w\-]+', rest, re.UNICODE) if len(o) >= 2]
        termer = ['"%s"' % f.replace('"', '') for f in fraser]
        for o in ord_:
            o = o.replace('"', '')
            termer.append('"%s"*' % o if len(o) >= 4 else '"%s"' % o)
        if not termer:
            return ''
        return (' OR ' if eller else ' AND ').join(termer)

    def sok(self, fraga: str, omfang: list | None = None, antal: int = 12) -> list:
        antal = max(1, min(int(antal or 12), 30))
        villkor, args = '', []
        if omfang:
            prefix = {'improvements': ['imp:%', 'kampanj:%'], 'kontoret': ['kontor:%', 'privat:%'],
                      'partner': ['partner:%'], 'repon': ['repo:%'], 'syntes': ['harledd:%'],
                      'agarens-ord': ['privat:agarens-ord', 'privat:bestallning', 'imp:intervju', 'imp:direktiv']}
            delar = []
            for o in omfang:
                for p in prefix.get(o, []):
                    delar.append('klass like ?')
                    args.append(p)
            if delar:
                villkor = ' and (' + ' or '.join(delar) + ')'
        sedda, ut = set(), []
        for eller in (False, True):
            q = self._fts_fraga(fraga, eller)
            if not q:
                break
            try:
                rader = self.lager.fraga(
                    "select kalla_id, klass, titel, talare, datum, snippet(sok, 5, '«', '»', ' … ', 28) as utdrag, "
                    "bm25(sok, 0, 0, 3.0, 0, 0, 1.0) as rang from sok where sok match ?" + villkor +
                    " order by rang limit ?", [q] + args + [antal * 3])
            except Exception:
                rader = []
            for r in rader:
                bas = r['kalla_id'].split('~')[0]
                if bas in sedda or self.dold(bas):
                    continue
                sedda.add(bas)
                r['kalla_id'] = bas
                ut.append(r)
            if len(ut) >= antal:
                break
        for r in ut:
            r['traff'] = 'ord'
        extra = self._delord(fraga, villkor, args, sedda, antal)
        extra += self._stam(fraga, villkor, args, sedda, antal)
        ut = fordela(ut, extra, antal)
        for r in ut:
            r['kalla_klass'] = KLASSER.get(r['klass'], r['klass'])
            if r['klass'] == 'partner:forstaelse':
                f = self.lager.en('select nr, ersatt_av from forstaelse where id=?', (r['kalla_id'][8:],))
                if f:
                    r['status'] = 'ersatt' if f['ersatt_av'] else 'gällande'
                    r['nr'] = 'F-%d' % f['nr']
            elif r['klass'] == 'kontor:beslut':
                k = self.lager.en('select data from kalla where id=?', (r['kalla_id'],))
                if k and json.loads(k['data']).get('ersatt_markerad'):
                    r['status'] = 'innehåller SUPERSEDED-markering'
            r.pop('rang', None)
        return ut

    def _delord(self, fraga: str, villkor: str, args: list, sedda: set, antal: int) -> list:
        """Andra passet: poster där ett sökord (minst DELORD_MIN tecken) står inuti ett längre ord, i samma tabell och
        med samma omfång. Poster som första passet redan gav och dolda källor räknas inte; en raderad tråd finns inte
        i tabellen. LIKE väljer kandidaterna (viker bara versaler i A–Z); Python avgör att ordet står inuti ett ord."""
        termer = delordstermer(fraga)[:DELORD_TERMER]
        if not termer:
            return []
        monster = []
        for t in termer:
            m = '%' + t.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_') + '%'
            monster += [m, m]
        alla_ord = [f.lower() for f in re.findall(r'"([^"]+)"', fraga)] + list(dict.fromkeys(
            o.strip('-').lower() for o in re.findall(r'[\w\-]+', re.sub(r'"[^"]*"', ' ', fraga), re.UNICODE)
            if len(o.strip('-')) >= 2))
        try:
            rader = self.lager.fraga(
                "select kalla_id, klass, titel, talare, datum, text from sok where (" +
                ' or '.join(["titel like ? escape '\\' or text like ? escape '\\'"] * len(termer)) + ")" + villkor +
                " order by rowid", monster + args)
        except Exception:
            return []
        kandidater = []
        for i, r in enumerate(rader):
            bas = r['kalla_id'].split('~')[0]
            if bas in sedda or self.dold(bas):
                continue
            rang = delordsrang(termer, alla_ord, r['titel'], r['text'])
            if rang is not None:
                kandidater.append((rang + (i,), bas, r))
        ut = []
        for _, bas, r in sorted(kandidater, key=lambda k: k[0]):
            if bas in sedda:
                continue
            sedda.add(bas)
            text = r.pop('text')
            ut.append(dict(r, kalla_id=bas, traff='delord',
                           utdrag=delordsutdrag(text, termer) or delordsutdrag(r['titel'], termer)))
            if len(ut) >= antal:
                break
        return ut

    def _stam(self, fraga: str, villkor: str, args: list, sedda: set, antal: int) -> list:
        """Third pass: stem prefixes in the same FTS index and visibility scope."""
        termer = stamtermer(fraga)
        if not termer:
            return []
        query = ' OR '.join('"%s"*' % s for s in termer)
        rows = self.lager.fraga(
            "select kalla_id, klass, titel, talare, datum, snippet(sok, 5, '«', '»', ' … ', 28) as utdrag "
            "from sok where sok match ?" + villkor + " order by bm25(sok, 0, 0, 3.0, 0, 0, 1.0), rowid",
            [query] + args)
        result = []
        for r in rows:
            bas = r['kalla_id'].split('~')[0]
            if bas in sedda or self.dold(bas):
                continue
            sedda.add(bas)
            result.append(dict(r, kalla_id=bas, traff='stam'))
            if len(result) >= antal:
                break
        return result

    # --------------------------------------------------------------- öppna
    def oppna(self, kid: str, omkrets: int = 2) -> dict | None:
        post = self.lager.en('select * from kalla where id=?', (kid,))
        if not post or self.dold(kid):
            return None
        data = json.loads(post['data'] or '{}')
        omkrets = max(0, min(int(omkrets), 6))
        grannar = [g for g in self.lager.fraga('select id, talare, ordning, text, titel from kalla where grupp=? and ordning '
                                               'between ? and ? order by ordning',
                                               (post['grupp'], post['ordning'] - omkrets, post['ordning'] + omkrets))
                   if not self.dold(g['id'])]
        totalt = self.lager.en('select count(*) as n, max(ordning) as sista from kalla where grupp=?', (post['grupp'],))
        ut = {'id': kid, 'klass': post['klass'], 'klass_text': KLASSER.get(post['klass'], post['klass']),
              'titel': post['titel'], 'datum': post['datum'], 'ref': post['ref'],
              'position': '%s av %s' % (post['ordning'], totalt['sista']), 'sammanhang': []}
        for g in grannar:
            text = g['text']
            kap = len(text) > 9000
            ut['sammanhang'].append({'id': g['id'], 'talare': g['talare'], 'nr': g['ordning'],
                                     'denna': g['id'] == kid, 'text': text[:9000] + ('\n[… avkapat, öppna posten ensam '
                                                                                  'för resten]' if kap else '')})
        if post['klass'].startswith('imp:'):
            ut['samtal'] = {k: data.get(k) for k in ('url', 'fangad', 'uppdaterad', 'revision', 'sha256', 'meddelanden')}
            ut['tid_not'] = ('Meddelandetider saknas i fångsten; datum är samtalets senaste uppdatering eller '
                             'fångstdatum, inte när just detta meddelande skrevs.')
            visade = [g['ordning'] for g in grannar]
            if visade:
                ut['visar'] = '%s %d–%d av %s' % ('avsnitt' if post['klass'] == 'imp:dokument' else 'meddelande',
                                                  min(visade), max(visade), totalt['sista'])
            alla = data.get('bilagor') or []
            bilagor = [b for b in alla if b.get('meddelande') in visade]
            if bilagor:
                ut['bilagor'] = [dict({k: b.get(k) for k in ('id', 'namn', 'mime', 'meddelande')},
                                      status=bilagestatus(b)) for b in bilagor]
            ovriga = [b for b in alla if b not in bilagor]
            if ovriga:  # även bilagor utan meddelandebindning; annars ser läsaren aldrig att de finns
                ut['ovriga_bilagor'] = [dict({k: b.get(k) for k in ('id', 'namn', 'mime', 'meddelande')},
                                             status=bilagestatus(b)) for b in ovriga]
            if post['ordning'] < (totalt['sista'] or 0):
                ut['senare_i_samtalet'] = ('%d meddelanden kommer efter detta i samma samtal; senare rättelser kan '
                                           'finnas där.' % ((totalt['sista'] or 0) - post['ordning']))
        if data.get('ersatt_markerad'):
            ut['varning'] = 'Posten innehåller en SUPERSEDED-markering; läs vad som ersätter den innan den används.'
        rel = self.lager.fraga("select nr, slag, text, auktoritet, ersatt_av, tid from forstaelse "
                               "where kallor like ? order by nr", ('%' + post['grupp'].split(':', 1)[-1] + '%',))
        if rel:
            ut['partnerns_forstaelse_som_citerar'] = [
                {'nr': 'F-%d' % r['nr'], 'slag': r['slag'], 'auktoritet': r['auktoritet'],
                 'status': 'ersatt' if r['ersatt_av'] else 'gällande', 'text': r['text'][:600], 'tid': r['tid']}
                for r in rel]
        return ut

    def bilaga(self, kid: str) -> dict | None:
        """Improvements-bilaga ur korpusen (id imp:ATT-…)."""
        m = re.match(r'imp:(ATT-(\d{3})-\d{3})$', kid or '')
        if not m or self.dold(kid):
            return None
        sid = 'CONV-%s' % m.group(2)
        post = self.lager.en("select data from kalla where grupp=? limit 1", ('imp:' + sid,))
        if not post:
            return None
        for b in json.loads(post['data']).get('bilagor') or []:
            if b['id'] == kid:
                return b
        return None
