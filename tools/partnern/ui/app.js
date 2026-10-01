'use strict';
// Samtalsytan. Allt innehåll från servern (Johnnys text, svar, källor) renderas som DOM-noder med textContent;
// ingen innerHTML används för innehåll. Utkast och ej bekräftade inspel ligger i webbläsaren tills servern
// bekräftat att de är sparade, och samma klient_id används vid varje nytt försök så att inget dubbleras.

const $ = (id) => document.getElementById(id);
const tillstand = { trad: null, vy: null, tradar: [], utkorgTimer: null, pollTimer: null, vyer: {}, livepoll: {}, escNar: 0 };

// ------------------------------------------------------------------ hjälp
function el(tag, attrs, ...barn) {
  const e = document.createElement(tag);
  if (attrs) for (const [k, v] of Object.entries(attrs)) {
    if (v === undefined || v === null || v === false) continue;
    if (k === 'class') e.className = v;
    else if (k === 'text') e.textContent = v;
    else if (k.startsWith('on')) e.addEventListener(k.slice(2), v);
    else e.setAttribute(k, v === true ? '' : v);
  }
  for (const b of barn.flat()) if (b !== null && b !== undefined && b !== false) e.append(b instanceof Node ? b : document.createTextNode(String(b)));
  return e;
}
function tid(iso) {
  if (!iso) return '';
  const d = new Date(iso);
  const idag = new Date();
  const hm = d.toLocaleTimeString('sv-SE', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  return d.toDateString() === idag.toDateString() ? hm : d.toLocaleDateString('sv-SE') + ' ' + hm.slice(0, 5);
}
function storlek(n) { return n > 1e6 ? (n / 1e6).toFixed(1) + ' MB' : Math.max(1, Math.round(n / 1e3)) + ' kB'; }
function uuid() { return (crypto.randomUUID ? crypto.randomUUID() : String(Date.now()) + Math.random().toString(16).slice(2)).replace(/[^A-Za-z0-9_-]/g, ''); }
function las(nyckel, standard) { try { const v = localStorage.getItem(nyckel); return v ? JSON.parse(v) : standard; } catch { return standard; } }
function skriv(nyckel, v) { try { localStorage.setItem(nyckel, JSON.stringify(v)); } catch { /* full eller blockerad */ } }

async function api(metod, sokvag, kropp) {
  const opt = { method: metod, credentials: 'same-origin', headers: {} };
  if (metod !== 'GET') { opt.headers['X-Partner'] = '1'; opt.headers['Content-Type'] = 'application/json'; opt.body = JSON.stringify(kropp || {}); }
  const r = await fetch(sokvag, opt);
  if (r.status === 401) { visaInloggning(); throw new Error('inte inloggad'); }
  const data = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(data.fel || ('HTTP ' + r.status));
  return data;
}

// ------------------------------------------------------------------ markdown → DOM (säkert)
function inline(text) {
  const ut = [];
  const re = /(`[^`]+`)|(\*\*[^*]+\*\*)|(\*[^*\s][^*]*\*)|(\[[^\]]+\]\((https?:\/\/[^)\s]+)\))|(https?:\/\/[^\s<>()]+[^\s<>().,;:!?])/g;
  let sist = 0, m;
  while ((m = re.exec(text))) {
    if (m.index > sist) ut.push(document.createTextNode(text.slice(sist, m.index)));
    if (m[1]) ut.push(el('code', { text: m[1].slice(1, -1) }));
    else if (m[2]) ut.push(el('strong', null, ...inline(m[2].slice(2, -2))));
    else if (m[3]) ut.push(el('em', null, ...inline(m[3].slice(1, -1))));
    else if (m[4]) { const t = m[4].slice(1, m[4].indexOf('](')); ut.push(el('a', { href: m[5], target: '_blank', rel: 'noopener noreferrer' }, t)); }
    else if (m[6]) ut.push(el('a', { href: m[6], target: '_blank', rel: 'noopener noreferrer' }, m[6]));
    sist = re.lastIndex;
  }
  if (sist < text.length) ut.push(document.createTextNode(text.slice(sist)));
  return ut;
}
// Kopiering som i Claudes chatt, tecken för tecken: webbläsarens urklipp, annars den äldre kopieringen ur en dold
// textruta med exakt samma text; går inget av dem markeras texten synligt för att kopieras för hand.
function kopieraKnapp(etikett, text, markera) {
  const knapp = el('button', { type: 'button', class: 'kopiera', 'aria-label': etikett, title: etikett }, 'Kopiera');
  knapp.addEventListener('click', async () => {
    const t = text();
    try {
      if (!navigator.clipboard || !window.isSecureContext) throw new Error('urklipp saknas');
      await navigator.clipboard.writeText(t);
      return kvittoKopiera(knapp, 'Kopierat', 'Kopierat till urklipp.');
    } catch { /* nästa väg */ }
    if (kopieraGammalt(t, knapp)) return kvittoKopiera(knapp, 'Kopierat', 'Kopierat till urklipp.');
    const mal = markera(knapp, t);
    if (mal && mal.select) { mal.focus(); mal.select(); }
    else if (mal) { const s = window.getSelection(); s.removeAllRanges(); const r = document.createRange(); r.selectNodeContents(mal); s.addRange(r); }
    kvittoKopiera(knapp, mal ? 'Markerat' : 'Gick inte', mal ? 'Urklipp gick inte att använda; texten är markerad, tryck ⌘C.' : 'Kunde inte kopiera.');
  });
  return knapp;
}
function kopieraGammalt(t, knapp) {
  const ruta = el('textarea', { class: 'urklipp', readonly: '', 'aria-hidden': 'true', tabindex: '-1' });
  ruta.value = t; document.body.append(ruta); ruta.focus(); ruta.select();
  let ok = false;
  try { ok = document.execCommand('copy'); } catch { ok = false; }
  ruta.remove(); knapp.focus();
  return ok;
}
// Hela svarets markdown-källa i en synlig, skrivskyddad ruta, när den måste markeras för hand.
function kallruta(knapp, t) {
  const verktyg = knapp.closest('.svarsverktyg');
  let ruta = verktyg.parentElement.querySelector('textarea.kallruta');
  if (!ruta) {
    ruta = el('textarea', { class: 'kallruta', readonly: '', 'aria-label': 'Svarets markdown-källa' });
    verktyg.after(ruta);
  }
  ruta.value = t;
  return ruta;
}
function kvittoKopiera(knapp, kort, lang) {
  knapp.textContent = kort; $('utkaststatus').textContent = lang;
  clearTimeout(knapp.aterstall); knapp.aterstall = setTimeout(() => { knapp.textContent = 'Kopiera'; }, 1800);
}
function markdown(text) {
  const rot = el('div', { class: 'svar' });
  const rader = (text || '').replace(/\r/g, '').split('\n');
  let i = 0;
  while (i < rader.length) {
    const r = rader[i];
    if (/^```/.test(r)) {
      const kod = []; i++;
      while (i < rader.length && !/^```/.test(rader[i])) kod.push(rader[i++]);
      i++;
      const kodtext = kod.join('\n');
      rot.append(el('div', { class: 'kodblock' }, el('pre', null, el('code', { text: kodtext })),
        kopieraKnapp('Kopiera kodblocket', () => kodtext, (k) => k.parentElement.querySelector('code'))));
      continue;
    }
    const h = /^(#{1,6})\s+(.*)$/.exec(r);
    if (h) { rot.append(el('h' + Math.min(4, h[1].length + 1), null, ...inline(h[2]))); i++; continue; }
    if (/^\s*\|.*\|\s*$/.test(r) && i + 1 < rader.length && /^\s*\|[\s:|-]+\|\s*$/.test(rader[i + 1])) {
      const cell = (x) => x.trim().replace(/^\||\|$/g, '').split('|').map((c) => c.trim());
      const tab = el('table'); const th = el('tr');
      cell(r).forEach((c) => th.append(el('th', null, ...inline(c))));
      tab.append(el('thead', null, th)); const tb = el('tbody'); i += 2;
      while (i < rader.length && /^\s*\|.*\|\s*$/.test(rader[i])) { const tr = el('tr'); cell(rader[i]).forEach((c) => tr.append(el('td', null, ...inline(c)))); tb.append(tr); i++; }
      tab.append(tb); rot.append(tab); continue;
    }
    if (/^\s*>/.test(r)) {
      const bq = []; while (i < rader.length && /^\s*>/.test(rader[i])) bq.push(rader[i++].replace(/^\s*>\s?/, ''));
      rot.append(el('blockquote', null, ...inline(bq.join(' ')))); continue;
    }
    const lista = /^\s*([-*•]|\d+[.)])\s+/.exec(r);
    if (lista) {
      const ordnad = /\d/.test(lista[1]); const l = el(ordnad ? 'ol' : 'ul');
      while (i < rader.length && /^\s*([-*•]|\d+[.)])\s+/.test(rader[i])) {
        let t = rader[i].replace(/^\s*([-*•]|\d+[.)])\s+/, ''); i++;
        while (i < rader.length && /^\s{2,}\S/.test(rader[i]) && !/^\s*([-*•]|\d+[.)])\s+/.test(rader[i])) t += ' ' + rader[i++].trim();
        l.append(el('li', null, ...inline(t)));
      }
      rot.append(l); continue;
    }
    if (!r.trim()) { i++; continue; }
    const stycke = [];
    while (i < rader.length && rader[i].trim() && !/^(#{1,6}\s|```|\s*>|\s*([-*•]|\d+[.)])\s+)/.test(rader[i]) && !/^\s*\|.*\|\s*$/.test(rader[i])) stycke.push(rader[i++]);
    const p = el('p');
    stycke.forEach((s, n) => { if (n) p.append(el('br')); p.append(...inline(s)); });
    rot.append(p);
  }
  return rot;
}

