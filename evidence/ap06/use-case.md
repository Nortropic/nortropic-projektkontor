# AP06 — verkligt användningsprov

Kontoret använde den levererade beredningskärnan för sitt eget återstående
AP06-uppdrag: kommandot, dess ändpunktsprov och metodanvisning. Det var framtida
arbete inom accepterat mandat, inte återspelning av ett avslutat uppdrag.

Kärnan levererades genom Runtime i PR7. Därefter valde kedjedrivaren relevanta
källor, läste dem, formulerade härledda krav och handlingsspecifikt mandat samt
angav observerbart beteende för varje planerat prov. AP05 och befintliga fil-/
hash- och uppslagsverktyg användes för bindning och jämförelse. Ursprungliga
källor, citat, identifierare och fulla spår ligger endast i privat local/.
Arbetskopior av privata källor eller råhistorik har inte förts till kandidaten.

Kärnan sammanställde sju krav, deras skäl och provkopplingar, separat författad
utförarkontext, ett taskutkast i faktiskt Runtime-format och en privat spårkedja.
Den skilde fakta, sakomdöme, beslut och befogenhet, och markerade allt som utkast.
Den uppfann inga revisioner, acceptansprogram eller befogenheter och startade
varken modeller eller publicering. Mekanisk fullständighet gav inget godkännande.

## Bevarad kedja och motiverade ändringar

1. **real-cli-v1:** första verkliga beredningen efter kärnintegration. Sex valda
   källor; sju krav och sju observerbara kontroller. Separat sakgranskning fann
   att granskningsansvaret behövde preciseras för att inte skapa en ny ägargrind.
2. **real-cli-v2:** preciseringen och starkare prov för case-alias och privata
   felutskrifter bereddes uttryckligt. V1 behölls. Kontroll mot V1:s oförändrade
   manifest efter scopeändringen markerade berörda krav för omprövning, men
   upphävde inte ägarens beslut. Separat granskning reproducerade båda versionerna.
3. **office-assignment-cli-1:** V2 granskades och frystes till en verklig Runtime-
   körning. Den nådde 12 godkända kandidatprov men stoppades av ett fel i VÄRDENS
   acceptansstartare: isolerad Python/runpy saknade vanlig scriptkatalog. Det
   missades i kontraktsgranskningen och rättas öppet i cli-host-correction.json.
   Kandidaten fick inte kringgå felet eller ändra sin acceptans. Gamla frysta
   bytes och det verkliga negativa utfallet bevaras. Ingen integration skedde.
4. **real-cli-v3:** samma krav bereddes på nytt med en explicit teknisk rättelse,
   bevarade tidigare källbindningar och ny hostacceptans/taskidentitet. Bara den
   kontrollerade scriptkatalogen tillförs startaren; sandbox, auditspärrar,
   provkrav och aktiva kärnhashar behålls. Den oförändrade Runtime-författade
   kandidaten klarade det korrigerade diagnostiska värdprovet och återanvänds
   som märkt, ännu ej godkänd referens i fortsättningsuppdraget.

5. **office-assignment-cli-2:** fortsättningen är genomförd. Runtime återställde
   referensfilerna byte för byte, körde rättad fryst acceptans och 12 ändpunktsprov,
   fick separat godkänd kodgranskning och integrerade genom skyddad PR8,
   `8e5f1c07a79ff288fc8e0a646bb9f7eb66a58f44`. Värden jämförde körbevis mot
   fjärrhuvud/träd/status utanför beredningsfunktionens egen utskrift.
6. **Levererad ingång prövad:** kommandot kördes på det verkliga V3-underlaget.
   Alla fyra utdata motsvarade den tidigare beredningen. Metodens legitima och
   negativa exempel reproducerades i isolerad native sandbox; nytt försök med
   samma utdatakatalog vägrades utan ändring. Se real-application.json och
   method-verification.json. Tidigare jämförelsetid/referenser skrevs inte över.

Privat spår: `evidence/ap06/local/real-cli-v1/`, `real-cli-v2/`, `real-cli-v3/`.
De granskade paketfälten finns i prepared-cli-package.json respektive
prepared-cli-continuation-package.json. Hostwrapper och exakt återanvänd kod
är dokumenterade tillägg till renderat brief, inga tysta mandat-/hashändringar.
Aktuellt körläge och nästa handling ägs enbart av docs/plan.md.

## Sakarbetet som kvarstår hos kedjedrivaren

Agenten måste fortfarande välja och läsa relevanta källor, förstå motsägelser,
derivera rimliga krav, bedöma faktisk handlingsspecifik befogenhet, utforma
verifiering som prövar avsedd funktion och innehållsgranska varje exportfält.
Den separata granskaren kontrollerar detta omdöme. Värden författar, granskar
 och fryser acceptansen och startar först därefter Runtime genom AP04.

Funktionen samlar upprepade bindningar och gör överlämningen konsekvent och
kontrollerbar. Ingen tidsbesparing eller minskad ägarbelastning har mätts eller
kvantifierats. Testhänvisningar och oförändrade filhashar är inte sakgodkännande.
Källjämförelsen gäller uttryckligt urval och angivet tillfälle; den bevisar inte
att senare/relevanta källor är uttömmande funna. A3/A6 och tidigare fynd behåller
sin status. Kartleveransen förblir avslutad och har inte öppnats på nytt.
