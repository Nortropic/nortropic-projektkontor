"""Bilagor: typ ur innehållet, härledda läsformer och ärlig stödgräns.

Originalet ligger orört i lagret. Här byggs bara härledda former som kan göras om: textlager (PDF genom
pdftotext, dokument genom macOS textutil eller zip-XML), sidbilder (pdftoppm) och en modellanpassad bild
(sips). Format som saknar extraktion på den här datorn (ljud, video, okänt) sparas men märks som oläst;
ingen text påstås om dem.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import zipfile
from pathlib import Path
from xml.etree import ElementTree

BILD = {'png': 'image/png', 'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'gif': 'image/gif', 'webp': 'image/webp',
        'heic': 'image/heic', 'heif': 'image/heif', 'tif': 'image/tiff', 'tiff': 'image/tiff', 'bmp': 'image/bmp'}
TEXT = {'txt', 'md', 'markdown', 'csv', 'tsv', 'json', 'yaml', 'yml', 'toml', 'xml', 'html', 'htm', 'py', 'js',
        'ts', 'tsx', 'jsx', 'css', 'sh', 'zsh', 'sql', 'log', 'ini', 'cfg', 'conf', 'rst', 'svg', 'swift', 'go',
        'rs', 'java', 'kt', 'rb', 'php', 'c', 'h', 'cpp', 'hpp', 'mjs', 'cjs', 'env.example', 'diff', 'patch'}
DOKUMENT = {'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'doc': 'application/msword', 'rtf': 'application/rtf', 'odt': 'application/vnd.oasis.opendocument.text',
            'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'pages': 'application/x-iwork-pages', 'key': 'application/x-iwork-keynote',
            'numbers': 'application/x-iwork-numbers'}
LJUD = {'mp3': 'audio/mpeg', 'm4a': 'audio/mp4', 'wav': 'audio/wav', 'aac': 'audio/aac', 'ogg': 'audio/ogg',
        'flac': 'audio/flac', 'opus': 'audio/opus'}
VIDEO = {'mp4': 'video/mp4', 'mov': 'video/quicktime', 'webm': 'video/webm', 'mkv': 'video/x-matroska',
         'avi': 'video/x-msvideo', 'm4v': 'video/x-m4v'}

MODELL_BILD_MAX_BYTE = 3_700_000   # under API:ts gräns för base64-bilder med marginal
MODELL_BILD_MAX_SIDA = 1568
TEXT_MAX_TECKEN_I_TUR = 60_000


def sakert_namn(namn: str) -> str:
    rent = re.sub(r'[\\/:*?"<>|\x00-\x1f]', '_', (namn or '').strip()).strip('. ')
    return (rent or 'fil')[:160]


def _andelse(namn: str) -> str:
    return namn.rsplit('.', 1)[-1].lower() if '.' in namn else ''


def _ar_text(b: bytes) -> bool:
    if b'\x00' in b[:65536]:
        return False
    try:
        b[:65536].decode('utf-8')
        return True
    except UnicodeDecodeError:
        # en avkapad flerbytesföljd i slutet av provet är inte ett fel
        try:
            b[:65530].decode('utf-8')
            return True
        except UnicodeDecodeError:
            return False


def identifiera(namn: str, huvud: bytes) -> dict:
    """Klass och mediatyp ur innehållet (magiska byte), med filändelsen bara som stöd."""
    a = _andelse(namn)
    if huvud.startswith(b'\x89PNG\r\n\x1a\n'):
        return {'klass': 'bild', 'mime': 'image/png'}
    if huvud.startswith(b'\xff\xd8\xff'):
        return {'klass': 'bild', 'mime': 'image/jpeg'}
    if huvud[:6] in (b'GIF87a', b'GIF89a'):
        return {'klass': 'bild', 'mime': 'image/gif'}
    if huvud[:4] == b'RIFF' and huvud[8:12] == b'WEBP':
        return {'klass': 'bild', 'mime': 'image/webp'}
    if huvud[4:8] == b'ftyp' and huvud[8:12] in (b'heic', b'heix', b'mif1', b'msf1', b'heim', b'heis'):
        return {'klass': 'bild', 'mime': 'image/heic'}
    if huvud[:4] in (b'II*\x00', b'MM\x00*'):
        return {'klass': 'bild', 'mime': 'image/tiff'}
    if huvud[:2] == b'BM' and a == 'bmp':
        return {'klass': 'bild', 'mime': 'image/bmp'}
    if huvud.startswith(b'%PDF'):
        return {'klass': 'pdf', 'mime': 'application/pdf'}
    if huvud[4:8] == b'ftyp':
        if a in LJUD:
            return {'klass': 'ljud', 'mime': LJUD[a]}
        return {'klass': 'video', 'mime': VIDEO.get(a, 'video/mp4')}
    if huvud[:4] == b'PK\x03\x04':
        if a in DOKUMENT:
            return {'klass': 'dokument', 'mime': DOKUMENT[a]}
        return {'klass': 'annat', 'mime': 'application/zip'}
    if huvud[:5] == b'{\\rtf':
        return {'klass': 'dokument', 'mime': 'application/rtf'}
    if huvud[:8] == b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1' and a == 'doc':
        return {'klass': 'dokument', 'mime': 'application/msword'}
    if huvud[:3] == b'ID3' or huvud[:4] in (b'fLaC', b'OggS') or (huvud[:4] == b'RIFF' and huvud[8:12] == b'WAVE'):
        return {'klass': 'ljud', 'mime': LJUD.get(a, 'audio/mpeg')}
    if huvud[:4] == b'\x1aE\xdf\xa3':
        return {'klass': 'video', 'mime': VIDEO.get(a, 'video/webm')}
    if _ar_text(huvud):
        if a == 'svg' or b'<svg' in huvud[:4096].lower():
            return {'klass': 'text', 'mime': 'image/svg+xml'}  # läses som text, visas aldrig som bild
        return {'klass': 'text', 'mime': 'text/plain; charset=utf-8'}
    return {'klass': 'annat', 'mime': 'application/octet-stream'}


def _kor(argv: list, timeout: int = 120) -> subprocess.CompletedProcess:
    return subprocess.run(argv, capture_output=True, timeout=timeout, check=False)


def harled(original: Path, klass: str, mime: str, katalog: Path) -> dict:
    """Bygg läsformer i `katalog` (idempotent). Returnerar beskrivning med stöd och gränser."""
    katalog.mkdir(parents=True, exist_ok=True, mode=0o700)
    info_fil = katalog / 'info.json'
    if info_fil.exists():
        try:
            return json.loads(info_fil.read_text('utf-8'))
        except ValueError:
            pass
    info = {'klass': klass, 'mime': mime, 'text': False, 'sidor': None, 'modellbild': False,
            'stod': '', 'begransning': ''}
    try:
        if klass == 'bild':
            info.update(_modellbild(original, mime, katalog))
        elif klass == 'pdf':
            info.update(_pdf(original, katalog))
        elif klass == 'text':
            data = original.read_bytes()
            text = data.decode('utf-8', errors='replace')
            (katalog / 'text.txt').write_text(text, 'utf-8')
            info.update(text=True, stod='texten läst som den är')
        elif klass == 'dokument':
            info.update(_dokument(original, mime, katalog))
        elif klass in ('ljud', 'video'):
            info.update(stod='sparad, inte läst',
                        begransning='Det finns ingen ljud-/videoextraktion på den här datorn (ingen ffmpeg eller '
                                    'transkribering). Innehållet har varken hörts eller setts.')
        else:
            info.update(stod='sparad, inte läst', begransning='Okänt format; innehållet har inte lästs.')
    except (OSError, subprocess.SubprocessError) as fel:
        info['begransning'] = 'Läsformen kunde inte byggas: %s' % type(fel).__name__
    info_fil.write_text(json.dumps(info, ensure_ascii=False), 'utf-8')
    return info


def _modellbild(original: Path, mime: str, katalog: Path) -> dict:
    mal = katalog / 'modellbild.jpg'
    storlek = original.stat().st_size
    sips = shutil.which('sips') or '/usr/bin/sips'
    if mime in ('image/png', 'image/jpeg', 'image/gif', 'image/webp') and storlek <= MODELL_BILD_MAX_BYTE:
        mått = _bildmatt(original, sips)
        if mått and max(mått) <= 8000:
            return {'modellbild': True, 'modellbild_fil': 'original', 'matt': mått,
                    'stod': 'bilden ges till modellen som den är'}
    r = _kor([sips, '-s', 'format', 'jpeg', '-s', 'formatOptions', '85', '-Z', str(MODELL_BILD_MAX_SIDA),
              str(original), '--out', str(mal)])
    if r.returncode == 0 and mal.exists() and mal.stat().st_size <= MODELL_BILD_MAX_BYTE:
        return {'modellbild': True, 'modellbild_fil': mal.name, 'matt': _bildmatt(mal, sips),
                'stod': 'bilden ges till modellen nedskalad (originalet är sparat orört)'}
    return {'modellbild': False, 'begransning': 'Bilden kunde inte göras läsbar för modellen på den här datorn.'}


def _bildmatt(p: Path, sips: str):
    r = _kor([sips, '-g', 'pixelWidth', '-g', 'pixelHeight', str(p)], timeout=30)
    b = re.search(rb'pixelWidth: (\d+)', r.stdout)
    h = re.search(rb'pixelHeight: (\d+)', r.stdout)
    return [int(b.group(1)), int(h.group(1))] if b and h else None


def _pdf(original: Path, katalog: Path) -> dict:
    pdftotext = shutil.which('pdftotext') or '/opt/homebrew/bin/pdftotext'
    pdfinfo = shutil.which('pdfinfo') or '/opt/homebrew/bin/pdfinfo'
    sidor = None
    r = _kor([pdfinfo, str(original)], timeout=60)
    m = re.search(rb'Pages:\s+(\d+)', r.stdout)
    if m:
        sidor = int(m.group(1))
    r = _kor([pdftotext, '-layout', '-enc', 'UTF-8', str(original), str(katalog / 'text.txt')], timeout=180)
    text = (katalog / 'text.txt').read_text('utf-8', errors='replace') if (katalog / 'text.txt').exists() else ''
    per_sida = text.split('\f') if text else []
    tomma = [i + 1 for i, s in enumerate(per_sida[:sidor or len(per_sida)]) if len(s.strip()) < 20]
    (katalog / 'sidtext.json').write_text(json.dumps(per_sida, ensure_ascii=False), 'utf-8')
    info = {'sidor': sidor, 'text': bool(text.strip()),
            'stod': 'textlager per sida; sidor kan öppnas som bild för visuell läsning (tabeller, diagram, layout)'}
    if tomma:
        info['begransning'] = ('Sidor utan läsbart textlager (troligen bild eller skanning): %s. De måste läsas '
                               'visuellt; innehållet är annars okänt.' % _intervall(tomma))
    return info


def _intervall(nr: list) -> str:
    delar, start, fore = [], None, None
    for n in nr:
        if start is None:
            start = fore = n
        elif n == fore + 1:
            fore = n
        else:
            delar.append(str(start) if start == fore else '%d–%d' % (start, fore))
            start = fore = n
    if start is not None:
        delar.append(str(start) if start == fore else '%d–%d' % (start, fore))
    return ', '.join(delar)


def pdf_sidbild(original: Path, katalog: Path, sida: int) -> Path | None:
    mal = katalog / ('sida-%d.png' % sida)
    if mal.exists():
        return mal
    pdftoppm = shutil.which('pdftoppm') or '/opt/homebrew/bin/pdftoppm'
    r = _kor([pdftoppm, '-png', '-r', '110', '-f', str(sida), '-l', str(sida), '-singlefile', str(original),
              str(katalog / ('sida-%d' % sida))], timeout=120)
    if r.returncode != 0 or not mal.exists():
        return None
    if mal.stat().st_size > MODELL_BILD_MAX_BYTE:
        sips = shutil.which('sips') or '/usr/bin/sips'
        jpg = katalog / ('sida-%d.jpg' % sida)
        _kor([sips, '-s', 'format', 'jpeg', '-Z', str(MODELL_BILD_MAX_SIDA), str(mal), '--out', str(jpg)])
        if jpg.exists():
            return jpg
    return mal


def _dokument(original: Path, mime: str, katalog: Path) -> dict:
    mal = katalog / 'text.txt'
    if mime.endswith('presentationml.presentation') or mime.endswith('spreadsheetml.sheet'):
        text = _office_xml_text(original, 'ppt/slides/' if 'presentation' in mime else 'xl/sharedStrings')
        mal.write_text(text, 'utf-8')
        return {'text': bool(text.strip()), 'stod': 'text ur dokumentets XML (layout, bilder och diagram ingår inte)',
                'begransning': 'Bilder, diagram och layout i dokumentet har inte setts.'}
    textutil = shutil.which('textutil') or '/usr/bin/textutil'
    r = _kor([textutil, '-convert', 'txt', '-output', str(mal), str(original)], timeout=120)
    if r.returncode == 0 and mal.exists():
        return {'text': bool(mal.read_text('utf-8', errors='replace').strip()),
                'stod': 'text ur dokumentet (macOS textutil)',
                'begransning': 'Inbäddade bilder, diagram och layout har inte setts.'}
    return {'text': False, 'begransning': 'Dokumentet kunde inte läsas på den här datorn.'}


def _office_xml_text(original: Path, prefix: str) -> str:
    delar = []
    with zipfile.ZipFile(original) as z:
        storlek = {i.filename: i.file_size for i in z.infolist()}
        namn = sorted(n for n in z.namelist() if n.startswith(prefix) and n.endswith('.xml'))
        summa = 0
        for n in namn[:400]:
            summa += storlek.get(n, 0)
            if storlek.get(n, 0) > 20_000_000 or summa > 80_000_000:
                delar.append('[%s hoppades över: för stor]' % n)
                continue
            try:
                rot = ElementTree.fromstring(z.read(n))
            except ElementTree.ParseError:
                continue
            texter = [e.text for e in rot.iter() if e.tag.endswith('}t') and e.text]
            if texter:
                delar.append('[%s]\n%s' % (n.rsplit('/', 1)[-1], ' '.join(texter)))
    return '\n\n'.join(delar)


def text_for(katalog: Path, max_tecken: int = TEXT_MAX_TECKEN_I_TUR, sidor: tuple | None = None) -> tuple:
    """(text, avkapad) ur den härledda läsformen."""
    if sidor and (katalog / 'sidtext.json').exists():
        per_sida = json.loads((katalog / 'sidtext.json').read_text('utf-8'))
        fran, till = sidor
        text = '\n'.join('--- sida %d ---\n%s' % (i + 1, per_sida[i]) for i in range(fran - 1, min(till, len(per_sida))))
    elif (katalog / 'text.txt').exists():
        text = (katalog / 'text.txt').read_text('utf-8', errors='replace')
    else:
        return '', False
    if len(text) > max_tecken:
        return text[:max_tecken], True
    return text, False
