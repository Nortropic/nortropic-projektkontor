# Aquarium v0 — läsning och visningssäker projektion

Aquarium är en lugn läsvy över vad kontoret har levererat, vad som faktiskt arbetar eller väntar och vad som behöver
ägaren. `tools/aquarium.py` gör två saker: den läser (avgränsat och utan skrivning) och den projicerar läsningen till en
visningssäker sammanfattning (kontraktets `schema` är 2). Den startar, godkänner, byter eller ändrar ingenting, och den
renderar ingenting; `tools/aquarium_vy.py` renderar sidan ovanpå projektionen och `tools/aquarium_fonster.py` håller
sidan öppen som ett lokalt fönster. Runtime och kontoret behåller sina egna sanningskällor.

## Vad som läses

`collect(runtime_root, office_root, ...)` läser åtta källor: `release`, `staffing`, `questions`, `service`, `engine`,
`tasks`, `watch` och `office`. Varje del är en utbytbar läsare, så prov använder syntetiska läsare i stället för verklig
drift.

- **Runtime genom en avgränsad sond.** `runtime_probe` läser pekaren `.runtime/ap10/active.json` (vanlig fil, ingen
  symlänk), tar releasekatalogen ur dess `config` och kör releasens *egen* frysta kod en gång med releasens egen
  Python (`-B -c PROBE`), utan skal, med 30 sekunders tidsgräns och en minimal miljö (`PATH`, `HOME`, `USER`,
  `LOGNAME`, `LANG`, `TMPDIR` plus `PYTHONDONTWRITEBYTECODE`, `NR_HOST_ROOT`, `NR_CONFIG_SHA256`, `LC_ALL=C`). Sonden
  lämnar sex delar som JSON: aktiv release, bemanning, modellfrågor (D030), tjänstens identiteter, motorns pågående
  körningar och om senaste omgången förlorade kapacitet. Varje körning bär sitt arbetsflödes-id, alltså uppdragets namn
  så som motorns läsning håller det. Aquarium ändrar ingenting i releasen; den läser bara.
- **Uppdragsfilerna genom `task_reader(runtime_root, identities)`.** Källan `tasks` (`Runtime · uppdragsfiler`) läses bara
  när motorn gick att läsa, och bara för de uppdrag motorns egen läsning visar som parkerade — högst de 32 första, i
  motorns ordning. För varje sådant id öppnas `.runtime/tasks/<id>/brief.md` komponent för komponent utan att följa
  länkar, högst 512 byte läses och bara rubrikraden (`# ...`) behålls, normaliserad och kapad vid 120 tecken. Ett id som
  inte är gemena bokstäver, siffror och bindestreck rör ingen fil alls. Läsaren listar ingen katalog, öppnar ingen annan
  fil och behåller inget annat: en brief är ett uppdrags prompt, och bara rubriken är visningsdata. Statusen per uppdrag
  är `läst`, `saknas` eller `oläslig`.
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
- **Verkstaden** — motorns körningar, delade i `items` (arbete) och `parked` (uppdrag som inte arbetar), båda i motorns
  ordning. En `ServiceIdentity` är en teknisk post och en `PrivateAssessment` är bevakningens egen omgång (den visas av
  Utkiken): ingen av dem är arbete eller ett parkerat uppdrag. En körning med väntande aktiviteter, eller bara med ett
  väntande arbetsflödessteg (det vanliga läget mellan två aktiviteter), arbetar; en körning med varken det ena eller det
  andra är parkerad. Varje arbetspost får `step`, `state` och `executor` *bara* ur de väntande aktivitetsnamnen: ett namn
  med `review` ger `granskning`/`granskas`, `execute_claude` eller `execute_codex` ger `utförande`/`pågår` med utföraren
  namngiven när exakt en av dem väntar, `publish_candidate` ger `integration`/`integreras`, annars `steg` eller
  `arbetsflödessteg`. `executor_basis` säger vilket steg som belägger utföraren. Konfigurerad bemanning blir aldrig en
  utförare här, och en utförare som motorn inte visar lämnas tom — vyn skriver då `ej belagd`.
  Varje parkerat uppdrag får `title` och `title_status` ur källan `tasks`: `läst` med rubrik, `saknas` när brief-filen
  inte finns, `oläslig` när rubriken inte gick att läsa och `okänd` när hela källan var otillgänglig. `titles` i
  Verkstaden säger om uppdragsfilerna gick att läsa; uppdragen visas även när titlarna är okända.
