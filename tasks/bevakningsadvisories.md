# Säkerhetsmeddelanden för aktiva låsta pip-versioner

Uppdrag: OVL-20260930-ac1914 C2. C1:s läsning av GitHubs SBOM hittade
inte Runtimes låsfil. Komplettera det befintliga AP10-intaget utan att ändra
dess bedömningsväg, modellsteg, körschema, befogenhet eller automatiskt uppgradera.

Läs exakt aktiva rotens `config/temporal-probe-requirements.lock` genom den
befintliga begränsade filläsaren. Låsfilen och Runtime ändras inte. Fråga
GitHubs publika `api.github.com/advisories` med `ecosystem=pip` och
`affects=paket@version`, en fråga per låst paket. Använd samma transportgränser:
adresskontroll före nätkontakt, ingen autentisering/proxy/redirect, högst
en MiB och tio sekunders socket-timeout. Det är ingen ny total tidsgräns.
Begränsa till granskade, ej återkallade meddelanden. Ogranskade meddelanden
och malware ingår inte; tomt svar betyder bara inga kända granskade meddelanden.

Varje GHSA blir egen hashbunden observation med allvarlighetsgrad, exakt låst
version och första rättade version kopplad till det angivna versionsintervallet.
GitHubs `affects` avgör tillämplighet; påstå ingen egen fullständig PEP440-tolkning.
Bevara råsvaret. Tomt giltigt svar ger daterad observation. Felaktigt svar,
nätfel, 429, okänd låssyntax eller ofullständig paginering gör paketet ofullständigt.
Tidigare paket skrivs aldrig om. Samma fullständiga underlag ska fortsatt kunna
återanvända bedömning; observationstiden är metadata, inte ändrad sakuppgift.

Produktionsändringen begränsas till `tools/bevakningsunderlag.py`, dess prov
och beskrivning samt ett prov av den befintliga bedömningsvägen i
`tools/test_bevakning.py`. Ingen förändring av `tools/bevakning.py` behövs.
Kör syntetiska prov av de fem fallen i beställningen, begränsningsfallen och
att den egna observationen når både analys och separat granskning utan exekvering.

Värdens nya `acceptance/bevakningsadvisories.py` binder modulens exakta SHA256.
Den tidigare frysta `acceptance/bevakningsschema.py` förblir oförändrad och
hashkontrolleras före import. Alla dess policy- och schemakontroller behålls;
endast modulbindningen och explicita syntetiska lås-/källfixturer anpassas i
den nya acceptansens kopia. Oberoende syntetiska advisory-kontroller läggs till.
Detta uppdragsdokument, JSON och den nya frysta acceptansen förbereds av värden
och ska ingå i separat granskning av hela diffen. Kandidaten får inte ändra
den aktiva acceptansen eller själv aktivera sig.

Klart för integration: nyckellös helsvit, grön fryst acceptans, separat
godkännande utan blockerande fynd och skyddad publicering. Aktivering förbereds
genom ordinarie AP10-övergång och redovisas i ÄGARENS TUR om den kräver ägaren.
En grön syntetisk svit bevisar inte att aktiv drift redan använder modulen.
Inga partnerkvittenser, start-/stoppkommandon, konton eller nya credentials ingår.

Källor: OVL-20260930-ac1914 C1, C2 och Klart när; befintliga
`tools/BEVAKNINGSUNDERLAG.md`, `tasks/bevakningsschema.md` och
`acceptance/bevakningsschema.py`; GitHubs REST-dokumentation för
[globala säkerhetsmeddelanden](https://docs.github.com/en/rest/security-advisories/global-advisories#list-global-security-advisories),
läst 2026-09-30.
