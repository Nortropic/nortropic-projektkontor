# Värdens bedömning — P1 och P3, 2026-09-20

Prövad commit: `300c239f2e33abf29140ac41e2e9d3b220a2cf00`.
Byggare och bedömare: Codex. Mottagare P1: separat färsk Claude Code-session.
Underlag: `p1-300c239-answer.md` och `p1-300c239.json`; separata P3-svar och
kvitton med prefix `p3-claude-300c239` respektive `p3-codex-300c239`.

## P1: PASS för mottagande på den angivna kandidaten

| Prövad del | Mottagarens svar kontrollerat mot filerna vid kandidaten | Bedömning |
|---|---|---|
| Åtagande | Återger uppdragets avgränsade första fas och skiljer I-09 från B-5 | Rätt |
| Utfört | Hittar dokumenten, rätt HEAD via Git-metadata och att fjärrrepo ännu inte konfigurerats; kallar inte fasen klar | Rätt |
| Skyddat | Kampanj, Runtime, syskonrepon, valv, befintliga prov och förbjudet publiceringsinnehåll identifierade | Rätt |
| Begränsningar | A3/A6 och FIND-004 öppna; arbetsregler är inte spärrar; ingen Runtime-körning eller minskad ägarbörda visad | Rätt |
| Nästa handling | Läser planens provstart; ser att den egna sessionen redan realiserar starten och anger värdens kontroll och protokoll som det följande steget | Rätt, med synligt tidsförbehåll |

Mottagaren gav citat och gjorde relevanta egna iakttagelser: exkluderingen av lokal
råevidens ligger i `.git/info/exclude` och följer inte med en klon; planen låg
naturligt kvar på läget före provstart under den frysta läsningen. Båda uppgifterna
stämmer. Senare planuppdatering bokför provet; inget gammalt protokoll skrivs om.

Faktisk start: interaktiv CLI under en PTY i repots rot, utan `-p`, ingen återupptagen
session och ingen inklistrad projekttext. Prompten bad om åtagande, utfört arbete,
skyddat material, begränsningar och nästa tillåtna handling med citat. Den gav inget
facit och inga källsvar. Claude använde automatiskt laddad AGENTS via CLAUDE-import
för läsordningen. Endast `Read` exponerades, med `dontAsk`, strikt tom MCP,
Chrome och slash-kommandon avstängda. Sessionen skrev inga projektfiler.
Värden skrev protokollen efter svaret. Alla åtta kandidatsfiler var oförändrade
under proven (`git diff --stat` tomt före bevarandet).

Råterminal och native sessionslogg bevaras lokalt, med sessionsloggens SHA-256 i
kvittot; de publiceras inte eftersom de innehåller absoluta lokala sökvägar och
verktygskontext. Det publika svaret är mottagarens slutliga text, utan redigering.

## P3: PASS för båda verktygen

Båda färska interaktiva sessionerna återgav `NPK-ENTRY-20260920-7C91E2` och
`docs/plan.md` utan något modellstyrt verktygsanrop. Claude hade inga verktyg;
Codex startades med `read-only` och `never`. Samma neutrala prompt användes om
markör och plansökväg, utan att lämna svaren. Ingen projekttext injicerades.
CLI-versioner och sessionsidentiteter finns i respektive kvitto.

Första Codex-försöket med CLI 0.147.0 gav HTTP 400 före något svar eftersom den
konfigurerade modellen krävde nyare klient. Det är ett bevarat misslyckat försök,
inte ett PASS. Nytt försök gjordes först med en redan installerad appbinär
0.155.0-alpha.2.6; ingen installation, modellväxling eller API-fallback gjordes.

Samtliga tre lyckade provsessioner avslutades efter färdigt svar; värdens
terminalverktyg returnerade exit 0. Den äldre felande Codex-sessionen avslutades
också med exit 0 på `/quit`; det ändrar inte dess misslyckade modellanrop.

## Räckvidd

P1 visar ett korrekt läsande mottagande av en mottagare vid en commit i detta repo,
inte att nästa uppgift utförts. P3 visar tillgänglig kontext vid respektive start,
inte förståelse eller efterlevnad över tid. Ingen Runtime-körning eller teknisk
repoövergripande skrivspärr har prövats. Ingen ägarbörda har mätts. Senare ändringar
måste bedömas på egna meriter; P1 påstås inte vara omkört på dem.