// ------------------------------------------------------------------ inloggning
function visaInloggning() { $('skal').hidden = true; $('inloggning').hidden = false; $('nyckel').focus(); }
async function loggaIn(nyckel) {
  await api('POST', '/api/logga-in', { nyckel });
  $('inloggning').hidden = true; await startaArbetsplatsen();
}
$('inloggningsformular').addEventListener('submit', async (e) => {
  e.preventDefault(); $('inloggningsfel').textContent = '';
  try { await loggaIn($('nyckel').value); } catch (f) { $('inloggningsfel').textContent = f.message; }
});

// ------------------------------------------------------------------ trådar
async function laddaTradar() {
  const d = await api('GET', '/api/tradar'); tillstand.tradar = d.tradar; ritaTradar();
}
function ritaTradar() {
  const lista = $('tradlista'); lista.replaceChildren();
  for (const t of tillstand.tradar) {
    lista.append(el('div', { class: 'tradrad' + (t.id === tillstand.trad ? ' vald' : '') },
      el('button', { class: 'trad' + (t.id === tillstand.trad ? ' vald' : ''), onclick: () => { stangTradmeny(); oppnaTrad(t.id, 'lagg'); }, 'aria-current': t.id === tillstand.trad ? 'true' : null,
        title: t.titel + ' · ' + tid(t.senast) + ' · ' + t.inspel + ' inspel' },
        el('span', { class: t.aktiv ? 'aktiv' : t.jobb_aktiva ? 'aktiv jobb' : 'punkt', title: t.aktiv ? 'Arbetar' : t.jobb_aktiva ? 'En utredning pågår' : null }), el('span', { class: 't', text: t.titel })),
      el('button', { class: 'radera', type: 'button', title: 'Radera tråden', 'aria-label': 'Radera tråden ' + t.titel, onclick: () => fragaRadera(t) }, soptunna())));
  }
}
function soptunna() {  // el() skapar HTML-element; ikonen behöver SVG:s namnrymd
  const ns = 'http://www.w3.org/2000/svg';
  const s = document.createElementNS(ns, 'svg'); s.setAttribute('viewBox', '0 0 20 20'); s.setAttribute('aria-hidden', 'true');
  const p = document.createElementNS(ns, 'path'); p.setAttribute('d', 'M4.5 6h11M8 6V4.5h4V6M6 6l.7 9.5h6.6L14 6M8.7 9v4M11.3 9v4');
  s.append(p); return s;
}
// ------------------------------------------------------------------ radera en tråd för gott (RADERA-TRAD-20260929)
function fragaRadera(t) {
  const d = $('raderadialog');
  d.dataset.trad = t.id; $('raderatext').textContent = '”' + t.titel + '”'; $('raderafel').textContent = '';
  $('raderabekrafta').disabled = false;
  d.showModal(); $('raderaavbryt').focus();  // det säkra valet har fokus
}
$('raderaavbryt').addEventListener('click', () => $('raderadialog').close());
$('raderabekrafta').addEventListener('click', async () => {
  const d = $('raderadialog'); const id = d.dataset.trad;
  $('raderabekrafta').disabled = true; $('raderafel').textContent = '';
  try { await api('POST', '/api/trad/' + id + '/radera', { bekraftat: true }); }
  catch (f) { $('raderafel').textContent = 'Tråden raderades inte: ' + f.message; $('raderabekrafta').disabled = false; return; }
  d.close();
  if (tillstand.trad === id) { tillstand.trad = null; await oppnaTrad('ny', 'ersatt'); }  // null: inget utkast sparas för den raderade
  try { localStorage.removeItem('utkast:' + id); if (las('senasteTrad', null) === id) localStorage.removeItem('senasteTrad'); } catch { /* */ }
  skriv('utkorg', las('utkorg', []).filter((x) => x.trad !== id));  // ett osparat inspel skulle annars bli en ny tråd
  await laddaTradar().catch(() => {});
  $('nytrad').focus();  // knappen som öppnade dialogen finns inte längre
});
async function oppnaTrad(id, adress) {  // adress: 'lagg' (ny historikpost), 'ersatt' eller 'ingen' (routern har redan satt den)
  if (tillstand.trad) sparaUtkast();  // spara den tråd som lämnas, aldrig en tom ruta innan utkastet laddats
  stoppaLivepoll(); rensaVyer();
  tillstand.trad = id; tillstand.vy = null; tillstand.vyNyckel = null;
  if (id !== 'ny') skriv('senasteTrad', id);
  if (adress !== 'ingen') satAdress('/forbattringar/' + id, adress === 'ersatt');
  ritaTradar(); laddaUtkast(); ritaTrad(); await hamtaTrad();
}
async function hamtaTrad() {
  if (!forbattringarSyns()) return;  // ingen läsning eller polling medan samtalet inte syns
  if (!tillstand.trad || tillstand.trad === 'ny') { tillstand.vy = null; stoppaLivepoll(); ritaTrad(); planera(8000); return; }
  try {
    const ny = await api('GET', '/api/trad/' + tillstand.trad); const nyckel = strukturnyckel(ny);
    // Tråden ritas om bara när något i den har ändrats (ett inspel, en tur, en notis), inte för att sekunder och
    // steg tickar: det levande arbetet uppdateras i arbetsvyn genom sin egen poll, så att öppna rader och markering
    // överlever (PARTNER-INSYN-20261001).
    if (nyckel !== tillstand.vyNyckel || !tillstand.vy) { tillstand.vy = ny; tillstand.vyNyckel = nyckel; ritaTrad(); }
    else tillstand.vy = ny;
  }
  catch (f) { $('tradstatus').textContent = 'Kunde inte läsa tråden: ' + f.message; }
  const arbetar = tillstand.vy && (tillstand.vy.aktiv || Object.keys(tillstand.vy.jobb_aktiva || {}).length);
  planera(arbetar && !Object.keys(tillstand.livepoll).length ? 1200 : 8000);
}
function strukturnyckel(vy) {
  return JSON.stringify({ trad: vy.trad, resonemang: vy.resonemang, poster: vy.poster, seq: vy.seq,
    aktiv: vy.aktiv ? { id: vy.aktiv.id, status: vy.aktiv.status } : null, jobb: Object.keys(vy.jobb_aktiva || {}).sort() });
}
function planera(ms) { clearTimeout(tillstand.pollTimer); if (!forbattringarSyns()) return; tillstand.pollTimer = setTimeout(async () => { await hamtaTrad(); if (forbattringarSyns() && Math.random() < 0.3) laddaTradar().catch(() => {}); }, ms); }

