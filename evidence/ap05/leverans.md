# AP-05 — ändringsbedömning och det verkliga kartärendet

Kodstödet och den separat granskade kartbedömningen är verifierade. Fasens
slutliga bevarande/integration binds utan självreferens av det lokala kvittot
`evidence/ap05/local/final-<kontorets HEAD>.json`. När kvittot matchar publicerad
HEAD är fasen avslutad; starta inte fler uppdrag eller kartändringen.

## Levererad arbetsförmåga

`tools/change_assessment.py` har två läsande kommandon: `manifest` tar fram de
redan bundna referenserna; `report` binder en kontrollobservation till dem och
redovisar berörda slutsatser/handlingar. Källuppgift, bedömning, beslut och
handlingsspecifik befogenhet hålls isär. Ändrat, saknat, osäkert eller ej kontrollerat
underlag markerar beroende slutsatser för omprövning, utan automatisk
falskförklaring, upphävande, hashuppdatering eller tillståndsgivning.

Källornas bytes mäts av befintligt Runtime-verktyg evidence_index. Värden läser
verkliga källor med befintlig åtkomst och bevarar privata fall lokalt. Runtime
bygger/testar/granskar/integrerar den syntetiska kodkandidaten. Ingen ny motor,
databas, modellanslutning, kostnad, behörighet eller generell uppdragsgrind.
Använd befintlig Python 3.12 enligt README och `tools/CHANGE_ASSESSMENT.md`.

## Verkligt utfall

[Fallbedömningen](../../cases/map-layer/assessment.md) skiljer det redan fattade
I-11 från den gamla tekniska domen och de nya observationerna. Generator/kvitto
hade ändrats efter FINAL-CHECK-1. Domen förlängdes inte tyst: en avgränsad ny
läskontroll visade 938 bevarade historiska filer, 261 förväntade tillägg och
rättelsetäckning inom redovisad lexikal/manuell räckvidd. Separat granskare
reproducerade observationerna. Exakt historisk generatordiff är fortfarande obelagd.

Det slutliga dokumenterade receptet kördes ordagrant mot det verkliga fallet:
1235 bundna källor matchade sina uttryckligen författade AP-05-referenser;
`complete_search=false` och valvskrivning `not_granted` bevarades. Detta säger
inte att källorna är oförändrade sedan FINAL-CHECK-1. Bevis:
[documented-application.json](documented-application.json),
[case-review.md](case-review.md) och
[case-evidence.json](../../cases/map-layer/case-evidence.json).
V1/v2/v3, fulla mätningar, underlag och återläst källarkiv finns lokalt.
Inga interna källor eller råsessioner följer med den publika redovisningen.

**Nästa kartärendehandling:** lämna den bundna befintliga kandidatens ingång,
översikt och lagerförklaring till ägaren via befintlig privat läsåtkomst för
begriplighetsomdöme. Därefter behövs ett separat avgränsat beslut om eventuell
kartleverans med målvalvets aktuella läge, kollisionskontroll, bevarandepunkt och
uttryckligt skrivmandat. I-11 ställs inte på nytt. Ingen kartskrivning startas i AP-05.

## Körning, prov och integration

Runtime-kod i båda uppdragen, oförändrad:
`2789ea0770e4234161e9bdb0378a6e3e7b8432d2`.

| Uppgift | Verkliga revisionsbindningar | Bevis |
|---|---|---|
| Huvudbygge office-change-assessment-1 | Input a218038b0952ab9d6b48f04bec4d231d5c16cbeb; slutkandidat 627bfac916a6ed0e5e47aa6d3ec439a8b1c4353a; integration ad3e7a1187cdfb52fbe58e38f07782774c415eff i PR4 | [assessment-run.json](assessment-run.json) |
| Teknisk metodrättelse inom samma AP-05 | Kandidat a6d9eec1e3a84ee7ee71716900c8063dd21c813b; integration f4deee4086efd9134060a4a42a4406c4d9fdc422 i PR5 | [recipe-run.json](recipe-run.json) |

Huvudbygget hade tre försök: separata granskare stoppade först giltiga tidsformat,
sedan bråkdelars tidsordning. Befintlig review-repair återanvändes med bevarad
historia, samma task/bas/acceptans och nya granskade kandidater. Inga blinda
omförsök eller ägarreläer. Separat metodgranskning rättade verktygsanropet och
värdansvaret. Dess sista kollisionsfynd återfanns efter huvudkörningens native
slutgranskning och stängdes därför genom den särskilda tekniska följduppgiften,
med egen fryst acceptans och separat granskning. Det doldes inte av ett tidigare
"approved". Slutlig metodrättelse klarade 20 enhetstester och frysta värdprov;
separat granskare provade även 15 riktade innehållskollisioner.

[workflow-verification.json](workflow-verification.json) visar faktiskt samspel
med befintlig hashverifierare: legitimt urval, förändring, borttagning, osäker
symlänk och ogiltig mätning. Alla mutationer skedde i isolerade syntetiska fixturer.
Frysta prov täcker även saknade referenser/skäl, okänd befogenhet, ofullständigt
urval, fel manifest, tidsordning, orörda referenser och ren import/API.
Runtimes separata granskare prövade kod, testfall och publik säkerhet före integration.

Grenskyddet kontrollerades före körning och av publiceraren före varje integration.
PR4/PR5:s verkliga head, merge, tree och obligatoriska statusresultat jämfördes
separat med körbevisen. Funktionens egen resultatutskrift var inte ensam bevisning.
Det avslutande dokument-/bevispaketet integreras med samma obligatoriska kontroller.

## Bevarande och räckvidd

[native-preservation.json](native-preservation.json) binder återläst privat arkiv
med båda körningarnas fulla historik, kandidat- och granskningsversioner samt en
konsekvent backup av befintlig Runtime-databas. Tidigare leveranser/historiker
är kvar. Runtime har inga spårade källändringar; nya lokala körbevis är normal
motorkörning. Kampanjens kontrollerade original, IR och valvet är orörda.

Färsk mottagare och avslutskandidatens separata granskning dokumenteras i
handover.json respektive closeout-review.md. Slutkvittot binder slutlig offentlig
revision till återläst GitHub-arkiv och lokalt arkiv. En publik klon saknar privata
källor och native körhistorik: den kan läsa kontrollerad fallredovisning och köra
syntetiska prov, men får inte fabricera ny källkontroll eller Runtime-status.

Oförändrade valda källor bevisar inte fullständig källsökning; nya filer hittas
inte automatiskt. Programmet autentiserar inte beslut och ersätter inte omdöme.
Ingen verklig valvläsning/-skrivning, full IR-audit eller allmän generatorgaranti
visas. A3, A6, FIND-004 och övriga tidigare auditfynd står kvar. AP-04:s kvalificerade
start/återupptagning/isolering/grenskydd återanvänds inom sin redovisade räckvidd;
ingen ny totalgranskning eller etablering gjordes.
