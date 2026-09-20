# AP04 — funktionell leverans och avslutsbevis

Resultatfunktionen är faktiskt byggd genom kontorets startingång och integrerad
av Runtime i [PR2](https://github.com/Nortropic/nortropic-projektkontor/pull/2).
Paketets slutgranskning, integration av avslutstexterna och slutarkivens återläsning
återstår vid denna texts commit. Planens slutkvittoregel avgör när även det är klart.

## Vad som fungerar

`tools/kontor.py` startar ett accepterat committat uppdrag, visar sparat läge,
återupptar samma Runtime-arbete med dess befintliga diagnos/review/signaler och
hämtar resultatet genom den Runtime-byggda `tools/kontor_result.py`.
Status/resultat startar inga workers, signaler eller publiceringar. De visar
observationstid/ålder, live=false och remote_current=false. Saknade eller
motsägande bevis blir unavailable. Runtime är fortfarande enda körmotor.

Kedjedrivaren startade office-result-1, avbröt dess första försök kontrollerat,
verifierade processavslut, sparade diagnos och återupptog via kontorets kommando.
En ny separat mottagare hittade rätt mandat, faktiskt vänteläge och exakt nästa
handling utan ägarens hjälp. Resultatbygget, hostacceptans, färsk kodreview och
skyddad integration följde sedan. Ingen rutinmässig ägarfråga behövdes.
Det visar denna kedja och överlämning; det är inget mått på långsiktig ägarbörda.

## Bundna identiteter

| Led | Revision / identitet |
|---|---|
| Startkoppling Runtime, skyddad PR15 | 09268df5f59a180afe863d4cf7f95c9ad95f8639 |
| Kontorets startkoppling, skyddad PR1 | 71e90f01f9ee3c8fb4ca003b879fc74bc4206b17 |
| Accepterade/frysta inputs | 0693a4c7429b6f7068fb887a5469bd4c48ba2279 |
| Faktiskt använd Runtime | 09268df5f59a180afe863d4cf7f95c9ad95f8639 |
| Kandidat byggd av Runtime | e3eb7e93c936b4d69e19d967e90d87d1f291785b |
| Resultatfunktion integrerad i kontoret | 5a6084ee156bb2d12537f5e58af62e125d83be14 |
| Integrerat/kandidatens träd | 1dd335b63a54ede503e4913dc85a12ba33e95f6b |
| Fryst hostacceptans SHA256 | 5f193ad4f0648ed7532b78e315c31d8bda3c6ba16c01517143c273b7477d83c1 |
| Separat Runtime-review | 01a0c004-c252-7ff0-a8f4-a1a80cce280a |

Senare commits bevarar inputs, tester/rapporter och avslutstexter samt begränsar
kontorets provider-val till faktiskt prövad Codex (riktat test; gamla Runtime-val
bevarade). De är inte den
Runtime-revision som körde uppdraget. Slutkvittot binder även båda slutliga main.
Inputhistoriken är bevarad på state/ap04-result-input; den är inte en separat
integration eller auktoritetskälla vid sidan av main och frysta Runtime-inputs.

## Prov och granskning

- 28 Runtime operator-/målrepo-tester PASS på granskad startkoppling. Sex nya
  tester prövar namngivet mål, riktiga Git-objekt/frysning, exakta native
  filskrivgränser, publiceringsgrindar och sidoeffektfri bevisläsning.
- Native sandbox tillät resultatfilen men nekade aktiv kontorsingång, AGENTS,
  värdacceptans, otillåten ny fil och symlänksflykt. Kandidaten kunde inte skriva
  aktiv Runtime, hostinputs eller publiceringsbehörighet.
- Försök 1: verklig Codex-process startad, kontrollerat SIGTERM, exit130,
  processgrupper avslutade; waiting_diagnosis bevarat. Försök 2: lyckat Codex-arbete.
  Historikens första 10 händelser är exakt prefix till de slutliga 33.
- Fryst hostacceptans körde kandidat i läsande sandbox och prövade giltig leverans,
  saknade bevis, felaktiga identiteter, fel integration, väntelägen och malformed
  input. Ren import/rendering prövades med audit-hook. Underlagets tre negativa
  I/O-prober stoppade builtins.open, io.open och os.open innan sidoeffekt.
- Separat Runtime-review godkände exakt kandidat utan blockerare. Granskaren
  rapporterade 13 unit tests och 282 egna edge-case-kontroller. Värden körde därefter
  de 13 levererade testerna samt kontorets tre ingångstester: PASS.
- Två försök och exakt en publicering. Aktiv återupptagning av redan avslutat
  uppdrag gav inga nya modellförsök eller publiceringar.
- Status/resultat jämfördes oberoende mot faktiska Runtime-kvitton och GitHub-PR,
  kandidatträd, mergeförälder och fjärr-main. 329 lokala kör-/bevis-/databasfilers
  innehåll var oförändrat efter läskommandona. Resultatets egen utskrift var inte
  ensam evidens. Se delivery-verification.json och result.json.
- Servern nekade PR1:s integration före statusar med HTTP405: två obligatoriska
  kontroller saknades. Rätt statusar sattes först efter faktiska tester och review.
  Även verklig fjärrkontroll med avsiktligt fel bas nekades före publicering.
  Fel mål, otillåtna paths, ändrad acceptans och saknad review prövas riktat.

Separat startgranskning /root/ap04_review fann AP04-R1: läsaren måste kontrollera
verkliga försökskvitton och hela providerföljden. Rättat och omkontrollerat godkänt
på Runtime 26cd64f och kontor 68ebffb; integrerade träd är identiska. Samma granskare
fann två luckor i resultatacceptansen (I/O vid import och gemensamma returfält),
vilka rättades före fryst input och godkändes med ovanstående acceptanshash.
En mellanliggande invändning om provider-fält återtogs efter verifierad felläsning.
Inget av detta stänger kampanjens A3/A6 eller historiska auditfynd.

## Bevarande, offentlighet och räckvidd

Kandidatpubliceringen omfattade bara de två granskade tillåtna källfilerna;
Publisher kontrollerade faktisk diff, filtyp, base, skydd och exakta test/review-
identiteter före push. Hela koden granskades separat före integration. Hostens
kompletterande innehållskvitto skrevs efteråt och är inte ett nytt förhandstillstånd.
Inputs och avslutspublicering kontrolleras separat före respektive push.
Privat råhistorik finns bara lokalt. Portabla .gitignore-regler hindrar att dessa
råkataloger följer med genom normal Git-add; innehållskontroll krävs fortfarande.

Native kördata och en konsekvent SQLite-backup är arkiverade lokalt i Runtime:
329 filer återlästa mot hashmanifest, SQLite integrity_check=ok. Kvitto:
native-preservation.json. Arkivet är på samma disk, inte skydd mot diskförlust.
Slutliga offentliga Git-träd får separat fjärr-/lokal arkivkontroll efter slutmerge.

Profilen är lokal och operatörsstartad. Ingen daemon, scheduler, webbpanel,
automatisk målprioritering eller ny affärsfunktion har byggts. Endast det namngivna
kontorsrepot är tillagt. Kontorsuppdrag stöder den prövade tools/-profilen med
exakta filrättigheter; den aktiva tools/kontor.py är hostägd. Legacy access/base-
omskrivning är inte aktiverad för kontorsuppdrag. Fryst Runtime-revision krävs för
start/återupptagning; framtida uppdrag ska binda sin accepterade revision.
Det verkliga nya målprovet gäller Codex med separat Codex-review. Kontorsprofilens
selector tillåter därför bara Codex; Claude för det nya målet kräver egen riktad
kvalificering. Äldre Claude-
bevis återanvänds inom sin gamla räckvidd; ingen ny faktisk Claude-skrivkörning
mot kontorsrepot påstås. Lokala bevis måste finnas för status/resultat efter kloning.

## Rekommenderad fortsättning — inte startad

Välj som nästa accepterade kontorsuppdrag en avgränsad funktion för
**beslutsbunden ändringsbedömning**: för en konkret föreslagen projektändring
visa vilka dokumenterade beslut som stödjer den, vilka som begränsar den och
vilka verkliga mål-/kostnads-/befogenhetsfrågor som måste tillbaka till ägaren.
Det ger kontoret en första sakfunktion för praxis och riktning, ovanpå den nu
prövade leveransvägen. Omfattning och klart-när behöver eget byggbeslut;
inget sådant arbete startas genom AP04-avslutet.
