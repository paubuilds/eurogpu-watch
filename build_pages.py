#!/usr/bin/env python3
"""Generate static SEO pages from data/prices.json + providers.json. No invented facts: every number comes from the data files."""
import json, re, os, html, datetime
# ---- CONFIG: change these two lines when moving to a custom domain ----
SITE_ORIGIN = "https://paubuilds.github.io"
BASE_PATH   = "/eurogpu-watch/"          # e.g. "/" for https://eurogpu.watch
SITE = SITE_ORIGIN + BASE_PATH
NAME = "EuroGPU.watch"
from gpu_models import GPUS, cheapest
e=html.escape
P=json.load(open("data/prices.json")); V={p["id"]:p for p in json.load(open("providers.json"))["providers"]}
GEN=P["generated_at"]; FX=P.get("fx") or {}
def is_eu(r):
    p=V.get(r["provider"],{}); return p.get("eu_incorporated") is True or r.get("eu_location") is True
def rows_for(rx): return sorted([r for r in P["prices"] if r.get("usd_hr") is not None and re.search(rx,r["gpu"],re.I)],key=lambda r:r["usd_hr"])
def cheapest_per_provider(rs):
    out={}; [out.setdefault(r["provider"],r) for r in rs]; return list(out.values())
def pname(r): return V.get(r["provider"],{}).get("name",r["provider"])
def rent(r):
    p=V.get(r["provider"],{}); u=p.get("affiliate_url")
    if not u: return ""
    rel="sponsored nofollow noopener" if p.get("link_is_referral") else "nofollow noopener"
    return f'<a class="rent-link" href="{e(u)}" target="_blank" rel="{rel}" aria-label="Rent at {e(p.get("name",""))}"><svg><use href="#external"/></svg></a>'
SYM={"gcore":"G","ovhcloud":"ovh","scaleway":"≋","verda":"v","nebius":"∷","runpod":"⬡","vast":"V"}
def exposure(p):
    m=re.match(r"(low|medium|high)",str(p.get("cloud_act_exposure","")),re.I); return m.group(1).lower() if m else "unknown"
def loc(r):
    raw=r.get("location") or "Not specified"
    for pat,name in [(r"^fr-par","Paris, France"),(r"^pl-waw","Warsaw, Poland"),(r"^nl-ams","Amsterdam, Netherlands"),(r"^multi-region incl. Luxembourg","Includes Luxembourg"),(r"^EU regions","EU regions"),(r"^unspecified","Not specified")]:
        if re.match(pat,raw,re.I): raw=name
    return f'<div class="location-cell">{e(raw)}<span>{"EU location listed" if r.get("eu_location") is True else "Confirm region with provider"}</span></div>'
def table(rs,best_all=None,best_eu=None):
    if not rs: return '<p class="page-empty">No live prices for this filter right now.</p>'
    out=[]
    for r in rs:
        p=V.get(r["provider"],{}); ex=exposure(p); nm=pname(r).replace(" (ex-DataCrunch)","")
        nat=f'€{r["native_price_hr"]:.2f} native rate' if r.get("currency")=="EUR" else "USD / GPU-hr"
        out.append(f'<tr><td><div class="gpu-cell"><span class="provider-icon {e(r["provider"])}" aria-hidden="true">{e(SYM.get(r["provider"],nm[0]))}</span><div><strong>{e(r["gpu"])}{"<span class=best-tag>BEST PRICE</span>" if best_all is not None and r["usd_hr"]==best_all else ""}{"<span class=\"best-tag eu\">BEST EU</span>" if best_eu is not None and r["usd_hr"]==best_eu and V.get(r["provider"],{}).get("eu_incorporated") is True else ""}</strong><small>{e(nm)} · {e(r.get("tier") or "")}</small></div></div></td>'
          f'<td>{loc(r)}</td><td><span class="hq"><span class="hq-code">{e(str(p.get("hq","?")))}</span></span></td><td><span class="exposure {ex}" title="{e(str(p.get("cloud_act_exposure","Not verified")))}">{ex.capitalize()}</span></td>'
          f'<td><strong class="offer-price">${r["usd_hr"]:.2f}</strong><span class="native-price">{nat}</span></td>'
          f'<td><div class="row-actions"><a class="source-link" href="{e(r["source"].split(" ")[0])}" rel="nofollow noopener" target="_blank" title="Fetched {e(r["fetched_at"])}">Source</a>{rent(r)}</div></td></tr>')
    return ('<div class="comparison"><div class="table-scroll"><table><thead><tr><th>GPU / Provider</th><th>Location</th><th>HQ</th><th>CLOUD Act exposure</th><th>Price / GPU-hr</th><th><span class="sr-only">Actions</span></th></tr></thead><tbody>'
            +"".join(out)+"</tbody></table></div></div>")