// ------------------------------------------------------------------ arbetsvyn: en levande poll per körning
// GET /api/korning/<id>/handelser?fran=<n> ger bara nya rader (markören), fasen, räknarna och delsvaret; var sekund
// medan körningen pågår. När servern säger klar hämtas tråden en gång och loggen fälls ihop ovanför svaret.
function sakerstallVy(run, slag, alt) {
  let v = tillstand.vyer[run.id];
  if (!v) {
    v = Arbetsvy.skapa({ id: run.id, slag, start: run.startad, modell: run.modell, anstrangning: run.raknare && run.raknare.anstrangning }, alt);
    tillstand.vyer[run.id] = v;
    if (run.delsvar) sattDelsvar(v, run.delsvar);
  }
  if (!v.klar) { v.levande(); v.sattLage(run); startaLivepoll(run.id, v); }  // också när tråden öppnas igen efter ett byte
  return v;
}
function sattDelsvar(v, text) {
  if (!v.delsvarEl) v.delsvarEl = el('div', { class: 'av-delsvar' });
  if (text === v._delsvarText) return;
  v._delsvarText = text;
  v.delsvarEl.replaceChildren(text ? markdown(text) : '');
}
// En pollkedja är bunden till sin post i tillstand.livepoll: stoppas den (trådbyte, radering, klar, 404) eller ersätts den
// medan ett anrop är i luften, ser fortsättningen att posten inte längre är dess egen och dör tyst — den varken ritar
// eller återarmar sig. Så kan en lämnad tråds vy aldrig skriva den öppna trådens huvud, och ingen stoppad kedja lämnar
// ett timer-id som hindrar nästa start.
function startaLivepoll(id, v) {
  if (tillstand.livepoll[id]) return;
  const post = { timer: null };
  tillstand.livepoll[id] = post;
  const egen = () => tillstand.livepoll[id] === post;
  const polla = async () => {
    if (!egen()) return;
    if (!forbattringarSyns()) { stoppaLivepoll(id); return; }
    let d;
    try { d = await api('GET', '/api/korning/' + encodeURIComponent(id) + '/handelser?fran=' + v.nasta); }
    catch (f) {
      if (!egen()) return;
      if (/HTTP 404|finns inte|händelselogg/.test(f.message)) { stoppaLivepoll(id); tillstand.vyNyckel = null; hamtaTrad(); return; }
      post.timer = setTimeout(polla, 3000); return;
    }
    if (!egen()) return;  // stoppad medan svaret var på väg
    if (d.aterstall) { stoppaLivepoll(id); v.forstor(); delete tillstand.vyer[id]; tillstand.vyNyckel = null; hamtaTrad(); return; }  // servern har startat om
    v.mata(d.handelser); v.sattLage(d);
    if (d.delsvar !== undefined) sattDelsvar(v, d.delsvar);
    if (d.klar) { stoppaLivepoll(id); tillstand.vyNyckel = null; hamtaTrad(); return; }
    post.timer = setTimeout(polla, 1000);
  };
  post.timer = setTimeout(polla, 60);
}
function stoppaLivepoll(id) {
  if (id === undefined) { for (const i of Object.keys(tillstand.livepoll)) stoppaLivepoll(i); return; }
  const post = tillstand.livepoll[id];
  if (post) clearTimeout(post.timer);
  delete tillstand.livepoll[id];
  const v = tillstand.vyer[id];
  if (v && !v.klar) v.paus();  // en pausad vy rör inte trådhuvudet; den väcks när dess tråd öppnas igen
}
const VYER_MAX = 20;
function rensaVyer() {  // avslutade vyer byggs billigt om när tråden öppnas; levande behålls tills de avslutas, men inte hur många som helst
  for (const [id, v] of Object.entries(tillstand.vyer)) if (v.klar) { v.forstor(); delete tillstand.vyer[id]; }
  const kvar = Object.keys(tillstand.vyer);
  for (const id of kvar.slice(0, Math.max(0, kvar.length - VYER_MAX))) {  // de äldsta som inte visas; en bortrensad vy byggs om ur serverns logg
    const v = tillstand.vyer[id];
    if (v.rot.isConnected) continue;
    stoppaLivepoll(id); v.forstor(); delete tillstand.vyer[id];
  }
}
async function laddaLogg(id, v, reservsteg) {  // en avslutad körnings logg (det som inte redan finns i vyn), först när den fälls ut
  try { const d = await api('GET', '/api/korning/' + encodeURIComponent(id) + '/handelser?fran=' + v.nasta + '&max=2000'); v.mata(d.handelser); }
  catch { if (!v.nasta) v.mata((reservsteg || []).map((s, n) => ({ n, typ: s.typ, text: s.text, tid: s.tid }))); }  // äldre tur utan händelselogg: journalens steg
}
function visaArbetet() { try { return localStorage.getItem('arbete:visa') === 'ja'; } catch { return false; } }
let huvudSagt = '';
function huvudStatus(text, sagt) {  // trådhuvudet: fasord och tid synligt; det upplästa byts bara när fasen byts
  const h = $('tradstatus');
  let synlig = h.querySelector('.synlig'), dold = h.querySelector('.dold');
  if (!synlig) { h.replaceChildren(synlig = el('span', { class: 'synlig', 'aria-hidden': 'true' }), dold = el('span', { class: 'dold' })); }
  synlig.textContent = text ? '✻ ' + text : '';
  if ((sagt || '') !== huvudSagt) { huvudSagt = sagt || ''; dold.textContent = huvudSagt ? 'Partnern ' + huvudSagt.toLowerCase() : ''; }
  document.title = (text ? '✻ ' : '') + 'Nortropic';
}

$('nytrad').addEventListener('click', () => { stangTradmeny(); oppnaTrad('ny', 'lagg'); });
$('tradtitel').addEventListener('click', async () => {
  if (!tillstand.trad || tillstand.trad === 'ny') return;
  const ny = prompt('Trådens namn', $('tradtitel').textContent);
  if (ny && ny.trim()) { await api('POST', '/api/trad/' + tillstand.trad + '/titel', { titel: ny.trim() }); await hamtaTrad(); await laddaTradar(); }
});

