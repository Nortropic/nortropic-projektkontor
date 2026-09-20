# Levande plan — AP-05

AKTUELLT STEG: Frysta syntetiska byggunderlag är färdiga och separat
granskat kontraktsfynd rättat; verkligt källurval är bundet lokalt. AP-04 är avslutad vid kontor 17ce93a / Runtime 2789ea0;
slutkvittot finns i evidence/ap04/local/. Starta inte dess uppdrag igen.

NÄSTA HANDLING: Starta AP-05 genom tools/kontor.py start --task andringsbedomning.json
när värdacceptans och brief är granskade och committade. Kandidatbas 17ce93a
förblir remote main tills Runtime har integrerat kodstödet.

ÅTERUPPTAGNINGSPUNKT: gren work/ap05; tasks/andringsbedomning.json, uppdrags-id
office-change-assessment-1. Kontrollera Git, aktuell Runtime-status och tidigare
skrivare före fortsatt arbete. Ingen körning startad ännu. Status/resultat är
rena läsningar med --task andringsbedomning.json. Privat källmappning och
mätningar finns i evidence/ap05/local/; publicera aldrig denna katalog.

Ordning: fryst syntetiskt kontrakt → Runtime-bygge/test/review/integration →
verklig tillämpning och separat sakgranskning → färsk mottagare → skyddad
integration av kontrollerad fallredovisning och slutbevarande. Värdens arbete
på denna gren och modellens isolerade kandidat har skilda filer; ingen annan
skriver i värdens arbetsyta. Inga Runtime-kodändringar. Gamla auditfynd öppna.

Tidigt sakfynd: generator och kartkvitto har nya identiteter efter FINAL-CHECK-1.
Pröva domens tillämplighet; flytta inte dess PASS tyst till dagens kandidat.

---

## Historik — AP-04-plan (avslutad; aktiva steg ovan gäller)

# Levande plan — AP-04

AKTUELLT STEG: Resultatfunktionen är byggd genom kontorets ingång och skyddat
integrerad av Runtime i PR2, 5a6084ee156bb2d12537f5e58af62e125d83be14.
Funktion, verkligt avbrott/återupptagande, negativa fall, färsk mottagare och
oberoende jämförelse mot körbevis/fjärrintegration är verifierade. Endast separat
slutgranskning, integration av avslutstexterna och slutligt Git/arkivbevarande återstår.

NÄSTA HANDLING: Granska exakt avslutskandidat i båda repon separat. Rätta bara
relevanta blockerare; integrera sedan kontrollerat innehåll genom skyddade PR:er.
Jämför slutlig HEAD och origin/main samt GitHub-arkiv och lokalt arkiv byte för
byte i båda repon. Bevara ett lokalt final-<office HEAD>-<runtime HEAD>.json
under evidence/ap04/local/ som binder slutrevisionerna utan självrefererande
commit. Om detta kvitto redan finns och matchar revisionerna är fasen avslutad:
redovisa och stanna; starta inte fler uppdrag eller nästa byggfas.

ÅTERUPPTAGNINGSPUNKT: Kontor work/ap04-closeout; Runtime work/ap04-receipt.
Körd Runtime-kod: 09268df5f59a180afe863d4cf7f95c9ad95f8639. Efter körrevisionen avgränsas office-profilen dessutom till faktiskt prövad
Codex-provider med riktat test; gammal Runtime-providerprofil är oförändrad.
Övriga senare ändringar gäller bevis, plan och råloggsexkludering.
Uppdrag office-result-1 är completed, två försök, en publicering. Även aktiv
återupptagning av avslutat uppdrag gav oförändrade räknare, inga nya modellkörningar
eller publiceringar. Alla registrerade processgrupper avslutade. Starta inte om.
Status och resultat kan läsas med `python3 -B tools/kontor.py status` respektive
`python3 -B tools/kontor.py resultat`. De läser snapshots, inte livebevakning.

Bevis: evidence/ap04/delivery-verification.json, result.json, interruption.json,
handover.json och leverans.md. Runtime evidence/ap04/result-run.json innehåller
försöks-/gransknings-/integrationsidentiteter; native-preservation.json binder
återläst lokalt arkiv och konsekvent databasbackup. Råhistorik är Git-exkluderad.
En färsk klon får inte hitta på lokala bevis: frånvaro visas som unavailable.

Nästa möjliga fas är ett nytt accepterat internt utvecklingsuppdrag med egen
verksamhetsnytta; rekommendationen i leverans.md är inget byggmandat. A3/A6 och
tidigare auditfynd är oförändrade. Alla fynd i just AP04:s start-/underlagsgranskning
är rättade och omkontrollerade; slutgranskningen prövar detta pakets bevis.

## Genomförd byggordning (slutbevarande återstår enligt ovan)

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
rådata förvaras endast lokalt i Git-exkluderad local/. Nya bevis och deras räckvidd står i leverans.md.
GitHub visar publikt kontorsrepo, befintlig adminåtkomst och oskyddad main vid start.
Skyddet infördes och verifierades före integration; HTTP405-provet finns bevarat. A3/A6 och auditfynd är oförändrade.

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
