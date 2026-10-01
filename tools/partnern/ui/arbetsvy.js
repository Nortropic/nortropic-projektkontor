'use strict';
// Arbetsvyn (PARTNER-INSYN-20261001): en körning visad som Claude Codes terminalutskrift, i samma ljusa yta som
// resten av samtalet. Rader: ⏺ anrop, ⎿ resultat (hopfällt; klick eller Enter fäller ut, alt-klick fäller alla),
// ■ start och slut, ⟲ komprimering, ↻ omförsök, ⚠ kvot och varning, ⊘ nekat, ✓ händelse (push, PR, sparat).
// Hjärtslag och faser står i statusraden längst ned (tänker, begär svar, verktygets tid), aldrig som rader.
// Samma komponent för partnerns tur, en utredning och (steg 2) en mottagarsession i Kontoret.
// Allt innehåll renderas som textContent genom el() i app.js. Loggen är aria-live="off" och en dold statusrad läser
// upp bara fasbyten, fel och var 30:e sekund, så att en logg som växer varje sekund inte läses upp rad för rad.

const Arbetsvy = (() => {
  const GLYF = { verktyg: '⏺', utredare: '⏺', text: '⏺', start: '■', slut: '■', komprimering: '⟲', omforsok: '↻', kvot: '⚠',
    varning: '⚠', nekat: '⊘', push: '✓', pr: '✓', uppgift: '✓', ko: '⏸', jobb: '✓', overlamning: '✓', forstaelse: '✓',
    resonemang: '✓', trad: '✓', koppling: '✓' };
  const FASORD = { start: 'Startar', tanker: 'Tänker', begar: 'Begär svar', svarar: 'Skriver', komprimerar: 'Komprimerar sammanhanget',
    omforsok: 'Omförsök', ko: 'I kö · väntar på en ledig plats', klar: 'Klart' };
  const HUVUDORD = { start: 'Startar', tanker: 'Tänker', begar: 'Undersöker', svarar: 'Skriver', verktyg: 'Undersöker',
    komprimerar: 'Komprimerar', omforsok: 'Försöker igen', ko: 'I kö', klar: 'Klart' };
  const TAK_LIVE = 200, TAK_KLAR = 120;
  const levande = new Set();
  let tick = null;
  function tickStart() {
    if (tick) return;
    tick = setInterval(() => {
      if (!levande.size) { clearInterval(tick); tick = null; return; }
      if (document.hidden) return;
      for (const v of levande) {
        if (!v.rot.isConnected) continue;  // en vy i en tråd som inte visas rör varken loggen eller trådhuvudet
        try { v._ticka(); } catch (f) { console.error('arbetsvyn: ' + f.message); levande.delete(v); }
      }
    }, 1000);
  }
  function k(n) { n = Number(n) || 0; return n >= 1000 ? (Math.round(n / 100) / 10).toLocaleString('sv-SE') + 'k' : String(n); }
  function tidSpann(s) {
    s = Math.max(0, Math.floor(s));
    if (s < 60) return s + ' s';
    if (s < 3600) return Math.floor(s / 60) + ' min ' + String(s % 60).padStart(2, '0') + ' s';
    return Math.floor(s / 3600) + ' h ' + String(Math.floor((s % 3600) / 60)).padStart(2, '0') + ' min';
  }
  function msText(x) { if (x === null || x === undefined) return ''; return x < 10000 ? (Math.round(x / 100) / 10).toLocaleString('sv-SE') + ' s' : tidSpann(x / 1000); }
  // Modellens namn: ur samtalsytans lästa modellval när det finns (mv i app.js), annars en fast tabell; aldrig
  // karta.js modellnamn, som läser Flödets data och kastar utanför Flödet.
  const NAMN = { 'claude-opus-5-5': 'Opus 5.5', 'claude-fable-5-1': 'Fable 5.1', 'claude-sonnet-5': 'Sonnet 5', 'claude-opus-5': 'Opus 5',
    'claude-haiku-4-5-20251001': 'Haiku 4.5' };
  function namn(id) {
    if (!id) return '';
    try { const m = typeof mv === 'object' && mv && mv.data && mv.data.modeller.find((x) => x.id === id); if (m && m.namn) return m.namn; } catch { /* utan val */ }
    return NAMN[id] || id;
  }
  function tokentext(r) {
    if (!r) return '';
    const inn = (r.tokens_in || 0) + (r.cache_lasta || 0) + (r.cache_skrivna || 0);
    return inn || r.tokens_ut ? k(inn) + ' in / ' + k(r.tokens_ut || 0) + ' ut' : '';
  }
  function visaArbetet() { try { return localStorage.getItem('arbete:visa') === 'ja'; } catch { return false; } }

  // En körning. korning: {id, slag: 'tur'|'jobb'|'session', start (epoksekunder), modell, anstrangning, status}.
  // alt: {rullare, onAvbryt, hopfalld, visaKalla, oppnaPanel, kallor, listpris}
  function skapa(korning, alt) {
    alt = alt || {};
    const vy = { id: korning.id, slag: korning.slag || 'tur', nasta: 0, antal: 0, fel: 0, klar: false, oppen: !alt.hopfalld,
      _rader: new Map(), _grupper: new Map(), _fas: null, _raknare: {}, _modell: korning.modell, _anstrangning: korning.anstrangning,
      _start: korning.start || Date.now() / 1000, _foljer: true, _nya: 0, _sagt: '', _sagtNar: 0, _lyssnare: null };
    const logg = el('ul', { class: 'av-logg', role: 'log', 'aria-live': 'off', 'aria-label': 'Arbetslogg' });
    const status = el('div', { class: 'av-status', 'aria-hidden': 'true' });
    const ljud = el('div', { class: 'dold', role: 'status', 'aria-live': 'polite', 'aria-atomic': 'true' });
    const piller = el('button', { type: 'button', class: 'av-piller', hidden: true, onclick: () => { vy._foljer = true; vy._nya = 0; piller.hidden = true; rulla(true); } });
    const tidigare = el('button', { type: 'button', class: 'av-tidigare', hidden: true, onclick: () => { logg.classList.add('alla'); tidigare.hidden = true; } });
    const fold = el('button', { type: 'button', class: 'av-fold', hidden: true, 'aria-expanded': 'false', onclick: () => vaxla() });
    const kropp = el('div', { class: 'av-kropp' }, tidigare, logg, piller, status);
    const fot = el('div', { class: 'av-fot', hidden: true });
    vy.rot = el('div', { class: 'arbetsvy av-' + vy.slag + (vy.oppen ? '' : ' hopfalld'), 'data-korning': vy.id }, fold, kropp, fot, ljud);
    kropp.hidden = !vy.oppen;

    function rullaren() { return alt.rullare || vy.rot.closest('.flode') || vy.rot.closest('.av-rullare') || null; }
    function nere() { const r = rullaren(); return !r || r.scrollHeight - r.scrollTop - r.clientHeight < 80; }
    function rulla(tvingat) { const r = rullaren(); if (!r) return; if (tvingat || vy._foljer) r.scrollTop = r.scrollHeight; }
    function vaxla(oppen) {
      vy.oppen = oppen === undefined ? !vy.oppen : !!oppen;
      kropp.hidden = !vy.oppen; fot.hidden = !vy.oppen || !fot.childNodes.length;
      vy.rot.classList.toggle('hopfalld', !vy.oppen);
      fold.setAttribute('aria-expanded', String(vy.oppen));
      fold.firstChild && (fold.firstChild.textContent = vy.oppen ? '▾ ' : '▸ ');
      if (vy.oppen && !vy._laddad && alt.ladda) { vy._laddad = true; alt.ladda(vy); }
    }

    // --- rader
    function rad(glyf, klass, text, tidtext, extra) {
      const r = el('li', { class: 'av-rad ' + klass }, el('span', { class: 'av-punkt', 'aria-hidden': 'true', text: glyf }),
        el('span', { class: 'av-text' }, text), el('span', { class: 'av-tid', text: tidtext || '' }));
      if (extra) r.append(extra);
      return r;
    }
    function behallare(h) {
      if (h.foralder && vy._rader.has(h.foralder)) {
        const f = vy._rader.get(h.foralder);
        let g = vy._grupper.get(h.foralder);
        if (!g) { g = el('ul', { class: 'av-grupp', role: 'group' }); f.li.append(g); vy._grupper.set(h.foralder, g); }
        return g;
      }
      return logg;
    }
    function detalj(h, res) {
      const d = el('div', { class: 'av-detalj' });
      if (h.indata) d.append(el('div', { class: 'av-etikett', text: 'Indata' }), el('pre', { class: 'av-pre', text: h.indata }));
      if (res && res.resultat && res.resultat.utdrag_lang) {
        const text = res.resultat.utdrag_lang;
        d.append(el('div', { class: 'av-etikett', text: 'Resultat' + (res.resultat.storlek > text.length ? ' (början av ' + storlek(res.resultat.storlek) + ')' : '') }),
          el('pre', { class: 'av-pre', text: text }));
        if (alt.oppnaPanel) d.append(el('button', { type: 'button', class: 'lank', onclick: () => alt.oppnaPanel('Resultat · ' + h.text, el('pre', { class: 'fritext', text: text })) }, 'Öppna i panelen'));
      }
      if (res && res.data && res.data.hunkar) d.append(el('div', { class: 'av-etikett', text: '+' + res.data.plus + ' −' + res.data.minus + ' i ' + res.data.hunkar + (res.data.hunkar === 1 ? ' hunk' : ' hunkar') }));
      return d;
    }
    function storlek(n) { return n > 1e6 ? (n / 1e6).toFixed(1) + ' MB' : n > 1000 ? Math.round(n / 1000) + ' kB' : n + ' tecken'; }
    function verktygsrad(h) {
      const punkt = el('span', { class: 'av-punkt ' + (vy.klar ? 'klar' : 'pagar'), 'aria-hidden': 'true', text: '⏺' });
      const tidk = el('span', { class: 'av-tid', text: '' });
      const anrop = el('div', { class: 'av-rad av-anrop', title: h.tid ? new Date(h.tid).toLocaleTimeString('sv-SE') : null }, punkt,
        el('span', { class: 'av-text' }, h.text || h.verktyg || 'verktyg'), tidk);
      const res = el('button', { type: 'button', class: 'av-rad av-res', hidden: true, 'aria-expanded': 'false' },
        el('span', { class: 'av-punkt', 'aria-hidden': 'true', text: '⎿' }), el('span', { class: 'av-text' }), el('span', { class: 'av-tid' }));
      const li = el('li', { class: 'av-steg', 'data-id': h.id || '' }, anrop, h.beskrivning ? el('div', { class: 'av-rad av-besk' }, el('span'), el('span', { class: 'av-text', text: h.beskrivning })) : null, res);
      const post = { li, punkt, tidk, res, h, resultat: null, detalj: null, start: h.tid ? Date.parse(h.tid) / 1000 : Date.now() / 1000 };
      res.addEventListener('click', (e) => { if (e.altKey) fallAlla(res.getAttribute('aria-expanded') !== 'true'); else fallUt(post); });
      if (h.id) vy._rader.set(h.id, post);
      return post;
    }
    function fallUt(post, oppen) {
      const ar = post.res.getAttribute('aria-expanded') === 'true';
      const ny = oppen === undefined ? !ar : !!oppen;
      if (ny && !post.detalj) { post.detalj = detalj(post.h, post.resultat); post.li.insertBefore(post.detalj, post.res.nextSibling); }
      if (post.detalj) post.detalj.hidden = !ny;
      post.res.setAttribute('aria-expanded', String(ny));
    }
    function fallAlla(oppen) { for (const p of vy._rader.values()) if (!p.res.hidden) fallUt(p, oppen); }
    function resultat(h) {
      const post = h.id ? vy._rader.get(h.id) : null;
      const fel = h.status === 'fel' || (h.resultat && h.resultat.fel);
      if (fel) vy.fel++;
      if (!post) {  // ett resultat utan känt anrop (t.ex. efter att loggen laddats mitt i): en egen dämpad rad
        if (!(h.resultat && h.resultat.utdrag)) return null;
        return rad('⎿', 'av-resultat av-los' + (fel ? ' fel' : ''), (fel ? '✗ ' : '') + h.resultat.utdrag, msText(h.ms));
      }
      post.resultat = h;
      post.punkt.classList.remove('pagar'); post.punkt.classList.add(fel ? 'fel' : 'klar');
      post.tidk.textContent = '';
      const utdrag = (h.resultat && h.resultat.utdrag) || (fel ? 'Fel' : '(inget utfall)');
      const nekat = /^(Fel: )?(PreToolUse hook|Nekat|Denied|The user doesn't want)/i.test(utdrag);
      post.res.querySelector('.av-text').textContent = (nekat ? '⊘ ' : fel ? '✗ ' : '') + utdrag;
      post.res.querySelector('.av-tid').textContent = msText(h.ms);
      post.res.classList.toggle('fel', !!fel); post.res.hidden = false;
      if (post.detalj) { post.detalj.remove(); post.detalj = null; if (post.res.getAttribute('aria-expanded') === 'true') fallUt(post, true); }
      const g = vy._grupper.get(h.id);  // underagentens grupp fälls ihop när den är klar
      if (g) { g.classList.add('hopfalld'); post.res.setAttribute('aria-expanded', 'false'); post.res.addEventListener('click', () => g.classList.toggle('hopfalld')); }
      return null;
    }
    function handelse(h) {
      const typ = h.typ;
      if (typ === 'verktyg' || typ === 'utredare') { vy.antal++; const p = verktygsrad(h); behallare(h).append(p.li); return; }
      if (typ === 'resultat') { const r = resultat(h); if (r) logg.append(r); return; }
      if (typ === 'text') { logg.append(rad('⏺', 'av-prosa', h.text || '', '')); return; }
      if (typ === 'slut') { logg.append(rad('■', 'av-slut' + (h.status === 'fel' ? ' fel' : ''), h.text || 'Klart', '')); return; }
      if (typ === 'pr' && h.data && h.data.url) {  // bara en https-adress blir en länk; annat står som text
        const url = /^https:\/\/[^\s"'<>]+$/.test(h.data.url) ? h.data.url : null;
        logg.append(rad('✓', 'av-' + typ, url ? el('a', { href: url, target: '_blank', rel: 'noopener noreferrer' }, h.text || url) : (h.text || h.data.url), '')); return;
      }
      if (typ === 'ko') { logg.append(rad('⏸', 'av-ko', h.text || '', '')); return; }
      const glyf = GLYF[typ] || '·';
      logg.append(rad(glyf, 'av-' + typ + (typ === 'nekat' || typ === 'varning' ? ' fel' : ''), h.text || '', ''));
    }
    function begransa() {
      const tak = vy.klar ? TAK_KLAR : TAK_LIVE;
      const barn = logg.children;
      const over = barn.length - tak;
      if (over <= 0 || logg.classList.contains('alla')) { tidigare.hidden = true; return; }
      for (let i = 0; i < barn.length; i++) barn[i].classList.toggle('av-dold', i < over);
      tidigare.textContent = 'Visa ' + over + ' tidigare rader'; tidigare.hidden = false;
    }

    // --- statusraden
    function fastext(f) {
      if (!f) return '';
      if (f.lage === 'verktyg' && f.verktyg) return (f.verktyg.namn || 'verktyg') + '…' + (f.verktyg.sekunder >= 3 ? ' ' + f.verktyg.sekunder + ' s' : '');
      if (f.lage === 'tanker') return 'Tänker…' + (f.tankt_tokens ? ' ~' + k(f.tankt_tokens) : '');
      if (f.lage === 'omforsok') return 'Omförsök' + (f.forsok ? ' ' + f.forsok : '') + '…';
      return (FASORD[f.lage] || f.lage || 'Arbetar') + (f.lage === 'klar' ? '' : '…');
    }
    function ritaStatus() {
      const f = vy._fas, r = vy._raknare || {};
      const sek = Math.max(0, Math.floor(Date.now() / 1000 - vy._start));
      const glyf = f && f.lage === 'komprimerar' ? '⟲' : f && f.lage === 'omforsok' ? '↻' : f && f.lage === 'ko' ? '⏸' : '✻';
      const delar = [tidSpann(sek), vy.antal + ' steg'];
      if (vy.fel) delar.push(vy.fel + (vy.fel === 1 ? ' fel' : ' fel'));
      const t = tokentext(r); if (t) delar.push(t);
      const m = namn(r.modell || vy._modell); if (m) delar.push(m + (r.anstrangning || vy._anstrangning ? ' · ' + (r.anstrangning || vy._anstrangning) : ''));
      if (r.kvot && Math.max(r.kvot.fem_timmar || 0, r.kvot.sju_dagar || 0) >= 0.75) delar.push('kvot ' + Math.round(Math.max(r.kvot.fem_timmar || 0, r.kvot.sju_dagar || 0) * 100) + ' %');
      if (f && f.utan_tolkning) delar.push(f.utan_tolkning + ' händelser utan tolkning');
      status.replaceChildren(el('span', { class: 'av-snurr' + (glyf === '✻' ? ' snurrar' : ''), text: glyf === '✻' ? '' : glyf }),
        el('span', { class: 'av-fas', text: ' ' + fastext(f) }), el('span', { class: 'av-matt', text: ' · ' + delar.join(' · ') }),
        alt.onAvbryt && !vy.klar ? el('button', { type: 'button', class: 'av-avbryt', onclick: () => alt.onAvbryt() }, 'Avbryt') : null);
      // det som läses upp: fasordet, bara vid byte, vid fel eller var 30:e sekund
      const sagt = (HUVUDORD[(f || {}).lage] || 'Arbetar') + (vy.fel ? ', ' + vy.fel + ' fel' : '');
      if (sagt !== vy._sagt || Date.now() - vy._sagtNar > 30000) { vy._sagt = sagt; vy._sagtNar = Date.now(); ljud.textContent = 'Partnern: ' + sagt + ', ' + vy.antal + ' steg, ' + tidSpann(sek) + '.'; }
      // trådhuvudet skrivs bara av en vy som visas och inte är pausad; en lämnad tråds vy rör aldrig den öppna trådens huvud
      if (alt.huvud && !vy._pausad && vy.rot.isConnected) alt.huvud((HUVUDORD[(f || {}).lage] || 'Undersöker') + ' · ' + tidSpann(sek), sagt);
    }
    vy._ticka = () => { if (!vy.klar) { ritaStatus(); if (vy._fas && vy._fas.verktyg && vy._fas.verktyg.sekunder !== undefined) { for (const p of vy._rader.values()) if (p.resultat === null && p.h.id === vy._fas.verktyg.id) p.tidk.textContent = '·· ' + Math.max(vy._fas.verktyg.sekunder, Math.floor(Date.now() / 1000 - p.start)) + ' s'; } } };

    // --- API
    vy.mata = (handelser) => {
      if (!handelser || !handelser.length) return;
      const varNere = nere();
      for (const h of handelser) { if (typeof h.n === 'number' && h.n < vy.nasta) continue; handelse(h); if (typeof h.n === 'number') vy.nasta = h.n + 1; else vy.nasta++; }
      begransa();
      if (vy.klar) { ritaFold(); return; }
      if (varNere || vy._foljer) { rulla(); vy._nya = 0; piller.hidden = true; }
      else { vy._foljer = false; vy._nya += handelser.length; piller.textContent = '↓ ' + vy._nya + ' nya rader'; piller.hidden = false; }
      ritaStatus();
    };
    function ritaFold() {
      const info = vy._info || {};
      const sek = info.sekunder !== undefined && info.sekunder !== null ? info.sekunder : Math.floor(Date.now() / 1000 - vy._start);
      const delar = ['Arbetade ' + tidSpann(sek), vy.antal + ' steg'];
      const t = tokentext(info.forbrukning ? { tokens_in: info.forbrukning.tokens_in, tokens_ut: info.forbrukning.tokens_ut } : vy._raknare); if (t) delar.push(t);
      const m = namn(info.modell || vy._modell); if (m) delar.push(m + (info.anstrangning ? ' · ' + info.anstrangning : ''));
      if (vy.fel) delar.push(vy.fel + ' fel');
      if (info.omforsok) delar.push(info.omforsok + ' omförsök');
      fold.replaceChildren(el('span', { 'aria-hidden': 'true', text: vy.oppen ? '▾ ' : '▸ ' }), el('span', { text: delar.join(' · ') }));
      fold.hidden = false;
    }
    vy.sattLage = (lage) => {  // {fas, raknare, status_text, startad}
      if (!lage) return;
      if (lage.fas) vy._fas = lage.fas;
      if (lage.raknare) vy._raknare = lage.raknare;
      if (lage.startad) vy._start = lage.startad;
      ritaStatus();
    };
    vy.avsluta = (info) => {  // info: {sekunder, tokens, modell, anstrangning, status, kallor, listpris_usd, orsak}
      info = info || {};
      vy.klar = true; vy._info = info; levande.delete(vy);
      if (info.raknare) vy._raknare = info.raknare;
      if (info.antal) vy.antal = Math.max(vy.antal, info.antal);
      if (info.fel) vy.fel = Math.max(vy.fel, info.fel);
      for (const p of vy._rader.values()) if (p.resultat === null) { p.punkt.classList.remove('pagar'); p.punkt.classList.add('klar'); p.tidk.textContent = ''; }
      ritaFold();
      status.replaceChildren();
      // sidfoten: lästa källor, listpris, valet att alltid visa arbetet
      fot.replaceChildren();
      const kallor = [...new Set((info.kallor || []).filter((x) => x.hur === 'last').map((x) => x.id))];
      if (kallor.length && alt.visaKalla) fot.append(el('div', { class: 'av-kallor' }, 'Lästa källor: ', kallor.slice(0, 60).map((id) => el('button', { type: 'button', class: 'kalla-lank', onclick: () => alt.visaKalla(id) }, id))));
      if (info.listpris_usd) fot.append(el('div', { class: 'av-etikett', text: 'Listpris ' + info.listpris_usd.toFixed(3).replace('.', ',') + ' USD (abonnemang, ingen kostnad)' }));
      if (vy.slag !== 'session') {
        const box = el('input', { type: 'checkbox', id: 'arbvisa-' + vy.id });
        box.checked = visaArbetet();
        box.addEventListener('change', () => { try { localStorage.setItem('arbete:visa', box.checked ? 'ja' : 'nej'); } catch { /* */ } });
        fot.append(el('label', { class: 'av-val', for: 'arbvisa-' + vy.id }, box, ' Visa arbetet i alla svar'));
      }
      fot.append(el('button', { type: 'button', class: 'lank', onclick: () => fallAlla(true) }, 'Fäll ut alla'), ' · ',
        el('button', { type: 'button', class: 'lank', onclick: () => fallAlla(false) }, 'Fäll ihop'));
      fot.hidden = !vy.oppen;
      begransa();
      ljud.textContent = 'Partnern: ' + (info.status === 'svarad' || info.status === 'klart' ? 'klart' : (info.status || 'avslutat')) + ', ' + vy.antal + ' steg.';
      if (alt.huvud) alt.huvud('', '');
    };
    vy.oppna = (oppen) => vaxla(oppen);
    vy.forstor = () => { levande.delete(vy); };
    // När tråden lämnas pausas vyn: ingen ticker, inget trådhuvud; när tråden öppnas igen väcks den (levande) och
    // pollen startar om (app.js sakerstallVy).
    vy.paus = () => { vy._pausad = true; levande.delete(vy); if (alt.huvud) alt.huvud('', ''); };
    vy.levande = () => { if (!vy.klar) { vy._pausad = false; levande.add(vy); tickStart(); } };
    if (!korning.klar) { vy.levande(); ritaStatus(); }
    return vy;
  }
  return { skapa, tidSpann, k };
})();
