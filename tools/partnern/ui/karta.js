'use strict';
// Flödet (MODELLKARTA-20260929): Nortropics flöde som en karta med fyra linjer. Vid varje hållplats står modellen och
// ansträngningen som arbetar där, och varje hållplats följer ett av fem val. Valen läses ur sina riktiga källor av
// servern (/api/arbetsplats/karta), som bara erbjuder modeller och nivåer som bevisligen fungerat i programmet som kör
// hållplatsen. Här väljer Johnny för partnern, sina två program och läsarna. Ett val sparas först när Johnny trycker
// Spara, aldrig av en ändrad meny. Innehåll renderas med el() (textContent) ur app.js.

const KARTLINJER = [
  { namn: 'Idé till main', under: 'alla repon', hp: [
    { id: 'du', namn: 'Du', val: 'du', under: 'en tanke, ett repo', text: 'Du lämnar en tanke, en länk eller ett repo i Förbättringar.' },
    { id: 'forbattringar', namn: 'Förbättringar', val: 'partner', under: 'partnern och utredaren', text: 'Partnern läser i original, resonerar och bereder beställningar. Utredaren kör samma modell och ansträngning.' },
    { id: 'backlog', namn: 'Backlog', val: 'ingen', under: 'vilande beställningar', text: 'Vilande beställningar väntar här. Inget startar av sig självt.' },
    { id: 'slapp', namn: 'Ditt släpp', val: 'ord', under: 'dina ord', text: '"släpp OVL-…" eller "avslå OVL-…" i en tråd. Utan dina ord flyttas ingenting.' },
    { id: 'arbetssession', namn: 'Arbetssession', val: 'runtime', startvakt: true, text: 'Startvakten startar mottagarens session i kontoret, Runtime eller Digitala, med Runtimes utförare och modell. Ansträngningen är i dag startvaktens egen. När startvakten är av gör dina sessioner det arbetet.' },
    { id: 'granskning', namn: 'Granskning', val: 'lasare', under: 'separat läsare', text: 'En separat läsare granskar kandidaten före publicering, genom Runtimes läsarprofil.' },
    { id: 'main', namn: 'Main', val: 'du', under: 'skyddad integration', text: 'Skyddad integration genom GitHub-appen. Ingen modell.' },
  ] },
  { namn: 'Kund till leverans', under: 'Digitala', hp: [
    { id: 'kund', namn: 'Kund', val: 'du', under: 'kunden', text: 'Kunden möter Nortropic genom Kundstart.' },
    { id: 'kundstart', namn: 'Kundstart', val: 'ingen', under: 'ingen AI i produktionen', text: 'Intervju och material i produktionen, utan språkmodell.' },
    { id: 'beredning', namn: 'Beredning', val: 'sessioner', under: 'kontoret', text: 'Kontoret bereder beställningen: problem, proportion, metod och kanalbehov.' },
    { id: 'research', namn: 'Research & brief', val: 'sessioner', under: 'Digitala', text: 'Intervju, research, brief och koncept.' },
    { id: 'bygge', namn: 'Bygge', val: 'sessioner', under: 'Digitala', text: 'Bygget i kundens repo med förhandsvisning bakom skydd. Redaktionellt pass och SEO hör hit.' },
    { id: 'kontroller', namn: 'Kontroller', val: 'lasare', under: 'kritik och provare', text: 'Mätningen är modellfri. Kritik och provare kör Runtimes profiler med läsarnas modell.' },
    { id: 'leverans', namn: 'Leverans', val: 'sessioner', under: 'Digitala', text: 'Prelaunch, kvalitetsbild och en färdig privat sida till dig.' },
    { id: 'lansering', namn: 'Lansering', val: 'sessioner', under: 'med ditt mandat', text: 'Lansering, sökkonsol och drift, bara med lanseringsmandat.' },
  ] },
  { namn: 'Motorn', under: 'Runtime-uppdrag', hp: [
    { id: 'forberedelse', namn: 'Förberedelse', val: 'runtime', roll: 'driver', under: 'driver, interaktiv', text: 'Rollerna driver och interaktiv förbereder uppdraget.' },
    { id: 'forgranskning', namn: 'Förgranskning', val: 'runtime', roll: 'preparation-review', text: 'Förberedelsen granskas innan uppdraget fryses.' },
    { id: 'genomforande', namn: 'Genomförande', val: 'runtime', roll: 'implementation', gren: 'diagnos vid fel', text: 'Uppdraget byggs. Faller något tar rollen diagnos över.' },
    { id: 'rgranskning', namn: 'Granskning', val: 'runtime', roll: 'review', text: 'Runtimes granskare läser kandidaten.' },
    { id: 'slutgranskning', namn: 'Slutgranskning', val: 'runtime', roll: 'final-review', text: 'Sista läsningen före integration.' },
    { id: 'integration', namn: 'Integration', val: 'du', under: 'skyddad', text: 'Skyddad integration med Runtimes kontroller. Ingen modell.' },
  ] },
  { namn: 'Bevakning', under: 'varje dag kl. 9', hp: [
    { id: 'omvarlden', namn: 'Omvärlden', val: 'du', under: 'källorna', text: 'Källorna som bevakningen läser.' },
    { id: 'bevakningen', namn: 'Bevakningen', val: 'bevakning', text: 'Intaget avgör om en modell behövs. Analys och granskning kör i så fall bevakningens modell.' },
    { id: 'aquarium', namn: 'Aquarium', val: 'du', under: 'läsvy', text: 'Lugn läsvy över vad som arbetar och väntar. Ingen modell.' },
  ] },
];
const VALORDNING = ['partner', 'sessioner', 'runtime', 'lasare', 'bevakning'];
const PROGRAMORDNING = ['claude_code', 'codex'];
const UTFORARNAMN = { claude: 'Claude', codex: 'Codex' };
const PROGRAMNAMN = { claude_egen: 'Claude Code', claude_runtime: 'Runtimes Claude Code', codex_egen: 'Codex', codex_runtime: 'Runtimes Codex' };
const kt = { data: null, fokus: null, vald: 'forbattringar', utkast: {}, sparar: null, besked: null };

