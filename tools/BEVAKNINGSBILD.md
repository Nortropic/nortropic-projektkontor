# Daterad privat bevakningsbild genom AP08

`bevakningsbild.py` sammanställer det namngivna åtagandet
`office-python-temporal` till befintliga `agarbild.render`, oförändrad.
Import gör ingen I/O. HTML är en fristående svensk läsbild: att öppna den läser
inte källor, uppdaterar ingenting och startar inget arbete. Bilden är daterad,
inte live, notifiering, bevakningsmotor eller bevis för AP10:s slutkvalificering.

## Gränssnitt och tidernas räckvidd

`view(native, latest, reviewed, generated_at)` är ren och lämnar exakt AP08:s
schema 1. Den läser varken filer eller klocka och ändrar inga indata.
`native` är den fångade statusordboken eller en uttrycklig otillgänglig observation.
`latest` och `reviewed` är null eller `{report, packet, integrity, locator}`;
`integrity` är `available` eller `unavailable`. Endast insamlarens dokumentärt
kontrollerade bindningar får betecknas `available`. Detta är ingen
äkthetsgaranti eller ny sakgranskning.

Tre stabila underlag och arbetsrader hålls isär:

- `native` / **Schema**: paus, stopp eller aktivering enligt den daterade
  schemaobservationen. Ett `STOPPED`-prefix har företräde. Pågående åtgärder
  redovisas separat; paus betyder inte att de har avbrutits.
- `latest` / **Senaste observation**: senaste rapportens paketdatum.
  Ogranskad, ofullständig, skadad eller otillgänglig observation blir väntan
  eller okänd, även när ett tidigare granskat positivt besked finns.
- `reviewed` / **Senast granskade besked**: separat daterad granskning,
  historisk när en annan observation är senare. Den ersätter aldrig ett fel
  i den senaste observationen. Radens och underlagets datum är originalets
  `reviewed_at`, även när granskningen återanvänds för ett senare paket.

Paketets `observed_at`, ärendebaslinjens `first_treated_at`, rapportens
`reported_at` och originalets `reviewed_at` visas var för sig. Återbruk bevarar
originalets granskningsdatum och anges uttryckligen som återanvänd granskning.
Det påstår ingen ytterligare oberoende granskning. Gamla luckor och rapportens
begränsningar följer med. Observation äldre än ett dygn vid framställningen
märks **inaktuell**. Det påstår ingen missad omgång under paus. Ogiltigt,
okänt eller framtida observationsdatum blir en lucka och förs aldrig in som
framtida `observed_at` i AP08.

Det granskade dygnsschemat är 09:00 Europe/Stockholm utan årsbegränsning,
`limited_actions=false`, med återkomstfönstret now22hours (`22:00:00`).
Ett årsbegränsat schema med `limited_actions=true` betecknas engångsprov,
inte flera dygns drift. Äldre 24-timmarspolicy är inte slutramen.
Cronfältet godtas som tomt endast som listan `[]` eller strängen exakt `'[]'`.
Saknade fält, andra strängar, null och icke-tomma listor ger okänt schema;
känd paus/stopp kvarstår i texten. Ingen eval eller generell strängtolkning sker.
Även listposterna kontrolleras: planerade tider måste ha tidszon, pågående
åtgärder måste ha båda köridentiteterna och senaste starter dessutom giltiga
`scheduled_at` och `started_at` med tidszon. Felaktiga poster ger okänt schema
med känd paus/stopp bevarad i texten.
Nästa native tid är en **planerad** åtgärd. Räknare, faktiska `started_at`,
`scheduled_at` och köridentiteter finns i underlagsdetaljerna. Senare/pågående
starter utan matchande läsbar rapport blir en aktuell rapportlucka. En start
bevisar inte slutfört källintag. Även **Senaste observation** blir då väntande
eller okänd, med det tidigare faktiska observationsdatumet bevarat.

