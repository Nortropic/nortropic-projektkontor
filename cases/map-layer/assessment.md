# Kartärendet — beslutsbunden ändringsbedömning, AP-05

**Sakbedömning:** den befintliga kartkandidaten kan lämnas till ägaren för
begriplighetsbedömning och ett separat, avgränsat beslut om eventuell kartleverans.
Tvålagersprincipen är redan vald. Ny läsbaserad kontroll ger stöd för de tekniska
egenskaper som berörs av den senare generatorändringen. Kartan är inte därmed
accepterad; inget skrivtillstånd till valvet finns genom AP-05.

Detta är kontorets bedömning av en verklig föreslagen förändring, inte en
kartinstallation. Underlag, observation och utförarens omdöme hålls isär nedan.
Separat granskning och revisionsbindningar redovisas i case-evidence.json och
../../evidence/ap05/case-review.md när granskningen är avslutad.

## Vad som redan är avgjort

**Källuppgift D1:** I-11 väljer ett nytt aktuellt lager bredvid det historiska,
med historiken orörd. I-10 kräver att den ersatta historiken behålls märkt.
Dessa principbeslut ska inte begäras på nytt. I-11 är uttryckligen inget tekniskt
PASS och inget skrivtillstånd. Se ../../docs/decisions.md, I-10 och I-11.

**Källuppgift F1:** FINAL-CHECK-1 §5 gav en positiv teknisk dom vid den granskade
revisionen: rättelser i tre berörda noter, 938 bevarade baslinjefiler och korrekt
redovisning av 261 tillägg. Rapportens övergripande FAIL upphäver inte just denna
avgränsade dom. Domen omfattade inte det verkliga valvet, A6, begriplighet eller
ägaracceptans. Det historiska beviset behålls med denna räckvidd.

## Senare förändring och tillämplighet

**Uppmätt källförändring F2:** generatorn och kartkvittot har andra SHA-256 än i
FINAL-CHECK-1:s identitetslista. Generatorn gick från `6cd4755e…` till `68b395ef…`;
kvittot från `e5b5fc91…` till `850f5563…`. Fulla tekniska identiteter finns i
case-evidence.json. Det är skäl att pröva domens tillämplighet, inte skäl att
upphäva I-11 eller förklara den gamla domen felaktig.

**Källuppgift F3:** ERRATA E-16/FC1-07 redovisar en ändring i kartans ingång
2026-09-20 kl. 16:17 UTC för att införa I-10:s bevarade, märkta historik. Den
aktuella ingången har denna innebörd och behåller varningen om ej godkänd
kompilering. Gamla generator- och kvittobytes hittades inte i den riktade
sökningen. Därför påstås ingen exakt historisk kod-diff eller att denna rad
var den enda ändringen.

**Kontinuitet F4–F5:** IR och tolv Markdown-familjefiler matchar den gamla
identitetslistan. Baslinjekvittot matchar den äldre kontrollens identitet. Tolv
aktuella JSON-familjekällor matchar dagens kvitto, men den historiska identiteten
för alla dessa JSON-filer kan inte härledas ur oförändrade Markdown-filer.
Varken hashjämförelsen eller dagens eget generatorkvitto räcker som sakgodkännande.

## Nya avgränsade observationer av dagens kandidat

Värden läste den befintliga kandidatkopian 2026-09-20 kl. 18:47:13 UTC.
Ingen generator kördes. Originalkällor, IR och verkligt valv ändrades inte.
Runtimes befintliga evidence_index användes för bytekontrollerna.

| Observation | Resultat | Vad den inte visar |
|---|---|---|
| F7: kandidat mot bevarat baslinjekvitto | Alla 938 filer har samma SHA-256 och byteantal; inga saknade | Att det verkliga valvets nuläge fortfarande motsvarar baslinjen |
| F8: faktisk tilläggsmängd | 261 filer: 260 i nya lagret, en pekarnot utanför; exakt förväntad mängd från dagens JSON-struktur och fasta ingångar | Sakinnehållets riktighet eller tillstånd att lägga in filerna |
| F6: rättelsetäckning | Tre berörda noter har rättelsen på rad 3 före berörd brödtext; nottiteln kan stå före rättelsen | Alla möjliga språkliga omformuleringar eller framtida generatorutdata |
| Kontroll efter läsning | Samtliga 1199 uppmätta kandidatfiler matchade fortfarande sina nybundna identiteter | En atomisk snapshot eller upptäckt av alla senare/nya källor |

