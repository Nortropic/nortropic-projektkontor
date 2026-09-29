# Modellfri kontroll av tal och kvarstående lägestext i en kontorspost

`postkontroll.py` läser en kontorspost och planändringen innan de lämnas till den separata granskningen, och
rapporterar det som går att avgöra mekaniskt ur texterna själva. Den kompletterar granskningen och ersätter den
inte: ingen post integreras utan godkänd granskning, och en post som passerar kontrollen är inte granskad.
Kontrollen gör ingen I/O utöver att läsa de filer den får, skriver inga filer och når inget nät.

    python3 -B tools/postkontroll.py POST.md PLANBLOCK.md
    python3 -B tools/postkontroll.py POST.md PLANBLOCK.md --plan PLAN-HELA.md --bas docs/plan.md
    python3 -B tools/postkontroll.py POST.md --json

`filer` är det ändringen skriver: postens text och planblocket. `--plan` är den hela planen efter ändringen, och
`--bas` planen före den. Ges båda läser textreglerna dessutom de stycken i planen som ändringen lägger till eller
skriver om, och bara dem: hela planen bär dussintals historiska block vars tal inte hör ihop, medan de ändrade
styckena är samma leverans som posten och ska räkna likadant. Exitkoden är 1 när något fynd finns, annars 0.

## Vad ett fynd är

Ett fynd är något att bemöta, inte en dom. Reglerna är grova mönster över svensk prosa och har ibland fel om texten.
Svaret när en regel har fel är att skriva om raden så den inte är tvetydig — ett tal som inte går att stämma av mot
sin källa är samma problem för granskaren som för kontrollen. Reglerna tystas inte per fall.

Posterna och planen är hårdbrutna vid omkring 120 tecken, så varje textregel läser stycken och inte rader. Den
första versionen läste rader och var därför blind för `26 rundor …,\nvarav 17 … och 8 …`, som är exakt den form
fynden har i verkligheten.

## Reglerna

| regel | vad den säger |
|---|---|
| `SUMMA` | `N X, varav A … och B …` där A + B inte blir N. Tal i parentes räknas inte som led, eftersom de är underuppgifter om ett led. |
| `TALSPRIDNING` | samma storhet (krav, rundor/rundan, version) bär olika tal på olika ställen i leveransen |
| `PARENTES` | ett stycke stänger en parentes som aldrig öppnades — det spår en halv omskrivning lämnar |
| `TURRADER` | prosans antal öppna rader mot antalet rader i ÄGARENS TUR-blocket |
| `TURFORM` | rad i blocket utan `— sedan ÅÅÅÅ-MM-DD`, eller turrad som hamnat utanför blocket |
| `PLANBLOCK` | en rubrik står två gånger i planen |
| `PLANFALL` | ett stycke i basens plan har ingen motsvarighet i kandidatens |
| `TURBORT` | ändringen tar bort en rad ur ÄGARENS TUR; bär planens prosa kvar den? |

`PLANFALL` och `TURBORT` kräver `--bas`. Blockets slut räknas som Aquarium-läsaren räknar det: vid första rad som
varken börjar med `- [beslut]` eller `- [operatörshandling]` (RUNTIME-PROFILER-AGARTUR-RATTELSE-20260927).

Ett tal eller ett parentestecken i backticks är citerad text — ofta en annan texts felräkning som posten redovisar
att den rättat — och räknas inte av `SUMMA`, `TALSPRIDNING` eller `PARENTES`. `TURRADER` läser stycket omaskerat,
eftersom den jämför mot ett faktiskt antal rader och inte mot ett annat tal i texten.

"en" och "ett" räknas inte som tal. På svenska är de nästan alltid obestämd artikel — "faller ett krav blir posten
ett förslag" — och att läsa dem som talet 1 lade ett tredje, meningslöst tal i varje jämförelse. Det stänger inte
falsklarmen: det enda falsklarmet mot en godkänd post i mätningen står kvar efteråt. Priset är att en räkning som
verkligen står i singular ("beskedet granskades i en runda") inte ses.

## Vad reglerna valdes ur

Alla 123 blockerande fynd i kontorets och Digitalas bevarade granskningsrundor 2026-09-24–29 lästes i original och
klassades efter om de går att avgöra modellfritt. Varje regel ovan fångar en klass som faktiskt fällde en runda;
en regel för motstridiga statusetiketter byggdes och togs bort igen sedan den bara gav falsklarm (olika spårs
"etapp 3" är inte samma etapp). `PLANBLOCK` är den enda regel vars fynd är klassat men inte uppmätt; de övriga sju
har var sin rad i mätningen bakåt. Ordlistan i `TALSPRIDNING` bär bara de storheter ett
fynd i genomgången vilar på; "anmärkningar", "mutationer" och "fynd" prövades och togs bort igen, eftersom de bara
bar falsklarm i mätningen. Mätningen bakåt och dess utfall står i
POSTKONTROLL-20260929 och i `evidence/nasta-uppdrag/local/postkontroll-20260929/`.

## Vad den inte gör

Kontrollen avgör ingenting om sak: om ett tal stämmer mot ett underlag den inte fått, om en gräns ur beställningen
är tappad i registret, om ett påstående om en körning är belagt, eller om en attribution till ägarens ord håller.
De klasserna dominerar de underkända rundorna och är granskningens arbete. Kontrollen tar bort den del av
redovisningsfelen som är räknebar, så att granskningen kan läggas på resten.
