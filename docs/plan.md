# Rutin: ingången följer main

Gäller varje session (UNDERHALL-INGANGAR-20260924). Börja med `python3 -B tools/ingang.py`: den hämtar och jämför
ingången med `origin/main` och varnar, men ändrar inget. Avviker ingången läses planen från `origin/main`
(`git show origin/main:docs/plan.md`) och avvikelsen rapporteras. Efter varje skyddad publicering snabbspolas ingången
om den är ren, annars redovisas avvikelsen i leveransbeskedet. Ingen arbetsgren lever bara lokalt: den slutar
publicerad, arkiverad eller kvar med namngivet skäl i planen. Nästa steg står i den gällande posten nedan.

---

# Levande plan — Aquarium v0 i slutprov, Runtime-förbättringen bereds parallellt. AP-10-rättningen levererad och aktiv

TVÅ SPÅR (ARBETA-VIDARE-20260925). Spår A, Aquarium: uthållighetsprovet pågår och skyddas. Fönstret, mätningen och
stoppkontrollen fortsätter utan ingrepp. Den prövade arbetskatalogen (primärutcheckningen) snabbspolas inte och byter
inte gren förrän provet är slut; det är ett namngivet undantag från rutinen ovan. Ingen ny Runtime-release aktiveras,
tjänsten startas inte om och AP-10 ändras inte. Annat arbete som påverkar tolkningen av lastmätningen redovisas i
leveransbeskedet. Ägarprovet väntar på ägaren (ägarens tur nedan), och leveransredovisningen förbereds; leveransen sker
mot den befintliga acceptansen. Spår B, Runtime: förbättringen av granskningens tidsgräns bereds i separat arbetsplats,
med riktad läsning, lösningsberedning och små isolerade, i första hand modellfria förprov, utan anslutning till den
levande motorn eller dess databas och utan implementation eller aktivering. Ett kort, samlat byggbeslut läggs fram för
ägarens accept så snart det är berett. Redovisningen håller spåren isär.

ETAPP 2 BYGGS: FÖNSTRET (inom AQUARIUM-V0-ACCEPT-20260924 och AQUARIUM-V0-ARBETSVARLD-20260924). Arbetsvärlden är
visad med verkliga källor: steg 3 i posten nedan är genomfört med den publicerade koden, sidan prövades färsk och
inaktuell i Chrome och visades för ägaren. Etapp 2 gör vyn till ett fönster som kan stå öppet. En användarägd
läsprocess lyssnar bara på 127.0.0.1 och läser om källorna högst varannan minut, och bara medan sidan är öppen och
frågar efter senaste läsningen; sidan laddar om sig när en ny läsning finns. Aktualiteten felar stängt: sidan blir
inaktuell av sin egen läsnings ålder, inte av att anslutningen bryts, så ett stoppat fönster blir inaktuellt när
senaste läsningen är fem minuter gammal. Jämförelsen (d) görs bara mellan fönstrets två senaste läsningar i minnet:
ett uppdrag som finns i båda med ett annat observerat läge märks "nytt läge", med förra läsningens tid och läge i
fördjupningen. Märket påstår inte när, hur eller av vem läget ändrades och beskriver ingen överlämning; det gäller bara
läsningen efter ändringen och spelas inte om. Vid första läsningen, efter omstart, när motorn inte kunde läsas i någon
av läsningarna eller när de ligger mer än fem minuter isär visas bara aktuellt läge. Ingen händelsemotor, databas eller
historik: fönstret håller två läsningar i minnet och skriver inga filer. Vägen, med en skrivare åt gången:
 1. Mallen (kedjedrivaren): `SCEN` får märket "nytt läge" på varje bänk, på granskningsbordet och på varje kort på
    tavlan, och fönstrets fotrad; båda är dolda tills renderaren sätter deras klass, så ögonblicksbilden ser ut som
    förut. På en bänk och vid granskningsbordet spelas märkets ankomst en gång i det färska läget, aldrig i det
    inaktuella läget eller med minskad rörelse; ett kort på tavlan får märket utan rörelse, eftersom ett vilande
    ärende aldrig animeras.
    Publiceras med denna post efter separat granskning. Genomfört 2026-09-25: första granskningsrundan underkände en
    kvarlämnad mening i modulens beskrivning om att mallen var oförändrad; den rättade mallen godkändes och publicerades
    (PR 49, main `72960eaa`), och ögonblicksbilden är pixel för pixel densamma som förut.
 2. Runtime-uppdrag `office-aquarium-window-1`: `tools/aquarium_fonster.py` (fönstret och jämförelsen), fönsterläget i
    renderaren i `tools/aquarium_vy.py`, prov i `tools/test_aquarium_fonster.py` och avsnittet om fönstret i
    `tools/AQUARIUM.md`, med frusen acceptans på uppdragsgrenen aquarium/uppdrag-fonster enligt arbetsformen nedan.
    Utföraren har bara filverktyg och kan inte köra prov, så beskrivningen namnger de befintliga prov som berörs.
    Runtimes sandlåda tillåter inga uttag, inte heller lokala, så proven driver fönstrets svar utan nätverk, och den
    verkliga porten prövas i steg 3. Granskningsvägen är planerad före start: Runtimes obligatoriska granskning har en
    fast gräns på 180 sekunder, så kedjedrivarens separata slutgranskning och skyddade publicering enligt
    AQUARIUM-V0-SLUTGRANSKNING-20260924 förbereds från början. Genomfört 2026-09-25 (AQUARIUM-V0-FONSTER-20260925):
    `office-aquarium-window-1`:s produkt klarade varje fryst kontroll, men ett av utförarens egna prov föll på ett enda
    påstående; efterföljaren `office-aquarium-window-2`, med samma bas och samma frusna acceptans och en beskrivning som
    namnger fallgroparna, byggdes och prövades av Runtime och klarade acceptansen. Runtimes egen granskning stannade vid
    180 sekunder, och kedjedrivaren slutgranskade separat och integrerade skyddat (PR 50, main `89da2f17`). Båda
    uppdragen står parkerade och återupptas inte.
 3. Kedjedrivaren: fönstret körs med den publicerade koden mot verkliga källor och prövas i Chrome, färskt, inaktuellt
    efter stopp och i helskärm 1920×1080, och visas sedan för ägaren. Fönstret körs från primärutcheckningen, eftersom
    läsningen hittar Runtime som systerkatalog till kontorsrepot. Genomfört 2026-09-25: den öppna sidan var färsk och
    laddades om vid varje ny läsning, 121-132 sekunder isär; när fönstret stoppades blev den inaktuell av sig själv när
    senaste läsningen passerat fem minuter (sett vid första kontrollen efteråt, 315 sekunder efter läsningen); allt utom
    läsning från 127.0.0.1 vägrades (403, 405, 404); inga filer ändrades
    utom motorns egen databas, som den körande motorn skriver ungefär varje minut även utan läsning; vid första
    läsningen och vid nästa sade fördjupningen vad jämförelsen vilade på. Helskärmsbilden 1920×1080 visades för ägaren.