function allaModeller() {  // namn för alla modeller som servern nämner
  const d = kt.data, ut = {};
  const lagg = (lista) => (lista || []).forEach((m) => { ut[m.id] = m.namn; });
  lagg(d.val.partner.erbjud); lagg(d.val.lasare.erbjud); lagg(d.val.runtime && d.val.runtime.erbjud); lagg(d.val.bevakning && d.val.bevakning.erbjud);
  for (const p of PROGRAMORDNING) lagg(d.val.sessioner.program[p].erbjud);
  return ut;
}
function modellnamn(id) { return id ? (allaModeller()[id] || id) : null; }
function vardetext(v) {  // "Opus 5.5 · high", "sessionen väljer" eller "okänt"; okänt blir aldrig ett påhittat värde
  if (!v || v.status === 'olasbar') return 'okänt';
  if (!v.modell) return v.status === 'sessionen' ? 'sessionen väljer' : 'okänt';
  return modellnamn(v.modell) + (v.anstrangning ? ' · ' + v.anstrangning : '');
}
function hallplatsvarde(h) {  // [text, ...fler rader] och raden under
  const d = kt.data;
  if (h.startvakt) {
    const s = d.startvakt;
    return { rader: [s.modell ? modellnamn(s.modell) + ' · ' + s.anstrangning : 'okänt'], under: 'startvakten, ' + (s.pa ? 'på' : 'av') };
  }
  if (h.val === 'sessioner') return { rader: ['din session'], under: h.under };
  const v = d.val[h.val];
  return { rader: [vardetext(v)], under: h.under || (v && v.utforare ? UTFORARNAMN[v.utforare] : '') };
}

