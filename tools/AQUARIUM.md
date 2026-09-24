# Aquarium v0 — läsning och visningssäker projektion

Aquarium är en lugn läsvy över vad kontoret har levererat, vad som faktiskt arbetar eller väntar och vad som behöver
ägaren. `tools/aquarium.py` gör två saker: den läser (avgränsat och utan skrivning) och den projicerar läsningen till en
visningssäker sammanfattning. Den startar, godkänner, byter eller ändrar ingenting, och den renderar ingenting; en senare
uppgift bygger vyn ovanpå projektionen. Runtime och kontoret behåller sina egna sanningskällor.

## Vad som läses

`collect(runtime_root, office_root, ...)` läser sju källor. Varje del är en utbytbar läsare, så prov använder syntetiska
läsare i stället för verklig drift.

- **Runtime genom en avgränsad sond.** `runtime_probe` läser pekaren `.runtime/ap10/active.json` (vanlig fil, ingen
  symlänk), tar releasekatalogen ur dess `config` och kör releasens *egen* frysta kod en gång med releasens egen
  Python (`-B -c PROBE`), utan skal, med 30 sekunders tidsgräns och en minimal miljö (`PATH`, `HOME`, `USER`,
  `LOGNAME`, `LANG`, `TMPDIR` plus `PYTHONDONTWRITEBYTECODE`, `NR_HOST_ROOT`, `NR_CONFIG_SHA256`, `LC_ALL=C`). Sonden
  lämnar sex delar som JSON: aktiv release, bemanning, modellfrågor (D030), tjänstens identiteter, motorns pågående
  körningar och om senaste omgången förlorade kapacitet. Aquarium ändrar ingenting i releasen; den läser bara.
- **Bevakningen genom kontorets befintliga `bevakningsbild`.** Modulen importeras bara inne i läsaren, så att importera
  `aquarium` är helt overksamt. Den explicita otillgängliga observationen (`unavailable`) eller ett senaste besked vars
  `integrity` inte är `available` gör bevakningen otillgänglig — skadat underlag presenteras aldrig som ett resultat. Ur
  rapporterna behålls bara `reported_at`, `reviewed`, `reviewed_at` och `decision`. En ägarfråga tas bara när
  bevakningsbildens egen `owner_decision.needed` är `yes`.
- **Kontoret genom `git show refs/remotes/origin/main:<sökväg>`**, alltså det publicerade innehållet — aldrig
  arbetsträdet: beslutsloggens poster (id, rubrik, text), leveransbeskeden `evidence/APnn/leverans.md` och planens
  block `ÄGARENS TUR`, samt `main` och dess datum.

En läsare som fallerar eller lämnar trasiga data gör bara sin egen källa otillgänglig, med lästid bevarad och utan att
någon privat text sparas. Otillgängliga källor är inget fel: projektionen säger det i stället.

## Vad som aldrig läses eller behålls

Inga privata råtexter, inga rapportinnehåll utöver de fyra fälten ovan, inga sökvägar, kör- eller trådidentifierare,
leverantörstexter eller e-postadresser. Projektionen kopierar bara de dokumenterade nycklarna; övriga nycklar i indata
ignoreras och kopieras aldrig. Kontorets texter reduceras till rubriker och datum och kopieras aldrig i sin helhet. Det
som ändå skulle kunna se privat ut i en rubrik ersätts av `[dolt]` innan det lämnar projektionen.

## Vad projektionen betyder — och inte

`project(readings, now)` är ren: ingen fil, klocka, process eller nät, och indata ändras aldrig. Den lämnar fem platser:

- **Arkivet** — en post per levererat eller avslutat åtagande, ur beslutsloggens id-markörer (`-LEVERANS`,
  `-LEVERANS-`, `-AVSLUT`) och ur leveransbesked som inte redan har en leveranspost. Inget hittas på: antalet är exakt
  antalet sådana poster, och en post utan datum läggs sist i stället för att gissa.
- **Verkstaden** — motorns körningar. En `ServiceIdentity` är en teknisk post, inte arbete. En körning med väntande
  aktiviteter, eller bara med ett väntande arbetsflödessteg (det vanliga läget mellan två aktiviteter), pågår; en
  väntande aktivitet vars namn innehåller `review` granskas. `model_evidence` är alltid falskt i v0: en väntande
  aktivitet eller en pågående körning är aldrig bevis för att en modell arbetar.
- **Utkiken** — bevakningens schema (`aktiverat`, `pausat`, `stoppat` eller `okänt`), nästa *planerade* tid, de tre
  senaste starterna, senaste rapporten och det senast granskade beskedet. En planerad omgång är inte en genomförd
  omgång, och en start är inte ett färdigt intag. En färsk läsning gör aldrig ett gammalt granskat besked aktuellt:
  beskedet behåller sin egen tid och märks `older_than_a_day`. Bevakningens modell följer inte modellvalet och ger
  aldrig upphov till en modellfråga.
- **Ägarens bord** — obesvarade beredningar med förslag (om ingen accept finns), planens ägartur, Runtimes
  modellfrågor för fortfarande valda modeller, och bevakningens egen ägarfråga. Inget annat blir en ägarpost.
- **Sockeln** — tjänstens verifierade identiteter (`igång`, `delvis`, `okänt`), aktiv konfiguration, bemanning och
  motorns räkneverk.

Rubrikraden visar `pågår`, `väntar` och `behöver dig`. Saknas en källa blir motsvarande tal `null`, aldrig noll: ett
okänt läge visas inte som lugnt. `lugnt` är sant bara när alla tre är noll *och* varje källa gick att läsa. En läsning är
en daterad ögonblicksbild, inte en live-vy och ingen notifiering; `read_at` och `stale_after_seconds` (300 sekunder för
Runtime-källor, 3600 för kontoret) finns med just för att vyn ska kunna visa hur färsk uppgiften är.

## Kommandot

```
python3 -B tools/aquarium.py NY_KATALOG
```

Läser kontoret (repot som äger `tools/`) och Runtime (systerkatalogen `Nortropic Runtime`), projicerar med klockans tid
och skriver `NY_KATALOG/projection.json` som UTF-8 (`json.dumps(..., ensure_ascii=False, indent=1, sort_keys=True)` och
ett avslutande radslut). `NY_KATALOG` får inte finnas; dess förälder måste finnas och får inte vara en symlänk.
Katalogen skapas med rättigheterna 0700 och filen med 0600 genom en exklusiv öppning som inte följer länkar. Lyckas det
avslutas kommandot med 0 utan utskrift; annars med 2 och enbart raden `Kunde inte skapa Aquariums projektion.` på
standardfel, utan något privat. Kommandot renderar, serverar, startar och ändrar ingenting.

Proven i `tools/test_aquarium.py` använder bara syntetiska data och tillfälliga kataloger under repots befintliga
`.scratch`; de läser aldrig verkliga källor, kör aldrig sonden och anropar aldrig git mot ett verkligt repo.
