"""Aquarium v0's scene and its renderer: the work world a display-safe projection is rendered into.

SCEN is the static Swedish page: one continuous workshop floor seen from above with persistent places, Arkivet (delivered
volumes), Verkstaden (a board of tasks that do not work and three benches), Granskningen (the review desk), Utkiken (the
watch at the big window), Ägarens bord (letters and a mark only when something waits for the owner), a toned-down
Maskinrummet (the technical base) and a toned-down frosted room for interactive work that is not observed. Every shown
value is a {{AQ_...}} placeholder or an <!--AQ:LISTA:...--> list slot that `render` fills with escaped text from a schema 2
projection (tools/aquarium.py); every state is a class that `render` sets through a placeholder. A bench figure and a
review figure follow the class aq-figur, and the watch figure follows the class aq-kor: `render` sets aq-figur only for
work whose executor the engine reading itself evidences and aq-kor only while the watch reading shows a round running, so
configured staffing never becomes an observed figure and an executor that is not evidenced is written out as `ej belagd`.
A place carries aq-otillganglig when its source could not be read, and its fog says that the state is unknown, not empty.
SCEN also holds the window's two marks, both hidden until their class is set: a `nytt läge` tag on each bench, on the
review desk and on each board card, shown with the class aq-nytt-lage (on a bench and the review desk the tag, card and
sign arrive once in the fresh look; a board card is a task that does not work and never moves), and the window's footer
line, shown with the body class aq-fonsterlage; `render` sets both only in the window mode.
PROVDATA is marked once for the whole page (body class aq-provdata). The page starts in the stale look (class
aq-inaktuell: the world stands still and fades, figures become outlines marked as last known, a banner says that this does
not mean work has ended); only SKRIPT, placed once at <!--AQ:SKRIPT--> and pinned by its SHA-256 in the page's
Content-Security-Policy, compares the reading's time with the viewer's clock and switches to the fresh look while the
reading is younger than the smallest source limit. Decorative motion (daylight, plants) runs only in the fresh look and
never with reduced motion. Each place links to a panel (:target) with its rows and its source line.

`render(projection, jamforelse)` with a comparison of the window's two latest readings (tools/aquarium_fonster.py)
renders the same scene as the window's page instead: FONSTERSKRIPT beside SKRIPT, both pinned by fonster_csp(), the body
class aq-fonsterlage, the mark aq-nytt-lage on every shown place whose task the comparison names, one added row per such
task and one last row in the Verkstaden panel that says what the comparison rests on. A mark says only that the observed
state differs from the previous reading; it never says when, how, by which route or by whom it changed, and it never
describes a handover. Called with one argument, or with None as the second, `render` returns exactly the snapshot.

`render` only fills SCEN and never changes it, and SCEN, SKRIPT and FONSTERSKRIPT are unchanged, byte for byte.
`render` is pure: no file, clock, process or network, the inputs are never mutated and the same inputs give the same
page; the modules it uses, ZONE and the pinned digests are created at import. The command reads one projection file and
writes one new page, and it collects, serves, starts and changes nothing.
"""
import base64
from datetime import datetime
import hashlib
import html
import json
import os
from pathlib import Path
import re
import stat
import sys
from zoneinfo import ZoneInfo