async function visaFlodet() {
  const rot = $('del-flodet');
  if (!kt.data) rot.replaceChildren(flodeshuvud(), status('Läser valen…'));
  try { kt.data = await api('GET', '/api/arbetsplats/karta'); }
  catch (f) { rot.replaceChildren(flodeshuvud(), status('Valen kunde inte läsas: ' + f.message, 'fel')); return; }
  ritaFlodet();
}
function flodeshuvud() {
  const m = kt.data && kt.data.matning;
  return el('header', { class: 'del-huvud' }, el('h1', { id: 'flodet-rubrik', tabindex: '-1' }, 'Nortropics flöde'),
    el('p', { class: 'dampad' }, 'Fyra linjer, och vid varje hållplats modellen och ansträngningen som arbetar där. Varje hållplats följer ett av fem val. Klicka på ett val för att se vilka hållplatser det styr.'),
    kt.data ? el('p', { class: 'kl dampad' }, 'Läst ' + nar(kt.data.lasttid) + '. ' + (m ? 'Bara det som fungerade i mätningen ' + nar(m.matt) + ' erbjuds: ' +
      Object.entries(m.program).map(([p, v]) => (PROGRAMNAMN[p] || p) + ' ' + String(v || '?').replace(/^codex-cli /, '').replace(/ \(Claude Code\)$/, '')).join(', ') + '. ' : ''),
    el('button', { class: 'lank', type: 'button', onclick: () => visaFlodet() }, 'Läs om')) : null);
}
function ritaFlodet(fokusEfter) {
  const rot = $('del-flodet');
  rot.replaceChildren(flodeshuvud(),
    el('section', { class: 'fv-val', 'aria-label': 'De fem valen' }, VALORDNING.map(valkort)),
    el('section', { class: 'fv-karta', 'aria-label': 'Kartan' }, KARTLINJER.map(linje)),
    el('section', { id: 'fv-detalj', class: 'fv-detalj', 'aria-live': 'polite' }, detalj(kt.vald)),
    el('p', { class: 'kl dampad fv-fot' }, 'Fylld punkt: ett av dina val. Streckad: sessionen väljer. Grå: ingen modell. Romb: dina ord.'));
  if (fokusEfter) { const e = document.getElementById(fokusEfter); if (e) e.focus(); }
}

