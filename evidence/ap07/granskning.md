# Separat sakgranskning — AP07-beredning

Granskare: /root/map_install_review. Endast läsande arbete; ingen filskrivning,
modellstart eller pilotkörning av granskaren.
Granskad revision: be465a16f7ea1458e094b27c32a4155170491881.
**Utfall: APPROVED för presentation som samlat byggbeslut. Inga blockerare.**
Detta är inte byggstart, publiceringstillstånd, I07b-avgörande eller effektbevis.

Granskaren bedömer att paketet ger mer än dokument/stödverktyg: en användbar
metodbeskrivning måste följas av faktisk tillämpning och separat sakbedömning.
Före/efter-rekommendation, valt prov, observation, fungerande kontrast och
representativitetsbedömning gör kriterierna observerbara. Anta/anpassa/avstå
är möjliga utfall. Historiskt urval ger smal bevisräckvidd.

Oberoende kontroller:
- 19 källors hash/storlek och 17 referensers källa/version/citat eller locator
  matchar. Originalturernas användarroll och metodvilja stämmer.
- AP05-manifest/bedömning och AP06-bundlens fyra utdata reproducerades i minnet;
  de matchar sparad invocation/hashkedja.
- Exakt tre avsiktliga luckor: acceptance, acceptance_sha256 och
  action_authority_missing. Beredning, genomförande och publicering hålls isär.
- AP06 är utvecklingsfall, inte nytt effektbevis. AP05-fallet är efter första
  kandidatbygget; historisk granskare hittade felet. Inget påstående om generell
  eller tidigare upptäckt/överlägsenhet lånas från dessa gamla händelser.
- Bundna primärsidor stöder begränsad metodanvändning; inga påståenden om läst
  IHI-nedladdningsmaterial, full alpha-tillämpning eller standardefterlevnad.
- Befintliga verktyg är oförändrade, privata underlag ignorerade av Git. Ny
  metodfil, teknisk acceptans och AP07-Runtimekörning finns ännu inte.

Kvarvarande risk att följa vid genomförande: att arbetsbeskrivningen blir en
rutinmässig obligatorisk kontroll utan visat behov. Paketets tillämpningsgräns,
korrekta kontrast och möjlighet att avstå hanterar risken i förslaget; effektens
sakgranskning ska pröva den igen. Ingen ny generell grind är accepterad.

Bindningar till privat underlag:
- case.json: 647c670a7340dd1a5084f5470975f8a03caa18db9d2895564b60c4534cf1c8e9
- spec.json: 6f83a195f3a056167ce4c85084af31c569eeb2afa2ab7fb40e8dbdaaedac5cfb
- bundle/package.json: 6b7d4b1a2a45975393436c815b0aa26455a9bb6b6fea13152e8f51c61f8c2400

Efter accept kan samma paket fortsätta med ny bevarad mandatversion och teknisk
acceptansgranskning/frysning. Ingen nollberedning behövs. AP06/tidigare leveranser,
A3/A6 och tidigare fynd behåller sin räckvidd/status.