Etapp 3 pågår sedan 2026-09-25: acceptansen i byggbeslutets avsnitt 7 med separat granskning av kod och verklig
tillämpning, mottagarprov, ägarprov (omkring en kvart av ägarens tid), åtta timmars uthållighetsprov och
leveransbesked. Mottagarprovet är klart: en färsk läsare i en separat session såg bara skärmbilder av den verkliga sidan
och svarade utan hjälp rätt på alla fem frågorna, jämfört med källorna. Den separata granskningen av kod och verklig
tillämpning godkände acceptansens punkter 1-8 och 11 utan blockerande fynd. Ägarprovet (punkt 9) står kvar och görs när
ägaren är tillgänglig; mottagarprovet ersätter inte ägarens svar (AQUARIUM-V0-AGARPROV-RATTELSE-20260925). Kvar är
ägarprovet, uthållighetsprovet (punkt 10) och leveransbeskedet. Uthållighetsprovet går i åtta timmar med grafikprocessorn tillåten, sedan ett första
prov visat att Chromes last beror på den: med rörelse omkring 3,6 sekunder processortid per minut med grafikprocessorn
mot 31,7 utan, och 0,9 med minskad rörelse; det första provet med programvarurendering avbröts efter 78 minuter som inte
representativt, och att sidan blir inaktuell när datorn sover är hittills visat bara som ett stoppat fönster. Därefter
leveransbesked och leveranspost. Prognos: leveransen när uthållighetsprovet är klart och ägarprovet gjort. Uppskattningar,
inga gränser.

ARBETSVÄRLDEN BYGGS (AQUARIUM-V0-ARBETSVARLD-20260924). Ägaren såg prototypen och godkände den sammanhängande rumsliga
arbetsvärlden som gestaltningsriktning, med de fyra redovisade tilläggen och två finjusteringar; det är ett godkännande
av riktningen, inte av den ännu ointegrerade implementationen. Tilläggen: (a) projektionen visar den utförare och det
aktuella steg som motorns läsning faktiskt belägger, skilt från konfigurerad bemanning, och okänd identitet visas som
okänd; (b) pågående arbete namnges ur motorläsningen, med korta titlar i scenen och tekniska identiteter i
fördjupningen; (c) för redan identifierade parkerade uppdrag läses bara titeln ur deras namngivna uppdragsfiler, och ett
saknat namn visas som en begränsning; (d) i etapp 2 får två efterföljande läsningar jämföras och ett nytt observerat läge
för samma arbetsobjekt gestaltas, utan att det påstår händelsetid, väg eller överlämning. Finjusteringarna: arbetet
dominerar scenen (maskinrummet och det frostade rummet tonas ned) och PROVDATA märks för hela provläget i stället för på
varje plats. Byggvägen, med en skrivare åt gången:
 1. Scenmall (kedjedrivaren): `SCEN` i `tools/aquarium_vy.py` byts mot arbetsvärlden ur den godkända prototypen med
    finjusteringarna, som statisk mall med platshållare; `SKRIPT` står kvar byte för byte. Separat granskad och skyddat
    publicerad. Genomfört 2026-09-24 med denna post: platser för 16 levererade volymer, 8 kort för uppdrag som inte
    arbetar, 3 bänkar, granskningsbordet, utkiken, 4 brev på ägarens bord, ett nedtonat maskinrum och ett nedtonat
    frostat rum; en figur ritas bara där renderaren markerar arbete som motorläsningen belägger, och en oläst källa
    visas som dimma, inte som tomhet.
 2. Runtime-uppdrag `office-aquarium-scene-2`, efterföljaren till det parkerade `office-aquarium-scene-1`, som står kvar
    parkerat, inte återupptas och vars frysta uppgift inte skrivs om: tilläggen a-c och datumregelns rättning i
    `tools/aquarium.py` och renderaren för arbetsvärlden i `tools/aquarium_vy.py`, med prov och anvisning, frusen
    acceptans och uppdragsgren enligt arbetsformen nedan. Rättelse av en tidigare redovisning: motorläsningen bär
    uppdragets id även för parkerade uppdrag, så deras kort namnges ur den, och uppdragsfilen ger den läsbara titeln
    (tillägg c). Granskningsvägen är planerad före start: kontorsuppdragens
    obligatoriska granskning i Runtime har en fast gräns på 180 sekunder, så kedjedrivarens separata slutgranskning och
    skyddade publicering enligt AQUARIUM-V0-SLUTGRANSKNING-20260924 förbereds från början. Genomfört 2026-09-25
    (AQUARIUM-V0-SCEN-20260925): `office-aquarium-scene-2`:s första försök föll på ett enda befintligt prov som fortfarande
    krävde schema 1, eftersom utföraren bara har filverktyg och inte kan köra proven; efterföljaren `office-aquarium-scene-3`,
    med samma bas och samma frusna acceptans och en beskrivning som namnger de berörda proven, byggdes och prövades av
    Runtime och klarade acceptansen. Runtimes egen granskning stannade vid 180 sekunder, och kedjedrivaren slutgranskade
    separat och integrerade skyddat (PR 47, main `db2d0a29`). Båda uppdragen står parkerade och återupptas inte.
 3. Kedjedrivaren: den publicerade koden körs mot verkliga källor till en privat sida som prövas i Chrome och visas för
    ägaren. Genomfört 2026-09-25: sidan prövades färsk och inaktuell i Chrome och visades för ägaren.
 4. Etapp 2: fönstret på 127.0.0.1 med jämförelsen (d); etapp 3: acceptans, mottagarprov, ägarprov och uthållighet.
    Pågår: posten ETAPP 2 BYGGS ovan.
Prognos, som ersätter den i posten KORRIGERAD GESTALTNING nedan: första användbara integrerade vy uppskattas till omkring
en och en halv arbetsdag efter beskedet, eftersom tilläggen a-c ändrar projektionen och inte bara utseendet; etapp 2 och
3 omkring två arbetsdagar därefter med jämförelsen (d) inräknad, plus ägarprovet och åtta timmars uthållighetsprov. Det
är uppskattningar, inga gränser. Beskedet står ordagrant privat i
`evidence/aquarium/local/owner-words-ja-arbetsvarld-20260924.md`.

KORRIGERAD GESTALTNING (AQUARIUM-V0-GESTALTNING-20260924). Ägaren såg den första verkliga vyn i ägarprovet: den är en
användbar statusvy med illustrerade byggnader och textpaneler, men inte den Aquarium-upplevelse som avsågs med
Gather, Munder Difflin och de andra rumsliga arbetsvärldarna. Dioramat med fem symbolbyggnader byggdes enligt den
senaste avgränsningen och missar ändå upplevelsen; det är en korrigering av riktningen, inte ett underkännande av
dataläsning, prov eller integration. Riktningen nu: ett fönster in i en liten, sammanhängande arbetsvärld, till exempel
ett verkstads- eller kontorsgolv, där arbetet är huvudpersonen: igenkännbara utförare vid begripliga arbetsplatser,
synliga arbetsobjekt, tydlig skillnad mellan arbete, granskning, väntan och leverans, överlämningar bara när underlaget
visar dem, och beständiga platser. En figur har en verklig motsvarighet; en konfigurerad roll blir inte en figur.
Dekorativ rörelse, gestaltning av ett observerat tillstånd och en belagd övergång hålls isär, och en animation är aldrig
en ny faktauppgift. Vyn visar sin täckning: interaktivt arbete som inte observeras varken uppfinns eller göms bakom en
för bred räknare. Miljön ska kunna växa senare med verkliga förmågor och verksamheter, men ingen tillväxtmotor byggs
nu och inga påhittade avdelningar eller framtida arbete visas.