// ------------------------------------------------------------------ rita en tråd
const STATUS = { undersoker: 'undersöker', svarad: 'svarat', begransad: 'begränsat', avbruten: 'avbrutet', fel: 'fel' };
function ritaTrad() {
  const vy = tillstand.vy;
  $('tradtitel').textContent = vy ? vy.trad.titel : 'Ny tråd';
  const flode = $('flode');
  const nere = flode.scrollHeight - flode.scrollTop - flode.clientHeight < 80;
  flode.replaceChildren();
  ritaDar(vy && vy.resonemang);
  const vantande = las('utkorg', []).filter((x) => x.trad === tillstand.trad);
  const tom = !vy && !vantande.length;
  $('huvud').classList.toggle('tom', tom);
  $('forslag').hidden = !tom;
  if (tom) {
    flode.append(el('div', { class: 'halsning' }, el('h1', null, el('span', { class: 'gnista', 'aria-hidden': 'true' }), halsning()),
      el('div', { class: 'notis' }, 'Lämna en tanke, en bild, en fil eller en länk. Partnern vet vad Nortropic är och tar reda på resten själv. Välj "Bara spara" (eller skriv "bara spara") om du bara vill spara något.')));
  } else if (vy) {
    const turFor = {};
    for (const p of vy.poster) if (p.slag === 'tur') for (const i of p.inspel) turFor[i] = p;
    for (const p of vy.poster) {
      if (p.slag === 'inspel') flode.append(ritaInspel(p, turFor[p.id]));
      else if (p.slag === 'tur') flode.append(ritaTur(p, vy));
      else if (p.slag === 'jobb') flode.append(ritaJobb(p, vy));
      else if (p.slag === 'overlamning') flode.append(ritaOverlamning(p));
      else if (p.slag === 'koppling') flode.append(el('div', { class: 'notis' }, p.riktning === 'ut' ? 'Kopplat till tråden ' : 'Kopplat hit från tråden ',
        el('button', { class: 'kalla-lank', onclick: () => oppnaTrad(p.annan, 'lagg') }, '«' + (p.annan_titel || p.annan) + '»'), p.skal ? ' — ' + p.skal : ''));
      else if (p.slag === 'forstaelse') flode.append(el('div', { class: 'notis' }, 'Sparat som ', el('button', { class: 'kalla-lank', onclick: () => visaKalla('F-' + p.nr) }, 'F-' + p.nr),
        ' (' + p.typ + ', ' + p.auktoritet.replace('_', ' ') + ')' + (p.ersatt ? ' — senare ersatt' : '') + ': ' + p.text.slice(0, 220)));
    }
  }
  for (const u of las('utkorg', []).filter((x) => x.trad === tillstand.trad)) flode.append(ritaVantande(u));
  if (!(vy && vy.aktiv)) huvudStatus('', '');  // annars sätter arbetsvyns ticker fasord och tid
  $('skickaavbryt').hidden = !(vy && vy.aktiv);
  $('skicka').title = vy && vy.aktiv ? 'Skicka – partnern svarar när det pågående arbetet är klart' : 'Skicka (Enter)';
  if (nere) flode.scrollTop = flode.scrollHeight;
}
function ritaDar(r) {
  const d = $('dar');
  if (!r || !(r.lage || r.fraga)) { d.hidden = true; return; }
  const oppen = d.querySelector('details') ? d.querySelector('details').open : false;
  const lista = (rubrik, v) => (v && v.length ? el('div', null, el('b', null, rubrik), el('ul', null, v.map((x) => el('li', null, x)))) : null);
  const det = el('details', { open: oppen }, el('summary', null, el('b', null, 'Där vi är (partnerns bild): '), r.lage || r.fraga),
    r.fraga ? el('div', null, el('b', null, 'Fråga: '), r.fraga) : null,
    lista('Spår', r.spar), lista('Invändningar', r.invandningar), lista('Att undersöka härnäst', r.nasta),
    el('div', { class: 'kl', text: 'Uppdaterat ' + tid(r.tid) + ' av partnern' }));
  d.hidden = false; d.replaceChildren(det);
}
function bilagechip(b) {
  const url = '/api/bilaga/' + b.sha;
  const bild = b.klass === 'bild';
  return el('a', { class: 'bilaga', href: url + (bild ? '' : '?ladda=1'), target: '_blank', rel: 'noopener', title: b.namn + ' · ' + b.typ + ' · ' + storlek(b.storlek) },
    bild ? el('img', { src: url, alt: b.namn, loading: 'lazy' }) : null, el('span', null, (b.ref ? b.ref + ' · ' : '') + b.namn));
}
function ritaInspel(p, tur) {
  const chips = [el('span', { class: 'chip ok', text: 'sparat ' + tid(p.tid) })];
  if (p.lage === 'bara_spara') chips.push(el('span', { class: 'chip', text: 'bara sparat, ingen analys' }));
  else if (!tur) chips.push(el('span', { class: 'chip varm', text: 'väntar på partnern' }));
  return el('div', { class: 'post johnny' },
    el('div', { class: 'rubrikrad' }, el('span', { class: 'vem', text: 'Du' }), ...chips),
    el('div', { class: 'bubbla' }, p.text ? el('div', { class: 'svar' }, ...(p.text.split('\n').map((r, n) => [n ? el('br') : null, ...inline(r)]).flat())) : null,
      p.bilagor && p.bilagor.length ? el('div', { class: 'bilagor' }, p.bilagor.map(bilagechip)) : null),
    p.kontext && p.kontext.length ? el('div', { class: 'sammanhang' }, el('span', { class: 'kl', text: 'Sammanhang från arbetsplatsen (underlag, inte dina ord):' }),
      p.kontext.map((k) => el('a', { class: 'chip lank-chip', href: '/kontoret/objekt/' + encodeURIComponent(k.ref), 'data-nav': true }, (OBJEKTSLAG[k.typ] || k.typ) + ' · ' + k.titel))) : null);
}
// En avslutad körnings arbetsvy: hopfälld till en rad ovanför svaret (ägarens val 2026-10-01), öppen när "Visa arbetet"
// är valt eller när turen slutade med fel, avbrott eller begränsning (då är loggen förklaringen). Loggen hämtas när
// den fälls ut; fanns den redan levande i vyn behålls den.
function klarVy(id, slag, p, info) {
  let v = tillstand.vyer[id];
  const oppen = visaArbetet() || !['svarad', 'klart'].includes(p.status);
  if (!v) {
    v = Arbetsvy.skapa({ id, slag, klar: true, modell: p.modell, anstrangning: info.anstrangning },
      { hopfalld: !oppen, visaKalla, oppnaPanel, ladda: (vy) => laddaLogg(id, vy, p.steg) });
    tillstand.vyer[id] = v;
    v.avsluta(info);
    if (oppen) v.oppna(true);
  } else if (!v.klar) {  // en levande vy blev klar (kanske medan tråden var lämnad): rader som inte hann hämtas laddas nu
    stoppaLivepoll(id); v.avsluta(info); v.oppna(oppen);
    if ((p.handelser || 0) > v.nasta) laddaLogg(id, v, p.steg);
  }
  return v;
}
function stegantal(steg) { return (steg || []).filter((s) => s.typ === 'verktyg' || s.typ === 'utredare').length; }
function ritaTur(p, vy) {
  const aktiv = vy.aktiv && vy.aktiv.id === p.id ? vy.aktiv : null;
  const kort = el('div', { class: 'post partner' });
  const chip = el('span', { class: 'chip ' + ({ svarad: 'ok', undersoker: 'varm', fel: 'fel', avbruten: 'fel', begransad: 'varm' }[p.status] || ''), text: STATUS[p.status] || p.status });
  kort.append(el('div', { class: 'rubrikrad' }, el('span', { class: 'vem', text: 'Partnern' }), chip, p.klar ? el('span', { text: tid(p.klar) }) : null, p.ateruppta ? el('span', { text: 'fortsättning' }) : null));
  const bubbla = el('div', { class: 'bubbla' });
  const forb = p.forbrukning || {};
  const info = { sekunder: forb.sekunder, forbrukning: forb, modell: p.modell, anstrangning: forb.anstrangning, status: p.status, kallor: p.kallor,
    listpris_usd: forb.listpris_usd, omforsok: forb.omforsok, antal: stegantal(p.steg), fel: (p.steg || []).filter((s) => / · fel$/.test(s.text || '')).length };
  if (p.status === 'svarad') {
    bubbla.append(klarVy(p.id, 'tur', p, info).rot);
    bubbla.append(markdown(p.svar));
    bubbla.append(el('div', { class: 'svarsverktyg' }, kopieraKnapp('Kopiera hela svaret som markdown', () => p.svar,
      kallruta)));
  }
  else if (p.status === 'undersoker') {
    if (aktiv) {
      const v = sakerstallVy(aktiv, 'tur', { onAvbryt: () => api('POST', '/api/tur/' + p.id + '/avbryt').then(hamtaTrad), oppnaPanel, visaKalla, huvud: huvudStatus });
      if (!v.delsvarEl) sattDelsvar(v, aktiv.delsvar || '');
      bubbla.append(v.rot, v.delsvarEl);
    } else bubbla.append(el('div', { class: 'pagar' }, 'Undersöker…'));  // registrerad men ännu ingen levande körning (eller en omstart)
  } else {
    const orsak = { avbruten: 'Avbrutet', begransad: 'Begränsat', fel: 'Fel' }[p.status] || p.status;
    bubbla.append(klarVy(p.id, 'tur', p, info).rot);
    if (p.svar) bubbla.append(markdown(p.svar));
    bubbla.append(el('div', { class: 'pagar' }, orsak + (p.orsak ? ': ' + p.orsak : '') + '. Ditt material är sparat.'));
    if (p.delsvar) bubbla.append(el('details', null, el('summary', null, 'Det som hann skrivas (ofullständigt)'), markdown(p.delsvar)));
    const senare = vy.poster.some((q) => q.slag === 'tur' && q.tid > p.tid && q.inspel.some((i) => p.inspel.includes(i)));
    if (!senare && !vy.aktiv) bubbla.append(el('div', { class: 'atgarder' }, el('button', { onclick: () => api('POST', '/api/tur/' + p.id + '/ateruppta').then(hamtaTrad) }, p.status === 'fel' ? 'Försök igen' : 'Återuppta')));
  }
  kort.append(bubbla);
  return kort;
}
const JOBBSTATUS = { registrerat: 'registrerad', pagar: 'pågår', klart: 'klar', begransat: 'begränsad', avbrutet: 'avbruten', misslyckat: 'misslyckad' };
function ritaJobb(p, vy) {
  const a = (vy.jobb_aktiva || {})[p.id];
  const k = el('div', { class: 'kort' }, el('h4', null, 'Utredning: ' + p.rubrik),
    el('div', { class: 'rubrikrad' }, el('span', { class: 'chip ' + (p.status === 'klart' ? 'ok' : 'varm'), text: JOBBSTATUS[p.status] || p.status }), el('span', { text: 'registrerad ' + tid(p.tid) })));
  if (a) {
    const v = sakerstallVy(a, 'jobb', { onAvbryt: () => api('POST', '/api/jobb/' + p.id + '/avbryt').then(hamtaTrad), oppnaPanel, visaKalla });
    if (!v.delsvarEl) sattDelsvar(v, a.delsvar || '');
    k.append(v.rot, v.delsvarEl);
  } else if (p.korning && p.status !== 'registrerat') {
    const forb = p.forbrukning || {};
    k.append(klarVy(p.korning, 'jobb', p, { sekunder: forb.sekunder, forbrukning: forb, modell: forb.modell, anstrangning: forb.anstrangning,
      status: p.status, listpris_usd: forb.listpris_usd, omforsok: forb.omforsok }).rot);
  }
  if (p.resultat) k.append(markdown(p.resultat));
  const h = (p.historik || []).slice(-1)[0];
  if (h && h.orsak && p.status !== 'klart') k.append(el('div', { class: 'pagar', text: h.orsak }));
  const knappar = el('div', { class: 'atgarder' });
  if (['registrerat', 'pagar'].includes(p.status)) knappar.append(el('button', { onclick: () => api('POST', '/api/jobb/' + p.id + '/avbryt').then(hamtaTrad) }, 'Avbryt'));
  if (['avbrutet', 'begransat', 'misslyckat'].includes(p.status)) knappar.append(el('button', { onclick: () => api('POST', '/api/jobb/' + p.id + '/ateruppta').then(hamtaTrad) }, 'Återuppta'));
  if (knappar.childNodes.length) k.append(knappar);
  return k;
}
const OVLSTATUS = ['lamnad', 'mottagen', 'startad', 'levererad'];
const OVLTEXT = { vilande: 'vilande i backloggen', lamnad: 'lämnad', mottagen: 'mottagen', startad: 'startad', levererad: 'levererad', avslagen: 'avslagen' };
const MOTTAGARNAMN = { 'kontorets-kedjedrivare': 'kontoret', digitala: 'Digitala', runtime: 'Runtime', kundstart: 'Kundstart' };
function starttext(s, status) {
  if (!s && status === 'vilande') return 'Vilande i backloggen: startvakten startar den inte förrän du släpper den ("släpp OVL-…" eller "genomför OVL-…").';
  if (!s) return status === 'lamnad' ? 'Startvakten har inte startat någon session ännu.' : '';
  const skal = s.skal ? ': ' + s.skal : '';
  return ({
    startad: 'Session ' + (s.fortsatt ? 'fortsatt ' : 'startad ') + tid(s.tid) + ' i ' + s.repo + ' (' + s.cli + ', ' + s.modell + ' ' + s.anstrangning + ')',
    vantar: 'Startvakten väntar' + skal, hindrad: 'Starten hindras' + skal, avbruten: 'Sessionen avbröts ' + tid(s.tid) + skal,
    klar: 'Sessionen avslutades ' + tid(s.tid) + ' efter leverans', avslutad: 'Sessionen avslutades ' + tid(s.tid) + skal,
    misslyckad: 'Starten misslyckades ' + tid(s.tid) + skal,
  })[s.typ] || s.typ;
}
function ritaOverlamning(p) {
  // En vilande beställning är inte lämnad förrän du släppt den: då är släppet dess "lämnad".
  const nar = {}; if (p.vilande_fran) nar.vilande = p.tid; else nar.lamnad = p.tid;
  for (const h of p.historik || []) nar[h.status] = h.tid;
  const steg = p.vilande_fran ? ['vilande'].concat(OVLSTATUS) : OVLSTATUS;
  const start = starttext(p.start, p.status);
  return el('div', { class: 'kort' }, el('h4', null, (p.vilande_fran ? 'Vilande beställning till ' : 'Överlämning till ') + (MOTTAGARNAMN[p.mottagare] || p.mottagare) + ': ' + p.rubrik),
    p.agarcitat ? el('blockquote', { class: 'svar' }, '”' + p.agarcitat + '”') : null,
    el('div', { class: 'tidslinje' }, steg.map((s) => el('span', { class: 'chip ' + (nar[s] ? 'ok' : ''), text: (s === 'vilande' ? 'vilande' : OVLTEXT[s]) + (nar[s] ? ' ' + tid(nar[s]) : '') }))),
    p.markning ? el('div', { class: 'pagar', text: 'Märkning: ' + p.markning.varde + (p.markning.luckor && p.markning.luckor.length ? ' — luckor: ' + p.markning.luckor.join('; ') : '') }) : null,
    start ? el('div', { class: 'pagar', text: start }) : null,
    el('div', { class: 'pagar', text: p.id + ' · mottagare: ' + p.mottagare + ' · paket: ' + p.katalog + (p.ap06 ? ' · AP-06: ' + p.ap06.status : '') }),
    el('div', { class: 'atgarder' }, el('a', { class: 'knapplank', href: '/kontoret/objekt/' + encodeURIComponent(p.id), 'data-nav': true }, 'Visa i Kontoret')));
}
function ritaVantande(u) {
  return el('div', { class: 'post johnny' },
    el('div', { class: 'rubrikrad' }, el('span', { class: 'vem', text: 'Du' }), el('span', { class: 'chip varm', text: u.fel ? 'inte sparat ännu — försöker igen' : 'skickas…' })),
    el('div', { class: 'bubbla' }, u.text || '', u.bilagor && u.bilagor.length ? el('div', { class: 'bilagor' }, u.bilagor.map((b) => bilagechip(b))) : null));
}

