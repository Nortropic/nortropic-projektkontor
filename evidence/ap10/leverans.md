# AP10 — avgränsat lokalt bevakningsansvar

Det namngivna Python-/Temporal-åtagandet använder kontorets befintliga ärende,
AP05:s källbindning, AP06:s förslagsberedning och AP08:s daterade redovisning.
Temporal bär kalendern och samma motor kan samtidigt bära accepterat AP04-arbete.
Nya sakbedömningar kräver separat granskning; privat arbete har ingen PR-väg.

## Tillämpning och bevisens räckvidd

Ett uttryckligt märkt engångskalenderprov startade utan manuell trigger efter
att den särskilda interaktiva startterminalen hade avslutats. Den övervakande
assistentkonversationen var fortfarande aktiv. Provet omfattade verkligt
externintag, lokal observation, analys och separat granskning. Det är inte
bevis för flera dygns drift eller för arbete när datorn är avstängd.

En annan utförare tog faktiskt över sparat operatörsarbete, genomförde
återkomst/intag och lämnade tillbaka konkreta diagnoser. Två tidigare
kvalificeringsomgångar bevaras oförändrade som otillräckliga; rättningarna
prövades i nya identifierade omgångar efter skyddad integration.

Sakutfallet för den valda användningen är behåll inom avgränsad räckvidd.
Komponentspecifika ändringar blir inte generella Temporal-egenskaper. Ingen
allmän säkerhetsklarering, beroendeuppgradering eller starkare graceful-drain-
garanti följer. AP09:s kvarvarande bevisluckor och tidigare auditstatus består.

Ett verkligt behövligt AP04-uppdrag byggde bevakningens läsbild medan åtagandet
var aktivt. Åtagandets stopp lämnade detta bygge och den delade tjänsten kvar.
Fryst acceptans, separat kodgranskning och skyddad integration har använts.
Isolerade prov kompletterar verkligheten för bortfall, dubbletter, ändrat
underlag, otillåtna handlingar, paus, avbrott, återkomst och begränsade resurser.
Syntetiska utfall är inte uppmätta verksamhetseffekter.

## Slutbindning

Verifierat 2026-09-21. Aktiv Runtime `ac62629983805015e8c0c040098c2d5287dbc41e`, kontor
`09e1e44f7ba2fc5522e3137da01d528ec7138a10` och lokal konfiguration SHA256
`ffb4ae62e6dac010a0058da1c11ed25a75190469cf49896992939c80ee3fa30f`.

Kontorskodens skyddade integration: https://github.com/Nortropic/nortropic-projektkontor/pull/21. Runtime-vägen:
https://github.com/Nortropic/nortropic-runtime/pull/21. Den separata helkedjegranskningen
godkände slutbindningen inom redovisad räckvidd. Exakta privata kvitton och
slutbild finns i den befintliga privata hemvisten. Dokumentens senare integration
ändrar inte det aktiverade kodparet.

Den verkliga privata kvalificeringens ursprungliga revisions-, konfigurations-,
observations- och granskningsidentiteter bevaras. Slutreleasen återanvänder dess
privata körbevis genom verifierad byteekvivalens; den nya läsbilden och native
kalenderns slutargument kontrolleras faktiskt. Revisionsbyte räknas inte som
nytt intag eller ny sakgranskning. Privata källor, resultat och råhistorik
publiceras inte.

## Fortsatt drift

Endast `office-python-temporal` lämnas aktivt, dagligen 09:00 Europe/Stockholm.
BUFFER_ONE och 22 timmars catchup medger högst en missad giltig schematid.
Inga historiska observationer återskapas. Inloggningsstarten är användarägd,
RunAtLoad utan KeepAlive-omstartsloop. Kod och konfiguration är frysta.

Native workflowgräns är 1200 sekunder inklusive kö, med begränsad städning.
Högst en analysprocess och en oberoende granskarprocess per omgång, noll
automatiska omtag. Processförsök är inte antal backendanrop eller exakt
abonnemangs-/tokenkostnad. Privat lagring har periodisk vakt, inte exakt quota.
Den privata kvalificeringen redovisar tillgänglig faktisk användning; ingen
uppmätt tidsbesparing eller garanterad ägaravlastning påstås.

[Driftanvisningen](../../docs/bevakningsansvar-ap10.md) beskriver läsning,
resursram, paus, stopp och avregistrering. AP08 är en privat daterad läsbild,
inte livebevakning eller aktiv notifiering. Planen äger nästa handling.
Utvecklingsfasens avslut startar ingen ytterligare byggfas eller något annat
stående åtagande.
