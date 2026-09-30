# Nortropic — den gemensamma interna arbetsplatsen

Nortropic samlar de tre befintliga användarytorna på en adress: **Hem**, **Kontoret** (Aquarium), **Kundstart** och
**Förbättringar** (förbättringspartnern), och **Flödet**: kartan över hela flödet med alla modellval. Arbetsplatsen är förbättringspartnerns tjänst på `127.0.0.1:4760`, med samma
process, inloggning och Host-/Origin-skydd. Ingen ny process, inget nytt ramverk, inget nytt repo. Uppdraget och
gränserna står i beslutet ARBETSPLATS-20260929; planen äger nästa handling.

```sh
python3 -B tools/partner.py start    # tjänsten, som förut
python3 -B tools/partner.py oppna    # öppnar Nortropic inloggad (Hem)
```

**Nortropic.app.** `python3 -B tools/partner.py app` skapar `~/Applications/Nortropic.app` med Nortropics ikon. Dra den
till Dock: ett klick startar tjänsten om den inte kör och öppnar Nortropic inloggad. Appen är ett skalskript med fasta
sökvägar till kontorets primärutcheckning och den Python som skapade den. Den innehåller ingen nyckel (den läses av
`partner.py oppna` vid varje klick), startar inget vid inloggning och ändrar inga systeminställningar. Kommandot ersätter
bara en app som det själv skapat; `--mal` väljer en annan plats och `--utan-ikon` hoppar över ikonen. Går start eller
öppning inte visar appen ett besked om att köra `partner.py status`.

## Delarna och deras adresser

| Adress | Innehåll |
| --- | --- |
| `/` | **Hem**: bara hälsningen. Rutorna Fortsätt där du var, Levererat och ändrat, Kontoret just nu, Behöver dig och Sök i underlaget togs bort på ägarens besked (HEM-RUTOR-20260929); sidan läser ingenting. `GET /api/arbetsplats/hem` finns kvar oförändrad men anropas inte längre av sidan |
| `/kontoret` | **Kontoret**: Aquarium som arbetsvärld, med samma uppgifter som lista bredvid |
| `/kontoret/objekt/<ref>` | samma, med ett objekt öppet: `OVL-…` (överlämning), `beslut:<ID>`, `uppdrag:<namn>` |
| `/kontoret/presentation` | bara Aquarium, helskärm möjlig, ingen navigation eller lista i sidan; Esc tillbaka |
| `/kundstart` | **Kundstart**: provläget, ditt provärende, kopplingar och det som är öppet enligt planens ägartur |
| `/flodet` | **Flödet**: Nortropics flöde som en karta med fyra linjer, och de fem modellvalen (se nedan) |
| `/forbattringar`, `/forbattringar/ny`, `/forbattringar/t_…` | **Förbättringar**: partnerns samtalsyta. Sidomenyn har Ny tråd, Överlämningar och trådarna; Sök i tidigare resonemang, Bestående förståelse och Tjänst och källor togs bort ur menyn på ägarens besked (HEM-RUTOR-20260929), medan `/api/sok`, `/api/forstaelse` och `/api/lage` finns kvar oförändrade |

Direktlänkar, omladdning och bakåt/framåt fungerar för alla adresser. Gamla ingångar består: `/#t_…` och `/#ny` leds
till `/forbattringar/…`, `#nyckel=` loggar in (`partner.py oppna`), och Aquarium-fönstret (`tools/aquarium_fonster.py`,
port 8741) finns kvar som eget kommando.

## Kontoret och Aquarium

Aquarium-sidan serveras av tjänsten själv på `/kontoret/aquarium`, genom fönstrets `Fonster`: samma avgränsade läsning
som `tools/aquarium.py` (i en egen process med tidsgräns), samma takt (högst en läsning varannan minut, bara när någon
tittar, en i taget), samma renderare och samma med sha256 fästa skript. Sidans skript frågar `/lasning.json` och laddar
om när läsningen är ny. Bara den sidan får ramas in, och bara av samma ursprung (`frame-ancestors 'self'`,
`X-Frame-Options: SAMEORIGIN`); allt annat har kvar `frame-ancestors 'none'`. Skalets egen policy tillåter bara ramar
från samma ursprung (`frame-src 'self'`). Båda kräver inloggning.