Vägen dit: referenserna Gather, Munder Difflin och Bot Crossing granskas i sina faktiska visuella miljöer, skärmbilder
och demonstrationer, inte bara README-texter; det som inte går att se redovisas i stället för att gissas, och ingen bred
ny inspirationssökning görs. Därifrån hämtas rumslighet, igenkänning, synliga utförare, begripligt arbete och känslan
av en sammanhängande arbetsplats, inte motorer, sociala funktioner, licensierad grafik eller produktomfång. Sedan tas
EN rekommenderad riktning fram som öppningsbar prototyp i tre lägen: verkligt lugnt läge, aktivt förlopp med märkta
PROVDATA och gammalt eller otillgängligt underlag. Provdata blandas aldrig med den verkliga driftvyn, och ingen modell
startas för att skapa aktivitet åt demonstrationen. Beskedet visar prototypen och förklarar kort vad som hämtats från
referenserna, hur världen visar verkligt arbete och vilken avgränsad ändring som behövs jämfört med nuvarande
implementation; ägaren bedömer upplevelsen och tar ställning innan den integrerade vyn ändras mer. Kräver riktningen en
ny datakälla eller ett utökat mandat redovisas den skillnaden innan den genomförs. Genomfört 2026-09-24: referenserna
granskades, prototypen byggdes privat i `evidence/aquarium/local/prototyp-arbetsvarld-20260924/` och visades för ägaren,
och ägaren godkände riktningen med avgränsade tillägg (AQUARIUM-V0-ARBETSVARLD-20260924, posten överst).

Ändras från accepterad v0: scenen (mallen `SCEN`, platsernas form och placering, rubrikens och platsernas texter,
reglerna för figurer och rörelse); undervattenstemat är inte längre bärande. Återanvänds: läsarna och den
visningssäkra projektionen (`tools/aquarium.py`), källbindningar, observationstider, integritetsskydd,
färskhetsprincipen (sidan inaktuell tills skriptet visar en ung läsning) och den lokala driften; dioramat och dess
förhandsvisning bevaras som jämförelsepunkt. Den separata Runtime-förbättringen ligger fortsatt efter Aquarium och är
inget skäl att låta vyn förbli en statisk statuspanel. Prognosen ändras och ersätter prognosen i B nedan (själv ersatt
av prognosen i posten överst, bevarad som historik): första
levererade vyn kommer efter ägarens besked om riktningen, med renderaren för den nya världen och datumregelns rättning
som en koduppgift, uppskattningsvis omkring en arbetsdag efter beskedet om ändringen bara gäller presentationen; en ny
datakälla blir ett eget uppdrag. Hela v0 uppskattas som förut till omkring en till två arbetsdagar därefter, plus
ägarprovet och åtta timmars uthållighetsprov. Det är uppskattningar, inga gränser. Återkopplingen står ordagrant privat
i `evidence/aquarium/local/owner-words-aterkoppling-gestaltning-20260924.md`.

AKTUELLT 2026-09-24, efter ägarbesluten AP10-SIGNAL-OCH-AQUARIUM-BEREDNING-20260924 och AQUARIUM-V0-ACCEPT-20260924,
ägarens återkoppling AQUARIUM-V0-GESTALTNING-20260924 och ägarens ja AQUARIUM-V0-ARBETSVARLD-20260924. AP-11 och
modellvalet är avslutade och återöppnas inte
(historik nedan). Drift nu: aktiv konfiguration `e756fe5b` (runtime `c1cdaf5d`, kontoret `df5ed5dc`), AP-10:s schema
bundet till den och opausat; omgången 2026-09-25 07:00Z slutade otillräcklig (kapacitet), och nästa ordinarie körning
är 2026-09-26 07:00Z. I motorn väntar `office-aquarium-projection-1`,
`-2` och `-3` i `waiting_diagnosis`, `-4` parkerat i `waiting_review` och `office-aquarium-scene-1` parkerat i
`waiting_diagnosis`, `office-aquarium-scene-2` parkerat i `waiting_diagnosis`, `office-aquarium-scene-3` parkerat i
`waiting_review`, `office-aquarium-window-1` parkerat i `waiting_diagnosis` och `office-aquarium-window-2` parkerat i
`waiting_review`; inget av dem återupptas (se B, AQUARIUM-V0-PROJEKTION-20260924, AQUARIUM-V0-GESTALTNING-20260924,
AQUARIUM-V0-SCEN-20260925 och AQUARIUM-V0-FONSTER-20260925).

A. RIKTAD AP-10-RÄTTNING - levererad och aktiv. Det privata steget registrerar nu en
avslutningssignal och avslutar anropet inom den befintliga stoppmodellen, i stället för att gå vidare till sin
tidsgräns (Runtime D031, PR 58): prövat med riktig process och riktig signal genom den berörda vägen, separat granskat
och skyddat integrerat. Stoppförmågan före rättningen räckte för nästa ordinarie omgång, eftersom aktivitetens egen
städning stängde hela processgruppen inom omkring åtta sekunder utan kvarlämnade processer; ingen paus behövdes.
Ägaren aktiverade övergång 15 2026-09-24T13:39Z: konfiguration `e756fe5b` ersätter `145edd45`, runtime `c1cdaf5d`,
kontoret oförändrat `df5ed5dc`, och bara `runtime/private_stage.py` och dess prov ändrades. Återläst 13:40Z: tjänsten
igång med rätt identiteter, AP-10:s schema ombundet och i övrigt oförändrat, AP-10:s kommando oförändrat, AP-11 orört.
Runtime-planens ingång bär detaljerna.

Iakttagelse, inte beställd åtgärd: bevakningens omgångar sedan 2026-09-22 slutar korrekt som otillräckliga, eftersom
leverantören inte tar emot analysens anrop (kapacitet); senast granskade besked är från 2026-09-21. Ingen
modellvalsfråga skrivs för bevakningen: D030 frågar i utvecklingsvägen, inte i bevakningens privata steg. Bevakningens
modellval ändras inte inom detta mandat.

B. AQUARIUM V0 - ACCEPTERAT 2026-09-24 (AQUARIUM-V0-ACCEPT-20260924); ETAPP 1 PÅGÅR, STEG 1-3 KLARA, STEG 4 ERSATT. Byggbeslutet är
[evidence/aquarium/byggbeslut.md](../evidence/aquarium/byggbeslut.md) med sina tre skisser, nu med ägarens preciseringar.

