# Förbättringspartnern — Projektkontorets interna samtalsyta

Johnny lämnar en tanke, skärmklipp, filer, en länk eller ett repo — utan analysprompt — och får ett
systemkunnigt, källbundet resonemang. Partnern fortsätter tidigare trådar, minns rättelser och beslut mellan
sessioner och bereder ett uppdrag till kontoret först när Johnny tydligt beställer genomförande. En lämnad
överlämning startar mottagarens session av sig själv (startvakten, se Överlämning). Uppdraget och gränserna står i
besluten FORBATTRINGSPARTNER-20260928 och FORBATTRINGSPARTNER-OVERLAMNING-AUTOSTART-20260929; planen äger nästa handling.

Tjänsten är också Nortropics gemensamma arbetsplats: samtalsytan är delen **Förbättringar** bredvid Hem, Kontoret
(Aquarium) och Kundstart, och `partner.py oppna` öppnar Hem. Se `tools/ARBETSPLATS.md` och beslutet ARBETSPLATS-20260929.

## Använda

```sh
python3 -B tools/partner.py start     # startar tjänsten på http://127.0.0.1:4760 (i bakgrunden)
python3 -B tools/partner.py oppna     # öppnar samtalsytan inloggad i webbläsaren
python3 -B tools/partner.py status    # kör den, vilken kod (main?) och var ligger datan
python3 -B tools/partner.py stopp     # pågående arbete avbryts, journalförs och återupptas vid nästa start
python3 -B tools/partner.py autostart # visar hur ägaren gör tjänsten bestående (skriver ingenting)
python3 -B tools/partner.py app       # skapar ~/Applications/Nortropic.app: ett klick startar och öppnar (se ARBETSPLATS.md)
```

Python 3.9 eller senare räcker (macOS egen `python3` fungerar).

Ytan har ungefär Claude-appens form: sidomeny med "Ny tråd", sökning, trådarna och dina verktyg; en tom tråd visar
en hälsning med inmatningsrutan i mitten och förslag under; i en tråd står svaren i en kolumn och rutan längst ned.
Modell och ansträngning väljer du i rutan: klicka på "Opus 5.5 · high" (↑↓ modell, ←→ ansträngning, Enter, Esc)
eller skriv `/model`, `/model sonnet` eller `/effort max`. Valet sparas i `data/installningar.json` och gäller från
nästa svar i alla trådar; en pågående körning påverkas inte, och kommandona skickas aldrig till partnern. Varje svar
visar vilken modell och ansträngning det kördes med.

I rutan: skriv, klistra in bilder (⌘V), släpp flera filer eller bifoga med "+". Enter skickar, Skift+Enter ger ny
rad. Varje kodblock i ett svar har en knapp "Kopiera" som kopierar blockets text exakt (utan språkmarkör), och under
varje svar kopierar en knapp hela svaret som markdown, ordagrant. Knapparna nås med Tab och fungerar med Enter och
mellanslag; ett kort "Kopierat" bekräftar. Går urklippet inte att använda prövas den äldre kopieringen ur en dold
ruta med samma text; går inte heller den markeras texten synligt (för hela svaret dess markdown-källa i en
skrivskyddad ruta) och ytan säger att den ska kopieras med ⌘C. Växeln "Bara spara" (eller att skriva "bara spara") sparar utan analys. Medan partnern arbetar kan ett nytt inspel skickas efter svaret eller "Skicka och avbryt
pågående" (en sen rättelse). Sökfältet hittar tidigare resonemang och underlag utan modellanrop. "Bestående
förståelse" visar vad som sparats, vad som ersatts och av vad. "Tjänst och källor" visar kod, modell, förbrukning
och källtäckning.

Tjänsten körs lokalt på Johnnys Mac och nås bara när den är igång; det är ett synligt beroende. Den startas inte
automatiskt vid inloggning. Att göra den bestående kräver en LaunchAgent som ägaren själv aktiverar (hanterad
policy nekar `launchctl` för sessioner): `partner.py autostart` skriver ut filen och de två kommandona.

## Vad partnern gör utan särskilda instruktioner

