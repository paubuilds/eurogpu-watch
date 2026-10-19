'use strict';
const $ = (selector) => document.querySelector(selector);
const esc = (value) => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const safeUrl = (value) => { try { const url = new URL(String(value).split(' ')[0]); return ['http:', 'https:'].includes(url.protocol) ? url.href : '#'; } catch { return '#'; } };
const state = { prices: [], providers: {}, family: 'H100', limit: 6, visible: [], loading: false, mode: 'snapshot' };
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
  const matchedCount = rows.length, providerCount = new Set(rows.map(row => row.provider)).size;
  rows.sort((a,b) => (Number.isFinite(a.usd_hr) ? a.usd_hr : Infinity) - (Number.isFinite(b.usd_hr) ? b.usd_hr : Infinity));
  if ($('#best').checked) { const seen = new Set(); rows = rows.filter(row => !seen.has(row.provider) && seen.add(row.provider)); }
  if ($('#sort').value === 'desc') rows.reverse();
  const cheapest = rows.reduce((min,row) => Number.isFinite(row.usd_hr) ? Math.min(min,row.usd_hr) : min, Infinity);
  state.visible = rows.slice(0,state.limit);
  $('#results-count').textContent = `${matchedCount} matching offer${matchedCount === 1 ? '' : 's'} · ${providerCount} provider${providerCount === 1 ? '' : 's'}`;
  $('#offers').innerHTML = state.visible.map((row,index) => {
    const p = state.providers[row.provider] || {}, ex = exposure(p), name = p.name || row.provider;
    return `<tr><td><div class="gpu-cell"><span class="provider-icon ${esc(row.provider)}" aria-hidden="true">${esc(symbols[row.provider] || name[0])}</span><div><strong>${esc(row.gpu)}${row.usd_hr === cheapest ? '<span class="best-tag">LOWEST</span>' : ''}</strong><small>${esc(name.replace(' (ex-DataCrunch)',''))}</small></div></div></td><td>${locationInfo(row)}</td><td><span class="hq"><span class="hq-code">${esc(p.hq || '?')}</span>${esc(countries[p.hq] || p.hq || 'Unknown')}</span></td><td><span class="exposure ${ex}" title="${esc(p.cloud_act_exposure || 'Not verified')}">${ex[0].toUpperCase() + ex.slice(1)}</span></td><td><strong class="offer-price">${money(row.usd_hr)}</strong><span class="native-price">${row.currency === 'EUR' ? esc(nativeMoney(row)) + ' native rate' : 'USD / GPU-hr'}</span></td><td><div class="row-actions"><button class="details-button" data-detail="${index}" aria-label="Details for ${esc(row.gpu)} from ${esc(name)}">Details</button>${p.affiliate_url ? `<a class="rent-link" href="${esc(safeUrl(p.affiliate_url))}" target="_blank" rel="${p.link_is_referral ? 'sponsored nofollow noopener' : 'noopener'}" aria-label="Rent ${esc(row.gpu)} from ${esc(name)}"><svg><use href="#external"/></svg></a>` : ''}</div></td></tr>`;
  }).join('') || '<tr><td colspan="6" class="empty">No offers match these filters. Try another GPU or reset the filters.</td></tr>';
  $('#showing').textContent = `Showing ${state.visible.length} of ${rows.length}${$('#best').checked ? ' best provider offers' : ' offers'} · Sources in Details`;
  $('#load-more').hidden = state.limit >= rows.length;
  $('#price-sort span').textContent = $('#sort').value === 'asc' ? '↑' : '↓';
}
function filterChanged() { state.limit = 6; draw(); }
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
  $('#dialog-content').innerHTML = `<p class="dialog-kicker">${esc(p.name || row.provider)} · OFFER DETAILS</p><h2 id="dialog-title">${esc(row.gpu)}</h2><div class="dialog-price">${money(row.usd_hr)} <span>/ GPU-hour</span></div><dl class="detail-list">${fields.map(([key,value]) => `<div><dt>${key}</dt><dd>${value}</dd></div>`).join('')}</dl>${p.claims?.length ? `<details class="dialog-claims"><summary>Provider evidence &amp; verification notes<span>+</span></summary><ul>${p.claims.map(c => `<li><a href="${esc(safeUrl(c.url))}" target="_blank" rel="noopener">${esc(c.claim)} ↗</a><br>${esc(c.status)}</li>`).join('')}</ul></details>` : ''}<p class="dialog-disclaimer">${p.link_is_referral ? 'This is a referral link. EuroGPU.watch may earn credits at no additional cost to you. ' : ''}Confirm availability, region, taxes and included resources with the provider. Jurisdiction indicators are not a compliance guarantee.</p>${p.affiliate_url ? `<a class="button" href="${esc(safeUrl(p.affiliate_url))}" target="_blank" rel="${p.link_is_referral ? 'sponsored nofollow noopener' : 'noopener'}">View offer at ${esc((p.name || row.provider).replace(' (ex-DataCrunch)',''))} <svg><use href="#external"/></svg></a>` : ''}`;
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
function applyData(prices, providers, mode) {
  if (!Array.isArray(prices.prices) || !Array.isArray(providers.providers)) throw new Error('Invalid price feed');
  state.prices = prices.prices.filter(row => typeof row.gpu === 'string' && typeof row.provider === 'string' && Number.isFinite(row.usd_hr));
  state.providers = Object.fromEntries(providers.providers.map(p => [p.id,p]));
  state.mode = mode;
  $('#updated-at').textContent = `${mode === 'snapshot' ? 'Snapshot' : 'Updated'} · ${dateLabel(prices.generated_at)}`;
  $('#updated-at').title = mode === 'snapshot' ? 'Using the bundled dataset. Refresh to try the published feed again.' : 'Latest published EuroGPU.watch dataset';
  $('#fx-note').textContent = prices.fx ? `EUR/USD ${prices.fx.EURUSD} (${prices.fx.date}).` : '';
  const models = [...new Set(state.prices.map(r => r.gpu))].sort();
  const previousModel = $('#model').value;
  $('#model').innerHTML = '<option value="">All models</option>' + models.map(gpu => `<option>${esc(gpu)}</option>`).join('');
  if (models.includes(previousModel)) $('#model').value = previousModel;
  drawQuickOffers();
  drawMini();
  draw();
}
async function fetchJson(url, signal) { const response = await fetch(url,{signal,cache:'no-cache'}); if (!response.ok) throw new Error('Feed unavailable'); return response.json(); }
async function refreshPrices() {
  if (state.loading) return;
  state.loading = true; $('#refresh').disabled = true; $('#refresh').setAttribute('aria-label','Refreshing prices');
  const controller = new AbortController(), timeout = setTimeout(() => controller.abort(),8000);
  try {
    const [prices,providers] = await Promise.all([fetchJson('data/prices.json',controller.signal),fetchJson('providers.json',controller.signal)]);
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
$('#reset').addEventListener('click',() => { $('#euhq').checked = true; $('#euloc').checked = false; $('#dpa').checked = false; $('#best').checked = true; $('#sort').value = 'asc'; chooseGpu('H100'); });
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
