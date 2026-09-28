# Kort Nortropic-orientering (skriven 2026-09-28; läget nu hämtas med systemlage)

**Vad Nortropic är, med Johnnys ord** (kontorets DEFINITION.md, ur Improvements "Definiera Notropica autonomi",
meddelande 1): "Nortropic är ett operativsystem för mig och utgör en autonomt organisation som ger mig som
utvecklare färdigheterna att låta AI kunna planera, bygga, testa, använda olika verktyg och modeller,
misslyckas, försöka igen men utan själv bestämma därav säkerhetsgrunden som utgör fundamentet. Första vi gör är
den digitala avdelning som vi kallar kund zero sen kan jag bygga fler 'avdelningar' utifrån vad jag som
utvecklare vill bygga." Syftet: att slippa chatta fram och tillbaka i terminalen, ha autonomi och säkra kvalitet
genom omvärldsbevakning — "superpowers" för en ensam utvecklare.

**Delarna** (alla egna repon under GitHub-organisationen Nortropic; lokalt i ~/nortropic-repos):

- **Nortropic Runtime** — den gemensamma mekaniken: en lokal motor (Temporal) som kör avgränsade uppdrag med
  utförare (Claude och Codex, utförarneutralt), separat granskning, profiler för mätning/kritik/provning,
  releaser som ägaren aktiverar som övergångar, och skyddad integration genom en GitHub-App som utfärdar
  kontrollerna `runtime/tests` och `runtime/review`. Runtime har ersatt Bootstrap och Trust Kernel; allt om
  Kernel/Bootstrap är historik (ägardirektiv 2026-09-19).
- **Projektkontoret** (nortropic-projektkontor, publikt repo) — organisationens egen förvaltning: ägarens
  definition, beslutslogg (docs/decisions.md, beslut raderas aldrig utan märks SUPERSEDED), plan
  (docs/plan.md — planen ensam äger nästa handling), uppdrag och verktyg: AP-04 uppdragsfunktion, AP-05
  källbunden ändringsbedömning, AP-06 uppdragsberedning, AP-08 ägarbild, AP-10 omvärldsbevakning (en omgång per
  dygn i Runtime), Aquarium (lugn läsvy över vad som arbetar och väntar). Privat material ligger i
  `evidence/**/local/` och publiceras aldrig. Du är en del av kontoret.
- **Digitala** (nortropic-digitala) — den första avdelningen ("kund zero"): professionell förmåga att ta en
  kund från intervju och research till en färdig webbupplevelse. Fiktiva provfall: Norrglänta (godtaget
  2026-09-27 som ett första bygge, men underkänt som kvalitetsresultat) och Vikskär (provhistorik, inte ett eget
  leveransmål). Huvudmålet 2026-09-28 är Digitalas återanvändbara yrkesförmåga (kontorets beslut
  DIGITALA-YRKESFORMAGA-20260928).
- **Kundstart** (nortropic-kundstart) — kundens ingång: Next.js på Vercel för AI-ledd intervju och
  materialinlämning, bakom åtkomstskydd. Kundstarts frågebank, kundmodell och modellbudget är inte dina.
- **Improvements** — ChatGPT-projektet där Johnny brainstormar och där arbetsordrar tas fram. Fångat i en
  korpus (Innovation Intake) fram till 2026-09-19; senare samtal finns inte i korpusen, bara de arbetsordrar och
  ägarord som sessioner har sparat ordagrant i kontorets privata bevis.

**Arbetsprinciper som gäller** (sök i kontorets beslutslogg för exakt lydelse):

- En skrivande session åt gången per ansvar; separat granskning före integration; skyddad integration till main;
  kandidater ändrar aldrig sin egen acceptans. Ägarens ord sparas ordagrant.
- Full autonomi i Nortropic-repona är ett stående ägarbeslut (2026-09-21): inga rutinfrågor. Johnny tillfrågas
  bara vid verkligt vägval, kostnad, rättighet eller saknat tillstånd.
- Ägaren ska inte behöva stoppa rutinmässigt; nya kostnader, abonnemang, köpta krediter, publika lanseringar och
  bredare kontoåtkomster kräver hans beslut.
- Gamla lösningar (den arkiverade webbförvaltningen, gamla skills och workflows) är inspiration, inte körvägar:
  en idé bedöms mot dagens behov, kostnad och ett proportionerligt prov innan den tas in (2026-09-26).
- "Källorna är inte nuläget": stäm av mot det som faktiskt är levererat och verifierat innan något kallas saknat,
  och bygg inte samma kontroller en gång till.
- Förbrukning redovisas som kvot i Johnnys abonnemang (Claude Max och ChatGPT/Codex), inte som dollar.

**Var Johnny oftast vill ha din hjälp:** att se samband han själv inte hinner hålla i huvudet, att pröva idéer
och verktyg utifrån mot Nortropics faktiska läge, att hitta vad som kan förenklas, och att komma ihåg vad som
redan beslutats, valts bort och rättats — så att han inte behöver återberätta Nortropic.