Rollen (`partnern/roll.md`) och en kort Nortropic-orientering (`partnern/orientering.md`) följer med varje tur,
tillsammans med ett läge som servern räknar fram: vilken kod tjänsten kör, trådens "Där vi är" (märkt som
partnerns egen sammanfattning), kopplade trådar, gällande förståelse, källtäckning och senast lästa systemläge.
Gällande förståelse har två delar: Johnnys egna rättelser och beslut i sin helhet, och partnerns egna tidigare
bedömningar, märkta som sådana. Bedömningarna står i sin helhet bara när de hör till tråden, en kopplad tråd
eller liknar det Johnny tar upp i turen; övriga står som en rad var, och det som inte ryms sägs uttryckligen.
Så styr inte äldre domar från andra trådar varje nytt samtal. Partnern söker och läser själv
fördjupning med sina verktyg. Den svarar proportionerligt, resonerar för och emot, kan avråda, sparar det som
ska bära framåt och håller trådens läge aktuellt.

## Delar

| Del | Fil | Status |
| --- | --- | --- |
| Lager: journal (original, append-only, fsync), innehållsadresserade bilagor, härlett index | `partnern/lager.py` | Indexet byggs om ur journalen |
| Bilagor: typ ur innehållet, textlager (pdftotext, textutil, zip-XML), sidbilder (pdftoppm), modellbild (sips) | `partnern/bilagor.py` | Ljud, video och okänt sparas men märks olästa |
| Källindex: Improvements-korpusen, ägarens sparade ord och beställningar, kontorets beslut/plan, andra repons dokument, förberedelsens syntes | `partnern/kallor.py` | Byggs om vid start och inom tio minuter när repons lokala origin/main, de sparade ägarorden eller korpusens manifest ändras (`partner.py index` gör det direkt); privata filer tvättas från hemligheter |
| Systemläge: git (origin/main, primärutcheckning), planen på main, Runtimes drift genom Aquariums läsning, öppna PR | `partnern/systemlage.py` | Alltid med lästid och ålder |
| Verktyg för modellen: sök, öppna i sammanhang, bilaga, systemläge, repo, GitHub (GET), förståelse, resonemang, tråd, bered_uppdrag, utred | `partnern/verktyg.py` | Genom MCP-bryggan, per körning |
| Agentloop: Claude Code headless (`claude -p`, dvs. Agent SDK via CLI) i begränsat läge | `partnern/agent.py` | Se modell och drift nedan |
| Webbkrok och destinationspolicy | `partnern/krok.py`, `partnern/webbpolicy.py` | Servern avgör varje webbanrop |
| Bakgrundsutredningar | `partnern/jobb.py` | Journalförda, återupptas efter omstart |
| Överlämning till kontoret | `partnern/overlamning.py` | Paket i `evidence/nasta-uppdrag/local/partner-OVL-…/` med AP-06-utkast, ett per mottagare |
| Startvakt | `partnern/start.py` | Startar mottagarens session för en lämnad överlämning; väntar synligt när skrivplatsen är upptagen eller kvoten slut |
| Server och samtalsyta | `partnern/server.py`, `partnern/ui/` | 127.0.0.1, inloggning, svenska |

## Modell, drift och gränser

Agentloopen är Claude Code i headless-läge på Johnnys befintliga Claude Code-inloggning (Max-abonnemanget) —
samma väg som Runtime redan använder. Ingen ny leverantör, API-nyckel eller köpta krediter. Varje tur körs som en
egen process i `data/arbetsyta/` med `--restricted`, `--strict-mcp-config`, utan auto-minne och CLAUDE.md, med
verktygen WebFetch, WebSearch, en underagent ("utredare") och partnerns egna verktyg; inga fil-, skal- eller
skrivverktyg. Standard är huvudmodellen `claude-opus-5-5` med ansträngningen `high` och utredaren `sonnet`. Johnny byter
huvudmodell och ansträngning i ytan (`/model`); valbara är Opus 5.5, Fable 5.1 (egen kvot), Sonnet 5, Opus 5 och Haiku
4.5, med ansträngningen low, medium, high, xhigh eller max. Valet och utredarens modell står i
`data/installningar.json` (`{"modell": {"huvud": "…", "anstrangning": "…"}}`).

Verkställda gränser (samma fil, `gransar`): två samtidiga modellkörningar, 15 min och 40 verktygssteg per tur,
30 min och 150 verktygssteg per bakgrundsutredning, 8 USD listprisvärde per körning (`--max-budget-usd`), 150
körningar och 250 USD listprisvärde per dygn. Listprisvärdet
är Claude Codes egen uppskattning, inte en faktura: förbrukningen är abonnemangets kvot. Varje tur journalför
tokens, tid, omförsök och modell. Sparande, sökning och öppning av källor anropar aldrig en modell.

