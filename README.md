# EuroGPU.watch MVP
Run: `python3 fetch_prices.py && python3 -m http.server 8080` → http://localhost:8080
Deploy free: push folder to a GitHub repo → enable GitHub Pages; schedule `fetch_prices.py` with a GitHub Actions cron (e.g. hourly) that commits data/prices.json. Alternative: Cloudflare Pages (connect repo, no build command, output dir `/`).
Hetzner, Genesis Cloud: no fetcher (see status in data/prices.json).
Sources: watchworks /api/prices (free, no key, no published ToS/rate limit — cache, hit ≤1/h), Vast.ai bundles API (public, no key; respect vast.ai/terms), Runpod GraphQL gpuTypes (public, no key; needs content-type header).
