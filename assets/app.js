'use strict';
const $ = (selector) => document.querySelector(selector);
const esc = (value) => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const safeUrl = (value) => { try { const url = new URL(String(value).split(' ')[0]); return ['http:', 'https:'].includes(url.protocol) ? url.href : '#'; } catch { return '#'; } };
const state = { prices: [], providers: {}, history: null, generatedAt: null, family: 'H100', limit: 12, visible: [], loading: false, mode: 'snapshot' };
let quickFamily = 'H100';
const countries = { FR:'France', LU:'Luxembourg', NL:'Netherlands', FI:'Finland', US:'United States', DE:'Germany', PL:'Poland', GB:'United Kingdom' };
const symbols = {gcore:'G',ovhcloud:'ovh',scaleway:'≋',verda:'v',nebius:'∷',runpod:'⬡',vast:'V'};
const money = value => Number.isFinite(value) ? '$' + value.toFixed(2) : 'n/a';
const nativeMoney = row => Number.isFinite(row.native_price_hr) ? new Intl.NumberFormat('en',{style:'currency',currency:row.currency || 'USD',maximumFractionDigits:3}).format(row.native_price_hr) : 'Not listed';
const dpaListed = value => value === true || (typeof value === 'string' && /^true(?:\b|\s|\()/i.test(value));
function dateLabel(value) { const d = new Date(value); return Number.isNaN(d.getTime()) ? 'Time not provided' : new Intl.DateTimeFormat('en-GB',{day:'numeric',month:'short',year:'numeric',hour:'2-digit',minute:'2-digit',timeZone:'UTC'}).format(d) + ' UTC'; }
function exposure(provider) { const raw = String(provider.cloud_act_exposure || 'Unknown'); return /^(low|medium|high)\b/i.test(raw) ? raw.match(/^(low|medium|high)/i)[0].toLowerCase() : 'unknown'; }
function locationInfo(row) {
  const raw = row.location || 'Not specified';
  let name = raw;
  if (/^fr-par/.test(raw)) name = 'Paris, France';
  if (/^pl-waw/.test(raw)) name = 'Warsaw, Poland';
  if (/^nl-ams/.test(raw)) name = 'Amsterdam, Netherlands';
  if (/^multi-region incl. Luxembourg/.test(raw)) name = 'Includes Luxembourg';
  if (/^EU regions/.test(raw)) name = 'EU regions';
  if (/^unspecified/i.test(raw)) name = 'Not specified';
  return `<div class="location-cell">${esc(name)}<span>${row.eu_location === true ? 'EU location listed' : 'Confirm region with provider'}</span></div>`;
}
function draw() {
  const euhq = $('#euhq').checked, euloc = $('#euloc').checked, dpa = $('#dpa').checked, model = $('#model').value;
  let rows = state.prices.filter(row => {
    const provider = state.providers[row.provider] || {};
    return (!state.family || row.gpu.toUpperCase().includes(state.family)) && (!model || state.family || row.gpu === model) && (!euhq || provider.eu_incorporated === true) && (!euloc || row.eu_location === true) && (!dpa || dpaListed(provider.dpa));
  });
  const famRows = state.prices.filter(row => (!state.family || row.gpu.toUpperCase().includes(state.family)) && (!model || state.family || row.gpu === model));
  const bestAll = famRows.reduce((m,r) => Math.min(m,r.usd_hr), Infinity);
  const bestEu = famRows.filter(r => state.providers[r.provider]?.eu_incorporated === true).reduce((m,r) => Math.min(m,r.usd_hr), Infinity);
  const matchedCount = rows.length, providerCount = new Set(rows.map(row => row.provider)).size;
  rows.sort((a,b) => (Number.isFinite(a.usd_hr) ? a.usd_hr : Infinity) - (Number.isFinite(b.usd_hr) ? b.usd_hr : Infinity));
  if ($('#best').checked) { const seen = new Set(); rows = rows.filter(row => !seen.has(row.provider) && seen.add(row.provider)); }
  if ($('#sort').value === 'desc') rows.reverse();
  const cheapest = rows.reduce((min,row) => Number.isFinite(row.usd_hr) ? Math.min(min,row.usd_hr) : min, Infinity);
  state.visible = rows.slice(0,state.limit);
  $('#results-count').textContent = `${matchedCount} matching offer${matchedCount === 1 ? '' : 's'} · ${providerCount} provider${providerCount === 1 ? '' : 's'}`;
  $('#offers').innerHTML = state.visible.map((row,index) => {
    const p = state.providers[row.provider] || {}, ex = exposure(p), name = p.name || row.provider;
    return `<tr><td><div class="gpu-cell"><span class="provider-icon ${esc(row.provider)}" aria-hidden="true">${esc(symbols[row.provider] || name[0])}</span><div><strong>${esc(row.gpu)}${row.usd_hr === bestAll ? '<span class="best-tag">BEST PRICE</span>' : ''}${row.usd_hr === bestEu && p.eu_incorporated === true ? '<span class="best-tag eu">BEST EU</span>' : ''}</strong><small>${esc(name.replace(' (ex-DataCrunch)',''))}</small></div></div></td><td>${locationInfo(row)}</td><td><span class="hq"><span class="hq-code">${esc(p.hq || '?')}</span>${esc(countries[p.hq] || p.hq || 'Unknown')}</span></td><td><span class="exposure ${ex}" title="${esc(p.cloud_act_exposure || 'Not verified')}">${ex[0].toUpperCase() + ex.slice(1)}</span></td><td><strong class="offer-price">${money(row.usd_hr)}</strong><span class="native-price">${row.currency === 'EUR' ? esc(nativeMoney(row)) + ' native rate' : 'USD / GPU-hr'}</span></td><td><div class="row-actions"><button class="details-button" data-detail="${index}" aria-label="Details for ${esc(row.gpu)} from ${esc(name)}">Details</button>${p.affiliate_url ? `<a class="rent-link" data-track="${esc(row.provider)}|${esc(row.gpu)}" href="${esc(safeUrl(p.affiliate_url))}" target="_blank" rel="${p.link_is_referral ? 'sponsored nofollow noopener' : 'noopener'}" aria-label="Rent ${esc(row.gpu)} from ${esc(name)}"><svg><use href="#external"/></svg></a>` : ''}</div></td></tr>`;
  }).join('') || '<tr><td colspan="6" class="empty">No offers match these filters. Try another GPU or reset the filters.</td></tr>';
  $('#showing').textContent = `Showing ${state.visible.length} of ${rows.length}${$('#best').checked ? ' best provider offers' : ' offers'} · Sources in Details`;
  $('#load-more').hidden = state.limit >= rows.length;
  $('#price-sort span').textContent = $('#sort').value === 'asc' ? '↑' : '↓';
}
function filterChanged() { state.limit = 12; draw(); }
function chooseGpu(family) {
  state.family = family;
  document.querySelectorAll('[data-gpu]').forEach(button => { const active = button.dataset.gpu === family; button.classList.toggle('active',active); button.setAttribute('aria-pressed',String(active)); });
  $('.all-models').hidden = !!family;
  $('#model').value = '';
  filterChanged();
}
function openOffer(index) {
  const row = state.visible[index]; if (!row) return;
  const p = state.providers[row.provider] || {};
  const fields = [
    ['Offer / tier',esc(row.tier || 'Not listed')],
    ['Native price',esc(nativeMoney(row)) + ' / GPU-hr'],
    ['Location',esc(row.location || 'Not specified')],
    ['EU location',row.eu_location === true ? 'Yes — listed in source' : row.eu_location === false ? 'No' : 'Unknown — confirm with provider'],
    ['Company HQ',esc(countries[p.hq] || p.hq || 'Unknown')],
    ['EU company',p.eu_incorporated === true ? 'Yes' : p.eu_incorporated === false ? 'No' : 'Not verified'],
    ['DPA',esc(p.dpa === true ? 'Listed in provider metadata' : p.dpa || 'Not verified')],
    ['CLOUD Act',esc(p.cloud_act_exposure || 'Not verified')],
    ['Price collected',esc(dateLabel(row.fetched_at))],
    ['Original source',`<a href="${esc(safeUrl(row.source))}" target="_blank" rel="noopener">Open price source ↗</a>`]
  ];
  $('#dialog-content').innerHTML = `<p class="dialog-kicker">${esc(p.name || row.provider)} · OFFER DETAILS</p><h2 id="dialog-title">${esc(row.gpu)}</h2><div class="dialog-price">${money(row.usd_hr)} <span>/ GPU-hour</span></div><dl class="detail-list">${fields.map(([key,value]) => `<div><dt>${key}</dt><dd>${value}</dd></div>`).join('')}</dl>${p.claims?.length ? `<details class="dialog-claims"><summary>Provider evidence &amp; verification notes<span>+</span></summary><ul>${p.claims.map(c => `<li><a href="${esc(safeUrl(c.url))}" target="_blank" rel="noopener">${esc(c.claim)} ↗</a><br>${esc(c.status)}</li>`).join('')}</ul></details>` : ''}<p class="dialog-disclaimer">${p.link_is_referral ? 'This is a referral link. EuroGPU.watch may earn credits at no additional cost to you. ' : ''}Confirm availability, region, taxes and included resources with the provider. Jurisdiction indicators are not a compliance guarantee.</p>${p.affiliate_url ? `<a class="button" data-track="${esc(row.provider)}|${esc(row.gpu)}" href="${esc(safeUrl(p.affiliate_url))}" target="_blank" rel="${p.link_is_referral ? 'sponsored nofollow noopener' : 'noopener'}">View offer at ${esc((p.name || row.provider).replace(' (ex-DataCrunch)',''))} <svg><use href="#external"/></svg></a>` : ''}`;
  $('#offer-dialog').showModal();
}
function drawQuickOffers() {
  const seen = new Set();
  const rows = state.prices.filter(row => row.gpu.toUpperCase().includes(quickFamily) && (!$('#quick-eu').checked || state.providers[row.provider]?.eu_incorporated === true)).sort((a,b) => a.usd_hr-b.usd_hr).filter(row => !seen.has(row.provider) && seen.add(row.provider)).slice(0,3);
  $('#quick-offers').innerHTML = rows.map(row => {
    const p = state.providers[row.provider] || {};
    return `<div class="quick-offer"><span class="quick-provider-mark ${esc(row.provider)}" aria-hidden="true">${esc(symbols[row.provider] || '?')}</span><span><span class="quick-name">${esc((p.name || row.provider).replace(' (ex-DataCrunch)',''))}</span><span class="quick-meta">${esc(row.gpu)} · ${esc(p.hq || 'HQ unknown')}</span></span><strong>${money(row.usd_hr)}</strong></div>`;
  }).join('') || '<p>No offers match. Try another GPU or include all companies.</p>';
  $('#console-compare>span').textContent = `Compare ${quickFamily} offers`;
  document.querySelectorAll('[data-quick-gpu]').forEach(button => button.setAttribute('aria-pressed',String(button.dataset.quickGpu === quickFamily)));
}
function drawMini() {
  // feature card: highest vs lowest H100 among EU-incorporated providers (best offer per provider), from live data
  const seen = new Set();
  const rows = state.prices.filter(r => r.gpu.toUpperCase().includes('H100') && state.providers[r.provider]?.eu_incorporated === true).sort((a,b) => a.usd_hr-b.usd_hr).filter(r => !seen.has(r.provider) && seen.add(r.provider));
  if (!rows.length) return;
  const lo = rows[0], hi = rows[rows.length-1], nm = r => (state.providers[r.provider]?.name || r.provider).replace(' (ex-DataCrunch)','');
  $('#mini-lo').textContent = money(lo.usd_hr); $('#mini-hi').textContent = money(hi.usd_hr);
  $('#mini-lo-label').innerHTML = `H100 · ${esc(nm(lo))} <i>↘</i>`; $('#mini-hi-label').textContent = `H100 · ${nm(hi)}`;
}
function agoLabel(iso) { const m = Math.round((Date.now() - new Date(iso).getTime())/60000); if (!Number.isFinite(m)) return 'time unknown'; if (m < 1) return 'just now'; if (m < 60) return m + ' min ago'; const h = Math.floor(m/60); return h < 48 ? h + ' h ' + (m%60) + ' min ago' : Math.floor(h/24) + ' days ago'; }
function tickAgo() { if (!state.generatedAt) return; const t = 'Updated ' + agoLabel(state.generatedAt); $('#updated-at').textContent = t; $('#updated-at').title = dateLabel(state.generatedAt); const p = $('#pulse-ago'); if (p) p.textContent = t; }
setInterval(tickAgo, 30000);
// ---- EU premium, sparklines, deals: computed only from data/prices.json and data/history.json ----
const PULSE_MODELS = ['H100','H200','B200','A100','L40S','RTX 4090'];
function modelRx(name) { const rx = state.history?.models?.[name]; try { return rx ? new RegExp(rx,'i') : null; } catch { return null; } }
function matchModel(name, gpu) { const rx = modelRx(name); return rx ? rx.test(gpu) : gpu.toUpperCase().includes(name); }
function cheapestOf(name, euOnly) { return state.prices.filter(r => matchModel(name, r.gpu) && (!euOnly || state.providers[r.provider]?.eu_incorporated === true)).sort((a,b) => a.usd_hr-b.usd_hr)[0] || null; }
function sparkline(name) {
  const pts = (state.history?.points || []).filter(p => p.g?.[name]);
  if (pts.length < 2) return '';
  const xs = pts.map(p => new Date(p.t).getTime()), all = pts.flatMap(p => [p.g[name][0], p.g[name][2]]).filter(Number.isFinite);
  const x0 = Math.min(...xs), x1 = Math.max(...xs), y0 = Math.min(...all), y1 = Math.max(...all), W = 220, Hh = 44;
  const X = t => x1 === x0 ? 0 : (t-x0)/(x1-x0)*W, Y = v => y1 === y0 ? Hh/2 : Hh - (v-y0)/(y1-y0)*(Hh-6) - 3;
  const line = i => pts.filter(p => Number.isFinite(p.g[name][i])).map((p,k) => (k ? 'L' : 'M') + X(new Date(p.t).getTime()).toFixed(1) + ' ' + Y(p.g[name][i]).toFixed(1)).join(' ');
  return `<svg class="spark" viewBox="0 0 ${W} ${Hh}" preserveAspectRatio="none" role="img" aria-label="${esc(name)} cheapest price history, ${pts.length} snapshots"><path d="${line(0)}" class="spark-all"/><path d="${line(2)}" class="spark-eu"/></svg>`;
}
function drawPulse() {
  const grid = $('#pulse-grid'); if (!grid) return;
  grid.innerHTML = PULSE_MODELS.map(name => {
    const all = cheapestOf(name,false), eu = cheapestOf(name,true); if (!all) return '';
    const prem = eu ? (eu.usd_hr/all.usd_hr - 1)*100 : null, nm = r => (state.providers[r.provider]?.name || r.provider).replace(' (ex-DataCrunch)','');
    const meter = prem === null ? '<div class="meter none"><span style="width:100%"></span></div><small>No EU-company offer right now</small>' : `<div class="meter" title="EU premium ${prem.toFixed(0)}%"><span style="width:${Math.min(100,Math.max(4,prem/2)).toFixed(0)}%"></span></div><small>${prem <= 0.5 ? 'No EU premium right now' : 'EU premium +' + prem.toFixed(0) + '%'}</small>`;
    const sp = sparkline(name);
    return `<article class="pulse-card"><header><strong>${esc(name)}</strong><a href="gpu/${esc(name.toLowerCase().replace(/ /g,'-'))}/">Details ↗</a></header>
      <div class="pulse-prices"><div><span>Best price</span><b>${money(all.usd_hr)}</b><small>${esc(nm(all))}</small></div><div><span>Best EU</span><b>${eu ? money(eu.usd_hr) : '–'}</b><small>${eu ? esc(nm(eu)) : 'none listed'}</small></div></div>
      ${meter}${sp || `<p class="collecting">Collecting history since ${esc(dateLabel(state.history?.started_at || state.generatedAt))}</p>`}</article>`;
  }).join('') || '<p class="pulse-empty">No data.</p>';
  // deals: needs >= 24h of history
  const pts = state.history?.points || [], now = pts.length ? new Date(pts[pts.length-1].t).getTime() : 0;
  const old = pts.filter(p => now - new Date(p.t).getTime() >= 24*3600e3).pop();
  const span = pts.length ? (now - new Date(pts[0].t).getTime())/3600e3 : 0;
  $('#history-note').textContent = pts.length ? `History: ${pts.length} snapshot${pts.length === 1 ? '' : 's'} since ${dateLabel(state.history.started_at)}. Purple line = cheapest overall, green = cheapest EU company.${old ? '' : ' “Deals today” appears once 24 hours of history exist (' + Math.max(0, 24 - span).toFixed(0) + ' h to go).'}` : '';
  if (!old) { $('#deals').hidden = true; return; }
  const last = pts[pts.length-1], deals = [];
  for (const [name, v] of Object.entries(last.g)) { const o = old.g[name]; if (!o) continue;
    [[0,'overall'],[2,'EU company']].forEach(([i,label]) => { if (Number.isFinite(v[i]) && Number.isFinite(o[i]) && v[i] < o[i]) deals.push({name, label, from:o[i], to:v[i], pct:(1 - v[i]/o[i])*100, provider:v[i+1]}); }); }
  deals.sort((a,b) => b.pct - a.pct);
  $('#deals').hidden = !deals.length;
  $('#deals-list').innerHTML = deals.slice(0,5).map(d => `<li><strong>${esc(d.name)}</strong> <span>${esc(d.label)}</span> <b>−${d.pct.toFixed(0)}%</b> <small>${money(d.from)} → ${money(d.to)} · ${esc(state.providers[d.provider]?.name || d.provider)}</small></li>`).join('');
  $('#deals-note').textContent = `Cheapest price now vs snapshot of ${dateLabel(old.t)}.`;
}
// ---- click analytics hook: no-op unless a privacy-friendly counter (e.g. GoatCounter) is loaded ----
window.eurogpuTrack = window.eurogpuTrack || function (provider, gpu) {
  if (window.goatcounter && window.goatcounter.count) window.goatcounter.count({ path: 'rent/' + provider + '/' + gpu, title: 'Rent click', event: true });
};
document.addEventListener('click', ev => { const a = ev.target.closest('[data-track]'); if (a) { const [p,g] = a.dataset.track.split('|'); try { window.eurogpuTrack(p,g); } catch {} } });
function applyData(prices, providers, mode) {
  if (!Array.isArray(prices.prices) || !Array.isArray(providers.providers)) throw new Error('Invalid price feed');
  state.prices = prices.prices.filter(row => typeof row.gpu === 'string' && typeof row.provider === 'string' && Number.isFinite(row.usd_hr));
  state.providers = Object.fromEntries(providers.providers.map(p => [p.id,p]));
  state.mode = mode;
  state.generatedAt = prices.generated_at; tickAgo();
  $('#updated-at').title = mode === 'snapshot' ? 'Using the bundled dataset. Refresh to try the published feed again.' : 'Latest published EuroGPU.watch dataset';
  $('#fx-note').textContent = prices.fx ? `EUR/USD ${prices.fx.EURUSD} (${prices.fx.date}).` : '';
  const models = [...new Set(state.prices.map(r => r.gpu))].sort();
  const previousModel = $('#model').value;
  $('#model').innerHTML = '<option value="">All models</option>' + models.map(gpu => `<option>${esc(gpu)}</option>`).join('');
  if (models.includes(previousModel)) $('#model').value = previousModel;
  drawQuickOffers();
  drawMini();
  draw();
  drawPulse();
}
async function fetchJson(url, signal) { const response = await fetch(url,{signal,cache:'no-cache'}); if (!response.ok) throw new Error('Feed unavailable'); return response.json(); }
async function refreshPrices() {
  if (state.loading) return;
  state.loading = true; $('#refresh').disabled = true; $('#refresh').setAttribute('aria-label','Refreshing prices');
  const controller = new AbortController(), timeout = setTimeout(() => controller.abort(),8000);
  try {
    const [prices,providers] = await Promise.all([fetchJson('data/prices.json',controller.signal),fetchJson('providers.json',controller.signal)]);
    try { state.history = await fetchJson('data/history.json',controller.signal); } catch { state.history = null; }
    applyData(prices,providers,'live');
  } catch {
    if (!state.prices.length) { $('#updated-at').textContent = 'Price data unavailable'; $('#offers').innerHTML = '<tr><td colspan="6" class="empty">Prices could not be loaded. Please refresh or visit the original EuroGPU.watch dataset.</td></tr>'; }
    else $('#updated-at').title = 'Could not refresh. Showing the most recently loaded dataset and its original timestamp.';
  } finally { clearTimeout(timeout); state.loading = false; $('#refresh').disabled = false; $('#refresh').setAttribute('aria-label','Refresh prices'); }
}
document.querySelectorAll('[data-gpu]').forEach(button => button.addEventListener('click',() => chooseGpu(button.dataset.gpu)));
['euhq','euloc','dpa','sort','model','best'].forEach(id => $('#'+id).addEventListener('change',filterChanged));
$('#price-sort').addEventListener('click',() => { $('#sort').value = $('#sort').value === 'asc' ? 'desc' : 'asc'; filterChanged(); });
$('#offers').addEventListener('click',event => { const button = event.target.closest('[data-detail]'); if (button) openOffer(Number(button.dataset.detail)); });
$('.dialog-close').addEventListener('click',() => $('#offer-dialog').close());
$('#offer-dialog').addEventListener('click',event => { if (event.target === $('#offer-dialog')) { const rect = event.target.getBoundingClientRect(); if (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom) event.target.close(); } });
$('#load-more').addEventListener('click',() => { state.limit += 12; draw(); });
$('#reset').addEventListener('click',() => { $('#euhq').checked = false; $('#euloc').checked = false; $('#dpa').checked = false; $('#best').checked = false; $('#sort').value = 'asc'; chooseGpu('H100'); });
document.querySelectorAll('[data-quick-gpu]').forEach(button => button.addEventListener('click',() => { quickFamily = button.dataset.quickGpu; drawQuickOffers(); }));
$('#quick-eu').addEventListener('change',drawQuickOffers);
$('#console-compare').addEventListener('click',() => { $('#euhq').checked = $('#quick-eu').checked; $('#euloc').checked = false; $('#dpa').checked = false; $('#best').checked = true; $('#sort').value = 'asc'; chooseGpu(quickFamily); });
$('#refresh').addEventListener('click',refreshPrices);
$('#eu-filter-link').addEventListener('click',() => { $('#euloc').checked = true; filterChanged(); });
$('.menu-toggle').addEventListener('click',() => { const open = $('.site-header nav').classList.toggle('open'); $('.menu-toggle').setAttribute('aria-expanded',String(open)); $('.menu-toggle').setAttribute('aria-label',open ? 'Close navigation' : 'Open navigation'); });
document.querySelectorAll('.site-header nav a').forEach(link => link.addEventListener('click',() => { $('.site-header nav').classList.remove('open'); $('.menu-toggle').setAttribute('aria-expanded','false'); $('.menu-toggle').setAttribute('aria-label','Open navigation'); }));
async function init() {
  const params = new URLSearchParams(location.search);
  if (params.has('eu')) $('#euhq').checked = params.get('eu') === '1';
  const family = params.get('gpu');
  if (family && [...document.querySelectorAll('[data-gpu]')].some(button => button.dataset.gpu === family.toUpperCase())) chooseGpu(family.toUpperCase());
  await refreshPrices();
}
init();