Claude Code sparar modellens egen sessionsfil under `~/.claude/projects/<arbetsyta>/`; den är en cache för
trådens modellkontext. Partnerns journal är originalet: saknas sessionen startar en ny med trådens historik ur
journalen.

## Data och säkerhet

Datan ligger privat i `evidence/partner/local/` (git-ignorerad, katalog 0700, filer 0600): `journal/`, `blobs/`,
`harlett/`, `turer/` (per körning: systemprompt, rå ström, delsvar), `index.sqlite`. Inloggningsnyckeln och
kaknyckeln ligger i `~/.nortropic-hemligheter/partner/`. Servern svarar bara på 127.0.0.1 och godkända
Host-namn; API:t kräver inloggningskaka (HttpOnly, SameSite=Strict) och ett eget huvud på skrivningar;
bryggan och kroken kräver en körningsnyckel som bara gäller under körningen. Bilagor visas med
`Content-Security-Policy: sandbox`; SVG och okända typer laddas bara ned.

Källor är material, aldrig instruktioner. Deterministiska spärrar:

- Ägarens ord (`agarens_ord`) kräver att citatet är en eller flera hela satser, minst tre ord, som Johnny själv
  skrivit i samma tråd: ur ett inspel, eller ur flera av trådens tre senaste inspel i tidsordning. Text i bilagor,
  källor, andra trådar och svar kan aldrig bli ägarens ord, och ett lösryckt ord räcker inte. Beslut och rättelser
  kräver ägarens ord; en post som bygger på ägarens ord kan bara ersättas av nyare ord från ägaren.
- En beställning (`bered_uppdrag`) ska stå bland trådens tre senaste inspel, ur ett eller flera av dem i
  tidsordning, så att en beställning och Johnnys avgränsning i nästa meddelande bärs tillsammans. Den ska innehålla
  en sats med ett beställningsord som verb ("genomför", "kör", "bygg", "beställ" …) som varken är en fråga eller
  negerad i sin egen sats. En kort hel sats räcker ("genomför båda", "kör det"). En negation fäller bara när den
  gäller beställningsordet ("genomför inte", "jag vill inte att du genomför"); ett "inte" längre bort är en
  avgränsning ("beställ båda men det är till riktiga kunder, inte fiktiva test byggen"). Är något beställningsord i
  citatet negerat nekas hela citatet. "ja", "precis" och "låter bra" blir aldrig ett uppdrag, och samma inspel ger
  aldrig två överlämningar. Nekas ett citat säger felbeskedet vilken regel som fällde (för kort, saknar
  beställningsord, negation, fråga, för gammal eller inte funnen), och paketets `AGARENS-ORD.md` innehåller alla
  citerade inspel ordagrant. Samma beställning kan ge en överlämning per mottagare (kontoret, Digitala, Runtime,
  Kundstart) men aldrig två till samma mottagare. Medan en överlämning i tråden är öppen (lämnad, mottagen,
  startad) skapas ingen ny till samma mottagare, om inte partnern uttryckligen anger att Johnny beställt något
  annat; det nya paketet pekar då ut vilket det skiljer sig från. Fäller en av de två spärrarna säger svaret vilken
  spärr och vilken befintlig överlämning.
- WebFetch går bara till publika värdar som Johnny länkat i tråden, som finns bland träffarna från en webbsökning
  under samma körning, eller som står i en kort lista över exakta dokumentationsvärdar där ingen utomstående kan
  publicera innehåll eller läsa loggar (de hämtas utan frågedel). Länkar i bilagor, hämtade sidor och andra
  verktygssvar gör aldrig en värd tillåten. En adress som bär en annan adress — en validerare, ett arkiv eller en
  proxy som hämtar något åt en — hämtas aldrig. Lokala adresser, långa sökvägs- eller frågedelar och adresser eller
  sökfrågor med hemlighets- eller personuppgiftsliknande värden nekas, och en sökning med `site:` görs bara mot
  dokumentationsvärdarna och Johnnys länkar. GitHub läses med verktyget `github` (API, endast GET), inte med WebFetch.
