# Privat ägarbild

`agarbild.py` skapar en fristående svensk HTML-läsrapport av ett uttryckligt,
källbundet underlag som värden redan har bedömt. Rapporten visar användning och
begränsningar, leverans och aktuell tillgänglighet var för sig, observerat arbete,
nästa motiverade handling samt den tillförda bedömningen av ägarens beslutsbehov.
Den är en daterad projektion, inte en livebild eller en källa till nya befogenheter.

```sh
python3 -B tools/agarbild.py INPUT.json NEW.html
python3 -B -m unittest discover -s tools -p test_agarbild.py
```

Endast Python-standardbiblioteket behövs (Python 3.11 eller senare). Om datorns
`python3` är en Xcode-stub, använd en redan installerad Python, exempelvis
`/opt/homebrew/bin/python3.12`. Testerna använder tillfälliga syntetiska filer i
repots befintliga `.scratch`; inga privata källor behövs.

`render(data) -> str` validerar ett Python-objekt och returnerar HTML utan IO,
klockläsning eller ändring av objektet. Fel ger `ValidationError`, en `ValueError`,
utan återgivning av privata värden. CLI läser UTF-8-JSON, avvisar dubbla nycklar
även i nästlade objekt samt NaN/Infinity, och validerar hela rapporten innan någon
utfil skapas. Framgång ger exitkod 0 utan utskrift. Fel ger exitkod 2 och endast:

```text
Kunde inte skapa ägarbilden. Kontrollera underlag och nya lokala filsökvägar.
```

Indata måste vara en vanlig fil. Utdata måste vara en **ny** vanlig fil;
välj filändelsen `.html` så att den enkelt kan öppnas som HTML.
CLI skapar den med exklusiv `O_EXCL`/`O_NOFOLLOW` och rättigheter `0600`.
Alla föräldrakataloger måste redan finnas. Symlänkar avvisas i båda sökvägarna,
även i föräldrar och före `..`. Befintlig utfil, katalog, FIFO, symlänk eller
alias till indatan avvisas; även hårda länkar till indatan är befintliga filer.
Indata och tidigare utgåvor skrivs aldrig över. Läsning kan påverka filsystemets
åtkomsttid. Utfilen ska förvaras på en betrodd lokal plats. Kontrollerna är inte
en garanti mot en angripare som samtidigt byter föräldrakataloger eller ändrar
indata. Ett skrivfel kan lämna en ofullständig ny fil med privata rättigheter;
använd en annan ny sökväg efter diagnos och betrakta aldrig en felkörning som leverans.

Öppna en lyckad utfil direkt som lokal fil i webbläsaren. Ingen server behövs.
HTML innehåller inga skript, formulär, externa resurser, fjärrlänkar, refresh,
inbäddade ramar eller körkontroller. Typsnitt kommer från datorn. Inline-CSS
saknar `url()` och `@import`. CSP är `default-src 'none'; style-src 'unsafe-inline';
base-uri 'none'; form-action 'none'`. Länkar går enbart till rapportens egna
underlagsdetaljer. Källplatser återges som escapad text; programmet följer dem
aldrig. Även text som ser ut som en URL, HTML eller ett kommando förblir text.
Att öppna rapporten gör inget arbete och läser inga källor.

## Exakt schema 1

Alla nedanstående nycklar krävs, på samtliga nivåer; inga extra nycklar tillåts.
Notationens `text`, datum och ID ska ersättas med värden. JSON-exemplet i nästa
avsnitt kan användas direkt som syntetisk indata.

```text
{
  "schema": 1,
  "generated_at": "timezone-aware ISO8601",
  "title": "text",
  "summary": "text",
  "scope": "text",
  "capabilities": [{
    "title": "text", "use": "text", "limits": "text",
    "delivery": "text", "availability": "text", "evidence": ["e1"]
  }],
  "work": [{
    "title": "text",
    "state": "accepted|running|waiting|finished|superseded|unknown|proposed",
    "text": "text", "observed_at": "aware ISO8601 or null", "evidence": ["e1"]
  }],
  "next_action": {
    "text": "text", "owner": "text",
    "authority": "accepted|proposed|none|unknown", "evidence": ["e1"]
  },
  "owner_decision": {
    "needed": "yes|no|unknown", "question": "text", "reason": "text",
    "evidence": ["e1"]
  },
  "issues": [{"text": "text", "evidence": ["e1"]}],
  "evidence": [{
    "id": "ASCII alnum/hyphen ID", "title": "text", "kind": "text",
    "observed_at": "aware ISO8601 or null", "revision": "text", "locator": "text",
    "sha256": "64 lowercase hex or null", "text": "text"
  }]
}
```