- **Utkiken** — bevakningens schema (`aktiverat`, `pausat`, `stoppat` eller `okänt`), nästa *planerade* tid, de tre
  senaste starterna, senaste rapporten och det senast granskade beskedet. En planerad omgång är inte en genomförd
  omgång, och en start är inte ett färdigt intag. En färsk läsning gör aldrig ett gammalt granskat besked aktuellt:
  beskedet behåller sin egen tid och märks `older_than_a_day`. Bevakningens modell följer inte modellvalet och ger
  aldrig upphov till en modellfråga.
- **Ägarens bord** — obesvarade beredningar med förslag (om ingen accept finns), planens ägartur, Runtimes
  modellfrågor för fortfarande valda modeller, och bevakningens egen ägarfråga. Inget annat blir en ägarpost.
- **Sockeln** — tjänstens verifierade identiteter (`igång`, `delvis`, `okänt`), aktiv konfiguration, den *konfigurerade*
  bemanningen och motorns räkneverk: `busy` är antalet arbetsposter, `idle_tasks` antalet parkerade uppdrag och
  `identity_records` antalet tekniska identitetsposter. Alla tre är `null` när motorn inte gick att läsa.

Rubrikraden visar `pågår` (antalet arbetsposter), `väntar` och `behöver dig`. Saknas en källa blir motsvarande tal
`null`, aldrig noll: ett okänt läge visas inte som lugnt. `lugnt` är sant bara när alla tre är noll *och* var och en av de
åtta källorna gick att läsa. En läsning är en daterad ögonblicksbild, inte en live-vy och ingen notifiering; `read_at` och
`stale_after_seconds` (300 sekunder för Runtime-källorna, inklusive `uppdragsfiler`, och 3600 för kontoret) finns med just
för att vyn ska kunna visa hur färsk uppgiften är.

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

## Datum

Ett datum är ett verkligt kalenderdatum mellan 2000-01-01 och 2099-12-31, skrivet antingen `YYYY-MM-DD` utan siffra
intill eller som åtta siffror `YYYYMMDD` utan bokstav eller siffra intill. Därför blir en åttasiffrig följd inne i en
commit-hash, en digest eller ett annat tecken-id aldrig ett datum, och en kandidat som inte är ett riktigt datum hoppas
över medan sökningen fortsätter. Första giltiga datumet i id:t används, annars det första i texten, annars inget
(`null`). Samma regel gäller Arkivets `date` och en öppen berednings `since` vid Ägarens bord.
Saknar en leveranspost i beslutsloggen datum används datumet i leveransbeskedet för samma åtagande, och posten säger det.

## Scenen

`tools/aquarium_vy.py` renderar projektionen till en sida: ett sammanhängande verkstadsgolv sett ovanifrån, med samma
platser varje gång, så att läget känns igen i stället för att läsas som en tabell. `render(projection)` är ren — ingen
fil, klocka, process eller nät, indata ändras aldrig och samma projektion ger samma sida — och den fyller bara sidans
platshållare och listrader med text som HTML-flyktas.

- **Arkivet** — hyllan med levererade och avslutade åtaganden, nyast först; dagens leverans märks, en post utan datum
  står som `odaterad` och antalet är exakt antalet poster.
- **Verkstaden** — tavlan med *uppdrag som inte arbetar* (namn och rubrik ur `uppdragsfiler`) och tre bänkar för arbete
  som motorn visar som pågående.
- **Granskningen** — granskningsbordet, som visar en granskning eller en integration.
- **Utkiken** — bevakningen vid fönstret: schemat, nästa *planerade* omgång (en planerad omgång är inte en genomförd),
  de senaste starterna, senaste rapporten och datumet för det senast granskade beskedet.
- **Ägarens bord** — kuvert och en märkning bara när något verkligen väntar på dig.
- **Maskinrummet** — tjänsten, den konfigurerade bemanningen och de tekniska identitetsposterna, medvetet nedtonat.
- **Det frostade rummet** — interaktivt arbete, som inte observeras.

