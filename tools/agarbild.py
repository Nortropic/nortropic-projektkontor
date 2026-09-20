"""A dated, private Swedish reading surface. No source access or execution."""

import datetime as dt
from fractions import Fraction
import html
import json
import os
from pathlib import Path
import re
import stat
import sys


class ValidationError(ValueError):
    """Input does not satisfy the report contract (no private error values)."""


def _require(condition):
    if not condition:
        raise ValidationError("Ogiltigt rapportunderlag.")


def _object(value, keys):
    _require(type(value) is dict and set(value) == set(keys.split()))


def _text(value):
    _require(type(value) is str and bool(value.strip()))
    # Unpaired surrogates are legal JSON escapes but cannot produce UTF-8.
    try:
        value.encode("utf-8")
    except UnicodeError:
        raise ValidationError("Ogiltigt rapportunderlag.") from None


def _texts(value, keys):
    for key in keys.split():
        _text(value[key])


def _list(value, nonempty=False):
    _require(type(value) is list and (not nonempty or bool(value)))


# Calendar ISO8601 with explicit timezone; basic and extended forms supported.
_DATE = re.compile(
    r"(?P<base>[0-9]{4}(?:-[0-9]{2}-[0-9]{2}|[0-9]{4})[Tt]"
    r"[0-9]{2}(?::[0-9]{2}(?::[0-9]{2})?|[0-9]{2}(?:[0-9]{2})?))"
    r"(?P<fraction>[.,][0-9]+)?(?P<zone>Z|[+-][0-9]{2}(?::?[0-9]{2})?)"
)


def _date(value):
    _text(value)
    match = _DATE.fullmatch(value)
    _require(match is not None)
    zone = match["zone"]
    if zone != "Z":
        offset = zone[1:].replace(":", "")
        _require(int(offset[:2]) < 24 and (len(offset) == 2 or int(offset[2:]) < 60))
    fraction = match["fraction"]
    # Fractional seconds only: do not misread fractional ISO minutes as seconds.
    time_part = match["base"].upper().split("T")[1].replace(":", "")
    _require(fraction is None or len(time_part) == 6)
    try:
        parsed = dt.datetime.fromisoformat(match["base"] + zone.replace("Z", "+00:00"))
        _require(parsed.utcoffset() is not None)
        utc = parsed.astimezone(dt.timezone.utc)
        seconds = utc.toordinal() * 86400 + utc.hour * 3600 + utc.minute * 60 + utc.second
        # Retain all supplied decimal precision, including sub-microsecond times.
        return Fraction(seconds) + (Fraction("0." + fraction[1:]) if fraction else 0)
    except (ValueError, OverflowError):
        raise ValidationError("Ogiltigt rapportunderlag.") from None


STATES = {
    "accepted": "Accepterat", "running": "Pågående enligt underlaget",
    "waiting": "Teknisk väntan", "finished": "Avslutat enligt underlaget",
    "superseded": "Ersatt — historik", "unknown": "Okänt läge",
    "proposed": "Föreslaget — inte accepterat",
}
AUTHORITIES = {
    "accepted": "Accepterad enligt underlaget",
    "proposed": "Föreslagen — inte accepterad",
    "none": "Ingen befogenhet angiven som given",
    "unknown": "Befogenhet okänd",
}
DECISIONS = {
    "yes": "Ett ägarbeslut behövs enligt underlaget",
    "no": "Inget ägarbeslut behövs enligt underlaget",
    "unknown": "Behovet av ägarbeslut är okänt",
}


def _enum(value, options):
    _require(type(value) is str and value in options)


