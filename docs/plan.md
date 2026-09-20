# Levande plan — besluthemmet

AKTUELLT STEG: Separat dokumentgranskning efter körda P1 och P3; fasen är ännu inte levererad.

NÄSTA HANDLING: Låt den separata granskaren pröva dokumentkandidaten och provprotokollen mot O1–O9; rätta eventuella blockerare och visa rättelserna för granskaren före uppladdning.

ÅTERUPPTAGNINGSPUNKT: `docs/plan.md` i `nortropic-projektkontor`, gren `main`. Börja utan skrivningar, kontrollera `git status --short --branch`, `git log -1 --oneline`, artefakter och processläge. Byggaren Codex äger skrivansvaret under pågående fas; övertagande kräver att den föregående skrivaren konstaterats avslutad. P1 och båda P3-sessionerna har lämnat svar och avslutats med exit 0; granskaren arbetar enbart läsande.

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

Separat dokumentgranskning O1–O9 med eventuella rättelser och omkontroll,
innehållskontroll, publikt fjärrrepo, verifierad uppladdning samt lokal arkivkopia
med filhashar. P1 och P3 är körda på commit `300c239f2e33abf29140ac41e2e9d3b220a2cf00`;
värdens bedömning finns i `evidence/entry/provbedomning-300c239.md`. Lokal råevidens och bevarandepunkter
ligger i Git-exkluderade `evidence/entry/local/` och ska inte laddas upp.

## Väntan och begränsningar

Codex CLI 0.147.0 nekades modellen med HTTP 400. Försöket bevarades och
avslutades; redan installerad appbinär 0.155.0-alpha.2.6 gav lyckat P3. Ingen
installation eller global verktygsinställning ändrades av byggaren. Interaktiva
verktygsstarter lagrar själva sessionshistorik och projektets trust-val i sin
befintliga användarprofil; inga andra projekts inställningar ändrades.
Inget känt kapacitetsstopp. Ingen saknad ägaraccept. A3 och A6 för förberedelsen
är inte uppfyllda; FIND-004 är inte stängt. Ingen Runtime-körning, ingen visad
minskad ägarbörda och inget bevis för efterlevnad över tid. När denna fas är
verifierad stannar byggaren. Nästa bygge kräver eget accepterat uppdrag.
