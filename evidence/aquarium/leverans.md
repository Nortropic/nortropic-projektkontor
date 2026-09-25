# Aquarium v0 — kontorets lugna fönster

Aquarium v0 är en läsvy över kontorets arbetsvärld: ett sammanhängande verkstadsgolv sett ovanifrån, med arkivet för det
som är levererat, verkstaden och granskningsbordet för det som arbetar, utkiken för bevakningen, ägarens bord för det som
behöver ägaren och ett nedtonat maskinrum. Arbetet är huvudpersonen: en figur ritas bara där motorns läsning belägger
arbetet, konfigurerad bemanning blir aldrig observerat arbete, och en källa som inte gick att läsa visas som dimma, inte
som tomhet. Vyn läser; den startar, godkänner, byter och ändrar ingenting.

Levererat i kontorsrepot: `tools/aquarium.py` (läsning och visningssäker projektion), `tools/aquarium_vy.py` (sidan och
ögonblicksbilden), `tools/aquarium_fonster.py` (fönstret på 127.0.0.1 med jämförelsen mellan två läsningar), proven
`tools/test_aquarium*.py` och anvisningen `tools/AQUARIUM.md`. Fönstret öppnas med `python3 -B tools/aquarium_fonster.py`
från kontorsrepots primärutcheckning och sidan på http://127.0.0.1:8741/ i Chrome, i helskärm och vid behov speglad till
tv:n; det stoppas med Ctrl-C. Fönstret läser om källorna högst varannan minut och bara medan en sida är öppen, håller den
senaste läsningen i minnet och skriver inga filer. Ögonblicksbilden görs med `tools/aquarium.py` och `tools/aquarium_vy.py`.

## Provdata och verkliga observationer

Publikt är kod, prov, anvisning och syntetiska scenarier. Varje syntetiskt scenario och varje sida gjord av ett sådant bär
märket PROVDATA, en gång för hela sidan; en verklig läsning är aldrig provdata, och fönstret jämför aldrig två läsningar
som skiljer sig i det. Allt verkligt — läsningar, sidor, skärmbilder, mottagarprovet och ägarens svar — ligger privat i
`evidence/aquarium/local/` och publiceras inte. Siffrorna nedan är mätningar av verkliga körningar, inte innehållet i
verkliga sidor.

## Acceptansen

Byggbeslutets acceptans (`evidence/aquarium/byggbeslut.md`, avsnitt 7), prövad 2026-09-25 mot den publicerade koden:

1. Spårbarhet — uppfylld: varje visad uppgift har källa och lästid, och en separat granskare jämförde den verkliga vyns
   huvuduppgifter med de bevarade källorna utan att finna någon osann uppgift.
2. Klassning — uppfylld: frusna acceptanser med fasta scenarier för varje byggd del.
3. Tid — uppfylld: en gammal ögonblicksbild som öppnas senare ser inaktuell ut; en öppen sida vars fönster stoppats blev
   inaktuell när senaste läsningen passerat fem minuter (sett vid första kontrollen efteråt, 315 sekunder efter
   läsningen); utan skript är sidan inaktuell; lästider visas aldrig som sidans skapelsetid.
4. Luckor — uppfylld: en verklig läsning där alla Runtime-källor var oläsbara visades som dimma med "läget är okänt, inte
   tomt", och huvudraden sade att det var okänt om något väntade på ägaren.
5. Provdata — uppfylld.
6. Läsande — uppfylld: inga formulär eller knappar; fönstret svarade bara på läsförfrågningar från 127.0.0.1 med rätt
   värdnamn (annat fick 403, 405 eller 404); under en körning ändrades inga filer utom motorns egen databas, som den
   körande motorn skriver ungefär varje minut även utan läsning.
7. Integritet — uppfylld: den visningssäkra projektionen bär inga sökvägar, promptar, råhändelser eller nycklar, och de
   publika filerna bär bara provdata, med ett redan redovisat undantag (nedan).
8. Mottagarprov — uppfyllt: en färsk läsare i en separat session såg bara skärmbilder av den verkliga sidan och svarade
   utan hjälp rätt på alla fem frågorna, jämfört med källorna.
9. Ägarprov — godkänt (AQUARIUM-V0-AGARPROV-GODKANT-20260925): ägaren bedömde att vyn känns lugn och att den verkar
   bra, och förklarade ägarprovet godkänt; ägarens omdöme avgör. De fem frågorna besvarade ägaren inte var för sig, om
   vyn känns som ett akvarium och inte som en tabell uttalade sig ägaren inte särskilt om, och svaret säger inte om ägaren
   såg det levande fönstret eller en bild av det.
10. Uthållighet — uppfylld för öppethållning och aktualitet; lasten redovisas med siffror nedan. Sidan stod öppen i
    huvudlös Chrome med grafikprocessorn och en vy på 1920×1080 i åtta timmar, 09:05:51-17:05:59Z den 25 september. Alla
    96 kontroller, en var femte minut, visade en färsk sida, den senaste läsningen var som mest 121 sekunder gammal och fönsterprocessen
    levde hela tiden. Chromes minne låg mellan omkring 190 och 540 MB och var lägre vid slutet än vid början. När
    fönstret stoppades blev den öppna sidan inaktuell efter 210 sekunder, när senaste läsningen hade passerat fem
    minuter. Att sidan blir inaktuell när datorn sover är inte prövat genom en verklig sömn (nedan).