En figur ritas bara där motorns läsning belägger arbetet: bänkarnas och granskningens figurer följer klassen `aq-figur`
och bevakningens figur klassen `aq-kor`. En utförare som motorns läsning inte belägger skrivs ut som `ej belagd` i
stället för att gissas, och den konfigurerade bemanningen visas bara som konfiguration i Maskinrummet — den blir aldrig
en figur och aldrig observerat arbete. Interaktivt arbete, till exempel kedjedrivarens sessioner, observeras inte och
visas därför inte, varken som arbete eller som frånvaro av arbete.

Sidan är en ögonblicksbild, inte en live-vy; i fönstret laddas den om när det finns en ny läsning (se Fönstret). Den
startar i det inaktuella läget och görs färsk bara av sin egen lilla
skript-rad (fäst med sin SHA-256 i sidans Content-Security-Policy) så länge läsningen är yngre än den minsta
`stale_after_seconds` bland de lästa källorna; varje källrad märks dessutom `inaktuell` för sig när just den källan hunnit
bli gammal. En inaktuell sida visar `senast kända läge`: världen står still, figurerna blir konturer och en banderoll
säger att det inte betyder att arbete, tjänst eller ägarärenden har upphört. En källa som inte gick att läsa visas som
dimma med texten att läget är okänt, inte tomt — aldrig som tomhet eller nollor. En sida vars projektion är `provdata`
märks `PROVDATA` en gång för hela sidan: den är syntetisk och ingen observation av verksamheten.

Sidan gör aldrig något annat: den läser ingen källa och anropar ingen modell, och den hämtar inget över nätet — utom att
fönstrets sida frågar sitt eget fönster på 127.0.0.1 efter den senaste lästiden. Den har inget formulär och
ingen knapp som startar, godkänner, pausar eller ändrar något, och den visar inga privata texter, sökvägar eller
körningsidentifierare — bara det projektionen redan har gjort visningssäkert.

```
python3 -B tools/aquarium_vy.py PROJEKTION.json NY.html
```

`PROJEKTION.json` måste vara en vanlig fil (ingen symlänk), högst 1 000 000 byte, och läses genom en öppning som inte
följer länkar. `NY.html` får inte finnas, dess förälder måste finnas och får inte vara en symlänk, och sidan skrivs som
UTF-8 med rättigheterna 0600 genom en exklusiv öppning som inte följer länkar. Lyckas det avslutas kommandot med 0 utan
utskrift; annars med 2 och enbart raden `Kunde inte skapa Aquariums vy.` på standardfel, utan något privat. Kommandot
läser bara den angivna filen och samlar, serverar, startar eller ändrar ingenting.

Proven i `tools/test_aquarium_vy.py` använder bara syntetiska projektioner och tillfälliga filer under repots befintliga
`.scratch`; de läser aldrig verkliga källor och använder aldrig nätet.

## Fönstret

Vyn ovan är ett kommando som skriver en sida. Fönstret är samma sida, men öppen: en egen läsprocess som du startar och
stoppar, och som läser om medan sidan är öppen.

```
python3 -B tools/aquarium_fonster.py [--port PORT]
```

Kommandot gör först en läsning — samma avgränsade läsning som `tools/aquarium.py` gör — och lyssnar sedan på
`127.0.0.1`, på port `8741` eller den port du anger (fyra eller fem siffror, 1024–65535). Lyckas det skrivs raden
`Aquarium-fönstret: http://127.0.0.1:8741/ · stoppa med Ctrl-C` på standard ut, och processen stannar där tills du
avslutar den med Ctrl-C; då avslutas den tyst med 0. Går något fel — felaktiga argument, en första läsning som inte gick
att göra eller en port som inte kunde öppnas — avslutas kommandot med 2 och enbart raden
`Kunde inte starta Aquariums fönster.` på standardfel, utan något privat och utan att något skrivs på standard ut.
Fönstret är en användarägd process: det startar inte vid inloggning, det är ingen bakgrundstjänst, det installerar
ingenting och det exponerar ingenting utåt. Öppna adressen i Chrome, lägg fönstret i helskärm och spegla skärmen till
tv:n om du vill ha bilden uppe i rummet.

**Sidan laddar om sig själv.** Fönstrets sida bär, vid sidan av `SKRIPT`, ett andra litet skript, `FONSTERSKRIPT`, som
är fäst med sin SHA-256 i sidans Content-Security-Policy precis som `SKRIPT`. Var 30:e sekund frågar det `/lasning.json`
efter den senaste lästiden och laddar om sidan bara när tiden skiljer sig från den sida du ser. Det patchar ingenting
och ritar ingenting själv: renderaren förblir det enda stället som gör en sida av en projektion. Har du en panel öppen
och ingen ny läsning finns, ligger panelen kvar — sidan laddas inte om i onödan.

