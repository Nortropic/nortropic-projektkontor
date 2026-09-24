# AP11 — ändligt utvecklingsansvar utan aktiv interaktiv kedjedrivare

2026-09-21. **FÖRSLAG; endast beredningen är beställd.** Planen i
`docs/plan.md` äger aktuellt steg och nästa handling. Ingen aktivering ingår nu.

## Resultatet att acceptera

Kontoret kan bära ett namngivet, accepterat utvecklingsmål i sitt eget repo:
läsa ett faktiskt delresultat, bereda nästa nödvändiga tekniska uppgift, låta
separat granska uppgiften och dess prov, genomföra den genom Runtime och följa
upp resultatet — även när den interaktiva kedjedrivarsessionen har avslutats.
Det gäller ett ändligt åtagande, inte rätt att hitta på nya verksamhetsmål.

Ägaren ska inte behöva återstarta projektledningen genom en ny prompt efter
varje uppgift eller bära granskarnas fynd mellan sessioner. Tekniska omtag ska
ha konkret diagnos och bevarad historik. Verkliga mål-, kostnads- och
befogenhetsändringar återkommer som ett samlat beslut.

## Varför nu och vad som redan fungerar

Definitionen anger planera, bygga, testa och försöka igen utan att AI bestämmer
sin egen befogenhet; den vill bort från ständig terminaldialog. I03 gäller
minskad samordning, I04 kontoret först och Digitala därefter. Det rättade
byggförslaget §8 lämnade stående ansvar och executive-funktionen öppna.
AP10 har nu löst ett namngivet bevakningsansvar, inte alla slags ansvar.

AP04–AP10 tillgodoräknas: en aktiv kedjedrivare kan redan driva ett accepterat
mål genom flera beroende uppgifter, separat granskning och integration.
Detta byggs **inte** en gång till. AP05/AP06 ger källbedömning och beredning;
AP08 en daterad läsbild; AP07 förblir frivilligt ANPASSA utan belagd förbättring.
Kartleveransen och tidigare auditstatus förblir avslutade inom sin räckvidd.

Den återstående skillnaden är operativ: AP04 tar ett fryst uppdrag. Diagnos,
nya uppdragsunderlag och övergångar mellan uppdrag har fortfarande en aktiv
värd/kedjedrivare som bärare. AP10:s privata bedömare får inte ändra kod,
skapa bygguppdrag eller publicera. Den ska inte få dessa rättigheter nu heller.
Att en påbörjad DevelopmentTask fortsätter är inte bevis för att nästa uppgift
bereds och drivs utan den interaktiva kedjedrivaren.

Prioriteringen är **vår nya rekommendation**, inte ett dolt tidigare byggbeslut.
Vi tar upp denna återstående del av §8 före Digitala för att göra kontorets
eget utvecklingsansvar uthålligt. I04 anger inte när Digitala måste starta.
Vi tillskriver inte byggförslagets illustrativa webbprojekt status som beställning.
En extra uppdragsyta eller generell projektmotor har inte ett visat behov här.

## Återanvändning och verkliga luckor

| Del | Redan levererat / mandatfråga | Det som behöver tillkomma |
| --- | --- | --- |
| Professionellt omdöme, uppdelning, källor | Befintlig agent, AP05/AP06, plan och beslut. Ägaren behöver tillåta teknisk uppdelning inom fasen, inte varje fil | En avgränsad körprofil för samma agent som kan bära detta ansvar mellan interaktiva sessioner |
| Genomförande | AP04:s frysta task, kodprov, granskningsåtergång och skyddade Publisher | Koppling från separat granskad härledd uppgift till befintlig start/fortsättning; inga ersättningar för dessa mekanismer |
| Beständighet | Temporal, befintlig tjänst/databas, försökshistorik | Ett namngivet ändligt utvecklingsåtagande som återkallar agenten vid faktiskt delresultat och bevarar vilken nästa handling som får ske |
| Slutresultat | AP04 visar enskilda leveranser; AP08 återger tillförda bedömningar | Samlad avstämning av just åtagandets krav mot flera faktiska delresultat, fortsatt arbete och handlingsspecifik befogenhet |
| Ägarbesked | AP08:s befintliga privata HTML | Underlag från samma utvecklingsåtagande till AP08, ingen ny dashboard/server eller beslutskanal |

