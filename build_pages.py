#!/usr/bin/env python3
"""Generate static SEO pages from data/prices.json + providers.json. No invented facts: every number comes from the data files."""
import json, re, os, html, datetime
# ---- CONFIG: change these two lines when moving to a custom domain ----
SITE_ORIGIN = "https://paubuilds.github.io"
BASE_PATH   = "/eurogpu-watch/"          # e.g. "/" for https://eurogpu.watch
SITE = SITE_ORIGIN + BASE_PATH
NAME = "EuroGPU.watch"
GPUS = [  # slug, display name, regex matching normalized GPU names in data
 ("h100","H100",r"\bH100\b"),("h200","H200",r"\bH200\b"),("b200","B200",r"\bB200\b"),("a100","A100",r"\bA100\b"),
 ("l40s","L40S",r"\bL40S\b"),("l4","L4",r"^(NVIDIA )?L4$"),("rtx-4090","RTX 4090",r"4090"),("rtx-5090","RTX 5090",r"5090"),
 ("rtx-a6000","RTX A6000",r"A6000"),("rtx-pro-6000","RTX PRO 6000",r"PRO 6000"),("a10","A10",r"^A10$|\bA10 ")]
e=html.escape
P=json.load(open("data/prices.json")); V={p["id"]:p for p in json.load(open("providers.json"))["providers"]}
GEN=P["generated_at"]; FX=P.get("fx") or {}
def is_eu(r):
    p=V.get(r["provider"],{}); return p.get("eu_incorporated") is True or r.get("eu_location") is True
def rows_for(rx): return sorted([r for r in P["prices"] if r.get("usd_hr") is not None and re.search(rx,r["gpu"],re.I)],key=lambda r:r["usd_hr"])
def cheapest_per_provider(rs):
    out={}; [out.setdefault(r["provider"],r) for r in rs]; return list(out.values())
def pname(r): return V.get(r["provider"],{}).get("name",r["provider"])
def table(rs):
    if not rs: return "<p>No live prices for this filter right now.</p>"
    t="".join(f"<tr><td>{e(r['gpu'])}</td><td>{e(pname(r))}</td><td>{e(r.get('tier') or '')}</td><td><b>${r['usd_hr']:.2f}</b></td>"
      f"<td>{'€%.2f'%r['native_price_hr'] if r.get('currency')=='EUR' else ''}</td><td>{e(r.get('location') or 'unspecified')}</td>"
      f"<td>{e(V.get(r['provider'],{}).get('hq',''))}</td><td><a href=\"{e(r['source'].split(' ')[0])}\" rel=nofollow>source</a> {e(r['fetched_at'])}</td></tr>" for r in rs)
    return f"<table><thead><tr><th>GPU</th><th>Provider</th><th>Offer</th><th>$/GPU-hr</th><th>Native</th><th>Location</th><th>HQ</th><th>Source / fetched (UTC)</th></tr></thead><tbody>{t}</tbody></table>"
CSS="body{font-family:system-ui,sans-serif;margin:2rem auto;max-width:1100px;padding:0 1rem;color:#1a1a2e;line-height:1.5}a{color:#0033a0}table{border-collapse:collapse;width:100%;font-size:14px}th,td{padding:6px 8px;border-bottom:1px solid #ddd;text-align:left}th{background:#0033a0;color:#fff}small,.muted{color:#666}nav a{margin-right:.6rem}details{margin:.4rem 0}"
def head(title,desc,path,ld):
    url=SITE+path
    return (f'<title>{e(title)}</title>\n<meta name="description" content="{e(desc)}">\n<link rel="canonical" href="{url}">\n'
      f'<meta property="og:type" content="website"><meta property="og:site_name" content="{NAME}"><meta property="og:title" content="{e(title)}">'
      f'<meta property="og:description" content="{e(desc)}"><meta property="og:url" content="{url}"><meta name="twitter:card" content="summary">\n'
      + "".join(f'<script type="application/ld+json">{json.dumps(x,ensure_ascii=False)}</script>\n' for x in ld))
def nav():
    return '<a href="%s">Home</a>'%BASE_PATH + "".join(f'<a href="{BASE_PATH}gpu/{s}/">{n}</a>' for s,n,rx in GPUS if rows_for(rx)) + f'<a href="{BASE_PATH}eu-gdpr-gpu-cloud/">EU / GDPR guide</a>'
