# AP10 — kontoret bär ett avgränsat bevakningsansvar

2026-09-21. **Samlat FÖRSLAG, inte accepterat bygge eller driftmandat.**
Planen i `docs/plan.md` äger aktuellt steg och nästa handling. Detta dokument är
det beredda beslutspaketet; ingen parallell masterplan.

## Rekommenderat verksamhetsresultat

Kontoret tar ansvar för att återkommande bevaka officiella förändringar som kan
beröra de Python- och Temporalberoenden som redan ingick i AP09. Det inhämtar,
kontrollerar den lokala användningen, bedömer betydelsen, låter granska nya
sakslutsatser och lämnar ett motiverat behåll, inte tillämpligt, otillräckligt
eller ett konkret åtgärdsbeslut för ägaren. Nästa omgång beställs inte av ägaren.
Åtgärder utanför åtagandet bereds men genomförs inte.

Detta är nästa rekommenderade operativa förmåga efter kontorets redan visade
uppdragskedja. Ett enda accepterat utvecklingsmål ska bära fem beroende delmål
fram till denna användbara funktion och dess driftöverlämning. Det är inte en
ny omgång AP09 för att få starkare bevis: dess sakbeslut och shutdown-lucka
bevaras. Det är heller inget generellt självförbättringsprogram.

**Nu:** kontoret kan ta emot ett accepterat mål, bereda källbundna uppgifter,
driva flera beroende steg, ordna granskning och skyddad integration, överlämna
verkligt återstående arbete och lämna daterad ägarbild. AP06:s kärna→CLI och
AP09:s femdelade tillämpning visar detta inom sina räckvidder. En längre fas
behöver inte en ny projektmotor eller en ny planfunktion.

**Efteråt:** kontoret bär också ett namngivet ansvar mellan beställningarna.
Ägaren behöver inte minnas när bevakningen ska göras, starta varje omgång,
sammanföra releaseinformation med lokal användning eller transportera frågor
till granskare. Ingen uppmätt tidsbesparing påstås.

## Varför detta arbete nu

Definitionen anger omvärldsbevakning som del av Nortropics syfte. I-04 placerar
kontoret först; I-03 anger mindre återberättande och samordning, inte ett procentmått.
Det rättade byggförslaget §4 och §8 lämnar stående ansvar utan ägartur öppet
(RF-16), skilt från drift på annan värd eller när datorn är avstängd (RF-17).
AP09 ger nu verkligt tillämpningsunderlag för ett sådant begränsat ansvar.

Prioriteringen är kedjedrivarens härledda rekommendation, inte ett tidigare
ägarbeslut. I-05 rangordnade inte behoven. Vi flyttar medvetet fram just denna
väntande del av byggförslaget, efter redan levererade förkrav. RF-17 lämnas öppet.
Ett återställningsprojekt utan aktuellt flyttbehov, ännu en metodpilot och en
generell mål-/uppgiftsmotor tillför inte det valda verksamhetsresultatet.

## Avgränsat åtagande att acceptera

- **Objekt:** samma Python/Temporal-användning som AP09, inga andra produkter,
  generellt nyhetsflöde, säkerhetscertifiering eller löfte om fullständig bevakning.
- **Källor:** officiella releaseförteckningar för CPython och Temporal Python SDK,
  följt av relevanta officiella utgåvenoter. De gamla fasta releasesidorna räcker
  inte för att upptäcka senare utgåvor. Urvalet begränsas av installerad komponent,
  versionslinje och faktisk användning. Python.org och Temporal-projektets
  officiella GitHub-repo är de avsedda externa intagsytorna. Inga privata data
  skickas med hämtningsanrop; otillräcklig täckning redovisas.
- **Frekvens:** föreslagen normaldrift en gång per dygn på befintlig dator när den
  är vaken och den lokala tjänsten är tillgänglig. Det är ett föreslaget
  verksamhetsval, inte ett krav hämtat ur intervjun eller en projekttidsgräns.
  Ingen parallell omgång; försenade tillfällen samlas till högst en aktuell
  omgång vid återkomst. Uteblivna tillfällen bevaras som lucka, inte utförda intag.