Rättelsesökningen omfattade 1194 UTF-8-läsbara filer, inklusive alla 261 tillägg,
ingång, canvas och pekarnot. Fem historiska binärfiler omfattades av bytekontrollen,
men inte textsökningen. Regeln var bredare än generatorns egen:
`\benda\b[^\n]{0,80}(?:lär|inlär)|\blär(?:ande)?loop[^\n]{0,80}\benda\b`,
med skiftlägesokänslig matchning. Tolv radträffar klassades manuellt: tre rättelserader,
åtta relevanta rader i de tre rättade noterna och en irrelevant träff om ägartur.
Det är en avgränsad lexikal och manuell kontroll, ingen generell språkgaranti.

**Egen bedömning J1–J3:** tidigare bevis återanvänds som historisk grund. De nya
observationerna ger separat stöd för dagens rättelsetäckning, baslinjebevarande
och lagergräns. Saknad historisk kod-diff behöver därför inte ensam blockera
ägarens nästa kartbeslut. Detta är ett nytt avgränsat omdöme om de faktiskt
observerade egenskaperna, inte en tyst förlängning av FINAL-CHECK-1:s revision.

## Befogenhet för konkreta handlingar

| Handling | Befogenhet i detta ärende |
|---|---|
| Bedöma källorna och göra de relevanta läskontrollerna | Givet genom AP05-ACCEPT; utfört |
| Förbereda och lämna detta beslutsunderlag | Givet genom AP05-ACCEPT |
| Skriva kodstöd och bevara bedömningen i kontorsprojektet | Givet genom AP05-ACCEPT, via befintlig Runtime-väg |
| Publicera innehållskontrollerad fallredovisning i kontorsrepot | Givet genom AP05-ACCEPT; interna källor och råhistorik omfattas inte |
| Acceptera själva kartförändringen | Inget sådant ägarbeslut finns här |
| Skriva nytt lager/pekarnot i det verkliga valvet | Inte givet; separat uttryckligt skrivbeslut krävs |
| Publicera kartmaterial eller interna källor | Inte givet genom AP-05 |

En oförändrad referens eller giltig datastruktur ändrar ingen av dessa befogenheter.
Funktionen redovisar uppgiven befogenhet och dess källa; den autentiserar inte
beslutsfattaren och delar inte ut tillstånd.

## Exakt nästa handling och återstående underlag

Nästa utförare lämnar **den befintliga, bundna kandidatens ingång, översikt och
lagerförklaring** till ägaren genom befintlig privat läsåtkomst. Källmappningen
finns lokalt enligt ../../evidence/ap05/local/case-history.json; publicera inte
kandidatfilerna för att göra dem lättare att visa.

Ägarens återstående omdöme är konkret: går det att förstå vilket lager som är
aktuellt respektive historiskt, hur man når källorna och vilka uppgifter som är
beslut, förslag eller obestyrkta? Tvålagersprincipen ställs inte på nytt.

Det återstående beslutet är om **ett separat, avgränsat kartleveranspaket** får
kontrollera det namngivna målvalvets aktuella läge och namnkonflikter samt därefter
skriva just den bedömda kandidatens nya lager och pekarnot, med historiken orörd.
Det paketet behöver binda exakt mål, aktuell baslinje, kandidat och bevarandepunkt
före skrivning. Vid kollision eller ändrat underlag omprövas berörda slutsatser;
ingen överskrivning motiveras av AP-05. Sådant mandat och sådana målvalvsbevis
finns inte i denna leverans. Nästa fas startas inte automatiskt.

A3, A6, FIND-004 och övriga tidigare auditfynd står kvar. Ingen IR-audit,
omkompilering, kampanjtotalgranskning, kartinstallation eller ny Runtime-förmåga
påstås här. Generatorns lexikala begränsning kvarstår även efter denna kontroll.

## Var kodstödet tillför arbetsförmåga

Agenten gjorde sakläsningen och omdömet; beslutsloggen innehåller beslutens status.
Kodstödet gör det upprepade samordningsarbetet: kontrollerar att skäl och källor
finns, binder en jämförelse till rätt referensversion, skiljer uppgift/omdöme/befogenhet
och räknar fram vilka slutsatser och handlingar som berörs av ändrat, saknat,
otillgängligt eller okontrollerat underlag. Nästa utförare behöver inte manuellt
återskapa hela denna beroendekedja ur en fri agenttext.

Tidigare bedömningar bevaras. En ny författad version motiveras separat;
referenshashar uppdateras aldrig av kontrollfunktionen. En aktuell bytekontroll
av det valda urvalet är inte en komplett källsökning. Nytillkomna filer utanför
urvalet upptäcks inte automatiskt: en ändrad kandidat kräver också uttrycklig
ny inventeringsobservation inom det relevanta ärendet. Se
../../tools/CHANGE_ASSESSMENT.md för den återanvändbara metoden.
