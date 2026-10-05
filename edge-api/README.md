# edge-api — Cloudflare Workers (Lab 17)

A small TypeScript Worker built for **Lab 17 — Cloudflare Workers Edge Deployment**
of the DevOps Core course.

For the graded deliverable (deployment URL, evidence, K8s vs Workers comparison)
see [WORKERS.md](WORKERS.md).

## Routes

| Method | Path       | Description                                              |
| ------ | ---------- | -------------------------------------------------------- |
| GET    | `/`        | App metadata using plaintext vars from `wrangler.jsonc`. |
| GET    | `/health`  | Liveness probe — always `{ "status": "ok" }`.            |
| GET    | `/edge`    | Edge metadata from `request.cf` (colo, country, ...).    |
| GET    | `/info`    | Vars + safe presence-check of secrets.                   |
| GET    | `/counter` | KV-backed visit counter (uses `SETTINGS` namespace).     |

Anything else → `404`.

## Prerequisites

- Node.js 18+ and npm
- A Cloudflare account
- Wrangler CLI authenticated (`npx wrangler login`)

## Local development

```bash
npm install
# Optional: provide local secrets so /info and /counter work in dev
Copy-Item .dev.vars.example .dev.vars   # PowerShell
# or: cp .dev.vars.example .dev.vars     # bash

npx wrangler dev
```

Then open:

- <http://localhost:8787/>
- <http://localhost:8787/health>
- <http://localhost:8787/edge>
- <http://localhost:8787/info>
- <http://localhost:8787/counter>

```powershell
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> curl.exe localhost:8787
{
  "app": "edge-api",
  "course": "devops-core",
  "version": "1.0.0",
  "message": "Hello from Cloudflare Workers (edge-api).",
  "routes": [
    "/",
    "/health",
    "/edge",
    "/info",
    "/counter"
  ],
  "startedAt": "2026-05-13T16:44:14.464Z",
  "now": "2026-05-13T16:46:11.604Z"
}
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> curl.exe localhost:8787/health
{
  "status": "ok"
}
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> curl.exe localhost:8787/edge  
{
  "colo": "ARN",
  "country": "FI",
  "city": "Helsinki",
  "region": "Uusimaa",
  "asn": 56594,
  "asOrganization": "CGI GLOBAL LIMITED",
  "httpProtocol": "HTTP/1.1",
  "tlsVersion": "TLSv1.3",
  "timezone": "Europe/Helsinki",
  "clientAcceptEncoding": "br, gzip",
  "observedAt": "2026-05-13T16:46:20.629Z"
}
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> curl.exe localhost:8787/info
{
  "app": "edge-api",
  "course": "devops-core",
  "version": "1.0.0",
  "secrets": {
    "API_TOKEN": "present (26 chars)",
    "ADMIN_EMAIL": "present (17 chars)"
  },
  "note": "Plaintext vars (APP_NAME, COURSE_NAME) live in wrangler.jsonc and are safe to commit. Secrets are injected via `wrangler secret put` and are never echoed."
}
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course> curl.exe localhost:8787/counter
{
  "key": "visits",
  "visits": 2,
  "previous": 1,
  "persistedIn": "Workers KV (binding SETTINGS)"
}
```

## First-time Cloudflare setup

```powershell
npx wrangler login
npx wrangler whoami

# Create the KV namespace and paste the returned id into wrangler.jsonc
npx wrangler kv namespace create SETTINGS

# Add the production secrets
npx wrangler secret put API_TOKEN
npx wrangler secret put ADMIN_EMAIL
```

