"""Aquarium v0's scene: the work world the page is rendered into, held by the chain driver (AQUARIUM-V0-ARBETSVARLD-20260924).

SCEN is the static Swedish page: one continuous workshop floor seen from above with persistent places, Arkivet (delivered
volumes), Verkstaden (a board of tasks that do not work and three benches), Granskningen (the review desk), Utkiken (the
watch at the big window), Ägarens bord (letters and a mark only when something waits for the owner), a toned-down
Maskinrummet (the technical base) and a toned-down frosted room for interactive work that is not observed. Every shown
value is a {{AQ_...}} placeholder or an <!--AQ:LISTA:...--> list slot that the renderer fills with escaped text from a
display-safe projection (tools/aquarium.py); every state is a class that the renderer sets through a placeholder: a figure
is drawn only where a place carries the class aq-figur, which the renderer sets only for work the engine reading
evidences, and a place carries aq-otillganglig when its source could not be read. PROVDATA is marked once for the whole
page (body class aq-provdata). The page starts in the stale look (class aq-inaktuell: the world stands still and fades,
figures become outlines marked as last known, a banner says that this does not mean work has ended); only SKRIPT, placed
once at <!--AQ:SKRIPT--> and pinned by its SHA-256 in the page's Content-Security-Policy, compares the reading's time with
the viewer's clock and switches to the fresh look while the reading is younger than the given limit. Decorative motion
(daylight, plants) runs only in the fresh look and never with reduced motion. Each place links to a panel (:target) with
its rows and its source line. Nothing here reads, runs or changes anything. The renderer that fills SCEN is a separate
step (the Runtime task office-aquarium-scene-2) and keeps both constants unchanged; SKRIPT is unchanged from the diorama
template, byte for byte.
"""

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
<g class="aq-park {{AQ_PARK_1_CLASS}}" filter="url(#aq-skugga-s)"><rect x="435" y="154" width="120" height="30" rx="3"/><circle cx="495" cy="159" r="3" class="aq-nal"/><text x="442" y="174">{{AQ_PARK_1_NAMN}}</text><title>{{AQ_PARK_1_TITEL}}</title></g>
<g class="aq-park {{AQ_PARK_2_CLASS}}" filter="url(#aq-skugga-s)"><rect x="561" y="154" width="120" height="30" rx="3"/><circle cx="621" cy="159" r="3" class="aq-nal"/><text x="568" y="174">{{AQ_PARK_2_NAMN}}</text><title>{{AQ_PARK_2_TITEL}}</title></g>
<g class="aq-park {{AQ_PARK_3_CLASS}}" filter="url(#aq-skugga-s)"><rect x="687" y="154" width="120" height="30" rx="3"/><circle cx="747" cy="159" r="3" class="aq-nal"/><text x="694" y="174">{{AQ_PARK_3_NAMN}}</text><title>{{AQ_PARK_3_TITEL}}</title></g>
<g class="aq-park {{AQ_PARK_4_CLASS}}" filter="url(#aq-skugga-s)"><rect x="813" y="154" width="120" height="30" rx="3"/><circle cx="873" cy="159" r="3" class="aq-nal"/><text x="820" y="174">{{AQ_PARK_4_NAMN}}</text><title>{{AQ_PARK_4_TITEL}}</title></g>
<g class="aq-park {{AQ_PARK_5_CLASS}}" filter="url(#aq-skugga-s)"><rect x="435" y="190" width="120" height="30" rx="3"/><circle cx="495" cy="195" r="3" class="aq-nal"/><text x="442" y="210">{{AQ_PARK_5_NAMN}}</text><title>{{AQ_PARK_5_TITEL}}</title></g>
<g class="aq-park {{AQ_PARK_6_CLASS}}" filter="url(#aq-skugga-s)"><rect x="561" y="190" width="120" height="30" rx="3"/><circle cx="621" cy="195" r="3" class="aq-nal"/><text x="568" y="210">{{AQ_PARK_6_NAMN}}</text><title>{{AQ_PARK_6_TITEL}}</title></g>
<g class="aq-park {{AQ_PARK_7_CLASS}}" filter="url(#aq-skugga-s)"><rect x="687" y="190" width="120" height="30" rx="3"/><circle cx="747" cy="195" r="3" class="aq-nal"/><text x="694" y="210">{{AQ_PARK_7_NAMN}}</text><title>{{AQ_PARK_7_TITEL}}</title></g>
<g class="aq-park {{AQ_PARK_8_CLASS}}" filter="url(#aq-skugga-s)"><rect x="813" y="190" width="120" height="30" rx="3"/><circle cx="873" cy="195" r="3" class="aq-nal"/><text x="820" y="210">{{AQ_PARK_8_NAMN}}</text><title>{{AQ_PARK_8_TITEL}}</title></g>
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
<text x="60" y="884" class="aq-fot-text">Läsvy · startar, godkänner och ändrar ingenting · välj en plats för detaljer, källa och tid</text>
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