SCEN = '''<!DOCTYPE html>
<html lang="sv"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="Content-Security-Policy" content="{{AQ_CSP}}"><meta name="color-scheme" content="light"><title>Nortropic · verkstaden</title><style>:root{--ram:#17211f;--black:#2d2a25;--dampad:#6f695e;--barnsten:#e6a445;--gron:#6fae80;--claude:#c97a5d;--codex:#587b9c;--okand:#9b9990;--hy:#f0d4bf;--har:#4b3b33;--prov:#ffd9a0}
*{box-sizing:border-box}html,body{margin:0;height:100%;background:var(--ram);font-family:-apple-system,"SF Pro Text","Helvetica Neue",Arial,sans-serif;color:#eef3f1}
.aq-scen{display:block;width:100vw;height:100vh}
.aq-kontor{font-size:13px;font-weight:700;letter-spacing:3px;fill:#9fb8b3}.aq-rubrik{font-size:20px;font-weight:600;fill:#f2f6f4}
.aq-observerat{font-size:14px;fill:#dfe9e6}.aq-tackning{font-size:12px;fill:#9fb8b3;text-decoration:underline}.aq-fot-text{font-size:12px;fill:#9fb8b3}
.aq-skal{fill:#f1ebdf}.aq-vagg{fill:#e5dcc9}.aq-fonster{stroke:#b5ccd3;stroke-width:1.5}.aq-post{stroke:#f6f3ec;stroke-width:3}.aq-karm{fill:#d8cdb7}.aq-trad{fill:#9db8a2;opacity:.8}
.aq-innervagg{fill:#ddd3c0}.aq-innervagg-front{fill:#e8e0cf}.aq-glas{fill:#dde8ea;opacity:.8}.aq-dorr{fill:#cdbb98}
.aq-dagsljus path{fill:#fff8e3;opacity:.3}.aq-dagsljus{opacity:0}
.aq-matta{opacity:.85}.aq-matta-ark{fill:#dfe5d8}.aq-matta-gr{fill:#dde3e6}.aq-matta-utk{fill:#efe3cb}.aq-matta-bord{fill:#eddbd1}.aq-maskingolv{fill:#e7e4dd}
.aq-halvvagg{fill:#e2d9c7}
.aq-bord-topp{fill:#e7d7b8}.aq-bord-front{fill:#c8b089}.aq-bord-valnot{fill:#c39a73}.aq-bord-valnot-front{fill:#a17a55}.aq-disk{fill:#e3ddd2}.aq-disk-front{fill:#c9c1b2}
.aq-fot{fill:#8d938f}.aq-skarm{fill:#34403d}.aq-skarm-rader rect{fill:#4c5a56}.aq-tangent{fill:#f5f2eb;stroke:#d8cfbd}
.aq-lampsken{fill:url(#aq-sken);opacity:0}.aq-lampfot{fill:#8a918d}.aq-lamparm{stroke:#8a918d;stroke-width:3;stroke-linecap:round}.aq-lamphuvud{fill:#9aa19d}
.aq-sits{fill:#6f7e7a}.aq-rygg{fill:none;stroke:#566460;stroke-width:6;stroke-linecap:round}
.aq-kruka{fill:#d8c7ad}.aq-krukskugga{fill:#00000014}.aq-blad ellipse{fill:#7fa287}.aq-blad .aq-blad-ljus{fill:#9bbb9f}
.aq-bokhylla{fill:#c9ab80}.aq-hyllplan{fill:#ad8e62}.aq-hyllnot{font-size:11px;fill:#a58f6a;font-style:italic}.aq-fler{font-size:12px;font-weight:600;fill:#8a7552}
.aq-bok{fill:#fbf8f0;stroke:#dcd3c2}.aq-bokrygg{stroke:#dcd3c2}.aq-papper{fill:#fbf8f0;stroke:#ded6c5}.aq-black{fill:#c9c2b3}
.aq-vol-0 rect{fill:#b9a27b}.aq-vol-1 rect{fill:#98ad9c}.aq-vol-2 rect{fill:#b39c96}.aq-vol-3 rect{fill:#a3b3c0}.aq-vol-4 rect{fill:#bdb892}.aq-vol-5 rect{fill:#98a7ae}
.aq-vol.aq-av{display:none}.aq-vol.aq-ny rect{stroke:#fff5d6;stroke-width:1.6}
.aq-tavla{fill:#b7996b}.aq-kork{fill:#d9c5a0}.aq-tavla-rubrik{font-size:11px;font-weight:700;letter-spacing:1.2px;fill:#6a5738}.aq-tavla-not{font-size:11px;fill:#6a5738}
.aq-park rect{fill:#e9e4d8;stroke:#c7bfae}.aq-park text{font-size:10px;fill:#4f4738}.aq-park .aq-nal{fill:#a89c86;stroke:none}.aq-park.aq-av{display:none}
.aq-park.aq-titel-saknas rect{stroke:#9c8a6a;stroke-dasharray:4 3}
.aq-arbetskort rect{fill:#fffdf6;stroke:#d9cfbb}.aq-arbetskort .aq-nal{fill:#c96f5b;stroke:none}.aq-nal{fill:#c96f5b}
.aq-korg{fill:#e4d8c2;stroke:#cdbd9f}.aq-korg-text{font-size:10px;fill:#8f836d}
.aq-lupglas{fill:#ffffff55;stroke:#6f7773;stroke-width:3}.aq-lupskaft{stroke:#6f7773;stroke-width:4;stroke-linecap:round}
.aq-rapportflagga{fill:#d9cfbb}.aq-kalender rect{fill:#fbf8f0;stroke:#d9cfbb}.aq-kalender .aq-kalender-topp{fill:#c9a36a}.aq-kalender text{font-size:13px;font-weight:700;fill:var(--black)}
.aq-lapp rect{fill:#f3e6c2;stroke:#dccba0;transform-box:fill-box;transform-origin:center;transform:rotate(-4deg)}.aq-lapp text{font-size:10px;fill:#6f603f}
.aq-platsskylt{font-size:11px;fill:#7d725f}
.aq-vaktljus-karna{fill:#b7b2a6}.aq-vaktljus-sken{fill:url(#aq-barnsten);opacity:0}
.aq-kuvert{fill:#fffaf0;stroke:#d9c9aa}.aq-kuvert-vik{fill:none;stroke:#d9c9aa}.aq-brev.aq-av{display:none}
.aq-marke{display:none}.aq-marke circle{fill:#e0875a}.aq-marke text{font-size:15px;font-weight:700;fill:#fff}
.aq-rack{fill:#a9b1ad}.aq-rackenhet{fill:#bcc3bf}.aq-tjanst-karna{fill:#8f9894}.aq-tjanst-sken{fill:url(#aq-gront);opacity:0}.aq-tjanstnamn{font-size:10px;fill:#7b8581}
.aq-skap rect{fill:#c8ceca}.aq-skap .aq-lada{fill:#d9dedb}.aq-kabel{fill:none;stroke:#b7bfbb;stroke-width:2.5}
.aq-maskinrummet .aq-zon{fill:#9d9486}.aq-maskinrummet .aq-zon-under{fill:#8f8778}
.aq-motesgolv{fill:#e9e5dc}.aq-frost-inre rect,.aq-frost-inre circle{fill:#d6d1c7}.aq-frostglas{fill:#f1eee6cc;stroke:#e2ddd2;stroke-width:3}.aq-frostpost{stroke:#e6e1d7;stroke-width:2.5}
.aq-dorrskylt rect{fill:#fffdf8;stroke:#e8e0d0}.aq-dorrskylt-a{font-size:11px;font-weight:700;letter-spacing:1.4px;fill:#7d7361}.aq-dorrskylt-b{font-size:10.5px;fill:#8a7f6b}
.aq-kaffemaskin{fill:#5d6563}.aq-mugg{fill:#f7f3ea;stroke:#cdbfa5}.aq-rundbord{fill:#d8c7a8}
.aq-person{display:none}.aq-person .aq-hy{fill:var(--hy)}.aq-person .aq-har{fill:var(--har)}
.aq-claude .aq-jacka{fill:var(--claude)}.aq-codex .aq-jacka{fill:var(--codex)}.aq-okand .aq-jacka{fill:var(--okand)}.aq-vakt .aq-jacka{fill:var(--okand)}
.aq-skylt{display:none}.aq-skylt rect{fill:#fffdf8;stroke:#e3d9c6}.aq-skylt-a{font-size:12px;font-weight:700;fill:var(--black)}.aq-skylt-b{font-size:11px;fill:#4f4a42}.aq-skylt-c{font-size:10.5px;fill:var(--dampad)}
.aq-arbetskort,.aq-lupp{display:none}
.aq-senast{display:none}.aq-senast rect{fill:#3a3934}.aq-senast text{font-size:10px;fill:#f2eee5;letter-spacing:.4px}
.aq-bank.aq-pagar .aq-arbetskort,.aq-bank.aq-pagar .aq-skylt{display:inline}.aq-bank.aq-pagar .aq-skarm{fill:#d4ebe5}.aq-bank.aq-pagar .aq-skarm-rader rect{fill:#9fc4bb}
.aq-bank.aq-figur .aq-person,.aq-gransk.aq-figur .aq-person{display:inline}.aq-bank.aq-figur .aq-stol,.aq-gransk.aq-figur .aq-stol{display:none}
.aq-gransk.aq-granskas .aq-arbetskort,.aq-gransk.aq-granskas .aq-skylt,.aq-gransk.aq-granskas .aq-lupp,.aq-gransk.aq-integreras .aq-arbetskort,.aq-gransk.aq-integreras .aq-skylt{display:inline}
.aq-vakt{display:none}.aq-utkiken.aq-kor .aq-vakt,.aq-utkiken.aq-kor .aq-vakt .aq-person,.aq-utkiken.aq-kor .aq-vakt .aq-skylt{display:inline}
.aq-utkiken.aq-kor>.aq-stol,.aq-utkiken.aq-kor .aq-platsskylt{display:none}
.aq-utkiken.aq-vantar .aq-rapportflagga,.aq-utkiken.aq-vantar .aq-vaktljus-karna{fill:var(--barnsten)}.aq-utkiken.aq-kor .aq-vaktljus-karna{fill:#9fd0bd}
.aq-bordet.aq-harbord .aq-marke{display:inline}.aq-bordet.aq-ofullstandig .aq-korg{stroke:#9c8a6a;stroke-dasharray:4 3}
.aq-maskinrummet.aq-igang .aq-tjanst-karna{fill:var(--gron)}.aq-maskinrummet.aq-delvis .aq-tjanst-karna{fill:var(--barnsten)}
.aq-dimma{display:none}.aq-otillganglig .aq-dimma{display:inline}.aq-dimma rect{fill:#f5f3eef0;stroke:#d8d4ca;stroke-dasharray:6 6}
.aq-dimma-a{font-size:14px;font-weight:700;fill:#5d584e}.aq-dimma-b{font-size:12px;fill:#6d675a}
.aq-zon{font-size:12px;font-weight:700;letter-spacing:2.2px;fill:#7d705a}.aq-zon-under{font-size:12px;fill:#6f6555}
.aq-lank{cursor:pointer}.aq-lank:focus{outline:none}.aq-lank:focus-visible .aq-plats{outline:2px solid #587b9c}
.aq-provband{display:none}.aq-provdata .aq-provband{display:inline}.aq-provband rect{fill:var(--prov)}.aq-provband text{font-size:13px;font-weight:700;fill:#5a3d10;letter-spacing:.6px}
.aq-banner{display:none}.aq-inaktuell .aq-banner{display:inline}.aq-banner rect{fill:#2b2a26f2}.aq-banner-a{font-size:14px;font-weight:700;fill:#ffe2b0}.aq-banner-b{font-size:13px;fill:#ece6d8}
.aq-farsk .aq-dagsljus{opacity:1;animation:aq-drift 70s ease-in-out infinite alternate}.aq-farsk .aq-gungar .aq-blad{transform-box:fill-box;transform-origin:50% 100%;animation:aq-gunga 9s ease-in-out infinite alternate}
.aq-farsk .aq-bank.aq-pagar .aq-lampsken,.aq-farsk .aq-gransk.aq-granskas .aq-lampsken{opacity:.7}.aq-farsk .aq-bank.aq-pagar .aq-lamphuvud{fill:#ffe7a8}
.aq-farsk .aq-bordet.aq-harbord .aq-lampsken{opacity:.55}.aq-farsk .aq-utkiken.aq-vantar .aq-vaktljus-sken{opacity:.55}
.aq-farsk .aq-maskinrummet.aq-igang .aq-tjanst-sken{opacity:.45;animation:aq-andas 4s ease-in-out infinite}
.aq-farsk .aq-bank.aq-figur .aq-arm-v{animation:aq-skrivV 1s ease-in-out infinite}.aq-farsk .aq-bank.aq-figur .aq-arm-h{animation:aq-skrivH 1s ease-in-out infinite}
.aq-farsk .aq-gransk.aq-figur .aq-armar{animation:aq-las 5s ease-in-out infinite}.aq-farsk .aq-gransk.aq-granskas .aq-lupp{animation:aq-lupen 5s ease-in-out infinite}
.aq-farsk .aq-utkiken.aq-kor .aq-armar{animation:aq-las 7s ease-in-out infinite}
@keyframes aq-andas{0%,100%{opacity:.25}50%{opacity:.6}}@keyframes aq-drift{from{transform:translateX(-36px)}to{transform:translateX(36px)}}
@keyframes aq-gunga{from{transform:rotate(-2.5deg)}to{transform:rotate(2.5deg)}}
@keyframes aq-skrivV{0%,100%{transform:translateY(0)}50%{transform:translateY(-4px)}}@keyframes aq-skrivH{0%,100%{transform:translateY(-4px)}50%{transform:translateY(0)}}
@keyframes aq-las{0%,100%{transform:translateX(0)}50%{transform:translateX(7px)}}@keyframes aq-lupen{0%,100%{transform:translate(0,0)}50%{transform:translate(12px,5px)}}
@media (prefers-reduced-motion:reduce){*{animation:none!important}}
.aq-inaktuell .aq-varld{filter:url(#aq-stilla)}.aq-inaktuell .aq-varld *{animation:none!important}
.aq-inaktuell .aq-person .aq-jacka,.aq-inaktuell .aq-person .aq-hy,.aq-inaktuell .aq-person .aq-har{fill:#ffffff80;stroke:#5f594e;stroke-width:1.6;stroke-dasharray:4 3}
.aq-inaktuell .aq-senast{display:inline}
.aq-panel{display:none;position:fixed;left:24px;bottom:24px;max-width:560px;max-height:70vh;overflow:auto;background:#fbf8f1;color:#2d2a25;border-radius:14px;padding:16px 18px;
font-size:14px;line-height:1.45;box-shadow:0 10px 30px #0006}.aq-panel:target{display:block}
.aq-panel h2{margin:0 0 6px;font-size:16px}.aq-panel p{margin:6px 0}.aq-stang{float:right;color:#6f695e;font-size:13px}
.aq-lista{list-style:none;margin:8px 0;padding:0}.aq-lista li{padding:5px 0;border-top:1px solid #e8e1d3}.aq-etikett{display:inline-block;min-width:150px;margin-right:10px;font-weight:600;color:#5b5446}
.aq-kalla{font-size:12px;color:#6f695e}.aq-inaktuell-kalla{color:#8a5a22}.aq-otillganglig-kalla{color:#8a5a22}
.aq-nytt{display:none}.aq-nytt-lage .aq-nytt{display:inline}.aq-nytt rect,.aq-park .aq-nytt rect{fill:#fff1c9;stroke:#d79a3c;stroke-width:1.2;stroke-dasharray:none}.aq-nytt text,.aq-park .aq-nytt text{font-size:10px;font-weight:700;fill:#6b4610;letter-spacing:.3px}.aq-park .aq-nytt text{font-size:9px}
.aq-farsk .aq-bank.aq-nytt-lage .aq-arbetskort,.aq-farsk .aq-bank.aq-nytt-lage .aq-skylt,.aq-farsk .aq-bank.aq-nytt-lage .aq-nytt,.aq-farsk .aq-gransk.aq-nytt-lage .aq-arbetskort,.aq-farsk .aq-gransk.aq-nytt-lage .aq-skylt,.aq-farsk .aq-gransk.aq-nytt-lage .aq-nytt{animation:aq-anlander 1.8s ease-out 1 both}
@keyframes aq-anlander{from{opacity:.15;transform:translateY(-14px)}to{opacity:1;transform:none}}
.aq-fonsterrad{display:none}.aq-fonsterlage .aq-fonsterrad{display:inline}.aq-fonsterlage .aq-bildrad{display:none}
@media (max-width:700px){.aq-panel{left:12px;right:12px;bottom:12px;max-width:none}}</style></head>
<body class="aq-inaktuell {{AQ_BODY_CLASS}}" data-read-at="{{AQ_READ_AT}}" data-stale-after="{{AQ_STALE_AFTER}}">
<svg class="aq-scen" viewBox="0 0 1600 900" preserveAspectRatio="xMidYMid meet" role="group" aria-label="{{AQ_ARIA}}"><defs><linearGradient id="aq-himmel" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#bcd9e4"/><stop offset="1" stop-color="#e9f3f4"/></linearGradient><pattern id="aq-ek" width="240" height="26" patternUnits="userSpaceOnUse"><rect width="240" height="26" fill="#eadfc9"/><rect y="25" width="240" height="1" fill="#ddd0b6"/><rect x="0" y="0" width="1" height="26" fill="#e0d4bc"/><rect x="150" y="0" width="1" height="26" fill="#e0d4bc"/><rect x="40" y="9" width="60" height="1" fill="#e4d8c1"/></pattern><radialGradient id="aq-sken"><stop offset="0" stop-color="#fff0c4" stop-opacity=".9"/><stop offset="1" stop-color="#fff0c4" stop-opacity="0"/></radialGradient><radialGradient id="aq-barnsten"><stop offset="0" stop-color="#f1b24f" stop-opacity=".85"/><stop offset="1" stop-color="#f1b24f" stop-opacity="0"/></radialGradient><radialGradient id="aq-gront"><stop offset="0" stop-color="#78c08c" stop-opacity=".9"/><stop offset="1" stop-color="#78c08c" stop-opacity="0"/></radialGradient><filter id="aq-skugga" x="-20%" y="-20%" width="140%" height="160%"><feDropShadow dx="0" dy="5" stdDeviation="5" flood-color="#3b2f1f" flood-opacity=".16"/></filter><filter id="aq-skugga-s" x="-30%" y="-30%" width="160%" height="180%"><feDropShadow dx="0" dy="3" stdDeviation="2.5" flood-color="#3b2f1f" flood-opacity=".15"/></filter><filter id="aq-oskarp"><feGaussianBlur stdDeviation="5"/></filter><filter id="aq-stilla"><feColorMatrix type="saturate" values=".3"/></filter></defs>
<text x="60" y="40" class="aq-kontor">NORTROPIC · VERKSTADEN</text><text x="60" y="68" class="aq-rubrik">{{AQ_RUBRIK}}</text>
<text x="1540" y="40" class="aq-observerat" text-anchor="end">läst {{AQ_OBSERVERAT}} · <tspan id="aq-alder">{{AQ_ALDER_UTAN_SKRIPT}}</tspan></text>
<a href="#p-kallor" class="aq-lank"><text x="1250" y="40" class="aq-tackning" text-anchor="end">Här syns Runtimes körningar och kontorets register · interaktivt arbete syns inte · källor och tider</text></a>
<g class="aq-varld" transform="translate(0 8)">
<rect x="48" y="80" width="1504" height="768" rx="22" class="aq-skal"/>
<rect x="62" y="94" width="1476" height="740" rx="12" fill="url(#aq-ek)"/>
<rect x="62" y="94" width="1476" height="26" class="aq-vagg"/>
<rect x="150" y="96" width="210" height="22" rx="3" class="aq-fonster" fill="url(#aq-himmel)"/>
<line x1="202" y1="96" x2="202" y2="118" class="aq-post"/>
<line x1="254" y1="96" x2="254" y2="118" class="aq-post"/>
<line x1="306" y1="96" x2="306" y2="118" class="aq-post"/>
<line x1="358" y1="96" x2="358" y2="118" class="aq-post"/>
<rect x="146" y="117" width="218" height="4" rx="2" class="aq-karm"/>
<rect x="560" y="96" width="260" height="22" rx="3" class="aq-fonster" fill="url(#aq-himmel)"/>
<line x1="612" y1="96" x2="612" y2="118" class="aq-post"/>
<line x1="664" y1="96" x2="664" y2="118" class="aq-post"/>
<line x1="716" y1="96" x2="716" y2="118" class="aq-post"/>
<line x1="768" y1="96" x2="768" y2="118" class="aq-post"/>
<rect x="556" y="117" width="268" height="4" rx="2" class="aq-karm"/>
<rect x="1188" y="96" width="324" height="22" rx="3" class="aq-fonster" fill="url(#aq-himmel)"/>
<line x1="1240" y1="96" x2="1240" y2="118" class="aq-post"/>
<line x1="1292" y1="96" x2="1292" y2="118" class="aq-post"/>
<line x1="1344" y1="96" x2="1344" y2="118" class="aq-post"/>
<line x1="1396" y1="96" x2="1396" y2="118" class="aq-post"/>
<line x1="1448" y1="96" x2="1448" y2="118" class="aq-post"/>
<line x1="1500" y1="96" x2="1500" y2="118" class="aq-post"/>
<rect x="1184" y="117" width="332" height="4" rx="2" class="aq-karm"/>
<path d="M1190 114 q10 -10 22 0 q12 -14 26 0 q10 -8 20 0 q14 -12 28 0 q10 -9 22 0 q12 -13 26 0 q10 -8 20 0 q12 -12 26 0 q10 -9 22 0 q12 -13 26 0 q12 -10 24 0 q10 -8 20 0 l0 4 l-322 0 z" class="aq-trad"/>
<g class="aq-dagsljus"><path d="M150 120 L360 120 L318 330 L108 330 Z"/><path d="M560 120 L820 120 L780 360 L520 360 Z"/><path d="M1188 120 L1512 120 L1450 380 L1126 380 Z"/></g>
<rect x="80" y="250" width="304" height="232" rx="16" class="aq-matta aq-matta-ark"/>
<rect x="976" y="198" width="164" height="260" rx="16" class="aq-matta aq-matta-gr"/>
<rect x="1178" y="138" width="340" height="236" rx="16" class="aq-matta aq-matta-utk"/>
<rect x="1180" y="430" width="340" height="200" rx="16" class="aq-matta aq-matta-bord"/>
<rect x="410" y="640" width="740" height="188" rx="8" class="aq-maskingolv"/>
<rect x="392" y="94" width="12" height="344" class="aq-innervagg"/>
<rect x="392" y="500" width="12" height="334" class="aq-innervagg"/>
<rect x="1150" y="94" width="12" height="238" class="aq-innervagg"/>
<rect x="1150" y="404" width="12" height="430" class="aq-innervagg"/>
<rect x="62" y="501" width="238" height="10" class="aq-innervagg"/><rect x="62" y="511" width="238" height="12" class="aq-innervagg-front"/>
<rect x="1156" y="399" width="140" height="10" class="aq-innervagg"/><rect x="1156" y="409" width="140" height="12" class="aq-innervagg-front"/>
<rect x="1400" y="399" width="138" height="10" class="aq-innervagg"/><rect x="1400" y="409" width="138" height="12" class="aq-innervagg-front"/>
<rect x="1156" y="647" width="100" height="10" class="aq-innervagg"/><rect x="1156" y="657" width="100" height="12" class="aq-innervagg-front"/>
<rect x="1352" y="647" width="186" height="10" class="aq-innervagg"/><rect x="1352" y="657" width="186" height="12" class="aq-innervagg-front"/>
<rect x="410" y="628" width="740" height="8" class="aq-glas"/>
<rect x="1312" y="830" width="80" height="12" rx="4" class="aq-dorr"/>
<a href="#p-arkivet" class="aq-lank"><g class="aq-plats aq-arkivet {{AQ_ARKIV_STATUS}}"><title>Arkivet: levererat</title>
<rect x="78" y="122" width="306" height="84" rx="4" class="aq-bokhylla" filter="url(#aq-skugga)"/>
<rect x="84" y="160" width="294" height="4" class="aq-hyllplan"/>
<rect x="84" y="200" width="294" height="4" class="aq-hyllplan"/>
<g class="aq-vol aq-vol-0 {{AQ_VOL_1_CLASS}}"><rect x="92" y="128" width="14" height="30" rx="2"/><title>{{AQ_VOL_1_TITEL}}</title></g>
<g class="aq-vol aq-vol-1 {{AQ_VOL_2_CLASS}}"><rect x="110" y="131" width="14" height="27" rx="2"/><title>{{AQ_VOL_2_TITEL}}</title></g>
<g class="aq-vol aq-vol-2 {{AQ_VOL_3_CLASS}}"><rect x="128" y="134" width="14" height="24" rx="2"/><title>{{AQ_VOL_3_TITEL}}</title></g>
<g class="aq-vol aq-vol-3 {{AQ_VOL_4_CLASS}}"><rect x="146" y="128" width="14" height="30" rx="2"/><title>{{AQ_VOL_4_TITEL}}</title></g>
<g class="aq-vol aq-vol-4 {{AQ_VOL_5_CLASS}}"><rect x="164" y="131" width="14" height="27" rx="2"/><title>{{AQ_VOL_5_TITEL}}</title></g>
<g class="aq-vol aq-vol-5 {{AQ_VOL_6_CLASS}}"><rect x="182" y="134" width="14" height="24" rx="2"/><title>{{AQ_VOL_6_TITEL}}</title></g>
<g class="aq-vol aq-vol-0 {{AQ_VOL_7_CLASS}}"><rect x="200" y="128" width="14" height="30" rx="2"/><title>{{AQ_VOL_7_TITEL}}</title></g>
<g class="aq-vol aq-vol-1 {{AQ_VOL_8_CLASS}}"><rect x="218" y="131" width="14" height="27" rx="2"/><title>{{AQ_VOL_8_TITEL}}</title></g>
<g class="aq-vol aq-vol-2 {{AQ_VOL_9_CLASS}}"><rect x="236" y="134" width="14" height="24" rx="2"/><title>{{AQ_VOL_9_TITEL}}</title></g>
<g class="aq-vol aq-vol-3 {{AQ_VOL_10_CLASS}}"><rect x="254" y="128" width="14" height="30" rx="2"/><title>{{AQ_VOL_10_TITEL}}</title></g>
<g class="aq-vol aq-vol-4 {{AQ_VOL_11_CLASS}}"><rect x="272" y="131" width="14" height="27" rx="2"/><title>{{AQ_VOL_11_TITEL}}</title></g>
<g class="aq-vol aq-vol-5 {{AQ_VOL_12_CLASS}}"><rect x="290" y="134" width="14" height="24" rx="2"/><title>{{AQ_VOL_12_TITEL}}</title></g>
<g class="aq-vol aq-vol-0 {{AQ_VOL_13_CLASS}}"><rect x="308" y="128" width="14" height="30" rx="2"/><title>{{AQ_VOL_13_TITEL}}</title></g>
<g class="aq-vol aq-vol-1 {{AQ_VOL_14_CLASS}}"><rect x="326" y="131" width="14" height="27" rx="2"/><title>{{AQ_VOL_14_TITEL}}</title></g>
<g class="aq-vol aq-vol-2 {{AQ_VOL_15_CLASS}}"><rect x="344" y="134" width="14" height="24" rx="2"/><title>{{AQ_VOL_15_TITEL}}</title></g>
<g class="aq-vol aq-vol-3 {{AQ_VOL_16_CLASS}}"><rect x="362" y="128" width="14" height="30" rx="2"/><title>{{AQ_VOL_16_TITEL}}</title></g>
<text x="231" y="194" class="aq-fler" text-anchor="middle">{{AQ_ARKIV_FLER}}</text>
<text x="231" y="226" class="aq-hyllnot" text-anchor="middle">plats för fler leveranser</text>
<g filter="url(#aq-skugga)"><rect x="158" y="300" width="150" height="66" rx="6" class="aq-bord-topp"/><rect x="158" y="362" width="150" height="10" rx="4" class="aq-bord-front"/></g><g class="aq-lampa"><circle cx="286" cy="308" r="52" class="aq-lampsken"/><circle cx="302" cy="322" r="6" class="aq-lampfot"/><line x1="302" y1="322" x2="286" y2="306" class="aq-lamparm"/><circle cx="286" cy="306" r="8" class="aq-lamphuvud"/></g><g class="aq-stol" filter="url(#aq-skugga-s)"><rect x="181" y="388" width="34" height="30" rx="10" class="aq-sits"/><path d="M181 422 q17 12 34 0" class="aq-rygg"/></g><g class="aq-stol" filter="url(#aq-skugga-s)"><rect x="251" y="388" width="34" height="30" rx="10" class="aq-sits"/><path d="M251 422 q17 12 34 0" class="aq-rygg"/></g>
<rect x="178" y="314" width="52" height="34" rx="2" class="aq-bok"/><line x1="204" y1="314" x2="204" y2="348" class="aq-bokrygg"/>
<g class="aq-vaxt aq-gungar" transform="translate(362 474) scale(1.10)"><ellipse cx="0" cy="18" rx="17" ry="6" class="aq-krukskugga"/><rect x="-12" y="3" width="24" height="17" rx="6" class="aq-kruka"/><g class="aq-blad"><ellipse cx="-10" cy="-5" rx="7" ry="14" transform="rotate(-30 -10 -5)"/><ellipse cx="10" cy="-5" rx="7" ry="14" transform="rotate(30 10 -5)"/><ellipse cx="0" cy="-12" rx="7.5" ry="16"/><ellipse cx="-4" cy="-2" rx="5" ry="10" transform="rotate(-8 -4 -2)" class="aq-blad-ljus"/></g></g>
<text x="231" y="468" class="aq-zon" text-anchor="middle">ARKIVET</text><text x="231" y="485" class="aq-zon-under" text-anchor="middle">{{AQ_ARKIV_UNDER}}</text>
<g class="aq-dimma"><rect x="84" y="126" width="294" height="76" rx="12"/><text x="231" y="158" text-anchor="middle" class="aq-dimma-a">kunde inte läsas</text><text x="231" y="178" text-anchor="middle" class="aq-dimma-b">läget är okänt, inte tomt</text></g>
</g></a>
<a href="#p-verkstaden" class="aq-lank"><g class="aq-plats aq-verkstaden {{AQ_VERK_STATUS}}"><title>Verkstaden: arbete och uppdrag som inte arbetar</title>
<rect x="424" y="124" width="522" height="112" rx="6" class="aq-tavla" filter="url(#aq-skugga)"/><rect x="431" y="131" width="508" height="98" rx="4" class="aq-kork"/>
<text x="442" y="146" class="aq-tavla-rubrik">UPPDRAG SOM INTE ARBETAR</text><text x="928" y="146" class="aq-tavla-not" text-anchor="end">{{AQ_TAVLA_UNDER}}</text>
<g class="aq-park {{AQ_PARK_1_CLASS}}" filter="url(#aq-skugga-s)"><rect x="435" y="154" width="120" height="30" rx="3"/><circle cx="495" cy="159" r="3" class="aq-nal"/><text x="442" y="174">{{AQ_PARK_1_NAMN}}</text><g class="aq-nytt"><rect x="501" y="148" width="52" height="14" rx="7"/><text x="527" y="158.2" text-anchor="middle">nytt läge</text></g><title>{{AQ_PARK_1_TITEL}}</title></g>
<g class="aq-park {{AQ_PARK_2_CLASS}}" filter="url(#aq-skugga-s)"><rect x="561" y="154" width="120" height="30" rx="3"/><circle cx="621" cy="159" r="3" class="aq-nal"/><text x="568" y="174">{{AQ_PARK_2_NAMN}}</text><g class="aq-nytt"><rect x="627" y="148" width="52" height="14" rx="7"/><text x="653" y="158.2" text-anchor="middle">nytt läge</text></g><title>{{AQ_PARK_2_TITEL}}</title></g>
<g class="aq-park {{AQ_PARK_3_CLASS}}" filter="url(#aq-skugga-s)"><rect x="687" y="154" width="120" height="30" rx="3"/><circle cx="747" cy="159" r="3" class="aq-nal"/><text x="694" y="174">{{AQ_PARK_3_NAMN}}</text><g class="aq-nytt"><rect x="753" y="148" width="52" height="14" rx="7"/><text x="779" y="158.2" text-anchor="middle">nytt läge</text></g><title>{{AQ_PARK_3_TITEL}}</title></g>
<g class="aq-park {{AQ_PARK_4_CLASS}}" filter="url(#aq-skugga-s)"><rect x="813" y="154" width="120" height="30" rx="3"/><circle cx="873" cy="159" r="3" class="aq-nal"/><text x="820" y="174">{{AQ_PARK_4_NAMN}}</text><g class="aq-nytt"><rect x="879" y="148" width="52" height="14" rx="7"/><text x="905" y="158.2" text-anchor="middle">nytt läge</text></g><title>{{AQ_PARK_4_TITEL}}</title></g>
<g class="aq-park {{AQ_PARK_5_CLASS}}" filter="url(#aq-skugga-s)"><rect x="435" y="190" width="120" height="30" rx="3"/><circle cx="495" cy="195" r="3" class="aq-nal"/><text x="442" y="210">{{AQ_PARK_5_NAMN}}</text><g class="aq-nytt"><rect x="501" y="184" width="52" height="14" rx="7"/><text x="527" y="194.2" text-anchor="middle">nytt läge</text></g><title>{{AQ_PARK_5_TITEL}}</title></g>
<g class="aq-park {{AQ_PARK_6_CLASS}}" filter="url(#aq-skugga-s)"><rect x="561" y="190" width="120" height="30" rx="3"/><circle cx="621" cy="195" r="3" class="aq-nal"/><text x="568" y="210">{{AQ_PARK_6_NAMN}}</text><g class="aq-nytt"><rect x="627" y="184" width="52" height="14" rx="7"/><text x="653" y="194.2" text-anchor="middle">nytt läge</text></g><title>{{AQ_PARK_6_TITEL}}</title></g>
<g class="aq-park {{AQ_PARK_7_CLASS}}" filter="url(#aq-skugga-s)"><rect x="687" y="190" width="120" height="30" rx="3"/><circle cx="747" cy="195" r="3" class="aq-nal"/><text x="694" y="210">{{AQ_PARK_7_NAMN}}</text><g class="aq-nytt"><rect x="753" y="184" width="52" height="14" rx="7"/><text x="779" y="194.2" text-anchor="middle">nytt läge</text></g><title>{{AQ_PARK_7_TITEL}}</title></g>
<g class="aq-park {{AQ_PARK_8_CLASS}}" filter="url(#aq-skugga-s)"><rect x="813" y="190" width="120" height="30" rx="3"/><circle cx="873" cy="195" r="3" class="aq-nal"/><text x="820" y="210">{{AQ_PARK_8_NAMN}}</text><g class="aq-nytt"><rect x="879" y="184" width="52" height="14" rx="7"/><text x="905" y="194.2" text-anchor="middle">nytt läge</text></g><title>{{AQ_PARK_8_TITEL}}</title></g>
<text x="928" y="226" class="aq-tavla-not" text-anchor="end">{{AQ_PARK_FLER}}</text>
<g class="aq-bank {{AQ_BANK_1_CLASS}}"><title>{{AQ_BANK_1_TITEL}}</title>
<g filter="url(#aq-skugga)"><rect x="421" y="246" width="168" height="64" rx="6" class="aq-bord-topp"/><rect x="421" y="306" width="168" height="10" rx="4" class="aq-bord-front"/></g>
<rect x="508" y="286" width="10" height="8" class="aq-fot"/><rect x="483" y="252" width="60" height="34" rx="4" class="aq-skarm"/><g class="aq-skarm-rader"><rect x="491" y="260" width="34" height="3" rx="1"/><rect x="491" y="267" width="44" height="3" rx="1"/><rect x="491" y="274" width="26" height="3" rx="1"/></g>
<rect x="490" y="292" width="46" height="11" rx="3" class="aq-tangent"/>
<g class="aq-lampa"><circle cx="569" cy="258" r="52" class="aq-lampsken"/><circle cx="585" cy="272" r="6" class="aq-lampfot"/><line x1="585" y1="272" x2="569" y2="256" class="aq-lamparm"/><circle cx="569" cy="256" r="8" class="aq-lamphuvud"/></g>
<g class="aq-stol" filter="url(#aq-skugga-s)"><rect x="496" y="326" width="34" height="30" rx="10" class="aq-sits"/><path d="M496 360 q17 12 34 0" class="aq-rygg"/></g>
<g class="aq-arbetskort" filter="url(#aq-skugga-s)"><rect x="425" y="258" width="44" height="34" rx="3"/><circle cx="447" cy="263" r="3" class="aq-nal"/><rect x="432" y="272" width="30" height="3" rx="1" class="aq-black"/><rect x="432" y="279" width="24" height="3" rx="1" class="aq-black"/></g>
<g class="aq-person"><g class="aq-armar"><ellipse cx="496" cy="322" rx="6" ry="9" class="aq-jacka aq-arm-v"/><ellipse cx="530" cy="322" rx="6" ry="9" class="aq-jacka aq-arm-h"/></g><rect x="490" y="330" width="46" height="30" rx="15" class="aq-jacka aq-kropp"/><circle cx="513" cy="326" r="13" class="aq-hy aq-huvud"/><path d="M500 324 a13 13 0 0 1 26 0 v4 a13 9 0 0 1 -26 0 z" class="aq-har"/><g class="aq-senast"><rect x="443" y="282" width="140" height="20" rx="7"/><text x="513" y="296" text-anchor="middle">senast kända {{AQ_SENAST}}</text></g></g>
<g class="aq-skylt"><rect x="425" y="368" width="176" height="52" rx="10"/><text x="435" y="385" class="aq-skylt-a">{{AQ_BANK_1_NAMN}}</text><text x="435" y="400" class="aq-skylt-b">{{AQ_BANK_1_VEM}}</text><text x="435" y="414" class="aq-skylt-c">{{AQ_BANK_1_VAD}}</text></g>
<g class="aq-nytt"><rect x="533" y="354" width="66" height="17" rx="8.5"/><text x="566" y="366.5" text-anchor="middle">nytt läge</text></g>
</g>
<g class="aq-bank {{AQ_BANK_2_CLASS}}"><title>{{AQ_BANK_2_TITEL}}</title>
<g filter="url(#aq-skugga)"><rect x="601" y="246" width="168" height="64" rx="6" class="aq-bord-topp"/><rect x="601" y="306" width="168" height="10" rx="4" class="aq-bord-front"/></g>
<rect x="688" y="286" width="10" height="8" class="aq-fot"/><rect x="663" y="252" width="60" height="34" rx="4" class="aq-skarm"/><g class="aq-skarm-rader"><rect x="671" y="260" width="34" height="3" rx="1"/><rect x="671" y="267" width="44" height="3" rx="1"/><rect x="671" y="274" width="26" height="3" rx="1"/></g>
<rect x="670" y="292" width="46" height="11" rx="3" class="aq-tangent"/>
<g class="aq-lampa"><circle cx="749" cy="258" r="52" class="aq-lampsken"/><circle cx="765" cy="272" r="6" class="aq-lampfot"/><line x1="765" y1="272" x2="749" y2="256" class="aq-lamparm"/><circle cx="749" cy="256" r="8" class="aq-lamphuvud"/></g>
<g class="aq-stol" filter="url(#aq-skugga-s)"><rect x="676" y="326" width="34" height="30" rx="10" class="aq-sits"/><path d="M676 360 q17 12 34 0" class="aq-rygg"/></g>
<g class="aq-arbetskort" filter="url(#aq-skugga-s)"><rect x="605" y="258" width="44" height="34" rx="3"/><circle cx="627" cy="263" r="3" class="aq-nal"/><rect x="612" y="272" width="30" height="3" rx="1" class="aq-black"/><rect x="612" y="279" width="24" height="3" rx="1" class="aq-black"/></g>
<g class="aq-person"><g class="aq-armar"><ellipse cx="676" cy="322" rx="6" ry="9" class="aq-jacka aq-arm-v"/><ellipse cx="710" cy="322" rx="6" ry="9" class="aq-jacka aq-arm-h"/></g><rect x="670" y="330" width="46" height="30" rx="15" class="aq-jacka aq-kropp"/><circle cx="693" cy="326" r="13" class="aq-hy aq-huvud"/><path d="M680 324 a13 13 0 0 1 26 0 v4 a13 9 0 0 1 -26 0 z" class="aq-har"/><g class="aq-senast"><rect x="623" y="282" width="140" height="20" rx="7"/><text x="693" y="296" text-anchor="middle">senast kända {{AQ_SENAST}}</text></g></g>
<g class="aq-skylt"><rect x="605" y="368" width="176" height="52" rx="10"/><text x="615" y="385" class="aq-skylt-a">{{AQ_BANK_2_NAMN}}</text><text x="615" y="400" class="aq-skylt-b">{{AQ_BANK_2_VEM}}</text><text x="615" y="414" class="aq-skylt-c">{{AQ_BANK_2_VAD}}</text></g>
<g class="aq-nytt"><rect x="713" y="354" width="66" height="17" rx="8.5"/><text x="746" y="366.5" text-anchor="middle">nytt läge</text></g>
</g>
<g class="aq-bank {{AQ_BANK_3_CLASS}}"><title>{{AQ_BANK_3_TITEL}}</title>
<g filter="url(#aq-skugga)"><rect x="781" y="246" width="168" height="64" rx="6" class="aq-bord-topp"/><rect x="781" y="306" width="168" height="10" rx="4" class="aq-bord-front"/></g>
<rect x="868" y="286" width="10" height="8" class="aq-fot"/><rect x="843" y="252" width="60" height="34" rx="4" class="aq-skarm"/><g class="aq-skarm-rader"><rect x="851" y="260" width="34" height="3" rx="1"/><rect x="851" y="267" width="44" height="3" rx="1"/><rect x="851" y="274" width="26" height="3" rx="1"/></g>
<rect x="850" y="292" width="46" height="11" rx="3" class="aq-tangent"/>
<g class="aq-lampa"><circle cx="929" cy="258" r="52" class="aq-lampsken"/><circle cx="945" cy="272" r="6" class="aq-lampfot"/><line x1="945" y1="272" x2="929" y2="256" class="aq-lamparm"/><circle cx="929" cy="256" r="8" class="aq-lamphuvud"/></g>
<g class="aq-stol" filter="url(#aq-skugga-s)"><rect x="856" y="326" width="34" height="30" rx="10" class="aq-sits"/><path d="M856 360 q17 12 34 0" class="aq-rygg"/></g>
<g class="aq-arbetskort" filter="url(#aq-skugga-s)"><rect x="785" y="258" width="44" height="34" rx="3"/><circle cx="807" cy="263" r="3" class="aq-nal"/><rect x="792" y="272" width="30" height="3" rx="1" class="aq-black"/><rect x="792" y="279" width="24" height="3" rx="1" class="aq-black"/></g>
<g class="aq-person"><g class="aq-armar"><ellipse cx="856" cy="322" rx="6" ry="9" class="aq-jacka aq-arm-v"/><ellipse cx="890" cy="322" rx="6" ry="9" class="aq-jacka aq-arm-h"/></g><rect x="850" y="330" width="46" height="30" rx="15" class="aq-jacka aq-kropp"/><circle cx="873" cy="326" r="13" class="aq-hy aq-huvud"/><path d="M860 324 a13 13 0 0 1 26 0 v4 a13 9 0 0 1 -26 0 z" class="aq-har"/><g class="aq-senast"><rect x="803" y="282" width="140" height="20" rx="7"/><text x="873" y="296" text-anchor="middle">senast kända {{AQ_SENAST}}</text></g></g>
<g class="aq-skylt"><rect x="785" y="368" width="176" height="52" rx="10"/><text x="795" y="385" class="aq-skylt-a">{{AQ_BANK_3_NAMN}}</text><text x="795" y="400" class="aq-skylt-b">{{AQ_BANK_3_VEM}}</text><text x="795" y="414" class="aq-skylt-c">{{AQ_BANK_3_VAD}}</text></g>
<g class="aq-nytt"><rect x="893" y="354" width="66" height="17" rx="8.5"/><text x="926" y="366.5" text-anchor="middle">nytt läge</text></g>
</g>
<text x="946" y="236" class="aq-fler" text-anchor="end">{{AQ_VERK_FLER}}</text>
<g class="aq-vaxt aq-gungar" transform="translate(430 506) scale(0.90)"><ellipse cx="0" cy="18" rx="17" ry="6" class="aq-krukskugga"/><rect x="-12" y="3" width="24" height="17" rx="6" class="aq-kruka"/><g class="aq-blad"><ellipse cx="-10" cy="-5" rx="7" ry="14" transform="rotate(-30 -10 -5)"/><ellipse cx="10" cy="-5" rx="7" ry="14" transform="rotate(30 10 -5)"/><ellipse cx="0" cy="-12" rx="7.5" ry="16"/><ellipse cx="-4" cy="-2" rx="5" ry="10" transform="rotate(-8 -4 -2)" class="aq-blad-ljus"/></g></g>
<text x="685" y="470" class="aq-zon" text-anchor="middle">VERKSTADEN</text><text x="685" y="487" class="aq-zon-under" text-anchor="middle">{{AQ_VERK_UNDER}}</text>
<g class="aq-dimma"><rect x="416" y="126" width="540" height="306" rx="12"/><text x="686" y="273" text-anchor="middle" class="aq-dimma-a">kunde inte läsas</text><text x="686" y="293" text-anchor="middle" class="aq-dimma-b">läget är okänt, inte tomt</text></g>
</g></a>
<a href="#p-granskningen" class="aq-lank"><g class="aq-plats aq-granskningen {{AQ_GRANSK_STATUS}}"><title>Granskningen</title>
<rect x="964" y="176" width="10" height="300" rx="3" class="aq-halvvagg"/>
<g class="aq-gransk {{AQ_GRANSK_CLASS}}"><title>{{AQ_GRANSK_TITEL}}</title>
<g filter="url(#aq-skugga)"><rect x="988" y="246" width="144" height="64" rx="6" class="aq-bord-topp"/><rect x="988" y="306" width="144" height="10" rx="4" class="aq-bord-front"/></g><g class="aq-stol" filter="url(#aq-skugga-s)"><rect x="1043" y="326" width="34" height="30" rx="10" class="aq-sits"/><path d="M1043 360 q17 12 34 0" class="aq-rygg"/></g>
<rect x="1000" y="258" width="46" height="34" rx="2" class="aq-papper"/><rect x="1006" y="264" width="30" height="3" rx="1" class="aq-black"/><rect x="1006" y="271" width="34" height="3" rx="1" class="aq-black"/>
<g class="aq-luplampa"><circle cx="1104" cy="262" r="6" class="aq-lampfot"/><line x1="1104" y1="262" x2="1090" y2="282" class="aq-lamparm"/><circle cx="1088" cy="284" r="11" class="aq-lupglas"/></g>
<g class="aq-arbetskort" filter="url(#aq-skugga-s)"><rect x="1052" y="256" width="44" height="34" rx="3"/><circle cx="1074" cy="261" r="3" class="aq-nal"/><rect x="1059" y="270" width="30" height="3" rx="1" class="aq-black"/><rect x="1059" y="277" width="24" height="3" rx="1" class="aq-black"/></g>
<g class="aq-lupp"><circle cx="1018" cy="272" r="10" class="aq-lupglas"/><line x1="1025" y1="279" x2="1034" y2="288" class="aq-lupskaft"/></g>
<g class="aq-person"><g class="aq-armar"><ellipse cx="1043" cy="322" rx="6" ry="9" class="aq-jacka aq-arm-v"/><ellipse cx="1077" cy="322" rx="6" ry="9" class="aq-jacka aq-arm-h"/></g><rect x="1037" y="330" width="46" height="30" rx="15" class="aq-jacka aq-kropp"/><circle cx="1060" cy="326" r="13" class="aq-hy aq-huvud"/><path d="M1047 324 a13 13 0 0 1 26 0 v4 a13 9 0 0 1 -26 0 z" class="aq-har"/><g class="aq-senast"><rect x="990" y="282" width="140" height="20" rx="7"/><text x="1060" y="296" text-anchor="middle">senast kända {{AQ_SENAST}}</text></g></g>
<g class="aq-skylt"><rect x="972" y="368" width="176" height="52" rx="10"/><text x="982" y="385" class="aq-skylt-a">{{AQ_GRANSK_NAMN}}</text><text x="982" y="400" class="aq-skylt-b">{{AQ_GRANSK_VEM}}</text><text x="982" y="414" class="aq-skylt-c">{{AQ_GRANSK_VAD}}</text></g>
<g class="aq-nytt"><rect x="1080" y="354" width="66" height="17" rx="8.5"/><text x="1113" y="366.5" text-anchor="middle">nytt läge</text></g>
</g>
<rect x="996" y="428" width="76" height="26" rx="6" class="aq-korg" filter="url(#aq-skugga-s)"/><text x="1034" y="446" class="aq-korg-text" text-anchor="middle">granskning</text>
<text x="1140" y="236" class="aq-fler" text-anchor="end">{{AQ_GRANSK_FLER}}</text>
<text x="1060" y="500" class="aq-zon" text-anchor="middle">GRANSKNINGEN</text><text x="1060" y="517" class="aq-zon-under" text-anchor="middle">{{AQ_GRANSK_UNDER}}</text>
<g class="aq-dimma"><rect x="976" y="200" width="164" height="262" rx="12"/><text x="1058" y="325" text-anchor="middle" class="aq-dimma-a">kunde inte läsas</text><text x="1058" y="345" text-anchor="middle" class="aq-dimma-b">läget är okänt, inte tomt</text></g>
</g></a>
<a href="#p-utkiken" class="aq-lank"><g class="aq-plats aq-utkiken {{AQ_UTK_STATUS}} {{AQ_UTK_CLASS}}"><title>Utkiken: bevakningen</title>
<g filter="url(#aq-skugga)"><rect x="1230" y="150" width="220" height="64" rx="6" class="aq-bord-topp"/><rect x="1230" y="210" width="220" height="10" rx="4" class="aq-bord-front"/></g>
<rect x="1295" y="190" width="10" height="8" class="aq-fot"/><rect x="1270" y="156" width="60" height="34" rx="4" class="aq-skarm"/><g class="aq-skarm-rader"><rect x="1278" y="164" width="34" height="3" rx="1"/><rect x="1278" y="171" width="44" height="3" rx="1"/><rect x="1278" y="178" width="26" height="3" rx="1"/></g>
<rect x="1277" y="196" width="46" height="11" rx="3" class="aq-tangent"/>
<g class="aq-stol" filter="url(#aq-skugga-s)"><rect x="1283" y="252" width="34" height="30" rx="10" class="aq-sits"/><path d="M1283 286 q17 12 34 0" class="aq-rygg"/></g>
<g class="aq-rapport"><rect x="1360" y="160" width="46" height="36" rx="2" class="aq-papper"/><rect x="1360" y="160" width="46" height="8" rx="2" class="aq-rapportflagga"/><rect x="1366" y="174" width="30" height="3" rx="1" class="aq-black"/><rect x="1366" y="181" width="24" height="3" rx="1" class="aq-black"/><title>{{AQ_UTK_RAPPORT_TITEL}}</title></g>
<g class="aq-kalender" filter="url(#aq-skugga-s)"><rect x="1414" y="160" width="30" height="34" rx="4"/><rect x="1414" y="160" width="30" height="9" rx="3" class="aq-kalender-topp"/><text x="1429" y="186" text-anchor="middle">{{AQ_UTK_DAG}}</text><title>{{AQ_UTK_DAG_TITEL}}</title></g>
<g class="aq-lapp" filter="url(#aq-skugga-s)"><rect x="1174" y="234" width="66" height="50" rx="3"/><text x="1207" y="254" text-anchor="middle">granskat</text><text x="1207" y="272" text-anchor="middle">{{AQ_UTK_GRANSKAT}}</text><title>{{AQ_UTK_GRANSKAT_TITEL}}</title></g>
<g class="aq-vaktljus"><circle cx="1492" cy="182" r="32" class="aq-vaktljus-sken"/><circle cx="1492" cy="182" r="10" class="aq-vaktljus-karna"/></g>
<text x="1340" y="232" class="aq-platsskylt" text-anchor="middle">{{AQ_UTK_PLATS}}</text>
<g class="aq-vakt"><g class="aq-person"><g class="aq-armar"><ellipse cx="1283" cy="248" rx="6" ry="9" class="aq-jacka aq-arm-v"/><ellipse cx="1317" cy="248" rx="6" ry="9" class="aq-jacka aq-arm-h"/></g><rect x="1277" y="256" width="46" height="30" rx="15" class="aq-jacka aq-kropp"/><circle cx="1300" cy="252" r="13" class="aq-hy aq-huvud"/><path d="M1287 250 a13 13 0 0 1 26 0 v4 a13 9 0 0 1 -26 0 z" class="aq-har"/><g class="aq-senast"><rect x="1230" y="208" width="140" height="20" rx="7"/><text x="1300" y="222" text-anchor="middle">senast kända {{AQ_SENAST}}</text></g></g><g class="aq-skylt"><rect x="1212" y="292" width="176" height="52" rx="10"/><text x="1222" y="309" class="aq-skylt-a">{{AQ_UTK_NAMN}}</text><text x="1222" y="324" class="aq-skylt-b">{{AQ_UTK_VEM}}</text><text x="1222" y="338" class="aq-skylt-c">{{AQ_UTK_VAD}}</text></g></g>
<text x="1346" y="356" class="aq-zon" text-anchor="middle">UTKIKEN</text><text x="1346" y="373" class="aq-zon-under" text-anchor="middle">{{AQ_UTK_UNDER}}</text>
<g class="aq-dimma"><rect x="1166" y="124" width="366" height="198" rx="12"/><text x="1349" y="217" text-anchor="middle" class="aq-dimma-a">kunde inte läsas</text><text x="1349" y="237" text-anchor="middle" class="aq-dimma-b">läget är okänt, inte tomt</text></g>
</g></a>
<a href="#p-bordet" class="aq-lank"><g class="aq-plats aq-bordet {{AQ_BORD_STATUS}}"><title>Ägarens bord</title>
<g filter="url(#aq-skugga)"><rect x="1262" y="470" width="196" height="68" rx="6" class="aq-bord-valnot"/><rect x="1262" y="534" width="196" height="10" rx="4" class="aq-bord-valnot-front"/></g><g class="aq-stol" filter="url(#aq-skugga-s)"><rect x="1343" y="552" width="34" height="30" rx="10" class="aq-sits"/><path d="M1343 586 q17 12 34 0" class="aq-rygg"/></g>
<rect x="1280" y="482" width="60" height="38" rx="5" class="aq-korg" filter="url(#aq-skugga-s)"/><text x="1310" y="534" class="aq-korg-text" text-anchor="middle">in</text>
<g class="aq-lampa"><circle cx="1434" cy="486" r="52" class="aq-lampsken"/><circle cx="1450" cy="500" r="6" class="aq-lampfot"/><line x1="1450" y1="500" x2="1434" y2="484" class="aq-lamparm"/><circle cx="1434" cy="484" r="8" class="aq-lamphuvud"/></g>
<g class="aq-brev {{AQ_BREV_4_CLASS}}"><rect x="1289" y="488" width="42" height="26" rx="2" class="aq-kuvert"/><path d="M1289 488 l21 14 l21 -14" class="aq-kuvert-vik"/><title>{{AQ_BREV_4_TITEL}}</title></g>
<g class="aq-brev {{AQ_BREV_3_CLASS}}"><rect x="1286" y="484" width="42" height="26" rx="2" class="aq-kuvert"/><path d="M1286 484 l21 14 l21 -14" class="aq-kuvert-vik"/><title>{{AQ_BREV_3_TITEL}}</title></g>
<g class="aq-brev {{AQ_BREV_2_CLASS}}"><rect x="1283" y="480" width="42" height="26" rx="2" class="aq-kuvert"/><path d="M1283 480 l21 14 l21 -14" class="aq-kuvert-vik"/><title>{{AQ_BREV_2_TITEL}}</title></g>
<g class="aq-brev {{AQ_BREV_1_CLASS}}"><rect x="1280" y="476" width="42" height="26" rx="2" class="aq-kuvert"/><path d="M1280 476 l21 14 l21 -14" class="aq-kuvert-vik"/><title>{{AQ_BREV_1_TITEL}}</title></g>
<g class="aq-marke"><circle cx="1346" cy="458" r="14"/><text x="1346" y="463" text-anchor="middle">{{AQ_BORD_ANTAL}}</text></g>
<text x="1446" y="530" class="aq-fler" text-anchor="end">{{AQ_BORD_FLER}}</text>
<g class="aq-vaxt aq-gungar" transform="translate(1500 610) scale(1.00)"><ellipse cx="0" cy="18" rx="17" ry="6" class="aq-krukskugga"/><rect x="-12" y="3" width="24" height="17" rx="6" class="aq-kruka"/><g class="aq-blad"><ellipse cx="-10" cy="-5" rx="7" ry="14" transform="rotate(-30 -10 -5)"/><ellipse cx="10" cy="-5" rx="7" ry="14" transform="rotate(30 10 -5)"/><ellipse cx="0" cy="-12" rx="7.5" ry="16"/><ellipse cx="-4" cy="-2" rx="5" ry="10" transform="rotate(-8 -4 -2)" class="aq-blad-ljus"/></g></g>
<text x="1350" y="616" class="aq-zon" text-anchor="middle">ÄGARENS BORD</text><text x="1350" y="633" class="aq-zon-under" text-anchor="middle">{{AQ_BORD_UNDER}}</text>
</g></a>
<a href="#p-maskinrummet" class="aq-lank"><g class="aq-plats aq-maskinrummet {{AQ_SOCKEL_CLASS}}"><title>Maskinrummet: Runtime</title>
<rect x="470" y="668" width="200" height="104" rx="8" class="aq-rack"/>
<rect x="480" y="678" width="180" height="18" rx="3" class="aq-rackenhet"/>
<rect x="480" y="702" width="180" height="18" rx="3" class="aq-rackenhet"/>
<rect x="480" y="726" width="180" height="18" rx="3" class="aq-rackenhet"/>
<g class="aq-tjanstljus"><circle cx="520" cy="687" r="9" class="aq-tjanst-sken"/><circle cx="520" cy="687" r="4.5" class="aq-tjanst-karna"/></g><text x="520" y="764" class="aq-tjanstnamn" text-anchor="middle">daemon</text>
<g class="aq-tjanstljus"><circle cx="570" cy="687" r="9" class="aq-tjanst-sken"/><circle cx="570" cy="687" r="4.5" class="aq-tjanst-karna"/></g><text x="570" y="764" class="aq-tjanstnamn" text-anchor="middle">motor</text>
<g class="aq-tjanstljus"><circle cx="620" cy="687" r="9" class="aq-tjanst-sken"/><circle cx="620" cy="687" r="4.5" class="aq-tjanst-karna"/></g><text x="620" y="764" class="aq-tjanstnamn" text-anchor="middle">arbetare</text>
<g class="aq-skap"><rect x="720" y="672" width="130" height="96" rx="6"/><rect x="728" y="680" width="54" height="10" rx="2" class="aq-lada"/><rect x="790" y="680" width="54" height="10" rx="2" class="aq-lada"/><rect x="728" y="693" width="54" height="10" rx="2" class="aq-lada"/><rect x="790" y="693" width="54" height="10" rx="2" class="aq-lada"/><rect x="728" y="706" width="54" height="10" rx="2" class="aq-lada"/><rect x="790" y="706" width="54" height="10" rx="2" class="aq-lada"/><rect x="728" y="719" width="54" height="10" rx="2" class="aq-lada"/><rect x="790" y="719" width="54" height="10" rx="2" class="aq-lada"/><rect x="728" y="732" width="54" height="10" rx="2" class="aq-lada"/><rect x="790" y="732" width="54" height="10" rx="2" class="aq-lada"/><rect x="728" y="745" width="54" height="10" rx="2" class="aq-lada"/><rect x="790" y="745" width="54" height="10" rx="2" class="aq-lada"/><title>{{AQ_SOCKEL_TITEL}}</title></g>
<path d="M670 712 C 690 712, 700 720, 720 720" class="aq-kabel"/>
<text x="780" y="800" class="aq-zon" text-anchor="middle">MASKINRUMMET · RUNTIME</text><text x="780" y="817" class="aq-zon-under" text-anchor="middle">{{AQ_SOCKEL_UNDER}}</text>
</g></a>
<a href="#p-interaktivt" class="aq-lank"><g class="aq-plats aq-interaktivt"><title>Interaktivt arbete: observeras inte</title>
<rect x="78" y="600" width="306" height="220" rx="10" class="aq-motesgolv"/>
<g class="aq-frost-inre" filter="url(#aq-oskarp)"><rect x="160" y="676" width="140" height="56" rx="12"/><circle cx="180" cy="760" r="12"/><circle cx="230" cy="768" r="12"/><circle cx="280" cy="760" r="12"/></g>
<rect x="78" y="600" width="306" height="220" rx="10" class="aq-frostglas"/>
<line x1="180" y1="600" x2="180" y2="820" class="aq-frostpost"/>
<line x1="282" y1="600" x2="282" y2="820" class="aq-frostpost"/>
<g class="aq-dorrskylt"><rect x="141" y="690" width="180" height="44" rx="10"/><text x="231" y="709" text-anchor="middle" class="aq-dorrskylt-a">INTERAKTIVT ARBETE</text><text x="231" y="725" text-anchor="middle" class="aq-dorrskylt-b">syns inte här · observeras inte</text></g>
</g></a>
<g class="aq-lounge"><g filter="url(#aq-skugga)"><rect x="1180" y="676" width="120" height="44" rx="6" class="aq-disk"/><rect x="1180" y="716" width="120" height="10" rx="4" class="aq-disk-front"/></g><rect x="1196" y="682" width="30" height="26" rx="5" class="aq-kaffemaskin"/><circle cx="1250" cy="696" r="7" class="aq-mugg"/><circle cx="1420" cy="740" r="26" class="aq-rundbord" filter="url(#aq-skugga-s)"/><g class="aq-stol" filter="url(#aq-skugga-s)"><rect x="1365" y="732" width="34" height="30" rx="10" class="aq-sits"/><path d="M1365 766 q17 12 34 0" class="aq-rygg"/></g><g class="aq-stol" filter="url(#aq-skugga-s)"><rect x="1441" y="732" width="34" height="30" rx="10" class="aq-sits"/><path d="M1441 766 q17 12 34 0" class="aq-rygg"/></g></g>
<g class="aq-vaxt aq-gungar" transform="translate(1210 800) scale(1.20)"><ellipse cx="0" cy="18" rx="17" ry="6" class="aq-krukskugga"/><rect x="-12" y="3" width="24" height="17" rx="6" class="aq-kruka"/><g class="aq-blad"><ellipse cx="-10" cy="-5" rx="7" ry="14" transform="rotate(-30 -10 -5)"/><ellipse cx="10" cy="-5" rx="7" ry="14" transform="rotate(30 10 -5)"/><ellipse cx="0" cy="-12" rx="7.5" ry="16"/><ellipse cx="-4" cy="-2" rx="5" ry="10" transform="rotate(-8 -4 -2)" class="aq-blad-ljus"/></g></g>
<g class="aq-vaxt" transform="translate(1510 690) scale(0.90)"><ellipse cx="0" cy="18" rx="17" ry="6" class="aq-krukskugga"/><rect x="-12" y="3" width="24" height="17" rx="6" class="aq-kruka"/><g class="aq-blad"><ellipse cx="-10" cy="-5" rx="7" ry="14" transform="rotate(-30 -10 -5)"/><ellipse cx="10" cy="-5" rx="7" ry="14" transform="rotate(30 10 -5)"/><ellipse cx="0" cy="-12" rx="7.5" ry="16"/><ellipse cx="-4" cy="-2" rx="5" ry="10" transform="rotate(-8 -4 -2)" class="aq-blad-ljus"/></g></g>
<g class="aq-vaxt aq-gungar" transform="translate(560 590) scale(0.90)"><ellipse cx="0" cy="18" rx="17" ry="6" class="aq-krukskugga"/><rect x="-12" y="3" width="24" height="17" rx="6" class="aq-kruka"/><g class="aq-blad"><ellipse cx="-10" cy="-5" rx="7" ry="14" transform="rotate(-30 -10 -5)"/><ellipse cx="10" cy="-5" rx="7" ry="14" transform="rotate(30 10 -5)"/><ellipse cx="0" cy="-12" rx="7.5" ry="16"/><ellipse cx="-4" cy="-2" rx="5" ry="10" transform="rotate(-8 -4 -2)" class="aq-blad-ljus"/></g></g>
<g class="aq-vaxt" transform="translate(1000 590) scale(0.80)"><ellipse cx="0" cy="18" rx="17" ry="6" class="aq-krukskugga"/><rect x="-12" y="3" width="24" height="17" rx="6" class="aq-kruka"/><g class="aq-blad"><ellipse cx="-10" cy="-5" rx="7" ry="14" transform="rotate(-30 -10 -5)"/><ellipse cx="10" cy="-5" rx="7" ry="14" transform="rotate(30 10 -5)"/><ellipse cx="0" cy="-12" rx="7.5" ry="16"/><ellipse cx="-4" cy="-2" rx="5" ry="10" transform="rotate(-8 -4 -2)" class="aq-blad-ljus"/></g></g>
</g>
<g class="aq-banner"><rect x="170" y="97" width="1260" height="34" rx="17"/><text x="800" y="119" text-anchor="middle"><tspan class="aq-banner-a">Inaktuell · ingen ny läsning sedan {{AQ_SENAST}}</tspan><tspan class="aq-banner-b" dx="12">Bilden visar senast kända läge; det betyder inte att arbete, tjänst eller ägarärenden har upphört.</tspan></text></g>
<g class="aq-provband"><rect x="1172" y="866" width="368" height="26" rx="8"/><text x="1356" y="884" text-anchor="middle">PROVDATA · inte en observation av verksamheten</text></g>
<text x="60" y="884" class="aq-fot-text aq-bildrad">Läsvy · startar, godkänner och ändrar ingenting · välj en plats för detaljer, källa och tid</text><text x="60" y="884" class="aq-fot-text aq-fonsterrad">Läsvy · startar, godkänner och ändrar ingenting · läser om högst varannan minut medan sidan är öppen · nytt läge = ändrat sedan förra läsningen, inte när eller hur</text>
</svg>
<section class="aq-panel" id="p-arkivet" aria-labelledby="t-arkivet"><a class="aq-stang" href="#">Stäng</a><h2 id="t-arkivet">Arkivet</h2><p>Levererade och avslutade åtaganden ur kontorets beslutslogg och leveransbesked, nyast först.</p><ul class="aq-lista"><!--AQ:LISTA:arkivet--></ul><p class="aq-kalla">{{AQ_KALLA_ARKIVET}}</p></section><section class="aq-panel" id="p-verkstaden" aria-labelledby="t-verkstaden"><a class="aq-stang" href="#">Stäng</a><h2 id="t-verkstaden">Verkstaden</h2><p>Arbete som motorn visar som pågående, och uppdrag i motorn som inte arbetar.</p><ul class="aq-lista"><!--AQ:LISTA:verkstaden--></ul><p class="aq-kalla">{{AQ_KALLA_VERKSTADEN}}</p></section><section class="aq-panel" id="p-granskningen" aria-labelledby="t-granskningen"><a class="aq-stang" href="#">Stäng</a><h2 id="t-granskningen">Granskningen</h2><p>Granskningar och integrationer som motorn visar som pågående.</p><ul class="aq-lista"><!--AQ:LISTA:granskningen--></ul><p class="aq-kalla">{{AQ_KALLA_GRANSKNINGEN}}</p></section><section class="aq-panel" id="p-utkiken" aria-labelledby="t-utkiken"><a class="aq-stang" href="#">Stäng</a><h2 id="t-utkiken">Utkiken</h2><p>Bevakningens schema, omgångar och besked. Starter är startade, inte genomförda.</p><ul class="aq-lista"><!--AQ:LISTA:utkiken--></ul><p class="aq-kalla">{{AQ_KALLA_UTKIKEN}}</p></section><section class="aq-panel" id="p-bordet" aria-labelledby="t-bordet"><a class="aq-stang" href="#">Stäng</a><h2 id="t-bordet">Ägarens bord</h2><p>Det som väntar på dig: beslut, operatörshandlingar och modellfrågor.</p><ul class="aq-lista"><!--AQ:LISTA:bordet--></ul><p class="aq-kalla">{{AQ_KALLA_BORDET}}</p></section><section class="aq-panel" id="p-maskinrummet" aria-labelledby="t-maskinrummet"><a class="aq-stang" href="#">Stäng</a><h2 id="t-maskinrummet">Maskinrummet</h2><p>Tjänsten, den konfigurerade bemanningen och de tekniska identitetsposterna. Konfiguration är inte observerat utförande.</p><ul class="aq-lista"><!--AQ:LISTA:maskinrummet--></ul><p class="aq-kalla">{{AQ_KALLA_MASKINRUMMET}}</p></section><section class="aq-panel" id="p-interaktivt" aria-labelledby="t-interaktivt"><a class="aq-stang" href="#">Stäng</a><h2 id="t-interaktivt">Interaktivt arbete</h2><p>Aquarium läser Runtimes motor, tjänst och bevakning och kontorets publicerade register. Interaktiva sessioner, till exempel kedjedrivarens, observeras inte och visas därför inte, varken som arbete eller som frånvaro av arbete. Rubrikens räkning gäller bara det som observeras i Runtime.</p></section><section class="aq-panel" id="p-kallor" aria-labelledby="t-kallor"><a class="aq-stang" href="#">Stäng</a><h2 id="t-kallor">Källor och tider</h2><p>När varje källa lästes och när den räknas som inaktuell. Läsningen är en ögonblicksbild, inte live.</p><ul class="aq-lista"><!--AQ:LISTA:kallor--></ul><p class="aq-kalla">Tiderna är lästider, inte sidans skapelsetid; en ny sida gör inte en läsning nyare.</p></section>
<!--AQ:SKRIPT-->
</body></html>
'''

