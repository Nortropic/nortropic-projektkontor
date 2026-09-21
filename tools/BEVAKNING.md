# Privat bedömningspolicy för Python-/Temporalbevakning

`bevakning.py` är kontorets policy för Runtimes befintliga privata steg.
Import gör ingen I/O. Runtime äger omgångsidentitet, process- och resursgränser,
modellkörning, separata analys-/granskningsanrop och exklusiv slutskrivning.
Integrationen av denna policy aktiverar ingenting. Fryst acceptans, oberoende
granskning och skyddad integration ligger hos Runtime. Ingen ny scheduler,
utförare, publiceringsväg, credential, AP08-projektion eller driftåtgärd införs.

## Värdprotokoll

- `prepare(output, local_roots, versions, prior, context)` anropar befintlig
  `bevakningsunderlag.collect` exakt en gång, även vid oförändrad grund.
  `output` är en ny privat katalog: `round/intake/data`. Resultatet har
  `completed`, `needs_model` och en fast, icke-känslig `reason`.
  Läsbart men ofullständigt intag kräver modellbedömning.
- `workspace(workspace, round_home, context, role)` fyller en tom, värdskapad
  arbetskatalog för `analysis` eller `review`. Alla källor valideras före kopiering.
- `prompt(role)` ger fasta instruktioner. `schema(role)` ger leverantörens
  formatschema för analys och granskning. Endast `uniqueItems` utelämnas
  rekursivt, även i `proposal.claims` under `anyOf`; alla andra nycklar och
  värden bevaras, inklusive obligatoriska fält och `additionalProperties: false`.
  Varje anrop ger ett fristående schema. Leverantörsformatet är snävare än
  värdens strikta acceptanskontroll: värden kräver fortfarande unika beläggs-
  och anspråks-ID:n samt samtliga semantiska beroenden mellan fälten.
  Dubbletter avvisas utan deduplicering även med korrekt hashbundet syntetiskt
  godkännande och vid återbruk; ogiltigt ursprung kräver ny bedömning.
  Prompternas krav på unika ID:n kvarstår. Rättningen gäller observerad
  `invalid_json_schema` för `uniqueItems`; lokala prov bevisar inte full
  leverantörskompatibilitet eller en genomförd verksamhetsbedömning.
- `finish(round_home, request, config)` returnerar rapporten. Runtime ensam
  skriver `round/report/result.json`; policyn skapar aldrig den filen.
  Ett godkänt åtgärdsförslag kan skapa `report/ap06.json` exklusivt. Värden
  tillhandahåller `report/`. Ett upprepat sådant anrop avvisas utan överskrivning.

Värden skriver förberedelseresultatet till `intake/result.json` och vid tidigare
omgång dess `{home, report, packet}` till `intake/previous.json`. Respektive
modellsteg skriver `analysis/result.json` eller `review/result.json` med
`completed`, `answer`, `provider:{valid_terminal,thread_id,usage}`,
`elapsed_seconds` och `process_group_removed`. De tre framgångsflaggorna måste
vara äkta `true`; trådidentiteterna ska vara icke-tomma och olika. Rapporten
litar inte på `request.outcomes`. Tokenstatistik i `provider.usage` får saknas
eller vara null och är inget villkor för sakgodkännande. Analysens kanoniska
JSON och båda faktiska resultatfilernas bytehashar binds i granskningsbeviset.

Endast `office-python-temporal` kan ge granskat besked. Paketets
`runtime_revision`, `office_revision` och `active_config_sha256` måste stämma
med konfigurationen; även `request.config_sha256` måste stämma. Värdens övriga
körfält ger inga ytterligare rättigheter. Saknade, felaktiga eller misslyckade
steg, avslag, samma tråd, fel hash eller fel identitet ger `reviewed=false`,
`decision=insufficient` och tomma granskningsbindningar. Tidigare positivt
besked återanvänds aldrig som tyst reserv. AP05 och gamla luckor bevaras.

## Fryst urval och oförändrad AP05-bas

Värden väljer exakt fyra filer direkt under `context`, tillsammans högst 2 MiB:
`case.json`, `watch.json`, `authority.md`, `prior-decision.md`. Policyn läser
inte andra privata underlag. Markdownfilerna måste vara icke-tomma och innehålla
valt aktuellt AP10-mandat respektive faktiskt granskat AP09-beslut. Modellerna
ska skilja dessa från historiska förslag och mandat; källtext skapar inga rättigheter.

