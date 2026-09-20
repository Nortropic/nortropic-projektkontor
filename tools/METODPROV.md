# Metodprov: pröva en osäker koppling i liten skala

Detta är en frivillig försökskandidat inom AP07. Metoden är ännu inte bedömd
mot verkliga tillämpningar. Den ger inget belägg för förbättrad produktivitet.
Värden genomför senare falltillämpningar och separat utfallsbedömning. Befintlig
Runtime ansvarar för frysta exempelkontroller, separat granskning och skyddad
integration. Dokumentet inför inget nytt körsystem eller automatiskt godkännande.

## När ett förprov kan hjälpa

Ett litet representativt förprov kan vara användbart när en konkret koppling
innehåller en osäkerhet som kan ändra nästa beslut och få betydande följder.
Läs först det faktiska kontraktet mellan delarna: vad lämnas, vad förväntas och
vilka villkor gäller? Sök och återanvänd befintliga giltiga tester och observationer
för just denna fråga, version och miljö. Dokumentera deras räckvidd.

Avstå från ett nytt prov när befintliga belägg redan besvarar frågan eller när
läsning räcker. En metodetikett motiverar inte extra arbete. Förprovet är ingen
obligatorisk grind, tillitsregel, behörighetsregel, generell revision eller nytt
ramverk. Utföraren väljer försöket utifrån den faktiska situationen och den
kvarstående osäkerheten.

## Kort arbetsrecept

1. **Avgränsa före körning.** Skriv frågan, hypotesen och nuvarande arbetssätt,
   inklusive dess tester. Ange redan tillgängliga belägg och vad de inte avgör.
   Formulera en observerbar förutsägelse och vad som skulle motsäga hypotesen.
2. **Välj minsta representativa uppställning.** Ange exakta indata, kontrakt,
   relevanta versioner och vilka egenskaper hos kopplingen som måste finnas med.
   Beskriv förenklingarna. Skriv vilket beslut observationen kan ändra, beslutet
   före provet samt avgränsning och stoppvillkor. För tidig upptäckt måste det
   nödvändiga provet gå att göra med det som finns nu; en framtida otillgänglig
   produkt får inte vara förutsättning för påståendet.
3. **Pröva och bevara.** Kör inom befintligt mandat i en isolerad uppställning.
   Bevara faktiska observationer, även uteblivna, negativa och tvetydiga resultat.
   Skilj observerat beteende från tolkningen av det. Anteckna avvikelser från
   förhandsplanen utan att skriva om den i efterhand.
4. **Bedöm vad resultatet bär.** Jämför förutsägelse och observation och skilj
   mellan fel i provobjektet, fel i försöksuppställningen och otillräcklig
   observation. Ange beslutet efter provet, skälen och vad som förblir okänt.
5. **Välj fortsättning och stanna.** Anta, anpassa eller avstå från metoden i den
   aktuella situationen; alla tre är giltiga utfall. Redovisa merarbetet jämfört
   med nuvarande arbetssätt och om provet faktiskt ändrade eller underbyggde
   beslutet. Avsluta när stoppvillkoret nås. En ny fråga blir ett uttryckligt
   nytt ställningstagande inom gällande uppdrag.

## Försöksmiljö och resultat som inte ger ett klart svar

Använd syntetiska exempel när de kan återge den relevanta egenskapen utan
originalmaterial. Beskriv varför exemplet är representativt och vad det lämnar
utanför. Original bevaras orörda. Tidigare evidens är oföränderlig: en rättelse
eller ett nytt försök blir en ny, hänvisande anteckning, aldrig en överskrivning.
Bevara exakta provindata och resultat i redan tillåten hemvist; privata källor
och råhistorik hör inte hemma i publik metodredovisning.

Ett avvikande resultat visar inte ensamt var felet ligger. Ett fel i provobjektet
kräver stöd för att en tillämplig förväntan faktiskt bröts. Ett fel i uppställningen
kan innebära att fel villkor prövades; då avgör försöket inte objektets beteende
under avsedda villkor. Saknas avgörande observation ska slutsatsen vara
otillräckligt underlag. Vid oklar orsak bevaras osäkerheten.

Avbryt hängande försök och dokumentera vad som hann observeras. Gör inga blinda
omkörningar och utvidga inte urval eller tolkning tills resultatet blir positivt.
Ett motiverat nytt försök behöver en angiven ändring, förväntad ny information
och egen stoppgräns. Samma återkommande fel utan ny grund avslutar försöket.
Ett gott utfall inom avgränsningen ska inte skapa onödiga reparationer eller extra
granskningar. Redan gällande krav på separat granskning kvarstår.

## Bedöm nyttan utan att tillskriva metoden för mycket

Bevara i en kort försöksanteckning: förhandsplanen ovan, exakta indata och använd
exempelversion, faktiskt kommando och körmiljö, observationer, beslut före och
efter, kvarstående osäkerhet och tillkommande arbete. Ange tillgänglig faktisk
förfluten tid och resursanvändning från körsystemets egna uppgifter. Saknas en
uppgift markeras den som saknad; rekonstruera inte mätvärden ur minnet.

Jämförelsen gäller nuvarande arbetsform, som själv kan använda läsning och tester.
Ange vad den faktiskt gjorde eller skulle ha gjort enligt en i förväg bevarad
plan. Skilj observerad jämförelse från ett antagande om alternativt förlopp.
Redovisa även dubbelarbete och ett oförändrat beslut. En lyckad körning visar
inte tidsvinst, lägre kostnad eller minskad ägarbelastning; sådana påståenden
kräver stöd från en relevant jämförelse med redovisade begränsningar.