SKRIPT = '''(function () {
  var body = document.body, age = document.getElementById('aq-alder');
  function fresh(node, now) {
    var read = Date.parse(node.getAttribute('data-read-at') || ''), limit = Number(node.getAttribute('data-stale-after')) * 1000;
    return isFinite(read) && isFinite(limit) && limit > 0 && now - read >= 0 && now - read <= limit;
  }
  function tick() {
    var now = Date.now(), ok = fresh(body, now), read = Date.parse(body.getAttribute('data-read-at') || ''), rows = document.querySelectorAll('li[data-read-at]');
    body.classList.toggle('aq-farsk', ok);
    body.classList.toggle('aq-inaktuell', !ok);
    if (age) {
      var minutes = Math.floor((now - read) / 60000);
      age.textContent = !isFinite(read) || minutes < 0 ? 'ålder okänd' : minutes < 1 ? 'nyss' : minutes < 60 ? 'för ' + minutes + ' min sedan' :
        minutes < 2880 ? 'för ' + Math.floor(minutes / 60) + ' tim sedan' : 'för ' + Math.floor(minutes / 1440) + ' dygn sedan';
    }
    for (var i = 0; i < rows.length; i++) rows[i].classList.toggle('aq-inaktuell-kalla', !fresh(rows[i], now));
  }
  tick();
  setInterval(tick, 30000);
})();'''

