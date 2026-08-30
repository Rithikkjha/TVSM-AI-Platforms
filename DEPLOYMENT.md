# TVSM AI Platform — Deployment & Operations Guide

This document is the single reference for deploying and running the two apps on the
UAT VM, plus every command needed to debug them.

- **VM:** `smartbrainuser@tazsmrtbrnvmuat01` — `10.44.59.200` (Ubuntu 24.04, Python 3.12)
- **Apps:**
  - **SmartBrain** (Engineering Memory Graph) — Python venv, port **8000**
  - **PlanIQ** (estimation-tool) — Docker container, port **9000**
- **Reverse proxy:** nginx, TLS termination, single hostname + path routing

---

## 1. Public URL map

Everything is served under one DNS name (`smartbrain.tvsmotor.net` → `10.44.59.200`)
with path-based routing in nginx:

| URL | Goes to | What it is |
|-----|---------|------------|
| `https://smartbrain.tvsmotor.net/brain/chatbot/` | 127.0.0.1:8000 | SmartBrain chat UI |
| `https://smartbrain.tvsmotor.net/brain/mcp` | 127.0.0.1:8000 | MCP server (stateless HTTP) |
| `https://smartbrain.tvsmotor.net/brain/v1/...` | 127.0.0.1:8000 | SmartBrain REST API |
| `https://smartbrain.tvsmotor.net/planiq/` | 127.0.0.1:9000 | PlanIQ / estimation tool |

nginx strips the `/brain` and `/planiq` prefix before forwarding; each app runs with a
matching `--root-path` so generated links stay correct.

---

## 2. Layout on the VM

```
~/tvsm-ai-platform/
├── smartbrain-v2/          # SmartBrain code
│   ├── .venv/              # Python virtualenv (rebuilt on VM, not in git)
│   ├── .env                # real secrets (NOT in git)
│   ├── data/               # Neo4j + Qdrant + bm25 index (~900M, NOT in git)
│   ├── docker-compose.yml  # neo4j + qdrant (+ api, unused here)
│   └── reqs.txt            # dependency list we install
├── estimation-tool/        # PlanIQ code
│   ├── .env.dev            # real secrets, DEV_MODE=false (NOT in git)
│   └── docker-compose.yml  # app-only, port 9000, --root-path /planiq
└── deploy/nginx/tvsm-platform.conf   # the nginx site config
```

> **Not in git / not in the zip:** `.env*` files and the `data/` folder.
> If you ever rebuild the folder from the zip, you must restore these manually
> (see §9 Disaster recovery).
---

## 3. First-time setup (what we ran, in order)

### 3.1 Infra — Neo4j + Qdrant (Docker)

```bash
cd ~/tvsm-ai-platform/smartbrain-v2
docker compose up -d neo4j qdrant        # start the two data stores
docker ps                                # confirm emg2-neo4j + emg2-qdrant are (healthy)
```

- Neo4j: bolt on host port **7688**, browser on **7475**
- Qdrant: REST on host port **6335**
- Data persists in `./data/` (bind mounts, NOT docker volumes — deleting the folder
  deletes the data; `docker compose down` is safe, `down -v` is NOT relevant here since
  there are no named volumes).

### 3.2 SmartBrain — Python venv + dependencies

```bash
cd ~/tvsm-ai-platform/smartbrain-v2
sudo apt install -y python3.12-venv      # only needed once, if venv module missing
python3 -m venv .venv                    # create the virtualenv
source .venv/bin/activate                # activate it (prompt shows (.venv))
pip install -U pip
pip install -r reqs.txt                  # install all deps
```

> **Important:** `pip install -e .` and `docker compose up api` both FAIL — `pyproject.toml`
> points hatch at an old `src/` layout that no longer exists. We install deps directly instead.

> **MCP version pin:** `reqs.txt` uses `mcp>=1.9,<2`. mcp 2.x moved `FastMCP` out of
> `mcp.server.fastmcp` and breaks our import. 1.9 still has stateless Streamable HTTP
> (`stateless_http=True`), which is what we use, so pin to 1.x.

### 3.3 SmartBrain — run the API (via systemd — recommended)

Install the service once (details + unit file contents in §7):