Kedjedrivaren bär nästa hantering: diagnostisera underlag, respektera paus/stopp
eller invänta planerad omgång inom befintligt mandat. Ett aktuellt bundet
`propose_action` med AP06-utkast är en **ogenomförd ägarfråga**:
`owner_decision.needed=yes`, `next_action.authority=proposed`. Ogranskad eller
avslagen bedömning och teknisk väntan skapar ingen rutinmässig ägaruppgift.
Insamling och ren visning använder samma strukturella AP06-kontroll: status
`draft`, `mechanical_complete=false` och tomt `package.task_draft`.
Både fullständigt och kompakt dokumentärt utkast godtas. Finns `private`
krävs en spec med tom `task`; annars krävs icke-tom `package.brief` och
`package.gaps`. Varje förekommande lucklista, både på rotnivå och i paketet,
måste innehålla ordböcker med icke-tom kod och subjekt samt
`action_authority_missing`. Minst en lista krävs; finns båda ska de stämma
överens. En felaktig rotlista kan aldrig döljas av paketets lista.
En godtycklig ordbok eller felaktig luckpost ger inget lyckat besked eller
ägarfråga. En skadad rapport avbryter inte insamlingen av äldre läsbar evidens.
Ett fortfarande senaste bundet granskat förslag kvarstår som ägarfråga även
efter ett dygn, med inaktualitetsvarning och behov av aktuell kontroll.
Det ger enbart `proposed`, aldrig verkställighetsmandat. Ett senare fel,
ogranskat besked eller en senare native start utan rapport hindrar att ett
äldre förslag visas som aktuell ägarfråga. Inga restart-, uppgraderings-,
publicerings- eller aktiveringskommandon finns i verktyget.

## Begränsad insamling

`collect(runtime_root, status_reader=None)` lämnar exakt
`{native, latest, reviewed}`. Rotargumentet är en Python-söm för operatör och
syntetiska prov, ingen CLI-väljare för godtyckliga mål. Insamlaren läser endast:

- `.runtime/ap10/active.json` och exakt utpekad fryst konfiguration/release;
- hashvalda filer i releasen för bindningskontroll och `context/watch.json`
  för det namngivna ärendet;
- omedelbara `rounds/*/report/result.json`, respektive
  `intake/data/packet.json` och originalets `analysis/result.json` och
  `review/result.json`.

Inga events, stderr-filer, credentials, källnyttolaster, råsessioner eller
reparationer läses/skrivs. Varje dokumentärt JSON är högst 8 MiB, sammanlagda
dokumentläsningar högst 64 MiB och antalet omedelbara omgångskataloger högst
512. Hashkontroll av frysta filer har separat gräns 512 MiB. En överskriden
gräns innebär ofullständigt/otillgängligt underlag, aldrig att nyare arbete
bevisligen saknas. Även en äldre rapports för stora paket eller analys-/reviewfil
markerar hela insamlingens senaste observation som otillgänglig med uttrycklig
gränsdiagnos. Markeringen kvarstår om senare rapporter ryms och kan läsas;
redan verifierad granskningshistorik bevaras separat. Samma sak gäller den
sammanlagda dokumentbudgeten. Dubblettnycklar och icke-finita JSON-tal avvisas.

Filer öppnas som reguljära no-follow-filer genom kontrollerade föräldrakataloger.
Symlänkar, traversal, pekare utanför rot/release och icke-reguljära objekt avvisas.
Konfigurationens bytehash, kanoniska rotkopplingar, 40-hex-revisioner och alla
valda filhashar kontrolleras före statusanrop, även med injicerad läsare.
`files` är en sökväg→SHA256-mappning eller en lista av `{path, sha256}`.
Sökvägarna är relativa till releasen. Bindningarna
`runtime/runtime/obligation.py` och `context/watch.json` måste finnas.
Hela releasens `runtime`-träd kontrolleras också före anropet: varje fil måste
vara reguljär och hashbunden i `files`, och kataloger måste leda till sådana
filer. Olistade importartefakter, inklusive `__pycache__/*.pyc`, avvisas liksom
symlänkar i trädet. `-B` hindrar bara nya bytekodskrivningar; befintlig bytekod
kan fortfarande läsas och måste därför omfattas av samma frysta bindning.
`host_root` är angiven kanonisk Runtime-rot; `office_root` måste vara exakt
syskonet `nortropic-projektkontor`. Den oanvända kontorskatalogen öppnas inte
och behöver inte finnas vid syntetisk insamling. `database` måste vara exakt
`<Runtime-rot>/.runtime/runtime.sqlite`. No-follow-kontrollerna kvarstår för
alla faktiskt lästa sökvägar och deras föräldrar. Verkliga revisioner eller
kommande identiteter uppfinns inte.

