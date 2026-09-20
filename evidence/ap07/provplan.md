# AP07 — försöksplan låst före observation

Status: förregistrerad hostplan inom AP07-ACCEPT. Inte resultat eller effektbevis.
Tidpunkt/bytes binds i local/protocol-freeze.json före första metodprov.
Tidigare paketgranskning tillgodoräknas. Ingen ny inventering/audit.

## Hypotes, jämförelse och motbevis

H1: När en avgörande koppling är osäker och saknar giltigt körbevis kan ett litet
representativt förprov ge ett beslutspåverkande observationstillskott före större
arbete, med befintliga komponenter. Metoden är ett val, aldrig obligatorisk grind.
H0/motbevis: vanlig läsning/granskning identifierar redan samma fråga och ger samma
beredningsbeslut; förprovet kräver den framtida produkten, provar fel miljö, ger
falsk trygghet, skapar fel i fungerande fall eller kostar arbete utan beslutsnytta.
PDSA/GOV.UK är metodstöd, inte lokal effektevidens.

Dagens arbetsform är käll-/kontraktsläsning, konkreta prov vid behov och separat
granskning. Den förbjuds INTE att köra kommandon eller upptäcka fel för att göra
jämförelsen gynnsam. Ingen mätning av generell produktivitet eller ägarbörda.

## Försök A — AP06:s utvecklingsfall (värden känner facit)

Återanvänd händelsekedjan och rättelsens gamla prov. Ny, avgränsad fråga:
kan antagandet om körkontext prövas med kärnan och beroendet som redan fanns på
CLI-bas dd1f8c5, utan den framtida CLI-kandidaten? Kopiera endast dessa historiska
produktbytes till isolerad provyta. Använd de två historiska launcherformerna i
provet utan att ändra deras frysta original. Jämför direkt körbar import med den
isolerade launchern. Registrera returkod/observation och vad den säger/inte säger.
Detta är ett retrospektivt genomförbarhetsprov med facitkunnig värd, inte blind
upptäckt eller nytt bevis att gamla rättelsen fungerar. Normal källläsning skulle
också kunna finna felet; historisk granskning missade det just då.

## Försök B — överföring och fungerande kontrast

Två små underlag, bytebundna innan färska körningar:
- X: AP05:s första metodrecept i kandidat c4ac46ba. Ny observation av förmågan
  att granska/pröva recept före rättelse/fortsatt integration; inte före ursprungsbygge.
- Y: den senare fungerande motsvarigheten med samma befintliga verktyg och
  syntetiska data. Exakta urval redovisas privat. Y är ett fungerande kontrastfall,
  inte en norm att kräva fler kontroller när befintligt underlag räcker.

Fyra engångskörningar: befintlig arbetsform på X och Y, metodanvisningen på X och Y.
Varje körning har ny ephemeral CLI-session med befintlig Runtime-providerprofil,
endast vald provyta läsbar och .scratch skrivbar, nät/externa verktyg avstängda.
De är hostledda metodtillämpningsprov, INTE produktkandidater, nya motorer eller
Runtime-taskhistorik. Artefaktbygget sker separat genom vanlig AP04/Runtime.

Samma uppgift och sakunderlag per X/Y, skillnad endast tillgången till den generella
metodanvisningen. Utföraren får inte rättelsefacit, felkategorin, de historiska
reparationsprotokollen eller en checklista över kommandon som avslöjar svaret.
Metodanvisningen innehåller generella beslutskriterier och ett orelaterat syntetiskt
exempel, inga AP05-/AP06-diagnoser. Befintlig arbetsforms instruktioner följer med
båda armarna. Fyra separata körningar begränsar överföring mellan armar men är inte
statistiskt jämförbara grupper; samma modell, historiskt urval, ingen randomisering.

Utföraren ska först anteckna läst underlag, osäkerhet, första beredningsbeslut,
vald/avstådd kontroll och förväntat utfall. Därefter väljer och genomför den själv
relevant minsta prov om motiverat. Efteråt: faktiska observationer, beslutets
förändring eller oförändring, tillräckligt nästa steg, facitexponering och gränser.
Båda armarna får avstå prov med skäl; metodarmens överföring är endast visad om
utföraren faktiskt väljer/genomför ett relevant prov där behov finns. Värden fyller
inte i ett saknat prov åt utföraren för att rädda hypotesen.

## Bedömningsregler låsta före utfall

Registrera utan ny infrastruktur: tid/usage ur befintlig CLI-output, faktiska
kommandon/förprov, rättningsförslag och motiverat slutbeslut. Värdens arbete med
urval, isolering, underlagskontroll och granskning redovisas separat; sessionstid
är inte mänsklig arbetstid, tokens är inte kostnad eller nyttomått.

Bedöm X: upptäcktes verklig oförenlighet; var observationen relevant; motiverades
rättelse/stoppa fortsatt integration? Bedöm Y: kunde fungerande flöde fortsätta utan
obelagt fel, onödig rättning eller omotiverad granskningseskalering? Skilj verkligt
produkt-/receptfel från provytans eget förberedelsefel.

Anta endast en snäv valbar metod om observationer ger relevant stöd utan oacceptabla
nackdelar. Anpassa om nyttan gäller en snävare situation eller vanlig arbetsform
redan gör samma sak. Avstå om ingen tillräcklig tillförsel visas. Likvärdiga utfall
är inget positivt effektbevis. Begränsad tillämpbarhet kan beskrivas utan att påstå
överlägsenhet. Inget extra fall läggs till för att vända ett negativt utfall.

Hängning/tekniskt startfel: bevara exakt försök; en motiverad teknisk rättelse får
återuppta samma sakprov i ny version, aldrig tyst byta underlag eller dölja exponering.
Försöksgräns hanterar hängning, ingen total projekttidsgräns införs.
Separat granskare bedömer underlag, exponering, observationer, kontrast, jämförelse,
extra arbete och slutsats före metodadoption. A3/A6 och tidigare fynd oförändrade.
