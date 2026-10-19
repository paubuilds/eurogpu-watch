"""Shared GPU model families (used by build_pages.py, update_history.py and, via data/history.json, the browser)."""
import re
GPUS = [  # slug, display name, regex matching normalized GPU names in data
 ("h100","H100",r"\bH100\b"),("h200","H200",r"\bH200\b"),("b200","B200",r"\bB200\b"),("a100","A100",r"\bA100\b"),
 ("l40s","L40S",r"\bL40S\b"),("l4","L4",r"^(NVIDIA )?L4$"),("rtx-4090","RTX 4090",r"4090"),("rtx-5090","RTX 5090",r"5090"),
 ("rtx-a6000","RTX A6000",r"A6000"),("rtx-pro-6000","RTX PRO 6000",r"PRO 6000"),("a10","A10",r"^A10$|\bA10 ")]
def cheapest(prices, providers, rx, eu_company=False):
    """Cheapest row for a model family; eu_company=True restricts to EU-incorporated providers."""
    rs=[r for r in prices if isinstance(r.get("usd_hr"),(int,float)) and re.search(rx,r["gpu"],re.I)
        and (not eu_company or providers.get(r["provider"],{}).get("eu_incorporated") is True)]
    return min(rs,key=lambda r:r["usd_hr"]) if rs else None
