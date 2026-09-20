# AP07 — tillämpning och jämförelse

Separat sakgranskad slutsats: **anpassa till valbart stöd inom befintlig
arbetsform; inför ingen ny kontrollrutin**. Prövningen visar självständigt provval
och avgränsning. Den visar inte bättre beslut än grundarmen eller minskad ägarbörda.

## Vad vi faktiskt gjorde

Hypotes, jämförelse och motbevis låstes före observation i [provplanen](provplan.md).
AP05/AP06 användes för verklig beredning: tidigare versioner med öppna mandat-/
acceptansluckor bevarades, det accepterade mandatet lades till explicit, och en
riktad rättelse i värdens exempelkontroll granskades innan Runtime-start.
De 23 bundna underlagen matchade vid [jämförelsen inför avslut](source-recheck.json).
Detta är avgränsad integritetskontroll, inte sakgodkännande eller fullständig sökning.

Runtime byggde den generella metodbeskrivningen och dess fristående syntetiska
exempel. [Körbevis](method-run.json) binder fryst acceptans, separat artefaktgranskning
och skyddad PR10. Exemplet handlar om enhetsomvandling och avslöjar inga falldiagnoser.

AP06:s utvecklingsfall prövades separat med endast kärna och beroende från
`dd1f8c56456b575f017219621402658b5200c592`, före den framtida CLI-kandidaten.
Direkt körning lyckades; isolerad runpy-körning saknade syskonimport och avslutade
med kod 1; kontrollerad importkontext lyckades. Det visar att den konkreta osäkerheten
kunde prövas med då tillgänglig kod. Värden kände facit. Detta är ett retrospektivt
genomförbarhetsprov, inte blind upptäckt eller ett nytt effektbevis för gamla rättelsen.
Det verifierar inte den framtida CLI:n i sin helhet. Vanlig kodläsning kunde också
identifiera frågan.

Fyra färska engångskörningar använde befintlig kvalificerad providerprofil, med
separata läsbara provytor och endast egen `.scratch` skrivbar. Ingen ny motor
eller anslutning byggdes. X innehöll ett ordagrant utdrag ur det äldre AP05-receptet;
Y det fungerande receptet. Verktygsbytes var bundna och gemensamma. Det var inte
en återspelning av hela den historiska miljön. Inom varje fall skiljde indata
endast genom tillgången till metodanvisningen och uppmaningen att bedöma dess nytta.

## Observation och beredningsbeslut

| Fall | Före eget prov | Självvalt prov och observation | Efter prov |
|---|---|---|---|
| X, befintlig arbetsform | Anpassa kopplingen: läsning visar olika gränssnitt. | En syntetisk källa, oförändrat recept och faktisk verifierare. Exit 2, otillgänglig mätning, ingen rapport. | Samma beslut, nu underbyggt av körutfall och bevarat fel. |
| X, metodanvisning | Samma gränssnittshinder hittat genom egen läsning. | Eget en-källsprov av originalreceptet; samma exit 2 och bevarade felutfall. | Samma beslut; rekommenderad rättelse är inte utförd. |
| Y, befintlig arbetsform | Preliminärt användbart; hela kopplingen saknar tillgängligt körbevis i provytan. | Ett normalfall med oförändrat recept. Exit 0, rapport med oförändrade källbindningar och fortsatt `not_granted`. | Användbart för avgränsad jämförelse; inga reparationer eller fler prov. |
| Y, metodanvisning | Samma preliminära användbarhet och konkreta osäkerhet. | Självvalt normalfall; exit 0, sparad rapport, bevarade bindningar och fortsatt `not_granted`. | Samma positiva beslut, nu körbelagt; ingen reparation eller utvidgad provning. |

Alla fyra valde själva syntetiska data och relevant kontroll. Inga provkommandon
eller rättelsefacit gavs till utförarna. På X gav körningen en faktisk observation
av konsekvens och felhantering, men **inget ändrat beslut eller unikt tillskott
jämfört med grundarmen**. Den historiska AP05-granskaren hade dessutom redan funnit
felet. Ny metodöverlägsenhet kan inte lånas från den gamla rättelsen.

