# AP07 — levererad metodpilot inom avgränsad räckvidd

Kontoret har prövat ett återanvändbart arbetssätt på faktiskt tidigare kontorsarbete.
[Separat granskat metodbeslut: ANPASSA](../../docs/metodbeslut-ap07.md).
[Anvisningen](../../tools/METODPROV.md) är valbart stöd i den befintliga arbetsvägen,
inte en ny kontrollrutin. Den hjälper utföraren precisera en avgörande osäkerhet,
välja ett representativt litet prov och stanna vid tillräckligt nästa beslut.

AP06-retrospektivet visar att körkontextens fråga kunde prövas med redan tillgänglig
kärna. Fyra färska överförings-/kontrastkörningar visar eget provval och korrekt
stopp. Båda arbetsformerna nådde samma beslut; metodarmarna tog mer registrerad
sessionstid. **Ingen förbättrad produktivitet, tidsvinst eller minskad ägarbörda
är belagd.** Det är ett avslutat begränsat försök, inte ett lärandeprogram.

## Bevis och återanvändning

- [Låst försöksplan](provplan.md) och [faktisk tillämpning](tillampning.md):
  före/efter-beslut, observation, fungerande kontrast, exponering och merarbete.
- [Fyra körkvitton i begränsad form](trial-summary.json): verklig native usage/tid,
  inputbindningar och avslut. Fulla indata, kommandon och råspår bevaras privat.
- [Runtime-leverans](method-run.json): office-method-trial-1, kandidat
  `3b6bee7145ba961dcf1460d3c35101824d07964e`, skyddad
  [PR10](https://github.com/Nortropic/nortropic-projektkontor/pull/10), merge
  `16d11720e4c5f0caba30b9709d0a877cfab83217`. Fryst exempelkontroll och separat
  artefaktreview godkända. Slutpaketet ändrar endast metodtextens status/läshänvisning,
  inte dess exempel eller arbetsrecept.
- [Separat sakgranskning](substantive-review.json): metodtillämpning, bevisens
  räckvidd, kontrast, resursuppgifter och slutsats, inte bara dokumentstruktur.
- [Återanvända prov](reused-evidence.json) täcker äldre rättelser och negativa
  käll-/mandatfall inom sina räckvidder. Original, frysta kontroller och rättelser
  ändrades inte. Riktat tekniskt fynd i AP07-värdacceptansen rättades/granskades
  före körstart; v1/v2/v3 och tidigare review bevaras privat.
- [Källkontroll](source-recheck.json) gäller 23 valda bindningar före avslutstillägg.
  Senare metodbeslut är nya utdata. Beredningsgrenens privata material/tekniska
  inputs ligger kvar i lokal historia och arkiv, inte i publicerad ancestry.
  Ingen referenshash har skrivits över för att dölja ändringen av beslutsloggen.

Faktiskt använd Runtime-revision är
`2789ea0770e4234161e9bdb0378a6e3e7b8432d2`, utan kodändringar. Metodbyggets
kontorsbas var `d79cfc049b4da8920e3c7458cdbee1e7236f0a21`. De fyra metodproven
använde exakt metod från PR10, bunden i körbeviset. Det lokala slutkvittot
`local/final-<fjärr-main-revision>.json` binder slutpaketets verkliga integration,
servergrindar, fjärrträd, båda repo-revisioner och slutligt bevarande. Före detta
kvitto återstår bara avslut enligt planen; texten ensam är inte integrationsbevis.

## Bevarande och nästa utförare

[Nativearkivet](native-preservation.json) bevarar metodtaskens arbetsytor,
historik och konsistent Runtime-databasbackup.
[Pilotarkivet](pilot-preservation.json) bevarar frysta indata, egna provytor,
privata källor, beredningsversioner och fullständiga försöksresultat.
Båda ligger Git-exkluderat under `local/` och har återlästs mot filhashar.
Det är privat bevarande på samma disk, inte separat katastrofbackup.
Senare avslutsreview, publiceringskvitto och slutkvitto bevaras där i egna filer.

Nästa utförare börjar i [planen](../../docs/plan.md), därefter metodbeslut och
anvisning vid konkret behov. Ingen ny ägarförklaring eller ny masterprompt behövs
för att återfinna resultatet. Avslutade försök återstartas inte. Nya funktionella
uppdrag kräver eget mandat; AP07 beställer ingen fortsatt byggfas.

Etableringen, AP04–AP06 och kartleveransen behåller sina redovisade begränsningar.
Ingen Runtime-kod, kampanj, IR eller valv ändrades. Inga nya tjänster, tekniska
rättigheter eller modellanslutningar infördes. A3/A6 och tidigare auditfynd stängs
inte. Sakbedömning och konkret handlingsbefogenhet kräver fortsatt ansvar.