def head(title,desc,path,ld):
    url=SITE+path
    return (f'<title>{e(title)}</title>\n<meta name="description" content="{e(desc)}">\n<link rel="canonical" href="{url}">\n'
      f'<meta property="og:type" content="website"><meta property="og:site_name" content="{NAME}"><meta property="og:title" content="{e(title)}">'
      f'<meta property="og:description" content="{e(desc)}"><meta property="og:url" content="{url}"><meta name="twitter:card" content="summary">\n'
      + "".join(f'<script type="application/ld+json">{json.dumps(x,ensure_ascii=False)}</script>\n' for x in ld))
def nav():
    return '<a href="%s">Home</a>'%BASE_PATH + "".join(f'<a href="{BASE_PATH}gpu/{s}/">{n}</a>' for s,n,rx in GPUS if rows_for(rx)) + f'<a href="{BASE_PATH}eu-gdpr-gpu-cloud/">EU / GDPR guide</a>'
def faq_html(faq): return '<section class="faq page-faq" aria-labelledby="faq-title"><div><div class="eyebrow">GOOD QUESTIONS</div><h2 id="faq-title">FAQ</h2><span class="faq-asterisk" aria-hidden="true">✳</span></div><div class="faq-items">'+"".join(f"<details><summary>{e(q)}<span>+</span></summary><p>{a}</p></details>" for q,a in faq)+"</div></section>"
def faq_ld(faq): return {"@context":"https://schema.org","@type":"FAQPage","mainEntity":[{"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":re.sub("<[^>]+>","",a)}} for q,a in faq]}
def dataset_ld(name,desc,path):
    return {"@context":"https://schema.org","@type":"Dataset","name":name,"description":desc,"url":SITE+path,"dateModified":GEN,
      "creator":{"@type":"Organization","name":NAME,"url":SITE},"isAccessibleForFree":True,
      "distribution":[{"@type":"DataDownload","encodingFormat":"application/json","contentUrl":SITE+"data/prices.json"}],
      "variableMeasured":"GPU rental price per GPU-hour (USD; EUR converted at ECB reference rate)"}
# ---- newsletter (same Brevo endpoint + GDPR line as the home page) ----
NL_ACTION = 'https://9d237d23.sibforms.com/serve/MUIFABIgAxvxanofnM_TvgDXkpFG4KJzWpRWFOGdSxqy5LgvMJyYg5wtFyaegPVw_5HC8lmSAQ4P7KeyapQSHPHlx3c96zcgaia8-_Wx5Q-xsxU-tURMQR06d59dtYiRlmvSH9SDGKOG2BmwhRRjpHe0L_xp8irba-crKRwT0F2OeT78PFsXrf-erFDJJ8mk1mCALFc3npiI3cUt4Q=='
NL_GDPR = 'Weekly email, unsubscribe anytime. Stored in the EU by Brevo.'
def nl_form(fid, btn="Subscribe"):
    return (f'<form class="nl-form" action="{NL_ACTION}" method="post" target="_blank"><label class="sr-only" for="{fid}">Email address</label>'
            f'<div class="email-field nl-field"><input id="{fid}" name="EMAIL" type="email" placeholder="you@company.eu" required autocomplete="email"><button type="submit" class="nl-btn">{btn}</button></div>'
            f'<input type="text" name="email_address_check" class="honeypot" tabindex="-1" aria-hidden="true" autocomplete="off"><input type="hidden" name="locale" value="en"><small>{NL_GDPR}</small></form>')
