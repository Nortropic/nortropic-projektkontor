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
