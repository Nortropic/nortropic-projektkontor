# Avgränsad metodrättelse inom AP-05

Runtime-huvuduppgiften integrerades i PR4 efter fryst acceptans och separat
review-3. En kompletterande metodgranskare fann därefter en kvarstående
kollision: output under en saknad vald källsökväg kunde skapa källsökvägen som
katalog. Fasens klart-när är därför inte uppfyllt enbart genom huvudkörningens
completed. Fyndet varken döljs eller stängs av den native granskningens godkännande.

Fyndet reproducerades av värden i en isolerad syntetisk kopia. Baslinjens
avsedda felutfall bevaras lokalt i recipe-baseline-failure.json. Inga original
ändrades. Den tekniska följduppgiften office-change-assessment-recipe-1 rättar
bara metodens kollisionsvillkor och tillför regression i befintligt test.
Kärnmodul och Runtime är oförändrade. Samma kvalificerade Runtime-väg används.

Separat kontraktsgranskning av /root/ap05_contract_review: godkänt för start,
inga blockerare. Verifierad acceptans-SHA256:
`4a0222c17fe3978876ecf0e7af2964a2a7f6dd6ea434d12537b595d44b1e4203`.
Brief `e32411d6233a48622682bce9ffd6a4fe1ca21c1d884b39de2e8601dbdd89b600`;
task `d71791e526419e1c62d4606bba20661992f32d41a0b2061fd32a6b1d50bc2d6b`.

Värdprovet exekverar dokumentets faktiska recept i befintlig native sandbox med
syntetiska filer. Det prövar output under/över/på vald källa samt legitim ny
output under bred gemensam rot, bevarade källvägar och tidigare enhetstester.
Separat Runtime-granskning krävs före följdkandidatens skyddade integration.
Slutlig korrigeringsdom och körbevis finns i leverans.md när fasen är färdig.
