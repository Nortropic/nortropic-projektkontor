# Avgränsat bevakningsunderlag

`bevakningsunderlag.py` samlar officiella Python-/Temporalunderlag och kopior av
namngivna lokala Runtime-filer till ett nytt privat paket. Värden anropar den
frysta, granskade modulen. Modulen startar inga modeller, kommandon, scheman,
installationer eller publiceringar. Källtext är evidens, aldrig instruktioner
eller tillstånd. Inget hämtat eller lokalt innehåll exekveras.

## Anrop och privat bevarande

`collect(output, local_roots, versions, previous=None, fetcher=None)` returnerar
paketet och skriver samma innehåll i `output/packet.json`. `output` måste vara
en **ny** katalog med en redan befintlig föräldrakatalog. Befintlig katalog,
fil eller symlänk avvisas före hämtning; ingenting där ersätts. Nya katalogen
har rättighet 700 och nya filer 600. Fel vid lagring avbryter med en fast
felorsak och kan lämna ett partiellt nytt uttag för värdens undersökning.
Ett sådant uttag ska inte återanvändas som nytt output.

`local_roots` innehåller exakt `active` och `working`, med `Path` till respektive
rot. `active` avser den frysta kod som faktiskt används; `working` avser den
aktuella arbetskopian. De jämförs som separata observationer. Modulen upptäcker
inte själv aktiv revision och hämtar inte versioner genom att köra koden.
Värden binder rötterna och lämnar `versions` med `python`, `temporalio`,
`active_config_sha256`, `runtime_revision` och `office_revision`. Alla fem är
icke-tomma strängar; installerade versioner ska vara numeriska stabila
`major.minor.patch`. Versionsmappningen kopieras. Modulens strukturkontroll
verifierar inte värdens revisions- eller konfigurationsuppgifter.

`LOCAL_FILES` är den fasta läslistan med femton filer för vardera roten:

- `runtime/worker.py`, `runtime/workflow.py`, `runtime/activities.py`
- `runtime/run.py`, `runtime/service.py`, `runtime/profile.py`
- `config/temporal-probe-requirements.lock`, `docs/runtime-v0.1.md`
- `runtime/daemon.py`, `runtime/shared.py`, `runtime/release.py`
- `runtime/private_workflow.py`, `runtime/private_activity.py`
- `runtime/private_stage.py`, `runtime/obligation.py`

Ytterligare filer kräver en granskad kodändring. Varje fil får vara högst 1 MiB.
Symlänkar avvisas i hela kedjan av rot, källfil och output, även i deras
föräldrar. `..` avvisas. Kataloger öppnas via deskriptorer utan att följa
symlänkar; endast vanliga källfiler läses. Saknad, osäker, oläsbar eller för stor
lokal fil får en egen `unavailable`-post, aldrig tyst utelämnande.
Originalens innehåll och rättigheter skrivs inte om. Vanlig filsystemsläsning
kan påverka åtkomsttid; paketet är ingen atomär ögonblicksbild av flera filer.

## Officiellt urval och transport

Varje anrop hämtar Python-indexet
`https://www.python.org/downloads/source/` och Temporal-indexet
`https://api.github.com/repos/temporalio/sdk-python/releases?per_page=20`.
Python väljs numeriskt: senaste stabila patch i installerad major/minor-linje
och installerad utgåva. Indexets länktext och release-sökväg måste stämma med
versionen, och installerad utgåva måste finnas där. Om en stabil versionsetikett
pekar på fel release-sökväg blir indexet otillgängligt och paketet ofullständigt;
posten hoppas inte över. Release-sidans H1 måste ange den begärda Python-versionen.

Temporal väljs numeriskt bland **de första 20 indexposterna**. Drafts,
prereleases och icke-numeriska stabila taggar räknas inte som kandidater.
Senaste stabila versionens och installerad versions detaljer hämtas via
`/releases/tags/<major.minor.patch>`. Installerad version kan ligga utanför
indexfönstret; dess separata detalj måste ändå finnas. Detaljens `tag_name`
måste överensstämma med begärd tagg och får inte vara draft/prerelease.

Dubbletter inom respektive produkt hämtas en gång. Det blir högst sex anrop,
utan omtag eller paginering. Om ett index fallerar försöker modulen fortfarande
hämta installerad utgåvas detalj och de övriga oberoende observationerna.
Urvalet är avgränsat till vald Python-linje, Temporal-fönstret och installerade
utgåvor. Det garanterar inte att alla relevanta eller senare källor hittats.

`fetch(url)` accepterar endast indexadresserna, Python-sökvägar som exakt
matchar `/downloads/release/python-[0-9]+/` och ovanstående numeriska
Temporal-taggar. Okänd URL avvisas före nätkontakt. Transporten använder
standardbibliotekets `urllib.request.build_opener`, explicit
`ProxyHandler({})`, GET, fast User-Agent `Nortropic-Office-Intake/1`, fast
`Accept-Encoding: identity`, normal TLS-verifiering och timeout 10 sekunder.
Inga credentials, auth-hanterare, cookies eller proxy används. Redirect avvisas
även till tillåten adress. HTTP-fel och nätfel ger otillgängligt underlag. Timeout är transportens
timeout, ingen garanti för total körtid för hela insamlingen.

