# AP-07 — prövad metodförbättring från verkligt kontorsarbete

STATUS: förslag till ett samlat byggbeslut, inte accepterat byggmandat.
Beredningsmandatet gäller endast detta förslag. Paketet använder levererad AP05/AP06;
byggstart, metodprov och publicering väntar på uttrycklig accept.

## Vad Nortropic får och varför nu

Kontoret ska kunna ta ett belagt arbetsproblem, välja ett tillräckligt arbetssätt
ur lästa primärkällor, göra ett litet relevant försök, värdera utfallet och lämna
**anta, anpassa eller avstå** med spårbara skäl. Det är en avgränsad, beställd
metodtillämpning för Nortropic som Customer Zero, inte en stående lärmotor.

Första problemet: i AP06 granskades en värdlauncher som sedan saknade fungerande
syskonimport i den verkliga isolerade provkontexten. Det upptäcktes först när
Runtime redan hade byggt CLI-kandidaten. Produktfilerna kunde därefter återanvändas
byte för byte. Felet är redan rättat och AP06 levererad. Det som saknas är prövad
överförbar metodkompetens för att välja ett tidigt representativt prov av ett
osäkert integrationsantagande, i stället för att bara skriva ännu en kontrollregel.

Agent + beslutslogg kan redan resonera och minnas; AP05 binder källor och AP06
sammanställer uppdrag. Inget av deras leveransbevis visar att en färsk utförare kan
välja, tillämpa och begränsa denna metod i ett annat fall. Det är den nya förmågan
som ska visas. Ägaren ska inte behöva välja metodnamn, provkommandon, förmedla fynd
eller avgöra varje tekniskt omtag. Ingen tids- eller procentsparande effekt påstås.

## Placering i gällande byggordning

Definitionens praxis/metoder, I-03 och I-04 samt BYGGFORSLAG §1.4 och §4.1 är grund.
Etableringen, AP04, AP05, AP06 och KART-INFORANDE-01 räknas som levererade inom sina
räckvidder. AP06 täcker den relevanta briefberedningen ur äldre AP02; ingen ny sådan
mekanism föreslås. FK/repoövergången och motorvalet görs inte om.

BYGGFORSLAG §8, rättat genom E-15 och I-07b, lämnade lärandespåret väntande på utfört
kontorsarbete. AP04–AP06 ger nu körningar, fel och omtag att lära ur. Min rekommendation
är att ägaren bedömer detta som tillräckligt för **denna enda pilot**. Det är en
konkretisering av det väntande spåret, inte automatisk upphävning av väntan eller
ett mandat för Evolution Plane, bevakning, schemaläggning eller självägda förändringar.

## Omfattning och verkliga fall

1. Återanvänd AP06:s belagda händelseförlopp som utvecklingsfall. Formulera före prov
   hypotesen att ett kort representativt försök med redan befintligt beroende kan
   skilja fel i värdens provkontext från fel i den framtida produkten. Vid den gamla
   CLI-basrevisionen fanns beredningskärnans syskonimport redan; den framtida CLI:n
   får inte användas som förutsättning för ett påstående om upptäckt före dess bygge.
   Gamla lyckade diagnos-/rättelseprov räknas inte som nya effektbevis.
2. Jämför två tillräckliga arbetssätt: käll-/kontraktsläsning med vanlig separat
   granskning, respektive samma läsning med ett valt litet körbart prov av den
   osäkra kopplingen. Metodkällor: IHI:s PDSA för att planera/pröva/studera/anpassa
   en förändring, och GOV.UK:s alpha-vägledning om minsta prov av det riskfyllda
   antagandet. Det är vår avgränsade tillämpning; vårdområde respektive offentlig
   tjänsteutveckling gör dem inte till en bevisad Nortropic-standard. Ingen full
   alpha-process, tidsnorm, standardcertifiering eller metodplattform importeras.
3. Pröva överföring med en färsk utförare på **AP05:s första metodrecept mot
   evidence_index**. Den bevarade kandidaten c4ac46ba3d14467a74680a4da5681c08eb1ce7ae
   antog manifest som argv-operand; verktyget använder stdin. Detta är en annan
   gränssnittsfråga än syskonimport. Underlaget fanns efter första kandidatbygget:
   provet avser beslut före rättelsebygge/fortsatt integration, inte före första
   bygget. Den historiska granskaren hittade redan felet; nyttan får inte redovisas
   som överlägsen den granskningen utan nya belägg.
4. Ge utföraren avgränsat dåvarande recept/verktygsunderlag och den nya
   arbetsbeskrivningen, utan rättelseprotokoll eller facit. Låt utföraren först
   ange risk, vald metod, förväntat observerbart utfall och beredningsrekommendation;
   därefter välja och utföra minsta prov på syntetiska data, och motivera eventuell
   ändring av rekommendationen. Separat korrekt kontrastfall ska kunna fortsätta
   utan fabricerat fel eller omotiverad ny grind. Urvalet är historiskt och värden
   känner facit; begränsningen ska redovisas, ingen full blindning påstås.
5. Leverera en användbar arbetsbeskrivning med körbara isolerade exempel, en faktisk
   tillämpningsredovisning och separat sakgranskat metodbeslut anta/anpassa/avstå.
   Bara en underbyggd metodändring tas in i kontorets arbetssätt. Ett negativt
   metodutfall är tillåtet; ett dokument utan genomförd tillämpning är inte leverans.

## Återanvändning, hemvist och utförande

