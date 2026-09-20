# AP-06 — leverans av källbunden uppdragsberedning

Kontoret har en körbar beredningsfunktion: [metod och ingång](../../tools/BERED_UPPDRAG.md).
Ur kedjedrivarens valda källor, bedömningar, krav och prov skapar den en privat
spårkedja och ett separat granskningsbart brief-/Runtime-taskutkast. Den visar
luckor och berörda krav vid ändrat/otillräckligt underlag. Sakbedömning, källuppgift,
beslut, faktisk befogenhet och verifieringsbevis hålls isär. Allt förblir utkast
fram till värdens separata sakgranskning och frysning.

## Verkligt genomförande

- Kärna: Runtime-task office-assignment-core-1, skyddad [PR7](https://github.com/Nortropic/nortropic-projektkontor/pull/7),
  `dd1f8c56456b575f017219621402658b5200c592`. Fryst värdacceptans och separat review godkända.
- Kärnan beredde det faktiskt återstående AP06-uppdraget, CLI + ändpunktsprov:
  sju krav med observerbar verifiering. Underlag, omdöme, motiverade rättelser,
  värdgranskning/frysning och utförande är bevarade i [användningsfallet](use-case.md).
- Kommandot: office-assignment-cli-2, skyddad [PR8](https://github.com/Nortropic/nortropic-projektkontor/pull/8),
  `8e5f1c07a79ff288fc8e0a646bb9f7eb66a58f44`. Den aktiva kärnan, dess beroende,
  kontor.py och värdindata/acceptans var utanför kandidatens skrivgräns.
- Använd Runtime-revision genom hela paketet:
  `2789ea0770e4234161e9bdb0378a6e3e7b8432d2`, utan källkodsändringar.

core-run.json och cli-run.json binder frysta underlag, exakta kandidater, verkliga
prov-/review-identiteter och fjärrintegration. Fjärr-PR, committräd och obligatoriska
statusar jämfördes separat från funktionens utskrift. Main-skydden var aktiva och
Runtime återkontrollerade dem före integration; ingen grind kringgicks.

Kärnans 16 syntetiska tester och 20 återanvända AP05-regressionsprov passerade i
kärnbygget. Frysta värdprov prövade legitimt/negativt underlag, fel id/version/citat,
mandat/provluckor, mål/skrivgränser, privata fält och sidoeffektfri beredning.
CLI:s 12 ändpunktstester samt separata frysta värdprov passerade. Separat Runtime-
granskning godkände varje integrerad kandidat. Metodens verkliga Markdown-exempel
reproducerades i native sandbox; originalmaterial ändrades aldrig i negativa prov.
Det levererade kommandots verkliga V3-bundle jämfördes exakt mot beredningen.

## Öppet redovisad värdrättelse

Första CLI-tasken office-assignment-cli-1 stannade före review/integration eftersom
värdens frysta auditlauncher saknade vanlig syskonimport. Kontraktsgranskningen
hade missat detta. [Rättelsen](cli-host-correction.json) bevarar negativt utfall;
ingen produktändring gjordes för att dölja felet, ingen gammal acceptans skrevs om.
Korrigerad launcher granskades separat och ett nytt kärnberett uppdrag frystes.
Runtime återanvände sina tidigare filer byte för byte och gav dem nya verkliga
prov, separat review och skyddad integration. CLI1 visar fortfarande historiskt
waiting_diagnosis i native state, utan process: återuppta inte det ersatta uppdraget.
Detta är ingen kvarvarande implementationsuppgift eller retroaktivt PASS.

## Begränsningar och fortsatt ansvar

Agenten måste välja/läsa källor, tolka skäl/motsägelser, bedöma konkret befogenhet,
utforma tillräckliga observerbara prov och granska exportinnehåll. Funktionen
kontrollerar mekaniska samband och givna observationer; oförändrade hashvärden
bevisar inte uttömmande källurval, begriplighet, sakgodkännande eller tillstånd.
Det tidigare uttrycket human substantive review inför ingen ny ägargrind:
behörig kedjedrivare och separat granskare sköter detta inom accepterat mandat.

Inget acceptansprogram genereras/aktiveras, ingen Runtime-start eller publicering
sker från kommandot. Varje bundle skapas exklusivt och föregångare bevaras. Privata
fält exporteras inte automatiskt; även avsiktliga exportfält kräver innehållskontroll.
Mätning och lookup görs med befintliga värdverktyg; CLI mäter inte källor på nytt.
Ingen tids-/belastningsvinst har mätts. Detta är den befintliga lokala kvalificerade
miljön, inte en generell fleranvändartjänst eller garanti mot fientliga samtidiga
filbyten. En färsk klon saknar privat evidens och ska visa frånvaro, inte hitta på den.

Tidigare leveranser/bevis bevaras. Ingen kampanj-/IR-/valvskrivning, omkompilering,
ny motor/tjänst/kostnad/behörighet eller Runtime-kodändring. Kartspåret förblir
avslutat; A3/A6 och tidigare auditfynd behåller status och betydelse.

## Bevarande och slutpunkt

native-preservation.json binder återläst privat arkiv över tre uppdrags alla
kandidat-/granskningshistoriker och en konsekvent SQLite-backup. Underlag V1–V3,
mandat, lookup och frysta bindningar finns i evidence/ap06/local/. Samma disk är
bevarande, inte skydd mot diskförlust. Inget privat råmaterial publiceras.

[Slutgranskning](closeout-review.json) och [mottagarprov](handover.json) är godkända
inom sina angivna räckvidder. Slutintegrationen binds i det privata slutkvittot.
Det lokala final-<kontorsrevision>.json skrivs och återläses efter skyddad integration
av dokument/bevis, och binder publicerat träd, faktisk Runtime-revision och arkiv.
Om kvittot matchar aktuell main är AP06 avslutad: redovisa och stanna. Nästa bygge
kräver nytt mandat. Ingen ny fas eller återstart av avslutade uppdrag ingår.