def nl_card(title, line="Best EU prices, biggest drops, new providers. Every Monday. Free."):
    return f'<aside class="nl-card" aria-label="Newsletter signup"><div><div class="eyebrow">WEEKLY GPU PRICE CHECK-IN</div><h2>{e(title)}</h2><p>{e(line)}</p></div>{nl_form("nl-email-card")}</aside>'
ICONS=open("index.html").read().split('<svg class="icon-library"',1)[1].split("</svg>",1)[0] if os.path.exists("index.html") else ""
def page(path,title,desc,body,ld):
    os.makedirs(path.strip("/") or ".",exist_ok=True)
    m=re.match(r"<h1>(.*?)</h1><p>(.*?)</p>",body,re.S); h1,lede=(m.group(1),m.group(2)) if m else (e(title),""); rest=body[m.end():] if m else body
    B=BASE_PATH
    html_=f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="theme-color" content="#d6c5f4">
{head(title,desc,path,ld)}<link rel="icon" type="image/svg+xml" href="{B}assets/favicon.svg"><link rel="stylesheet" href="{B}assets/style.css"><link rel="stylesheet" href="{B}assets/pages.css"></head><body>
<svg class="icon-library" {ICONS}</svg>
<div class="hero-shell page-shell" id="top"><header class="site-header wrap"><a class="brand" href="{B}" aria-label="EuroGPU.watch home"><span class="brand-mark"><svg><use href="#chip"/></svg></span><span>EuroGPU<span class="brand-light">.watch</span></span></a>
<nav aria-label="Main navigation"><a href="{B}#explore">GPU prices</a><a href="{B}gpu/h100/">H100</a><a href="{B}gpu/a100/">A100</a><a href="{B}gpu/l40s/">L40S</a><a href="{B}eu-gdpr-gpu-cloud/">EU &amp; GDPR guide</a><a href="#nl-email-card">Newsletter</a></nav>
<a class="button nav-button" href="{B}#explore">All prices <svg><use href="#arrow"/></svg></a><button class="menu-toggle" aria-label="Open navigation" aria-expanded="false"><span></span><span></span></button></header>
<section class="page-hero wrap"><p class="hero-overline">LIVE · UPDATED {e(GEN[:16].replace("T"," "))} UTC</p><h1>{h1}</h1><p class="page-lede">{lede}</p></section></div>
<main class="page-body wrap">{rest}</main>
<section class="newsletter wrap page-news" id="newsletter"><div><div class="eyebrow">YOUR WEEKLY COMPUTE CHECK-IN</div><h2>Good GPUs.<br>Great finds. Your inbox.</h2><p>The cheapest GPUs in Europe, every Monday.</p></div>{nl_form("nl-email-bottom")}</section>
<aside class="nl-bar" id="nl-bar" hidden aria-label="Newsletter signup"><p><strong>Cheapest EU GPUs, every Monday.</strong> <span>Free · unsubscribe anytime</span></p>{nl_form("nl-email-bar")}<button class="nl-close" type="button" aria-label="Dismiss newsletter bar">×</button></aside>
<script src="{B}assets/newsletter.js" defer></script>
<footer class="site-footer wrap"><div class="footer-top"><a class="brand" href="{B}"><span class="brand-mark"><svg><use href="#chip"/></svg></span><span>EuroGPU<span class="brand-light">.watch</span></span></a><p>Data generated {e(GEN)} UTC from public provider APIs and pricing pages. EUR→USD at ECB rate {FX.get("EURUSD")} ({FX.get("date")}). EU prices usually exclude VAT. Not legal advice.</p><a href="#top">Back to top ↑</a></div>
<div class="footer-bottom"><span>© 2026 EuroGPU.watch · Some links are referral links; we may earn credits at no cost to you. Rankings are by price only.</span><div><a href="{B}providers.json">Provider sources ↗</a><a href="{B}data/prices.json">Price data ↗</a><a href="{B}#newsletter">Newsletter</a></div></div>
<nav class="footer-gpus" aria-label="GPU price pages">{nav()}</nav></footer>
<script>function ago(){{document.querySelectorAll('[data-ago]').forEach(function(el){{var m=Math.round((Date.now()-new Date(el.dataset.ago))/60000);el.textContent='updated '+(m<1?'just now':m<60?m+' min ago':Math.floor(m/60)+' h '+(m%60)+' min ago');}});}}ago();setInterval(ago,30000);
document.querySelector('.menu-toggle').addEventListener('click',function(){{var n=document.querySelector('.site-header nav'),o=n.classList.toggle('open');this.setAttribute('aria-expanded',String(o));}});</script>
</body></html>'''
    open(os.path.join(path.strip("/"),"index.html"),"w").write(html_)
def claims_list(pids):
    out=[]
    for pid in pids:
        p=V[pid]; c="; ".join(f'{e(x["claim"])} (<a href="{e(x["url"])}" rel=nofollow>{e(x["status"].split(" ")[0])}</a>)' for x in p.get("claims",[]))
        out.append(f"<li><b>{e(p['name'])}</b>: HQ {e(str(p['hq']))}, EU-incorporated: {e(str(p['eu_incorporated']))}, DPA: {e(str(p['dpa']))}, CLOUD Act exposure: {e(str(p['cloud_act_exposure']))}. {c}</li>")
    return '<ul class="claims">'+"".join(out)+"</ul>"
HIST=json.load(open("data/history.json")) if os.path.exists("data/history.json") else {"points":[]}
def spark_svg(name):
    pts=[p for p in HIST.get("points",[]) if name in p.get("g",{})]
    if len(pts)<2: return f'<p class="collecting">Collecting history since {e((HIST.get("started_at") or GEN)[:16].replace("T"," "))} UTC — chart appears after 2 snapshots.</p>'
    ts=[datetime.datetime.fromisoformat(p["t"]).timestamp() for p in pts]; vals=[v for p in pts for v in (p["g"][name][0],p["g"][name][2]) if isinstance(v,(int,float))]
    x0,x1,y0,y1=min(ts),max(ts),min(vals),max(vals); W,Hh=220,44
    X=lambda t:0 if x1==x0 else (t-x0)/(x1-x0)*W; Y=lambda v:Hh/2 if y1==y0 else Hh-(v-y0)/(y1-y0)*(Hh-6)-3
    def line(i): 
        q=[(X(t),Y(p["g"][name][i])) for t,p in zip(ts,pts) if isinstance(p["g"][name][i],(int,float))]
        return " ".join(("M" if k==0 else "L")+f"{x:.1f} {y:.1f}" for k,(x,y) in enumerate(q))
    return f'<svg class="spark" viewBox="0 0 {W} {Hh}" preserveAspectRatio="none" role="img" aria-label="{e(name)} price history, {len(pts)} snapshots"><path d="{line(0)}" class="spark-all"/><path d="{line(2)}" class="spark-eu"/></svg><small>{len(pts)} snapshots since {e(HIST["started_at"][:10])} · purple = cheapest overall, green = cheapest EU company</small>'
def stats_block(name,rx):
    a=cheapest(P["prices"],V,rx); b=cheapest(P["prices"],V,rx,True)
    if not a: return "",(None,None)
    prem=(b["usd_hr"]/a["usd_hr"]-1)*100 if b else None
    meter=(f'<div class="meter"><span style="width:{min(100,max(4,prem/2)):.0f}%"></span></div><small>{"No EU premium right now" if prem<=0.5 else f"EU premium +{prem:.0f}%"}: cheapest EU-company offer vs cheapest anywhere</small>' if prem is not None else '<div class="meter none"><span style="width:100%"></span></div><small>No EU-company offer right now</small>')
    return (f'<div class="page-stats"><article class="pulse-card"><div class="pulse-prices"><div><span>Best price</span><b>${a["usd_hr"]:.2f}</b><small>{e(pname(a))}</small></div><div><span>Best EU</span><b>{"$%.2f"%b["usd_hr"] if b else "–"}</b><small>{e(pname(b)) if b else "none listed"}</small></div></div></article>'
            f'<article class="pulse-card"><header><strong>EU premium</strong></header>{meter}</article><article class="pulse-card"><header><strong>Price history</strong></header>{spark_svg(name)}</article></div>'
            f'<p class="price-note">Dataset <span data-ago="{e(GEN)}">generated {e(GEN[:16].replace("T"," "))} UTC</span>.</p>'), (a["usd_hr"], b["usd_hr"] if b else None)
urls=[("",GEN)]
# ---- per-GPU pages ----
for slug,name,rx in GPUS:
    rs=rows_for(rx)
    if not rs: continue
    eu=cheapest_per_provider([r for r in rs if is_eu(r)]); allc=rs[:25]
    sb,(ba,be)=stats_block(name,rx)
    path=f"gpu/{slug}/"; ce=eu[0] if eu else None
    title=f"{name} price in Europe – cheapest EU / GDPR GPU cloud | {NAME}"
    desc=(f"Live {name} rental prices from EU-headquartered or EU-located providers. Cheapest right now: ${ce['usd_hr']:.2f}/GPU-hr at {pname(ce)}." if ce else f"Live {name} rental prices; no EU offer found at last update.")+f" Updated {GEN[:16]} UTC."
    faq=[(f"What is the cheapest {name} in Europe right now?",
          f"At the last update ({GEN} UTC) the cheapest {name} from an EU-incorporated provider or EU-located host was ${ce['usd_hr']:.2f} per GPU-hour at {e(pname(ce))} ({e(ce.get('tier') or '')}), source: {e(ce['source'].split(' ')[0])}." if ce else f"No EU-incorporated or EU-located {name} offer was found at the last update ({GEN} UTC)."),
         (f"What is the cheapest {name} worldwide?", f"${rs[0]['usd_hr']:.2f} per GPU-hour at {e(pname(rs[0]))} ({e(rs[0].get('tier') or '')}, location: {e(rs[0].get('location') or 'unspecified')}) as of {GEN} UTC."),
         ("How are prices collected?","Prices are fetched automatically from each provider's public API or pricing page about every 15 minutes. Each row links to its source and fetch timestamp. EUR prices are converted at the ECB reference rate; EU prices usually exclude VAT."),
         ("Does an EU provider protect me from the US CLOUD Act?","Providers incorporated in the EU without a US parent generally carry lower CLOUD Act exposure than US-headquartered providers, but this is a simplification and not legal advice. See the EU / GDPR guide and each provider's sources.")]
    body=(f"<h1>{e(name)} price in Europe</h1><p>Live {e(name)} GPU rental prices, filtered for EU data residency. {len(rs)} live {e(name)} offers tracked; {len(eu)} providers with an EU-incorporated entity or EU-located host.</p>"
          +sb+f"<h2>Cheapest EU {e(name)} per provider</h2>{table(eu,ba,be)}"+nl_card(f"Get {name} price drops weekly")+f"<h2>All {e(name)} offers, cheapest first (any jurisdiction, top 25)</h2>{table(allc,ba,be)}"
          +f"<h2>EU providers offering {e(name)}</h2>"+(claims_list(sorted({r['provider'] for r in eu if r['provider'] in V})) if eu else "<p>None at last update.</p>")+faq_html(faq))
    page(path,title,desc,body,[dataset_ld(f"{name} GPU rental prices in Europe",desc,path),faq_ld(faq)]); urls.append((path,GEN))
# ---- EU / GDPR guide ----
eu_all=sorted([r for r in P["prices"] if is_eu(r) and r.get("usd_hr") is not None],key=lambda r:r["usd_hr"])
best={}; [best.setdefault(n,r) for r in eu_all for s,n,rx in GPUS if re.search(rx,r["gpu"],re.I)]
euids=[k for k,p in V.items() if p.get("eu_incorporated") is True]; usids=[k for k,p in V.items() if p.get("eu_incorporated") is False]
faq=[("Which GPU cloud providers are incorporated in the EU?", "Tracked EU-incorporated providers: "+", ".join(e(V[k]["name"])+f" ({e(str(V[k]['hq']))})" for k in euids)+". Each claim links to the provider's own page."),
     ("Which tracked GPU clouds are US-headquartered?", ", ".join(e(V[k]["name"]) for k in usids)+". US-headquartered companies are subject to the US CLOUD Act regardless of where data is stored."),
     ("Do these providers offer a GDPR Data Processing Agreement (DPA)?","See the DPA field per provider below; each is linked to the source we checked, and claims we could not confirm are marked unverified."),
     ("Is this legal advice?","No. It is a factual summary of public provider documents. Check the linked sources and consult your DPO or lawyer.")]
body=("<h1>EU / GDPR GPU cloud: providers, DPAs and CLOUD Act exposure</h1><p>A source-linked comparison of GPU cloud providers by EU incorporation, DPA availability and US CLOUD Act exposure, with live prices.</p>"
      "<h2>Cheapest EU price per GPU model</h2>"+table([best[n] for s,n,rx in GPUS if n in best])+nl_card("Get EU GPU price drops weekly")+
      "<h2>EU-incorporated providers</h2>"+claims_list(euids)+"<h2>US-headquartered providers</h2>"+claims_list(usids)+faq_html(faq))
desc="Compare EU-incorporated vs US-headquartered GPU clouds: DPA availability, CLOUD Act exposure and live cheapest EU GPU prices, all with sources."
page("eu-gdpr-gpu-cloud/","EU GDPR GPU cloud – DPA & CLOUD Act comparison with live prices | "+NAME,desc,body,[dataset_ld("EU GPU cloud prices and compliance",desc,"eu-gdpr-gpu-cloud/"),faq_ld(faq)]); urls.append(("eu-gdpr-gpu-cloud/",GEN))
# ---- home page head/nav injection ----
h=open("index.html").read()
hd=head(f"{NAME} – live GPU prices with EU data residency, GDPR & CLOUD Act filter","Live H100, A100, L40S, RTX 4090 rental prices from EU and US GPU clouds, filterable by EU incorporation, DPA and CLOUD Act exposure. Every price sourced and timestamped.","",[dataset_ld("EuroGPU.watch GPU rental prices","Live GPU rental prices with EU residency metadata","")])
h=re.sub(r"<title>.*?</title>\n?","",h,flags=re.S)
h=re.sub(r"<!--SEO-->.*?<!--/SEO-->","<!--SEO-->\n"+hd.replace("\\","\\\\")+"<!--/SEO-->",h,flags=re.S)
h=re.sub(r"<!--NAV-->.*?<!--/NAV-->","<!--NAV-->"+nav()+"<!--/NAV-->",h,flags=re.S)
open("index.html","w").write(h)
# ---- sitemap, robots, llms.txt ----
open("sitemap.xml","w").write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'+"".join(f"<url><loc>{SITE}{p}</loc><lastmod>{d[:10]}</lastmod><changefreq>hourly</changefreq></url>\n" for p,d in urls)+"</urlset>\n")
bots=["GPTBot","OAI-SearchBot","ChatGPT-User","ClaudeBot","Claude-User","Claude-SearchBot","PerplexityBot","Perplexity-User","Google-Extended","Applebot-Extended","CCBot","Bingbot","Googlebot"]
open("robots.txt","w").write("".join(f"User-agent: {b}\nAllow: /\n\n" for b in bots)+"User-agent: *\nAllow: /\n\n"+f"Sitemap: {SITE}sitemap.xml\n")
lt=[f"# {NAME}","",f"> Live GPU rental price tracker for Europe. Filters by EU incorporation, GDPR DPA availability and US CLOUD Act exposure. Prices are fetched from public provider APIs/pages every ~15 min; last update {GEN} UTC.","",
    "## Data",f"- [Live prices JSON]({SITE}data/prices.json): every row has provider, gpu, usd_hr, native price/currency, source URL, fetched_at",
    f"- [Provider compliance JSON]({SITE}providers.json): HQ, EU incorporation, DPA, CLOUD Act exposure, claims with source URLs and verification status","","## Pages",
    f"- [EU / GDPR GPU cloud guide]({SITE}eu-gdpr-gpu-cloud/)"]+[f"- [{n} price in Europe]({SITE}{p})" for p,_ in urls if p.startswith("gpu/") for s,n,rx in GPUS if p==f"gpu/{s}/"]+["","## Cheapest EU price per GPU (last update)"]+[f"- {n}: ${r['usd_hr']:.2f}/GPU-hr at {pname(r)} ({r['source'].split(' ')[0]}, fetched {r['fetched_at']})" for n,r in best.items()]+["","Not legal advice. Hetzner and Genesis Cloud prices are not tracked."]
open("llms.txt","w").write("\n".join(lt)+"\n")
open(".nojekyll","w").write("")
print("pages:",len(urls),"; EU best:",{n:r['usd_hr'] for n,r in best.items()})