En färsk session är inte automatiskt en blindad utvärdering. Redovisa vilken
förkunskap utförare och bedömare hade, om de sett förväntat svar eller tidigare
utfall och hur fallet valdes. Bevara exakt vilket underlag var och en fick och
när svaret blev känt. Ett historiskt, utvalt fall kan belysa en tillämpning men
bevisar inte allmän effektivitet. Ett konstruerat exempel med känt svar är en
demonstration, inte ett blindat effektprov.

Metodnamn, ifyllda fält, lyckad exekvering och hashvärden bevisar varken nyttig
metodeffekt, källsanning, fullständig täckning eller befogenhet. AP05 kan binda
valda källor och bedömningar; AP06 kan bära beredningen av ett efterföljande
uppdrag. De avgör inte sakfrågan eller ger nya tillstånd. Separat granskare
behöver bedöma resonemangets tillräcklighet, gränser och eventuellt vilseledande
effekter i både text och exempel, inte bara kontrollera att fält finns.

## Fristående syntetisk demonstration

Fråga: bevarar en föreslagen omvandling massan när en syntetisk avsändare anger
gram och mottagaren förväntar kilogram? Hela kontraktet för exemplet är att
1 kilogram motsvarar 1000 gram och att decimalvärden får användas. Hypotesen är
att division med 1000 ger de fyra förväntade mottagarvärdena nedan. Varje avvikelse
skulle motsäga hypotesen för det aktuella värdet.

Nuvarande arbetssätt är att läsa enhetskontraktet och återanvända giltiga
omvandlingstester. I denna konstruerade situation finns inga tidigare körbevis.
Beslutet före provet är att föreslå faktorn 1/1000 utifrån kontraktet. Just detta
enkla samband går också att avgöra genom läsning: körningen visas för att göra
arbetsreceptet konkret, inte för att kräva ett förprov här.

Minsta uppställningen är fyra syntetiska värden, en omvandlingsfunktion och
oberoende angivna förväntningar från kontraktet. Noll, ett delvärde, en hel enhet
och ett större värde ingår. Beslutet som kan ändras är valet av omvandlingsfaktor
för dessa exempel. Stoppgränsen är en körning av de fyra fallen; inga automatiska
omförsök eller utökningar. Uppställningen finns i sin helhet nu och kräver ingen
framtida produkt. Författaren känner svaret och har valt värdena: ingen blindning
eller faktisk verksamhetsjämförelse påstås.

Kör kodblocket med Python 3.12 utan optimeringsflaggan som stänger av assertions.
Det använder bara standardbiblioteket, behöver inga filer, nätverk, modeller eller
paket, skriver inga filer och skriver ut exakt ett JSON-objekt. Vid en bruten
numerisk förväntan avbryter en assertion innan något beslut skrivs ut.

```python
import json
from decimal import Decimal


def till_kilogram(gram):
    return gram / Decimal("1000")


fall = (
    ("0", "0"),
    ("250", "0.25"),
    ("1000", "1"),
    ("2500", "2.5"),
)
observationer = []
for gram_text, vantat_text in fall:
    faktiskt = till_kilogram(Decimal(gram_text))
    vantat = Decimal(vantat_text)
    assert faktiskt == vantat, (gram_text, faktiskt, vantat)
    observationer.append(f"{gram_text} g gav {faktiskt} kg")

print(json.dumps({
    "hypothesis": "Division med 1000 ger avtalade kilogram för de valda gramvärdena.",
    "observation": "; ".join(observationer),
    "decision": "Behåll föreslagen faktor för dessa exempel; ingen reparation motiveras.",
    "limitation": "Känt syntetiskt svar; visar inte en verklig koppling eller metodens nytta.",
}, ensure_ascii=False))
```

Om assertions håller stöder observationen faktorn för dessa fyra värden.
Beslutet efter provet är då oförändrat men har ett körbelägg inom denna gräns.
Merarbetet består av att formulera fallen, köra och bedöma dem utöver läsningen;
ingen besparing är mätt. Ingen produkt, avrundningspolicy eller övriga värden
har prövats. JSON-utskriften är en försöksanteckning, inte ett godkännandeverktyg.

## Begränsat metodstöd och avslut

Två primärkällor ger stöd för uppläggets idéer:

- [IHI: Plan-Do-Study-Act (PDSA) Worksheet](https://www.ihi.org/library/tools/plan-do-study-act-pdsa-worksheet)
  beskriver att planera en förändringsprövning, prova, observera och lära samt
  besluta om justeringar och bevara anteckningar mellan försök. Ursprungskontexten
  är förbättringsarbete i hälso- och sjukvård. Här används endast dessa idéer;
  inget fullständigt ramverk införs.
- [GOV.UK: How the alpha phase works](https://www.gov.uk/service-manual/agile-delivery/how-the-alpha-phase-works)
  beskriver minimala prototyper riktade mot riskfyllda antaganden som underlag
  för fortsatt vägval; hela användarresan behöver inte byggas. Kontexten är
  utformning av offentlig service. Här lånas avgränsningsprincipen, inte hela
  alfa-fasen, dess tidsnormer eller organisationskrav.

Källbeskrivningarna bygger på värdens lästa och granskade sammanfattningar i
uppdraget. För IHI avser läsningen förklaringssidan; ingen nedladdad arbetsmall
eller läsning av ett fullständigt ramverk påstås. Dessa källor motiverar ett
försöksupplägg men bevisar inte effekten av vår ännu omätta tillämpning.

Tillräckligt resultat är ett underbyggt svar på det avgränsade nästa beslutet,
eller ett tydligt besked om varför underlaget inte räcker. Bevara observation,
osäkerhet och beslut och stanna där. Gällande befogenheter, separat granskning
och skyddad integration består; metoden ger aldrig utföraren ett utvidgat uppdrag.
