# Levande plan — AP-04

AKTUELLT STEG: Startkopplingen är separat godkänd och skyddat integrerad.
Runtime 09268df5f59a180afe863d4cf7f95c9ad95f8639 (PR15), kontor
71e90f01f9ee3c8fb4ca003b879fc74bc4206b17 (PR1); integrerade träd/baser
matchar granskade kandidater. Resultatuppdragets brief och acceptans är separat
godkända och frysta i tasks/resultat.json, tasks/resultat.md, acceptance/resultat.py.

NÄSTA HANDLING: Uppdrag office-result-1 är startat och står i waiting_diagnosis
på försök 1 efter avsiktligt SIGTERM-prov. Provider avslutad med exit130,
interrupted=signal; provider-, worker- och engine-grupper är verifierat avslutade.
Kör först `python3 -B tools/kontor.py status` och kontrollera kvitto/processer.
Återuppta sedan samma uppdrag med:
`python3 -B tools/kontor.py fortsatt --diagnosis "Controlled interruption completed; provider, worker and engine groups removed; unchanged accepted input and verifier; continue same task"`.
Starta inte ett nytt uppdrag. Hantera därefter verkliga test-/granskningsutfall
med Runtimes diagnos-/review-återgång. evidence/ap04/interruption.json binder provet.

ÅTERUPPTAGNINGSPUNKT: Kontor work/ap04-result-task; Runtime main vid ovanstående
pinnade revision, rent. Kör-id office-result-1, underlag tasks/resultat.json.
`python3 -B tools/kontor.py status` är en läsning; `fortsatt` är en aktiv handling.
Codex är kedjedrivare. Kontrollera Runtime evidence/runs/office-result-1 och
.runtime/tasks/office-result-1 samt processer innan skrivansvaret tas över.
Raw sessions sparas enbart lokalt, aldrig i offentligt Git. Om katalogerna ännu
saknas är uppdraget inte startat. Om de finns får start inte upprepas.

Granskning /root/ap04_review godkände Runtime 26cd64f och kontor 68ebffb;
AP04-R1 rättat (verkliga försökskvitton krävs). 28 Runtime-prov och 3 kontorsprov
PASS. GitHub nekade kontorsmerge utan obligatoriska statusar med HTTP405,
"2 of 2 required status checks are expected". Därefter korrekta statusar och
skyddad squashintegration. Underlagsgranskning rättade två acceptansluckor
(import-I/O och gemensamma returfält); slutlig acceptans SHA256 5f193ad4...
godkänd, tre native I/O-negativprov PASS. Detta är ännu inte AP04-slutleverans.

## Byggordning

1. Startkoppling och målrepoanpassning, riktade negativa prov, separat granskning.
2. Verifiera main-skyddet. Integrera granskade startkandidater i båda repon.
3. Frys accepterat resultatfunktionsuppdrag i kontorsrepot. Starta via kontorets
   ingång; bevara faktiskt avbrott/diagnos och återuppta samma uppdrag.
4. Runtime testar, separat granskar och integrerar resultatfunktionen.
5. Jämför resultat med riktiga körbevis/fjärrrevision, prova läsningars sidoeffektfrihet,
   färsk överlämning och bevarande. Slutgranska och redovisa; stanna.

## Bevis och begränsningar

Etableringens bevis under evidence/entry bevaras oförändrade. Runtime v0.1 och
review-continuation återanvänds inom sin räckvidd. Ny fas får evidence/ap04;
rådata förvaras endast lokalt i Git-exkluderad local/. Inga nya PASS påstås ännu.
GitHub visar publikt kontorsrepo, befintlig adminåtkomst och oskyddad main vid start.
Skyddet ska införas och verifieras före integration. A3/A6 och auditfynd är oförändrade.

---

## Historik — etableringens slutplan (avslutad)

# Levande plan — besluthemmet

AKTUELLT STEG: Avsluta fas 1 med separat kontrollerad slutredovisning och sista bevarandet. Definition, beslut, arbetsform, P1, P3, dokumentgranskning och första verifierade publicering är levererade; slutkandidaten ska också bindas till fjärrrevision och lokalt arkiv före byggarens slutbesked.

NÄSTA HANDLING: Slutför endast slutkandidatens bevarandekontroll: efter separat kontroll av avslutstexterna, innehållskontroll och uppladdning, jämför `git rev-parse HEAD` med `git ls-remote origin refs/heads/main`, återläs GitHub-arkiv och lokalt arkiv mot filhasharna; redovisa därefter och stanna. Om slutkvittot redan finns och matchar HEAD är denna handling utförd: invänta ett eget accepterat uppdrag, starta inget nytt bygge.

