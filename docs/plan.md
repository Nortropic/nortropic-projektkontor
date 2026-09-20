# Levande plan — besluthemmet

AKTUELLT STEG: Verifiera etablerade dokument genom P1, P3 och separat dokumentgranskning; fasen är ännu inte levererad.

NÄSTA HANDLING: Byggaren bevarar dokumentkandidaten i Git och startar det färska interaktiva P1-provet med Claude Code i repots rot, enbart läsrätt.

ÅTERUPPTAGNINGSPUNKT: `docs/plan.md` i `nortropic-projektkontor`, gren `main`. Börja utan skrivningar, kontrollera `git status --short --branch`, `git log -1 --oneline`, artefakter och processläge. Byggaren Codex äger skrivansvaret under pågående fas; övertagande kräver att den föregående skrivaren konstaterats avslutad. Inga provsessioner är ännu startade.

## Utfört och läst

Definitionen är mekaniskt hämtad; beslutsloggen, uppdraget och ingångarna finns.
Startidentiteter och källkontroll: `evidence/entry/start.json`. Ingen fasaccept
eller godkänd granskning påstås ännu. Befintliga abonnemangsinloggningar för
Claude Code och Codex samt GitHub-inloggning är tillgängliga; ingen ny behörighet,
installation eller tjänst har skaffats.

Riktat nuläge (full läsredovisning i uppdraget):
- **Finns:** `~/Nortropic Runtime`, HEAD/main `a941207a9ca57697967cf33dcd1c3ea5d884051a`, releasecommit `580630bcb9d46bb11e17e25053664eec4e23b8ae`; arbetsform och provformer återanvänds.
- **Finns:** förberedelsekampanjen under `~/nortropic/intake-campaigns/improvements-preparation-2026-09`, filrevisioner i startprotokollet. B-5 och arbetsorderns SHA-256 stämmer.
- **Fanns inte:** målrepot före start; central definitionsfil inte funnen i den riktade sökningen. Det senare är ingen total inventering.
- **Kunde inte nås:** inget nödvändigt namngivet underlag.

## Återstående inom accepterad fas

P1 och P3, separat dokumentgranskning O1–O9 med eventuella rättelser och omkontroll,
innehållskontroll, publikt fjärrrepo, verifierad uppladdning samt lokal arkivkopia
med filhashar. Proven är ännu inte körda. Lokal råevidens och bevarandepunkter
ligger i Git-exkluderade `evidence/entry/local/` och ska inte laddas upp.

## Väntan och begränsningar

Inget känt kapacitetsstopp. Ingen saknad ägaraccept. A3 och A6 för förberedelsen
är inte uppfyllda; FIND-004 är inte stängt. Ingen Runtime-körning, ingen visad
minskad ägarbörda och inget bevis för efterlevnad över tid. När denna fas är
verifierad stannar byggaren. Nästa bygge kräver eget accepterat uppdrag.