Listan bredvid scenen visar samma visningssäkra projektion, grupperad som platserna (Behöver dig, Överlämningar,
Uppdrag i Runtime, Levererat, Bevakningen, Källor och tider). Ett klick på en plats i Aquarium öppnar samma grupp i
listan. Ett objekt öppnas med sina underlag: en överlämnings kvittenser, leveransbevis och tråden där den beställdes, ett
besluts post i beslutsloggen på main, ett Runtime-uppdrags rubrik och läge. Aquarium tas bort ur sidan när Kontoret
inte syns. Presentationsläget bygger ingen lista och ingen navigation; det visar bara Aquarium-sidan.

## Resonera om det här

Vid ett objekt öppnar **Resonera om det här** ett nytt samtal i Förbättringar med objektet som *sammanhang*: ett kort
ovanför skrivrutan visar vilka objekt och källor som följer med, och varje kan tas bort. Ingenting skickas förrän du
skriver och skickar. Hänvisningarna sparas i inspelet vid sidan av texten (`kontext`: ref, slag, titel och källa, tagna
ur källan, högst sex, bara befintliga objekt; annat nekas). De blir aldrig Johnnys ord: `agarens_ord` och
beställningsspärren läser bara texten. Partnern får dem märkta som underlag, inte instruktioner, och öppnar källorna med
sina verktyg. En överlämning har dessutom en väg till tråden där den beställdes, och ett objekt visar de trådar där du
resonerat om det.

## Kundstart

Kundstart är kundens egen vy och öppnas separat; den interna navigationen följer aldrig med. Arbetsplatsen visar
provläget, om testservern på `127.0.0.1:3131` svarar (ett GET av startsidan, utan kakor eller nycklar), Kundstart-repots
revision och vad testservern byggdes från, Kundstarts beslut ur beslutsloggen, Digitalas `verktyg/kundstart.py` på main,
överlämningar till Kundstart och planens öppna ägarrader om Kundstart. **Öppna ditt provärende** går till
`127.0.0.1:3131/samtal`, som öppnar det ärende webbläsaren redan är inloggad i; kommandona för testservern kan kopieras.

**Ärenden** (ägarens beslut ARBETSPLATS-KUNDSTART-ARENDEN-20260929): en lista över ärendenas metadata — kundens namn,
provmärkning, skapad, senast ändrad, antal svar och material och senaste inlämning — hämtad från testserverns interna
`GET /api/intern/arenden`. Testservern delar lagring med produktionen, så även riktiga kunders ärenden syns, men bara som
metadata: ingen kundtext, inga svar, inget material och inga länkar. Partnerns tjänst läser Kundstarts interna nyckel ur
Kundstart-repots `.env.local` vid varje hämtning, bara den raden, och skickar den bara till 127.0.0.1 utan att följa
omdirigeringar; nyckeln sparas inte, loggas inte, lämnar aldrig servern
och ges aldrig till partnerns modell. Bara listans godkända fält behålls. En hämtning läser varje ärende i lagringen (vid
införandet omkring 930 provärenden, tio sidor, ungefär 70 sekunder), så den görs i bakgrunden, bara när Kundstart-delen
visas och högst var 15:e minut; Hem hämtar den aldrig. Saknas nyckeln, svarar testservern inte eller har den inte listan än visas det i stället för en tom
lista. Ärenden öppnas inte härifrån, och arbetsplatsen skapar inga ärenden. En rad här är inget bevis för att en import
har körts.

## Flödet

Ägarens beställning MODELLKARTA-20260929: alla modell- och ansträngningsval samlade i en enkel karta över hela flödet.
Fyra linjer (Idé till main, Kund till leverans, Motorn och Bevakning) visar vid varje hållplats modellen och
ansträngningen som arbetar där. Varje hållplats följer ett av fem val, och färgen säger vilket. Kartans hållplatser står i
`ui/karta.js`; värdena läses av servern (`partnern/modellkarta.py`, `GET /api/arbetsplats/karta`) ur den källa som
faktiskt styr dem:

| Val | Källa | Valbart här |
| --- | --- | --- |
| Partnern | arbetsplatsens `installningar.json` (samma som samtalsytans /model) | ja, gäller från nästa svar; en Claude-modell kör Claude Code, en Codex-modell Codex |
| Dina sessioner | Claude Codes `~/.claude/settings.json` och Codex `~/.codex/config.toml` | ja, i båda programmen (ägarens besked 2026-09-29) |
| Runtime | den aktiva releasen, läst med releasens egen kod (samma avgränsade väg som Aquarium) | ja; modellen avgör utföraren för alla roller, och bytet aktiveras av sig självt när Runtime är ledigt (se nedan) |
| Läsarna | arbetsplatsens `installningar.json` (`lasare`); utan val väljer sessionen | ja; kontorets granskning och Digitalas kritik och provare hämtar valet (se nedan), och ansträngningen följer Runtimes läsarprofil |
| Bevakningen | den aktiva releasens val för bevakningen (utförare, modell, ansträngning); före det valet Runtimes Codex-profil | ja, med Claude eller Codex; aktiveras av sig självt som Runtime |