// ------------------------------------------------------------------ komponera: utkast, bilagor, utkorg
const utkast = { text: '', bilagor: [], kontext: [] };
function utkastNyckel() { return 'utkast:' + (tillstand.trad || 'ny'); }
function sparaUtkast() {
  utkast.text = $('text').value;
  const kvar = utkast.text || utkast.bilagor.length || utkast.kontext.length;
  if (kvar) skriv(utkastNyckel(), { text: utkast.text, bilagor: utkast.bilagor.filter((b) => b.sha), kontext: utkast.kontext });
  else { try { localStorage.removeItem(utkastNyckel()); } catch { /* */ } }
  $('utkaststatus').textContent = kvar ? 'Utkast — inte skickat (finns bara i den här webbläsaren)' : '';
}
function laddaUtkast() {
  const u = las(utkastNyckel(), { text: '', bilagor: [] });
  utkast.text = u.text || ''; utkast.bilagor = u.bilagor || []; utkast.kontext = Array.isArray(u.kontext) ? u.kontext : [];
  $('text').value = utkast.text; ritaBilagor(); ritaKontext(); sparaUtkast(); anpassaHojd();
}
const OBJEKTSLAG = { overlamning: 'Överlämning', beslut: 'Beslut', uppdrag: 'Runtime-uppdrag' };
function ritaKontext() {  // "Resonera om det här": vilka objekt och källor som följer med nästa inspel; inget skickas förrän du skickar
  const k = $('kontextkort');
  k.hidden = !utkast.kontext.length;
  k.replaceChildren(el('div', { class: 'kl', text: 'Följer med när du skickar — som underlag, inte som dina ord:' }),
    ...utkast.kontext.map((x, n) => el('span', { class: 'chip kontextchip' },
      el('a', { href: '/kontoret/objekt/' + encodeURIComponent(x.ref), 'data-nav': true }, (OBJEKTSLAG[x.typ] || x.typ) + ' · ' + x.titel),
      x.kalla ? el('span', { class: 'kl', title: x.kalla, text: ' · källa: ' + (/^t_/.test(x.kalla) ? 'tråden där den beställdes' : /^kontor:beslut:/.test(x.kalla) ? 'beslutsloggen på main' : x.kalla) }) : null,
      el('button', { type: 'button', title: 'Ta bort ur sammanhanget', 'aria-label': 'Ta bort ' + x.titel + ' ur sammanhanget',
        onclick: () => { utkast.kontext.splice(n, 1); ritaKontext(); sparaUtkast(); } }, '×'))));
}
function ritaBilagor() {
  const l = $('bilagelista'); l.replaceChildren();
  utkast.bilagor.forEach((b, n) => l.append(el('span', { class: 'bilaga' },
    b.sha && b.klass === 'bild' ? el('img', { src: '/api/bilaga/' + b.sha, alt: '' }) : null,
    el('span', null, b.namn + ' · ' + (b.fel ? 'fel: ' + b.fel : b.sha ? 'sparad på servern' : 'laddar upp…')),
    el('button', { type: 'button', title: 'Ta bort', onclick: () => { utkast.bilagor.splice(n, 1); ritaBilagor(); sparaUtkast(); } }, '×'))));
}
async function laddaUpp(fil, namn) {
  const post = { namn: namn || fil.name || 'fil', storlek: fil.size };
  utkast.bilagor.push(post); ritaBilagor();
  try {
    const r = await fetch('/api/bilaga', { method: 'POST', credentials: 'same-origin', body: fil,
      headers: { 'X-Partner': '1', 'X-Filnamn': encodeURIComponent(post.namn), 'Content-Type': 'application/octet-stream' } });
    const d = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error(d.fel || 'HTTP ' + r.status);
    Object.assign(post, d);
  } catch (f) { post.fel = f.message; }
  ritaBilagor(); sparaUtkast();
}
function laggTillFiler(filer) {
  for (const f of filer) {
    let namn = f.name;
    if (!namn || /^image\.(png|jpe?g)$/i.test(namn)) {
      const d = new Date(); const p = (x) => String(x).padStart(2, '0');
      namn = 'skarmklipp-' + d.getFullYear() + p(d.getMonth() + 1) + p(d.getDate()) + '-' + p(d.getHours()) + p(d.getMinutes()) + p(d.getSeconds()) + '.' + ((f.type || 'image/png').split('/')[1] || 'png');
    }
    laddaUpp(f, namn);
  }
}
async function skicka(avbryt) {
  sparaUtkast();
  if (!utkast.bilagor.length && KOMMANDO.test(utkast.text)) { // /model och /effort hanteras här och skickas aldrig
    const text = utkast.text;
    $('text').value = ''; utkast.text = ''; sparaUtkast(); anpassaHojd();
    try { await kommando(text); } catch (f) { $('utkaststatus').textContent = 'Kunde inte byta: ' + f.message; }
    return;
  }
  if (utkast.bilagor.some((b) => !b.sha && !b.fel)) { $('utkaststatus').textContent = 'Väntar på att bilagorna laddas upp…'; return; }
  const bilagor = utkast.bilagor.filter((b) => b.sha);
  if (!utkast.text.trim() && !bilagor.length) return;
  const post = { klient_id: uuid(), trad: tillstand.trad || 'ny', text: utkast.text, bilagor, kontext: utkast.kontext.map((x) => x.ref), lage: $('baraspara').checked ? 'bara_spara' : null, avbryt_pagaende: !!avbryt, skapad: new Date().toISOString() };
  const utkorg = las('utkorg', []); utkorg.push(post); skriv('utkorg', utkorg);
  $('text').value = ''; utkast.text = ''; utkast.bilagor = []; utkast.kontext = []; sattLage(false); ritaBilagor(); ritaKontext(); sparaUtkast(); anpassaHojd();
  ritaTrad(); await tomUtkorg();
}
async function tomUtkorg() {
  clearTimeout(tillstand.utkorgTimer);
  let utkorg = las('utkorg', []);
  for (const u of [...utkorg]) {
    try {
      const d = await api('POST', '/api/inspel', { klient_id: u.klient_id, trad: u.trad, text: u.text, bilagor: u.bilagor.map((b) => b.sha), kontext: u.kontext || [], lage: u.lage, avbryt_pagaende: u.avbryt_pagaende });
      utkorg = las('utkorg', []).filter((x) => x.klient_id !== u.klient_id); skriv('utkorg', utkorg);
      if (u.trad === 'ny' && tillstand.trad === 'ny') {
        try { localStorage.removeItem('utkast:ny'); } catch { /* */ }
        tillstand.trad = d.inspel.trad; skriv('senasteTrad', d.inspel.trad);
        if (forbattringarSyns()) satAdress('/forbattringar/' + d.inspel.trad, true);
      }
    } catch (f) {
      if (/inte inloggad/.test(f.message)) return;
      u.fel = f.message; skriv('utkorg', las('utkorg', []).map((x) => (x.klient_id === u.klient_id ? u : x)));
      if (/^(Tomt|Texten|För många|Okänd bilaga|klient_id|Okänd hänvisning|Sammanhanget)/.test(f.message)) { // går inte att rätta genom nya försök
        skriv('utkorg', las('utkorg', []).filter((x) => x.klient_id !== u.klient_id));
        if (/^(Okänd hänvisning|Sammanhanget)/.test(f.message)) {  // texten går aldrig förlorad: tillbaka som utkast, utan sammanhanget
          const nyckel = 'utkast:' + u.trad; const fore = las(nyckel, null);
          const ledig = !fore || !(fore.text || '').trim();
          if (ledig) skriv(nyckel, { text: u.text, bilagor: u.bilagor || [], kontext: [] });
          if (tillstand.trad === u.trad) laddaUtkast();
          alert('Inspelet skickades inte: ' + f.message + (ledig ? '. Texten ligger kvar som utkast, utan sammanhanget.'
            : '. Tråden har redan ett annat utkast, så texten står här för att kopieras:\n\n' + u.text));
        } else alert('Inspelet kunde inte sparas: ' + f.message);
      }
    }
  }
  $('utkorg').textContent = las('utkorg', []).length ? 'Ett eller flera inspel är inte sparade på servern ännu; nytt försök om några sekunder.' : '';
  if (las('utkorg', []).length) tillstand.utkorgTimer = setTimeout(tomUtkorg, 5000);
  if (forbattringarSyns()) { await laddaTradar().catch(() => {}); await hamtaTrad(); }
}
function anpassaHojd() { const t = $('text'); t.style.height = 'auto'; t.style.height = Math.min(t.scrollHeight + 2, window.innerHeight * 0.4) + 'px'; }