FONSTERSKRIPT = '''(function () {
  var read = document.body.getAttribute('data-read-at');
  function poll() {
    fetch('/lasning.json', {cache: 'no-store'}).then(function (answer) {
      return answer.ok ? answer.json() : null;
    }).then(function (latest) {
      if (latest && typeof latest.read_at === 'string' && latest.read_at !== read) location.reload();
    }).catch(function () {});
  }
  poll();
  setInterval(poll, 30000);
})();'''

# --- constants and formats --------------------------------------------------------

SCHEMA = 2
ERROR = 'Ogiltig projektion för Aquariums vy.'
COMMAND_ERROR = 'Kunde inte skapa Aquariums vy.'
MAX_BYTES = 1000000
KEYS = ('schema', 'provdata', 'read_at', 'sources', 'revisions', 'headline', 'arkivet',
        'verkstaden', 'utkiken', 'agarens_bord', 'sockeln')
SOURCES = ('release', 'staffing', 'questions', 'service', 'engine', 'tasks', 'watch', 'office')
MONTHS = ('jan', 'feb', 'mar', 'apr', 'maj', 'jun', 'jul', 'aug', 'sep', 'okt', 'nov', 'dec')
KINDS = {'beslut': 'Beslut', 'operatörshandling': 'Operatörshandling', 'modellfråga': 'Modellfråga'}
WAITING = {'beslut': 'ett beslut väntar på dig',
           'operatörshandling': 'en operatörshandling väntar på dig',
           'modellfråga': 'en modellfråga väntar på dig'}
