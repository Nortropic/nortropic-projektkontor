'use strict';
// Nortropics arbetsplats: huvudnavigationen (Hem, Kontoret, Kundstart, Förbättringar) runt partnerns samtalsyta.
// Allt här läser: ingen vy anropar en modell, skriver i journalen eller startar något. Innehåll renderas som DOM-noder
// med textContent (el() i app.js). Adressen bär bara del och objekt-id, aldrig privata texter eller nycklar; i
// webbläsaren sparas bara senaste adress per del och om Kontorets lista är dold (samtalsytans nycklar: se app.js).

const DELAR = { hem: 'Hem', kontoret: 'Kontoret', kundstart: 'Kundstart', forbattringar: 'Förbättringar' };
const as = { del: null, vag: null, forsta: true, kontorTimer: null, kontorData: null, kontorGrupp: null, kundstart: null };
const KUNDSTART_PROV = 'http://127.0.0.1:3131';

// ------------------------------------------------------------------ hjälp
function alder(iso) {
  if (!iso) return 'okänd tid';
  const s = Math.round((Date.now() - new Date(iso).getTime()) / 1000);
  if (!isFinite(s)) return 'okänd tid';
  if (s < 60) return 'nyss';
  if (s < 3600) return 'för ' + Math.round(s / 60) + ' min sedan';
  if (s < 86400) return 'för ' + Math.round(s / 3600) + ' h sedan';
  return 'för ' + Math.round(s / 86400) + ' dygn sedan';
}
function nar(iso) {  // en händelsetid som går att läsa: i dag 12:07, i går 09:15, 27 sep 10:58 (sekunderna i title)
  if (!iso) return 'okänd tid';
  const d = new Date(iso);
  if (isNaN(d)) return 'okänd tid';
  const hm = d.toLocaleTimeString('sv-SE', { hour: '2-digit', minute: '2-digit' });
  const idag = new Date(); const igar = new Date(Date.now() - 864e5);
  if (d.toDateString() === idag.toDateString()) return 'i dag ' + hm;
  if (d.toDateString() === igar.toDateString()) return 'i går ' + hm;
  return d.toLocaleDateString('sv-SE', { day: 'numeric', month: 'short' }).replace('.', '') + ' ' + hm;
}
function tidEl(iso) { return el('time', { datetime: iso || '', title: iso ? new Date(iso).toLocaleString('sv-SE') : null, text: nar(iso) }); }
function stor(t) { return t ? t.charAt(0).toUpperCase() + t.slice(1) : t; }
function dag(iso) {  // ett datum utan klockslag (Arkivet) visas som datum, aldrig med påhittad tid
  if (!iso) return 'odaterad';
  return /^\d{4}-\d{2}-\d{2}$/.test(iso) ? iso : tid(iso);
}
function lank(href, text, attrs) { return el('a', Object.assign({ href, 'data-nav': true }, attrs || {}), text); }
function status(text, klass) { return el('p', { class: 'status ' + (klass || ''), role: 'status', text }); }
function objektlank(ref) { return '/kontoret/objekt/' + encodeURIComponent(ref); }
function beslutIText(text) {  // beslutsid inom parentes i en ägarrad, t.ex. "(KUNDSTART-20260927)"
  const m = String(text || '').match(/\(([A-ZÅÄÖ0-9][A-ZÅÄÖ0-9-]{3,119})(?:,\s*([A-ZÅÄÖ0-9][A-ZÅÄÖ0-9-]{3,119}))*\)\s*$/);
  if (!m) return [];
  return String(text).slice(String(text).lastIndexOf('(') + 1, -1).split(',').map((x) => x.trim()).filter((x) => /^[A-ZÅÄÖ0-9][A-ZÅÄÖ0-9-]{3,119}$/.test(x));
}
function delaTitel(t) {  // "ID — rubrik" ur beslutsloggens rubrikrad
  const i = String(t || '').indexOf(' — ');
  return i > 0 ? [t.slice(0, i), t.slice(i + 3)] : [null, t];
}
function beslutsrad(ref, titel, datum) {
  const [id, rubrik] = delaTitel(titel);
  return el('li', null, el('span', { text: stor(rubrik) }), el('div', { class: 'kl dampad' }, lank(objektlank(ref), id || ref), datum ? ' · ' + datum : ''));
}
function utanBeslut(text) { return beslutIText(text).length ? String(text).slice(0, String(text).lastIndexOf('(')).trim() : text; }
function resoneraOm(refs) {  // lägger objekten i nästa inspels sammanhang och öppnar ett nytt samtal; inget skickas
  const u = las('utkast:ny', { text: '', bilagor: [] });
  const fore = Array.isArray(u.kontext) ? u.kontext : [];
  const nya = refs.filter((r) => !fore.some((x) => x.ref === r.ref));
  u.kontext = fore.concat(nya).slice(0, 6);
  skriv('utkast:ny', u);
  navigera('/forbattringar/ny');
}