**Läsningstakten.** En läsning görs bara när sidan frågar, och bara när det gått minst 120 sekunder sedan den förra
läsningen *började*. Alltså läses källorna högst varannan minut, och bara medan en sida är öppen; står ingen sida öppen
rörs källorna inte alls. En läsning i taget: frågar sidan medan en läsning pågår görs ingen ny. Misslyckas en läsning
behålls den förra läsningen och dess sida oförändrade, men försöket räknas som påbörjat, så nästa försök sker tidigast
120 sekunder senare.

**Färskheten avgör sidan själv.** Fönstret gör ingenting åt hur färsk sidan ser ut. Det är sidans eget `SKRIPT` som var
30:e sekund jämför läsningens tid med din klocka. Ett stoppat fönster, en sovande dator eller ett nät som ligger nere
ger därför en sida som blir `inaktuell` när dess läsning är äldre än fem minuter — den ser aldrig färskare ut än den
läsning den vilar på.

**`nytt läge`.** Fönstret håller sina två senaste läsningar i minnet och jämför dem. Ett uppdrags observerade läge i en
läsning är antingen *arbete* med motorns steg, tillstånd och utförare, eller *vilar* för ett uppdrag som inte arbetar;
ett uppdrags-id som förekommer mer än en gång i samma läsning är tvetydigt och har inget läge. Skiljer sig läget mellan
de två läsningarna märks uppdraget `nytt läge`: en märkning på den plats som visar uppdraget — en bänk, granskningsbordet
eller ett kort på tavlan — och en rad i fördjupningen som säger vilken tid den förra läsningen har och vilket läge den
visade. Raden säger bara att läget skiljer sig från förra läsningen. Den säger ingenting om när, hur, via vilken väg
eller av vem det ändrades, och den beskriver ingen **överlämning** mellan två utförare: källorna belägger ingen sådan,
och då påstår fönstret ingen. Den tid som står i raden är en lästid, inte en händelsetid.

Finns ingen jämförelse säger fördjupningen vilken: `första läsningen sedan fönstret startade` vid den första läsningen
och efter en omstart, och `underlaget räcker inte för en jämförelse` när underlaget inte räcker — när motorn inte gick
att läsa i någon av läsningarna, när den ena är provdata och den andra inte, eller när tiden mellan läsningarna inte är
mer än 0 och högst 300 sekunder. Då visas bara det aktuella läget, utan någon uppdiktad tidigare övergång. En märkning
gäller bara läsningen efter ändringen: nästa läsning jämför på nytt, och märkningen är borta om läget inte ändrats igen.
På en bänk och vid granskningsbordet anländer märkningen en gång i det färska läget; ett kort på tavlan är ett uppdrag
som inte arbetar och flyttar sig aldrig.

**Minne, inte historik.** Fönstret håller den senaste läsningen och dess sida i minnet och inget annat: ingen skriven
fil, ingen händelsemotor, ingen databas och ingen historik. Stoppar du fönstret är det borta, och nästa start börjar om
med en första läsning.

**Vad fönstret svarar på.** Bara `GET` av `/` och `/lasning.json`, bara från `127.0.0.1` och bara när förfrågans
värdnamn är exakt `127.0.0.1:PORT` — det hindrar andra sidor i webbläsaren från att läsa fönstret genom ett annat namn
för 127.0.0.1. Allt annat får en fast rad: 405 för andra metoder, 403 för annan klient eller annat värdnamn och 404 för
andra sökvägar. Innan den första läsningen finns svarar `/` med 503. Svaren cachas inte, sidan får inte bäddas in i en
annan sida, och fönstret för ingen logg över vad som efterfrågats.

Proven i `tools/test_aquarium_fonster.py` använder bara syntetiska projektioner, egna läsare och en egen klocka. De
binder aldrig en socket: svaren efterfrågas direkt, hanteraren körs mot en koppling i minnet, och servern och läsningen
byts ut när kommandot prövas. De läser aldrig verkliga källor, använder aldrig nätet och skriver ingen fil.