MISSING_TITLE = {'saknas': 'titel saknas i uppdragsfilen', 'oläslig': 'titeln kunde inte läsas',
                 'okänd': 'uppdragsfilerna kunde inte läsas'}
NAME_LIMIT = 22
UNREADABLE_ENGINE = 'Motorn kunde inte läsas; inget visas som noll'
UNREADABLE_WATCH = 'bevakningen kunde inte läsas'
NOT_MODEL_CHOICE = ' · följer inte modellvalet'

# The window mode: the comparison of the window's two latest readings, and nothing else.
JAMFOR_KEYS = ('grund', 'forra_read_at', 'uppdrag')
LAGE_KEYS = ('plats', 'step', 'state', 'executor')
GRUNDER = ('första', 'otillräcklig', 'jämförd')
FIRST_READING = 'första läsningen sedan fönstret startade; bilden visar bara aktuellt läge'
NO_BASIS = 'underlaget räcker inte för en jämförelse; bilden visar bara aktuellt läge'
NOT_WHEN_OR_HOW = '; nytt läge visar det uppdaterade läget, inte när eller hur det ändrades'
FÖRRA_STEG = {'granskning': 'granskning', 'integration': 'integration', 'steg': 'steg pågår'}
MARK = ' aq-nytt-lage'

# The renderer touches no file: the zone and the pinned script digest are made at import, and the
# zone is asked for both a winter and a summer offset here so that no lookup is left to `render`.
ZONE = ZoneInfo('Europe/Stockholm')
ZONE.utcoffset(datetime(2026, 1, 15))
ZONE.utcoffset(datetime(2026, 7, 15))
_PLACEHOLDER = re.compile(r'\{\{(AQ_[A-Z0-9_]+)\}\}')
_SLOT = re.compile(r'<!--AQ:LISTA:([a-z]+)-->')
_NAMES = frozenset(_PLACEHOLDER.findall(SCEN))
_SLOTS = frozenset(_SLOT.findall(SCEN))
_DATE = re.compile(r'\d{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12]\d|3[01])')
_CSP = ("default-src 'none'; style-src 'unsafe-inline'; script-src 'sha256-"
        + base64.b64encode(hashlib.sha256(SKRIPT.encode('utf-8')).digest()).decode('ascii')
        + "'; base-uri 'none'; form-action 'none'")