Ingen generell mandatdatabas, målrouter, metodplattform, ny scheduler eller
ny agentmodell föreslås. Temporal äger körstate; planen äger sakligt nästa steg.
Planen får inte bli en andra exekveringskö. Exakt kodmängd avgörs genom minsta
nödvändiga koppling; ny kod är inget fristående acceptanskriterium.

## Fem delmål och deras beroenden

1. **Bind utvecklingsåtagandet.** Efter fasaccept: bind mål, aktuella källor,
   tillåtna effekter, budget, slutkrav och nedanstående verkliga leveransdelar.
   Låt granska den övergripande acceptansen före implementation. Befintliga
   mål-/körbevis återanvänds; ingen ny allmän kvalificering. Resultat: ett
   körbart avgränsat mandat och separat granskad acceptans, inte ett nytt målval.
2. **Etablera minsta beständiga drivarkoppling.** Beroende av 1. Återanvänd
   befintlig agent och Temporal för läsning/beredning, separat granskning och
   begränsad värdöverlämning till AP04. Frys drivare, mandat och övergripande
   acceptans. Integrera små granskade ändringar före aktivering. Resultat:
   nästa tillåtna steg kan tas utan en aktiv interaktiv drivarsession; privata
   data och Publisher-rättigheter hålls utanför byggkandidaten.
3. **Låt vägen leverera de återstående kontorsdelarna.** Beroende av 2.
   Två verkliga, nödvändiga delar ingår redan i denna accept:
   **A: leveransavstämning för just AP11** som binder dess namngivna målkrav och
   underuppdrag till faktiskt granskade och fjärrintegrerade uppdragsresultat,
   öppna luckor och nästa tillåtna handling. Befintliga AP04-resultatläsare
   återanvänds; detta är ingen generell resultatmotor eller ny tillitsregel.
   **B: överlämning/läsning** av samma åtagande genom AP08 och befintlig
   resultatväg, så att en mottagare kan fortsätta rätt arbete utan återberättelse.
   B tillför A:s avstämning/fortsättningspunkt till befintliga läsare och
   renderare; ingen parallell beslutslogg eller ny beslutsauktoritet byggs.
   B ska beredas från A:s faktiskt integrerade gränssnitt och observerade
   resultat, inte bara vara en i förväg fryst andra task. Dessa delar är
   driftens användbara resultat-/överlämningsfunktion, inte demonstrationskod.
   De får inte ändra den aktiva drivaren, mandatet eller den övergripande
   verifierare som bedömer deras eget försök.
4. **Pröva självständigt fortsatt arbete och avbrott.** Beroende av 3:s verkliga
   pågående arbete. Visa en övergång efter verifierat avslut av den interaktiva
   start-/drivarsessionen, sedan en faktisk återupptagning av kvarvarande arbete
   från sparat läge. En separat observatör får läsa bevis, men inte driva eller
   signalera kedjan under det påstått självständiga intervallet. Relevant
   underkännande/diagnos och mandatöverskridande prövas separat i isolerade
   provytor när sådant inte uppstår naturligt. Syntetiska utfall märks som sådana.
5. **Slutgranska hela åtagandet och avsluta det.** Beroende av 3–4. Oberoende
   granskare jämför verkliga native-historier, frysta revisioner, acceptans,
   separat kandidatgranskning och fjärrintegration. Leveransavstämningens egen
   utskrift är inte ensam bevisning. Spara slutkvitto/återupptagningspunkt och
   AP08-besked. Avsluta just detta utvecklingsåtagande; endast AP10:s accepterade
   Python-/Temporalbevakning har fortsatt stående mandat.

## Faktisk Runtime-passform och skydd för pågående drift

Läst aktiv Runtime: `ac62629983805015e8c0c040098c2d5287dbc41e`.
Aktiv kontorskod: `09e1e44f7ba2fc5522e3137da01d528ec7138a10`.
Kontorets senare dokumentleverans är `5845a700afb09fb397c6d877029eb20329a10b05`.
Privat beredning binder aktiv konfiguration och jämför utvald läst kod med de
faktiskt frysta filerna. Denna läsning är inte en ny AP10-driftkvalificering.

