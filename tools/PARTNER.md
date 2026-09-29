# Förbättringspartnern — Projektkontorets interna samtalsyta

Johnny lämnar en tanke, skärmklipp, filer, en länk eller ett repo — utan analysprompt — och får ett
systemkunnigt, källbundet resonemang. Partnern fortsätter tidigare trådar, minns rättelser och beslut mellan
sessioner och bereder en beställning till kontoret först när Johnny beställer: hans "beställ" ger en vilande
beställning i backloggen, och för genomförande lämnas den bara när han uttryckligen säger det. En lämnad överlämning
startar mottagarens session av sig själv (startvakten, se Överlämning); en vilande gör det aldrig. Ett repo eller
verktyg som Johnny lämnar läses i original och i sin helhet (se Läsning i original). Uppdraget och gränserna står i
besluten FORBATTRINGSPARTNER-20260928, FORBATTRINGSPARTNER-OVERLAMNING-AUTOSTART-20260929 och
FORBATTRINGSPARTNER-BACKLOG-20260929; planen äger nästa handling.

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

Ytan har ungefär Claude-appens form: sidomeny med "Ny tråd", "Backlog" och trådarna; en tom tråd visar
en hälsning med inmatningsrutan i mitten och förslag under; i en tråd står svaren i en kolumn och rutan längst ned.
Modell och ansträngning väljer du i rutan: klicka på "Opus 5.5 · high" (↑↓ modell, ←→ ansträngning, Enter, Esc)
eller skriv `/model`, `/model sonnet` eller `/effort max`. Valet sparas i `data/installningar.json` och gäller från
nästa svar i alla trådar; en pågående körning påverkas inte, och kommandona skickas aldrig till partnern. Varje svar
visar vilken modell och ansträngning det kördes med. Samma val finns i arbetsplatsens Flödet (`/flodet`, se
`tools/ARBETSPLATS.md`), tillsammans med Nortropics övriga modellval.

I rutan: skriv, klistra in bilder (⌘V), släpp flera filer eller bifoga med "+". Enter skickar, Skift+Enter ger ny
rad. Varje kodblock i ett svar har en knapp "Kopiera" som kopierar blockets text exakt (utan språkmarkör), och under
varje svar kopierar en knapp hela svaret som markdown, ordagrant. Knapparna nås med Tab och fungerar med Enter och
mellanslag; ett kort "Kopierat" bekräftar. Går urklippet inte att använda prövas den äldre kopieringen ur en dold
ruta med samma text; går inte heller den markeras texten synligt (för hela svaret dess markdown-källa i en
skrivskyddad ruta) och ytan säger att den ska kopieras med ⌘C. Växeln "Bara spara" (eller att skriva "bara spara") sparar utan analys. Medan partnern arbetar kan ett nytt inspel skickas efter svaret eller "Skicka och avbryt
pågående" (en sen rättelse). Sidomenyn har Ny tråd, Backlog (tidigare Överlämningar, se Överlämning) och trådarna.
Sökfältet, "Bestående förståelse"
och "Tjänst och källor" togs bort ur menyn på ägarens besked (HEM-RUTOR-20260929). Partnern söker och sparar sin
förståelse som förut, en sparad punkt öppnas från sin notis i tråden (till exempel "Sparat som F-26"), och
`/api/sok`, `/api/forstaelse` och `/api/lage` svarar som förut.

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
| Lager: journal (original, append-only utom när ägaren raderar en tråd, fsync), innehållsadresserade bilagor, härlett index | `partnern/lager.py` | Indexet byggs om ur journalen |
| Bilagor: typ ur innehållet, textlager (pdftotext, textutil, zip-XML), sidbilder (pdftoppm), modellbild (sips) | `partnern/bilagor.py` | Ljud, video och okänt sparas men märks olästa |
| Källindex: Improvements-korpusen, ägarens sparade ord och beställningar, kontorets beslut/plan, andra repons dokument, förberedelsens syntes | `partnern/kallor.py` | Byggs om vid start och inom tio minuter när repons lokala origin/main, de sparade ägarorden eller korpusens manifest ändras (`partner.py index` gör det direkt); privata filer tvättas från hemligheter |
| Systemläge: git (origin/main, primärutcheckning), planen på main, Runtimes drift genom Aquariums läsning, öppna PR | `partnern/systemlage.py` | Alltid med lästid och ålder |
| Verktyg för modellen: sök, öppna i sammanhang, bilaga, systemläge, repo, GitHub (GET, i delar), förståelse, resonemang, tråd, backlog, bered_uppdrag, backlog_beslut, utred | `partnern/verktyg.py` | Genom MCP-bryggan, per körning |
| Agentloop: Claude Code headless (`claude -p`, dvs. Agent SDK via CLI) i begränsat läge | `partnern/agent.py` | Se modell och drift nedan |
| Webbkrok och destinationspolicy | `partnern/krok.py`, `partnern/webbpolicy.py` | Servern avgör varje webbanrop |
| Bakgrundsutredningar | `partnern/jobb.py` | Journalförda, återupptas efter omstart |
| Överlämning till kontoret och backloggen | `partnern/overlamning.py` | Paket i `evidence/nasta-uppdrag/local/partner-OVL-…/`, vilande eller lämnat, med krav, prov, märkning och AP-06-utkast, ett per mottagare |
| Startvakt | `partnern/start.py` | Startar mottagarens session för en lämnad överlämning, aldrig för en vilande; väntar synligt när skrivplatsen är upptagen eller kvoten slut |
| Server och samtalsyta | `partnern/server.py`, `partnern/ui/` | 127.0.0.1, inloggning, svenska |

