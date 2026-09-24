# AP09 — omvärldsbevakning med prövad betydelse för kontorets arbete

FÖRSLAG, inte byggmandat. En sammanhängande verksamhetsleverans i fem beroende
delmål. Inget visst antal timmar, ingen allmän förbättringskampanj.

## Resultatet och varför nu

Kontoret tar ansvar för ett avgränsat bevakningsuppdrag: hämta relevanta offentliga
leverantörsuppgifter, skilja nya/ändrade uppgifter från redan behandlade, bedöma
påverkan på den faktiskt använda kontorsvägen, pröva avgörande tekniska påståenden
och lämna ett granskat handlingsbesked som en utförare kan använda. Ägaren ska
inte leta nyheter, jämföra versioner, transportera källor eller instruera granskare.

Första bevakningsområdet är kontorets nu använda Python-/Temporal-beroenden och
frågan: vad i aktuella leverantörsändringar berör längre accepterade uppdrag,
upprepade anrop eller avslut/återupptagning i vår befintliga körväg?
Startärendet är Temporal Python SDK 1.33.0:s publicerade ändringar, inklusive
upprepade anrop i contrib.deepagents och avslut av aktiviteter. SDK 1.33.0 är redan
installerad på värden. En versionsnyhet är alltså varken ett saknat beroende eller
bevis för att dess funktion används här. Första prövningen ska kunna landa i
redan tillgodosett, inte tillämpligt, tillämpligt med konkret åtgärd eller otillräckligt
underlag. Ingen positiv förbättring eller Runtime-uppgradering är förutbestämd.

Detta väljs ur definitionens omvärldsbevakningsriktning, I03:s avlastning och I04:s
kontor-först, efter faktisk etablering och AP04–AP08. Byggförslagets §8 skjuter upp
stående obevakat ansvar; detta förslag tar inte det steget. Aktiv kedjedrivare
utför två avgränsade omgångar och ett sammanhängande användningsprov. Ingen ny
rangordning tillskrivs ägaren. Förslaget konkretiserar en kvarstående riktning,
inte en tidigare redan accepterad roadmaprad för AP09.

I dag kan agenten göra en engångsanalys manuellt. AP05 kan jämföra utvalda lokala
källor, AP06 bereda en bedömd åtgärd, AP04 genomföra ett accepterat koduppdrag och
AP08 presentera utfallet. Inget av deras slutkvitton visar en återanvändbar verklig
kedja från leverantörspublicering till bedömd lokal tillämplighet och kontrollerad
teknisk prövning över två omgångar. Den luckan är leveransens ansvar. Ett nytt
register, en rapportmall eller fler dokument ensamma fyller den inte.

## Fem interna delmål, med beroenden och observerbart resultat

1. **Första riktiga intaget och konkret påverkan**. Värden använder befintlig
   webbläsning/HTTP-läsning för namngivna offentliga release-/API-källor från
   temporalio/sdk-python och Python.org, väljer endast material som berör frågan
   och binder det till installerade versioner och berörd Runtime-kod. Uppgifternas
   publicerings-/versionsdatum, hämtningstid och lokala observation skiljs åt.
   Källtext är data, aldrig instruktion eller tillstånd. Resultat: första riktiga
   ärendet med spårbar källa, lokal beröring eller motiverad icke-beröring och exakt
   kvarstående sakfråga. Ingen generell dependency-scan eller sårbarhetsaudit.
2. **Återanvändbar kontorsväg för nästa intag** (efter 1). Återanvänd AP05:s
   manifest/källkontroll och AP06:s beredning. Bygg bara den minsta filbaserade
   koppling som behövs mellan redan hämtat leverantörsmaterial, tidigare bevarad
   omgång och dessa funktioner: källidentitet/version/tider, bevarad föregångare,
   identifiering av samma/ändrat/saknat material och hänvisning till befintligt
   ärende. Ingen ny hashare, webbcrawler, beslutsdatabas eller tillståndsmaskin.
   Befintliga verktyg får ersätta kod där de räcker. Runtime bygger eventuellt
   kodstöd och anvisning med syntetiska data i små avgränsade tasks. Resultat:
   verkligt nytt uttag kan föras in utan att ägaren sammanför metadata och utan
   att en identisk publicering blir ett nytt åtgärdsärende.