def validate(data):
    """Validate without reading sources, changing data or consulting a clock."""
    _object(data, "schema generated_at title summary scope capabilities work next_action owner_decision issues evidence")
    _require(type(data["schema"]) is int and data["schema"] == 1)
    _texts(data, "title summary scope")
    generated = _date(data["generated_at"])
    _list(data["evidence"], nonempty=True)
    ids = set()

    def observation(value):
        if value is not None:
            _require(_date(value) <= generated)

    for item in data["evidence"]:
        _object(item, "id title kind observed_at revision locator sha256 text")
        _texts(item, "id title kind revision locator text")
        _require(re.fullmatch(r"[A-Za-z0-9-]+", item["id"]) is not None)
        _require(item["id"] not in ids)
        ids.add(item["id"])
        observation(item["observed_at"])
        digest = item["sha256"]
        _require(digest is None or (type(digest) is str and re.fullmatch(r"[0-9a-f]{64}", digest) is not None))

    def references(value):
        _list(value, nonempty=True)
        _require(all(type(ref) is str for ref in value))
        _require(len(value) == len(set(value)) and all(ref in ids for ref in value))

    _list(data["capabilities"])
    for item in data["capabilities"]:
        _object(item, "title use limits delivery availability evidence")
        _texts(item, "title use limits delivery availability")
        references(item["evidence"])
    _list(data["work"])
    for item in data["work"]:
        _object(item, "title state text observed_at evidence")
        _texts(item, "title text")
        _enum(item["state"], STATES)
        observation(item["observed_at"])
        references(item["evidence"])
    item = data["next_action"]
    _object(item, "text owner authority evidence")
    _texts(item, "text owner")
    _enum(item["authority"], AUTHORITIES)
    references(item["evidence"])
    item = data["owner_decision"]
    _object(item, "needed question reason evidence")
    _enum(item["needed"], DECISIONS)
    _texts(item, "question reason")
    references(item["evidence"])
    _list(data["issues"])
    for item in data["issues"]:
        _object(item, "text evidence")
        _text(item["text"])
        references(item["evidence"])


_CSS = """
:root { color-scheme: light; --ink:#243432; --muted:#526460; --line:#cdd5ce;
  --paper:#f5f4ee; --card:#fffefa; --accent:#285852; }
* { box-sizing:border-box; }
body { margin:0; background:var(--paper); color:var(--ink);
  font:1.05rem/1.65 system-ui,sans-serif; }
main { max-width:76rem; margin:auto; padding:3.5rem 2rem; }
header { max-width:56rem; margin-bottom:2.5rem; }
h1,h2,h3,p { margin-top:0; }
h1 { font:500 clamp(2.2rem,5vw,3.9rem)/1.12 Georgia,serif; margin-bottom:1.2rem; }
h2 { font:500 1.8rem/1.25 Georgia,serif; margin-bottom:1.2rem; }
h3 { font-size:1.12rem; line-height:1.4; }
.kicker { text-transform:uppercase; letter-spacing:.12em; font-size:.78rem; font-weight:700; }
.lead { font-size:1.2rem; }
.meta { color:var(--muted); font-size:.9rem; }
section { margin:2.5rem 0; }
.grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(min(100%,22rem),1fr)); gap:1.2rem; }
.card { background:var(--card); border:1px solid var(--line); border-radius:.65rem; padding:1.5rem; }
.notice { border-left:3px solid var(--accent); padding:1rem 1.3rem; background:#e9eeea; }
dl { margin:1rem 0; }
dt { font-size:.8rem; letter-spacing:.04em; font-weight:700; margin-top:.85rem; }
dd { margin:0; }
.copy { white-space:pre-wrap; overflow-wrap:anywhere; }
a { color:var(--accent); text-underline-offset:.2em; }
a:focus-visible,summary:focus-visible { outline:3px solid var(--accent); outline-offset:4px; }
summary { cursor:pointer; font-weight:600; padding:.65rem 0; overflow-wrap:anywhere; }
details { border-top:1px solid var(--line); padding:.4rem 0; }
details:target { outline:2px solid var(--accent); outline-offset:.4rem; }
.evidence-body { padding:.8rem 1rem 1rem; }
.refs { font-size:.9rem; margin-bottom:0; }
.work-item { border-top:1px solid var(--line); padding:1.3rem 0 .3rem; }
.state { font-size:.82rem; font-weight:700; color:var(--muted); }
footer { border-top:1px solid var(--line); padding-top:1.5rem; color:var(--muted); }
@media(max-width:40rem) { main { padding:2rem 1.1rem; } .card { padding:1.1rem; } }
@media print { body { background:white; } main { padding:0; } .card { break-inside:avoid; } }
"""


