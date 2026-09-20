# AP-05 — separat granskning före bygge

Separat läsande session `/root/ap05_contract_review`, före implementation.
Underlag: aktivt uppdrag, fryst uppgiftskontrakt, task-JSON och värdacceptans;
Runtimes befintliga profil och kandidatregler. Ingen Runtime-kodändring.

B1: briefen angav tools/.scratch, medan Runtime tillåter .scratch i kandidatens
rot. Rättat och separat omkontrollerat. Inga andra blockerare i kontraktet.
Granskaren föreslog dessutom CLI-prov, strikta bool-/heltalsprov i manifest,
osorterade indata samt prövning av dubblettnyckel i annars giltig JSON.
Dessa infördes före frysning. Tidigare granskningssteg avsåg äldre digest;
slutkvittot nedan anger den frysta versionen.

Slutversion av värdacceptans:
`0b291823a9e7f20617c150cb7a48dc35b0bcba5e9255dcef3a5ad9ace81fcf3b`.
Separat slutkvittens: digest och det rättade dubblettprovet bekräftade; inga
kvarstående blockerare i byggkontraktet.

Metodens begränsningstexter kan inte sakgodkännas genom strängantal i testet.
Den efterföljande separata Runtime-granskningen ska pröva deras innebörd,
att historiska omdömen/befogenheter bevaras och att mätmetoden inte ger ett
falskt fullständighets- eller tillståndsbesked.

Räckvidd: kontrakt, inte ännu byggd kod eller den verkliga fallbedömningen.