Byggväg, läst ur Runtimes faktiska kontorsprofil (`runtime/task.py` och runbookens AP04-avsnitt): ett kontorsuppdrag
får skriva uttryckligt uppräknade filer under `tools/` (aldrig `tools/kontor.py`), varje anrop får 1-3600 modellsekunder,
inga automatiska omtag, frusen acceptans som värden kör i sin sandlåda, utförare och granskare namngivna i uppdraget,
och uppdragets indata måste ligga committade på den rena ingången innan `tools/kontor.py start`; för v0 läggs de därför
på en namngiven uppdragsgren enligt arbetsformen nedan (AQUARIUM-V0-UPPDRAGSGREN-20260924). Gränsen två filer och 480 sekunder gäller bara AP-11:s ändliga
utvecklingsbindning och tillämpas inte här. Uppdragen namnger Claude (`claude-opus-5`) som utförare och granskare, som
den aktiva konfigurationens utförarval redan gör för alla utvecklingsroller; inget modellval eller utförarval ändras.
Med samma modellfamilj som författare och granskare är granskningen en separat läsning, inte en oberoende bedömning.
Tar en modell inte emot anrop väntar arbetet enligt den befintliga mekanismen (D030 där den gäller), och modell,
utförare eller betalväg byts inte utan ägarens beslut.

Etapp 1, första användbara ögonblicksbild. Läge: steg 1 genomfört 2026-09-24 (varje källa läsbar, privat avläsning); steg 2
publicerat i PR 43 (`tools/aquarium_vy.py` med bara sidan `SCEN` och färskhetsskriptet `SKRIPT`); steg 3
klart: Runtime byggde och prövade kandidaten som `office-aquarium-projection-4` mot den frysta acceptansen, och
kedjedrivaren granskade den separat och integrerade den skyddat (main `cb96867f`, PR 42) enligt
AQUARIUM-V0-SLUTGRANSKNING-20260924, sedan `-1`, `-2` och `-3` fallit på luckor i kedjedrivarens egna indata
(AQUARIUM-V0-PROJEKTION-20260924); steg 4 är ersatt av den korrigerade gestaltningen, och dess uppdrag
`office-aquarium-scene-1` är parkerat och återupptas inte (arbetsformen nedan). Nästa steg står i posten överst.
De ursprungliga stegen:
 1. Källprov (kedjedrivaren, läsande): varje uppräknad källa läses med de tillåtna verktygen och en verklig avläsning
    sparas privat. Skäl till den interaktiva vägen: en Runtime-kandidat arbetar i en klon av kontorsrepot, där de privata
    källorna inte finns (de är ospårade), och byggkandidater arbetar med syntetiska data.
 2. Scenmall (kedjedrivaren): de fem platserna, vattnets ljus och vyns tre lägen ur skisserna som en statisk mall
    under `tools/`. Skäl: formgivningen prövas visuellt i Chrome i korta varv; mallen är formgivning, inte logik.
 3. Runtime-uppdrag: läsning och visningssäker projektion, `tools/aquarium.py` med prov och anvisning, mot syntetiska
    fixturer. Byggbeslutets etapp 0 ingår här: provscenarierna och sanningsreglerna fryses i uppdragets acceptans, som
    granskas separat innan uppdraget startas.
 4. Runtime-uppdrag: återgivning av projektionen i scenmallen, `tools/aquarium_vy.py` med prov. Ersatt 2026-09-24 av den
    korrigerade gestaltningen (AQUARIUM-V0-GESTALTNING-20260924): först prototyp och ägarens besked, sedan en renderare för
    den nya arbetsvärlden tillsammans med datumregelns rättning. Ägarens ja kom 2026-09-24
    (AQUARIUM-V0-ARBETSVARLD-20260924); byggvägen står i posten överst.
 5. Kedjedrivaren: den publicerade koden körs mot verkliga källor till en privat sida som prövas i Chrome och visas för
    ägaren. Skäl: körningen läser privata källor och den visuella kontrollen görs i Chrome, båda utanför en kandidat.
Etapp 2 är fönstret på 127.0.0.1 (ett Runtime-uppdrag), etapp 3 acceptans, mottagarprov, ägarprov, uthållighet och
leveransbesked. Prognos, uppdaterad 2026-09-24 när steg 3 nåtts (ersatt av prognosen i posten överst, bevarad som
historik): steg 3 tog omkring två och en halv timme från frysta indata till
integration, inklusive tre luckor i de egna indata; utförarens del var 12-16 minuter per försök. Första
användbara vy väntas därför när steg 4 är integrerat, sannolikt 2026-09-24 eller 2026-09-25, och hela v0 omkring en
till två arbetsdagar därefter, plus ägarprovet och åtta timmars uthållighetsprov. Ägarens närvaro behövs för
ägarprovet (cirka 15 minuter) och vid en eventuell formgivningsfråga.

Ägarens tur: väntar ett beslut eller en operatörshandling på ägaren skrivs det i denna plan under en egen rad med
blockets rubrik (orden ägarens och tur i versaler, ensamma på raden), som rader `- [beslut] text — sedan ÅÅÅÅ-MM-DD`
eller `- [operatörshandling] text`; Aquarium läser blocket från main. Ett beslut väntar på ägaren: ägarprovet i etapp 3
(byggbeslutets acceptans, punkt 9), där ägarens omdöme avgör och ett nej ger ett formgivningsvarv inom etappen:

ÄGARENS TUR
- [beslut] Ägarprovet: öppna Aquarium-fönstret, svara på de fem frågorna och bedöm om vyn känns lugn och som ett akvarium och inte som en tabell — sedan 2026-09-25