- `schema` är strikt heltalet `1`, inte bool eller flyttalet `1.0`.
- All text är icke-tomma UTF-8-kompatibla strängar. Enbart blanktecken räcker
  inte. Textens betydelse verifieras inte. Även vid `needed: "no"` krävs både
  `question` och `reason`, exempelvis ”Ingen fråga i detta underlag”.
- `capabilities`, `work` och `issues` får vara tomma listor. `evidence` måste
  innehålla minst ett objekt. Varje referenslista `evidence` måste vara icke-tom,
  ha unika strängar och hänvisa till befintliga unika underlags-ID:n.
- Underlags-ID följer `[A-Za-z0-9-]+`. `sha256` är `null` eller exakt 64 små
  hextecken. Hashar återges utan beräkning, uppdatering eller autenticitetspåstående.
- Datum ska vara verkliga ISO8601-kalenderdatum med klockslag och explicit
  tidszon, exempelvis `2026-09-20T18:00:00+02:00` eller `2026-09-20T16:00Z`.
  Kompakt datum/klockslag stöds också. Sekunder kan ha decimalpunkt eller
  decimalkomma; all tillförd precision bevaras i tidsjämförelsen. Tidszon är
  `Z` eller en offset `±HH:MM`, `±HHMM` eller `±HH`. Ogiltiga datum och
  offsetkomponenter avvisas. Ingen lokal tidszon antas.
- `generated_at` måste finnas och visas som **Framställd**. Varje `observed_at`
  är ett datum enligt ovan eller JSON `null`. Observationer efter
  `generated_at` avvisas, även över tidszonsgränser. Käll- och arbetstider visas
  som **Observerad**, med ålder räknad vid framställning. `null` visas uttryckligen
  som saknad observation med okänd ålder; det betyder inte att inget pågår.

Arbetsobservationer visas nyast först, följda av de utan tid. Ersatt arbete
(`superseded`) placeras separat i historiken och räknas inte som aktivt eller
som ägarhinder. Ingen aktivräkning eller trafikljusklassning görs. Tekniska
väntelägen bestämmer aldrig `owner_decision`. `proposed` är uttryckligen inte
accepterat. `accepted` återger en tillförd uppgift, utan att autentisera mandatet.

`issues` visas öppet. Renderaren söker inte efter semantiska motsägelser och
väljer aldrig den mest positiva av flera källuppgifter. Alla tillförda källor
finns kvar i native `details`/`summary`, även underlag som inte refererats.
Identifierare, revisioner, källplatser och hashvärden visas där. Värden ska skriva
begripliga huvudrubriker och lägga tekniska kvitton i underlagen; renderaren kan
inte känna igen privata eller tekniska uppgifter som placerats i fritext.

## Körbart syntetiskt exempel

Samtliga sakuppgifter här är påhittade. Spara JSON som en privat lokal indatafil
och välj ett nytt HTML-filnamn vid varje framställning.

