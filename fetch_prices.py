#!/usr/bin/env python3
"""Fetch live GPU prices -> data/prices.json. Every row carries source + fetched_at. No invented prices."""
import json, urllib.request, datetime, re
import urllib.parse
UA={"User-Agent":"EuroGPU.watch-MVP/0.1 (contact: TBD)"}
EU={"AT","BE","BG","HR","CY","CZ","DK","EE","FI","FR","DE","GR","HU","IE","IT","LV","LT","LU","MT","NL","PL","PT","RO","SK","SI","ES","SE"}
def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
def get(url, data=None, h={}):
    r=urllib.request.Request(url, data=data, headers={**UA, **h}); return json.load(urllib.request.urlopen(r, timeout=30))
rows=[]; status={}
def norm(g): return re.sub(r"^(NVIDIA|AMD Instinct|GeForce)\s+","",g).strip()
# 1 watchworks
try:
    d=get("https://gpu.watchworks.dev/api/prices"); t=now()
    for p in d["prices"]:
        rows.append(dict(provider=p["provider"],gpu=norm(p["gpu"]),tier=p.get("kind"),usd_hr=p["usd_hr"],location=None,eu_location=None,
          source="https://gpu.watchworks.dev/api/prices",source_updated_at=d.get("updated_at"),fetched_at=t))
    status["watchworks"]=f"ok {len(d['prices'])}"
except Exception as e: status["watchworks"]=f"error {e}"
# 2 runpod graphql (public, no key)
try:
    q='{"query":"{ gpuTypes { id displayName memoryInGb securePrice communityPrice } }"}'
    d=get("https://api.runpod.io/graphql",q.encode(),{"content-type":"application/json"}); t=now(); n=0
    for g in d["data"]["gpuTypes"]:
        for tier,k in (("secure","securePrice"),("community","communityPrice")):
            if g.get(k): rows.append(dict(provider="runpod",gpu=g["displayName"],tier=tier,usd_hr=g[k],location=None,eu_location=None,
                source="https://api.runpod.io/graphql (gpuTypes)",source_updated_at=None,fetched_at=t)); n+=1
    status["runpod"]=f"ok {n}"
except Exception as e: status["runpod"]=f"error {e}"
# 3 vast marketplace: cheapest per GPU model, split EU / non-EU by host geolocation
try:
    q=json.dumps({"rentable":{"eq":True},"verified":{"eq":True},"limit":1000,"order":[["dph_total","asc"]]})
    d=get("https://console.vast.ai/api/v0/bundles/?q="+urllib.parse.quote(q)); t=now(); best={}
    for o in d["offers"]:
        cc=(o.get("geolocation") or "").split(",")[-1].strip(); eu=cc in EU
        per=o["dph_total"]/max(o.get("num_gpus") or 1,1); key=(o["gpu_name"],eu)
        if key not in best or per<best[key][0]: best[key]=(per,o.get("geolocation"))
    for (g,eu),(per,loc) in best.items():
        rows.append(dict(provider="vast",gpu=g,tier="marketplace min, per GPU",usd_hr=round(per,4),location=loc,eu_location=eu,
            source="https://console.vast.ai/api/v0/bundles/",source_updated_at=None,fetched_at=t))
    status["vast"]=f"ok {len(d['offers'])} offers -> {len(best)} rows"
except Exception as e: status["vast"]=f"error {e}"
# ---------- EU-HQ providers ----------
def add(prov,gpu,tier,price,cur,loc,eu,src,t,n=1):
    rows.append(dict(provider=prov,gpu=norm(gpu),tier=tier,usd_hr=None,native_price_hr=round(price/n,4),currency=cur,gpus_in_instance=n,
        location=loc,eu_location=eu,source=src,source_updated_at=None,fetched_at=t))
import subprocess, html as H
def rendered_text(url):
    dom=subprocess.run(["google-chrome","--headless=new","--no-sandbox","--disable-gpu","--virtual-time-budget=8000","--dump-dom",url],capture_output=True,text=True,timeout=60).stdout
    t=re.sub(r"<script.*?</script>|<style.*?</style>","",dom,flags=re.S); t=H.unescape(re.sub(r"<[^>]+>"," | ",t)); return re.sub(r"(\s*\|\s*)+"," | ",t)
def run(name,fn):
    n0=len(rows)
    try: fn(); status[name]=f"ok {len(rows)-n0}"
    except Exception as e: status[name]=f"error {type(e).__name__}: {e}"
