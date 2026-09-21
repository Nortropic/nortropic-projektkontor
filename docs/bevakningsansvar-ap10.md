# AP10 — ett namngivet lokalt bevakningsansvar

Kontoret bevakar samma avgränsade Python-/Temporal-användning som AP09.
Det läser relevanta officiella releaseförteckningar och utgåvenoter, jämför
namngivna lokala underlag och låter granska nya sakbedömningar. Leverantörens
påstående, lokal användning, bedömning och befogenhet hålls åtskilda.
Ett åtgärdsförslag bereds genom AP06; det genomförs aldrig av bevakningen.

## Arbetsväg och återanvändning

En native Temporal Schedule, `office-python-temporal`, driver den privata
kedjan intag → bedömning → separat sakgranskning → privat redovisning.
AP05 kontrollerar bundna källberoenden. AP06 används vid konkret åtgärdsförslag.
AP08 ger en daterad läsbild. Runtime äger körning, schema och återkomst; kontoret
äger källurval och sakbedömning. AP04-byggarbetets tester, oberoende kodgranskning
och skyddade publicering består oförändrade. Privat sakbedömning har ingen PR-väg.

Varje omgång observerar både externa källor och lokal användning på nytt.
En fullständigt oförändrad kontrollerad grund kan återanvända ett faktiskt
bundet tidigare granskat besked. Ursprunglig granskningsdag och öppna luckor
bevaras. Saknad/ändrad källa eller lokal användning är inte ett automatiskt
sakbeslut. Felaktiga, saknade eller avvisade bevis ger otillräckligt besked.
Gamla omgångar skrivs aldrig om för att se aktuella ut.

Urvalet är begränsat till installerad Python major/minor-linje och installerad
utgåva samt installerad Temporal Python SDK och stabila utgåvor i dess begränsade
releaseindex. Det är ingen fullständig säkerhets-, kompatibilitets- eller
supportgranskning. Oförändrat urval bevisar inte att alla relevanta källor hittats.
AP09:s starkare graceful-drain-lucka och tidigare auditstatus består.

## Drift och resurser

Ordinarie tid är 09:00 Europe/Stockholm. Native BUFFER_ONE och 22 timmars
catchup-fönster medger högst en missad schematid vid återkomst, även när
Stockholms två morgnar ligger 23timmar från varandra. Äldre missar är luckor.
Nästa ordinarie tid är en ny händelse och kan följa en nyligen upphämtad omgång.
Ett märkt förkortat kalenderprov är inte flera dygns faktisk drift.

En gemensam aktivitetsslot kan köa vanligt byggarbete och bevakning. Den native
workflowens körgräns är 1200 sekunder inklusive kö. Stegens körgränser är
intag 90, analys 480, separat granskning 240 och rapport 60 sekunder, med begränsad
städning. Högst en analysprocess och en granskarprocess per omgång, noll
automatiska omtag. Detta räknar processförsök, inte enskilda backendanrop och
inte en exakt token-, abonnemangskvot- eller kostnadsbudget.

Otillgänglig källa, kvot eller autentisering ger bevarat bortfall, ingen snabb
omstart eller köpt reservväg. Senare ordinarie omgång kan göra ett nytt intag.
Privata loggar begränsas till 1 MiB per ström. Privat rund-/dispatchlagring har
en periodisk 512 MiB-vakt och 64 MiB startmarginal; den är ingen exakt diskquota.
Kortvarig tillväxt kan överskrida gränsen. Ingen automatisk gallring av historik.
Vid lagringshinder krävs operatörens diagnos och bevarande enligt befintlig väg.

Fryst kod/config ligger separat från arbetsgrenarna. Vanligt branchbyte ändrar
inte den aktiva koden. Endast det namngivna användarägda LaunchAgent-objektet
`se.nortropic.ap10-runtime` används. Det startar befintlig lokal motor vid
inloggning; ingen root-tjänst, extern värd eller ny nätport mot omvärlden.
Datorn måste vara tillgänglig. Sömn, utloggning, stopp eller kvotbrist medger
ingen garanti om utfört arbete. RunAtLoad gäller, ingen KeepAlive-omstartsloop.

## Läsning, paus och stopp

Från kontorsrepot skapas en ny privat daterad AP08-bild med:

```sh
/opt/homebrew/bin/python3.12 -B tools/bevakningsbild.py evidence/ap10/local/bild-YYYYMMDD-HHMM
```

Välj en ny katalog. Läs dess `index.html`. Läsningen startar ingen modell,
inhämtning, fortsättningssignal eller publicering. Den skiljer schema,
senaste faktiska observation och senast granskat besked. En gammal bild är
inte aktuell driftstatus. Ingen aktiv notifiering eller livevy utlovas.
Kedjedrivaren hanterar rutinmässig diagnos; ägaren tar endast verkliga beslut
om ändrat mål, kostnad eller befogenhet.

Från Runtime-repots rot används befintlig venv och den aktiva frysta vägen:

```sh
.runtime/temporal-venv/bin/python -B -m runtime.obligation status
.runtime/temporal-venv/bin/python -B -m runtime.obligation pause
.runtime/temporal-venv/bin/python -B -m runtime.obligation stop
```

`status` läser bara. `pause` hindrar nya starter och består över återkomst;
en pågående omgång får avslutas inom sin ram. `stop` markerar STOPPED och
avbryter/städar bara åtagandets egna körningar. Vanliga byggen och den delade
motorn fortsätter. Ett pausat åtagande kan uttryckligen `resume`:as av behörig
operatör. STOPPED kräver först uttrycklig omkonfigurering, exempelvis `daily`,
och därefter `resume`; inloggning återaktiverar inget pausat eller stoppat ansvar.

Avregistrering av loginstart är en annan åtgärd än bevakningsstopp: kontrollera
först andra byggen, avregistrera endast den namngivna LaunchAgenten och bevara
dess plist, databas, frysta releaser och historik. Exakta steg finns i Runtime
`docs/private-obligation.md`. Gör ingen blind databasåterställning eller ominstallation.

## Fortsättning utan återberättelse

Kontorets `docs/plan.md` äger läget och nästa handling. Privat hemvist är
`evidence/ap10/local/`; den publiceras inte. Där finns ägaraccept, bevis,
frysta revisions-/konfigurationsidentiteter och återupptagningspunkt.
En mottagare börjar läsande, verifierar att tidigare skrivare lämnat över och
använder samma ärende och befintliga verktyg. Detta åtagande ger ingen stående
rätt att bygga nya funktioner, ändra Runtime, uppgradera beroenden eller skriva i valv.
