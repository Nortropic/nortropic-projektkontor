# Förbättringspartnern — Projektkontorets interna samtalsyta

Johnny lämnar en tanke, skärmklipp, filer, en länk eller ett repo — utan analysprompt — och får ett
systemkunnigt, källbundet resonemang. Partnern fortsätter tidigare trådar, minns rättelser och beslut mellan
sessioner och bereder ett uppdrag till kontoret först när Johnny tydligt beställer genomförande. Uppdraget och
gränserna står i beslutet FORBATTRINGSPARTNER-20260928; planen äger nästa handling.

## Använda

```sh
python3 -B tools/partner.py start     # startar tjänsten på http://127.0.0.1:4760 (i bakgrunden)
python3 -B tools/partner.py oppna     # öppnar samtalsytan inloggad i webbläsaren
python3 -B tools/partner.py status    # kör den, vilken kod (main?) och var ligger datan
python3 -B tools/partner.py stopp     # pågående arbete avbryts, journalförs och återupptas vid nästa start
```

I ytan: skriv, klistra in bilder (⌘V), släpp flera filer eller bifoga. "Bara spara" (eller att skriva "bara spara")
sparar utan analys. Medan partnern arbetar kan ett nytt inspel skickas efter svaret eller "Skicka och avbryt
pågående" (en sen rättelse). Sökfältet hittar tidigare resonemang och underlag utan modellanrop. "Bestående
förståelse" visar vad som sparats, vad som ersatts och av vad. "Tjänst och källor" visar kod, modell, förbrukning
och källtäckning.

Tjänsten körs lokalt på Johnnys Mac och nås bara när den är igång; det är ett synligt beroende. Den startas inte
automatiskt vid inloggning. Att göra den bestående kräver en LaunchAgent som ägaren själv aktiverar (hanterad
policy nekar `launchctl` för sessioner).

## Vad partnern gör utan särskilda instruktioner

Rollen (`partnern/roll.md`) och en kort Nortropic-orientering (`partnern/orientering.md`) följer med varje tur,
tillsammans med ett läge som servern räknar fram: trådens "Där vi är", kopplade trådar, gällande förståelse
(ägarens rättelser och beslut först), källtäckning och senast lästa systemläge. Partnern söker och läser själv
fördjupning med sina verktyg. Den svarar proportionerligt, resonerar för och emot, kan avråda, sparar det som
ska bära framåt och håller trådens läge aktuellt.

## Delar

| Del | Fil | Status |
| --- | --- | --- |
| Lager: journal (original, append-only, fsync), innehållsadresserade bilagor, härlett index | `partnern/lager.py` | Indexet byggs om ur journalen |
| Bilagor: typ ur innehållet, textlager (pdftotext, textutil, zip-XML), sidbilder (pdftoppm), modellbild (sips) | `partnern/bilagor.py` | Ljud, video och okänt sparas men märks olästa |
| Källindex: Improvements-korpusen, ägarens sparade ord och beställningar, kontorets beslut/plan, andra repons dokument, förberedelsens syntes | `partnern/kallor.py` | `partner.py index` bygger om; privata filer tvättas från hemligheter |
| Systemläge: git (origin/main, primärutcheckning), planen på main, Runtimes drift genom Aquariums läsning, öppna PR | `partnern/systemlage.py` | Alltid med lästid och ålder |
| Verktyg för modellen: sök, öppna i sammanhang, bilaga, systemläge, repo, GitHub (GET), förståelse, resonemang, tråd, bered_uppdrag, utred | `partnern/verktyg.py` | Genom MCP-bryggan, per körning |
| Agentloop: Claude Code headless (`claude -p`, dvs. Agent SDK via CLI) i begränsat läge | `partnern/agent.py` | Se modell och drift nedan |
| Webbkrok och destinationspolicy | `partnern/krok.py`, `partnern/webbpolicy.py` | Servern avgör varje webbanrop |
| Bakgrundsutredningar | `partnern/jobb.py` | Journalförda, återupptas efter omstart |
| Överlämning till kontoret | `partnern/overlamning.py` | Paket i `evidence/nasta-uppdrag/local/partner-OVL-…/` med AP-06-utkast |
| Server och samtalsyta | `partnern/server.py`, `partnern/ui/` | 127.0.0.1, inloggning, svenska |

## Modell, drift och gränser