def ovh():
    u="https://eu.api.ovh.com/v1/order/catalog/public/cloud?ovhSubsidiary=FR"; d=get(u); t=now()
    for a in d["addons"]:
        pc=a["planCode"]; g=((a.get("blobs") or {}).get("technical") or {}).get("gpu")
        if not g or not re.match(r"^[a-z0-9]+-\d+\.consumption$",pc): continue
        p=[x for x in a["pricings"] if x.get("intervalUnit")=="hour"]
        if p: add("ovhcloud",g["model"],"public cloud on-demand ("+pc.split('.')[0]+", excl. VAT)",p[0]["price"]/1e8,"EUR","EU regions (see source)",None,u,t,g.get("number") or 1)
def scaleway():
    for z in ["fr-par-2","nl-ams-1","pl-waw-2"]:
        u=f"https://api.scaleway.com/instance/v1/zones/{z}/products/servers"; d=get(u)["servers"]; t=now()
        for k,v in d.items():
            if v.get("gpu") and v.get("hourly_price"): add("scaleway",v["gpu_info"]["gpu_name"],f"on-demand {k}",v["hourly_price"],"EUR",z,True,u,t,v["gpu"])
def verda():
    u="https://api.datacrunch.io/v1/instance-types"; d=get(u); t=now()
    for x in d:
        n=x["gpu"]["number_of_gpus"]
        if n and float(x["price_per_hour"])>0: add("verda",x["model"],f"on-demand {x['instance_type']}",float(x["price_per_hour"]),x["currency"].upper(),"unspecified (FI/IS/other)",None,u,t,n)
def nebius():
    u="https://nebius.com/prices"; h=urllib.request.urlopen(urllib.request.Request(u,headers={"User-Agent":"Mozilla/5.0"}),timeout=30).read().decode()
    tx=re.sub(r"<script.*?</script>|<style.*?</style>","",h,flags=re.S); tx=H.unescape(re.sub(r"<[^>]+>"," | ",tx)); tx=re.sub(r"(\s*\|\s*)+"," | ",tx); t=now()
    sec=tx.split("Preemptible")[0]
    for m in re.finditer(r"NVIDIA ([A-Z][\w ]+?) \| [\d-]+ \| [\d-]+ \| (from )?\$([\d.]+)",sec):
        add("nebius",m.group(1).replace("HGX ",""),"on-demand"+(" (from)" if m.group(2) else ""),float(m.group(3)),"USD","unspecified (FI/FR/US/...)",None,u,t)
def gcore():
    u="https://gcore.com/pricing/ai"; tx=rendered_text(u); t=now()
    pr=re.findall(r"€([\d.]+) per GPU",tx); cfg=re.search(r"Configuration \| GPU \| (.*?) \| [A-Z][a-z]",tx).group(1).split(" | ")
    gp=[re.sub(r"^\d+×","",c) for c in cfg]
    if not pr or len(pr)>len(gp): raise ValueError("layout changed")
    for g,p in zip(gp,pr): add("gcore",g,"GPU cloud bare-metal (per GPU, excl. VAT)",float(p),"EUR","multi-region incl. Luxembourg (see source)",None,u,t)
for n,f in [("ovhcloud",ovh),("scaleway",scaleway),("verda",verda),("nebius",nebius),("gcore",gcore)]: run(n,f)
status["hetzner"]="skipped: GEX GPU prices are rendered client-side only after interaction; no public API without account token"
status["genesiscloud"]="skipped: www.genesiscloud.com TLS handshake fails from this host (curl err 35, headless Chrome empty)"
# FX: ECB daily reference rate, for USD comparison column only
try:
    x=get("https://api.frankfurter.app/latest?from=EUR&to=USD")
    usd=x["rates"]["USD"]; fxdate=x["date"]
except Exception: usd=None; fxdate=None
for r in rows:
    if r.get("currency") is None: r["currency"]="USD"; r["native_price_hr"]=r["usd_hr"]
    if r["usd_hr"] is None: r["usd_hr"]=round(r["native_price_hr"]*(usd if r["currency"]=="EUR" else 1),4) if (r["currency"]=="USD" or usd) else None
fx={"EURUSD":usd,"date":fxdate,"source":"https://api.frankfurter.app (ECB reference rates)"}
# dedupe: drop watchworks runpod rows when Runpod's own API returned the same GPU+tier
_rp={(r['gpu'].lower(),r['tier']) for r in rows if r['provider']=='runpod' and 'api.runpod.io' in r['source']}
# Runpod's own API is authoritative; watchworks names differ slightly (e.g. 'A100 SXM 80GB' vs 'A100 SXM'), so drop all watchworks Runpod rows when the API succeeded
_n=len(rows)
if _rp: rows[:]=[r for r in rows if not ('watchworks' in r['source'] and r['provider']=='runpod')]
status['dedupe']=f"removed {_n-len(rows)} watchworks runpod rows (Runpod API used instead)"
import os; os.makedirs("data",exist_ok=True)
json.dump({"generated_at":now(),"status":status,"fx":fx,"prices":rows},open("data/prices.json","w"),indent=1)
print(status, len(rows))
