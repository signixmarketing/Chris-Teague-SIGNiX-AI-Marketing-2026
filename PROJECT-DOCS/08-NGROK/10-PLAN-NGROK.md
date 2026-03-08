# Plan: ngrok for SIGNiX Push Notifications (Development)

This plan defines how to **set up ngrok** and **apply the required codebase changes** so SIGNiX’s servers can send push notifications (webhooks) to a developer’s machine during development and test. It is reusable for building the project from scratch: a different developer on a different computer with a different ngrok account can follow this plan; only **their** domain, authtoken, and whether ngrok is already installed will differ.

**Design context:** [07-SIGNiX-SUBMIT/DESIGN-SIGNiX-SUBMIT.md](../07-SIGNiX-SUBMIT/DESIGN-SIGNiX-SUBMIT.md) Section 8 defers push notifications and notes that **ngrok** (or similar) can expose a local URL so SIGNiX can POST webhooks to the Django app. This plan enables that. [GENERAL-KNOWLEDGE/KNOWLEDGE-SIGNiX.md](../GENERAL-KNOWLEDGE/KNOWLEDGE-SIGNiX.md) and [SIGNiX Push Notifications](https://www.signix.com/pndocumentation) describe the webhook format and subscription.

**Usage:** Follow the implementation order (Section 4). Run the “already set up?” check (Section 4.0) first; if ngrok is already installed and authenticated, skip to the batch you need. Apply the **codebase changes** (Section 5) in the order given—they are required for the app to work correctly when accessed through the tunnel. Replace every placeholder (e.g. `YOUR_NGROK_DOMAIN`) with **your** ngrok hostname.

---

## 1. What is ngrok?

- **ngrok** is a tunneling service that exposes a local server (e.g. Django `runserver` on port 8000) to the internet via a public HTTPS URL.
- SIGNiX push notifications are HTTP POSTs from SIGNiX’s servers to a **callback URL** you register. That URL must be reachable from the internet. On a dev machine behind a home/office network, ngrok provides that reachable URL and forwards requests to your local Django app.
- **Free tier** is sufficient for development: one dev domain (or custom name if your plan allows), one online endpoint, and enough requests for testing. See Section 2.

---

## 2. Free Tier Summary (as of 2024–2025)

Use the [ngrok pricing and limits](https://ngrok.com/docs/pricing-limits/free-plan-limits/) docs for current numbers. Typical free-tier highlights:

| Item | Free tier |
|------|-----------|
| **Domain** | One free **dev domain** with an auto-generated name (e.g. `something-random.ngrok-free.dev`). Choosing a **custom name** (e.g. `myproject.ngrok-free.app`) may **require an upgrade** in the ngrok dashboard; use your dev domain if so. |
| **Online endpoints** | 1 (one tunnel at a time on free tier is typical). |
| **Agents** | 1 (one machine running the ngrok agent). |
| **HTTP requests** | 20,000/month. |
| **Data transfer out** | 1 GB/month. |

**Browser interstitial:** Free tier may show a warning page when the tunnel URL is opened in a **browser**. That does **not** affect API or webhook traffic: SIGNiX will POST to your URL and the request will reach Django. For browser testing you can send the header `ngrok-skip-browser-warning: 1` or use a non-browser client (e.g. `curl`).

---

## 3. Prerequisites

- **Django app** runnable ([70-PLAN-MASTER.md](../70-PLAN-MASTER.md) plans 1–4 at minimum; PHASE-PLANS-DOCS 1–4 if you use document generation through the tunnel). The app does not need a push-notification endpoint yet; this plan only establishes the tunnel and the code changes so that when you add the endpoint, SIGNiX can reach it.
- **Your machine:** Linux (WSL2 or native), macOS, or Windows. Commands below are for Linux/WSL2; adjust for your OS.
- **Network:** Outbound HTTPS to ngrok’s services so the ngrok agent can connect.
- **ngrok:** May **not** be installed when you start; Batch 1 covers install. If it is already installed and authenticated, Section 4.0 tells you how to skip ahead.

---

## 4. What Varies Per Developer / Machine

| Item | Notes |
|------|--------|
| **ngrok account** | Each developer has their own; sign up at [ngrok.com](https://ngrok.com) (free). |
| **Authtoken** | From the ngrok dashboard for **your** account; run `ngrok config add-authtoken <TOKEN>` once per machine. |
| **Domain hostname** | Your ngrok dev domain (e.g. `abc123.ngrok-free.dev`) or a custom domain if your plan allows. **You must substitute this everywhere** the plan or code uses a placeholder (e.g. `YOUR_NGROK_DOMAIN`). |
| **Already installed?** | If `ngrok version` and `ngrok http 8000` already work, skip Batch 1 (and optionally Batch 2 if you already know your domain). |

---

## 5. Codebase Changes (Required)

These changes are **required** for the app to work when accessed through the ngrok tunnel. Apply them in the order below. Replace `YOUR_NGROK_DOMAIN` (or similar) with your actual ngrok hostname (e.g. `unreproachable-draftily-shanelle.ngrok-free.dev`).

### 5.1 config/settings.py

- **ALLOWED_HOSTS:** Ensure the list includes ngrok host patterns so Django accepts requests via the tunnel. Use leading-dot form so any subdomain is allowed:
  ```python
  ALLOWED_HOSTS = [
      "localhost",
      "127.0.0.1",
      ".ngrok-free.app",
      ".ngrok-free.dev",
      ".ngrok.io",
  ]
  ```
- **CSRF_TRUSTED_ORIGINS:** Add the **exact** origin(s) for **your** ngrok domain (http and https), so login and other POSTs through the tunnel pass CSRF:
  ```python
  CSRF_TRUSTED_ORIGINS = [
      "https://YOUR_NGROK_DOMAIN",
      "http://YOUR_NGROK_DOMAIN",
  ]
  ```
  Example: `"https://unreproachable-draftily-shanelle.ngrok-free.dev"` and `"http://unreproachable-draftily-shanelle.ngrok-free.dev"`.
- **SECURE_PROXY_SSL_HEADER:** When app code derives absolute URLs from the current request (for example, the SIGNiX callback URL in Plan 3), Django must trust ngrok’s forwarded HTTPS scheme or it may incorrectly emit `http://YOUR_NGROK_DOMAIN` even though the browser is on HTTPS. Add:
  ```python
  SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
  ```
  This keeps `request.build_absolute_uri("/")` aligned with the external ngrok URL.
- **PDF_IMAGE_BASE_URL:** So that document generation (Generate/Regenerate) works when triggered via the ngrok URL, image URLs in the generated HTML must be reachable by wkhtmltopdf on the server. Set:
  ```python
  PDF_IMAGE_BASE_URL = "http://127.0.0.1:8000"
  ```
  (Use a different host/port only if your app runs elsewhere when generating.)

### 5.2 apps/documents/services.py

- In **build_document_context**, when building the base URL for image variables, **prefer** `settings.PDF_IMAGE_BASE_URL` when set, so image URLs are always local and wkhtmltopdf can fetch them. Then build image URLs from that base first; fall back to `request.build_absolute_uri` or `SITE_URL` only when `PDF_IMAGE_BASE_URL` is not set. (See this plan's implementation notes or the current repo for the exact logic.)

### 5.3 Health endpoint (for Batch 5 sanity check)

- **apps/users/views.py:** Add a view that returns `JsonResponse({"status": "ok"})` with status 200 (no auth). Example name: `health`.
- **config/urls.py:** Add `path("health/", users_views.health, name="health")` (or equivalent).

### 5.4 .vscode/launch.json (Cursor / VS Code)

- Add a **launch configuration** that runs `scripts/run_ngrok.py` with `NGROK_DOMAIN` and `NGROK_PORT` in `env`. Set `NGROK_DOMAIN` to **your** ngrok hostname (e.g. `YOUR_NGROK_DOMAIN.ngrok-free.dev`).
- Add a **compound** launch configuration that starts both the Ngrok config and the Django runserver config so that “Django with ngrok” starts both and stopping the debugger stops both.

### 5.5 scripts/run_ngrok.py

- Create a script that: reads `NGROK_DOMAIN` and `NGROK_PORT` from the environment; runs `ngrok http --domain <domain> <port>`; and forwards SIGINT/SIGTERM to the ngrok process so that when the debug session stops, ngrok exits. Exit with a clear error if `NGROK_DOMAIN` is not set.

### 5.6 scripts/verify_ngrok.sh

- Create a script that: curls `https://${NGROK_DOMAIN}/health/` (with `ngrok-skip-browser-warning: 1`); exits 0 if the HTTP status is 200, else 1. Use `NGROK_DOMAIN` from the environment, or a default (e.g. the repo’s example domain)—**if you use a different domain, set `NGROK_DOMAIN` when running the script or edit the default inside the script.**

---

## 6. Implementation Order and Batches

### 6.0 Check if ngrok is already set up (skip batches if so)

Before installing or redoing steps:

1. Run `ngrok version`. If it prints a version, ngrok is installed; otherwise run Batch 1.
2. Run `ngrok http 8000` (stop with Ctrl+C after a few seconds). If you see a **forwarding URL**, your authtoken is configured and Batch 1 is complete. If you see “ERR_NGROK_801” or “authtoken required”, run Batch 1 step 3.
3. If you already have a domain (e.g. dev domain) from the ngrok dashboard, note its full hostname and skip Batch 2.

Then proceed to the batches below (or skip to Batch 3 if you only need to run the tunnel).

---

### Batch 1: Install ngrok and authenticate

**Goal:** Install the ngrok agent and link it to **your** ngrok account.

**Steps:**

1. Create an ngrok account at [ngrok.com](https://ngrok.com) (email or Google) if you don’t have one.
2. Install ngrok:
   - **Linux (Debian/Ubuntu/WSL2):**
     ```bash
     curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | \
       sudo gpg --dearmor -o /etc/apt/keyrings/ngrok.gpg && \
     echo "deb [signed-by=/etc/apt/keyrings/ngrok.gpg] https://ngrok-agent.s3.amazonaws.com buster main" | \
       sudo tee /etc/apt/sources.list.d/ngrok.list && \
     sudo apt update && sudo apt install ngrok
     ```
   - **macOS:** `brew install ngrok`. **Windows:** Download from [ngrok downloads](https://ngrok.com/download) and add to PATH.
3. In the [ngrok dashboard](https://dashboard.ngrok.com/get-started/your-authtoken), copy **your** authtoken. Run:
   ```bash
   ngrok config add-authtoken <YOUR_AUTHTOKEN>
   ```

**Verification:** `ngrok version` succeeds; `ngrok http 8000` shows a forwarding URL (then Ctrl+C).

---

### Batch 2: Confirm your domain (or claim one)

**Goal:** Know the full hostname you will use for the tunnel (e.g. `something.ngrok-free.dev`).

- If you **already have** a domain in the ngrok dashboard (e.g. the free dev domain), note its full hostname and skip to Batch 3.
- If not: log in to the [ngrok dashboard](https://dashboard.ngrok.com) → **Universal Gateway → Domains** (or **Cloud Edge → Domains**). Use the existing dev domain or create one if the plan allows without “Requires Upgrade”. Do **not** delete your only domain.

**Verification:** You have a single hostname (e.g. `yourname.ngrok-free.dev`) to use as `YOUR_NGROK_DOMAIN` everywhere below.

---

### Batch 3: Run tunnel to Django

**Goal:** Expose the local Django server at `https://YOUR_NGROK_DOMAIN`.

1. Start Django (e.g. `python manage.py runserver` or “Django: runserver” in Cursor).
2. Start ngrok with **your** domain and port (e.g. 8000):
   ```bash
   ngrok http --domain=YOUR_NGROK_DOMAIN 8000
   ```
3. In another terminal, verify: `curl -H "ngrok-skip-browser-warning: 1" https://YOUR_NGROK_DOMAIN/health/` returns 200 (or hit `/admin/` and get a 302). Optional: open `http://127.0.0.1:4040` to inspect requests.

**Cursor (optional):** Use the compound launch “Django with ngrok” after setting `NGROK_DOMAIN` in `.vscode/launch.json` to **your** domain. Then starting the debugger runs both Django and ngrok; stopping stops both.

---

### Batch 4: Document webhook URL and optional config

**Goal:** Record the URL SIGNiX will use and any optional config.

1. Write down **your** webhook base URL: `https://YOUR_NGROK_DOMAIN`. The full callback will be that base plus the path you add for push (for this project’s working integration: `/signix/push` in SubmitDocument; Django’s listener route remains `/signix/push/`).
2. Optional: add a named tunnel in `~/.config/ngrok/ngrok.yml` (see [ngrok config](https://ngrok.com/docs/agent/config)) so you can run `ngrok start django` instead of typing the full command.
3. When you implement the push endpoint, register the full callback URL in SIGNiX’s push notification configuration (per SIGNiX docs).

**Verification:** You have a single place that states your domain and how you start the tunnel.

---

### Batch 5: Scripted sanity check (optional)

**Goal:** A script or one-liner that verifies “tunnel is up and Django is reachable.”

- **Health URL:** `GET /health/` returns 200 and `{"status": "ok"}` (implemented in Section 5.3).
- **One-liner:**  
  `curl -sS -o /dev/null -w "%{http_code}" -H "ngrok-skip-browser-warning: 1" https://YOUR_NGROK_DOMAIN/health/`  
  Expected: `200`.
- **Script:** `scripts/verify_ngrok.sh` (Section 5.6). Run `./scripts/verify_ngrok.sh` or `NGROK_DOMAIN=YOUR_NGROK_DOMAIN ./scripts/verify_ngrok.sh`. Exit 0 if status 200, else 1.

**Verification:** With Django and ngrok running, the script exits 0. With ngrok stopped, it exits 1.

---

## 7. Summary Table

| Step | Goal | When to skip |
|------|------|--------------|
| 6.0 | Check if already set up | — (always run first) |
| Batch 1 | Install ngrok, add authtoken | Skip if `ngrok version` and `ngrok http 8000` already work |
| Batch 2 | Confirm domain | Skip if you already have a domain hostname |
| Batch 3 | Run tunnel | Run when you need to expose Django |
| Batch 4 | Document webhook URL | Run once per project/machine |
| Batch 5 | Optional sanity check | Optional |

| Batch | Verification |
|-------|---------------|
| 1 | `ngrok version`; `ngrok http 8000` shows forwarding URL |
| 2 | You know your full domain hostname |
| 3 | `curl` to tunnel URL (e.g. `/health/`) returns 200 |
| 4 | Domain and start command documented |
| 5 | `./scripts/verify_ngrok.sh` exits 0 when tunnel is up, 1 when down |

---

## 8. Relation to SIGNiX Push Implementation

- This plan provides the **tunnel** and **codebase changes** so the app accepts requests from the ngrok URL. It does **not** implement the Django endpoint that receives SIGNiX webhooks or register the URL with SIGNiX.
- When implementing push: add a view/URL for the callback (e.g. `/signix/push/`), validate requests per SIGNiX docs, update `SignatureTransaction` and related state, and register the full callback URL used by SubmitDocument. In this project’s verified integration, that emitted URL is `https://YOUR_NGROK_DOMAIN/signix/push` (no trailing slash), while Django still serves the listener at `/signix/push/`.
- Development workflow: start Django, start ngrok with your domain, then test; use the ngrok Web Interface (`http://127.0.0.1:4040`) to inspect webhook payloads.

---

## 9. References

- [ngrok Quickstart (Linux)](https://ngrok.com/docs/getting-started/?os=linux)
- [ngrok Free plan limits](https://ngrok.com/docs/pricing-limits/free-plan-limits/)
- [ngrok HTTP agent / tunnels](https://ngrok.com/docs/http)
- [ngrok config file](https://ngrok.com/docs/agent/config)
- [07-SIGNiX-SUBMIT/DESIGN-SIGNiX-SUBMIT.md](../07-SIGNiX-SUBMIT/DESIGN-SIGNiX-SUBMIT.md) — Section 8 (Push notifications deferred; ngrok for dev)
- [GENERAL-KNOWLEDGE/KNOWLEDGE-SIGNiX.md](../GENERAL-KNOWLEDGE/KNOWLEDGE-SIGNiX.md) — Push notifications overview
- [SIGNiX Push Notifications](https://www.signix.com/pndocumentation)

---

*To use this plan: apply the codebase changes (Section 5) and substitute your ngrok domain everywhere. Run Section 6.0; then run Batches 1–4 in order (skipping any step that is already done). Add Batch 5 if you want the scripted verification.*