$('komponera').addEventListener('submit', (e) => { e.preventDefault(); skicka(false); });
$('skickaavbryt').addEventListener('click', () => skicka(true));
$('text').addEventListener('input', () => {
  sparaUtkast(); anpassaHojd();
  if (/^\//.test($('text').value)) $('utkaststatus').textContent = '/model väljer modell och ansträngning · /model sonnet · /effort max';
  else if (/^\/model|^\/effort/.test($('utkaststatus').textContent)) $('utkaststatus').textContent = '';
});
$('text').addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey && !e.isComposing) { e.preventDefault(); skicka(false); }
  // Esc två gånger avbryter det pågående arbetet, som i Claude Code: bara med fokus i rutan, utan öppen meny eller
  // dialog, och aldrig på ett enda tryck (ett tiominutersarbete ska inte dö av misstag). Knappen Avbryt finns kvar.
  if (e.key === 'Escape' && tillstand.vy && tillstand.vy.aktiv && $('modellval').hidden && !document.querySelector('dialog[open]')) {
    e.preventDefault();
    if (tillstand.escNar && Date.now() - tillstand.escNar < 2000) {
      tillstand.escNar = 0; $('utkaststatus').textContent = 'Avbryter…';
      api('POST', '/api/tur/' + tillstand.vy.aktiv.id + '/avbryt').then(hamtaTrad).catch((f) => { $('utkaststatus').textContent = 'Kunde inte avbryta: ' + f.message; });
    } else {
      tillstand.escNar = Date.now(); $('utkaststatus').textContent = 'Tryck Esc igen för att avbryta det pågående arbetet.';
      setTimeout(() => { if (tillstand.escNar && Date.now() - tillstand.escNar >= 2000) { tillstand.escNar = 0; if (/Esc igen/.test($('utkaststatus').textContent)) $('utkaststatus').textContent = ''; } }, 2100);
    }
  }
});
function halsning() {
  const h = new Date().getHours();
  return h >= 5 && h < 10 ? 'God morgon, Johnny' : h >= 10 && h < 17 ? 'Hej, Johnny' : h >= 17 && h < 23 ? 'God kväll, Johnny' : 'Hej, nattuggla';
}
function sattLage(spara) {
  $('baraspara').checked = spara;
  $('lage-svara').classList.toggle('vald', !spara); $('lage-svara').setAttribute('aria-pressed', String(!spara));
  $('lage-spara').classList.toggle('vald', spara); $('lage-spara').setAttribute('aria-pressed', String(spara));
}
$('lage-svara').addEventListener('click', () => sattLage(false));
$('lage-spara').addEventListener('click', () => sattLage(true));
const FORSLAG = [['Vad väntar på mig?', 'Vad väntar på mig just nu?'], ['Fortsätt där vi var', 'Fortsätt där vi var.'],
  ['Vad har vi bestämt om …', 'Vad har vi bestämt om '], ['Titta på en länk', 'Titta på den här länken: ']];