- **Lokal aktualitet:** varje omgång läser de namngivna versions-, konfigurations-
  och användningsunderlagen som behövs för frågan. Ny källa, lokal förändring
  eller saknad observation kan kräva omprövning även när releasen är oförändrad.
  Samma kontrollerade underlag ger inte dubblettärenden eller ny modellgranskning
  utan sakskäl. Ett återanvänt beslut behåller ursprung, räckvidd och öppna luckor.
- **Följd:** intag→lokal observation→sakbedömning→relevant separat granskning→
  privat beslutsredovisning/AP08. Vid motiverad åtgärd utanför mandatet: AP06-
  beredning till konkret ägarbeslut, ingen automatisk uppgradering eller rättning.
- **Driftgräns:** en användarägd lokal process för befintlig Temporal-tjänst och
  worker får efter godkänd kvalificering hållas aktiv och startas vid inloggning.
  Inga administratörsrättigheter, ny värd eller köpt tjänst. Sömn/avstängd dator,
  stoppad process och kvotbrist innebär uteblivet arbete, aldrig aktuell garanti.
  En enkel dokumenterad paus/stopp återkallar framtida starter; redan pågående
  arbete stoppas eller avslutas kontrollerat med bevarad journal.
- **Slutläge:** efter verifierad leverans lämnas just detta åtagande aktivt tills
  ägaren pausar/avslutar det. Det måste omfattas uttryckligen av accepten. Det
  beställer inga andra mål och skapar ingen stående rätt att ändra kod.

## Återanvändning, verkliga luckor och körpassform

| Del | Återanvänds | Verkligt tillägg |
|---|---|---|
| Projektledning | Befintlig agent, plan, beslut, en skrivare, AP06 teknisk uppdelning | Ett sammanhängande fasmandat; ingen ny produktfunktion behövs för tekniska övergångar |
| Bedömning | AP05, AP09:s käll-/användningsarbete och granskade slutsatser | Kontorets koppling av återkommande intag och lokal observation till samma ärende och beredning |
| Rapportering | AP08:s daterade privata bild, rena status/resultatläsningar | Uppgifter om förfallotid, faktiskt intag och utebliven observation; inget nytt dashboardprojekt |
| Byggande | AP04/Runtime, frysta värdprov, separat granskning, skyddad publicerare | Bara koden och kvalificeringen som de två nya körbehoven nedan kräver |
| Körning mellan beställningar | Befintlig Temporal, SQLite-historik, processkontroll och exklusiv motorlåsning | Beständig lokal aktivering samt ett avgränsat privat läs-/bedömningsuppdrag som kan avslutas utan kodkandidat/PR |

Läst bas: kontor `613544012b64c191b9e48b3cd94fa2282352e53b`, Runtime
`2789ea0770e4234161e9bdb0378a6e3e7b8432d2`. Nuvarande `run.py` startar tjänst och
worker inom ett enskilt anrop och stänger dem efteråt. `DevelopmentTask` går från
modellarbete via kodacceptans och review till publicering. `task.py` tillåter
för kontoret explicit `tools/`, Codex och fryst Runtime-revision; workerns
`profile.py` har nät av och saknar verkligt privat kontorsunderlag. Dagens väg
är därför **inte redan kvalificerad** för obemannad privat sakbedömning.