ARBETSFORM FÖR V0:S RUNTIME-UPPDRAG (AQUARIUM-V0-UPPDRAGSGREN-20260924), ett avgränsat undantag från rutinen ovan för
v0:s koduppgifter genom Runtimes kontorsväg; det behöver inte frågas om på nytt för varje deluppgift. Runtimes kontorsväg
kräver att uppdragets indata ligger committade på ingången medan kontorets main står kvar på uppdragets bas fram till
publiceringen. Därför står ingången, bara medan ett accepterat Aquarium-uppdrag pågår, på en namngiven uppdragsgren med
indata ovanpå main och en planpost som säger vilket uppdrag som pågår, varför grenen används och var
återupptagningspunkten finns. Main är ingångens viloläge. När basen är fryst integreras inget annat till kontorets main
- inte heller plan, dokument eller indata - förrän uppdragets publicering är hanterad; löpande läge bokförs genom
befintlig återupptagningsväg (planposten på uppdragsgrenen och kontorets privata återupptagning) utan att den frysta
fjärrbasen flyttas. En skrivare åt gången. Startkontrollens varning står kvar och förklaras av undantaget; den stängs
aldrig av eller kringgås. Uppdragsgren, exakta indata och återupptagningsläge bevaras enligt befintlig bevarandeväg, så
att arbetet kan tas över utan att ägaren minns grennamn eller återberättar uppdraget. Tiden, omkring 1-2 timmar per
uppdrag, är en uppskattning och ingen återställningsgräns: vid avbrott eller kvotbrist bevaras samma arbete, och grenen
byts inte, filer återställs inte och uppdraget startas inte om bara för att tiden gått. Efter verifierad skyddad
integration hanteras publiceringen av uppdragsunderlaget enligt befintlig granskning och sekretessgräns; originalens
identiteter bevaras och acceptansen skrivs aldrig om i efterhand. Därefter återförs ingången till ren main lika med
origin/main utan att uppdragsgren eller bevis går förlorade, och nästa uppdrag utgår från det då aktuella läget.
Uppdrag och grenar i v0: `office-aquarium-projection-1` (läsning och projektion), `-2` (rättad acceptans), `-3`
(förtydligad beskrivning) och `-4` (prövningsmiljön beskriven; byggt och prövat av Runtime, slutgranskat och
integrerat av kedjedrivaren, PR 42), alla på grenen aquarium/uppdrag-projektion. De tre första står i
`waiting_diagnosis`; `-4` står parkerat i `waiting_review` och ska inte återupptas för att publicera samma arbete igen.
Inget av dem återupptas. Grenen står
kvar lokalt med namngivet skäl: dess åtta commits är
uppdragsindatas ursprungliga identiteter, och den integreras inte (indata publicerades byte för byte i PR 43);
den är också arkiverad som git bundle i `evidence/aquarium/local/etapp1/`. `office-aquarium-scene-1` (scenens
renderare för dioramat och datumregelns rättning) kördes på grenen aquarium/uppdrag-scen och står i `waiting_diagnosis`;
det parkerades efter den korrigerade gestaltningen, återupptas inte och publiceras inte. Grenen står kvar lokalt med det
skälet och är arkiverad som git bundle i `evidence/aquarium/local/etapp1/`. Varje senare uppdrag namnges här innan dess
bas fryses, med granskningsvägen planerad före start enligt AQUARIUM-V0-SLUTGRANSKNING-20260924. Genomfört efter
AQUARIUM-V0-ARBETSVARLD-20260924: `office-aquarium-scene-2` (första försöket; ett befintligt prov stod kvar på schema 1)
och `office-aquarium-scene-3` (samma acceptans, preciserad beskrivning; byggt och prövat av Runtime, slutgranskat och
integrerat av kedjedrivaren, PR 47), båda på grenen aquarium/uppdrag-scen-2. `-2` står i `waiting_diagnosis` och `-3`
parkerat i `waiting_review`, och inget av dem återupptas för att publicera samma arbete igen. Grenen står kvar lokalt med
namngivet skäl: dess commits är uppdragsindatas ursprungliga identiteter och övertagandets registrering, och den
integreras inte (indata publicerades byte för byte med denna post); den är också arkiverad som git bundle i
`evidence/aquarium/local/etapp1/`. Det parkerade `office-aquarium-scene-1` och dess gren är orörda. Genomfört i etapp 2
(posten ETAPP 2 BYGGS överst): `office-aquarium-window-1` (första starten vägrades av Runtime innan något skapades,
eftersom den frysta acceptansen översteg Runtimes gräns för indatafiler; efter omstruktureringen byggdes en kandidat vars
produkt klarade varje fryst kontroll medan ett av utförarens egna prov föll på ett enda påstående) och
`office-aquarium-window-2` (samma bas och frusna acceptans, en beskrivning som namnger fallgroparna; byggt och prövat av
Runtime, slutgranskat och integrerat av kedjedrivaren, PR 50), båda på grenen aquarium/uppdrag-fonster. `-1` står i
`waiting_diagnosis` och `-2` parkerat i `waiting_review`, och inget av dem återupptas för att publicera samma arbete
igen. Grenen står kvar lokalt med namngivet skäl: dess commits är uppdragsindatas ursprungliga identiteter, acceptansens
omstrukturering och övertagandets registrering, och den integreras inte (indata publicerades byte för byte med denna
post); den är också arkiverad som git bundle i `evidence/aquarium/local/etapp2/`.

UNDERHÅLL (UNDERHALL-INGANGAR-20260924) - GENOMFÖRT 2026-09-24, efter det samlade beskedet och sedan övergång 15
aktiverats och lästs tillbaka. Mätt läsande: kontorets ingång stod på main; 33 lokala grenar, varav 12 utan kopia på
origin; ingen stash. Unikt innehåll mätt per fil och blob mot mains historik: beslutsunderlagen för AP07, AP08, AP09
och AP11 och de accepterade uppdragsfilerna med frusen acceptans för AP07, AP10 och AP11 var värda att publicera och
är publicerade byte för byte som de låg på grenarna (PR 38); allt annat ligger på main i annan form eller är ersatta planlägen utan
publiceringsvärde. De tolv grenarna finns kvar och är arkiverade som git bundle i
`evidence/entry/local/maintenance-20260924/branches-without-origin-copy-20260924.bundle` (SHA256
`44f5d79bb368c905200841cae2068800b268d8f1c562d2ed3e5effbd71eb9cd9`): aquarium/byggbeslut, aquarium/byggbeslut-r1,
prep/ap10-operativt-bevakningsansvar, work/ap06, work/ap07, work/ap07-preparation, work/ap08, work/ap08-preparation,
work/ap09-preparation, work/ap10-execution, work/ap10-intake-task och work/map-presentation. Kvar med namngivet skäl:
office/aterfunnet-underlag och office/aterfunnet-underlag-r1, den första granskningsrundans commit för det återfunna
underlaget, med samma träd som det publicerade; bara meddelandet rättades. Kvar med namngivet skäl: aquarium/accept och
aquarium/accept-r1, registreringens första granskningsrunda (underkänd för två utelämnade ägarinstruktioner), och
aquarium/arbetsform och aquarium/arbetsform-r1, arbetsformens första granskningsrunda (underkänd för ett försvagat
publiceringsvillkor och en kvarlämnad motsägelse), samt aquarium/arbetsform-r2, ett ogranskat mellanläge av samma rättelse,
bevarade som historik. Kvar med namngivet skäl: aquarium/gestaltning-r1, gestaltningsregistreringens första
granskningsrunda (underkänd för en kvarlämnad nästa-steg-mening om det parkerade uppdraget och en ofullständig
förteckning över motorns väntande uppdrag), bevarad som historik. Kvar med namngivet skäl: aquarium/scenmall-fonster-r1,
fönstermallens första granskningsrunda (underkänd för en kvarlämnad mening om att mallen var oförändrad), bevarad som
historik och arkiverad som git bundle i `evidence/aquarium/local/etapp2/`. Kvar med namngivet skäl: aquarium/etapp3-plan-r1,
etapp 3-planpostens första granskningsrunda (underkänd för ett felräknat intervall mellan två läsningar), bevarad som
historik och arkiverad som git bundle i `evidence/aquarium/local/etapp3/`. Kvar med namngivet skäl: aquarium/agarprov-r1,
ägarprovspostens första granskningsrunda (underkänd för en kvarlämnad mening om att punkterna 9 och 10 återstod), bevarad
som historik och arkiverad som git bundle i `evidence/aquarium/local/etapp3/`. Runtimes del står i
Runtime-planen (dess uppdrag publicerat som Runtime PR 60, dess ingång nu på main). Protokollet står i `AGENTS.md` och
i rutinen överst i denna plan; startkontrollen är `tools/ingang.py`.