def _pinned(script):
    """The base64 of one script's SHA-256, as a Content-Security-Policy pins it."""
    return base64.b64encode(hashlib.sha256(script.encode('utf-8')).digest()).decode('ascii')


# The window page pins both scripts and may ask its own window, and nothing else, over the network.
_FONSTER_CSP = ("default-src 'none'; style-src 'unsafe-inline'; script-src 'sha256-"
                + _pinned(SKRIPT) + "' 'sha256-" + _pinned(FONSTERSKRIPT)
                + "'; connect-src 'self'; base-uri 'none'; form-action 'none'")


def _refuse():
    raise ValueError(ERROR)


def csp():
    """The page's Content-Security-Policy, pinning SKRIPT by its SHA-256."""
    return _CSP


def fonster_csp():
    """The window page's policy, pinning SKRIPT and FONSTERSKRIPT by their SHA-256."""
    return _FONSTER_CSP


def _moment(value):
    """An aware ISO time as Stockholm local time; anything else is not a time."""
    if type(value) is not str:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return None
    return parsed.astimezone(ZONE)


def _is_date(value):
    return type(value) is str and _DATE.fullmatch(value) is not None


def TID(value):
    """`<day> <mon> <HH>:<MM>` in Stockholm local time, never a relative label."""
    moment = _moment(value)
    if moment is None:
        return 'tid okänd'
    return '%d %s %02d:%02d' % (moment.day, MONTHS[moment.month - 1], moment.hour, moment.minute)


def DATUM(value):
    """`<day> <mon>` for a date, or the Stockholm local date of an ISO time."""
    if _is_date(value):
        return '%d %s' % (int(value[8:10]), MONTHS[int(value[5:7]) - 1])
    moment = _moment(value)
    if moment is None:
        return 'datum okänt'
    return '%d %s' % (moment.day, MONTHS[moment.month - 1])


def NÄR(value):
    """A date keeps its day, a point in time keeps its clock."""
    return DATUM(value) if _is_date(value) else TID(value)


def _LOKALT(value):
    """The Stockholm local date of an ISO time as `YYYY-MM-DD`."""
    moment = _moment(value)
    return None if moment is None else '%04d-%02d-%02d' % (moment.year, moment.month, moment.day)


def NAMN(value):
    text = value if type(value) is str else ''
    return text if len(text) <= NAME_LIMIT else text[:NAME_LIMIT - 1] + '…'


def EXEC(name):
    if name == 'claude':
        return 'Claude'
    if name == 'codex':
        return 'Codex'
    return name if type(name) is str else str(name)


def MODELL(executor, model):
    return EXEC(executor) + (' · modell okänd' if model is None else ' ' + model)


def SEDAN(item):
    since = item['since']
    return 'starttid okänd' if since is None else 'sedan ' + TID(since)


def ANTAL(count, singular, plural):
    """A count with a singular and a plural form; exactly 1 is the singular."""
    return singular if count == 1 else plural % count


def KÄLLA(sources, ids):
    """`Källa: ` or `Källor: ` and, per source, its title with its read time or its absence."""
    parts = []
    for name in ids:
        source = sources[name]
        parts.append(source['title'] + ' · läst ' + TID(source['read_at'])
                     if source['status'] == 'ok' else source['title'] + ' · otillgänglig')
    return ('Källa: ' if len(ids) == 1 else 'Källor: ') + '; '.join(parts)


def VEM(item):
    """Who the engine reading evidences at this step; an executor it does not show is not filled in."""
    step = item['step']
    if step == 'utförande':
        return (EXEC(item['executor']) + ' · utförare') if item['executor'] else 'utförare ej belagd'
    if step == 'granskning':
        return 'granskare ej belagd'
    if step == 'integration':
        return 'värdens integration'
    if step == 'steg':
        return 'steg pågår'
    return 'arbetsflödessteg'


def STEG(item):
    return ', '.join(item['activities']) if item['activities'] else 'arbetsflödessteg'


def TEKNISK(item):
    return (item['task'] + ' · ' + item['type'] + ' · ' + STEG(item) + ' · ' + SEDAN(item))


def TITEL(item):
    """A parked task's title, or what the task file could not tell."""
    if item['title_status'] == 'läst' and type(item['title']) is str:
        return item['title']
    return MISSING_TITLE.get(item['title_status'], 'titeln kunde inte läsas')


def FÖRRA(lage):
    """What the previous reading showed for this task; a reading's state, never an event."""
    if lage['plats'] == 'vilar':
        return 'arbetade inte'
    if lage['step'] == 'utförande':
        return 'utförande · ' + ('utförare ej belagd' if lage['executor'] is None
                                else EXEC(lage['executor']))
    return FÖRRA_STEG.get(lage['step'], 'arbetsflödessteg')


