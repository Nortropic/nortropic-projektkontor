# AP-05 — separat sakgranskning av kartärendet

Granskare: separat läsande session `/root/ap05_case_review`. Värden skrev
bedömning och kontrollkod; granskaren använde egen läskod utan att köra värdens
skript eller generatorn. Inga filer ändrades av granskaren.

Underlag: I-11, FINAL-CHECK-1 §5 med historisk identitetslista, relevanta senare
rättelser, dagens befintliga kartkandidat och bundna indata. Ingen IR-sakaudit,
valvläsning eller total kampanjgranskning. Fulla interna sökvägar och råunderlag
bevaras endast lokalt. Kontrollerade bindningar finns i
../../cases/map-layer/case-evidence.json.

## Fynd och rättelser

Första bedömningen sköt upp kandidatens begränsade läskontroll till ett nytt
mandat. Separat scopeprövning slog fast att senaste AP-05 redan omfattar denna
nödvändiga källäsning. Kontrollen utfördes inom paketet, utan generatoromkörning.

I v2 saknades direkt beroende till baslinjekvittot i tre slutsatser; en handlings-
text bar kvar ett för brett påstående om återstående teknisk tillämplighet,
och en bevarandehandling blandade publicering i sin text. V3 rättar detta:
baslinjekvittot binds till F7/F8/J2, A3 avser målvalvets återstående förutsättningar,
A1 gäller bara bevarande och publicering har eget mandat. Nästa handlings-id är
NEXT_OWNER för att inte blandas ihop med öppna auditkriteriet A6. V1/v2 bevaras.

## Oberoende observation

2026-09-20T18:49:11Z reproducerade granskaren 1199 kandidatfiler utan symlänkar,
samtliga manifesthashar/byteantal, 938 oförändrade baslinjefiler, exakt 261
förväntade tillägg (260 inom lagret, en pekarnot utanför), samma tolv lexikala
radträffar och fem historiska binärfiler. Den manuella träffklassningen stämde.
Alla bundna källhashar stämde; även v3:s källor återkontrollerades vid slutgranskning.

## Slutdom

**Godkänd inom sak- och publiceringsgranskningens räckvidd; inga kvarvarande
blockerare i v3 eller den granskade publika falltexten.**

- Privat bedömning map-case-v3.json:
  `179e43593f52b9a44a881b41adcc8cd525e2a001b07d61fc86366a21fe61ef2c`.
- Publik cases/map-layer/assessment.md:
  `5d7fabb78936873cfd8a4bfb1beaa1c03d35254f7eb1e1362b9f9c06abc7d609`.

Granskaren bekräftar att texten skiljer historiskt bevis, nya observationer,
sakbedömning och faktisk befogenhet. Inga privata källutdrag, områdes-/familjenamn,
användaridentiteter, absoluta privata sökvägar eller råloggar hittades i falltexten.
Tekniska identiteter, antal och generiska slutsatser bedömdes relevanta för den
uttryckligen tillåtna fallredovisningen. Lokal evidenspekare avslöjar inte
originalkällornas placering.

Domen gäller dessa revisioner och den avgränsade sakmätningen. Den godkänner
inte själva kartförändringen, A3/A6, skrivning till valvet, kodens prov eller
fjärrintegration. Kompletterande bindningsfiler och slutleveransen granskas för sig.