- Körningsnyckeln för bryggan och kroken går bara genom processmiljön, aldrig i processargumenten.

**Kända gränser.** Att den sparade förståelsetexten stämmer med det citerade ägarordet prövas inte maskinellt;
citatet visas alltid bredvid posten, och beställningsregeln är ordbaserad (en ovanlig formulering kan nekas eller
släppas igenom; partnern frågar då hellre). Spärren prövar att citatet är Johnnys egen beställning, inte att han
inte har ångrat sig i ett senare meddelande; det bedömer partnern. Värdar som en webbsökning returnerat blir hämtbara under körningen: en
planterad instruktion som får modellen att söka fram en viss webbplats kan göra den hämtbar, men bara med korta
adresser utan inbäddade adresser, hemligheter eller personuppgifter. Inloggningskakan är tillståndslös i 30 dagar (utloggning rensar bara
webbläsaren) och spärren efter åtta felaktiga inloggningar gäller alla i tio minuter. Webbpolicyns
adresskontroller kan neka en vanlig länk vars frågedel liknar en domän (t.ex. `?utm_source=example.com`); de
felar hellre stängt. Bilagor läses av lokala
verktyg (pdftotext, textutil, sips, zip-XML). Arbete som avbröts av en omstart återupptas automatiskt bara om det
startade inom den senaste timmen; äldre står kvar som avbrutet med en knapp. En tur som stoppades av dygnsgränsen
tas om först när Johnny trycker Återuppta. Svaret är huvudagentens text; en kort mellanrad som följs av fler
verktygsanrop och ett längre svar räknas till arbetet och står bara i delsvaret. Partnerns omdöme prövas av
slutproven (verkliga körningar) och Johnnys rättelser, inte av de deterministiska proven.

## Källtäckning

Improvements-korpusen är förberedelsekampanjens fångst (källgräns 2026-09-19 14:12Z): 61 samtal, 3 111
meddelanden, 3 projektfiler och 132 unika bilagefiler; 3 registrerade bilagor saknar bytes och 4 är historiskt
otillgängliga. Samtal i ChatGPT-projektet efter källgränsen finns inte i korpusen. Tjänsten har ingen
direktåtkomst till ChatGPT. Senare arbetsordrar och ägarord finns där sessioner sparat dem ordagrant i kontorets
privata bevis. En ny fångst genom befintlig Intake-väg (Chrome-session med ChatGPT-inloggning) läggs in genom att
peka `PARTNER_IMPROVEMENTS` på den nya korpusen och starta om tjänsten (eller köra `partner.py index`). Ägarord och
beställningar som sessioner sparar blir sökbara inom tio minuter. Nya beslut och planändringar blir det när
primärutcheckningens origin/main har uppdaterats; tjänsten hämtar inte själv från GitHub, men sessioner gör det vid
start (`ingang.py`) och efter varje publicering. Repo-verktygen läser den senast hämtade origin/main.

## Överlämning

När Johnny tydligt beställer genomförande skriver partnern ett paket per mottagare i kontorets beställningsväg:
`ARBETSORDER.md` (sammanställd, märkt som sådan), `AGARENS-ORD.md` (de citerade inspelen ordagrant), hashade
underlagsfiler, `OVERLAMNING.json` och ett AP-06-utkast (`ap06/utkast/`) med sina luckor. Status "lämnad";
aktuell status är sista raden i paketets `KVITTENS.jsonl`, och `overlamningar` visar den även när tjänsten inte
kör. AP-06-utkastets behörighet bygger på det ordbaserade citatet; mottagaren läser `AGARENS-ORD.md`.

Id:t är `OVL-<datum>-<inspel>`; en andra mottagare ur samma inspel får mottagarens kortnamn som tillägg
(`OVL-…-runtime`), och står en katalog redan på ett id (till exempel en rest efter ett avbrott) tas nästa lediga id
med löpnummer. Ett befintligt paket byter aldrig namn, flyttas aldrig och skrivs aldrig över.