def JÄMFÖRELSE(jamforelse):
    """The window's comparison line: what differs from the previous reading, not when or how."""
    if jamforelse['grund'] == 'första':
        return FIRST_READING
    if jamforelse['grund'] == 'otillräcklig':
        return NO_BASIS
    count = len(jamforelse['uppdrag'])
    changed = ('inget uppdrag i nytt läge' if not count
               else ANTAL(count, '1 uppdrag i nytt läge', '%d uppdrag i nytt läge'))
    return ('jämfört med läsningen ' + TID(jamforelse['forra_read_at']) + ': ' + changed
            + NOT_WHEN_OR_HOW)


def _nytt(jamforelse, task):
    """Whether this reading shows a new observed state for this task, compared with the previous."""
    return jamforelse is not None and task in jamforelse['uppdrag']


def _MARKT(klass, jamforelse, task):
    """The mark on a place that shows a task in a new observed state."""
    return klass + MARK if _nytt(jamforelse, task) else klass


def _TILLAGG(jamforelse, task):
    """A row's addition: the previous reading's time and the state it showed."""
    if not _nytt(jamforelse, task):
        return ''
    return (' · nytt läge; förra läsningen ' + TID(jamforelse['forra_read_at']) + ': '
            + FÖRRA(jamforelse['uppdrag'][task]))


# --- the page ---------------------------------------------------------------------


def _escape(value):
    return html.escape(value, quote=True)


def _rad(label, text):
    return ('<li><span class="aq-etikett">' + _escape(label) + '</span>' + _escape(text) + '</li>')


def _validate(projection):
    """Refuse anything that is not a schema 2 projection, without private values in the message."""
    if type(projection) is not dict or set(projection) != set(KEYS):
        _refuse()
    if type(projection['schema']) is not int or projection['schema'] != SCHEMA:
        _refuse()
    if type(projection['provdata']) is not bool:
        _refuse()
    if _moment(projection['read_at']) is None:
        _refuse()
    sources = projection['sources']
    if type(sources) is not dict or set(sources) != set(SOURCES):
        _refuse()
    for name in SOURCES:
        source = sources[name]
        if type(source) is not dict or source.get('status') not in ('ok', 'otillgänglig'):
            _refuse()
        if source['status'] == 'ok':
            if _moment(source.get('read_at')) is None:
                _refuse()
            if type(source.get('stale_after_seconds')) is not int:
                _refuse()
    headline = projection['headline']
    if type(headline) is not dict:
        _refuse()
    for key in ('pagar', 'vantar', 'behover_dig'):
        value = headline.get(key)
        if value is not None and type(value) is not int:
            _refuse()


def _validate_jamforelse(jamforelse):
    """Refuse anything that is not one comparison of two readings, as `jamfor` returns it."""
    if type(jamforelse) is not dict or set(jamforelse) != set(JAMFOR_KEYS):
        _refuse()
    uppdrag = jamforelse['uppdrag']
    if jamforelse['grund'] not in GRUNDER or type(uppdrag) is not dict:
        _refuse()
    if jamforelse['grund'] == 'jämförd':
        if _moment(jamforelse['forra_read_at']) is None:
            _refuse()
    elif jamforelse['forra_read_at'] is not None or uppdrag:
        _refuse()
    for task, lage in uppdrag.items():
        if type(task) is not str or type(lage) is not dict or set(lage) != set(LAGE_KEYS):
            _refuse()
        if lage['plats'] == 'vilar':
            if any(lage[key] is not None for key in ('step', 'state', 'executor')):
                _refuse()
        elif lage['plats'] == 'arbete':
            if type(lage['step']) is not str or type(lage['state']) is not str:
                _refuse()
            if lage['executor'] is not None and type(lage['executor']) is not str:
                _refuse()
        else:
            _refuse()


def _fill(values, rows, jamforelse):
    """Three passes over SCEN: escaped placeholders, then list rows, then the pinned scripts."""
    if set(values) != _NAMES or set(rows) != _SLOTS:
        _refuse()

    def one(found):
        return _escape(values[found.group(1)])

    def slot(found):
        return ''.join(rows[found.group(1)])

    page = _PLACEHOLDER.sub(one, SCEN)
    page = _SLOT.sub(slot, page)
    script = '<script>' + SKRIPT + '</script>'
    if jamforelse is not None:
        script += '<script>' + FONSTERSKRIPT + '</script>'
    return page.replace('<!--AQ:SKRIPT-->', script)


def _rubrik(projection, waiting):
    """Work, watch and owner in one line; an unknown count is never spoken of as nothing."""
    h, U = projection['headline'], projection['utkiken']
    if h['pagar'] is None:
        work = 'motorn kunde inte läsas'
    elif h['pagar'] == 0:
        work = 'inget uppdrag arbetar i Runtime'
    elif h['pagar'] == 1:
        work = 'ett uppdrag arbetar i Runtime'
    else:
        work = '%d uppdrag arbetar i Runtime' % h['pagar']
    if U['status'] != 'ok':
        watch = 'bevakningen kunde inte läsas'
    elif U['schedule'] == 'stoppat':
        watch = 'bevakningen stoppad'
    elif U['schedule'] == 'pausat':
        watch = 'bevakningen pausad'
    elif (U['running'] or 0) > 0:
        watch = 'bevakningen kör en omgång'
    elif U['latest'] is not None and U['latest']['cause'] is not None:
        watch = 'bevakningens senaste omgång otillräcklig'
    elif U['waiting']:
        watch = 'bevakningens besked väntar på granskning'
    else:
        watch = 'bevakningen i vila'
    line = work + ' · ' + watch + ' · ' + waiting
    if projection['headline'].get('lugnt') is True:
        line = 'Lugnt · ' + line
    if projection['provdata']:
        line = 'PROVDATA · ' + line
    return line[:1].upper() + line[1:]


def _agare(B):
    """What waits for the owner; an unread source makes it unknown, never empty."""
    items = B['items']
    if len(items) == 1:
        known = WAITING.get(items[0]['kind'], 'ett ärende väntar på dig')
    else:
        known = '%d ärenden väntar på dig' % len(items)
    if B['status'] == 'ok':
        return 'inget väntar på dig' if not items else known
    return 'okänt om något väntar på dig' if not items else known + ' · fler kan finnas'


def _arkivet(A, R, sources, local_date, values, rows):
    items = A['items']
    for number in range(1, 17):
        item = items[number - 1] if len(items) >= number else None
        if item is None:
            values['AQ_VOL_%d_CLASS' % number] = 'aq-av'
            values['AQ_VOL_%d_TITEL' % number] = ''
        else:
            values['AQ_VOL_%d_CLASS' % number] = ('aq-pa aq-ny' if item['date'] == local_date
                                                  else 'aq-pa')
            values['AQ_VOL_%d_TITEL' % number] = (
                item['key'] + ' · ' + item['title'] + ' · '
                + (DATUM(item['date']) if item['date'] else 'odaterad'))
    values['AQ_ARKIV_STATUS'] = '' if A['status'] == 'ok' else 'aq-otillganglig'
    values['AQ_ARKIV_FLER'] = '+%d' % (len(items) - 16) if len(items) > 16 else ''
    if A['status'] != 'ok':
        values['AQ_ARKIV_UNDER'] = 'kontorets källa kunde inte läsas'
        rows['arkivet'] = [_rad('Läge', 'Kontorets källa kunde inte läsas; inget visas som tomt')]
    elif not items:
        values['AQ_ARKIV_UNDER'] = 'inga leveranser registrerade'
        rows['arkivet'] = [_rad('Läge', 'Inga leveranser registrerade')]
    else:
        under = ANTAL(len(items), '1 leverans', '%d leveranser')
        dated = next((item for item in items if item['date']), None)
        values['AQ_ARKIV_UNDER'] = (under if dated is None
                                    else under + ' · senast ' + DATUM(dated['date']))
        rows['arkivet'] = [_rad(DATUM(item['date']) if item['date'] else 'odaterad',
                                item['key'] + ' · ' + item['title'] + ' — ' + item['basis'])
                           for item in items]
    values['AQ_KALLA_ARKIVET'] = (KÄLLA(sources, ('office',))
                                  + ('' if R['office_main'] is None
                                     else ' · main ' + R['office_main']))


def _verkstaden(V, sources, values, rows, jamforelse):
    """The benches take the work in progress; the board takes the tasks that do not work."""
    bench = [item for item in V['items'] if item['state'] == 'pågår']
    desk = [item for item in V['items'] if item['state'] in ('granskas', 'integreras')]
    parked = V['parked']
    values['AQ_VERK_STATUS'] = values['AQ_GRANSK_STATUS'] = ('' if V['status'] == 'ok'
                                                             else 'aq-otillganglig')
    for number in range(1, 4):
        item = bench[number - 1] if len(bench) >= number else None
        if item is None:
            values['AQ_BANK_%d_CLASS' % number] = 'aq-vilar'
            values['AQ_BANK_%d_NAMN' % number] = ''
            values['AQ_BANK_%d_VEM' % number] = ''
            values['AQ_BANK_%d_VAD' % number] = ''
            values['AQ_BANK_%d_TITEL' % number] = 'ledig bänk'
            continue
        # A figure is drawn only where the engine reading itself evidences an executor step.
        klass = 'aq-pagar'
        if item['step'] == 'utförande':
            klass += (' aq-figur aq-claude' if item['executor'] == 'claude' else
                      ' aq-figur aq-codex' if item['executor'] == 'codex' else
                      ' aq-figur aq-okand')
        values['AQ_BANK_%d_CLASS' % number] = _MARKT(klass, jamforelse, item['task'])
        values['AQ_BANK_%d_NAMN' % number] = NAMN(item['short'])
        values['AQ_BANK_%d_VEM' % number] = VEM(item)
        values['AQ_BANK_%d_VAD' % number] = SEDAN(item)
        values['AQ_BANK_%d_TITEL' % number] = TEKNISK(item)
    values['AQ_VERK_FLER'] = '+%d' % (len(bench) - 3) if len(bench) > 3 else ''
    for number in range(1, 9):
        item = parked[number - 1] if len(parked) >= number else None
        if item is None:
            values['AQ_PARK_%d_CLASS' % number] = 'aq-av'
            values['AQ_PARK_%d_NAMN' % number] = ''
            values['AQ_PARK_%d_TITEL' % number] = ''
            continue
        values['AQ_PARK_%d_CLASS' % number] = _MARKT(
            'aq-pa' if item['title_status'] == 'läst' else 'aq-pa aq-titel-saknas',
            jamforelse, item['task'])
        values['AQ_PARK_%d_NAMN' % number] = NAMN(item['short'])
        values['AQ_PARK_%d_TITEL' % number] = (TITEL(item) + ' · ' + item['task'] + ' · '
                                               + SEDAN(item))
    values['AQ_PARK_FLER'] = '+%d' % (len(parked) - 8) if len(parked) > 8 else ''

    if V['status'] != 'ok':
        values['AQ_TAVLA_UNDER'] = 'okänt'
        values['AQ_VERK_UNDER'] = 'motorn kunde inte läsas'
        rows['verkstaden'] = [_rad('Läge', UNREADABLE_ENGINE)]
    else:
        values['AQ_TAVLA_UNDER'] = ('inga' if not parked
                                    else ANTAL(len(parked), '1 uppdrag', '%d uppdrag'))
        values['AQ_VERK_UNDER'] = (
            ('inget arbete observerat i motorn' if not bench
             else ANTAL(len(bench), '1 i arbete', '%d i arbete'))
            + ' · ' + ANTAL(len(parked), '1 uppdrag arbetar inte', '%d uppdrag arbetar inte'))
        listed = [_rad('Pågår', item['task'] + ' · ' + VEM(item) + ' · ' + SEDAN(item)
                       + ' · steg ' + STEG(item) + _TILLAGG(jamforelse, item['task']))
                  for item in bench]
        if not listed:
            listed = [_rad('Läge', 'Inget arbete pågår i motorn')]
        if parked:
            listed += [_rad('Arbetar inte', item['task'] + ' · ' + TITEL(item) + ' · '
                            + SEDAN(item) + _TILLAGG(jamforelse, item['task']))
                       for item in parked]
        else:
            listed.append(_rad('Arbetar inte', 'inga uppdrag'))
        if V['titles'] != 'ok':
            listed.append(_rad('Uppdragsfiler',
                               'kunde inte läsas; titlarna är okända men uppdragen visas'))
        rows['verkstaden'] = listed
    if jamforelse is not None:
        # The window always says what the comparison rests on, also when the engine was unreadable.
        rows['verkstaden'].append(_rad('Jämförelse', JÄMFÖRELSE(jamforelse)))
    values['AQ_KALLA_VERKSTADEN'] = KÄLLA(sources, ('engine', 'tasks'))

    first = desk[0] if desk else None
    if first is None:
        values['AQ_GRANSK_CLASS'] = 'aq-vilar'
        values['AQ_GRANSK_NAMN'] = ''
        values['AQ_GRANSK_VEM'] = ''
        values['AQ_GRANSK_VAD'] = ''
        values['AQ_GRANSK_TITEL'] = 'ingen granskning'
    else:
        values['AQ_GRANSK_CLASS'] = _MARKT('aq-granskas aq-figur aq-okand'
                                           if first['state'] == 'granskas' else 'aq-integreras',
                                           jamforelse, first['task'])
        values['AQ_GRANSK_NAMN'] = NAMN(first['short'])
        values['AQ_GRANSK_VEM'] = VEM(first)
        values['AQ_GRANSK_VAD'] = SEDAN(first)
        values['AQ_GRANSK_TITEL'] = TEKNISK(first)
    values['AQ_GRANSK_FLER'] = '+%d' % (len(desk) - 1) if len(desk) > 1 else ''
    if V['status'] != 'ok':
        values['AQ_GRANSK_UNDER'] = 'motorn kunde inte läsas'
        rows['granskningen'] = [_rad('Läge', UNREADABLE_ENGINE)]
    elif not desk:
        values['AQ_GRANSK_UNDER'] = 'ingen granskning observerad'
        rows['granskningen'] = [_rad('Läge',
                                     'Ingen granskning eller integration pågår i motorn')]
    else:
        reviewing = sum(1 for item in desk if item['state'] == 'granskas')
        integrating = sum(1 for item in desk if item['state'] == 'integreras')
        parts = ([('%d granskas' % reviewing)] if reviewing else [])
        parts += ([('%d integreras' % integrating)] if integrating else [])
        values['AQ_GRANSK_UNDER'] = ' · '.join(parts)
        rows['granskningen'] = [
            _rad('Granskas' if item['state'] == 'granskas' else 'Integreras',
                 item['task'] + ' · ' + VEM(item) + ' · ' + SEDAN(item) + ' · steg ' + STEG(item)
                 + _TILLAGG(jamforelse, item['task']))
            for item in desk]
    values['AQ_KALLA_GRANSKNINGEN'] = KÄLLA(sources, ('engine',))