ÅTERUPPTAGNINGSPUNKT: `docs/plan.md`, gren `main` i `nortropic-projektkontor`. Börja utan skrivningar med `git status --short --branch` och `git log -1 --oneline`; kontrollera bevis, åtkomst och att föregående skrivare är avslutad. Alla P1/P3-processer är avslutade. Byggaren Codex har ensam skrivansvaret fram till sitt slutbesked. Slutkvittot är lokalt `evidence/entry/local/final-<full HEAD>.json`; det binder den sista uppladdningen och arkivåterläsningen utan självrefererande Git-commit. En ny klon kan själv jämföra HEAD, remote och samtliga spårade filers bytes. Lokal råevidens och arkiv följer inte med klonen.

## Levererat och belagt

- **Definition och beslut:** `DEFINITION.md` och `docs/decisions.md`. Originalets tre stycken matchar mekaniskt, 913 byte. Samtliga 14 I-svar och B-besluten är kontrollerade; B-3 har en uttryckligt markerad utelämning av absolut lokal sökväg. Ingen tolkning har lagts in i definitionen.
- **Arbetsformen och nuläget:** `AGENTS.md`, enradig `CLAUDE.md`, uppdraget och denna enda plan. Startkontroll och källidentiteter i `evidence/entry/start.json`.
- **P1 och P3:** körda interaktivt på `300c239f2e33abf29140ac41e2e9d3b220a2cf00`. Svar, sessioner och räckvidd i `evidence/entry/provbedomning-300c239.md` med länkade kvitton. P1 visar mottagande, P3 laddning. Senare ändringar är dokumentgranskade, inte nya mottagningsprov.
- **Separat granskning:** O1–O9 PASS utan olösta blockerande fynd för `06217b60f23737244964f1a17b47677cad697333`, rapport `evidence/entry/granskning-06217b6.md`. Ett mindre precisionsfel rättat och omkontrollerat.
- **Publikt fjärrrepo:** [Nortropic/nortropic-projektkontor](https://github.com/Nortropic/nortropic-projektkontor). Första uppladdade revision `5f78f016039a2d7ded72a7ded086b0893fafafc2` är återhämtad från GitHub och alla 16 filers bytes jämförda. Lokal arkivkopia återläst mot samma filhashar: `evidence/entry/publicering-5f78f01.json`. Slutkandidatens bevarande bokförs enligt återupptagningspunkten ovan.

## Lästa nuläget vid byggstart

Full redovisning med räckvidd i uppdraget:
- **Finns:** `~/Nortropic Runtime`, HEAD/main `a941207a9ca57697967cf33dcd1c3ea5d884051a`, releasecommit `580630bcb9d46bb11e17e25053664eec4e23b8ae`; arbetsform och provformer återanvänds.
- **Finns:** förberedelsekampanjen under `~/nortropic/intake-campaigns/improvements-preparation-2026-09`, filrevisioner i startprotokollet. B-5 och arbetsorderns SHA-256 stämmer.
- **Fanns inte:** målrepot före start; central definitionsfil inte funnen i riktad sökning. Det senare är ingen total inventering.
- **Kunde inte nås:** inget nödvändigt namngivet underlag.

## Väntan, diagnos och begränsningar

Inget kvarstående kapacitets- eller behörighetshinder. Codex CLI 0.147.0 nekades
modellen med HTTP 400; försöket bevarades och avslutades. Redan installerad appbinär
0.155.0-alpha.2.6 gav lyckat P3. Ingen installation, modellväxling eller
API-fallback gjordes. Interaktiva verktygsstarter lagrar själva sessionshistorik
och projektets trust-val i sin befintliga användarprofil; byggaren har inte ändrat
global verktygspolicy eller andra projekts inställningar.

Förberedelsens A3/A6 är inte uppfyllda; FIND-004 är inte stängt. Ingen Runtime-körning,
utförd nästa uppgift, minskad ägarbörda eller efterlevnad över tid är visad.
Arbetsregler är inte tekniska skrivspärrar. Lokala arkiv är på samma disk och skyddar
inte mot diskförlust. `.git/info/exclude` utesluter `evidence/entry/local/` lokalt;
regeln följer inte med en klon och ersätter aldrig kontroll före uppladdning.

Efter verifierat slutbevarande är fasen slut. Nästa möjliga arbete är att
kedjedrivaren förbereder nästa nyttiga uppgift för ett eget accepterat uppdrag.
Det arbetet och senare användning av Runtime startas inte genom denna fas.