**Startvakten** (`partnern/start.py`) gör att en lämnad överlämning startar arbetet av sig själv. Varje minut, och
direkt när tjänsten startar, går den igenom öppna överlämningar. För en lämnad överlämning som ingen har kvitterat
startar den en session i mottagarens repo: kontorets primärutcheckning för kontorets kedjedrivare,
annars `nortropic-digitala`, `Nortropic Runtime` eller `nortropic-kundstart`. Sessionen får en fast instruktion.
Den börjar utan skrivningar och kontrollerar Git, planen och sina grannar (ListAgents). Den kvitterar `mottagen`,
läser planen, `AGARENS-ORD.md` och `ARBETSORDER.md`, kvitterar `startad` och arbetar inom gällande mandat och plan med
separat granskning och skyddad integration. Den avslutar med `levererad` eller `avslagen`. Nya kostnader, konton,
aktivering av övergångar och publika lanseringar skriver den i planens ÄGARENS TUR i stället för att göra dem.
Paketet bär instruktionens material, men bara Johnnys ord är beslut.

- **En session per överlämning.** För Claude härleds sessionens id ur överlämningens id; för Codex binder trådens id
  i paketets första ström. Startbeslutet tas under ett fillås i paketet, och en levande session startas aldrig om,
  inte heller efter en omstart av tjänsten: den känns igen på sin process, vars kommandorad bär paketets sökväg. En session som
  stoppades av kvot, åtkomst eller ett avbrott (till exempel en omstart av datorn) fortsätter i samma session. Efter
  ett fel eller ett avslut startas ingen ny session. En session som kvitterat `levererad` eller `avslagen` följs ändå
  upp: startvakten skriver `klar` (eller utfallet) i `START.jsonl` och hämtar den avslutade processen, också när
  kvittensen lästes före varvet eller tjänsten har startats om sedan sessionen avslutades.
- **En skrivande session per ansvar.** Starten väntar, med skälet synligt, så länge någon annan skriver i
  mottagarens repo. Det gäller en Claude Code- eller Codex-process med arbetskatalog i repot, ändringar i
  primärutcheckningen, en worktree med ändringar från de senaste 30 minuterna och startvaktens egen session för
  en annan överlämning i samma repo. Också en fortsättning väntar på en annan skrivare; där räknas inte
  worktree-regeln, eftersom sessionens egna worktrees inte är en annan skrivare. Vakten tar aldrig över och startar
  aldrig bredvid.
- **Utföraren väljs som i dag:** i Runtimes bemanning, rollen `driver`, så som Johnny valt den i Runtimes modellval
  (D028–D030). Bemanningen läses genom Aquariums befintliga sond. Claude Code körs med Runtimes fastlåsta
  `.runtime/bin/claude-2.1.257` i behörighetsläget `auto`; i dag anger bemanningen Claude med modellen
  `claude-opus-5`. Codex körs med den fastlåsta `.runtime/bin/codex-0.155.1` (`exec --json --approve-for-me`, och
  `exec resume <tråd>` för att fortsätta). Båda får bemanningens modell och ansträngningen `high`, och binärens
  kontrollsumma prövas mot den som Runtime själv binder före varje start. De kör på Johnnys abonnemang (Claude
  Code-inloggningen respektive Codex ChatGPT-inloggning) i en miljö som byggs från grunden utan API-nycklar. Det finns
  ingen reservväg. Går bemanningen inte att läsa väntar starten synligt. Saknas kvot eller åtkomst väntar den också
  synligt och fortsätter samma session, med samma utförare och modell, tidigast en timme senare. Ett senare byte i
  bemanningen gäller bara nya överlämningar.
- **Tak:** högst sex nya automatiska starter per dygn (UTC, `gransar.startvakt_per_dygn` i
  `data/installningar.json`). En fortsättning av samma session räknas inte. Startvakten stängs av med
  `{"startvakt": {"pa": false}}` i samma fil, och ansträngningen kan ändras där (`{"startvakt": {"anstrangning": "…"}}`).
- **Sover datorn eller kör inte tjänsten** sker starten när tjänsten kör igen; ingen överlämning hoppas över.
- Startvakten kör bara i den ordinarie tjänsten, aldrig i en prov- eller utvecklingsinstans (egen `PARTNER_DATA`,
  `PARTNER_PORT` eller `PARTNER_PROV_DOLJ`), och den startar ingenting annat än mottagarsessioner.