VILANDE POSTER, inga åtgärder nu. `office-watch-policy-1` och `office-assignment-cli-1` (DevelopmentTask, vilande sedan
2026-09-20/21) återupptas inte. Före en eventuell fortsättning ska prövas: verkligt behov i dag, gällande mandat,
bevarat läge i motor och bevis, och kompatibilitet med den körrevision de då skulle köra. Tjänstens identitetskörningar
från tidigare konfigurationer (25 vilande vid registreringen) är ett namngivet underhållsärende: deras användning i
bevis, återgång och identitetskontroller kontrolleras innan någon åtgärd föreslås. Ingetdera är förkrav för Aquarium.

ÅTERUPPTAGNINGSPUNKT: denna post, AP10-SIGNAL-OCH-AQUARIUM-BEREDNING-20260924, AQUARIUM-V0-BEREDNING-20260924,
UNDERHALL-INGANGAR-20260924, UNDERHALL-INGANGAR-GENOMFORT-20260924, AQUARIUM-V0-ACCEPT-20260924, AQUARIUM-V0-UPPDRAGSGREN-20260924,
AQUARIUM-V0-SLUTGRANSKNING-20260924, AQUARIUM-V0-PROJEKTION-20260924, AQUARIUM-V0-GESTALTNING-20260924,
AQUARIUM-V0-ARBETSVARLD-20260924, AQUARIUM-V0-SCEN-20260925, AQUARIUM-V0-FONSTER-20260925, AQUARIUM-V0-AGARPROV-20260925,
AQUARIUM-V0-AGARPROV-RATTELSE-20260925, ARBETA-VIDARE-20260925 och Runtime-planens ingång.

---

# Historik 2026-09-24 — AP-11 avslutat; modellvalet (steg 3) levererat och aktivt

AKTUELLT 2026-09-24. Det ändliga åtagandet AP-11 är **godkänt och avslutat**. `office-ap11-assessment-6`, dess enda
räknade granskning (anrop 31, resultatets SHA256 `d63221afc0ab1c3008911b49e48af684d64ca6c636bf188d9f31e5eccc756a77`), godkände hela slutacceptansen G1-G10 utan
blockerande fynd 2026-09-23T22:59Z; Runtime satte scopet `stopped` och skrev `final.json` (SHA256
`925d566df223bce280e23e5b6dbeea7bac71bdf4189f78f2cec02dc89a960926`). 31 av 48 anrop, implementationsförsök 1 av 6 per arbetsdel. Vid avslutet var
aktiv release runtime `2def3667`, kontor `df5ed5dc`, konfiguration `d4f2e63e`; sedan 2026-09-24T07:26Z kör den nya
releasen och sedan 11:51Z dess modellbyte, konfiguration `145edd45` (se AKTIVERAT nedan). AP-10 fortsätter inom sitt
mandat, dagligen 07:00Z.

AP-11 i korthet: A och B integrerades som PR 28 och 29; sex helhetsbedömningar, de fem första inconclusive och bevarade;
G6-demonstrationen bars av den femte och prövades av den sjätte; två fel i Runtime hittades live och rättades (D026 och
D027). Hela beslutskedjan står i beslutsloggen under AP11-BEREDNING till AP11-AVSLUT-20260924; värdens eget
stängningskvitto ligger i Runtime under `.runtime/ap11/claude-path/sixth-assessment-20260924/CLOSURE-READBACK.json`.

MODELLVALET, steg 3 från 2026-09-22 (se MODELLVAL-FORTSÄTTNING-20260924), redovisat skilt från AP-11; AP-11
återöppnas inte. Tillgodoräknat och inte ombyggt: modellvalet i den frysta releasekonfigurationen med vägran i stället
för reserv (D022), identitetskontrollen mot valt modellnamn, kvalificeringen av `claude-opus-5` och Runtimes egen
CLI-kopia (D023). Byggt och integrerat i Runtime 2026-09-24, varje del med separat granskning och skyddad integration:
 1. Codex-startkedjan kopplad till valet: D028, Runtime PR 52. Utan val är varje kommando byte för byte detsamma som
    förut, uppmätt mot den aktiva releasens egen kod.
 2. En enkel befintlig ingång för modellbyte utan källkodsredigering: D029, Runtime PR 53. Verktyget
    `scripts/model_choice.py` (stage, check, activate) körs som den aktiva releasens egen kopia och kan bara ändra
    modellvalet; aktiveringen är ägarens, och den börjar inte utan en väg tillbaka.
 3. En konkret modellvalsfråga till ägaren när vald modell saknar kapacitet: D030, Runtime PR 54. Värden frågar -
    vänta, eller byt modell med verktyget - och växlar aldrig själv; köp och uppgraderingar är aldrig ett val.

AKTIVERAT: ägaren aktiverade Runtime-releasen som bär del 1-3 (övergång 14) 2026-09-24T07:26Z, konfiguration
`416517ae` med runtime `221df157` och kontoret oförändrat `df5ed5dc`. Efterkontrollen fann tjänsten igång, AP-10:s schema
ombundet och i övrigt oförändrat (nästa körning 2026-09-25 07:00Z), AP-10:s kommando oförändrat och AP-11 orört.

Modellbyten görs nu med verktyget, som den aktiva releasens egen kopia (Runtime-runbooken, "Changing the model choice"):
`show` visar valet, `stage` och `check` förbereder och prövar, `activate` är ägarens. Verktygets första verkliga körning
stegade och kontrollerade ett uttryckligt Codex-val av den nuvarande modellen, som inte ändrar vad som körs, och ägaren
aktiverade det 11:51Z: konfiguration `145edd45`, tjänsten igång, AP-10:s schema ombundet och i övrigt oförändrat, AP-11
orört. Bytet har därmed körts i drift. Valet binds vid aktivering: de två vilande utvecklingsuppgifterna
`office-watch-policy-1` och `office-assignment-cli-1` kör den nya koden om de återupptas. Öppna poster utanför steg 3
står i Runtime-planens ingång. Nästa: inget kvar inom steg 3.

Iakttagelse utanför steg 3, inte åtgärdad: AP-10:s privata steg sväljer en avslutningssignal på samma sätt som AP-11:s
väktare gjorde före Runtime D026 (reproducerat 2026-09-24 med den då aktiva releasens egen kod, `2def3667`: anropet gick
vidare till sin tidsgräns; det privata steget är oförändrat i den nya releasen). Det hör till AP-10:s mandat och är
ägarens att avgöra.

