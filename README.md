# Nortropic Projekt- och innovationskontor

Ett hem för ägarens definition och beslut, etablerat inom Nortropics första byggfas.
Börja i [AGENTS.md](AGENTS.md). Aktuellt läge finns i [planen](docs/plan.md).

## AP-04 — uppdragsfunktionen byggs

Aktivt mandat och klart-när: [uppdrag](docs/uppdrag.md). Aktuellt läge och nästa
handling finns bara i [planen](docs/plan.md). Etableringen är avslutad.

Från repots rot: `python3 -B tools/kontor.py start --task resultat.json` startar
ett bevarat accepterat uppdrag. `status` läser senast sparad Runtime-observation;
den visar ålder och påstår inte att motorn eller GitHub observeras live.
`fortsatt` använder Runtimes befintliga återupptagning; `--diagnosis`,
`--review-repair`, `--review-retry` eller `--reconcile` kräver ett utrett skäl.
Kedjedrivaren håller uppdrag och kommandon aktuella i planen.

`resultat` är nästa verkliga uppgift genom den granskade startingången; modulen
är ännu inte levererad. Ingen av läshandlingarna får starta eller fortsätta arbete.
Runtime ska ligga i den befintliga syskonkatalogen `Nortropic Runtime`.