```bash
sudo cp ~/tvsm-ai-platform/deploy/systemd/smartbrain.service /etc/systemd/system/smartbrain.service
sudo systemctl daemon-reload
sudo systemctl enable --now smartbrain      # start now + auto-start on every boot
sudo systemctl status smartbrain            # confirm active (running)
```

- Runs `uvicorn api.app:app --host 0.0.0.0 --port 8000 --root-path /brain`.
- `--root-path /brain` makes it aware it's mounted under `/brain` behind nginx.
- `Restart=always` restarts it within 5s if it crashes; survives reboots.
- Logs: `journalctl -u smartbrain -f`.

> `pip install -e .` and `docker compose up api` still fail (old `src/` layout) — the
> service runs uvicorn from the venv directly, which is why §3.2 installs deps into `.venv`.

### 3.4 PlanIQ — run the estimation tool (Docker)

```bash
cd ~/tvsm-ai-platform/estimation-tool
docker compose up --build -d             # build + run in background, port 9000
docker ps                                # confirm the container is up
```

- Runs from `Dockerfile.app`, `env_file: .env.dev`, `--root-path /planiq`.
- `DEV_MODE=false` (manager's request) — real endpoints require Azure AD auth;
  only `/health` is open.
- Has `restart: unless-stopped`, so it auto-starts on reboot.

### 3.5 Certificate — pull wildcard cert from Azure Key Vault

```bash
az login --identity --allow-no-subscriptions        # log in as the VM's managed identity
mkdir -p ~/certwork && cd ~/certwork

# download the PFX (stored as a base64 secret) and decode it
az keyvault secret show --vault-name tvsmazcmnkyvprod01-ci --name tvsmotor-net-wc --query value -o tsv > cert.b64
base64 -d cert.b64 > cert.pfx

# split into full-chain cert + key (Ubuntu 24 OpenSSL 3 needs -legacy for Azure PFX)
openssl pkcs12 -in cert.pfx -nokeys -out fullchain.crt -passin pass: -legacy
openssl pkcs12 -in cert.pfx -nocerts -nodes -out tvsmotor-net-wc.key -passin pass: -legacy

# verify: subject must be *.tvsmotor.net, count should be >= 2
openssl x509 -in fullchain.crt -noout -subject -issuer -dates
grep -c "BEGIN CERTIFICATE" fullchain.crt
```

> **Prereq:** the VM's managed identity must have **Secret: Get + List** on the vault.
> If `az keyvault secret show` returns `ForbiddenByPolicy`, ask IT to grant it
> (object id from: `curl -s -H Metadata:true "http://169.254.169.254/metadata/identity/oauth2/token?api-version=2018-02-01&resource=https://vault.azure.net" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4 | cut -d. -f2 | base64 -d 2>/dev/null | grep -o '"oid":"[^"]*"'`).

### 3.6 nginx — install + configure

```bash
sudo mkdir -p /etc/nginx/certs
sudo cp ~/certwork/fullchain.crt         /etc/nginx/certs/tvsmotor-net-wc.crt
sudo cp ~/certwork/tvsmotor-net-wc.key   /etc/nginx/certs/tvsmotor-net-wc.key
sudo chmod 600 /etc/nginx/certs/tvsmotor-net-wc.key

sudo apt install -y nginx
sudo cp ~/tvsm-ai-platform/deploy/nginx/tvsm-platform.conf /etc/nginx/conf.d/tvsm-platform.conf
sudo rm -f /etc/nginx/sites-enabled/default   # remove default site so it doesn't grab :80
sudo nginx -t                                 # test config BEFORE reloading
sudo systemctl reload nginx                   # apply
```
---

## 4. Daily operations — start / stop / restart

### SmartBrain API (port 8000) — managed by systemd

The API runs as the `smartbrain` systemd service (set up in §7). Use systemctl —
do NOT use `nohup` anymore (it doesn't survive reboot).

```bash
sudo systemctl start smartbrain      # start
sudo systemctl stop smartbrain       # stop
sudo systemctl restart smartbrain    # restart (use this after a code change)
sudo systemctl status smartbrain     # is it running?
journalctl -u smartbrain -f          # live logs
journalctl -u smartbrain -n 50       # last 50 log lines
```

> Fallback only (service not installed yet): `cd ~/tvsm-ai-platform/smartbrain-v2 &&
> source .venv/bin/activate && nohup uvicorn api.app:app --host 0.0.0.0 --port 8000
> --root-path /brain > ~/smartbrain.log 2>&1 &` — but prefer the systemd service.

### Infra (Neo4j + Qdrant)

```bash
cd ~/tvsm-ai-platform/smartbrain-v2
docker compose up -d neo4j qdrant     # start
docker compose stop neo4j qdrant      # stop (keeps data)
docker compose restart neo4j qdrant   # restart
```

### PlanIQ (estimation, port 9000)

```bash
cd ~/tvsm-ai-platform/estimation-tool
docker compose up -d          # start
docker compose stop           # stop
docker compose restart        # restart
docker compose up --build -d  # rebuild after code change
```

### nginx

```bash
sudo systemctl reload nginx    # apply config change (no downtime)
sudo systemctl restart nginx   # full restart
sudo systemctl status nginx    # is it running?
```

---

## 5. Debugging — commands by symptom

### "Is everything up?" — quick health sweep

```bash
# processes / ports
ss -ltnp | grep -E "8000|9000|7688|6335"   # who is listening on which port
docker ps                                   # neo4j, qdrant, planiq containers

# app health directly (bypass nginx)
curl -s http://localhost:8000/v1/health           # SmartBrain -> JSON w/ neo4j/qdrant status
curl -s http://localhost:9000/health              # PlanIQ

# app health through nginx (tests TLS + routing). -k skips cert-name check on localhost
curl -sk -H "Host: smartbrain.tvsmotor.net" https://localhost/brain/v1/health
curl -sk -H "Host: smartbrain.tvsmotor.net" https://localhost/planiq/health
```

### SmartBrain won't respond / nginx returns 502 on /brain

A 502 means nginx is fine but the app on :8000 is down or crashing.

```bash
curl -s http://localhost:8000/v1/health   # empty = API down
tail -50 ~/smartbrain.log                  # see the traceback / startup errors
ss -ltnp | grep 8000                       # nothing = not listening
# then restart it (see §4) and re-check the log
```

### PlanIQ won't respond / 502 on /planiq

```bash
docker ps                     # is the estimation container listed?
docker ps -a                  # was it created but exited?
docker logs <container> --tail 50   # get the name/id from docker ps
docker compose -f ~/tvsm-ai-platform/estimation-tool/docker-compose.yml up -d
```

### Neo4j / Qdrant issues (health shows "disconnected")

```bash
docker ps                                  # are emg2-neo4j / emg2-qdrant healthy?
docker logs emg2-neo4j --tail 50
docker logs emg2-qdrant --tail 50
# check the app is pointed at the right host ports:
grep -E "NEO4J_URI|QDRANT_URL" ~/tvsm-ai-platform/smartbrain-v2/.env
#   expected: NEO4J_URI=bolt://localhost:7688   QDRANT_URL=http://localhost:6335
```

### nginx config / TLS issues

```bash
sudo nginx -t                        # validate config, shows line of any syntax error
sudo tail -50 /var/log/nginx/error.log   # runtime errors (upstream failures, cert issues)
sudo systemctl status nginx          # crashed? masked? show state
# inspect the cert nginx is serving:
openssl x509 -in /etc/nginx/certs/tvsmotor-net-wc.crt -noout -subject -dates
```

### "Can't reach it from my laptop"

Order of things to check:
1. **From the VM** — do the local `curl` health checks above pass? If not, fix the app first.
2. **DNS** — does `smartbrain.tvsmotor.net` resolve to `10.44.59.200`?
   `nslookup smartbrain.tvsmotor.net` (from laptop). If not, add a temporary hosts entry
   (see §8) or wait for IT to create the DNS record.
3. **Network / firewall** — is port **443** open from your laptop to `10.44.59.200`?
   `nc -vz 10.44.59.200 443` (from laptop). If it times out, it's a Netskope/NSG rule.

### Certificate / Key Vault

```bash
az account show                         # am I logged in as the managed identity?
az keyvault secret show --vault-name tvsmazcmnkyvprod01-ci --name tvsmotor-net-wc --query contentType -o tsv
#   application/x-pkcs12 = PFX (use the -legacy openssl split in §3.5)
```
---

## 6. Log locations

| What | Where |
|------|-------|
| SmartBrain API | `~/smartbrain.log` (from the `nohup ... >` redirect) |
| PlanIQ | `docker logs <estimation-container>` |
| Neo4j | `docker logs emg2-neo4j` |
| Qdrant | `docker logs emg2-qdrant` |
| nginx access | `/var/log/nginx/access.log` |
| nginx errors | `/var/log/nginx/error.log` |

Follow a log live: add `-f`, e.g. `tail -f ~/smartbrain.log` or `docker logs -f emg2-neo4j`.

---

## 7. (Recommended) Make SmartBrain survive reboots — systemd

`nohup` dies on reboot. Create a service so the API auto-starts:

```bash
sudo tee /etc/systemd/system/smartbrain.service > /dev/null <<'EOF'
[Unit]
Description=SmartBrain API
After=network.target docker.service

[Service]
User=smartbrainuser
WorkingDirectory=/home/smartbrainuser/tvsm-ai-platform/smartbrain-v2
ExecStart=/home/smartbrainuser/tvsm-ai-platform/smartbrain-v2/.venv/bin/uvicorn api.app:app --host 0.0.0.0 --port 8000 --root-path /brain
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now smartbrain      # start now + on every boot
sudo systemctl status smartbrain            # verify
journalctl -u smartbrain -n 50              # its logs (replaces ~/smartbrain.log)
```

After this, use `sudo systemctl restart smartbrain` instead of the nohup command, and
stop using `nohup`/`pkill` for it. nginx, Neo4j, Qdrant, and PlanIQ already auto-start.

---

## 8. Testing from your laptop before DNS exists

Add a temporary hosts entry so the hostname resolves to the VM (Mac/Linux):

```bash
sudo sh -c 'echo "10.44.59.200 smartbrain.tvsmotor.net" >> /etc/hosts'
```

Then open `https://smartbrain.tvsmotor.net/brain/chatbot/` in the browser.
Remove the line later once real DNS is in place. (Requires port 443 reachable — see §5.)

---

## 9. Disaster recovery — rebuilding from the zip

The zip (`tvsm-ai-platform.zip`) contains code + `.env` files but **NOT** `data/`.
If you rebuild the folder from the zip:

1. **Restore the ingested data** (avoids a multi-hour re-ingest). From the backup archive
   `smartbrain-data.tar.gz`:
   ```bash
   cd ~/tvsm-ai-platform/smartbrain-v2
   tar -xzf ~/smartbrain-data.tar.gz        # recreates ./data (neo4j, qdrant, bm25_index.pkl)
   du -sh data                               # sanity check ~900M
   ```
2. **Verify the `.env` files are present** (they ARE in the zip):
   ```bash
   ls -la ~/tvsm-ai-platform/smartbrain-v2/.env
   grep -E "AZURE_OPENAI_KEY|DEV_MODE" ~/tvsm-ai-platform/estimation-tool/.env.dev
   ```
3. **Rebuild the venv** (the `.venv` is never in the zip) — repeat §3.2.
4. Bring everything up per §3.

> **Never** delete the old `~/smartbrain-v2` / folder before confirming `data/` and `.env`
> are safely in the new location. The data lives in bind-mounted folders, not Docker
> volumes, so it is lost with the folder.

---

## 10. Key facts / gotchas cheat-sheet

- **Ports:** SmartBrain 8000, PlanIQ 9000, Neo4j bolt 7688 / browser 7475, Qdrant 6335.
- **API key** for SmartBrain protected routes: `emg-dev-key-2024` (header `X-API-Key`).
- **No `sentence-transformers`** installed — reranker falls back to hybrid top-k (fine).
- **mcp pinned `>=1.9,<2`** — 2.x breaks the FastMCP import; 1.9 still does stateless HTTP.
- **OpenSSL PFX split needs `-legacy`** on Ubuntu 24.04.
- **DEV_MODE=false** on PlanIQ — real endpoints need Azure AD; `/health` stays open.
- **nginx proxies to 127.0.0.1**, apps bind `0.0.0.0` — a 502 = app down, not nginx.
- **SmartBrain runs under systemd** (`smartbrain.service`) — auto-starts on boot,
  restarts on crash. A 502 after a reboot means it wasn't installed as a service; see §7.
- **`docker compose down -v` — never run it**; there are no named volumes, but avoid the habit.