def faq_html(faq): return "<h2>FAQ</h2>"+"".join(f"<details open><summary><b>{e(q)}</b></summary><p>{a}</p></details>" for q,a in faq)
def faq_ld(faq): return {"@context":"https://schema.org","@type":"FAQPage","mainEntity":[{"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":re.sub("<[^>]+>","",a)}} for q,a in faq]}
def dataset_ld(name,desc,path):
    return {"@context":"https://schema.org","@type":"Dataset","name":name,"description":desc,"url":SITE+path,"dateModified":GEN,
      "creator":{"@type":"Organization","name":NAME,"url":SITE},"isAccessibleForFree":True,
      "distribution":[{"@type":"DataDownload","encodingFormat":"application/json","contentUrl":SITE+"data/prices.json"}],
      "variableMeasured":"GPU rental price per GPU-hour (USD; EUR converted at ECB reference rate)"}
def page(path,title,desc,body,ld):
    os.makedirs(path.strip("/") or ".",exist_ok=True)
    open(os.path.join(path.strip("/"),"index.html"),"w").write(f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">\n{head(title,desc,path,ld)}<style>{CSS}</style></head><body><nav>{nav()}</nav>{body}'
      f'<hr><p class="muted"><small>Data generated {e(GEN)} UTC from public provider APIs and pricing pages. EUR→USD at ECB rate {FX.get("EURUSD")} ({FX.get("date")}). EU prices usually exclude VAT. Not legal advice. <a href="{BASE_PATH}">Live table</a> · <a href="{BASE_PATH}providers.json">providers.json</a> · <a href="{BASE_PATH}data/prices.json">prices.json</a></small></p></body></html>')
def claims_list(pids):
    out=[]
    for pid in pids:
        p=V[pid]; c="; ".join(f'{e(x["claim"])} (<a href="{e(x["url"])}" rel=nofollow>{e(x["status"].split(" ")[0])}</a>)' for x in p.get("claims",[]))
        out.append(f"<li><b>{e(p['name'])}</b>: HQ {e(str(p['hq']))}, EU-incorporated: {e(str(p['eu_incorporated']))}, DPA: {e(str(p['dpa']))}, CLOUD Act exposure: {e(str(p['cloud_act_exposure']))}. {c}</li>")
    return "<ul>"+"".join(out)+"</ul>"
urls=[("",GEN)]
# ---- per-GPU pages ----
for slug,name,rx in GPUS:
    rs=rows_for(rx)
    if not rs: continue
    eu=cheapest_per_provider([r for r in rs if is_eu(r)]); allc=cheapest_per_provider(rs)[:10]
    path=f"gpu/{slug}/"; ce=eu[0] if eu else None
    title=f"{name} price in Europe – cheapest EU / GDPR GPU cloud | {NAME}"
    desc=(f"Live {name} rental prices from EU-headquartered or EU-located providers. Cheapest right now: ${ce['usd_hr']:.2f}/GPU-hr at {pname(ce)}." if ce else f"Live {name} rental prices; no EU offer found at last update.")+f" Updated {GEN[:16]} UTC."
    faq=[(f"What is the cheapest {name} in Europe right now?",
          f"At the last update ({GEN} UTC) the cheapest {name} from an EU-incorporated provider or EU-located host was ${ce['usd_hr']:.2f} per GPU-hour at {e(pname(ce))} ({e(ce.get('tier') or '')}), source: {e(ce['source'].split(' ')[0])}." if ce else f"No EU-incorporated or EU-located {name} offer was found at the last update ({GEN} UTC)."),
         (f"What is the cheapest {name} worldwide?", f"${rs[0]['usd_hr']:.2f} per GPU-hour at {e(pname(rs[0]))} ({e(rs[0].get('tier') or '')}, location: {e(rs[0].get('location') or 'unspecified')}) as of {GEN} UTC."),
         ("How are prices collected?","Prices are fetched automatically from each provider's public API or pricing page about every 15 minutes. Each row links to its source and fetch timestamp. EUR prices are converted at the ECB reference rate; EU prices usually exclude VAT."),
         ("Does an EU provider protect me from the US CLOUD Act?","Providers incorporated in the EU without a US parent generally carry lower CLOUD Act exposure than US-headquartered providers, but this is a simplification and not legal advice. See the EU / GDPR guide and each provider's sources.")]
    body=(f"<h1>{e(name)} price in Europe</h1><p>Live {e(name)} GPU rental prices, filtered for EU data residency. {len(rs)} live {e(name)} offers tracked; {len(eu)} providers with an EU-incorporated entity or EU-located host.</p>"
          f"<h2>Cheapest EU {e(name)} per provider</h2>{table(eu)}<h2>Cheapest {e(name)} overall (any jurisdiction)</h2>{table(allc)}"
          f"<h2>EU providers offering {e(name)}</h2>"+(claims_list(sorted({r['provider'] for r in eu if r['provider'] in V})) if eu else "<p>None at last update.</p>")+faq_html(faq))
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
      "<h2>Cheapest EU price per GPU model</h2>"+table([best[n] for s,n,rx in GPUS if n in best])+
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