function ritaForslag() {
  $('forslag').replaceChildren(...FORSLAG.map(([etikett, text]) => el('button', { type: 'button', onclick: () => {
    $('text').value = text; sparaUtkast(); anpassaHojd(); $('text').focus(); $('text').setSelectionRange(text.length, text.length); } }, etikett)));
}
ritaForslag();

// ------------------------------------------------------------------ modell och ansträngning (som /model i Claude Code)
const KOMMANDO = /^\s*\/(model|modell|effort)(\s+\S+)?\s*$/i;
const ALIAS = { opus: 'claude-opus-5-5', 'opus-5-5': 'claude-opus-5-5', fable: 'claude-fable-5-1', sonnet: 'claude-sonnet-5',
  'opus-5': 'claude-opus-5', haiku: 'claude-haiku-4-5-20251001' };
const mv = { data: null, modell: 0, niva: 2 };
function modellnamn(id) { const m = mv.data && mv.data.modeller.find((x) => x.id === id); return m ? m.namn : id; }
function nivaerFor(id) {  // varje modell bär sina egna nivåer (Codex har andra än Claude); annars de gemensamma
  const m = mv.data && mv.data.modeller.find((x) => x.id === id);
  return (m && m.nivaer && m.nivaer.length) ? m.nivaer : mv.data.nivaer;
}
function markerad() { return mv.data.modeller[mv.modell] ? mv.data.modeller[mv.modell].id : mv.data.huvud; }
function nivaForModell(id, niva) {  // samma nivå om modellen har den; annars high, och annars modellens mittersta
  const lv = nivaerFor(id);
  return lv.includes(niva) ? niva : (lv.includes('high') ? 'high' : lv[Math.floor(lv.length / 2)]);
}
function ritaModellrad() { if (mv.data) $('modellrad').textContent = modellnamn(mv.data.huvud) + ' · ' + mv.data.anstrangning + ' ⌄'; }
async function laddaModellval() { mv.data = await api('GET', '/api/installningar'); ritaModellrad(); return mv.data; }
async function sparaModellval(huvud, anstrangning) {
  mv.data = await api('POST', '/api/installningar', { huvud, anstrangning });
  ritaModellrad();
  $('utkaststatus').textContent = modellnamn(mv.data.huvud) + ' · ' + mv.data.anstrangning + ' gäller från nästa svar.';
}
async function oppnaModellval() {
  const d = mv.data || await laddaModellval();
  mv.modell = Math.max(0, d.modeller.findIndex((m) => m.id === d.huvud));
  mv.niva = Math.max(0, nivaerFor(d.huvud).indexOf(d.anstrangning));
  ritaModellval(); $('modellval').hidden = false; $('modellrad').setAttribute('aria-expanded', 'true');
  placeraModellval(); $('modellval').focus();
}
function placeraModellval() {  // öppnas åt det håll där menyn får plats: nedåt när rutan står mitt på en tom sida
  const m = $('modellval'); const r = m.parentElement.getBoundingClientRect();
  m.style.maxHeight = ''; m.classList.remove('nedat');
  const under = window.innerHeight - r.bottom - 16, over = r.top - 16;
  const nedat = under >= m.offsetHeight || under > over;
  m.classList.toggle('nedat', nedat);
  m.style.maxHeight = Math.max(160, nedat ? under : over) + 'px';
}
function stangModellval() { $('modellval').hidden = true; $('modellrad').setAttribute('aria-expanded', 'false'); $('text').focus(); }
function ritaModellval() {
  const d = mv.data;
  $('modellval').replaceChildren(el('div', { class: 'mv-rubrik', text: 'Modell' }),
    ...d.modeller.map((m, i) => el('button', { type: 'button', class: 'mv-modell' + (i === mv.modell ? ' vald' : ''), onclick: () => { const niva = nivaerFor(markerad())[mv.niva]; mv.modell = i; mv.niva = Math.max(0, nivaerFor(markerad()).indexOf(nivaForModell(markerad(), niva))); valjModell(); } },
      el('span', { class: 'mv-namn', text: m.namn }), el('span', { class: 'mv-om', text: m.om }), m.id === d.huvud ? el('span', { class: 'mv-nu', text: '✓' }) : null)),
    el('div', { class: 'mv-niva' }, el('span', { class: 'etikett', text: 'Ansträngning' }),
      el('div', { class: 'mv-nivaer', role: 'group', 'aria-label': 'Ansträngning' }, ...nivaerFor(markerad()).map((n, i) => el('button', {
        type: 'button', class: 'mv-n' + (i === mv.niva ? ' vald' : ''), onclick: async () => { mv.niva = i; ritaModellval(); $('modellval').focus();
          try { await sparaModellval(markerad(), n); mv.modell = Math.max(0, mv.data.modeller.findIndex((m) => m.id === mv.data.huvud)); mv.niva = Math.max(0, nivaerFor(mv.data.huvud).indexOf(mv.data.anstrangning)); ritaModellval(); } catch (f) { $('utkaststatus').textContent = 'Kunde inte byta: ' + f.message; } } }, n)))),
    el('div', { class: 'mv-fot', text: '↑↓ modell · ←→ ansträngning · Enter · Esc · /model, /effort' }));
}
async function valjModell() {
  const d = mv.data; stangModellval();
  const ny = markerad();
  try { await sparaModellval(ny, nivaerFor(ny)[mv.niva] || nivaForModell(ny, d.anstrangning)); } catch (f) { $('utkaststatus').textContent = 'Kunde inte byta: ' + f.message; }
}
$('modellval').addEventListener('keydown', (e) => {
  const d = mv.data; if (!d) return;
  const flytta = (steg) => {  // nivåraden följer den markerade modellen och behåller nivån när den finns där
    const niva = nivaerFor(markerad())[mv.niva];
    mv.modell = (mv.modell + steg + d.modeller.length) % d.modeller.length;
    mv.niva = Math.max(0, nivaerFor(markerad()).indexOf(nivaForModell(markerad(), niva)));
  };
  if (e.key === 'ArrowDown') flytta(1);
  else if (e.key === 'ArrowUp') flytta(-1);
  else if (e.key === 'ArrowRight') mv.niva = Math.min(nivaerFor(markerad()).length - 1, mv.niva + 1);
  else if (e.key === 'ArrowLeft') mv.niva = Math.max(0, mv.niva - 1);
  else if (e.key === 'Enter') { e.preventDefault(); valjModell(); return; }
  else if (e.key === 'Escape') { e.preventDefault(); stangModellval(); return; }
  else return;
  e.preventDefault(); ritaModellval();
});
document.addEventListener('mousedown', (e) => {
  if (!$('modellval').hidden && !$('modellval').contains(e.target) && !$('modellrad').contains(e.target)) stangModellval();
});
$('modellrad').addEventListener('click', () => ($('modellval').hidden ? oppnaModellval() : stangModellval()));
async function kommando(text) {
  const m = text.trim().match(/^\/(model|modell|effort)(?:\s+(\S+))?$/i);
  const d = mv.data || await laddaModellval();
  const arg = ((m && m[2]) || '').toLowerCase();
  if (!arg) { await oppnaModellval(); return; }
  if (m[1].toLowerCase() === 'effort') {
    if (!nivaerFor(d.huvud).includes(arg)) { $('utkaststatus').textContent = 'Nivåerna är ' + nivaerFor(d.huvud).join(', ') + '.'; return; }
    await sparaModellval(d.huvud, arg); return;
  }
  const id = ALIAS[arg] || (d.modeller.some((x) => x.id === arg) ? arg : null);
  if (!id) { $('utkaststatus').textContent = 'Okänd modell: ' + arg + '. Välj med /model.'; return; }
  await sparaModellval(id, nivaForModell(id, d.anstrangning));
}
$('filval').addEventListener('change', (e) => { laggTillFiler([...e.target.files]); e.target.value = ''; });
document.addEventListener('paste', (e) => {
  const filer = [...(e.clipboardData ? e.clipboardData.files : [])];
  if (filer.length) { e.preventDefault(); laggTillFiler(filer); }
});
let dragDjup = 0;
window.addEventListener('dragenter', (e) => { if (e.dataTransfer && [...e.dataTransfer.types].includes('Files')) { dragDjup++; $('slapp').hidden = false; } });
window.addEventListener('dragleave', () => { dragDjup = Math.max(0, dragDjup - 1); if (!dragDjup) $('slapp').hidden = true; });
window.addEventListener('dragover', (e) => e.preventDefault());
window.addEventListener('drop', (e) => { e.preventDefault(); dragDjup = 0; $('slapp').hidden = true; if (e.dataTransfer && e.dataTransfer.files.length) laggTillFiler([...e.dataTransfer.files]); });
window.addEventListener('storage', (e) => { if (e.key === 'utkorg') ritaTrad(); });
window.addEventListener('hashchange', () => {
  const h = location.hash.slice(1);
  if (h.startsWith('nyckel=')) { loggaInMedFragment(h); return; }  // partner.py oppna i en redan öppen flik
  if (/^t_[A-Za-z0-9]+$/.test(h) || h === 'ny') navigera('/forbattringar/' + h, true);  // gamla länkar #t_…
});