Kontrastens positiva integritetsutfall gav ingen byggbefogenhet. Tidigare giltiga
AP05-prov för ändrad/saknad källa, separat mandat och bevarande återanvänds med
[exakta bindningar](reused-evidence.json). Originalmaterialet ändrades inte för att
återskapa ett fel. AP06:s felmiljö och X:s anropsfel täcker pilotens andra negativa
frågor. Ingen ny totalgranskning gjordes.

## Exponering och räckvidd

Värden valde historiska fall med kända svar. Granskaren kände också bakgrunden.
Utförarna fick egna frysta inputcommits, prompt, recept, verktyg, vanlig dokumentation
samt metod endast i metodarmarna. Ärvda instruktioner kontrollerades och kopierades.
Ett nativegränsprov avvisade åtkomst till värdens svarspost och skrivning i receptet.
Faktiska läsningar och kommandon bevaras privat. Ingen särskild historisk rättelselista
eller reparationsrapport syns i deras underlag eller körspår.

Dokumentationens gränssnitt och kända syntetiska hash var synliga och fick användas.
Utförarnas allmänna förkunskap och otillgänglig tjänstekontext kan inte uteslutas.
Färsk session betyder därför inte bevisad blindning. Samma modell, fyra utvalda
engångskörningar, ingen randomisering och en gemensam före/efter-instruktion även
till grundarmen begränsar kausala slutsatser.

Gamla körbevis gavs inte till kontrastutförarna; deras normalprov var motiverat av
den lokala evidensluckan. Kontrasten visar att de stannade efter ett fungerande
utfall. Den visar inte att de skulle avstå ett redan täckt prov om gamla bevis
hade funnits tillgängliga. Värden återanvänder dessa gamla bevis i leveransen.

## Extra arbete och tillgängliga mått

Alla armar läste kontrakt, skapade en liten syntetisk fixtur, körde ett receptprov
och bevarade bedömningen. Metodarmarna läste dessutom metodtexten. X-metodarmen
hade två extra läskommandon och en separat förplansfil; samma beslut följde.
Värdens tillkommande arbete omfattade urval, fyra isolerade ytor, input-/instruktions-
bindning, gränsprov, retrospektiv, samordning, riktade granskningar och bevarande.
En verifieringslucka i värdens exempelguard rättades före första Runtime-försöket;
det var tekniskt förarbete, inte bevis för metodens effekt.

Native sessionstid och tokenuppgifter redovisas i [resurskvittot](trial-summary.json).
De inkluderar agentens läsning/skrivning och körmiljöns väntan. Inputtokens kan
räkna samma kontext flera gånger; cached är delmängd, inte ytterligare tokens.
Mänsklig arbetstid, pengar, sparad tid och ägarbelastning är inte uppmätta.
Ingen kausal produktivitets- eller kostnadsskillnad påstås.

| Körning | Sessionsekunder | Inputtokens (varav cached) | Outputtokens | Shellkommandon / receptprov |
|---|---:|---:|---:|---:|
| baseline-x | 86.730 | 112604 (87168) | 4583 | 5 / 1 |
| method-x | 105.623 | 156609 (132736) | 5499 | 7 / 1 |
| baseline-y | 72.911 | 102476 (84480) | 3713 | 6 / 1 |
| method-y | 115.581 | 159249 (126208) | 5420 | 9 / 1 |

Metodarmens observerade extra sessionstid var 18,893 sekunder på X och 42,670 på Y.
Det är en beskrivning av dessa körningar, ingen kausal arbetskostnad. Metodbygget
tog därutöver 103,601 native sessionsekunder och dess artefaktreview 17,160; värdens
och sakgranskarens tid har inget tillförlitligt sammanlagt mått. Alla fyra färska
körningar avslutades normalt, utan omförsök, med bevarade inputbytes och avslutade
registrerade processgrupper.