## Modell, drift och gränser

Agentloopen är Claude Code i headless-läge på Johnnys befintliga Claude Code-inloggning (Max-abonnemanget) —
samma väg som Runtime redan använder. Ingen ny leverantör, API-nyckel eller köpta krediter. Varje tur körs som en
egen process i `data/arbetsyta/` med `--restricted`, `--strict-mcp-config`, utan auto-minne och CLAUDE.md, med
verktygen WebFetch, WebSearch, en underagent ("utredare") och partnerns egna verktyg; inga fil-, skal- eller
skrivverktyg. En modell och en ansträngning gäller allt (Johnnys besked 2026-09-29): svaret, utredaren och de
registrerade utredningarna kör det Johnny har valt. Standard är `claude-opus-5-5` med ansträngningen `high`. Utredaren
får samma modell och ansträngning i sin definition (`--agents`), och kroken nekar ett anrop som väljer en annan
agenttyp (till exempel en inbyggd agent med egen standardmodell) eller en annan modell. Johnny byter modell och
ansträngning i ytan (`/model`) eller i Flödet; valbara är Opus 5.5, Fable 5.1 (egen kvot), Sonnet 5, Opus 5 och Haiku
4.5, med ansträngningen low, medium, high, xhigh eller max. Finns en mätning (`python3 -B tools/partner.py matmodeller`,
kvittot `data/modellmatning.json`) erbjuds bara modellerna som fungerade i Johnnys Claude Code. Valet står i
`data/installningar.json`
(`{"modell": {"huvud": "…", "anstrangning": "…"}}`); en äldre egen utredarmodell där läses inte. Startvaktens
mottagarsessioner i andra repon kör Runtimes bemanning (rollen driver), se Startvakten.

Ägarbeslut 2026-09-29: förbättringspartnern har ingen användningsgräns. Inget dygnstak på antal körningar, inget
stegtak per tur eller bakgrundsutredning, ingen kostnadsspärr (`--max-turns` och `--max-budget-usd` skickas inte
längre till Claude Code). Vi har abonnemang, inget per-token-pris, så ett tak i USD eller i "listprisvärde" vore ett
tak mot ingenting — listprisvärdet (per tur och summerat per dygn i ytan) är bara Claude Codes egen uppskattning,
inte en faktura, och redovisas rent informativt. Förbrukningen som faktiskt kan ta slut är abonnemangets egen kvot,
vilket i så fall syns som ett vanligt "begränsat"-svar från körningen själv.

Kvar i `gransar`, och inget av det stoppar en tur för att mycket har körts: två samtidiga modellkörningar
(`samtidiga_korningar`; en tredje väntar på ledig plats och nekas aldrig), en hangvakt på 4 h per tur / 12 h per
bakgrundsutredning (`tur_max_sekunder`/`jobb_max_sekunder`) som bara fångar en process som blivit hängande — satt
långt bortom vad ett verkligt, aktivt arbete tar — och inmatningens storlek: högst 60 000 tecken och 20 bilagor per
inspel och högst 40 MB per fil (`inspel_max_tecken`, `inspel_max_bilagor`, `bilaga_max_byte`). Därutöver har
startvakten ett eget tak på sex nya automatiska starter per dygn (`startvakt_per_dygn`, se Startvakten nedan); det
gäller sessioner som partnern själv startar i andra repon. Varje tur journalför tokens, tid, omförsök och modell.
Sparande, sökning och öppning av källor anropar aldrig en modell.