Office-sviten är grön igen på main efter PR 30: ett fall i resultatavstämningens prov kunde aldrig falla som det var
skrivet (versaler av en fixtur med bara siffror) och ersattes med ett verkligt versalvärde. Ingen kod under prov ändrades.

ÅTERUPPTAGNINGSPUNKT: denna post och MODELLVAL-FORTSÄTTNING-20260924. Ingen lokal gren behöver kännas till.

---

# Levande plan — AP10 levererad; endast namngiven dygnsdrift fortsätter

2026-09-21. AP10:s fem delmål är verifierade inom [slutredovisningens](../evidence/ap10/leverans.md)
räckvidd. Byggfasen är avslutad. Endast `office-python-temporal` är aktivt,
dagligen 09:00 Europe/Stockholm. [Driftanvisningen](bevakningsansvar-ap10.md)
beskriver privat daterad AP08-läsning, resursgränser, paus, stopp och avregistrering.

NÄSTA HANDLING: nästa ordinarie omgång drivs av det namngivna native schemat.
Ingen ny ägarbeställning behövs för denna bevakning. Behörig mottagare börjar
läsande i evidence/ap10/local/LAS-MIG.md, kontrollerar aktuell native status,
senaste verkliga underlag och granskat besked samt föregående skrivares avslut.
Det privata slutkvittot binder aktiva revisioner, config och bevis. Denna daterade
plan är inte en livegaranti. Tekniskt bortfall hanteras genom bevarad diagnos;
förslag om kod-/beroendeändring är ingen verkställighetsbefogenhet.

AP09:s sakbeslut och bevisluckor, AP07 frivilligt ANPASSA och tidigare auditstatus
består. Ingen annan stående skyldighet eller nästa byggfas aktiveras.

---

# Bevarad tidigare plan — historisk status

# Levande plan — AP10 accepterad, delmål 1–2 pågår

AKTUELLT STEG: AP10-ACCEPT registrerad och bunden till berett/granskat paket.
Root har ensam skrivansvaret i båda namngivna repon. Ingen tjänst eller ny
bevakningsomgång är ännu aktiverad. Grundbevis och AP09-resultat återanvänds.

NÄSTA HANDLING: bind det namngivna åtagandet, lokal/external läslista och
resursram; separat granska den minsta gemensamma Runtime-tjänsten och privata
körvägen. Implementera/verifiera/integrera små delsteg. Därefter kontorskoppling,
verklig schemastart/samexistens/övertagande och samlat driftavslut — inom samma
accept, inga nya rutinmässiga ägarprompter.

ÅTERUPPTAGNING: evidence/ap10/local/LAS-MIG.md, accepted-mandate.md och
acceptance-start.json; work/ap10-runtime-service (Runtime), work/ap10-execution
(kontoret). Kontrollera Git, aktiva kvitton/processer och föregående skrivare.
Driftskonfiguration, nästa kommando och delresultat bevaras här före avbrott.
Fortsätt redan beredda fem delmål; ombered inte från noll.

Delmål: 1 bundet åtagande → 2 kvalificerad Runtime-koppling → 3 kontorets
bevakningskedja → 4 verklig automatisk omgång, avbrott, mottagare och behövligt
AP04-bygge med tjänsten aktiv → 5 separat slutgranskning och just åtagandet i
dygnsdrift. Tekniska delsteg kräver inte ny ägaraccept. AP08 efter väsentliga
resultat är information. Kvarstående osäkerhet är kvalificering, inte nytt mål.

BEVARAT: ingen dependency upgrade, ny extern tjänst/kostnad/modell, valv-/kampanj-/IR-
skrivning eller annan byggfas. AP09:s sakbeslut och graceful-drain-lucka är
oförändrade. AP07 frivilligt ANPASSA; A3/A6/FIND004 och gamla bevis består.
Om slutacceptans inte håller lämnas inte obestyrkt bevakning aktiv.

---

# Historik — AP10-beredning, ersatt av AP10-ACCEPT

AKTUELLT STEG: AP09 tillgodoräknas som levererad enligt slutkvittot. Ägaren har
beställt beredning av nästa sammanhängande operativa förmåga, inte byggstart.
[Det samlade byggbeslutet](../evidence/ap10/byggbeslut.md) föreslår att kontoret
bär ett avgränsat Python-/Temporalbevakningsansvar utan ny beställning per omgång.
Förslagets prioritering och dygnsintervall är härledda rekommendationer.
Ingen sådan drift har ännu accepterats eller startats.

NÄSTA HANDLING: lämna det separat granskade samlade förslaget till ägaren för
ett beslut om utvecklingsmål OCH avgränsad efterföljande drift. Efter uttrycklig
accept registrerar kedjedrivaren dess faktiska identitet och driver de fem
beroende delmålen inom samma fas. Fram till dess: ingen implementation,
intagsomgång, modellkörning, Runtime-ändring, processinstallation eller publicering.

ÅTERUPPTAGNING: gren `prep/ap10-operativt-bevakningsansvar`; börja med
`evidence/ap10/local/LAS-MIG.md`, beredningspaketet och granskningen, kontrollera
Git och faktisk accept före skrivövertagande. Ingen omberedning från noll.
Beredningsunderlagets saknade exekveringsbindningar fylls först vid behörig
teknisk uppdelning efter accept; de är inte nya ägarbeslut per fil.

## Vad kontoret redan kan ta ansvar för

- Etableringen: hitta definition, beslut, aktuellt uppdrag och återupptagningspunkt.
- AP04: köra accepterat utvecklingsuppdrag genom Runtime till granskad skyddad
  integration; status och resultat är rena läsningar.
- AP05/AP06: bedöma valda källor/ändringar och bereda motiverade uppgifter med
  skild källuppgift, bedömning och befogenhet. AP06 bar verkliga beroenden
  kärna→CLI; kedjedrivaren tog tekniska omtag utan nya ägarbeställningar.
- AP08: ge daterad privat leverans-/beslutsbild.
- AP09: göra verkligt officiellt intag, pröva lokal betydelse, överlämna och låta
  nästa utförare faktiskt fortsätta till separat granskat besked.
- Kartleveransen och AP07:s begränsade metodresultat tillgodoräknas inom sina
  räckvidder. De utgör inga återstående huvudprojekt.

Detta är operativ förmåga under ett accepterat, operatörsdrivet mål. Flera
beroende tekniska uppgifter behöver ett sammanhängande mandat, inte en ny
projektmotor. Kontoret har inte därigenom stående obemannat ansvar.

## Vad som återstår för den valda nästa förmågan

Verksamhetsresultat: samma avgränsade bevakningsansvar bärs mellan ägarens
beställningar. Befintlig agent, metoder och verktyg återanvänds. Verkliga
produktluckor: återkommande aktivering i den befintliga Temporal-motorn,
privat läs-/bedömningsuppdrag utan kod-PR, avgränsad profil och kontorets
koppling av källintag/lokal observation till bedömning/beredning/AP08.
Dessa finns inte i läst Runtime2789ea0: den startar/stänger tjänsten per
anrop och dess DevelopmentTask går via kandidat till publicering.

