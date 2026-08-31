# PlanIQ (estimation-tool) — deploy notes

Codebase: **estimation-tool 4** (swapped in on the platform).

## Changes applied on top of the stock repo
1. **`docker-compose.yml`** — rewritten to app-only (no Ollama), host port **9000**,
   `--root-path /planiq`, all config via `env_file: .env.dev`. (The stock compose ships
   Ollama + port 8000 + no Azure creds, which clashes with SmartBrain and misses the LLM keys.)
2. **`app/services/slm_engine.py`** — `INFERENCE_TIMEOUT_SECONDS` raised **120 → 300**.
   Reason: "analysis failed" was caused by the Azure OpenAI call timing out at 120s
   (`Azure OpenAI timeout (attempt N). Retrying...` in the logs) on the shared POC endpoint
   for large estimation prompts. 300s gives the LLM room to finish.
3. `.env.dev` — `DEV_MODE=true` (kept, so analysis can be tested via login). Azure creds present.
   Flip to `false` only once SSO is in front (it enforces Azure AD + Users.xlsx allowlist).

## nginx — NO change needed
The frontend still uses `API_BASE=''` (absolute `/api/...`) and `<script src="/mpcp-tracker.js">`,
already covered by the existing routes in `deploy/nginx/tvsm-platform.conf`
(`/api/`, `/health`, `/mpcp-tracker.js`, `/planiq/`).

## Deploy on the VM
```bash
# stop + remove the old container (needs the old compose file present)
cd ~/tvsm-ai-platform/estimation-tool && docker compose down

# replace the folder with the new zip
rm -rf ~/tvsm-ai-platform/estimation-tool
cd ~/tvsm-ai-platform && unzip -o ~/estimation-tool.zip

# build + run on port 9000
cd ~/tvsm-ai-platform/estimation-tool && docker compose up --build -d
docker ps
curl -s http://localhost:9000/health          # -> {"status":"healthy","devMode":"true"}
```
Then test analysis at `https://smartbrain.tvsmotor.net/planiq/`.

## If analysis STILL times out after this
It's not the app — it's the Azure OpenAI path. Confirm with the in-container latency test:
```bash
docker exec estimation-tool-app python -c "
import os,time,httpx
u=os.environ['AZURE_OPENAI_ENDPOINT'].rstrip('/')+'/openai/deployments/'+os.environ.get('AZURE_OPENAI_DEPLOYMENT_GPT4O','gpt-4o-mini')+'/chat/completions?api-version=2024-02-15-preview'
t=time.time(); r=httpx.post(u,headers={'api-key':os.environ['AZURE_OPENAI_KEY']},json={'messages':[{'role':'user','content':'hi'}],'max_tokens':10},timeout=180,verify=False)
print('status',r.status_code,'took',round(time.time()-t,1),'s')"
```
- fast (200, <5s) → POC endpoint throttles large prompts → need TPM bump / dedicated Azure OpenAI resource.
- slow / hangs → egress to `*.openai.azure.com` is flaky → network-team (Netskope) allowlist.
