# Nortropic Projekt- och innovationskontor

Ett hem för ägarens definition och beslut, etablerat inom Nortropics första byggfas.
Börja i [AGENTS.md](AGENTS.md). Aktuellt läge finns i [planen](docs/plan.md).

## AP-04 — uppdragsfunktionen

Från repots rot, med befintlig Runtime i syskonkatalogen `Nortropic Runtime`:

- `python3 -B tools/kontor.py status` visar senaste sparade observation.
- `python3 -B tools/kontor.py resultat` visar verifierad leverans och bevisreferenser.
- `python3 -B tools/kontor.py start --task NAMN.json` startar ett nytt accepterat,
  committat uppdrag. Det avslutade resultatbygget får inte startas igen.
- `python3 -B tools/kontor.py fortsatt --task NAMN.json` återupptar samma körning.
  Diagnos/review-återgång använder dokumenterat skäl och befintlig Runtime-grind.

Utan --task väljs den levererade uppgiften `resultat.json`. Status och resultat är
rena läsningar och visar observationens ålder; ingen livebevakning eller aktuell
GitHub-status påstås. De kräver lokala Runtime-bevis. En klon utan dessa ger
otillgänglig evidens, inte en fabricerad leverans. Start/fortsättning kräver exakt
Runtime-revision som uppdraget accepterar; läsning kräver inte ny modellkörning.
Kontorets kvalificerade utförarprofil är Codex; gamla Runtime-repots providers
är oförändrade. Kedjedrivaren bär kommando, kör-id och diagnos i [planen](docs/plan.md).

[Leveransbevis](evidence/ap04/delivery-verification.json) binder den riktiga
resultatfunktionen, avbrottet/återupptagningen och PR2. [Slutredovisningen](evidence/ap04/leverans.md)
anger räckvidd och återstående avslutskontroll. Nästa byggfas behöver eget mandat.

## AP-05 — ändringsbedömning

Kodstödet är verifierat med befintlig Python 3.12. På denna värd används
`/opt/homebrew/bin/python3.12` för metodens Python-kommandon; systemets `python3`
kan vara en äldre version. Ingen installation eller ny anslutning behövs.

[Metoden och kommandona](tools/CHANGE_ASSESSMENT.md) binder utvalda källversioner
till källuppgifter, sakbedömningar och befogenhet för varje handling. Ändrat eller
saknat underlag markerar berörda slutsatser för omprövning; verktyget fattar inga
beslut och ger inga tillstånd. Befintligt Runtime-verktyg mäter filerna, värden
läser verkliga källor och bevarar privata ärenden lokalt.

[Det verkliga kartärendet](cases/map-layer/assessment.md) bevarar AP-05:s dåvarande
bedömning. Den senare kartleveransen är avslutad; öppna den inte på nytt ur denna
historiska falltext. Aktuellt läge ägs av planen.
[AP-05:s leveransbevis](evidence/ap05/leverans.md) anger körning, granskning och
begränsningar. Endast kontrollerad fallredovisning är publik; intern källmappning
och original ligger i den lokala, Git-exkluderade evidensdelen. Nästa handling
ägs fortsatt av [planen](docs/plan.md), inte av en parallell ärendemotor.

## AP-06 — källbunden uppdragsberedning

[Användning och exempel](tools/BERED_UPPDRAG.md) är ingången till det lokala
kommandot. Det sammanställer valda underlag till ett nytt privat utkastspaket,
med spårbara krav/skäl/prov och konkreta luckor. Kedjedrivaren väljer och bedömer
underlag, sakgranskar och fryser uppdraget före AP04:s Runtime-start; inga
rutinmässiga ägarbesked införs. Beredningen startar aldrig Runtime eller ger mandat.
[Leverans och bevis](evidence/ap06/leverans.md) beskriver det verkliga uppdrag
som kärnan beredde och Runtime genomförde. Nästa handling finns endast i planen.