Nya mandatgränser: stående namngivet åtagande, lokal användarprocess med
inloggningsstart, nödvändig Runtime-komplettering och privat uppdragsprofil.
Inget behov av ny kostnad, värd, allmän scheduler, målrepo eller modellanslutning
är visat. RF17/avstängd dator lämnas utanför, och kvotbrist innebär synlig väntan.

## Ett sammanhängande användningsförlopp och fem delmål

Ägaren accepterar målet en gång → (1) kedjedrivaren binder åtagandet till det
verkliga AP09-ärendet → (2) kvalificerar minsta nödvändiga Runtime-väg →
(3) kopplar kontorets befintliga arbetskedja → (4) en senare verklig omgång
startar enligt schema efter avslutad interaktiv session, kontrollerar extern
OCH lokal förändring, hanterar avbrott/övertagande och lämnar granskat sakbesked
→ (5) hela kedjan slutgranskas och lämnas i avtalad, pausbar lokal drift.
Beroenden: 1→2; 1+2→3→4→5. Detaljer, acceptans och tillstånd finns i samma
byggbeslut, inte i en konkurrerande plan.

Under accepterad fas: små relevanta ändringar, separat granskning och skyddad
integration löpande; AP08 efter väsentliga resultat är information. Teknisk
uppdelning, testkommandon, granskarfrågor och rutinomtag bärs av kedjedrivaren.
Endast ändringar av mål, kostnad eller befogenhet återförs till ägaren.

BEVARAT: AP09:s sakbeslut, shutdown-bevislucka och tidigare intag ändras inte.
Ingen ny omgång eller rättning för att få starkare gammal garanti. AP07 är
frivilligt ANPASSA utan belagd förbättring. A3/A6/FIND-004 och tidigare auditstatus
bevaras. Historiken nedan är avslutad och bär ingen aktuell nästa handling.

---

# Historik — AP09 verifierat verksamhetsresultat och kontrollerat avslut

AKTUELLT STEG: båda verkliga intagen, aktuell lokal omobservation och färsk
mottagares faktiska fortsättning är separat sakgranskade utan blockerare.
Befintliga AP05/AP06/AP08 räckte; anvisningen är integrerad genom PR14.
Den granskade avslutsredovisningen integreras skyddat genom samma värdpublicerare.
Fasens slutstatus och faktiskt använda revisioner binds privat i
`evidence/ap09/local/final.json`. Status `verified_delivered` med matchande
revisioner innebär att AP09 är avslutad inom dess redovisade räckvidd.

NÄSTA HANDLING: root verifierar slutkvittot och lämnar den privata slutbilden
`evidence/ap09/local/picture-final/index.html` samt sakbeslutet till ägaren och
stannar. Ingen vidare intagsomgång, modellkörning eller byggfas startas.
Om kvittot saknas/ofullständigt: slutför bara kontrollerat avslut enligt kvarvarande
privata kvitton inom AP09-ACCEPT, återstarta inte den redan genomförda kedjan.

ÅTERUPPTAGNING: `evidence/ap09/local/LAS-MIG.md` leder till mandat, båda intagen,
mottagarens faktiska handlingar, separata granskningar och integrationsbevis.
Kontrollera Git, kvitto och registrerade skrivare före nytt skrivansvar. Root tog
över först efter uttryckligt mottagarstopp. Syntetiska utfall är särredovisade.
Planen ensam äger nästa handling; AP08 är daterad information, inte körstate.

SENARE BESTÄLLD OMGÅNG: en då behörig utförare börjar här och använder
`tools/OMVARLDSARBETE.md`, samma privata ärende och bevarade föregångare. Utför
nytt externt intag OCH lokal kontroll, ompröva konkreta skillnader och använd
AP06 bara vid motiverad åtgärd. Ingen ny rättighet eller stående bevakning följer
av anvisningen. Tekniska kommandon och granskningssamordning bärs av utföraren.

BEVARAT: etablering/AP04–AP08/karta tillgodoräknas. AP07 är frivilligt ANPASSA
utan belagd förbättring; tidigare auditstatus inklusive A3/A6/FIND-004 består.
Ingen installation, Runtime-kodändring, ny kostnad/rättighet eller valvskrivning.
Lokala versions-/användningsuppgifter och råhistorik stannar privat. Historiskt
AP08-avslut nedan bär inte aktuell nästa handling.

---

# Levande plan — AP08 slutleverans

AKTUELLT STEG: presentationskoden är byggd av befintlig Runtime, separat granskad
 och skyddat integrerad genom PR12. Verkligt privat arbetsuttag, källgranskning,
HTML-kontroll och färskt modellbaserat mottagarprov är genomförda. Kontrollerat
avslut och slutbild binds till faktiskt kvitto i `evidence/ap08/local/final.json`.
Kvitto med `status=verified_delivered` och matchande revisioner betyder att AP08
är avslutad inom redovisad räckvidd; den egna HTML-utskriften räcker inte.

NÄSTA HANDLING: kedjedrivaren verifierar det skyddade avslutet och det privata
slutkvittot. När kvittot är verifierat: lämna `evidence/ap08/local/final-view/index.html`
till ägaren och stanna. Ingen ytterligare fas är beställd och inget nytt ägarbeslut
behövs för AP08:s avslut. Ingen uppgift ska återstartas för att en gammal rapport
visar ett dåtida körläge.

ÅTERUPPTAGNING: börja med privat `evidence/ap08/local/LAS-MIG.md`, kvittot och
faktisk Git/Runtime-status innan skrivansvar tas. Avslutsgren `work/ap08-delivery`;
förberedelse, arbetsuttag och hela utförarhistoriken är bevarade privat. Om kvittot
saknas eller inte matchar: slutför endast redovisad kvarstående verifiering inom
AP08, inte ombyggnad eller ny modellkörning. Kontrollera journalerna före omtag.
Källor och tidigare rapporter ersätts inte. Runtime-revisionen för denna fas är
2789ea0770e4234161e9bdb0378a6e3e7b8432d2; faktisk kontorsrevision finns i slutkvittot.

UPPDATERING: en behörig kedjedrivare framställer nästa daterade bild under aktivt
beställt arbete enligt `tools/AGARBILD.md` och privat anvisning. Planen äger nästa
handling, Runtime äger körstate; HTML är en projektion. Ägaren sammanför inga
JSON-filer eller köridentiteter. Öppning är lokal läsning, ingen uppdatering.

BEVARAT: etablering, AP04–AP06 och kartleverans tillgodoräknas. AP06 CLI1 är ersatt
historik och får aldrig återupptas. AP07 är avslutad ANPASSA, enbart frivilligt stöd
vid konkret behov; ingen förbättring är belagd och piloten upprepas inte. A3/A6,
FIND-004 och tidigare auditstatus behåller räckvidd och betydelse. Ingen ny
Runtime-kod, kampanj-/IR-/valvskrivning, tjänst, kostnad eller rättighet ingår.