Startvakten visas vid Arbetssession: Runtimes drivande roll med utförare, modell och ansträngning. En release före
Runtimes D040 har ingen ansträngning i valet; då gäller startvaktens egen (`installningar.json`, `startvakt.anstrangning`).

**Runtime och bevakningen aktiveras av sig självt** (steg 2, Runtimes D040, när den är integrerad och aktiv). När
detta skrivs är D040 granskad men inte på Runtimes main; beslutet RUNTIME-VAL-I-FLODET-20260930 säger vad som återstår.
Spara skriver ett önskemål i Runtimes
inkorg, `.runtime/ap10/workplace-choice.json`, med ett nytt id: Runtimes val (utförare, modell, ansträngning) och
bevakningens. Kortet man inte ändrade behåller sitt väntande värde, annars det som kör. Bara det som fungerade i
mätningen av Runtimes egna program erbjuds och godtas. Runtimes eget verktyg läser önskemålet var femte minut
(`model_choice.py auto`) och prövar det mot mätningen igen. Det gör ingenting om valet redan kör och väntar medan Runtime
arbetar: när bevakningen kör eller kör inom 20 minuter, när arbete pågår i motorn, när en webbprofil kör, eller när
tjänsten inte svarar som väntat. Annars byter det release med samma väg tillbaka som ett handbyte. Kortet visar det
önskade valet och Runtimes status (`automatic-choice-status.json`) för just det önskemålet: väntar och varför, aktiveras
inte och varför, aktiverades, den förra versionen återställd, misslyckat eller avbrutet; en status om ett tidigare
önskemål visas som att valet väntar på Runtimes nästa titt. Aktiveraren är en LaunchAgent i Johnnys eget
sammanhang, eftersom sessioner inte får köra `launchctl`. Johnny startar den en gång, efter Runtimes övergång 19, med
`model_choice.py agent install`; tills dess säger kortet att valet väntar. En prov- eller utvecklingsinstans med egen
datakatalog skriver önskemålet där och kan aldrig utlösa ett verkligt byte, och en instans utan egen datakatalog skriver
inget önskemål. Saknas Runtimes inkorg på datorn säger kortet det och sparar inget.

**Läsarna följer valet** (steg 3, LASARNAS-VAL-20260930). Läsarna är de modeller som bara läser och bedömer: kontorets
separata granskning före integration och Digitalas kritik och provare. Alla tre kör genom Runtimes läsarprofiler i den
aktiva releasen och följer samma val, läst med samma funktion (`modellkarta.lasarval`): granskningen läser det i
processen, och Digitala hämtar det med `python3 -B tools/partner.py lasare`, som skriver valet som en JSON-rad och
aldrig ändrar något. Kontorets granskning körs med `python3 -B tools/granska.py KATALOG`: katalogen har
underlaget i Runtimes manifestform och frågan, verktyget kör kritikprofilen med granskningens svarsform och skriver
utfallet i `review.json` (modellen, varifrån den kom, Runtimes kvitto och svaret). Finns ett val nekas en annan modell,
i granskningen med `--modell` och i Digitala med `--utforare` eller `--modell`; finns inget anger sessionen modellen som
förut. Går valet inte att läsa nekas körningen i stället för att sessionen väljer. Ansträngningen följer Runtimes
läsarprofil (i dag medium för Claude och high för Codex), eftersom profilerna inte tar någon ansträngning. Att välja
läsarnas ansträngning kräver att Runtimes kritik- och provarprofil tar en ansträngning som parameter, en ändring i Runtime
som inte är gjord.

**Bara det som bevisligen fungerar erbjuds.** `python3 -B tools/partner.py matmodeller` prövar varje modell och nivå med
ett kort anrop ("Svara bara med ordet ok.", inga verktyg, inga MCP-servrar) i programmet som kör hållplatsen: Johnnys
Claude Code och Codex, och Runtimes fastlåsta Claude Code och Codex. Codex modellista läses per program, eftersom varje
Codex-version skriver sin egen lista. Ett fel som kan vara tillfälligt prövas om ett i taget; ett tydligt nej gör det
inte. Kvittot är `modellmatning.json` i datakatalogen, och kartan visar vilken mätning och vilka versioner den bygger på.
Samma prövning görs när ett val sparas, och samtalsytans modellväljare erbjuder och godtar också bara det som fungerade.

