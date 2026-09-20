# Levande plan — AP07 avslut och stopp

AKTUELLT STEG: AP07:s låsta pilot är genomförd. [Metodbeslut ANPASSA](metodbeslut-ap07.md)
ger valbart stöd i befintlig arbetsform, ingen ny kontrollrutin. Läs
[tillämpningsbevisen](../evidence/ap07/tillampning.md) och
[leveransredovisningen](../evidence/ap07/leverans.md). Etableringen, AP04–AP06 och
kartleveransen tillgodoräknas inom sina räckvidder. A3/A6 och tidigare fynd består.

NÄSTA HANDLING: Finns verifierat evidence/ap07/local/final-<fjärr-main-revision>.json
som matchar detta publicerade träd är AP07 levererad: redovisa och stanna.
Saknas kvittot ska kedjedrivaren endast slutföra det redan granskade avslutets
skyddade integration, fjärrjämförelse och privata bevarande. Inga pilotkörningar,
byggen eller tidigare tasks ska startas om. Ny funktionell fas är inte beställd.
En publik klon utan privat evidens kan läsa resultatet men inte fabricera kvittot.

ÅTERUPPTAGNING: work/ap07-delivery; kontrollera Git, aktuell fjärr-main, separat
review, publication-gate/publication-kvitto och faktiska registrerade processers
avslut före skrivövertagande. Status/resultat är rena läsningar. Tekniska
avslutssteg bärs av kedjedrivaren, inte av nya rutinprompter från ägaren.

Runtime 2789ea0770e4234161e9bdb0378a6e3e7b8432d2 är oförändrad. Metodartefakten
levererades genom office-method-trial-1, PR10 / 16d11720e4c5f0caba30b9709d0a877cfab83217.
Dess prövningsversion är bevarad; slutpaketet tillför metodbedömning och läsanvisning.
Fyra färska hostledda försök har egna nativejournaler under local/trial-runs/ och
exakta provytor under local/trials/. De är avslutade engångsprov, inte nya schedulers.

Privat återfinns mandat, tidigare AP05/AP06-beredningsversioner, faktiska indata,
råspår, granskning och arkiv i evidence/ap07/local/. Det tidigare beredningsarbetet
finns även på work/ap07 och i ap07-work-history.bundle; det är inte publik ancestry.
Ingen Runtime-kod, kampanj, IR, valv eller annan byggfas ingår. AP06 CLI1 är en
bevarad ersatt väntan och får aldrig återupptas eller få frysta kontroller ändrade.