Svaret får innehålla högst 1 MiB kodade bytes; högst 1 MiB + 1 byte läses för
att upptäcka överskridandet. Saknad `Content-Encoding` eller `identity` lämnar
bytes oförändrade. `gzip` avkodas trots begärd identity, med en separat gräns
på 1 MiB avkodade bytes. Expansionen begränsas under avkodningen. Exakt gräns
accepteras, gräns + 1 avvisas. Kodning avgörs enbart av HTTP-headern, aldrig
av innehållets magiska bytes. Omgivande blanktecken och bokstavsstorlek
ignoreras. Explicit tom header, okänd kodning (även `br`, `deflate`, `x-gzip`),
listor/kombinationer och upprepade `Content-Encoding`-headers avvisas.
Gzip kräver en fullständig enda medlem med giltig trailer och kontrollsumma;
trunkering, korruption, efterföljande bytes och sammanfogade medlemmar avvisas.
Felaktig, otillåten eller för stor transport ger otillgänglig källa och
ofullständigt paket; oberoende lyckade observationer bevaras.

## Paketets betydelse

Schema 1 innehåller `observed_at`, `sources`, `local`, `versions`, `complete`,
`fingerprint`, `same_controlled_basis` och `coverage`. Varje hämtning/läsning
får sin egen aktuella UTC-observationstid vid försökets början. Källposter har
`id`, `url`, `status`, `observed_at`, `published_at`, `sha256`, `path`, `error`;
lokala poster saknar `url` och `published_at`. Identiteterna är `python-index`,
`temporal-index`, `python-<version>`, `temporal-<version>` och
`active:<fil>`/`working:<fil>`. Filvägar i paketet är relativa till output.

`fetch` returnerar kroppens bytes efter HTTP-innehållsavkodning. Dessa bevaras
oförändrade i `<id>.raw`: identity är mottagna kroppsbytes, gzip är avkodade
kroppsbytes. Ingen teckenkonvertering, HTML-omskrivning eller JSON-omformatering
sker. `.raw` betyder den oparsade kroppen, inte komprimerade överföringsbytes
eller en nätverksinspelning. Källans SHA-256 och paketets fingeravtryck binder
dessa lagrade innehållsavkodade bytes. Transportmetadata som inte registrerats
läggs inte till i efterhand. Befintlig policy kopierar redan de bevarade bytesen.

Lokala kopior har prefix `active-` eller `working-`. Även hämtade svar vars innehåll inte går att
tolka bevaras i `<id>.raw` för privat felsökning, men deras post är
`unavailable` med null i `sha256` och `path`. Ingen del av ett för stort svar
bevaras som lyckad källa. Felorsaker är fasta och innehåller inga privata
sökvägar eller undantagstexter. Paket, rotnamn, källkopior och alla verkliga
lokala uppgifter hör hemma privat och ska inte publiceras automatiskt.

`published_at` kommer från Temporal `published_at` eller extraherbar Python
`Release Date` (Python-datumets källtext bevaras). Saknad uppgift är null.
Publiceringstid är skild från intagstid. **Första behandlingen** av redan
installerad utgåva är baslinjebehandling, inte belägg för ny publicering.
Tidpunkt och omdöme för första behandling hör till den senare granskade
rapporten och uppfinns inte av insamlaren.

`complete` betyder att alla valda externa och namngivna lokala observationer
är tillgängliga enligt dessa kontroller. Vid saknat index, version, detalj,
felaktigt innehåll eller annat läsfel blir paketet ofullständigt; lyckade
observationer finns kvar. Otillgängligt betyder **okänt**, aldrig oförändrat.

Endast kompletta paket får ett SHA-256-fingeravtryck över kanoniskt sorterade
identiteter, status, innehållshashar och versionsmappningen. Tider och
outputvägar ingår inte. `same_controlled_basis` är sant endast när både
föregående och aktuellt paket är kompletta och deras fingeravtryck är exakt
lika. Värden lämnar föregående paket som en dict; den ändras inte. En identisk
bas är inte sakgodkännande, fullständighetsbevis eller befogenhet. Referenser
flyttas inte fram och gamla beslut eller ärenden skrivs inte om eller dubbleras.

Äldre ofullständiga eller komprimerade paket avkodas eller skrivs aldrig om
i efterhand; deras ursprungliga revision och betydelse består. Senare intag
är en ny exklusiv privat observation. En ändrad hash förblir ändrad och blir
inte automatiskt godkänd genom transportreparationen.

AP09:s beslut och bevisluckor består. AP05 kan använda förändrade/saknade
underlag som stöd för omprövning. AP06 kan bereda motiverade åtgärdsförslag;
verkställande kräver handlingsspecifik befogenhet utanför denna modul.
Värden äger oberoende acceptans, separat granskning och skyddad integration.

## Syntetiska prov

Kör från repots rot med en installerad Python 3.12 eller senare:

```sh
python3.12 -B -m unittest discover -s tools -p test_bevakningsunderlag.py -v
```

Alla fixturer skapas i `.scratch` och städas efter provet. `fetcher` injiceras
i insamlingsproven; transportproven ersätter `build_opener` och prövar även
urllibs redirect-hanterare utan socket. Inga verkliga privata källor eller
nätkällor läses. Proven omfattar giltigt/identiskt/ändrat underlag, urvalsgräns,
deduplicering, råbytes, tidsuppgifter, saknade/felaktiga/för stora källor,
URL/redirect, symlänkar, befintligt output och bevarande av original/föregångare.
Transportfixturer använder `HTTPMessage` med verkligt stöd för upprepade headers.
Proven omfattar även identity/gzip, kodningsfel, separata storleksgränser,
begränsad expansion, trailer/kontrollsumma, gzip genom hela `collect` och
oförändrade äldre komprimerade paket. Tidigare datumetikett- och
URL/versionsregressioner finns kvar. Syntetiskt godkänt resultat återstartar
ingen förbrukad bevakningsomgång och aktiverar ingen ändrad kod; fryst acceptans
och oberoende granskning ägs av värden.