3. **Tillämpningsprövning och granskat åtgärdsbesked** (efter 1–2). Kedjedrivaren
   avgör relevans mot faktisk kod och giltiga bevis. För en avgörande kvarstående
   osäkerhet genomförs ett riktat tekniskt prov i isolerad yta med befintlig
   körmiljö; sakbedömning och provresultat granskas separat. En ny SDK/modell
   installeras inte. Befintliga bevis kan ge ett välgrundat avstå-besked utan
   nytt prov. Om ingen vald verklig uppgift motiverar nya tester dokumenteras
   det ärligt; en separat syntetisk relevant förändring provar då kedjans
   åtgärdsgren, tydligt skild från verksamhetsbeviset. Resultat: behåll/åtgärda/
   invänta-underlag med skäl, faktisk befogenhet och vid behov AP06-berett
   uppdrag. En Runtime-ändring lämnas som avgränsat förslag, inte genomförande.
4. **Ny verklig omgång och överlämning mitt i kedjan** (efter 2–3). En annan
   behörig utförare fortsätter från sparad plan, källor och ärende, hämtar de valda
   verkliga källorna igen och hanterar faktisk förändring eller oförändrat material.
   Ingen ny publicering måste ha inträffat under fasen; den får inte fabriceras.
   Isolerade negativa fixturer kompletterar förändrat/borttaget/motsägande underlag.
   Resultat: ingen förlorad källa, dubbelt åtgärdsärende, ny ägaråterberättelse eller
   omstart från noll. Relevanta öppna saker fortsätter; avslutade saker återöppnas
   endast av ett konkret nytt underlag. Kvotbrist är väntan, inte nytt mål/mandat.
5. **Verksamhetsacceptans och brukbar överlämning** (efter 1–4). Mottagaren får
   bevakningsfrågan och projektets befintliga ingång, inte en lista av testkommandon
   eller rättelsefacit. Mottagaren genomför en avgränsad faktisk fortsättning:
   hittar publiceringen, lokal beröring, relevanta prov/bevis och motiverad åtgärd;
   utför nästa tillåtna läs-/prövningshandling eller gör ett källmotiverat avslut
   utan åtgärd. Beskedet jämförs separat med originalkällor, faktiskt lokalt
   beteende och gällande mandat. Syntetiskt fall med relevant ändring måste dessutom
   gå hela vägen till korrekt berett uppdrag, och ett otillämpligt fall får inte
   ge obelagt fel/uppgraderingskrav. AP08 lämnar daterad slutbild med resultatet.

Delmålen är en enda fas; granskning/acceptans inom dem är utförarens arbete, inte
fem nya ägarbeslut. Delmål 3 är leverantörstillämpning, ingen upprepning av AP07:s
metodpilot eller jämförelse av förprov som arbetsmetod.

## Faktisk Runtime-passform och hemvist

Målrepo: Nortropic/nortropic-projektkontor. Läst Runtime-revision
2789ea0770e4234161e9bdb0378a6e3e7b8432d2: Office tillåts, Codex är kvalificerad
utförare, explicita tools/-filer, frysta värdägda briefer/acceptans, seriella steg,
separat review och skyddad publicering. Nät/webbsökning är avstängda hos kandidaten.
Privata ärenden kan därför inte läggas i dess publika klon. Verklig insamling och
sakbedömning sker av kedjedrivaren med befintlig värdåtkomst; den kontrollerade
kandidaten får syntetiska exempel och innehållsgranskat uppdragsunderlag.

