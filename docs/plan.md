# Levande plan — AP09 verifierat verksamhetsresultat och kontrollerat avslut

AKTUELLT STEG: båda verkliga intagen, aktuell lokal omobservation och färsk
mottagares faktiska fortsättning är separat sakgranskade utan blockerare.
Befintliga AP05/AP06/AP08 räckte; anvisningen är integrerad genom PR14.
Den granskade avslutsredovisningen integreras skyddat genom samma värdpublicerare.
Fasens slutstatus och faktiskt använda revisioner binds privat i
`evidence/ap09/local/final.json`. Status `verified_delivered` med matchande
revisioner innebär att AP09 är avslutad inom dess redovisade räckvidd.

NÄSTA HANDLING: root verifierar slutkvittot och lämnar den privata slutbilden
`evidence/ap09/local/picture-final/index.html` samt sakbeslutet till ägaren och
stannar. Ingen vidare intagsomgång, modellkörning eller byggfas startas.
Om kvittot saknas/ofullständigt: slutför bara kontrollerat avslut enligt kvarvarande
privata kvitton inom AP09-ACCEPT, återstarta inte den redan genomförda kedjan.

ÅTERUPPTAGNING: `evidence/ap09/local/LAS-MIG.md` leder till mandat, båda intagen,
mottagarens faktiska handlingar, separata granskningar och integrationsbevis.
Kontrollera Git, kvitto och registrerade skrivare före nytt skrivansvar. Root tog
över först efter uttryckligt mottagarstopp. Syntetiska utfall är särredovisade.
Planen ensam äger nästa handling; AP08 är daterad information, inte körstate.

SENARE BESTÄLLD OMGÅNG: en då behörig utförare börjar här och använder
`tools/OMVARLDSARBETE.md`, samma privata ärende och bevarade föregångare. Utför
nytt externt intag OCH lokal kontroll, ompröva konkreta skillnader och använd
AP06 bara vid motiverad åtgärd. Ingen ny rättighet eller stående bevakning följer
av anvisningen. Tekniska kommandon och granskningssamordning bärs av utföraren.

BEVARAT: etablering/AP04–AP08/karta tillgodoräknas. AP07 är frivilligt ANPASSA
utan belagd förbättring; tidigare auditstatus inklusive A3/A6/FIND-004 består.
Ingen installation, Runtime-kodändring, ny kostnad/rättighet eller valvskrivning.
Lokala versions-/användningsuppgifter och råhistorik stannar privat. Historiskt
AP08-avslut nedan bär inte aktuell nästa handling.

---

# Levande plan — AP08 slutleverans

AKTUELLT STEG: presentationskoden är byggd av befintlig Runtime, separat granskad
 och skyddat integrerad genom PR12. Verkligt privat arbetsuttag, källgranskning,
HTML-kontroll och färskt modellbaserat mottagarprov är genomförda. Kontrollerat
avslut och slutbild binds till faktiskt kvitto i `evidence/ap08/local/final.json`.
Kvitto med `status=verified_delivered` och matchande revisioner betyder att AP08
är avslutad inom redovisad räckvidd; den egna HTML-utskriften räcker inte.

NÄSTA HANDLING: kedjedrivaren verifierar det skyddade avslutet och det privata
slutkvittot. När kvittot är verifierat: lämna `evidence/ap08/local/final-view/index.html`
till ägaren och stanna. Ingen ytterligare fas är beställd och inget nytt ägarbeslut
behövs för AP08:s avslut. Ingen uppgift ska återstartas för att en gammal rapport
visar ett dåtida körläge.

ÅTERUPPTAGNING: börja med privat `evidence/ap08/local/LAS-MIG.md`, kvittot och
faktisk Git/Runtime-status innan skrivansvar tas. Avslutsgren `work/ap08-delivery`;
förberedelse, arbetsuttag och hela utförarhistoriken är bevarade privat. Om kvittot
saknas eller inte matchar: slutför endast redovisad kvarstående verifiering inom
AP08, inte ombyggnad eller ny modellkörning. Kontrollera journalerna före omtag.
Källor och tidigare rapporter ersätts inte. Runtime-revisionen för denna fas är
2789ea0770e4234161e9bdb0378a6e3e7b8432d2; faktisk kontorsrevision finns i slutkvittot.

UPPDATERING: en behörig kedjedrivare framställer nästa daterade bild under aktivt
beställt arbete enligt `tools/AGARBILD.md` och privat anvisning. Planen äger nästa
handling, Runtime äger körstate; HTML är en projektion. Ägaren sammanför inga
JSON-filer eller köridentiteter. Öppning är lokal läsning, ingen uppdatering.

BEVARAT: etablering, AP04–AP06 och kartleverans tillgodoräknas. AP06 CLI1 är ersatt
historik och får aldrig återupptas. AP07 är avslutad ANPASSA, enbart frivilligt stöd
vid konkret behov; ingen förbättring är belagd och piloten upprepas inte. A3/A6,
FIND-004 och tidigare auditstatus behåller räckvidd och betydelse. Ingen ny
Runtime-kod, kampanj-/IR-/valvskrivning, tjänst, kostnad eller rättighet ingår.