def _utkiken(U, sources, values, rows):
    """The watch's own place: a planned round is not a performed round."""
    model = MODELL(U['model']['executor'], U['model']['model'])
    values['AQ_UTK_PLATS'] = 'bevakningens plats · konfigurerad: ' + model
    values['AQ_KALLA_UTKIKEN'] = KÄLLA(sources, ('watch', 'staffing'))
    if U['status'] != 'ok':
        values.update({'AQ_UTK_STATUS': 'aq-otillganglig', 'AQ_UTK_CLASS': '',
                       'AQ_UTK_DAG': '–', 'AQ_UTK_DAG_TITEL': UNREADABLE_WATCH,
                       'AQ_UTK_GRANSKAT': '–', 'AQ_UTK_GRANSKAT_TITEL': UNREADABLE_WATCH,
                       'AQ_UTK_RAPPORT_TITEL': UNREADABLE_WATCH, 'AQ_UTK_NAMN': '',
                       'AQ_UTK_VEM': '', 'AQ_UTK_VAD': '', 'AQ_UTK_UNDER': UNREADABLE_WATCH})
        rows['utkiken'] = [_rad('Läge', 'Bevakningen kunde inte läsas; inget visas som lugnt'),
                           _rad('Konfigurerad utförare', model + NOT_MODEL_CHOICE)]
        return
    running = U['running'] or 0
    planned, starts = U['next_planned'], U['starts']
    values['AQ_UTK_STATUS'] = ''
    values['AQ_UTK_CLASS'] = ('aq-kor' if running > 0 else
                              'aq-vantar' if U['waiting'] else 'aq-lugn')
    values['AQ_UTK_DAG'] = DATUM(planned).split(' ')[0] if planned else '–'
    values['AQ_UTK_DAG_TITEL'] = ('nästa omgång planerad ' + TID(planned) + ' · inte genomförd'
                                  if planned else 'ingen planerad omgång känd')
    reviewed = U['reviewed']
    if reviewed is None:
        values['AQ_UTK_GRANSKAT'] = 'inget'
        values['AQ_UTK_GRANSKAT_TITEL'] = granskat = 'inget granskat besked'
    else:
        decision = reviewed['decision'] if reviewed['decision'] is not None else 'beslut okänt'
        granskat = (TID(reviewed['at']) + ' · ' + decision
                    + (' · äldre än ett dygn' if reviewed['older_than_a_day'] else ''))
        values['AQ_UTK_GRANSKAT'] = DATUM(reviewed['at'])
        values['AQ_UTK_GRANSKAT_TITEL'] = 'senast granskade besked ' + granskat
    latest = U['latest']
    if latest is None:
        report = 'ingen rapport'
        values['AQ_UTK_RAPPORT_TITEL'] = 'ingen rapport'
    else:
        report = ((TID(latest['at']) if latest['at'] is not None else 'tid okänd') + ' · '
                  + latest['outcome'] + ('' if latest['cause'] is None
                                         else ' · ' + latest['cause']))
        values['AQ_UTK_RAPPORT_TITEL'] = 'senaste rapport ' + report
    if running > 0:
        values['AQ_UTK_NAMN'] = 'Bevakningen'
        values['AQ_UTK_VEM'] = 'utförare ej belagd'
        values['AQ_UTK_VAD'] = ('omgång startad ' + TID(starts[0]) if starts
                                else 'omgång pågår · starttid okänd')
    else:
        values['AQ_UTK_NAMN'] = values['AQ_UTK_VEM'] = values['AQ_UTK_VAD'] = ''
    if U['schedule'] == 'stoppat':
        under = 'stoppad'
    elif U['schedule'] == 'pausat':
        under = 'pausad'
    elif U['schedule'] == 'okänt':
        under = 'schemat är okänt'
    elif running > 0:
        under = 'omgång pågår'
    elif latest is not None and latest['cause'] is not None:
        under = 'senaste omgången otillräcklig' + ('' if not planned
                                                   else ' · nästa ' + TID(planned))
    elif U['waiting']:
        under = 'besked väntar på granskning'
    elif planned:
        under = 'nästa omgång ' + TID(planned)
    else:
        under = 'ingen planerad omgång känd'
    values['AQ_UTK_UNDER'] = under
    listed = [_rad('Schema', U['schedule']),
              _rad('Nästa omgång', 'planerad ' + TID(planned) + ' · inte genomförd' if planned
                   else 'ingen planerad tid känd'),
              _rad('Senaste starter', ', '.join(TID(start) for start in starts) if starts
                   else 'inga kända')]
    if running > 0:
        listed.append(_rad('Igång vid läsningen', ANTAL(running, '1 omgång', '%d omgångar')))
    listed.append(_rad('Senaste rapport', report))
    listed.append(_rad('Senast granskade besked', granskat))
    listed.append(_rad('Konfigurerad utförare', model + NOT_MODEL_CHOICE))
    rows['utkiken'] = listed


def _bordet(B, sources, waiting, values, rows):
    items = B['items']
    marks = (['aq-harbord'] if items else []) + ([] if B['status'] == 'ok'
                                                 else ['aq-ofullstandig'])
    values['AQ_BORD_STATUS'] = ' '.join(marks)
    for number in range(1, 5):
        item = items[number - 1] if len(items) >= number else None
        if item is None:
            values['AQ_BREV_%d_CLASS' % number] = 'aq-av'
            values['AQ_BREV_%d_TITEL' % number] = ''
            continue
        values['AQ_BREV_%d_CLASS' % number] = 'aq-pa'
        values['AQ_BREV_%d_TITEL' % number] = (
            KINDS.get(item['kind'], item['kind']) + ': ' + item['text']
            + ('' if item['since'] is None else ' · sedan ' + NÄR(item['since'])))
    values['AQ_BORD_ANTAL'] = str(len(items)) if items else ''
    values['AQ_BORD_FLER'] = '+%d' % (len(items) - 4) if len(items) > 4 else ''
    values['AQ_BORD_UNDER'] = waiting
    listed = [_rad(KINDS.get(item['kind'], item['kind'])
                   + ('' if item['since'] is None else ' · sedan ' + NÄR(item['since'])),
                   item['text'] + ' — ' + item['basis']) for item in items]
    if B['status'] != 'ok':
        listed.append(_rad('Läge', 'En källa kunde inte läsas; fler ärenden kan finnas'))
    elif not items:
        listed = [_rad('Läge', 'Inga ärenden väntar på dig')]
    rows['bordet'] = listed
    values['AQ_KALLA_BORDET'] = KÄLLA(sources, ('office', 'questions', 'watch'))


def _maskinrummet(S, R, sources, values, rows):
    """Configuration is never observed work: the technical records are named as records."""
    service = S['service']
    verified = service['verified']
    if service['state'] == 'igång':
        tjanst = 'tjänsten igång · %s av 3 verifierade' % verified
    elif service['state'] == 'delvis':
        tjanst = 'tjänsten delvis igång · %s av 3 verifierade' % verified
    elif verified == 0:
        tjanst = 'tjänsten okänd · ingen verifierad'
    else:
        tjanst = 'tjänsten kunde inte läsas'
    records = S['identity_records']
    tekniskt = ('tekniska poster okända' if records is None
                else ANTAL(records, '1 teknisk post, inte en agent',
                           '%d tekniska poster, inte agenter'))
    values['AQ_SOCKEL_CLASS'] = ('aq-igang' if service['state'] == 'igång' else
                                 'aq-delvis' if service['state'] == 'delvis' else 'aq-okand')
    values['AQ_SOCKEL_UNDER'] = tjanst + ' · ' + tekniskt
    values['AQ_SOCKEL_TITEL'] = tekniskt
    listed = [_rad('Tjänsten', tjanst + ('' if not service['config']
                                         else ' · konfiguration ' + service['config']))]
    if S['staffing']:
        listed += [_rad('Konfigurerad · ' + entry['role'],
                        MODELL(entry['executor'], entry['model'])) for entry in S['staffing']]
    else:
        listed.append(_rad('Konfigurerad bemanning', 'okänd'))
    listed.append(_rad('Konfigurerad · bevakningen',
                       MODELL(S['watch_staffing']['executor'], S['watch_staffing']['model'])
                       + NOT_MODEL_CHOICE))
    listed.append(_rad('Arbetar inte', 'okänt' if S['idle_tasks'] is None
                       else ANTAL(S['idle_tasks'], '1 uppdrag', '%d uppdrag')))
    listed.append(_rad('Pågår', 'okänt' if S['busy'] is None else
                       'inget' if S['busy'] == 0 else
                       ANTAL(S['busy'], '1 uppdrag', '%d uppdrag')))
    listed.append(_rad('Identitetsposter', tekniskt))
    listed.append(_rad('Revision', _revision(R)))
    rows['maskinrummet'] = listed
    values['AQ_KALLA_MASKINRUMMET'] = KÄLLA(sources, ('service', 'staffing', 'engine', 'release'))


def _revision(R):
    return ('okänd' if R['runtime'] is None
            else 'Runtime ' + R['runtime'] + ' · konfiguration ' + str(R['config']))


def _kallor(sources, R, rows):
    """When each source was read and when it becomes stale; the times are read times."""
    listed = []
    for name in SOURCES:
        source = sources[name]
        label = '<span class="aq-etikett">' + _escape(source['title']) + '</span>'
        if source['status'] == 'ok':
            listed.append('<li data-read-at="' + _escape(source['read_at'])
                          + '" data-stale-after="' + str(source['stale_after_seconds']) + '">'
                          + label + 'läst ' + _escape(TID(source['read_at']))
                          + ' · inaktuell efter ' + str(source['stale_after_seconds'] // 60)
                          + ' min</li>')
        else:
            listed.append('<li class="aq-otillganglig-kalla">' + label
                          + 'otillgänglig vid läsningen</li>')
    listed.append(_rad('Kontoret · revision', 'okänd' if R['office_main'] is None
                       else 'main ' + R['office_main'] + ' · ' + TID(R['office_main_date'])))
    listed.append(_rad('Runtime · revision', _revision(R)))
    rows['kallor'] = listed


def render(projection, jamforelse=None):
    """Fill SCEN from one projection. Pure: no file, clock, process or network, nothing mutated.

    With a comparison of two readings the page is the window's: both scripts, the window's policy and
    footer line, and a mark and a row on each task whose observed state differs from the previous
    reading. Without one, and with `None`, it is exactly the snapshot.
    """
    _validate(projection)
    if jamforelse is not None:
        _validate_jamforelse(jamforelse)
    sources, R = projection['sources'], projection['revisions']
    read_at = projection['read_at']
    limits = [sources[name]['stale_after_seconds'] for name in SOURCES
              if sources[name]['status'] == 'ok']
    waiting = _agare(projection['agarens_bord'])
    body = 'aq-provdata' if projection['provdata'] else ''
    if jamforelse is not None:
        body = (body + ' aq-fonsterlage').strip()
    values = {'AQ_CSP': csp() if jamforelse is None else fonster_csp(),
              'AQ_BODY_CLASS': body,
              'AQ_READ_AT': read_at,
              'AQ_STALE_AFTER': str(min(limits)) if limits else '0',
              'AQ_OBSERVERAT': TID(read_at), 'AQ_SENAST': TID(read_at),
              'AQ_ALDER_UTAN_SKRIPT': 'ålder okänd',
              'AQ_RUBRIK': _rubrik(projection, waiting)}
    values['AQ_ARIA'] = ('Aquarium' + (' med PROVDATA' if projection['provdata'] else '') + ': '
                         + values['AQ_RUBRIK'] + ', läst ' + TID(read_at))
    rows = {}
    _arkivet(projection['arkivet'], R, sources, _LOKALT(read_at), values, rows)
    _verkstaden(projection['verkstaden'], sources, values, rows, jamforelse)
    _utkiken(projection['utkiken'], sources, values, rows)
    _bordet(projection['agarens_bord'], sources, waiting, values, rows)
    _maskinrummet(projection['sockeln'], R, sources, values, rows)
    _kallor(sources, R, rows)
    return _fill(values, rows, jamforelse)


# --- command ----------------------------------------------------------------------


def _read(source):
    """Read one regular projection file through a no-follow open, bounded, as UTF-8 JSON."""
    fd = os.open(str(Path(source).absolute()), os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        # A directory opens but is no projection: check before anything is read.
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            _refuse()
        parts, size = [], 0
        while size <= MAX_BYTES:
            chunk = os.read(fd, 65536)
            if not chunk:
                break
            parts.append(chunk)
            size += len(chunk)
    finally:
        os.close(fd)
    if size > MAX_BYTES:
        _refuse()
    return json.loads(b''.join(parts).decode('utf-8'))


def _write(target, page):
    """Write one new page through an exclusive, no-follow open with mode 0600."""
    path = Path(target).absolute()
    if path.name in ('', '.', '..'):
        _refuse()
    parent = os.open(str(path.parent), os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        fd = os.open(path.name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600,
                     dir_fd=parent)
        with os.fdopen(fd, 'wb') as stream:
            os.fchmod(stream.fileno(), 0o600)
            stream.write(page.encode('utf-8'))
    finally:
        os.close(parent)


def main(argv=None):
    arguments = sys.argv[1:] if argv is None else argv
    try:
        if len(arguments) != 2:
            _refuse()
        page = render(_read(arguments[0]))
        _write(arguments[1], page)
        return 0
    except Exception:
        print(COMMAND_ERROR, file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