Claude Code sparar modellens egen sessionsfil under `~/.claude/projects/<arbetsyta>/`; den är en cache för
trådens modellkontext. Partnerns journal är originalet: saknas sessionen startar en ny med trådens historik ur
journalen.

En tråd raderas för gott med papperskorgen på dess rad i listan och "Radera" i rutan som frågar
(RADERA-TRAD-20260929). Då försvinner trådens inspel, turer, resonemang och utredningar ur journalen, och
kopplingar till och från tråden. Journalen skrivs om atomärt, och indexet byggs om. Med dem försvinner också:
- turernas och utredningarnas kataloger under `turer/`;
- bilagor som ingen annan rad nämner, med sina härledda filer;
- Claude Codes sessionsfiler för trådens sessioner, om ingen kvarvarande rad nämner sessionen.

Filerna tas bort före journalen. En krasch mitt i raderingen lämnar därför antingen tråden kvar, så att den kan
raderas igen, eller en journal utan tråden, som indexet följer vid nästa start. Sparad förståelse ur tråden och
överlämningar som redan lämnats ligger kvar, och en rad `trad_raderad` utan innehåll visar att tråden fanns. Medan
partnern arbetar i tråden vägras raderingen, och en köad utredning startar antingen före raderingen eller inte alls.
Säkerhetskopior utanför tjänsten, till exempel Time Machine, rör den inte.

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
  spärr och vilken befintlig överlämning. En vilande beställning räknas som öppen i båda spärrarna.
- Johnnys "beställ" räcker för en vilande beställning (`vilande: true`). För genomförande (`vilande: false`) krävs att
  hans ord uttryckligen beställer det: ett beställningsord utom "beställ" och "bereda", varken negerat eller i en
  fråga; säger han "vilande" eller "backlog" blir den alltid vilande. Annars nekas anropet med besked om att lägga
  den som vilande.
- En vilande beställning släpps eller avslås bara på Johnnys ord i tråden (`backlog_beslut`): hans hela satser ur
  trådens tre senaste inspel, med ett ord för beslutet (släpp, genomför, kör, starta … respektive avslå, stryk, ta
  bort …) som varken är negerat eller en fråga, och med överlämningens id. Hans ord sparas ordagrant i en egen fil i
  paketet (`AGARENS-ORD-SLAPP-…` eller `AGARENS-ORD-AVSLAG-…`); resten av paketet lämnas orört. Mottagarens
  `kvittera` vägrar en vilande överlämning, och en kvittensrad väcker den aldrig.
- Underlag som inte går att öppna tappas inte tyst: `bered_uppdrag` vägrar och säger vilken post som föll, eller
  skapar beställningen med `godta_olost_underlag` och märker den ofullständig med posten ordagrant i arbetsordern.
- WebFetch går bara till publika värdar som Johnny länkat i tråden, som finns bland träffarna från en webbsökning
  under samma körning, eller som står i en kort lista över exakta dokumentationsvärdar där ingen utomstående kan
  publicera innehåll eller läsa loggar (de hämtas utan frågedel). Länkar i bilagor, hämtade sidor och andra
  verktygssvar gör aldrig en värd tillåten. En adress som bär en annan adress — en validerare, ett arkiv eller en
  proxy som hämtar något åt en — hämtas aldrig. Lokala adresser, långa sökvägs- eller frågedelar och adresser eller
  sökfrågor med hemlighets- eller personuppgiftsliknande värden nekas, och en sökning med `site:` görs bara mot
  dokumentationsvärdarna och Johnnys länkar. GitHub läses med verktyget `github` (API, endast GET), inte med WebFetch.
- `github` läser i original och i delar: hela filträdet (`git/trees/<ref>?recursive=1`) med varje post märkt per
  slag, filer i delar om högst 40 000 tecken (`fran_rad`) med besked om vilka rader som visats och om något
  återstår, filer över 1 MB genom `git/blobs`, och säkerhetsmeddelanden (`repos/…/security-advisories` och den
  globala `advisories`). Samma destination som tidigare; en kapad lista säger hur många poster som inte visas.
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
startade inom den senaste timmen; äldre står kvar som avbrutet med en knapp. En tur som stoppades av abonnemangets
kvot eller av hangvakten tas om först när Johnny trycker Återuppta. Regeln för uttryckligt genomförande och orden för
släpp och avslag är ordbaserade som beställningsregeln. Aquarium prövar att filen med Johnnys ord för ett släpp finns i
paketet men öppnar den inte; partnern och startvakten prövar också dess hash. En enskild rad över 20 000 tecken (till
exempel minifierad kod) visas bara till den gränsen. Svaret är huvudagentens text; en kort mellanrad
som följs av fler
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