Agentloopen är Claude Code i headless-läge på Johnnys befintliga Claude Code-inloggning (Max-abonnemanget) —
samma väg som Runtime redan använder. Ingen ny leverantör, API-nyckel eller köpta krediter. Varje tur körs som en
egen process i `data/arbetsyta/` med `--restricted`, `--strict-mcp-config`, utan auto-minne och CLAUDE.md, med
verktygen WebFetch, WebSearch, en underagent ("utredare") och partnerns egna verktyg; inga fil-, skal- eller
skrivverktyg. Huvudmodell `claude-opus-5-5` (hög ansträngning), utredaren `sonnet`; ändras i
`data/installningar.json` (`{"modell": {"huvud": "…"}}`).

Verkställda gränser (samma fil, `gransar`): två samtidiga modellkörningar, 15 min och 40 verktygssteg per tur,
8 USD listprisvärde per tur (`--max-budget-usd`), 150 körningar och 250 USD listprisvärde per dygn. Listprisvärdet
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
  skrivit i samma tråd. Text i bilagor, källor, andra trådar och svar kan aldrig bli ägarens ord, och ett lösryckt
  ord räcker inte. Beslut och rättelser kräver ägarens ord; en post som bygger på ägarens ord kan bara ersättas av
  nyare ord från ägaren.
- En beställning (`bered_uppdrag`) kräver dessutom att de citerade satserna står i något av trådens tre senaste
  inspel, innehåller själva beställningen ("genomför", "kör", "bygg" …) och varken är en fråga eller innehåller en
  negation ("inte", "aldrig" …). Ett bart "precis" eller "ja" blir aldrig ett uppdrag, och samma inspel ger aldrig
  två överlämningar.
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
släppas igenom; partnern frågar då hellre). Värdar som en webbsökning returnerat blir hämtbara under körningen: en
planterad instruktion som får modellen att söka fram en viss webbplats kan göra den hämtbar, men bara med korta
adresser utan inbäddade adresser, hemligheter eller personuppgifter. Inloggningskakan är tillståndslös i 30 dagar (utloggning rensar bara
webbläsaren) och spärren efter åtta felaktiga inloggningar gäller alla i tio minuter. Bilagor läses av lokala
verktyg (pdftotext, textutil, sips, zip-XML). Arbete som avbröts av en omstart återupptas automatiskt bara om det
startade inom den senaste timmen; äldre står kvar som avbrutet med en knapp. En tur som stoppades av dygnsgränsen
tas om först när Johnny trycker Återuppta.

## Källtäckning

Improvements-korpusen är förberedelsekampanjens fångst (källgräns 2026-09-19 14:12Z): 61 samtal, 3 111
meddelanden, 3 projektfiler och 132 unika bilagefiler; 3 registrerade bilagor saknar bytes och 4 är historiskt
otillgängliga. Samtal i ChatGPT-projektet efter källgränsen finns inte i korpusen. Tjänsten har ingen
direktåtkomst till ChatGPT. Senare arbetsordrar och ägarord finns där sessioner sparat dem ordagrant i kontorets
privata bevis. En ny fångst genom befintlig Intake-väg (Chrome-session med ChatGPT-inloggning) läggs in genom att
peka `PARTNER_IMPROVEMENTS` på den nya korpusen och köra `partner.py index`.

## Överlämning

När Johnny tydligt beställer genomförande skriver partnern ett paket i kontorets beställningsväg:
`ARBETSORDER.md` (sammanställd, märkt som sådan), `AGARENS-ORD.md` (hela inspelet ordagrant), hashade
underlagsfiler, `OVERLAMNING.json` och ett AP-06-utkast (`ap06/utkast/`) med sina luckor. Status "lämnad".
Mottagaren kvitterar:

```sh
python3 -B tools/partner.py overlamningar
python3 -B tools/partner.py kvittera OVL-… mottagen --av "<session>"
python3 -B tools/partner.py kvittera OVL-… levererad --av "<session>" --bevis "<PR eller commit>"
```

## Prov

`python3 -B -m unittest tools.test_partner` kör en riktig server i processen mot en fejkad `claude` som talar
Claude Codes strömformat, startar den riktiga MCP-bryggan och kör den riktiga webbkroken: lager och återbyggnad,
inloggning/värd/ursprung, bilagetyper och säker visning, avbruten uppladdning, sparat före modellen, bara spara,
idempotenta återförsök, sessionsfortsättning och återskapad historik, avbrott före och under körning, sen
rättelse, ordnat stopp och krasch mitt i arbetet (tur och utredning), upplockning av sparade inspel,
verktygsgränser, ägarens-ord-spärren och rättelsens företräde, överlämning utan dubbletter och med kvittens,
webbkroken med sökträffar och planterade länkar, bakgrundsutredning, provläge och dygnsgräns.