Det enda möjliga processanropet är den fasta redan kvalificerade venv-Python:
`-B -m runtime.obligation status`, med cwd i frysta releasens `runtime`,
`shell=False`, fångad text och 20 sekunders timeout. Miljön begränsas till
vanliga PATH/HOME/USER/LOGNAME/LANG/TMPDIR plus `PYTHONDONTWRITEBYTECODE=1`,
kontrollerad `NR_HOST_ROOT` och `NR_CONFIG_SHA256`. PYTHONPATH, PYTHONHOME och
andra NR-överskrivningar ärvs inte. Den fasta venv-tolkens vanliga symlänk är
undantaget; ingen annan kod-/konfigurationssymlänk får bli körbar.
Inget arbetsutcheckat Runtime importeras och ingen reservväg startar tjänster.
`status_reader(runtime_root, config)` ersätter endast detta anrop och får en
kopierad verifierad konfiguration med `directory` och `config_sha256`.
Pekare/konfiguration läses om efter anropet. Byte under anropet, timeout,
saknad tjänst, felkod eller ogiltigt JSON gör native observation otillgänglig;
läsbara rapporter bevaras. Fel lämnar fasta diagnoser utan privata feltexter.

Rapporter binds till åtagande, namngivet ärende, omgång, paketbytehash och
tidsuppgifter. Granskade besked kräver ursprungliga lyckade analys-/reviewbytes,
matchande hashvärden, äkta framgångsflaggor, olika icke-tomma tråd-ID:n och
approved utan blockerare. Kanonisk full analys med sorterade nycklar,
kompakta separatorer, `ensure_ascii=True`, `allow_nan=False` måste matcha både
review och rapport. Ändrad beslutssammanfattning räknas inte som granskad.
Återbruk kräver originalrapport direkt under samma rounds-katalog, inte en
återbrukad mellanrapport, samt samma fullständiga omräknade fingerprint,
ärende/kontext, beslut och ursprungliga granskningsmetadata.
Paketets `sources` och `local` måste vara listor men får vara tomma;
intaget äger insamlingens fullständighet. Post-, hash-, typ- och
fullständighetskontroller gäller fortfarande. Nullpaket, felaktiga grupper
eller ofullständiga paket blir aldrig lyckade kompletta observationer.

## Privat filutdata och prov

CLI har exakt ett argument: en **ny** privat utdatakatalog vars förälder finns.
Runtime härleds som syskonet `Nortropic Runtime` till kontorsrepot.
Befintlig målplats och symlänkade föräldrar avvisas före insamling. Lyckat
anrop returnerar 0 och skapar endast `input.json` och `index.html`, filer med
0600 i katalog med 0700. Fel ger 2 och fast stderr-diagnos utan överskrivning.
Otillgänglig native status kan fortfarande ge en användbar daterad bild.
Inget öppnas automatiskt och ingen server eller publicering sker. Både bilden
och dess indata förblir privata.

Syntetiska prov från reporoten:

```sh
/opt/homebrew/bin/python3.12 -B -m unittest discover -s tools -p test_bevakningsbild.py
```

Alla fixturer och utdata ligger under `.scratch`. Process- och nätanrop är
spärrade eller ersatta av syntetiska svar. Proven läser inga verkliga privata
källor, gör ingen native fråga eller modellkörning och ändrar ingen drift.
Runtime äger fryst acceptans, oberoende granskning, skyddad integration och
AP10:s verkliga samexistens- och slutbevis; dessa följer inte av kandidatproven.
