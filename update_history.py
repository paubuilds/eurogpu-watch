#!/usr/bin/env python3
"""Append a compact snapshot of data/prices.json to data/history.json.
Each point: t (UTC), and per GPU model [cheapest overall $/GPU-hr, provider, cheapest EU-company $/GPU-hr, provider] (null if none).
Size cap: every run kept for 7 days, older points thinned to the last point of each UTC day, max 400 days."""
import json, os, datetime
from gpu_models import GPUS, cheapest
KEEP_ALL_DAYS, MAX_DAYS = 7, 400
def run(prices_path="data/prices.json", providers_path="providers.json", hist_path="data/history.json"):
    P=json.load(open(prices_path)); V={p["id"]:p for p in json.load(open(providers_path))["providers"]}
    H=json.load(open(hist_path)) if os.path.exists(hist_path) else {"started_at":P["generated_at"],"points":[]}
    H["models"]={n:rx for s,n,rx in GPUS}
    g={}
    for s,n,rx in GPUS:
        a=cheapest(P["prices"],V,rx); b=cheapest(P["prices"],V,rx,True)
        if a or b: g[n]=[round(a["usd_hr"],4) if a else None,a["provider"] if a else None,round(b["usd_hr"],4) if b else None,b["provider"] if b else None]
    if g and not any(p["t"]==P["generated_at"] for p in H["points"]):
        H["points"].append({"t":P["generated_at"],"g":g})
    now=datetime.datetime.fromisoformat(P["generated_at"]); pts=sorted(H["points"],key=lambda p:p["t"]); out={}; recent=[]
    for p in pts:
        age=(now-datetime.datetime.fromisoformat(p["t"])).total_seconds()/86400
        if age>MAX_DAYS: continue
        if age<=KEEP_ALL_DAYS: recent.append(p)
        else: out[p["t"][:10]]=p          # last point of each day wins
    H["points"]=list(out.values())+recent
    H["note"]="Snapshots of cheapest live prices per model; generated from data/prices.json, never edited by hand."
    json.dump(H,open(hist_path,"w"),separators=(",",":"))
    return len(H["points"])
if __name__=="__main__": print("history points:",run())
