# AP07 — faktisk beredning, inte byggstart

[Samlat byggbeslut](byggbeslut.md) är huvudtexten. Status: förslag, inte accepterat.
Beredningen gjordes med levererad kod vid d79cfc049b4da8920e3c7458cdbee1e7236f0a21.

Värden valde och läste byggförslagets relevanta delar med ERRATA, definition,
intervjubesked och aktuella leveransbevis. BYGGFORSLAG:s bytes matchade ERRATA:s
gällande identitet 14e746fe0e68ceb97ed19c0ca48c895425ecef3848422c14b63de5086cc06b13.
Originalturerna CONV-059 m160/m163 slogs upp med kampanjens befintliga läsverktyg;
metodriktningen grundas inte bara i assistentens efterföljande syntes. Ingen IR
kompilerades eller godkändes. Begränsningarna från A3/A6 består.

Faktiskt genomfört:
- Befintlig evidence_index mätte 19 utvalda källor; AP05 skapade den bundna
  ändringsbedömningen. Samtliga matchade vid jämförelsetillfället i check.json.
  Detta är inte uttömmande källsökning eller evig aktualitet.
- 17 valda referenser kontrollerades mot sina lästa versioner; originalturens roll
  och citat kontrollerades med befintligt uppslag/normalisering. Inga nya RND-id:n.
- AP06:s levererade kommando kördes på verkliga CASE/CHECK/SPEC. Resultat: privat
  spårkedja, briefutkast, taskutkast och krav-/provkopplingar för åtta krav.
- AP06 returnerade korrekt **draft / mechanical_complete=false**: nytt byggmandat
  saknas och värdacceptansens fil/digest har ännu inte författats/granskats/frysts.
  Inga falska bindningar eller acceptansprogram skapades för att få grönt utfall.

Privata underlag och exakt invocation/hashkedja: `local/package-v1/`.
`bundle/brief.draft.md` bär målet, omfattningen och krav/prov; `byggbeslut.md`
preciserar verkliga fall, jämförelsens begränsning och samlat mandat. Kandidaten
ska få självständig innehållsgranskad kontext, inte åtkomst till privata hänvisningar.
Den beredda tasken är avsiktligt inte körbar och är inte placerad i `tasks/`.

Val av metod, problembild, överföringsfall, krav och provens tillräcklighet är
värdens sakarbete. AP05/AP06 sammanställde och kontrollerade mekaniska samband;
deras utskrift är inte godkännande eller bevis för metodens effekt. Ingen pilot,
modellkandidat, ny produktkod eller offentlig publicering är utförd i beredningen.

Förberedande separat sakgranskning ändrade förslaget: AP06-fallet är utvecklingsfall,
inte nytt effektbevis; AP05-fallet är efter första kandidatbygget och får bara
pröva överföring före rättelse/fortsatt integration; anta/anpassa/avstå är möjliga
utfall. Slutlig paketgranskning redovisas separat och ersätter inte ägaraccept.

Metodunderlag: lästa primärsidor från IHI och GOV.UK, privat bundna webbkopior med
URL och hämtningstid i `local/method-sources/retrieval.json`. Vi tillämpar endast
förändringsprovets cykel respektive minsta prov av riskant antagande; inga
allmänna standard-, certifierings-, tidsvinst- eller metodfullständighetspåståenden.

Efter accept återanvänds detta paket. Kedjedrivaren lägger till det faktiska
beslutet i en ny version, hanterar endast relevanta käll-/basändringar och gör
teknisk acceptans och granskning/frysning. Det kräver inte en ny masterprompt
eller ägaraccept per fil. Förändrad omfattning/kostnad/befogenhet kräver nytt besked.