// ------------------------------------------------------------------ valen
function valrad(nyckel, etikett, v, erbjud, medNiva, program) {  // modell- och nivåmeny med egen Spara-knapp
  const u = kt.utkast[nyckel] || { modell: v.modell || '', anstrangning: v.anstrangning || '' };
  const m = erbjud.find((x) => x.id === u.modell);
  const nivaer = m ? m.nivaer : [];
  const satt = (andring) => { kt.utkast[nyckel] = Object.assign({}, u, andring); ritaFlodet('fv-spara-' + nyckel); };
  const mval = el('select', { 'aria-label': etikett + ', modell', onchange: (e) => {
    const ny = erbjud.find((x) => x.id === e.target.value);
    satt({ modell: e.target.value, anstrangning: ny && ny.nivaer.includes(u.anstrangning) ? u.anstrangning : (ny && medNiva ? '' : u.anstrangning) });
  } },
  nyckel === 'lasare' ? el('option', { value: '', text: 'sessionen väljer', selected: !u.modell }) : null,
  m || !u.modell ? null : el('option', { value: u.modell, text: modellnamn(u.modell) + ' (ej bevisad)', selected: true, disabled: true }),
  grupper(erbjud).map(([utf, lista]) => el('optgroup', { label: UTFORARNAMN[utf] }, lista.map((x) => el('option', { value: x.id, text: x.namn, selected: x.id === u.modell })))));
  const rad = el('div', { class: 'fv-varden' }, program ? el('span', { class: 'fv-program', text: etikett }) : null, mval);
  if (medNiva) {
    rad.append(el('select', { 'aria-label': etikett + ', ansträngning', disabled: !m, onchange: (e) => satt({ anstrangning: e.target.value }) },
      nivaer.includes(u.anstrangning) ? null : el('option', { value: '', text: u.anstrangning && m ? u.anstrangning + ' (ej bevisad)' : 'ansträngning', selected: true, disabled: true }),
      nivaer.map((n) => el('option', { value: n, text: n, selected: n === u.anstrangning }))));
  } else if (v.anstrangning || (m && m.nivaer.length)) rad.append(el('span', { class: 'fv-fast liten', title: 'Fast i Runtimes läsarprofil', text: (m && m.nivaer[0]) || v.anstrangning }));
  const andrad = !!kt.utkast[nyckel] && (u.modell !== (v.modell || '') || (medNiva && u.anstrangning !== (v.anstrangning || '')));
  const klar = !medNiva || (m && nivaer.includes(u.anstrangning)) || (nyckel === 'lasare');
  if (andrad || kt.sparar === nyckel) rad.append(el('button', { type: 'button', id: 'fv-spara-' + nyckel, class: 'knapp primar fv-spara', disabled: !klar || kt.sparar === nyckel,
    onclick: () => sparaVal(nyckel, u) }, kt.sparar === nyckel ? 'Sparar…' : 'Spara'));
  if (andrad) rad.append(el('button', { type: 'button', class: 'lank', onclick: () => { delete kt.utkast[nyckel]; ritaFlodet('fv-kort-' + (nyckel === 'claude_code' || nyckel === 'codex' ? 'sessioner' : nyckel)); } }, 'Ångra'));
  const delar = [rad];
  if (v.bevisad === false) delar.push(status('Nuvarande värde har inte fungerat i senaste mätningen.', 'varning'));
  if (kt.besked && kt.besked.val === nyckel) delar.push(el('p', { class: 'fv-besked ' + (kt.besked.fel ? 'fel' : ''), role: 'status', text: kt.besked.text }));
  return delar;
}
// Runtimes automatiska aktivering (Runtimes D040): läget ur Runtimes statusfil, i Johnnys ord
const AKTIVERING = { none: 'Valet väntar på Runtimes nästa titt.', in_effect: 'Gäller.', waiting: 'Väntar tills Runtime är ledigt', refused: 'Aktiveras inte',
  activating: 'Aktiveras nu.', activated: 'Aktiverades', restored: 'Den nya versionen startade inte, så den förra kör igen.',
  failed: 'Bytet misslyckades', interrupted: 'Ett byte avbröts innan det rapporterades och behöver ses över.' };
const SKAL = [[/AP10 watch run is in progress/, 'bevakningen kör just nu'], [/less than 20 minutes away/, 'bevakningen kör inom 20 minuter'],
  [/work is in progress in the engine|work started in the engine/, 'arbete pågår i Runtime'], [/web profile run is in progress/, 'en webbprofil kör'],
  [/running service is not the recorded one/, 'Runtimes tjänst svarar inte som väntat'],
  [/did not work in the measurement/, 'valet har inte fungerat i mätningen av Runtimes egna program'],
  [/no way back/, 'det finns ingen säker väg tillbaka just nu']];