Varje steg står i paketets `START.jsonl` (bara tillägg: `vantar`, `hindrad`, `startad`, `avbruten`, `klar`,
`avslutad`, `misslyckad`, med skäl och en fast orsakskod) och i partnerns journal. Sessionens ström ligger i
paketets `session/`; för Codex binder trådens id i den första strömmen sessionen till överlämningen. Tråden och "Överlämningar" visar mottagaren, statusen och vilken session som startade och när,
eller vad starten väntar på. Aquarium visar en rad per öppen överlämning, lägger levererade och avslagna i Arkivet och
ett misslyckat eller hindrat startförsök på Ägarens bord (se `tools/AQUARIUM.md`).

Mottagaren kvitterar (startvaktens sessioner gör det själva):

```sh
python3 -B tools/partner.py overlamningar     # mottagare, status, senaste kvittens, session och startvaktens läge
python3 -B tools/partner.py kvittera OVL-… mottagen --av "<session>"
python3 -B tools/partner.py kvittera OVL-… levererad --av "<session>" --bevis "<PR eller commit>"
python3 -B tools/partner.py kvittera OVL-… avslagen --av "<session>" --bevis "<skäl>"
```

**Kända gränser för startvakten.** Den ser andra sessioner genom deras processer, Git och worktrees. En session vars
arbetskatalog ligger ovanför repot, till exempel en VS Code-session som öppnats i `~/nortropic-repos`, syns bara
genom sina ändringar. Därför kontrollerar mottagarsessionen också sina grannar själv. Går `lsof` inte att köra
återstår bara kontrollerna med Git. Codex har inte ListAgents; en Codex-session kontrollerar Git och worktrees.
Codex-vägen är prövad med en fejkad `codex` och mot den fastlåsta binärens händelseformat, men ingen verklig
Codex-session har startats av startvakten så länge bemanningen anger Claude. En session som avslutas utan leverans
lämnar överlämningen öppen med planen som återupptagningspunkt; startvakten startar ingen ny, utan nästa steg tas av
Johnny eller en session han startar.

En provinstans (egen `PARTNER_DATA`, `PARTNER_PORT` och `PARTNER_HEMLIGHETER` samt `PARTNER_PROV_DOLJ`) skriver sina
paket i sin egen data (`overlamningar/`), inte i beställningsvägen: den vanliga tjänsten indexerar `AGARENS-ORD.md`
där som Johnnys ord, och provtext i hans namn får aldrig hamna där.

## Prov

`python3 -B -m unittest tools.test_partner` kör en riktig server i processen mot en fejkad `claude` som talar
Claude Codes strömformat, startar den riktiga MCP-bryggan och kör den riktiga webbkroken: lager och återbyggnad,
inloggning/värd/ursprung, bilagetyper och säker visning, avbruten uppladdning, sparat före modellen, bara spara,
idempotenta återförsök, sessionsfortsättning och återskapad historik, avbrott före och under körning, sen
rättelse, bara spara med avbrott, ordnat stopp och krasch mitt i arbetet (tur och utredning), upplockning av
sparade inspel, verktygsgränser (stegtak per körningstyp), ägarens-ord-spärren och rättelsens företräde, lägets
uppdelning i Johnnys ord och partnerns egna bedömningar, mellanrader utanför svaret, samtalets alla bilagor och
läst andel vid öppning, ÄGARENS TUR läst som Aquarium, överlämning utan dubbletter (samma inspel och öppen
överlämning) och med kvittens, en överlämning per mottagare ur samma meddelande med egna id utan att ett befintligt
paket flyttas, webbkroken med sökträffar och planterade länkar, bakgrundsutredning, provläge och dygnsgräns.
Startvakten prövas med en fejkad mottagarsession som kör det riktiga kvitteringskommandot ur sin instruktion: exakt
en session per överlämning (även efter en omstart av tjänsten), väntan när skrivplatsen är upptagen och sedan start,
egen session i samma repo och dygnstaket, kvot och saknad inloggning med synlig väntan och samma session, Codex ur
bemanningen med kvot och fortsättning i samma tråd utan byte när bemanningen ändras, en levande Codex-session som
känns igen efter en omstart av vakten, ett kvotbesked utan avslutat varv, en fortsättning som väntar på en annan
skrivare, oläst bemanning utan reservväg,
fel och avbrott utan en andra session, ändrad binär, att prov- och utvecklingsinstanser aldrig startar något och att
processer, färska worktrees och raderade arbetskataloger bedöms rätt. Kopieringen prövas i en riktig webbläsare
(se beslutet).