```powershell
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course\edge-api> npx wrangler login

 ⛅️ wrangler 4.90.1
───────────────────
Attempting to login via OAuth...
Opening a link in your default browser: https://dash.cloudflare.com/oauth2/auth?response_type=code&client_id=...
Successfully logged in.
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course\edge-api> npx wrangler whoami

 ⛅️ wrangler 4.90.1
───────────────────
Getting User settings...
👋 You are logged in with an OAuth Token, associated with the email claymix007@gmail.com.
┌────────────────────────────────┬──────────────────────────────────┐
│ Account Name                   │ Account ID                       │
├────────────────────────────────┼──────────────────────────────────┤
│ Claymix007@gmail.com's Account │ ...                              │
└────────────────────────────────┴──────────────────────────────────┘
🔓 Token Permissions:
Scope (Access)
- account (read)
- user (read)
- workers (write)
- workers_kv (write)
- workers_routes (write)
- workers_scripts (write)
- workers_tail (read)
- d1 (write)
- pages (write)
- zone (read)
- ssl_certs (write)
- ai (write)
- ai-search (write)
- ai-search (run)
- queues (write)
- pipelines (write)
- secrets_store (write)
- artifacts (write)
- flagship (write)
- containers (write)
- cloudchamber (write)
- connectivity (admin)
- email_routing (write)
- email_sending (write)
- browser (write)
- offline_access
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course\edge-api> npx wrangler kv namespace create SETTINGS

 ⛅️ wrangler 4.90.1
───────────────────
Resource location: remote 

🌀 Creating namespace with title "SETTINGS"

X [ERROR] A KV namespace with the title "SETTINGS" already exists.


  You can list existing namespaces with their IDs by running:
    wrangler kv namespace list

  Or choose a different namespace name.


🪵  Logs were written to "C:\Users\claym\AppData\Roaming\xdg.config\.wrangler\logs\wrangler-2026-05-13_17-00-16_262.log"
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course\edge-api> npx wrangler kv namespace list
[
  {
    "id": "0938d409f5e94b169cacc09d704cda4d",
    "title": "SETTINGS",
    "supports_url_encoding": true
  }
]
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course\edge-api> npx wrangler secret put API_TOKEN

 ⛅️ wrangler 4.90.1
───────────────────
√ Enter a secret value: ... *****
🌀 Creating the secret for the Worker "edge-api"
√ There doesn't seem to be a Worker called "edge-api". Do you want to create a new Worker with that name and add secrets to it? ... yes
🌀 Creating new Worker "edge-api"...
✨ Success! Uploaded secret API_TOKEN
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course\edge-api> npx wrangler secret put ADMIN_EMAIL

 ⛅️ wrangler 4.90.1
───────────────────
√ Enter a secret value: ... ********************
🌀 Creating the secret for the Worker "edge-api"
✨ Success! Uploaded secret ADMIN_EMAIL
```

## Deploy

```bash
npx wrangler deploy
```

The output prints something like:

```text
https://edge-api.<your-subdomain>.workers.dev
```

```powershell
PS C:\Users\claym\Desktop\study\Spring25\DevOps\DevOps-Core-Course\edge-api> npx wrangler deploy

 ⛅️ wrangler 4.90.1
───────────────────
Total Upload: 3.22 KiB / gzip: 1.23 KiB
Your Worker has access to the following bindings:
Binding                                                 Resource
env.SETTINGS (0938d409f5e94b169cacc09d704cda4d)         KV Namespace
env.APP_NAME ("edge-api")                               Environment Variable
env.COURSE_NAME ("devops-core")                         Environment Variable

Uploaded edge-api (10.44 sec)
▲ [WARNING] Because your 'workers.dev' route is enabled and your 'preview_urls' setting is not in your Wrangler file, Preview URLs will be enabled for this deployment by default.

  To override this setting, you can disable Preview URLs by explicitly setting 'preview_urls =
  false' in your Wrangler file.


Deployed edge-api triggers (5.66 sec)
  https://edge-api.claymix.workers.dev
Current Version ID: a135f82c-762f-4ceb-8577-d3360622dbd0
```

## Operations

```bash
npx wrangler tail                 # live logs from production
npx wrangler deployments list     # version history
npx wrangler rollback             # roll back to previous version
```