**Så skrivs ett val.** Ett val sparas först när Johnny trycker Spara, aldrig av en ändrad meny. I Claude Codes fil
ändras bara `model`, `effortLevel` och `modelSettings[<modell>].effortLevel`, där Claude Code läser ansträngningen för
modellen. Ett valt långt fönster (`[1m]`) behålls, utom för Haiku 4.5, som inte har det på abonnemanget. I Codex fil ändras
bara raderna `model` och `model_reasoning_effort` överst, och de läggs först om de saknas. Står en av dem i en form
arbetsplatsen inte känner igen, står en sträng eller tabell över flera rader överst i Codex fil, eller har Claude Codes
fil en annan form än den som skrivs tillbaka (json med två blanksteg), skrivs ingenting; ägaren väljer då i programmet.
En lista över flera rader, som `notify`, följs rad för rad och räknas aldrig som en tabellrubrik. Den nya Codex-filen
prövas innan den skrivs: exakt en rad per nyckel överst och allt från första tabellen oförändrat. Filerna skrivs atomärt,
med samma rättigheter, i en länkad fils mål och bara om de inte ändrats sedan de lästes, eftersom Claude Codes /effort
skriver samma fil. Annars prövas det om, högst tre gånger. Ett litet fönster mellan jämförelsen och namnbytet går inte
att stänga, eftersom programmen inte låser sina filer. Varje val bokförs
i partnerns journal (`modellval`, före och efter). En prov- eller utvecklingsinstans, med egen datakatalog eller port,
skriver bara kopior i sin datakatalog och rör aldrig de riktiga filerna.

## Vad arbetsplatsen inte gör

Den anropar ingen modell vid navigering, statusläsning eller sökning, skriver ingenting i partnerns journal eller i något
annat system vid läsning och startar eller återupptar inga uppdrag. Det enda som skriver utanför webbläsaren är Flödets
Spara: Johnnys val, i den fil som styr det (se Flödet). Egna UI-uppgifter ligger bara i webbläsaren:
senaste adress per del (`arbetsplats:senast:*`), om Kontorets lista är dold (`arbetsplats:lista-dold`), senaste tråden
(`senasteTrad`), utkasten per tråd (`utkast:*`) och inspel som väntar på att skickas (`utkorg`). Okänt är aldrig noll:
en källa som inte gick att läsa visas som okänd,
med tidpunkten för senaste försöket, och övriga delar fungerar. Tider är händelsernas egna (en sammanfogning, en
kvittens); lästiden står för sig. Kundstart väntar aldrig på en Aquarium-läsning; den visar senaste läsningen och läser
om några gånger medan en ny pågår.

## Prov

`python3 -B -m unittest tools.test_arbetsplats` kör en riktig server i processen med fejkad `claude` och en injicerad
Aquarium-läsare (syntetisk projektion): adresser och 404, skalets och Aquarium-sidans huvuden, inloggning på varje ny väg,
läsningstakten, otillgänglig och långsam läsning, okänt i stället för noll, Hem, Kundstart mot en atrapp, objekt och
nekade referenser, sammanhanget i inspel och i modellens meddelande, att hänvisningar aldrig blir ägarens ord, dubbletter,
att läsning varken anropar modellen eller skriver i journalen, och att en nekad skrivning inte förstör nästa begäran på
samma anslutning. Användarresorna provas i Chromium mot en provinstans (se beslutet).
`python3 -B -m unittest tools.test_modellkarta` prövar Flödet: varje val ur sin källa, att bara det uppmätta erbjuds och
godtas, exakt vilka rader som skrivs i Claude Codes och Codex filer, att en okänd form och en samtidig skrivning inte
skriver något, läsarna, partnern, Runtimes och bevakningens önskemål (formen, att det andra kortets väntande värde står
kvar, att ett obevisat val och en länkad inkorg aldrig skrivs, statusen och om aktiveraren går), startvaktens
ansträngning ur Runtimes val, adresserna, att en provinstans aldrig rör de riktiga filerna eller Runtimes inkorg,
`partner.py lasare` och mätverktyget mot falska program. `python3 -B -m unittest tools.test_granska` prövar granskningen
mot en låtsas-release: läsarnas val avgör modell och utförare, en annan modell nekas, utfallet skrivs aldrig över, ett
svar godtas bara med ett kvitto som stämmer och ett avbrott skickas vidare till läsarprofilen.