// ------------------------------------------------------------------ adresser
function tolka(vag) {
  let m;
  if (vag === '/' || vag === '') return { del: 'hem' };
  if (vag === '/kontoret') return { del: 'kontoret' };
  if (vag === '/kontoret/presentation') return { del: 'kontoret', presentation: true };
  if ((m = vag.match(/^\/kontoret\/objekt\/([^/]+)$/))) return { del: 'kontoret', objekt: decodeURIComponent(m[1]) };
  if (vag === '/kundstart') return { del: 'kundstart' };
  if (vag === '/forbattringar') return { del: 'forbattringar', trad: null };
  if ((m = vag.match(/^\/forbattringar\/(ny|t_[A-Za-z0-9]+)$/))) return { del: 'forbattringar', trad: m[1] };
  return { del: 'hem', okand: vag };
}
function satAdress(vag, ersatt) {  // används av samtalsytan vid trådbyte; ritar inget om
  if (location.pathname === vag) return;
  if (ersatt) history.replaceState(null, '', vag); else history.pushState(null, '', vag);
  as.vag = vag; skriv('arbetsplats:senast:' + tolka(vag).del, vag);
}
function navigera(vag, ersatt) {
  if (location.pathname + location.hash === vag && !ersatt) { visa(); return; }
  if (ersatt) history.replaceState(null, '', vag); else history.pushState(null, '', vag);
  visa();
}
function forbattringarSyns() { return as.del === 'forbattringar' && !$('app').hidden; }
window.addEventListener('popstate', () => visa());
document.addEventListener('click', (e) => {
  const a = e.target.closest && e.target.closest('a[data-nav]');
  if (!a || e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
  const url = new URL(a.href, location.href);
  if (url.origin !== location.origin) return;
  e.preventDefault();
  navigera(url.pathname);
});
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape' && document.body.classList.contains('presentation') && !document.fullscreenElement) navigera('/kontoret');
});

async function visa() {
  const r = tolka(location.pathname);
  const fore = as.del;
  const ny = r.del;
  if (fore === 'forbattringar' && ny !== 'forbattringar') lamnaForbattringar();
  if (fore === 'kontoret' && (ny !== 'kontoret' || !!r.presentation !== as.presentation)) lamnaKontoret();
  as.del = ny; as.presentation = !!r.presentation;
  document.body.dataset.del = ny;
  document.body.classList.toggle('presentation', !!r.presentation);
  $('toppfalt').hidden = !!r.presentation;  // presentationen tonar bort navigationen helt
  for (const d of ['hem', 'kontoret', 'kundstart']) $('del-' + d).hidden = d !== ny;
  $('app').hidden = ny !== 'forbattringar';
  for (const a of document.querySelectorAll('.huvudnav a')) {
    if (a.dataset.del === ny) a.setAttribute('aria-current', 'page'); else a.removeAttribute('aria-current');
  }
  document.title = (r.presentation ? 'Presentation · ' : '') + DELAR[ny] + ' · Nortropic';
  skriv('arbetsplats:senast:' + ny, location.pathname);
  const flyttaFokus = !as.forsta;
  as.forsta = false;
  if (ny === 'hem') await visaHem(r);
  else if (ny === 'kontoret') await visaKontoret(r);
  else if (ny === 'kundstart') await visaKundstart();
  else await visaForbattringar(r.trad);
  if (flyttaFokus) {  // efter navigering: fokus till delens rubrik (eller samtalsrutan), så att läsaren vet var den är
    const mal = ny === 'forbattringar' ? $('tradtitel') : document.querySelector('#del-' + ny + ' h1');
    if (mal) { if (!mal.hasAttribute('tabindex')) mal.setAttribute('tabindex', '-1'); mal.focus({ preventScroll: false }); }
  }
}

// ------------------------------------------------------------------ Hem
function visaHem(r) {  // bara hälsningen (HEM-RUTOR-20260929): Hem läser ingenting
  $('del-hem').replaceChildren(el('header', { class: 'del-huvud' },
    el('h1', { id: 'hem-rubrik', tabindex: '-1' }, halsning()),
    r.okand ? status('Adressen ' + r.okand + ' finns inte; du är på Hem.', 'fel') : null));
}
function sektion(id, rubrik, ...barn) { return el('section', { class: 'block', 'aria-labelledby': id }, el('h2', { id }, rubrik), ...barn); }
function bordrad(x) {
  const beslut = beslutIText(x.text);
  return el('li', { class: 'bordrad' }, el('span', null, utanBeslut(x.text)),
    el('span', { class: 'dampad kl' }, (x.since ? 'sedan ' + dag(x.since) + ' · ' : '') + x.basis,
      ...beslut.map((b) => [' · ', lank(objektlank('beslut:' + b), b)]).flat()));
}

// ------------------------------------------------------------------ Kontoret
const PLATS_GRUPP = { 'p-arkivet': 'levererat', 'p-verkstaden': 'uppdrag', 'p-granskningen': 'uppdrag', 'p-utkiken': 'bevakning',
  'p-bordet': 'behover', 'p-maskinrummet': 'kallor', 'p-interaktivt': 'overlamningar', 'p-kallor': 'kallor' };