Mål: Nortropic/nortropic-projektkontor. Befintlig agent, plan, beslutslogg, AP05,
AP06, evidence_index, källuppslag, Python och AP04:s Runtime-väg återanvänds.
Inga nya program, installationer eller tjänster krävs för att bereda paketet.

Efter accept används Runtime för den avgränsade metodartefakten
`tools/METODPROV.md`: instruktion, tillämpningsgräns och syntetiska körbara exempel.
Det är verksamhetsmetodik i kontorsrepot, inte logik i Runtime. Inget nytt beständigt
kontrollprogram byggs. Värden utför verklig källäsning och tillämpningsprov med
befintlig åtkomst; Runtime-kandidaten får endast självständig innehållskontrollerad
brief och syntetiska data. Privata källor och råsessioner får inte följa med.

Runtime-revision 2789ea0770e4234161e9bdb0378a6e3e7b8432d2 stödjer kontorsrepo,
Codex och explicita tools/-filer. Metodfilen ryms i befintlig profil. Kandidaten
har ingen nätåtkomst eller privat källåtkomst; källäsning läggs därför inte på den.
Fryst värdacceptans, separat kandidatgranskning och skyddad integration återanvänds.
Aktiva verktyg, värdacceptans, gamla frysta tasks och Runtimes kod ändras inte.
Sakgranskning av metodens effekt är skild från mekanisk kontroll av exempel.
Metodartefaktens eventuella tidiga integration måste vara märkt som prövningskandidat;
ingen metodadoption bokförs förrän tillämpningsprovet och sakgranskningen är klara.

## Klart när — prövat beteende, inte dokumentmängd

- Källor och ursprungliga fel/rättelser är bundna till versioner. Fakta, hypotes,
  metodval och faktisk befogenhet är åtskilda. Berörda ändrade källor ger omprövning.
- Utvecklingsfallet visar om ett representativt prov går att formulera med bara
  då tillgängliga komponenter; befintliga rättelsebevis återanvänds med sin räckvidd.
- En färsk utförare kan överföra arbetssättet till AP05-fallet: före/efter-beslut,
  faktiska observationer och skäl finns, med korrekt kontrastfall. Sakgranskaren
  bedömer provets representativitet och vad som tillförts jämfört med vanlig läsning.
- Syntetiska negativa prov täcker missvisande provmiljö, felaktigt anropsantagande,
  saknad/ändrad källa och saknad befogenhet; ursprungsmaterial och gamla bevis orörda.
  Godkända exempel ger aldrig automatiskt rätt att bygga, godkänna eller publicera.
- Runtime-metodartefaktens frysta exempelkontroll och separata granskning passerar;
  slutlig metodbedömning har inga olösta blockerare. Slutsatsen kan vara avstå,
  men återanvändbar metodbeskrivning och faktiskt genomfört tillämpningsprov krävs.
- En ny mottagare hittar användning, begränsningar, resultat och nästa handling
  utan ägarens återberättelse. Kontrollerat innehåll integreras skyddat; slutbevis
  binder faktiskt använda kontors-/Runtime-revisioner och privat bevarande.

## Det samlade beslut som behövs

Acceptera AP07:s ovanstående omfattning och bedöm att utfört kontorsarbete enligt
I-07b räcker för denna pilot. Ge kedjedrivaren mandat att genomföra och separat
granska metodpiloten, köra det avgränsade Runtime-uppdraget, fatta tekniska
anta/anpassa/avstå-beslut inom omfånget och integrera metod/resultat efter grindarna.
Publiceringstillstånd avser endast innehållskontrollerad metod, syntetiska exempel,
nödvändiga uppdragsunderlag och begränsad fallredovisning i befintligt kontorsrepo.
Privata kopior, källidentifierare/sökvägar som röjer privat innehåll och råhistorik
stannar privat. Tekniska uppdelningar och rättelser kräver inga nya ägarprompter.

Inga nya tekniska rättigheter, konton, kostnader, externa mottagare, målrepon,
Runtime-ändringar, kampanj-/IR-/valvskrivningar, stående drift eller ny obligatorisk
grind ingår. Ändrat mål/kostnad/befogenhet går till ägaren. Ingen nästa fas startas.
I-08:s frågor förblir obesvarade: piloten begränsar sitt förbättringspåstående,
redovisar motbevis/urvalsbegränsning, använder AP05 vid ändrat underlag och ger sig
aldrig egen auktoritet. A3/A6 och tidigare fynd behåller status och betydelse.

## Berett, ännu inte fryst för körning

AP05-fall, källmanifest, mätning, uppslag, krav/prov och AP06:s verkliga utdata
bevaras privat under `evidence/ap07/local/package-v1/`. En läsbar beredningsrapport
och separat granskning länkas från planen. Det mekaniska utkastet ska ha luckor för
nytt byggmandat och ännu inte författad/granskad/fryst värdacceptans. Inga falska
hashar fylls i för att kalla det körklart.

Efter accept: lägg till det verkliga beslutet i en ny bevarad beredningsversion,
kontrollera endast ändrade beroenden och aktuell bas, författa/granska/frys teknisk
acceptans genom befintlig väg och genomför samma paket. Börja inte om ur tom kontext.

Metodkällor lästa vid beredningen:
- https://www.ihi.org/library/tools/plan-do-study-act-pdsa-worksheet
- https://www.gov.uk/service-manual/agile-delivery/how-the-alpha-phase-works
