# Levande plan — AP-06, verifierad funktion; slutpaketets integration/bevarande återstår

AKTUELLT STEG: Källbunden uppdragsberedning är byggd och verifierad genom AP04:s
befintliga Runtime. Kärnan är integrerad i PR7/dd1f8c5; det verkliga CLI-uppdrag som
kärnan beredde är genomfört och integrerat i PR8/8e5f1c0. Separat kod-/sakgranskning,
fryst acceptans, verklig användning och metodexempel är prövade. Slutpaketets separata avslutsgranskning och färska mottagare är godkända enligt
closeout-review.json och handover.json. Revisionsbekräftelse av dessa protokoll,
skyddad integration och slutarkiv återstår.

NÄSTA HANDLING: Slutför just dessa avslutssteg på work/ap06-delivery. Kandidaten
har ett enda publicerbart commit på aktuell main, med kontrollerade AP06-underlag,
metodpekare och bevis; privata eller tidigare opublicerade kart-/planhistoriker
ska inte följa med. Efter godkända verkliga grindar: integrera med befintlig
värdpublicerare, jämför HEAD/origin/main/GitHub-arkiv, bevara och återläs det lokala
final-<HEAD>.json i evidence/ap06/local/. Om ett sådant kvitto redan finns och
matchar publicerad main är AP06 färdig: redovisa och STANNA. Starta ingen ny fas.

ÅTERUPPTAGNINGSPUNKT: Börja utan skrivningar; kontrollera Git, kvittot och gamla
skrivare. Definition/uppdrag/AP06-ACCEPT är gällande grund. Läs
[evidence/ap06/leverans.md](../evidence/ap06/leverans.md) och
[use-case.md](../evidence/ap06/use-case.md), sedan relevanta bindningar i core-run.json,
cli-run.json, cli-continuation-review.json, real-application.json och
method-verification.json. Ingång till funktionen: tools/BERED_UPPDRAG.md.
Planen ensam äger nästa handling; inga tekniska delsteg ska bäras av ägaren.

## Exakta körningar och privat kontinuitet

- office-assignment-core-1: completed; startas inte igen. Accepterad fil
  tasks/uppdragsberedning-karn.json, integration dd1f8c56456b575f017219621402658b5200c592.
- office-assignment-cli-2: completed; startas inte igen. Accepterad fil
  tasks/uppdragsberedning-cli-continued.json, integration 8e5f1c07a79ff288fc8e0a646bb9f7eb66a58f44.
- office-assignment-cli-1: bevarad historisk waiting_diagnosis efter VÄRDENS
  felaktiga importlauncher. Ingen process finns kvar, inget integrerades.
  Den är uttryckligen ersatt av CLI2 inom samma mandat; återuppta den INTE och
  ändra aldrig dess frysta acceptans. cli-host-correction.json redovisar detta.

Status/resultat läses vid behov med tools/kontor.py och rätt --task. De är sparade
observationer, inte livekontroll och inte order om fortsatt körning. Runtime är
2789ea0770e4234161e9bdb0378a6e3e7b8432d2, oförändrad. Inga aktiva AP06-körningar enligt nativeprocesskvitton. Detta är inte ett
påstående om att alla äldre interaktiva sessioner på datorn har avslutats.

Privat fullmandat/start: evidence/ap06/local/accepted-mandate.md och start.json.
Aktuell beredning: local/real-cli-v3/ med case/check/spec/prepared, host-amendment,
freeze och command-bundle-v1. V1/V2, gammalt verifieringsutfall och explicita
omprövningar bevaras, inga referenser uppdaterades automatiskt. Värdens lokala
arbetsgren work/ap06 behåller tidigare opublicerade plan-/kartcommits.
Nativehistorik/DB-backup: local/native-ap06.tar.gz enligt native-preservation.json.
Slutligt Git/ärendearkiv binds i final-kvittot. Rådata stannar lokalt och Git-exkluderat.
En färsk klon utan detta material får inte fabricera lokal evidens eller mandat.

## Tillgodoräknat och avgränsat

Etableringen, AP04, AP05 och KART-INFORANDE-01 är levererade inom sina redovisade
räckvidder. Tidigare käll-/audit-/kartspår öppnas endast vid konkret behov, inte
som rutin. Tidigare slutkvitton och evidence/entry, ap04 och ap05 bevaras.
Kartans slutkvitto finns privat i evidence/map-delivery/local/final.json; ingen
valvläsning/skrivning eller kartomkörning gjordes i AP06. Begränsad ägaråterkoppling
är fortfarande inte bevisad begriplighet eller tekniskt PASS.

Beredningen är mekanik. Kedjedrivare och separat granskare väljer/läser och bedömer
källor, krav, provens tillräcklighet, handlingsspecifikt mandat och exportinnehåll.
Utdata förblir utkast; inga automatiska rättigheter, acceptansprogram, modellstarter
eller publiceringar. Ingen omätt tidsvinst eller allomfattande källaktualitet påstås.
A3/A6 och tidigare fynd stängs inte. Ingen ny motor, Runtime-ändring, IR-kompilering,
tjänst/kostnad/behörighet eller nästa byggfas ingår. Fråga ägaren endast vid verklig
ändring av mål, kostnad eller befogenhet — inga rutinmässiga fortsättningsbesked.