## Sökningen

Verktyget `sok` och `/api/sok` söker i indexets tabell `sok` (titel och text) i två pass, utan modell. Första passet
är FTS5 med hela ord: ett ord med minst fyra tecken söks som ordbörjan, ett ord med två eller tre tecken som helt ord
(ett tecken används inte) och "en fras" inom citattecken som exakt fras. Först måste alla ord finnas, sedan räcker
ett, och träffarna ordnas efter bm25 med titeln tre gånger tyngre. Andra passet (PARTNER-SOK-DELORD-20260930) söker
varje ord med minst fem tecken också inuti längre ord, så att "bevakning" hittar "omvärldsbevakningen" och "vakten"
hittar "startvakten". Det är en LIKE över samma tabell med samma omfång, och koden kontrollerar att ordet står direkt
efter en bokstav eller siffra; `_` och `-` skiljer ord åt som i indexet. Poster som första passet redan gav och dolda
källor i provläget räknas inte, och en raderad tråds text finns inte i tabellen. Delordsträffarna kommer efter de
andra och märks "delordsträff" i verktygets utdata (`"traff": "delord"` i `/api/sok`, annars `"ord"`). Sinsemellan
ordnas de efter hur många av frågans ord posten har, om träffen står i titeln och hur många gånger ordet står inuti
ett ord. Fyller första passet antalet hålls ändå en tredjedel av platserna (minst en) för delordsträffar; annars får
de platserna som blir över. Med antal 1 hålls ingen plats, så att den enda platsen går till en träff på hela ordet.
Urvalet av partnerns egna bedömningar som står i sin helhet i varje tur använder samma två pass och samma fördelning
mot det Johnny skriver.

Gränser som finns kvar: omvänt hittar ett sammansatt sökord inte en post som bara har efterledet ("startvakten" hittar
inte "vakten"), eftersom det skulle kräva ordsönderdelning. Ord under fem tecken, fraser och ord med bindestreck eller
understreck söks inte inuti ord; indexet delar redan vid de tecknen, så delarna hittas av första passet. Rangordningen
mellan träffar på hela ord är densamma som före delordspasset. LIKE viker bara versaler i A–Z, så ett sökord med å, ä
eller ö hittas inte inuti ett ord där de bokstäverna står som versaler. Sökverktyget prövar högst tio ord per fråga
inuti ord, i frågans ordning.

## Läsning i original

När Johnny lämnar ett repo eller ett verktyg hämtar partnern hela filträdet först och förtecknar alla delar, läser allt
som styr beteende eller beskriver metod i original och i sin helhet (stora filer i delar tills de är slut), prövar
varje del mot kontorets, Runtimes, Digitalas och Kundstarts main och redovisar täckningen i en tabell per repo: läst i
original, bedömt på namn eller beskrivning (med skäl) och inte läst. En sammanfattning från ett annat verktyg, som
WebFetch eller utredarens svar, räknas inte som läsning. Ryms inte allt i en tur registrerar partnern en utredning för
resten med samma krav. Reglerna står i `partnern/roll.md`.

## Överlämning

När Johnny beställer skriver partnern ett paket per mottagare i kontorets beställningsväg: `ARBETSORDER.md`
(sammanställd, märkt som sådan), `AGARENS-ORD.md` (de citerade inspelen ordagrant), underlaget löst till hashade
filer, `OVERLAMNING.json` och ett AP-06-utkast (`ap06/utkast/`). Beställningen bär det som krävs för att bygga: krav
med ett observerbart prov per krav (AP-06:s requirements och tests fylls ur dem), klart-när, berörda filer (repo och
sökväg), ordning och beroenden, resursram, ursprung (tråd och fynd) och en kort motivering. Den märks **byggklar** när
varje krav har ett prov, klart-när finns och allt underlag är löst till filer, annars **ofullständig** med luckorna
uppräknade; märkningen står i verktygets svar, i arbetsordern och i backloggen. Runtime-uppgiftens tekniska fält
(base-revision, allowed_paths, acceptans, steg och tidsram) fyller mottagaren i mot aktuell main när beställningen
släpps; de redovisas som väntande, inte som fel.

Läget när paketet skrivs står i `OVERLAMNING.json`: **vilande** (i backloggen) eller **lämnad**. Varje senare övergång
är en rad i paketets `KVITTENS.jsonl`, och den sista gällande raden gäller: Johnnys släpp eller avslag av en vilande
beställning (bokförda av partnern, med hans ord i en egen fil) och mottagarens kvittenser. `overlamningar` visar
statusen även när tjänsten inte kör. AP-06-utkastets behörighet bygger på det ordbaserade citatet; mottagaren läser
`AGARENS-ORD.md` (och vid ett släpp `AGARENS-ORD-SLAPP-…`).