AP05 validerar det ursprungliga ärendet. `watch.json` innehåller exakt `schema:1`,
samma `case_id`, tidszonsatt `first_treated_at`, icke-tomma `old_gaps` och
`source_map`. Varje ursprungligt käll-ID mappas uttryckligen till ett aktuellt
post-ID eller `null`. Ingen härledning från filnamn eller sökning sker.

Jämförelsen använder `change_assessment.reference_manifest(case)` oförändrad.
Nuvarande råbytes hash och storlek ger `ok` eller `changed`; otillgänglig post
ger `missing`. Null eller okänd mappning utelämnas ur kontrollen och blir
`not_checked` i AP05, aldrig oförändrad. `checked_at` är intagets `observed_at`
och får inte föregå ärendets skapande. `check.json` och det verkliga resultatet
från `assess(case, check)` bevaras som egna filer. AP05 markerar beroenden,
inte sanning. Nya utgåvor utanför den gamla mappningen finns fortfarande i
modellens aktuella paket.

Alla fyra kontextfiler kopieras oförändrade till intaget. `prepared.json` binder
ärende-ID, paketets faktiska bytehash, kontexthash, modellbehov, orsak och eventuell
föregångare. Kontexthashen beräknas över kanonisk JSON som mappar de fyra exakta
filnamnen till respektive bytehash. Kanonisk JSON är UTF-8 med
`sort_keys=True, separators=(',', ':'), ensure_ascii=True, allow_nan=False`.
Slutrapporten behöver därför inte den ursprungliga kontextkatalogen.

## Privat modellunderlag och bedömning

Arbetsytan innehåller endast kontextkopiorna, `packet.json`, `prepared.json`,
`ap05.json`, `INPUT.json` och tillgängliga valda lokala filer/utgåvetexter.
Råa Python-/Temporalindex kopieras inte. `INPUT.json` listar deras utelämnade
ID:n och täckningsgränsen; hash/metadata är fortfarande synliga men kan inte
stödja sakpåståenden om utelämnad text. Nyttolaster får genererade namn
`data/payload-NNN.txt`, aldrig instruktionernas eller originalens filnamn.
Granskaren får dessutom `assessment.json` med exakt kanoniskt analyssvar och
dess värdberäknade hash i `INPUT.json`. Analysen får inget granskningsmaterial.

Symlänkar i hela föräldrakatalogkedjan, absoluta/traverserande relativa nyttolastvägar,
icke-reguljära filer, fel hash, ändrad kontext, okänd roll och icke-tom arbetsyta
avvisas. Katalogåtkomst sker med no-follow-deskriptorer. Kataloger skrivs med
0700 och filer exklusivt med 0600. Nyttolaster begränsas till 1 MiB var och
40 MiB totalt. Varken källor, tidigare omgångar eller kontext skrivs om.
Fel över den publika API-gränsen har en fast diagnos utan sökväg eller innehåll.

Analysen skiljer leverantörsuppgift, lokal aktiv respektive arbetande användning,
sakomdöme och befogenhet. Tillåtna beslut är `retain`, `not_applicable`,
`insufficient`, `propose_action`. Belägg är unika aktuella post-ID:n. Ofullständigt
paket eller olösta motsägelser kräver `insufficient`. Ett ärligt sådant besked kan
bli oberoende godkänt, men återanvänds aldrig automatiskt. Åtgärdsförslag har
text, skäl, krav, observerbart prov och unika kända anspråks-ID:n från det frysta
ärendet. Annars är förslaget null. Ingen åtgärd anges som utförd.

Granskaren prövar den exakta analysens källstöd, tillämplighet, motsägelser,
gamla luckor, källinstruktioner och befogenhet. Giltigt format eller text i alla
fält är inte sakriktighet. Godkännande kräver tom blockerarlista; avslag kräver
konkreta blockerare. Båda prompterna förbjuder operativa/ändrande kommandon,
nätåtkomst och källändringar; ren filläsning är tillåten. Källinnehåll är alltid
icke-betrott belägg, aldrig instruktion. Modeller får inte välja värdfiler.