11. Tv-avstånd — i helskärm 1920×1080 är huvudraden och platsrubrikerna tydliga; den mindre texten under rubrikerna och
    namnen på korten är små på tre meters avstånd.

## Last

Fönsterprocessen använder omkring 0,05 sekunder processortid per minut, och en läsning omkring 0,8 sekunder. Chromes last
för den öppna sidan beror på grafikprocessorn: med rörelse och grafikprocessor i snitt 7,2 sekunder processortid per minut under
de åtta timmarna (5,8-8,7 per timme), 31,7 sekunder per minut utan grafikprocessor och 0,9 med minskad rörelse. Ett
tidigare kort prov med grafikprocessor gav 3,6; skillnaden mot de åtta timmarna är inte förklarad. Faller Chrome tillbaka till programvarurendering blir sidan dyr; inställningen minskad
rörelse är då den billiga vägen.

## Samtidigt arbete under uthållighetsprovet

Kedjedrivaren arbetade på samma dator medan provet pågick, och de intervallen kallas inte ostörda. Tyngst var Runtimes
provsvit (543-550 prov, knappt en minut per körning), som kördes omkring femton gånger mellan 13:04 och 14:08Z, och
kontorets provsvit (omkring 13 sekunder per körning) vid varje publicering. Därtill kom läsande granskningar, som mest
väntar på modellsvar, felinjiceringsvarv och uppspelningar av bevarade historiker utan motor. Två korta
skärmbildstillfällen 09:07-09:09Z lät en andra Chrome läsa samma fönster, och ägaren kan ha öppnat fönstret som en
andra läsare under ägarprovet, vid en tid som inte är känd. Nio publiceringar ändrade det observerade
kontoret, som fönstret är byggt att visa. Den prövade arbetskatalogen snabbspolades två gånger före 09:52Z, bara i
`docs/`, och stod sedan stilla till provets slut. Aktualiteten påverkades inte, eftersom alla kontroller var färska.
Chromes processortid per timme var som lägst (5,8 sekunder per minut) i timmen med mest samtidig last. Mätningen skiljer
alltså inte ut någon påverkan av det samtidiga arbetet, men utesluter den inte heller. Loggen står privat i `evidence/aquarium/local/etapp3/samtidigt-arbete-uthallighet-2.md`.

## Öppna punkter och gränser

- Att sidan blir inaktuell när datorn sover är visat bara genom ett stoppat fönster, inte genom en verklig sömn.
- Den mindre texten (lägesraderna och kortens namn) är liten på tv-avstånd.
- Arkivet visar AP10 som odaterad: det tar leveransposten i beslutsloggen, som saknar datum, fast leveransbeskedet har ett.
  Bristen är inte rättad i v0. Den rättas i ett eget uppdrag, `office-aquarium-arkivdatum-1`, som också är
  användningsprovet för Runtimes granskningstid (RUNTIME-GRANSKNINGSBUDGET-ACCEPT-20260925).
- Ett verkligt körnings-id från bevakningen står som provvärde i de tidigare publicerade `acceptance/aquarium.py` och
  `acceptance/aquarium_2.py`; det röjer inget innehåll, redovisades i AQUARIUM-V0-SCEN-20260925 och skrivs inte om.
- Byggbeslutets avsnitt 1 beskriver den tidigare dioramariktningen; den levererade gestaltningen följer
  AQUARIUM-V0-GESTALTNING-20260924 och AQUARIUM-V0-ARBETSVARLD-20260924.
- Författare, granskare och mottagare är samma modellfamilj: separata läsningar, inte oberoende bedömningar.
- Interaktivt arbete observeras inte och visas därför inte; vyns räkning gäller bara det som observeras i Runtime.

Uttryckligen utanför v0, som i byggbeslutet: händelseström och återspelning, lager och lägen, åtkomst från andra enheter,
start vid inloggning, historik och trender, handlingar från vyn och ett eget Aquarium-repo. Ett nytt bygge behöver ett
eget accepterat uppdrag.

## Slutbindning

Den prövade och levererade koden är Aquarium-filerna på kontorets main. De ändrades senast i PR 50 (`89da2f17`) och är
oförändrade sedan dess (sha256):
- `tools/aquarium.py` `49bbcd7b7eb74ce1df73590211a768ab97cb004347893ea2f6c761a1961cdddf`
- `tools/aquarium_vy.py` `fdbe4e485a739537e1103205afcea8fa667e8850dbbb0a5375573e22c1ca4c74`
- `tools/aquarium_fonster.py` `15864495afcdc2110373be4dc16d5fc79c880142029769c0c3149ba6f2b671f3`
- `tools/AQUARIUM.md` `ae6c03f0fef86ed1ffaa070be8a3bf864d53ff1058fd3f87e2bff821d0bc0339`
- `tools/test_aquarium.py` `2823e3fc14959a1dc98a0f9070fe78190f3ea64a512b0e11c2c07fbdcf5da657`
- `tools/test_aquarium_vy.py` `ddc96a272455dcfdf02e7ab078d6eaa52218b8eee6b1bf2a608b0a1fe71ce5e7`
- `tools/test_aquarium_fonster.py` `a0a28ed2369d682ec454c988e0b26557a563e669dd62e96654c2cd54d8890cd7`

Uthållighetsprovet körde fönstret från primärutcheckningen på `fccf32e9`, med samma filer. Leveransen själv lägger bara
till detta besked, en post i beslutsloggen och planens läge. Bevisen står privat i `evidence/aquarium/local/`.