def render(data):
    """Return standalone UTF-8-compatible HTML; no IO, time lookup or mutation."""
    validate(data)
    esc = html.escape
    generated = _date(data["generated_at"])
    # Reference labels contain no supplied technical identifiers or source URLs.
    numbers = {item["id"]: i for i, item in enumerate(data["evidence"], 1)}

    def refs(item):
        links = [f'<a href="#evidence-{numbers[ref]}">Underlag {numbers[ref]}</a>'
                 for ref in item["evidence"]]
        return '<p class="refs">Underlag: ' + ' · '.join(links) + '</p>'

    def paragraph(value, cls="copy"):
        return f'<p class="{cls}">{esc(value)}</p>'

    def field(label, value):
        return f'<dt>{label}</dt><dd class="copy">{esc(value)}</dd>'

    def observed(value):
        if value is None:
            return '<p class="meta">Observerad: observation saknas. Ålder okänd; detta visar inte att inget arbete pågår.</p>'
        age = generated - _date(value)
        days, seconds = divmod(int(age), 86400)
        age_text = f"{days} dygn, {seconds // 3600} timmar, {(seconds % 3600) // 60} minuter, {seconds % 60} sekunder"
        remainder = age - int(age)
        if remainder:
            micros = remainder * 1000000
            age_text += (f" och {int(micros)} mikrosekunder" if micros.denominator == 1
                         else f" och {remainder} sekund")
        return (f'<p class="meta">Observerad: <time datetime="{esc(value, quote=True)}">{esc(value)}</time>'
                f' · Ålder vid framställning: {age_text}.</p>')

    def work_card(item):
        return (f'<article class="work-item"><p class="state">{STATES[item["state"]]}</p>'
                f'<h3 class="copy">{esc(item["title"])}</h3>' + paragraph(item["text"])
                + observed(item["observed_at"]) + refs(item) + '</article>')

    out = ['<!doctype html><html lang="sv"><head><meta charset="utf-8">',
           '<meta name="viewport" content="width=device-width, initial-scale=1">',
           '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; style-src \'unsafe-inline\'; base-uri \'none\'; form-action \'none\'">',
           f'<title>{esc(data["title"])}</title><style>{_CSS}</style></head><body><main>',
           '<header><p class="kicker">Privat ägarbild · daterat underlag</p>',
           f'<h1 class="copy">{esc(data["title"])}</h1>', paragraph(data["summary"], "lead copy"),
           f'<p class="meta">Framställd: <time datetime="{esc(data["generated_at"], quote=True)}">{esc(data["generated_at"])}</time></p>',
           '<div class="notice"><p>Detta är en daterad projektion av det tillförda underlaget, inte en livebild. '
           'Ålder räknas vid framställning, inte när filen öppnas. Ingen bevakning eller källäsning sker här.</p>',
           '<p class="copy">Omfattning: ' + esc(data["scope"]) + '</p></div></header>',
           '<section aria-labelledby="capabilities"><h2 id="capabilities">Det här kan användas</h2><div class="grid">']
    for item in data["capabilities"]:
        out += [f'<article class="card"><h3 class="copy">{esc(item["title"])}</h3><dl>',
                field("Användning", item["use"]), field("Begränsningar", item["limits"]),
                field("Leverans", item["delivery"]), field("Aktuell tillgänglighet enligt underlaget", item["availability"]),
                '</dl>', refs(item), '</article>']
    if not data["capabilities"]:
        out.append(paragraph("Inga förmågor redovisade. Det fastställer inte vad som finns eller saknas."))
    out += ['</div></section><section aria-labelledby="work"><h2 id="work">Senast observerade arbete</h2>',
            '<p class="meta">Observationerna kan vara gamla eller saknas. Teknisk väntan avgör inte om ägaren behöver fatta beslut.</p>']
    current = [item for item in data["work"] if item["state"] != "superseded"]
    # Known observations, newest first; missing observations remain visible below.
    current.sort(key=lambda item: (item["observed_at"] is not None,
                                  _date(item["observed_at"]) if item["observed_at"] else -1), reverse=True)
    out.extend(work_card(item) for item in current)
    if not current:
        out.append(paragraph("Inget arbete redovisat utanför historiken. Det visar inte att inget arbete pågår."))
    out += ['</section><div class="grid"><section class="card" aria-labelledby="next"><h2 id="next">Nästa motiverade handling</h2>']
    item = data["next_action"]
    out += [paragraph(item["text"]), '<dl>', field("Ansvarig", item["owner"]),
            field("Befogenhet", AUTHORITIES[item["authority"]]), '</dl>', refs(item), '</section>',
            '<section class="card" aria-labelledby="decision"><h2 id="decision">Ägarens beslut</h2>']
    item = data["owner_decision"]
    out += [paragraph(DECISIONS[item["needed"]], "lead"), '<dl>', field("Fråga", item["question"]),
            field("Skäl", item["reason"]), '</dl>', refs(item), '</section></div>',
            '<section aria-labelledby="issues"><h2 id="issues">Osäkerheter och motstridiga uppgifter</h2>',
            '<p class="meta">Tillförda uppgifter visas utan att motsägelser löses eller det mest positiva beskedet väljs. Sakgranskning krävs.</p>']
    for item in data["issues"]:
        out += ['<article class="notice">', paragraph(item["text"]), refs(item), '</article>']
    if not data["issues"]:
        out.append(paragraph("Inga osäkerheter redovisade av författaren. Det bevisar inte att underlaget är fullständigt eller samstämmigt."))
    history = [item for item in data["work"] if item["state"] == "superseded"]
    out.append('</section>')
    if history:
        out += ['<section aria-labelledby="history"><h2 id="history">Historik · ersatt arbete</h2>',
                '<p>Tidigare ersatt arbete räknas inte som aktivt arbete eller som ett hinder för ägaren. Historiska väntelägen ska inte återupptas genom denna rapport.</p>']
        out.extend(work_card(item) for item in history)
        out.append('</section>')
    out += ['<section aria-labelledby="evidence"><h2 id="evidence">Underlag och spårbarhet</h2>',
            '<p class="meta">Källplatser visas som text och öppnas inte av rapporten. Revisioner och hashvärden återges utan kontroll eller uppdatering.</p>']
    for i, item in enumerate(data["evidence"], 1):
        out += [f'<details id="evidence-{i}"><summary>Underlag {i} · {esc(item["title"])}</summary><div class="evidence-body">',
                observed(item["observed_at"]), '<dl>', field("Identifierare", item["id"]),
                field("Typ", item["kind"]), field("Revision", item["revision"]),
                field("Källplats (endast text)", item["locator"]),
                field("SHA-256 (ej verifierad)", item["sha256"] if item["sha256"] is not None else "Saknas"),
                '</dl>', paragraph(item["text"]), '</div></details>']
    out += ['</section><footer><p>Värden ansvarar för källbunden sakgranskning, urval och bedömning av befogenhet. '
            'Renderingen autentiserar inte underlaget. Giltigt format, statusord eller hashvärden bevisar varken riktighet, leverans eller tillstånd.</p>',
            '<p>Rapporten ger ingen ny befogenhet och startar inget arbete. Separat granskning och verifierad skyddad leverans hanteras av befintlig Runtime. '
            'Rapportens egen utskrift är inte leveransbevis.</p></footer></main></body></html>']
    return '\n'.join(out)


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        _require(key not in result)
        result[key] = value
    return result