```json
{
  "schema": 1,
  "generated_at": "2026-09-20T18:00:00+02:00",
  "title": "Kontoret · syntetisk ägarbild",
  "summary": "Uppdrag kan beredas lokalt. Tillgängligheten behöver följas upp inom det angivna uppdraget.",
  "scope": "Enbart syntetiska uppgifter för prov av läsytan.",
  "capabilities": [{
    "title": "Bered ett avgränsat uppdrag",
    "use": "Samla bedömda krav med spårbara hänvisningar.",
    "limits": "Utkastet kräver sakgranskning och ger inget nytt mandat.",
    "delivery": "En tidigare version är levererad enligt det syntetiska kvittot.",
    "availability": "Åtkomsten är okänd i det senare underlaget.",
    "evidence": ["e1", "e2"]
  }],
  "work": [{
    "title": "Jämförelse av tillgänglighet",
    "state": "waiting",
    "text": "Teknisk väntan på separat jämförelse; ingen ägarfråga följer av väntan.",
    "observed_at": "2026-09-20T15:00:00Z",
    "evidence": ["e2"]
  }, {
    "title": "Äldre ersatt väntan",
    "state": "superseded",
    "text": "Det tidigare försöket är ersatt och ska inte återupptas.",
    "observed_at": "2026-08-01T12:00:00Z",
    "evidence": ["e1"]
  }],
  "next_action": {
    "text": "Jämför observationerna med det bevarade kvittot.",
    "owner": "Kedjedrivaren",
    "authority": "accepted",
    "evidence": ["e1", "e2"]
  },
  "owner_decision": {
    "needed": "no",
    "question": "Ingen ägarfråga i detta syntetiska underlag.",
    "reason": "Den tekniska jämförelsen ryms inom det angivna uppdraget.",
    "evidence": ["e2"]
  },
  "issues": [{
    "text": "Tidigare kvitto anger åtkomst; senare bedömning kan inte bekräfta den. Observationstid saknas för den senare källuppgiften.",
    "evidence": ["e1", "e2"]
  }],
  "evidence": [{
    "id": "e1",
    "title": "Tidigare syntetiskt kvitto",
    "kind": "Leveranskvitto",
    "observed_at": "2026-08-01T12:00:00Z",
    "revision": "syntetisk-version-1",
    "locator": "syntetiskt/kvitto.json",
    "sha256": null,
    "text": "Leverans och åtkomst observerades vid det äldre tillfället. Hash har inte tillförts."
  }, {
    "id": "e2",
    "title": "Senare syntetisk bedömning",
    "kind": "Bedömning",
    "observed_at": null,
    "revision": "syntetisk-version-2",
    "locator": "syntetiskt/bedomning.txt",
    "sha256": null,
    "text": "Tillgängligheten kan inte bekräftas. Den saknade observationstiden begränsar slutsatsen."
  }]
}
```

## Värdens privata uppdatering

1. Läs befintliga kontorets `status`/`resultat` för **rätt accepterad task**,
   tillsammans med kanonisk plan, relevanta beslut och faktiska kvitton. Använd
   befintlig behörig läsväg. Gör ingen bred källsökning och starta inte om gamla
   tasks eller ersatta väntelägen för att fylla en rapport.
2. Bevara exakt läst ögonblicksbild, observationstid och version i befintlig
   privat hemvist. Skilj observationstid från framställningstid. Saknas en uppgift,
   ange luckan; skapa inga verifierare, revisioner eller tider som inte finns.
3. Bedöm betydelsen: användbara förmågor och begränsningar, faktisk leverans,
   aktuell tillgänglighet enligt observationerna, senaste arbete, motsägelser,
   nästa motiverade handling och handlingsspecifik befogenhet. Bedöm separat om
   ägaren verkligen behöver besluta. Form och oförändrad hash är inget sakgodkännande.
4. Författa privat JSON enligt schemat, med källreferenser för varje huvuduppgift.
   Bevara motstridiga underlag. Skilj historisk ersatt väntan från nuvarande arbete.
   Ingen ny befogenhet, autoacceptans eller automatisk aktualisering följer av rapporten.
5. Rendera till en **ny** privat HTML-version. Behåll föregående indata och utdata.
   Renderaren samlar inte källor, anropar inte Runtime, beräknar inte nya hashvärden
   och uppdaterar inte tider. En ny rapport kräver värdens nya källbundna bedömning.
6. Låt en separat granskare jämföra huvudbudskapen med de bevarade källorna,
   inklusive leverans/tillgänglighet, nästa befogenhet, observationernas ålder,
   osäkerheter och ägarfråga. Värden utför också verklig privat tillämpning,
   webbläsarprov och mottagarprov. Renderarens utskrift ensam är inget leveransbevis.
7. Efter värdens kontroller: ge ägaren en konkret lokal öppningspunkt till den nya
   HTML-filen. Verkliga rapporter och privata indata publiceras inte. Befintlig
   Runtime äger extern acceptans, oberoende granskning och verifierad skyddad
   integration av produkten; denna läsyta påverkar inte den aktiva körvägen.

AP07 kan ge frivilligt stöd vid en konkret osäker koppling, men är inget
standardsteg och piloten ska inte upprepas här. Tidigare auditstatus ändras inte.
Denna kandidat har endast syntetiskt material; inga privata produktionskällor har
lästs eller tillförts. Ingen beslut-, befogenhets- eller körmotor ingår.