Faktisk profil: ett fryst Office-uppdrag, Codex, uttryckliga `tools/`-filer,
0 automatiska modellomtag, fryst värdacceptans och separat Publisher. Privat
bevakning har en annan begränsad profil. Workern har en aktivitetsplats.
AP06:s befintliga format räcker för underuppgifter; det är inte redan ett
format eller en auktorisation för ett beständigt utvecklingsåtagande.

**Runtime-kompletteringen i delmål 2** är just kvalificerad beständig körning
av den avgränsade kedjedrivaren, granskad uppgiftsöverlämning, bevarad väntan/
diagnos, åtagandebundet paus/stopp och avslut. Kontorets omdöme, krav, källarbete och leveransavstämning
hör till kontorsrepot. Ingen verksamhetskod flyttas in i Runtime för att passa
ett gammalt skrivfilter. Den befintliga privata bevakningsprofilen vidgas inte.

Bygggrenar och kandidater använder isolerade kopior och ändrar inte aktiva
releaser, instruktioner eller konfiguration. Den nuvarande aktiva Runtime kan
inte bara bytas ut medan den delade tjänsten kör. Därför behövs uttryckligt
mandat för **ett kontrollerat revisionsbyte av den delade körningen** efter
skyddad integration och riktad separat samexistensgranskning. Det omfattar
bevarande/återläsning av historik och konfiguration, dränering av eget arbete,
verifiering att ingen annan skrivare är aktiv och kontrollerat återtag vid fel.
Det får inte bli en andra motor/databas eller automatisk tom återställning.

AP10:s källurval, sakbeslut, schema, anropsgränser och rättigheter bevaras.
Byte får inte aktivera gamla väntande byggen, starta en extra bevakningsomgång
eller skriva om körhistorik. Giltiga AP10-bevis gäller tidigare revisioner;
ändrad gemensam kod får en riktad kompatibilitetskontroll, inte lånat PASS.

En lång byggaktivitet kan annars förbruka bevakningens 1 200 sekunders kö-
och körtid. Delmål 2 ska därför visa kontrollerad tilldelning av den delade
aktivitetsplatsen: bevakningen skyddas vid ordinarie tillfälle och nytt
byggarbete väntar när tillräckligt utrymme saknas. Ingen höjning av AP10:s
budget/frekvens, ny parallell modellkörning eller andra schemaläggningsmotor
är tillåten genväg. Går detta inte inom ramen redovisas hindret före aktivering.

## Operatörskontroll över just utvecklingsåtagandet

Befintlig värd/behörig kedjedrivare ska kunna pausa, återuppta och stoppa
åtagandet. Kontrollerna är explicita handlingar; statusläsning gör dem aldrig.
- **Paus:** inga nya underuppdrag eller diagnostiserade omtag startas. En redan
  startad underuppgift får avsluta sin befintliga implementation, granskning
  och skyddade integration inom det redan givna mandatet. Pausen består över
  process-/sessionsbyte. Återupptagning kräver explicit behörig handling men
  ingen ny fasbeställning när mandatet och budgeten fortfarande gäller.
- **Stopp:** inga nya drivsteg, underuppdrag, omtag eller ännu ej påbörjade
  publiceringar får starta. Endast åtagandets egna aktiva utförar-/granskar-
  processer avbryts kontrollerat och deras avslut verifieras. En redan skickad
  fjärreffekt kan inte garanteras återkallad: bevara identitet/resultat som
  osäkert tills en läsande avstämning fastställt vad som faktiskt integrerats.
  Ingen blind ompublicering, force push eller återställning följer av stopp.
- **Återkallat mandat:** fortsatt skrivning/start/publicering nekas; det kan
  inte återöppnas av modellen eller vanlig återstart. Ny ägarbefogenhet krävs.

Stopp får inte döda den delade tjänsten, ändra AP10:s paus/schema eller avbryta
orelaterade byggen. Kandidaten får varken kontrollera sin egen stoppstatus eller
utvidga aktiveringsrätten. Det namngivna Runtime-tillägget måste verkställa dessa
gränser även för redan köade aktiviteter; instruktionstext ensam räcker inte.

