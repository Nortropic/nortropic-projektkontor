# AP08 — privat leverans- och beslutsbild

Kontoret kan framställa en samlad, lokalt öppningsbar svensk läsingång ur utvalda
leveranser, sparade körbevis, plan och beslut. Kedjedrivaren samlar underlagen och
gör sakbedömningen; ägaren behöver inte sammanföra maskinformat eller kör-id.
Den verkliga bilden är privat och nås lokalt via `evidence/ap08/local/LAS-MIG.md`.
En publik klon innehåller kod, syntetiska prov och anvisning, inte ägarens data.

## Genomförd funktion och verifiering

Befintlig Runtime byggde `tools/agarbild.py`, dess syntetiska prov och
`tools/AGARBILD.md`. PR12 integrerade exakt kandidat efter det frysta hostprovet,
separat kodgranskning och verifierade serverskydd. `presentation-run.json` binder
revisioner, de tre produktfilerna och fem ursprungliga kör-/granskningsbevis.
19 syntetiska tester passerade hos utföraren; den separata kodgranskaren körde
12 läsprov och inspekterade CLI-skydd/prov utan egna filskrivningar. Hostacceptansen
körde CLI i befintlig sandlåda och prövade negativa fil-/underlagsfall.

Prov omfattar saknat/gammalt/motsägande underlag, ersatt väntan, verklig ägarfråga
och uttryckligt inget beslut; tidsgränser, injektion, filbevarande och exklusiv
privat utmatning. HTML har inga script, externa resurser, körknappar eller
formulär. Länkar är interna; källplatser är text. Formatkontroll avgör inte sak,
aktuellt driftläge eller befogenhet. Granskning och determinism stödjer ren
rendering; audit-hooken ensam detekterar inte systemklockläsning.

Verkligt arbetsuttag är källgranskat mot 13 uttryckligt valda källor. Två
formulerings-/tidsbindningar rättades med den tidigare versionen bevarad.
Separat kontroll av faktisk HTML jämförde 153 textvärden och 26 interna länkar.
En färsk modellbaserad mottagare läste den riktiga sidan i Chrome, öppnade alla
13 fördjupningar och återfann användning, begränsningar, ålder, nästa handling,
ansvar och beslutsbehov. `application-review.json` anger räckvidden.

Arbetsuttaget bevarar verkligt pågåendeobservation. Det senare privata slututtaget
ska bindas till faktisk kodintegration, separat tillämpningskontroll och slutkvitto,
inte till presentationens egen utskrift. Exakt slututtag, dess deltakontroll och
avslutsrevision binds i privat `local/final.json`. Planen anger slutkontroll och stopp.

## Begränsningar och bevarande

Detta är en daterad projektion, inte livebevakning, automatisk källupptäckt eller
stående redovisningstjänst. Rapportframställning föryngrar inga observationer.
Saknad observation är inte inaktivitet. Leverans och tillgänglighet hålls isär,
liksom historik och aktuellt arbete, förslag och accept. Det ersatta försöket
förblir historik och får inte återupptas.

Mottagarprovet visar modellens återfinnbarhet, inte ägarens personliga begriplighet
eller tids-/arbetsbesparing. Fulla källtexter återges inte i HTML; tekniska
fördjupningar binder valda källor med textplats, revision, tid och hash. Tidigare
auditfynd förklaras inte om eller stängs. AP07 är frivilligt ANPASSA, utan belagd
förbättring och utan ny pilot. Tidigare leveransers räckvidd består.

`native-preservation.json` binder återläst privat körarkiv och konsistent databasbackup.
Privata källor, råsessioner och rapporter publiceras inte. Kopior på samma disk är
inte skydd mot diskförlust. Ingen Runtime-kod, IR, kampanj eller valv ändrades.
Nästa utförare använder anvisningen och privat överlämning; ingen ny fas startas.
