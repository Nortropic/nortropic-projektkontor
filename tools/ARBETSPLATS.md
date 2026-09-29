# Nortropic — den gemensamma interna arbetsplatsen

Nortropic samlar de tre befintliga användarytorna på en adress: **Hem**, **Kontoret** (Aquarium), **Kundstart** och
**Förbättringar** (förbättringspartnern). Arbetsplatsen är förbättringspartnerns tjänst på `127.0.0.1:4760`, med samma
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
| `/` | **Hem**: fortsätt där du var (senaste tråd, öppna överlämningar, ditt provärende i Kundstart), levererat och ändrat (sammanfogningar med egen tid, sedan förra besöket när det går att jämföra), det som behöver dig (ur ägarens bord, uppdelat), Kontoret just nu och sökning |
| `/kontoret` | **Kontoret**: Aquarium som arbetsvärld, med samma uppgifter som lista bredvid |
| `/kontoret/objekt/<ref>` | samma, med ett objekt öppet: `OVL-…` (överlämning), `beslut:<ID>`, `uppdrag:<namn>` |
| `/kontoret/presentation` | bara Aquarium, helskärm möjlig, ingen navigation eller lista i sidan; Esc tillbaka |
| `/kundstart` | **Kundstart**: provläget, ditt provärende, kopplingar och det som är öppet enligt planens ägartur |
| `/forbattringar`, `/forbattringar/ny`, `/forbattringar/t_…` | **Förbättringar**: partnerns samtalsyta, som förut |

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
Arbetsplatsen skapar inga ärenden, hanterar inga länknycklar och läser inga kundärenden: listan kräver Digitalas interna
nyckel, som inte används här. En länk här är inget bevis för att en import har körts.

## Vad arbetsplatsen inte gör

Den anropar ingen modell vid navigering, statusläsning eller sökning, skriver ingenting i partnerns journal eller i något
annat system vid läsning och startar eller återupptar inga uppdrag. Egna UI-uppgifter ligger bara i webbläsaren:
besöksmarkören (`arbetsplats:besok`), senaste adress per del och utkasten per tråd. Okänt är aldrig noll: en källa som
inte gick att läsa visas som okänd, med tidpunkten för senaste försöket, och övriga delar fungerar. Tider är
händelsernas egna (en sammanfogning, en kvittens); lästiden står för sig. Hem och Kundstart väntar aldrig på en
Aquarium-läsning; de visar senaste läsningen och läser om några gånger medan en ny pågår.

## Prov

`python3 -B -m unittest tools.test_arbetsplats` kör en riktig server i processen med fejkad `claude` och en injicerad
Aquarium-läsare (syntetisk projektion): adresser och 404, skalets och Aquarium-sidans huvuden, inloggning på varje ny väg,
läsningstakten, otillgänglig och långsam läsning, okänt i stället för noll, Hem, Kundstart mot en atrapp, objekt och
nekade referenser, sammanhanget i inspel och i modellens meddelande, att hänvisningar aldrig blir ägarens ord, dubbletter,
att läsning varken anropar modellen eller skriver i journalen, och att en nekad skrivning inte förstör nästa begäran på
samma anslutning. Användarresorna provas i Chromium mot en provinstans (se beslutet).