Runtime-delmålet är större än en timer: livscykel/aktivering, privat läsuppdrag
utan publicering och dess begränsade profil måste kvalificeras tillsammans.
Temporal ska fortsatt äga schema och körstate; inga egna scheduler-loopar eller
andra motorer. Installerad SDK exponerar Schedule-API:t, och leverantörens
[Schedule-dokumentation](https://docs.temporal.io/develop/python/workflows/schedules)
beskriver aktivering, överlapp och paus. Detta är genomförbarhetsunderlag,
**inte ett Nortropic-körbevis**. Ingen SDK-uppgradering föreslås.

Verksamhetslogik, källurval, metod, sakbedömning och resultat hör till
`Nortropic/nortropic-projektkontor`. Runtime får bara den nödvändiga kopplingen
till detta namngivna åtagande och målrepo. Officiellt intag görs av en avgränsad
värdfunktion; bedömningsmodellen får bundna indata i privat prov-/arbetsyta,
inte generell nätåtkomst eller direkt valv-/kampanjåtkomst. Den får inte ändra
indata, mandat, körkod, schema, acceptans eller publiceringsrätt. Privata
bedömningar har ingen PR-väg. Byggkandidater använder fortsatt syntetiska data.

## Fem beroende delmål inom en fas

| Delmål | Beroende | Observerbart resultat |
|---|---|---|
| 1. Binda det operativa åtagandet till AP09 | Fasaccept | Det faktiska befintliga ärendet, smalt källurval, lokala läsobjekt och handlingsgränser är bundna. AP09:s behåll och bevisluckor förs vidare, inget återstartat rättningsuppdrag. Värdacceptans för de följande stegen är separat granskad. |
| 2. Kvalificera exakt nödvändig Runtime-väg | 1 | En ägaraccepterad aktivering kan ske efter avslutad interaktiv session; privat läsuppdrag slutförs utan kod-PR; avvisad åtkomst, paus, exklusivitet och bevarad historik är prövade. Små separat granskade skyddade integrationer; den nya vägen bedömer aldrig sin egen byggkandidat. |
| 3. Koppla kontorets verkliga bevakningsarbete | 1, 2 | Schemat driver den avgränsade kedjan med befintliga AP05/AP06/AP08, två produktkällor och aktuell lokal observation. Kontorsändringar byggs genom kvalificerad Runtime med syntetiska data, sedan privat tillämpning. Sakbeslut, återanvänt beslut och okänt hålls isär. |
| 4. Genomföra ansvarskedjan i faktisk användning | 3 | En senare omgång startar genom schemat utan ny ägarprompt/manuell start, behandlar verkligt externt och lokalt underlag och lämnar granskat besked. Relevant avbrott/återkomst och färsk utförares faktiska fortsättning av återstående arbete visas utan konkurrerande skrivare. |
| 5. Slutgranska och lämna i avtalad drift | 4 | Separat granskare binder hela användningskedjan till båda repo-revisionerna; paus/stopp, återupptagning och enkel driftanvisning fungerar. Privat slutkvitto och daterad AP08-bild visar vad som faktiskt är aktivt, senast observerat och obesvarat. |

Delmålen är interna kontrollpunkter, inte nya ägargrindar. Kedjedrivaren delar
upp tekniska uppdrag, fryser deras riktiga indata/acceptans, samordnar granskare
och hanterar tekniska omtag inom målet. Små ändringar integreras löpande under
befintliga skydd; ingen stor slutgren. Vid kvotbrist/sessionbyte sparas pågående
arbete, skrivansvar, diagnos och nästa handling i befintliga hemvister.

## Slutacceptans — verksamhetsförloppet måste fungera

Ägaren accepterar målet en gång. Kontoret genomför delmålen utan nya tekniska
beställningar och lämnar sedan det namngivna bevakningsansvaret i drift.

1. En verklig senare intagsomgång aktiveras automatiskt sedan den interaktiva
   drivarsessionen avslutats. Extern publiceringstid, hämtningstid, första
   behandling och lokal observation skiljs åt. Schemat/historiken och faktiska
   hämtningar används som bevis, inte bara kontorets egen sammanfattning.
2. Kontoret motiverar nytt sakbeslut, återanvändning eller otillräcklighet utifrån
   komponent/version/användning. Oförändrat material får vara rätt utfall. Ingen
   ny release, uppgradering, felupptäckt eller starkare shutdown-garanti krävs.
3. En faktisk behörig mottagare fortsätter en återstående del ur sparat läge.
   Relevant avbrott och återkomst bevarar föregångare, identifierar luckan och
   gör högst en aktuell fortsättning. Det är inte bara ett återberättarprov.
4. Isolerade negativa fall prövar källa borta/ändrad, lokalt ändrad användning,
   motsägande påstående, utebliven aktivering, förbrukad modellåtkomst, dubbel
   start och handling utanför mandat. Okänt förblir okänt; verkliga original
   ändras inte. Syntetiska utfall påstås inte vara uppmätta verksamhetseffekter.
5. Modellens instruktioner från källtext kan inte ge den nya befogenheter;
   profilgränser och frånvaro av privat publicering prövas. Status/resultat och
   öppning av AP08 får inte starta arbete. Vid helt stoppad dator/process kan
   ingen aktiv varning garanteras: senaste observation och förfallotid gör
   luckan avläsbar, och den redovisas vid nästa faktiska observation.
6. Nya sakslutsatser och hela kedjan är separat granskade. Alla nya kodändringar
   har relevant verifiering och skyddad integration, med faktiskt använda
   revisioner. Paus och stopp verifieras innan just detta åtagande lämnas aktivt.
7. Kontoret kan fortfarande utföra sina accepterade AP04-bygguppdrag medan den
   lokala tjänsten är aktiv. Ett verkligt behövligt kontorsuppdrag inom denna
   fas ska startas, granskas och skyddat integreras genom samma motor utan att
   ägaren manuellt stoppar bevakningen. Byggande och bevakning samordnas seriellt
   med befintlig exklusivitet; gamla uppdrag får inte blockeras permanent av
   det nya motorlåset eller de upptagna portarna. Äldre historiker bevaras.

Normalfrekvensen är ett dygn. Ett kortare, uttryckligt dokumenterat intervall
får användas för det avgränsade aktiveringsprovet med verkliga intag; det bevisar
inte dygnsdrift över lång tid. Slutkvittot skiljer provinställning från den
faktiskt lämnade dygnsinställningen. Ingen dold projektdeadline införs.

## Samlat nytt mandat som behövs

Accepten behöver omfatta **både** utvecklingsfasen och det följande begränsade
driftåtagandet. Tidigare AP-accepter räcker inte till nedanstående utvidgning.

1. Genomföra de fem delmålen, implementera/testa/dokumentera och skyddat integrera
   nödvändigt kontorsstöd samt innehållskontrollerade offentliga leveransbevis i
   befintligt kontorsrepo; återanvänd befintlig modellanslutning och granskning.
2. Ändra och skyddat integrera Runtime **endast** för den beskrivna aktiveringen,
   tjänstelivscykeln, privata läsuppdrag utan PR, frysta indata/profil och berörda
   tester/dokument. Befintliga uppdrag, historiker och publiceringsgrindar bevaras.
3. Etablera användarägd lokal process och inloggningsstart för detta åtagande,
   samt utföra dess dygnsvisa officiella nätintag och avgränsade privata läsning/
   bedömning utan ny ägartur. Runtime och kontoret får inte konkurrera om den
   befintliga motorlåsta tjänsten. Paus/stopp ingår. Ingen adminrätt begärs.
4. Publicera endast kontrollerad kod, metod, syntetiska exempel och begränsade
   bevis i respektive befintligt repo; hålla verkliga indata, lokala sökvägar,
   konfigurationer, privat fallredovisning och råhistorik i privat hemvist.

Inget nytt konto, betald tjänst, API-betalning, modellanslutning, uppgradering,
nytt målrepo, kampanj-/IR-/valvskrivning, kundkontakt eller generell självlärloop.
Befintlig abonnemangskvot används; tar den slut bevaras väntan utan betald
reservväg eller blinda modellomförsök. Behövs nytt mål, kostnad eller större
befogenhet återförs ett konkret beslut; oberoende tillåtna delar slutförs.

## Bevisgränser och bevarande

AP09:s behåll/inte-tillämpligt och otillräckliga graceful-drain-bevis står kvar.
Inga gamla fynd, A3/A6 eller FIND-004 stängs; AP07 förblir frivilligt ANPASSA utan
belagd effekt. I-08:s frågor används som checklista, inte besvarad teori:
förbättring/alternativ/nyfikenhet är utanför; betydelsen av lokala ändringar och
motsägelser kräver sakomdöme; framgång mäts i verkligt ansvarstagande; gammalt
underlag får inte bli aktuellt genom hashmatch; ingen självauktorisering eller
metrikoptimering får ersätta resultatet. Ingen universell tillitsregel föreslås.

Den privata beredningen bevarar källbindningar, observationer, AP05/AP06-utkast
och separat relevans-/paketgranskning. Oförändrade valda källor är inte garanti
för fullständighet. Det nuvarande mandatet tillåter endast denna beredning;
inget schema, ny intagsomgång, modellbygge, publicering eller Runtime-ändring
har startats genom förslaget.