function skaltext(s) { for (const [re, t] of SKAL) if (re.test(s || '')) return t; return s; }
function aktiveringsrader(v) {
  const a = v.aktivering, ut = [];
  if (v.onskat) ut.push(el('p', { class: 'fv-var fv-onskat', text: 'Önskat: ' + vardetext(v.onskat) + '.' }));
  if (!a || !a.igang) {
    if (v.onskat) ut.push(status('Aktiveraren är inte igång, så valet väntar. Johnny startar den en gång (Runtimes övergång 19 och agent install).', 'varning'));
    return ut;
  }
  // en status om ett tidigare önskemål säger inget om det som nyss sparades: Runtime har inte tittat än
  if (v.onskat && a.onskemal !== v.onskemal_id) { ut.push(el('p', { class: 'fv-besked', role: 'status', text: AKTIVERING.none })); return ut; }
  const problem = ['refused', 'restored', 'failed', 'interrupted'].includes(a.lage);
  if (!v.onskat && !problem) {
    if (a.lage === 'in_effect' && a.aktiverad) ut.push(el('p', { class: 'fv-var', text: 'Aktiverades ' + nar(a.aktiverad) + '.' }));
    return ut;
  }
  let text = AKTIVERING[a.lage] || 'Läget är okänt.';
  if (a.lage === 'waiting' || a.lage === 'refused' || a.lage === 'failed') text += a.skal ? ': ' + skaltext(a.skal) + '.' : '.';
  if (a.lage === 'activated') text += ' ' + nar(a.aktiverad || a.tid) + '.';
  ut.push(el('p', { class: 'fv-besked' + (problem ? ' fel' : ''), role: 'status', text: text + ' Senast kontrollerat ' + nar(a.tid) + '.' }));
  return ut;
}
function grupper(lista) {
  const ut = [];
  for (const utf of ['claude', 'codex']) { const l = lista.filter((x) => x.utforare === utf); if (l.length) ut.push([utf, l]); }
  return ut;
}
function valkort(k) {
  const v = kt.data.val[k];
  const streckad = k === 'sessioner' ? false : !v.modell;
  const kort = el('div', { class: 'fv-kort' + (kt.fokus === k ? ' markerad' : ''), 'data-val': k });
  kort.append(el('button', { type: 'button', id: 'fv-kort-' + k, class: 'fv-kortnamn', 'aria-pressed': String(kt.fokus === k),
    title: 'Visa hållplatserna som följer valet', onclick: () => { kt.fokus = kt.fokus === k ? null : k; ritaFlodet('fv-kort-' + k); } },
  el('span', { class: 'fv-prick' + (streckad ? ' streck' : '') }), v.namn));
  if (k === 'sessioner') {
    for (const p of PROGRAMORDNING) {
      const pv = v.program[p];
      if (v.valbar && pv.status !== 'olasbar') kort.append(...valrad(p, pv.namn, pv, pv.erbjud || [], true, true));
      else kort.append(el('div', { class: 'fv-varden' }, el('span', { class: 'fv-program', text: pv.namn }), el('span', { class: 'fv-varde', text: vardetext(pv) })));
      if (pv.skal) kort.append(status(pv.namn + ': ' + pv.skal, 'varning'));
    }
  } else if (v.valbar) {
    // Runtime och bevakningen utgår från det önskade valet när ett väntar på att aktiveras
    const bas = v.onskat ? Object.assign({}, v, { modell: v.onskat.modell, anstrangning: v.onskat.anstrangning, bevisad: null }) : v;
    kort.append(...valrad(k, v.namn, bas, v.erbjud || [], k !== 'lasare'));
    if (k === 'runtime' || k === 'bevakning') kort.append(...aktiveringsrader(v));
  } else {
    kort.append(el('div', { class: 'fv-varde', text: vardetext(v) }));
    if (v.bevisad === false) kort.append(status('Har inte fungerat i senaste mätningen.', 'varning'));
  }
  kort.append(el('p', { class: 'fv-var', text: 'I dag: ' + v.var }));
  if (v.skal) kort.append(status(v.skal, 'varning'));
  if (!v.valbar && v.varfor_inte) kort.append(el('p', { class: 'fv-var', text: v.varfor_inte }));
  return kort;
}
async function sparaVal(nyckel, u) {
  kt.sparar = nyckel; kt.besked = null; ritaFlodet('fv-spara-' + nyckel);
  try {
    kt.data = await api('POST', '/api/arbetsplats/karta', { val: nyckel, modell: u.modell || null, anstrangning: u.anstrangning || null });
    delete kt.utkast[nyckel];
    const v = nyckel === 'claude_code' || nyckel === 'codex' ? kt.data.val.sessioner.program[nyckel] : kt.data.val[nyckel];
    const runtimeval = nyckel === 'runtime' || nyckel === 'bevakning';
    kt.besked = { val: nyckel, text: 'Sparat ' + nar(new Date().toISOString()) + ': ' + vardetext(runtimeval && v.onskat ? v.onskat : v) + '.' +
      (runtimeval ? (v.onskat ? ' Bytet aktiveras av sig självt när Runtime är ledigt.' : ' Det kör redan.') : '') };
  } catch (f) { kt.besked = { val: nyckel, fel: true, text: 'Inte sparat: ' + f.message }; }
  kt.sparar = null;
  ritaFlodet('fv-kort-' + (nyckel === 'claude_code' || nyckel === 'codex' ? 'sessioner' : nyckel));
}