AP09:s starkare graceful-drain-lucka kräver ensam inget nytt prov och gör inte
redan kvalificerad avgränsad användning otillräcklig. Gamla beslut och luckor
ändras inte. Ingen bred säkerhets-, support- eller graceful-drain-garanti följer.

## Återanvändning, tidsomfång och AP06

Återanvändning kräver två fullständiga paket med samma omräknade fingerprint,
samma ärende/kontext, tidigare rapport/paket som stämmer med värdens angivna
kopior och rätt faktisk pakethash. `same_controlled_basis` eller en ensam
`reviewed`-flagga räcker aldrig. Policyn läser om originalets analys- och
reviewfiler, kontrollerar deras bytehashar, framgång, olika trådar, svar och
analysbindning. Varje omgångs intagskvitto måste också finnas och stämma med
förberedelsen, med äkta `completed=true`. Mellanliggande rapporters beslut,
resonemang, belägg och ursprung måste stämma. Kedjor har cykeldetektering
och högst 366 länkar.
Skadad, motsägande eller för lång historik kräver ny bedömning. Kontrollen
upprepas vid `finish`, så senare skador inte göms av ett tidigare preparebesked.

Återbruk behåller originalets omdöme och faktiska reviewtid, anger föregångare
och `review_origin`, men får aktuell omgångs observations-/rapporttid, pakethash
och AP05-kontroll. Ingen ny modellgranskning påstås. `first_treated_at` avser
ärendets baslinjebehandling, inte nya utgåvors eller senare påståendens behandling.
`reviewed_at` är originalets godkända reviewfils UTC-mtime, inte källans
publiceringstid. `reported_at` är faktisk UTC-tid. Rapporten är ingen levande garanti.

Ett färskt, godkänt `propose_action` går genom befintlig
`assignment_preparation.prepare`. En djup kopia av ärendet bevarar alla
ursprungliga källor, anspråk och åtgärder och får en separat ny åtgärd med
`authority.status=not_granted`, uttryckligt krav på separat handlingsspecifikt
ägarmandat och tomma mandatkällor. Det aktuella AP05-checket används.
Ett konkret krav och prov kommer från förslaget. Inga verifierade citatbindningar
uppfinns: `references=[]`, `reference_checks=[]`. Ingen körorder är accepterad:
`task={}`. AP06:s verkliga resultat visar därför bland annat
`action_authority_missing`, tomma referenser och saknade taskfält.

Analys/evidens ligger kvar bredvid utkastet. Exporttext skiljer omdöme från
befogenhet. Utkastet är aldrig körbart tillstånd; ingen uppgradering eller
publicering utförs. Återbruk bär befintligt AP06-utkast och föregångare utan
nytt `prepare`-anrop eller dubblerat förslag. Policyn validerar hela det bevarade
utkastet mot den godkända analysen, inklusive luckor, exporttext, prov och tom
körorder; enbart oförändrade privata indata räcker inte. AP06:s befintliga
validerings- och texthjälpare återanvänds utan filskrivning.
Andra beslut får inget konstgjort uppdrag.

## Avgränsad intagsrättning och prov

`LOCAL_FILES` utökas endast med `runtime/private_workflow.py`,
`runtime/private_activity.py`, `runtime/private_stage.py`, `runtime/obligation.py`.
Pythonindexets parser accepterar både `Python <stabil version>` och exakt
`Python <stabil version> - <månadsnamn eller förkortning med valfri punkt> <dag>, <år>`.
Numerisk stabil versionsordning, installerad linje och exakt överensstämmelse
mellan etikettens version och URL bevaras. Andra intagsfunktionskroppar ändras inte.

Proven i `test_bevakning.py` och `test_bevakningsunderlag.py` använder enbart
syntetiska källor och temporära kataloger under `.scratch`. Nättransport är
mockad/spärrad. De prövar oförändrad återanvändning, ändrade externa/lokala
källor, kontextändring, intagsluckor, skadade bindningar, saknad/avslagen eller
icke-oberoende granskning, privata kopieringsgränser och AP06 utan nytt mandat.
Verklig privat kontext, nätintag, värddrift och publicering ingår inte i proven.