## Slutacceptans och negativa fall

Klart först när samma accepterade mål, utan nya ägarbeställningar mellan
tekniska steg, har gett två beroende verkliga Office-leveranser enligt delmål 3
med separat granskning och skyddad integration. Minst nästa uppdrag måste ha
beretts ur föregående verkliga utfall efter drivarsessionens avslut. Att bara
köra två på förhand frysta uppgifter i följd räcker inte.

Slutgranskningen ska också visa:
- återupptagning utan förlorad historik, dubbla effekter eller konkurrerande
  skrivare, samt faktiskt fortsatt arbete av behörig färsk mottagare;
- stopp vid saknat/ändrat relevant underlag, oklart mandat, saknad granskning,
  osäker fjärrintegration eller otillgängliga bevis; inget tyst positivt besked;
- att skrivförsök mot aktiv drivare/acceptans/mandat, annan repo, AP10-config
  eller privata original avvisas, i isolerade negativa prov;
- att paus består, stopp hindrar nya egna effekter och återkallat mandat inte
  återöppnas av omstart; aktiv child/review och oklar publicering hanteras
  enligt ovan utan påverkan på AP10 eller andra uppdrag;
- att läsning av läge/resultat/AP08 inte startar modeller, fortsätter eller
  publicerar; avsaknad av färsk observation syns;
- att självständigt fönster, tillåtna externa operatörsåtgärder och eventuella
  manuella ingrepp redovisas exakt. Övervakad provkörning får inte kallas helt
  obemannad drift. Ingen uppmätt tidsbesparing eller generell autonomi påstås.

## Nya tillstånd som föreslås samlat

1. Implementera, testa, separat granska och skyddat integrera denna begränsade
   kontorsförmåga och dess nödvändiga Runtime-koppling i de två befintliga repona.
2. Aktivera **ett ändligt namngivet utvecklingsåtagande för AP11** på befintlig
   dator/abonnemang. Kedjedrivaren får själv bereda och efter separat granskning
   binda tekniska underuppdrag/acceptans inom fasens oförändrade övergripande
   krav, starta dem, hantera konkreta granskningsfynd och integrera via befintliga
   grindar. Den får inte ändra sitt eget mandat, aktiva drivare eller slutkrav.
3. Göra det uttryckliga kontrollerade revisionsbytet av den delade tjänsten
   enligt ovan. Ingen tyst aktivering via branchbyte och ingen ändring av
   bevakningsåtagandets verksamhetsomfattning följer av detta.
4. Publicera innehållskontrollerad kod, syntetiska prov, anvisningar och
   begränsade bevis i respektive befintligt publikt repo. Privata källor,
   lokala användningsdata och råhistorik förblir privata.

För första självständiga tillämpningen föreslås högst **48 modellprocessanrop
sammanlagt** för drivning, beredningsgranskning, implementation, kandidatgranskning
och teknisk diagnos efter aktivering; budgeten består över omstart. Högst sex
implementationsförsök per underuppgift, varje omtag kräver ny konkret diagnos,
0 blinda automatiska omtag. Befintligt maximalt anropsintervall överskrids inte;
delad kapacitet kan kräva kortare intervall. Det är ett föreslaget resurstak,
inte prognos, token-/kostnadsgaranti eller tidsgräns för projektet. Vid kvotbrist
bevaras arbete; vid uttömd accepterad ram stoppas nya anrop och verkligt behov
av utökning redovisas. Inga nya abonnemang, modeller, tjänster eller köp ingår.

Ingen annan repo, externa kunder/kundkontakt, Digitala-etablering, valvskrivning,
beroendeuppgradering, stående utvecklingsprogram eller självförbättring ingår.
A3/A6/FIND-004 och övrig tidigare auditstatus påverkas inte.

## Genomförande efter accept

Kedjedrivaren hanterar alla fem delmål och tekniska omtag inom samma fasmandat,
med små granskade integrationer och bevarad kontinuitet. Daterade AP08-besked
efter väsentliga resultat är information, inte nya ägargrindar. Nästa fas startas
inte automatiskt. Innan accept utförs endast denna beredning.