// ------------------------------------------------------------------ kartan
function linje(l) {
  const p = kt.data.val.sessioner.program;
  const sessioner = l.hp.some((h) => h.val === 'sessioner')
    ? el('span', { class: 'fv-linjeval', 'data-val': 'sessioner' }, el('span', { class: 'fv-prick' }), 'din session: ',
      PROGRAMORDNING.map((n, i) => [i ? ' · ' : '', el('b', { text: vardetext(p[n]) }), ' (' + p[n].namn + ')']).flat())
    : null;
  return el('div', { class: 'fv-linje' },
    el('p', { class: 'fv-linjenamn' }, l.namn, el('small', { text: l.under }), sessioner),
    el('div', { class: 'fv-rad' }, el('div', { class: 'fv-spar' }, l.hp.map(hallplats))));
}
function hallplats(h) {
  const valbar = h.val in kt.data.val;
  const v = valbar ? kt.data.val[h.val] : null;
  const form = !valbar ? h.val : (h.val === 'sessioner' || v.modell || h.startvakt ? 'val' : 'streck');
  const b = el('button', { type: 'button', class: 'fv-hp fv-' + form + (kt.fokus && h.val !== kt.fokus ? ' dimmad' : ''), 'data-id': h.id,
    'data-val': h.val, 'aria-pressed': String(kt.vald === h.id), onclick: () => { kt.vald = h.id; ritaFlodet(); document.querySelector('.fv-hp[data-id="' + h.id + '"]').focus(); } });
  const vt = valbar ? hallplatsvarde(h) : null;
  b.append(el('span', { class: 'fv-namn', text: h.namn }), el('span', { class: 'fv-punkt' }),
    el('span', { class: 'fv-modell' }, vt ? vt.rader.map((r) => el('b', { text: r })) : null, vt ? vt.under : h.under,
      h.gren ? el('span', { class: 'fv-gren', text: '↳ ' + h.gren }) : null));
  return b;
}
function detalj(id) {
  const h = KARTLINJER.flatMap((l) => l.hp).find((x) => x.id === id);
  if (!h) return null;
  const delar = [el('h2', { text: h.namn }), el('p', { text: h.text })];
  if (h.val in kt.data.val) {
    const v = kt.data.val[h.val];
    const vt = hallplatsvarde(h);
    const rader = h.val === 'sessioner'
      ? PROGRAMORDNING.map((p) => [v.program[p].namn, vardetext(v.program[p])])
      : [['I dag', vt.rader[0] + (h.startvakt ? ' (' + vt.under + ')' : '')]];
    rader.push(['Följer valet', v.namn], ['Så väljs det', v.var]);
    if (h.roll && v.roller && v.roller[h.roll]) rader.push(['Rollen', h.roll + ' · ' + (UTFORARNAMN[v.roller[h.roll]] || v.roller[h.roll])]);
    if (h.val === 'runtime' && v.config) rader.push(['Release', 'konfiguration ' + v.config]);
    delar.push(el('dl', null, rader.map(([dt, dd]) => [el('dt', { text: dt }), el('dd', { text: dd })]).flat()));
  }
  return delar;
}