**Backloggen** är de vilande beställningarna. Startvakten startar aldrig en vilande beställning, och den lägger inga
rader i planens ÄGARENS TUR; planen pekar hit. Den listas utan modell och bara genom läsning:

```sh
python3 -B tools/partner.py backlog           # id, mottagare, rubrik, datum, ursprung, märkning och motivering
python3 -B tools/partner.py backlog --alla    # också de som har släppts eller avslagits
```

Partnern läser samma lista med verktyget `backlog`, och i samtalsytan är knappen Backlog i sidomenyn (tidigare
Överlämningar, på ägarens besked) samma lista (`GET /api/backlog`). Går beställningsvägen inte att läsa är backloggen
okänd (kod 4), aldrig tom; ett paket som inte går att läsa räknas upp, och då sägs att backloggen inte är känd i sin
helhet. Lämnade och avslutade överlämningar syns i trådarna och i Kontoret.

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
paketets `session/`; för Codex binder trådens id i den första strömmen sessionen till överlämningen. Tråden och Kontorets lista över överlämningar visar mottagaren, statusen och vilken session som startade och när,
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
sparade inspel, verktyg per körningstyp utan stegtak, ägarens-ord-spärren och rättelsens företräde, lägets
uppdelning i Johnnys ord och partnerns egna bedömningar, mellanrader utanför svaret, samtalets alla bilagor och
läst andel vid öppning, ÄGARENS TUR läst som Aquarium, överlämning utan dubbletter (samma inspel och öppen
överlämning) och med kvittens, en överlämning per mottagare ur samma meddelande med egna id utan att ett befintligt
paket flyttas, webbkroken med sökträffar och planterade länkar, bakgrundsutredning, provläge och att ingen
användningsgräns stoppar flera turer i rad. Backloggen prövas med vilande beställningar (byggklar med krav, prov och
underlag löst till filer; ofullständig när ett prov eller klart-när saknas; underlag som inte går att öppna vägras
eller märks), regeln att "beställ" inte räcker för genomförande, dubblettregeln mellan vilande och lämnade, släpp och
avslag bara på Johnnys ord med id (ord utanför tråden, negerat, utan id och med ett annat id nekas), ett släpp som
lämnar paketet orört och bokför övergången, ett beslut samma sekund som ett annat som nekas läsbart utan att något
skrivs, kvittenser och rader utan hans ord som aldrig väcker en vilande beställning
och en backlog som inte kan läsas och därför är okänd. Radering av en tråd prövas med bilagor, turer, en
utredning och sessionsfiler: tråden och dess filer försvinner för gott, också kopplingar till och från den och en
utredningskatalog utan ström. En bilaga som en annan tråd använder, sparad förståelse och överlämningar ligger kvar,
och överlämningens vy tål att tråden saknas. Journalens seq fortsätter uppåt, också förbi en avbruten sista rad. En
krasch mellan journalbytet och indexet lämnar ingen tråd efter sig vid nästa start, och raderingen vägras medan
partnern arbetar i tråden. GitHub prövas med en fejkad `gh`: hela trädet märkt per slag,
ett kapat träd, en fil över 1 MB läst i delar till sista raden och hämtad en gång, säkerhetsmeddelanden, en kapad lista
och en otillåten sökväg. Modellvalet prövas så att utredaren får samma modell och ansträngning och kroken nekar andra
agenttyper och modeller.
Startvakten prövas med en fejkad mottagarsession som kör det riktiga kvitteringskommandot ur sin instruktion: exakt
en session per överlämning (även efter en omstart av tjänsten), väntan när skrivplatsen är upptagen och sedan start,
egen session i samma repo och dygnstaket, kvot och saknad inloggning med synlig väntan och samma session, Codex ur
bemanningen med kvot och fortsättning i samma tråd utan byte när bemanningen ändras, en levande Codex-session som
känns igen efter en omstart av vakten, ett kvotbesked utan avslutat varv, en fortsättning som väntar på en annan
skrivare, oläst bemanning utan reservväg,
fel och avbrott utan en andra session, ändrad binär, en vilande beställning som aldrig startas förrän Johnny släpper
den (inte heller med en kvittensrad eller ett felaktigt index), att prov- och utvecklingsinstanser aldrig startar något och att
processer, färska worktrees och raderade arbetskataloger bedöms rätt. Kopieringen prövas i en riktig webbläsare
(se beslutet).