const GRUPPER = [['uppdrag', 'Uppdrag i Runtime'], ['overlamningar', 'Överlämningar'], ['levererat', 'Levererat'], ['behover', 'Behöver dig'], ['bevakning', 'Bevakningen'], ['kallor', 'Källor och tider']];
function lamnaKontoret() {
  clearTimeout(as.kontorTimer); as.kontorTimer = null; as.kontorByggd = false;
  const ram = document.getElementById('aquarium');
  if (ram) ram.remove();  // ingen dold Aquarium-rendering eller omladdning när Kontoret inte syns
  if (document.fullscreenElement) document.exitFullscreen().catch(() => {});
}
async function visaKontoret(r) {
  const rot = $('del-kontoret');
  if (as.kontorByggd && !r.presentation && document.getElementById('kontor-lista')) {  // byte av objekt: scenen står kvar
    as.kontorObjekt = r.objekt || null;
    if (r.objekt) await visaObjekt(r.objekt);
    else { const o = document.getElementById('kontor-objekt'); if (o) { o.hidden = true; o.replaceChildren(); } }
    return;
  }
  const ram = document.getElementById('aquarium') || el('iframe', { id: 'aquarium', src: '/kontoret/aquarium',
    title: 'Aquarium: kontorets arbetsvärld (samma uppgifter finns som lista bredvid)', referrerpolicy: 'no-referrer' });
  ram.addEventListener('load', () => kopplaAquarium(ram), { once: false });
  const scen = el('div', { class: 'kontor-scen' }, ram);
  if (r.presentation) {
    rot.replaceChildren(el('h1', { id: 'kontor-rubrik', class: 'dold', tabindex: '-1' }, 'Kontoret, presentation'), scen,
      el('div', { class: 'presentationsverktyg', role: 'group', 'aria-label': 'Presentation' },
        document.fullscreenEnabled ? el('button', { type: 'button', class: 'knapp', onclick: () => document.documentElement.requestFullscreen().catch(() => {}) }, 'Helskärm') : null,
        lank('/kontoret', 'Avsluta presentation (Esc)', { class: 'knapp' })));
    return;
  }
  const lista = el('div', { id: 'kontor-lista', class: 'kontor-lista' });
  rot.replaceChildren(
    el('div', { class: 'kontor' },
      el('div', { class: 'kontor-vanster' },
        el('header', { class: 'del-huvud kontor-huvud' }, el('h1', { id: 'kontor-rubrik', tabindex: '-1' }, 'Kontoret'),
          el('p', { class: 'dampad' }, 'Aquarium visar kontorets arbete som en arbetsvärld. Klicka på en plats, eller använd listan.'),
          el('div', { class: 'knapprad' },
            el('button', { type: 'button', class: 'knapp listvaxel', 'aria-pressed': String(!las('arbetsplats:lista-dold', false)), 'aria-controls': 'kontor-hoger',
              onclick: (e) => { const dold = !las('arbetsplats:lista-dold', false); skriv('arbetsplats:lista-dold', dold); $('del-kontoret').classList.toggle('lista-dold', dold); e.currentTarget.setAttribute('aria-pressed', String(!dold)); e.currentTarget.textContent = dold ? 'Visa listan' : 'Dölj listan'; } },
              las('arbetsplats:lista-dold', false) ? 'Visa listan' : 'Dölj listan'),
            lank('/kontoret/presentation', 'Presentation', { class: 'knapp' }))),
        scen,
        lank('/kontoret/presentation', 'Visa Aquarium i helskärm', { class: 'knapp primar mobil-helskarm' })),
      el('aside', { id: 'kontor-hoger', class: 'kontor-hoger', 'aria-label': 'Arbetet i listform' }, lista)));
  rot.classList.toggle('lista-dold', !!las('arbetsplats:lista-dold', false));
  as.kontorByggd = true;
  await laddaKontoret(r);
}
function valjGrupp(id, fokus) {
  as.kontorGrupp = id;
  for (const k of document.querySelectorAll('.flik')) k.setAttribute('aria-pressed', String(k.dataset.grupp === id));
  const panel = document.getElementById('kontor-grupp');
  if (panel) { panel.setAttribute('aria-label', (GRUPPER.find((g) => g[0] === id) || [0, ''])[1]); panel.replaceChildren(gruppinnehall(id, (as.kontorData || {}).projektion, as.kontorData || {})); }
  if (fokus) { const k = document.querySelector('.flik[aria-pressed="true"]'); if (k) k.focus(); }
}
function kopplaAquarium(ram) {  // samma ursprung: en klickad plats i Aquarium öppnar samma grupp i listan
  try {
    const w = ram.contentWindow;
    const synka = () => { const g = PLATS_GRUPP[(w.location.hash || '').slice(1)]; if (g && !as.presentation) valjGrupp(g, false); };
    w.addEventListener('hashchange', synka);
  } catch { /* sidan är inte läsbar (t.ex. 503-text); listan fungerar ändå */ }
}
async function laddaKontoret(r, periodisk) {  // Aquarium-sidan laddar själv om när läsningen är ny; listan följer efter
  clearTimeout(as.kontorTimer);
  let d;
  try { d = await api('GET', '/api/arbetsplats/kontoret'); }
  catch (f) { d = { status: 'fel', fel: f.message }; }
  if (as.del !== 'kontoret' || as.presentation) return;
  const nyckel = (x) => (x ? x.status + '|' + (x.projektion ? x.projektion.read_at : '') + '|' + JSON.stringify(x.overlamningar || []) : '');
  const andrad = nyckel(d) !== nyckel(as.kontorData);
  as.kontorData = d;
  if (!periodisk) {
    as.kontorObjekt = r && r.objekt ? r.objekt : null;
    ritaKontorLista();
    if (as.kontorObjekt) await visaObjekt(as.kontorObjekt);
  } else if (andrad) ritaKontorGrupp();  // bara läsningens delar; ett öppet objekt och dess fokus lämnas orörda
  as.kontorTimer = setTimeout(() => { if (as.del === 'kontoret' && !as.presentation) laddaKontoret(null, true); },
    d.status === 'laser' || d.status === 'ingen_lasning' ? 4000 : 60000);
}
function ritaKontorGrupp() {
  const d = as.kontorData || {};
  const huvud = document.querySelector('#kontor-lista .lista-huvud');
  const panel = document.getElementById('kontor-grupp');
  if (!huvud || !panel) { ritaKontorLista(); return; }
  const hadeFokus = panel.contains(document.activeElement);
  huvud.replaceWith(listhuvud(d));
  panel.replaceChildren(gruppinnehall(as.kontorGrupp || 'uppdrag', d.projektion, d));
  if (hadeFokus) { panel.setAttribute('tabindex', '-1'); panel.focus({ preventScroll: true }); }
}
function listhuvud(d) {
  const p = d.projektion;
  return el('div', { class: 'lista-huvud' }, el('h2', null, 'Arbetet i listform'),
    p ? el('p', { class: 'kl dampad', text: 'Läst ' + tid(p.read_at) + ' (' + alder(p.read_at) + '). Samma visningssäkra uppgifter som Aquarium.' })
      : status(d.status === 'laser' || d.status === 'ingen_lasning' ? 'Läser kontorets källor…' : 'Kontorets läsning är inte tillgänglig just nu' + (d.senaste_fel ? ' (senaste försök ' + tid(d.senaste_fel) + ')' : '') + '. Läget är okänt, inte tomt.', d.status === 'laser' ? '' : 'varning'));
}
function ritaKontorLista() {
  const rot = document.getElementById('kontor-lista');
  if (!rot) return;
  const d = as.kontorData || {};
  const p = d.projektion;
  const huvud = listhuvud(d);
  const vald = as.kontorGrupp || 'uppdrag';
  const flikar = el('div', { class: 'flikar', role: 'group', 'aria-label': 'Visa plats' }, GRUPPER.map(([id, namn]) =>
    el('button', { type: 'button', 'aria-pressed': String(vald === id), 'aria-controls': 'kontor-grupp', class: 'flik', 'data-grupp': id,
      onclick: () => valjGrupp(id, true) }, namn)));
  const panel = el('section', { id: 'kontor-grupp', class: 'flikpanel', 'aria-label': (GRUPPER.find((g) => g[0] === vald) || [0, ''])[1] }, gruppinnehall(vald, p, d));
  const objekt = el('div', { id: 'kontor-objekt', class: 'objekt', hidden: true });
  rot.replaceChildren(huvud, objekt, flikar, panel);
}
function uppdragsrad(x, lage) {
  return el('li', null, lank(objektlank('uppdrag:' + x.task), x.title || x.task),
    el('div', { class: 'kl dampad', text: x.task + ' · ' + (lage === 'arbetar' ? (x.step || 'steg') + ' · ' + (x.state || '') + ' · utförare ' + (x.executor || 'ej belagd') : 'vilar sedan ' + tid(x.since)) + (x.title_status && x.title_status !== 'läst' ? ' · rubrik ' + x.title_status : '') }));
}
function gruppinnehall(g, p, d) {
  if (g === 'overlamningar') {
    const o = d.overlamningar || [];
    return o.length ? el('ul', { class: 'lista' }, o.map((x) => el('li', null, lank(objektlank(x.id), x.rubrik || x.id),
      el('div', { class: 'kl dampad', text: x.id + ' · ' + (MOTTAGARNAMN[x.mottagare] || x.mottagare) + ' · ' + (OVLTEXT[x.status] || x.status) + ' ' + tid(x.uppdaterad || x.lamnad) })))) : el('p', { text: 'Inga överlämningar från partnern ännu.' });
  }
  if (!p) return status('Den här delen bygger på Aquariums läsning, som inte finns just nu.', 'varning');
  const src = (namn) => (p.sources || {})[namn] || {};
  const okant = (namn) => src(namn).status && src(namn).status !== 'ok' ? status(src(namn).title + ' gick inte att läsa: läget är okänt.', 'varning') : null;
  if (g === 'behover') {
    const rader = (p.agarens_bord && p.agarens_bord.items) || [];
    return el('div', null, rader.length ? el('ul', { class: 'lista' }, rader.map((x) => {
      const b = beslutIText(x.text);
      return el('li', null, el('span', null, utanBeslut(x.text)), el('div', { class: 'kl dampad' }, x.kind + ' · ' + x.basis + (x.since ? ' · sedan ' + dag(x.since) : ''), ...b.map((id) => [' · ', lank(objektlank('beslut:' + id), id)]).flat()));
    })) : el('p', { text: 'Inget väntar på dig enligt de lästa källorna.' }), okant('office'), okant('questions'), okant('watch'));
  }
  if (g === 'uppdrag') {
    const v = p.verkstaden || {};
    if (v.status && v.status !== 'ok') return status('Runtimes motor gick inte att läsa: uppdragens läge är okänt.', 'varning');
    return el('div', null, el('h3', { class: 'grupp' }, 'Arbetar (' + (v.items || []).length + ')'),
      (v.items || []).length ? el('ul', { class: 'lista' }, v.items.map((x) => uppdragsrad(x, 'arbetar'))) : el('p', { class: 'dampad', text: 'Inget arbete som motorn visar som pågående. Interaktiva sessioner observeras inte.' }),
      el('h3', { class: 'grupp' }, 'Vilar (' + (v.parked || []).length + ')'), el('ul', { class: 'lista' }, (v.parked || []).map((x) => uppdragsrad(x, 'vilar'))));
  }
  if (g === 'levererat') {
    const a = p.arkivet || {};
    return (a.items || []).length ? el('ul', { class: 'lista' }, a.items.map((x) => el('li', null,
      /^beslutsloggen /.test(x.basis) ? lank(objektlank('beslut:' + x.basis.split(' ')[1].replace(/,$/, '')), x.title) : el('span', { text: x.title }),
      el('div', { class: 'kl dampad', text: dag(x.date) + ' · ' + x.basis })))) : (okant('office') || el('p', { text: 'Inga levererade åtaganden i de lästa källorna.' }));
  }
  if (g === 'bevakning') {
    const u = p.utkiken || {};
    if (u.status && u.status !== 'ok') return status('Bevakningen gick inte att läsa: läget är okänt.', 'varning');
    return el('ul', { class: 'lista' },
      el('li', null, 'Schema: ' + (u.schedule || 'okänt')),
      el('li', null, 'Nästa planerade omgång: ' + (u.next_planned ? tid(u.next_planned) : 'okänd') + ' (planerad, inte genomförd)'),
      el('li', null, 'Senaste start: ' + ((u.starts || [])[0] ? tid(u.starts[0]) : 'okänd')),
      el('li', null, 'Senaste rapport: ' + (u.latest ? tid(u.latest.at) + ' · ' + u.latest.outcome : 'ingen')),
      el('li', null, 'Senast granskade besked: ' + (u.reviewed ? tid(u.reviewed.at) + ' · ' + u.reviewed.decision + (u.reviewed.older_than_a_day ? ' · äldre än ett dygn' : '') : 'inget')));
  }
  return el('ul', { class: 'lista' }, Object.entries(p.sources || {}).map(([k, s]) => el('li', null, s.title + ': ' + (s.status === 'ok' ? 'läst ' + tid(s.read_at) : 'gick inte att läsa'),
    el('div', { class: 'kl dampad', text: 'räknas som inaktuell efter ' + Math.round((s.stale_after_seconds || 0) / 60) + ' min' + (s.status === 'ok' && (Date.now() - new Date(s.read_at).getTime()) / 1000 > s.stale_after_seconds ? ' · INAKTUELL nu' : '') }))),
    el('li', null, 'Revisioner: kontorets main ' + ((p.revisions || {}).office_main || '?') + ', Runtime ' + ((p.revisions || {}).runtime || '?') + ', konfiguration ' + ((p.revisions || {}).config || '?')));
}
async function visaObjekt(ref) {
  const rot = document.getElementById('kontor-objekt');
  if (!rot) return;
  rot.hidden = false;
  rot.replaceChildren(status('Öppnar ' + ref + '…'));
  let o;
  try { o = await api('GET', '/api/arbetsplats/objekt?ref=' + encodeURIComponent(ref)); }
  catch (f) { rot.replaceChildren(el('h2', { tabindex: '-1' }, ref), status('Objektet kunde inte öppnas: ' + f.message, 'fel'), lank('/kontoret', 'Stäng')); return; }
  const delar = [el('div', { class: 'objekt-huvud' }, el('span', { class: 'etikett', text: OBJEKTSLAG[o.typ] || o.typ }), lank('/kontoret', 'Stäng', { class: 'stang', 'aria-label': 'Stäng objektet' })),
    el('h2', { id: 'objekt-rubrik', tabindex: '-1' }, o.typ === 'beslut' ? stor(delaTitel(o.titel)[1]) : o.titel)];
  if (o.typ === 'overlamning') {
    const nar = { lamnad: o.lamnad }; for (const h of o.historik) nar[h.status] = h.tid || h.kvitterad;
    delar.push(el('div', { class: 'tidslinje' }, OVLSTATUS.map((s) => el('span', { class: 'chip ' + (nar[s] ? 'ok' : ''), text: OVLTEXT[s] + (nar[s] ? ' ' + tid(nar[s]) : '') }))));
    delar.push(el('p', { class: 'kl', text: o.ref + ' · mottagare ' + (MOTTAGARNAMN[o.mottagare] || o.mottagare) + ' · status ' + (OVLTEXT[o.status] || o.status) }));
    const s = starttext(o.start, o.status); if (s) delar.push(el('p', { text: s }));
    const lev = o.historik.filter((h) => h.bevis);
    for (const h of lev) delar.push(el('p', null, (OVLTEXT[h.status] || h.status) + ' av ' + (h.av || 'okänd') + ': ', el('span', { class: 'bevis', text: h.bevis })));
    if (!lev.length) delar.push(el('p', { class: 'dampad', text: 'Ingen leverans är kvitterad ännu. Resultatet syns här när mottagaren kvitterar det med ett bevis (PR eller commit).' }));
    if (o.bestalld_i) delar.push(el('p', null, 'Beställd i tråden ', lank('/forbattringar/' + o.bestalld_i.id, '«' + (o.bestalld_i.titel || o.bestalld_i.id) + '»'), '.'));
    delar.push(el('p', { class: 'kl dampad', text: 'Paketet: ' + (o.paket || 'okänt') + (o.ap06 ? ' · AP-06-utkast: ' + o.ap06.status : '') }));
  } else if (o.typ === 'beslut') {
    delar.push(el('p', { class: 'kl', text: (delaTitel(o.titel)[0] || o.ref) + ' · kontorets beslutslogg på main' + (o.datum ? ' · ' + o.datum : '') }));
    const text = el('div', { class: 'kalltext' }, status('Läser posten…'));
    delar.push(text);
    api('GET', '/api/kalla?id=' + encodeURIComponent(o.kallor[0].id) + '&omkrets=0').then((k) => {
      const d = k.sammanhang && k.sammanhang.find((g) => g.denna);
      const original = (d && d.text) || k.text || '';
      const utanRubrik = original.replace(/^##[^\n]*\n+/, '');  // rubriken står redan ovanför
      text.replaceChildren(markdown(utanRubrik || '(tom)'),
        el('div', { class: 'svarsverktyg' }, kopieraKnapp('Kopiera posten som markdown', () => original, (knapp, t) => kallruta(knapp, t))));
    }).catch((f) => text.replaceChildren(status('Posten kunde inte läsas: ' + f.message, 'fel')));
  } else if (o.typ === 'uppdrag') {
    delar.push(el('p', { class: 'kl', text: o.uppdrag + ' · ' + (o.lage === 'arbetar' ? (o.steg || 'steg') + ' · ' + (o.tillstand || '') + ' · utförare ' + (o.utforare || 'ej belagd') : 'vilar sedan ' + tid(o.sedan)) + ' · läst ' + tid(o.lasttid) }));
    delar.push(el('p', { class: 'dampad', text: 'Aquarium visar bara uppdragets rubrik och läge. Uppdragets underlag finns i Runtime och läses inte här.' }));
  }
  if (o.tradar && o.tradar.length) delar.push(el('p', null, 'Resonerat om i: ', ...o.tradar.map((t, n) => [n ? ', ' : '', lank('/forbattringar/' + t.id, '«' + t.titel + '»')]).flat()));
  const kalla = o.kallor && o.kallor[0] ? o.kallor[0].id : null;
  delar.push(el('div', { class: 'knapprad' },
    el('button', { type: 'button', class: 'knapp primar', onclick: () => resoneraOm([{ ref: o.ref, typ: o.typ, titel: o.titel, kalla }]) }, 'Resonera om det här'),
    o.typ === 'overlamning' && o.bestalld_i ? lank('/forbattringar/' + o.bestalld_i.id, 'Öppna tråden där den beställdes', { class: 'knapp' }) : null));
  delar.push(el('p', { class: 'kl dampad', text: '"Resonera om det här" öppnar ett nytt samtal med objektet som underlag. Inget skickas förrän du skriver och skickar.' }));
  rot.replaceChildren(...delar);
  rot.scrollIntoView({ block: 'nearest' });
}

// ------------------------------------------------------------------ Kundstart
function ksLuckor(d) {
  return sektion('h-ks-luckor', 'Öppet enligt planens ägartur',
    d.agarrader.status === 'ok' && Array.isArray(d.agarrader.rader) ? (d.agarrader.rader.length ? el('ul', { class: 'lista' }, d.agarrader.rader.map(bordrad)) : el('p', { text: 'Inga öppna rader om Kundstart i planens ägartur (läst ' + tid(d.agarrader.read_at) + ').' }))
      : status(d.agarrader.status === 'laser' || d.agarrader.status === 'ingen_lasning' ? 'Läser kontorets källor…' : 'Planens ägartur gick inte att läsa helt just nu: det som är öppet för Kundstart är okänt.', 'varning'));
}
async function uppdateraKsLuckor() {
  if (as.del !== 'kundstart') return;
  let d;
  try { d = await api('GET', '/api/arbetsplats/kundstart'); } catch { return; }
  const gammal = document.querySelector('[aria-labelledby="h-ks-luckor"]');
  const arenden = document.querySelector('[aria-labelledby="h-ks-arenden"]');
  if (as.del !== 'kundstart' || !gammal) return;
  gammal.replaceWith(ksLuckor(d));
  if (arenden) arenden.replaceWith(ksArenden(d.arenden));  // bara läsningens block; fokus i övrigt lämnas orört
  const vantar = d.agarrader.status === 'laser' || d.agarrader.status === 'ingen_lasning' || (d.arenden && d.arenden.pagar);
  as.ksForsok = vantar ? as.ksForsok + 1 : 0;
  if (as.ksForsok && as.ksForsok <= 30) as.ksTimer = setTimeout(uppdateraKsLuckor, 5000);
}
function ksArenden(a) {  // ärendenas metadata; ingen kundtext, inga svar, inget material och inga länkar
  const huvud = el('p', { class: 'kl dampad', text: 'Metadata ur Kundstarts lagring, som testservern delar med produktionen, så även riktiga kunders ärenden syns här. Ärenden öppnas inte härifrån; ditt provärende öppnas ovan. En läsning går igenom varje ärende i lagringen och görs därför i bakgrunden, högst var 15:e minut.' });
  if (!a || a.status !== 'ok') return sektion('h-ks-arenden', 'Ärenden', status((a && a.skal) || 'Ärendelistan kunde inte läsas.', a && a.status === 'laser' ? '' : 'varning'), huvud);
  if (!a.arenden.length) return sektion('h-ks-arenden', 'Ärenden', el('p', { text: 'Inga ärenden i Kundstart (läst ' + nar(a.lasttid) + ').' }), huvud);
  const rader = a.arenden.slice().sort((x, y) => String(y.uppdaterad).localeCompare(String(x.uppdaterad)));
  const rad = (r) => {
    const inl = r.senaste_inlamning;
    const tal = (n) => (n === null || n === undefined ? '?' : n);
    const lage = inl ? 'inlämnat ' + nar(inl.tid) + ' (' + tal(inl.svar) + ' svar, ' + tal(inl.material) + ' material)' + (r.andrat_efter_inlamning ? ', ändrat efter inlämning' : '') : 'inte inlämnat';
    return el('li', null, el('span', { text: r.kund }), r.testdialog ? el('span', { class: 'chip provlage arende-prov', text: 'prov' }) : null,
      el('div', { class: 'kl dampad' }, 'ändrat ', tidEl(r.uppdaterad), ' · skapat ' + nar(r.skapad) + ' · revision ' + tal(r.revision) + ' · ' + tal(r.svar) + ' svar · ' + tal(r.material) + ' material · ' + lage));
  };
  return sektion('h-ks-arenden', 'Ärenden · ' + rader.length + (a.komplett ? '' : '+'),
    el('ul', { class: 'lista' }, rader.slice(0, 8).map(rad)),
    rader.length > 8 ? el('details', { class: 'fler' }, el('summary', null, 'Visa ' + (rader.length - 8) + ' till'), el('ul', { class: 'lista' }, rader.slice(8).map(rad))) : null,
    a.komplett ? null : status(a.skal || 'Listan är avkortad.', 'varning'),
    a.pagar ? el('p', { class: 'kl dampad', text: 'En ny läsning pågår i bakgrunden.' }) : null,
    a.olasbara ? status(a.olasbara + ' dokument i Kundstarts lagring gick inte att läsa som ärenden och saknas i listan.', 'varning') : null,
    el('p', { class: 'kl dampad', text: 'Läst ' + nar(a.lasttid) + '.' }), huvud);
}
async function visaKundstart() {
  const rot = $('del-kundstart');
  if (!as.kundstart) rot.replaceChildren(el('header', { class: 'del-huvud' }, el('h1', { id: 'kundstart-rubrik', tabindex: '-1' }, 'Kundstart'), status('Läser…')));
  let d;
  try { d = await api('GET', '/api/arbetsplats/kundstart'); }
  catch (f) { rot.replaceChildren(el('header', { class: 'del-huvud' }, el('h1', { id: 'kundstart-rubrik', tabindex: '-1' }, 'Kundstart'), status('Kundstart-läget kunde inte läsas: ' + f.message, 'fel'))); return; }
  as.kundstart = d;
  clearTimeout(as.ksTimer);
  as.ksForsok = d.agarrader.status === 'laser' || d.agarrader.status === 'ingen_lasning' || (d.arenden && d.arenden.pagar) ? (as.ksForsok || 0) + 1 : 0;
  if (as.ksForsok && as.ksForsok <= 30) as.ksTimer = setTimeout(uppdateraKsLuckor, 5000);
  const s = d.provserver, k = d.kod;
  const kodtext = k.status === 'ok' ? 'Kundstart-repot står på ' + k.head + (k.ar_main ? ' (samma som main)' : ' (main är ' + k.main + ')') + (k.byggd ? ', testservern byggdes från ' + k.byggd : '') + '.' : 'Kundstart-repots revision gick inte att läsa.';
  const kommando = (t) => el('span', { class: 'kommando' }, el('code', { text: t }), kopieraKnapp('Kopiera kommandot ' + t, () => t, (knapp) => knapp.previousElementSibling));
  const beslut = d.beslut;
  rot.replaceChildren(
    el('header', { class: 'del-huvud' }, el('h1', { id: 'kundstart-rubrik', tabindex: '-1' }, 'Kundstart ', el('span', { class: 'chip provlage', text: 'provläge' })),
      el('p', { class: 'dampad' }, 'Kundens egen vy för intervju och material. Den öppnas separat och har ingen del av den här navigationen. Läst ' + nar(d.lasttid) + '. ',
        el('button', { class: 'lank', type: 'button', onclick: () => visaKundstart() }, 'Läs om'))),
    el('div', { class: 'kundstart-rutnat' },
      sektion('h-prov', 'Ditt provärende',
        s.kor ? el('p', null, 'Testservern kör. Kundstart öppnar det ärende som webbläsaren redan är inloggad i.')
          : status('Testservern kör inte, så provärendet kan inte öppnas just nu. Starta den med kommandot nedan.', 'varning'),
        el('div', { class: 'knapprad' }, s.kor ? el('a', { class: 'knapp primar', href: KUNDSTART_PROV + '/samtal', rel: 'noopener' }, 'Öppna ditt provärende') : null),
        el('details', { class: 'fler', open: !s.kor }, el('summary', null, 'Testservern'),
          el('p', { class: 'kl' }, 'Adress ', el('code', { text: s.adress }), '. ' + kodtext),
          el('ul', { class: 'lista kommandon' },
            el('li', null, s.kor ? 'Stoppa: ' : 'Starta i Kundstart-repot: ', kommando(s.kor ? 'npm run prov -- stopp' : 'npm run prov -- start')),
            el('li', null, 'Öppna ditt provärende med länken: ', kommando('npm run prov -- oppna')),
            el('li', null, 'Nytt provärende (bara när du vill): ', kommando('npm run prov -- oppna --ny'))),
          el('p', { class: 'kl dampad', text: 'Saknas inloggningen visar Kundstart sin egen länksida. Arbetsplatsen skapar inga ärenden och hanterar inga länknycklar.' }))),
      sektion('h-ks-lage', 'Så används Kundstart nu',
        beslut.length ? el('ul', { class: 'lista' }, beslut.slice(0, 2).map((b) => beslutsrad(b.ref, b.titel, b.datum))) : status('Kundstarts beslut gick inte att läsa i indexet.', 'varning'),
        beslut.length > 2 ? el('details', { class: 'fler' }, el('summary', null, 'Tidigare Kundstart-beslut (' + (beslut.length - 2) + ')'), el('ul', { class: 'lista' }, beslut.slice(2).map((b) => beslutsrad(b.ref, b.titel, b.datum)))) : null,
        el('p', { class: 'kl dampad', text: 'Lydelsen är beslutsloggens egen. Produktionens drift avläses inte härifrån.' })),
      sektion('h-ks-kopplingar', 'Kopplingar',
        el('ul', { class: 'lista' },
          el('li', null, d.digitala.status === 'ok' ? (d.digitala.verktyg ? 'Digitala: verktyg/kundstart.py finns på main ' + d.digitala.main + ' och skapar och hämtar ärenden med den interna nyckeln.' : 'Digitala: verktyg/kundstart.py finns inte på main ' + d.digitala.main + '.') : 'Digitala: gick inte att läsa.'),
          el('li', null, d.overlamningar.length ? ['Överlämningar till Kundstart: ', ...d.overlamningar.map((o, n) => [n ? ', ' : '', lank(objektlank(o.id), o.rubrik || o.id), ' (' + (OVLTEXT[o.status] || o.status) + ')']).flat()] : 'Inga överlämningar från partnern till Kundstart.'),
          el('li', null, 'Belagd import eller research för ett visst ärende syns inte här: arbetsplatsen läser inte Digitalas kundmappar, och ärendelistan nedan visar bara metadata. En rad här är inte bevis för att en import har körts.'))),
      ksLuckor(d),
      ksArenden(d.arenden)));
}

// ------------------------------------------------------------------ start
async function startaArbetsplatsen() {
  $('skal').hidden = false; $('inloggning').hidden = true;
  const h = location.hash.slice(1);
  if (location.pathname === '/' && (/^t_[A-Za-z0-9]+$/.test(h) || h === 'ny')) history.replaceState(null, '', '/forbattringar/' + h);  // gamla länkar
  await visa();
}
(async () => {
  const hash = location.hash.slice(1);
  if (hash.startsWith('nyckel=')) { await loggaInMedFragment(hash); return; }
  let session = null;
  try { session = await api('GET', '/api/session'); } catch { /* tjänsten svarar inte; inloggningen visas */ }
  if (session && session.inloggad) await startaArbetsplatsen(); else visaInloggning();
})();