// ------------------------------------------------------------------ paneler
function oppnaPanel(titel, innehall) {
  $('paneltitel').textContent = titel; $('panelinnehall').replaceChildren(...[].concat(innehall));
  $('panel').hidden = false; $('app').classList.add('med-panel');
}
$('stangpanel').addEventListener('click', () => { $('panel').hidden = true; $('app').classList.remove('med-panel'); });

async function visaKalla(id, omkrets) {
  oppnaPanel('Källa', el('div', { class: 'meta', text: 'Läser ' + id + '…' }));
  try {
    const d = await api('GET', '/api/kalla?id=' + encodeURIComponent(id) + '&omkrets=' + (omkrets || 2));
    if (d.text) { oppnaPanel('Källa', [el('div', { class: 'meta', text: id }), el('pre', { class: 'fritext', text: d.text })]); return; }
    const delar = [el('div', null, el('b', null, d.titel || id)), el('div', { class: 'meta', text: d.klass_text + ' · ' + d.ref + ' · position ' + d.position })];
    if (d.samtal) delar.push(el('div', { class: 'meta', text: 'Fångat ' + (d.samtal.fangad || '?') + ', senast uppdaterat ' + (d.samtal.uppdaterad || 'okänt') + '. ' + (d.tid_not || '') }));
    if (d.samtal && d.samtal.url) delar.push(el('div', { class: 'meta' }, el('a', { href: d.samtal.url, target: '_blank', rel: 'noopener noreferrer' }, 'Originalet i ChatGPT (kräver inloggning)')));
    if (d.varning) delar.push(el('div', { class: 'meta fel', text: d.varning }));
    for (const g of d.sammanhang) delar.push(el('div', { class: 'medd' + (g.denna ? ' denna' : '') }, el('div', { class: 'vem', text: g.talare + ' · ' + g.id }), g.text));
    if (d.bilagor) delar.push(el('div', { class: 'meta', text: 'Bilagor: ' + d.bilagor.map((b) => b.id + ' ' + b.namn + ' (' + b.status + ')').join('; ') }));
    if (d.senare_i_samtalet) delar.push(el('div', { class: 'meta', text: d.senare_i_samtalet }));
    for (const f of d.partnerns_forstaelse_som_citerar || []) delar.push(el('div', { class: 'meta', text: f.nr + ' (' + f.status + '): ' + f.text }));
    delar.push(el('button', { class: 'lank', onclick: () => visaKalla(id, (omkrets || 2) + 4) }, 'Visa mer sammanhang'));
    oppnaPanel('Källa', delar);
  } catch (f) { oppnaPanel('Källa', el('div', { class: 'fel', text: f.message })); }
}
// Ägarens besked 2026-09-29: "överlämningar kan vara denna backlog". Panelen visar de vilande beställningarna, som bara
// hans egna ord i en tråd släpper eller avslår; lämnade och avslutade överlämningar syns i trådarna och i Kontoret.
$('visaoverlamningar').addEventListener('click', async () => {
  const d = await api('GET', '/api/backlog');
  if (d.status === 'okand') { oppnaPanel('Backlog', el('div', { class: 'meta', text: 'Backloggen är okänd, inte tom: ' + d.skal + '.' })); return; }
  const poster = d.poster.filter((p) => p.status === 'vilande');
  const samman = d.sammanfattning;
  const delar = [];
  if (d.olasbara.length) delar.push(el('div', { class: 'meta', text: 'Backloggen är inte känd i sin helhet: ' + d.olasbara.length + ' paket gick inte att läsa (' + d.olasbara.map((o) => o.id).join(', ') + ').' }));
  for (const p of poster) {
    delar.push(el('div', { class: 'traff' },
      el('div', { class: 'kl', text: p.id + ' · till ' + (MOTTAGARNAMN[p.mottagare] || p.mottagare) + ' · ' + tid(p.datum) + ' · ' + p.markning }),
      el('div', { text: p.rubrik }),
      el('div', { class: 'meta', text: 'Släppbar: ' + (p.slappbar ? p.slappbar.varde + ' (' + p.slappbar.skal + ')' : 'okänd (beroenden i fri text)') }),
      p.luckor.length ? el('div', { class: 'kl', text: 'Luckor: ' + p.luckor.join('; ') }) : null,
      // PARTNER-BACKLOG-AKTUALITET-20260930: partnerns senare poster om beställningen prövas före ett släpp.
      (p.senare || []).length ? el('div', { class: 'fel', text: 'Nämns i senare poster, som prövas före ett släpp: ' + p.senare.map((f) => f.nr + ' (' + tid(f.tid) + '): ' + f.utdrag).join(' · ') + '. Ändrar en post beställningen, avslå den och be partnern lägga en ny.' }) : null,
      p.senare === null ? el('div', { class: 'kl', text: 'Senare poster är okända: partnerns index gick inte att läsa.' }) : null,
      el('div', { class: 'kl' }, 'Ursprung: ', el('a', { href: '/forbattringar/' + p.trad, 'data-nav': true }, p.trad_titel || p.trad), p.fynd ? ' · fynd: ' + p.fynd : ''),
      p.motivering ? el('div', { class: 'kl', text: 'Motivering: ' + p.motivering }) : null));
  }
  if (!poster.length && d.status === 'ok') delar.push(el('div', { class: 'meta', text: 'Inga vilande beställningar.' }));
  delar.push(el('div', { class: 'meta', text: 'En vilande beställning startas inte. Du släpper den genom att skriva till exempel "släpp OVL-…" i en tråd, eller avslår den med "avslå OVL-…". Ett släpp prövas mot partnerns senare poster om beställningen.' }));
  oppnaPanel('Backlog (' + poster.length + ' vilande' + (samman ? ', varav ' + samman.slappbara + ' släppbara nu, ' + samman.blockerade + ' blockerade, ' + samman.okanda + ' okända' : '') + ')', delar);
});

// ------------------------------------------------------------------ start
let forbattringarStartad = false;
async function visaForbattringar(trad) {  // trad: id ur adressen, 'ny', eller null (senaste tråden)
  if (!forbattringarStartad) { forbattringarStartad = true; laddaModellval().catch(() => {}); }
  await laddaTradar().catch(() => {});
  const senaste = las('senasteTrad', null);
  const nyttUtkast = las('utkast:ny', null);
  const valt = trad || ((nyttUtkast && (nyttUtkast.text || (nyttUtkast.bilagor || []).length || (nyttUtkast.kontext || []).length)) ? 'ny'
    : (senaste && tillstand.tradar.some((t) => t.id === senaste) ? senaste : 'ny'));
  if (valt !== tillstand.trad || !trad) await oppnaTrad(valt, trad ? 'ingen' : 'ersatt');
  else { laddaUtkast(); await hamtaTrad(); }
  if (las('utkorg', []).length) tomUtkorg();
}
function lamnaForbattringar() { if (tillstand.trad) sparaUtkast(); clearTimeout(tillstand.pollTimer); stoppaLivepoll(); huvudStatus('', ''); stangTradmeny(); }
function stangTradmeny() { $('app').classList.remove('tradmeny'); $('visatradar').setAttribute('aria-expanded', 'false'); }
$('visatradar').addEventListener('click', () => {
  const oppen = $('app').classList.toggle('tradmeny'); $('visatradar').setAttribute('aria-expanded', String(oppen));
  if (oppen) $('nytrad').focus();
});
async function loggaInMedFragment(hash) {
  history.replaceState(null, '', location.pathname);
  try { await loggaIn(decodeURIComponent(hash.slice(7))); } catch (f) { visaInloggning(); $('inloggningsfel').textContent = f.message; }
}