Detta kräver ingen Runtime-utökning: inga publika nätanrop inifrån kandidaten,
ingen ny modell/provider, inget nytt målrepo, ingen alltid-på-värd. Eventuellt
kodstöd hör naturligt hemma som kontorets filbaserade verktyg; Runtime förblir
motor. Värden använder befintlig arbetsväg för plan/beslut/dokument och granskad
skyddad dokumentationsintegration. Varje task fryser då aktuell godkänd bas;
inte hela fasen på en stor gren eller ett globalt körförsök.

Försöksgränser mot hängningar gäller per anrop; de är inte projekttidsgräns.
Diagnos, granskningsåtergång och historikbevarande återanvänds. Inga blinda retry,
automatisk modellväxling eller reservkostnader. En ny Codex/Claude-värdsession kan
fortsätta läsa planen; det innebär inte att Claude är kvalificerad Office-worker.

## Klart när hela kedjan fungerar

- Två faktiska intag inom det valda området är genomförda med verkliga källor och
  bevarade tider/versioner; om andra intaget är oförändrat redovisas det så.
- Minst ett verkligt leverantörspåstående har bedömts mot kontorets faktiska
  användning, relevanta befintliga körbevis eller motiverat nytt beteendeprov.
  Utfallet får vara avstå, men inte enbart en sammanfattning av release notes.
- Ny mottagare använder kedjan för verklig fortsättning enligt delmål 5 utan
  ägarens källurval, tekniska arbetsorder, kommandoförmedling eller granskarbud.
- Relevant förändring, oförändrat material, otillämplig nyhet, saknad/motsägande
  källa, felaktig versionskoppling och injektionsförsök ger rätt avgränsat utfall.
  Formatpass/hashlikhet blir aldrig sakaccept eller befogenhet. Fixturbevis och
  verkliga utfall särredovisas; inget krav att hitta en förbättring för att bli klar.
- Små granskade ändringar är löpande skyddat integrerade, privat material är
  innehållskontrollerat/bevarat och slutbevis binder faktiskt använda revisioner.
- AP08-bilder efter väsentliga delresultat är information, inte nya acceptpunkter.
  Planen bär nästa handling och återupptagning; slutleveransen lämnas och arbetet
  stannar. Ingen allmän effekt, ägarbesparing eller ständig tillsyn påstås utan bevis.

## Samlat mandat som behövs — ännu inte givet

Acceptera AP09:s ovanstående verksamhetsmål och fem interna delmål. Tillåt
implementation, prov, verkligt offentligt källintag/privat tillämpning, separat
granskning och skyddad integration i kontorsrepot genom befintlig Runtime.
Publicering omfattar innehållskontrollerad kod, syntetiska exempel, anvisning och
begränsade bevis. Verkliga ärenden, källkopior, privata sökvägar och råhistorik
stannar i befintlig privat hemvist. Inga interna uppgifter skickas till söktjänster.

Kedjedrivaren får formulera/frysa tekniska tasks, samordna granskare, hantera
rutinval och motiverade omtag och integrera delresultat utan nya ägarprompter.
Bara ändrat verksamhetsmål, kostnad eller befogenhet återförs till ägaren.

Förslaget ger inte automatiskt uppdateringsmandat för Runtime eller annan
infrastruktur, rätt att installera/byta beroenden, nya konton/tjänster/kostnader,
organisationsrättigheter, kundkontakt, nya repon, valvskrivning, daemon/scheduler
eller stående ansvar utanför aktivt beställt arbete. Ett sådant behov redovisas
med konkret sakunderlag; fasen bygger ingen generell plattform i förväg.

AP07:s I07b-bedömning utvidgas inte till ett generellt självförbättringsprogram.
I08:s nio frågor används som checklista; ingen sägs löst. A3/A6, FIND-004 och andra
fynd behåller status. Deras konkreta påverkan hanteras i berörd källa/prövning,
inte genom ny totalrevision eller genom att kalla denna accept en auditstängning.