def _nonfinite(_value):
    raise ValidationError("Ogiltigt rapportunderlag.")


def _checked_path(value):
    """Inspect every supplied component, including those preceding '..'."""
    # Path normalizes trailing '/.' and '/', which denote a directory, not a file.
    _require(bool(os.fspath(value)) and not os.fspath(value).endswith(("/", "/.")))
    path = Path(value)
    if not path.is_absolute():
        path = Path.cwd() / path
    current = Path(path.anchor)
    parts = path.parts[1:]
    _require(bool(parts))
    for i, part in enumerate(parts):
        current = current / part
        try:
            info = current.lstat()
        except FileNotFoundError:
            _require(i == len(parts) - 1)
            return current, None
        _require(not stat.S_ISLNK(info.st_mode))
        if i != len(parts) - 1:
            _require(stat.S_ISDIR(info.st_mode))
    return current, info


def _read_input(value):
    path, before = _checked_path(value)
    _require(before is not None and stat.S_ISREG(before.st_mode))
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, "rb") as stream:
        actual = os.fstat(stream.fileno())
        _require(stat.S_ISREG(actual.st_mode))
        _require((before.st_dev, before.st_ino) == (actual.st_dev, actual.st_ino))
        raw = stream.read()
    return json.loads(raw.decode("utf-8"), object_pairs_hook=_pairs, parse_constant=_nonfinite)


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    try:
        _require(len(args) == 2)
        document = render(_read_input(args[0])).encode("utf-8")
        output, existing = _checked_path(args[1])
        # All existing objects are rejected, including hardlinks and the input itself.
        _require(existing is None)
        fd = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, "wb") as stream:
            _require(stat.S_ISREG(os.fstat(stream.fileno()).st_mode))
            os.fchmod(stream.fileno(), 0o600)
            stream.write(document)
        return 0
    except (OSError, ValueError, TypeError, OverflowError, RecursionError):
        print("Kunde inte skapa ägarbilden. Kontrollera underlag och nya lokala filsökvägar.", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
