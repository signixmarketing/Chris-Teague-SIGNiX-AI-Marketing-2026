# n8n demo: SIGNiX-style notary lead routing

This folder is a **learning demo** (not production). It shows how to:

1. Accept leads from a form webhook (mirrors common fields on the [SIGNiX contact experience](https://www.signix.com/contact)).
2. **Score / route** notary leads by self-reported monthly volume:
   - **Low (0–5 / month)** → Self-serve path: autoresponse email + CTA to [Saving and Retrieving eNotary Transactions](https://www.signix.com/saving-and-retrieving-enotary-transactions).
   - **High (30+ / month)** → Internal email to **cteague@signix.com** for immediate follow-up.
   - **Everything else** (e.g. 6–29/mo notary, other products) → Internal **review** email to the same address so nothing disappears in the demo.

## Prerequisites

- [n8n](https://n8n.io/) **self-hosted** (Docker or npm) or **n8n Cloud**.
- **SMTP** credentials in n8n (Gmail app password, Microsoft 365 SMTP, SendGrid, etc.) for the **Send email** nodes—or replace those nodes with your own (Gmail OAuth node, etc.).

## Automated setup (recommended)

On a machine with **Docker Desktop** running:

```bash
cd demos/n8n-notary-lead-routing
./run-local-demo.sh
```

This will:

1. Create `.env` with a random `N8N_API_KEY` (if missing).
2. Run **n8n** via `docker compose` on [http://localhost:5678](http://localhost:5678).
3. **Import** and **activate** `signix-notary-lead-demo.json`.
4. Set **`demo-form.html`** webhook default to `http://localhost:5678/webhook/signix-notary-lead-demo`.

You still **must** open the workflow in the browser and attach **SMTP** to the three Send email nodes (see below)—that step needs your real mail credentials.

## Import the workflow (manual)

1. Open n8n → **Workflows** → **Import from File**.
2. Select `signix-notary-lead-demo.json`.
3. On each **Send email** node (`Email self-serve`, `Email sales`, `Email internal review`):
   - Add your **SMTP** credential (or reconnect if n8n prompts after import).
   - Replace `REPLACE_WITH_YOUR_ALLOWED_SENDER@yourdomain.com` with an address your provider allows (must match SPF/DKIM expectations for your SMTP).
4. Open the **Lead Webhook** node and use **Test URL** / **Production URL** (after **Activate**).
5. Paste that webhook URL into `demo-form.html` (`YOUR_N8N_WEBHOOK_URL`) or open the form with `?webhook=https://...`.

### If import or Send Email fails

n8n versions differ slightly: if **Send email** body fields differ (e.g. `message` vs `text`), open the node in the UI and paste the copy from this README’s “Autoresponse (low volume)” section into the plain-text body, using expressions for `{{ $json.first_name }}`, etc.

## Test with curl

```bash
WEBHOOK="https://your-n8n.example/webhook/signix-notary-lead-demo"

curl -sS -X POST "$WEBHOOK" \
  -H "Content-Type: application/json" \
  -d @sample-payload-low.json

curl -sS -X POST "$WEBHOOK" \
  -H "Content-Type: application/json" \
  -d @sample-payload-high.json

curl -sS -X POST "$WEBHOOK" \
  -H "Content-Type: application/json" \
  -d @sample-payload-review.json
```

## Autoresponse (low volume) — plain text

Use this in the **Email self-serve (lead)** node if you rebuild the step manually:

```text
Hi {{ $json.first_name }},

Thanks for reaching out about SIGNiX Remote Online Notarization (eNotary).

Based on the volume you shared, many teams get up to speed fastest by using our Academy resources first—especially how to save and retrieve eNotary transactions—so you can explore the product without waiting on a live demo.

START HERE (self-paced):
https://www.signix.com/saving-and-retrieving-enotary-transactions

That Academy article walks through practical concepts that typically answer the most common “how do I get started?” questions in-product.

WHAT TO DO NEXT ON YOUR OWN
• Work through the steps above in a non-production workspace if you have one.
• Note any compliance or integration constraints you hit—we address those fastest once we know your environment.

WHEN TO ENGAGE THE SIGNiX TEAM
If you later need high-volume throughput, enterprise controls, or deep integrations, reply to this email and we’ll route you to the right specialist.

— SIGNiX (demo automation)
```

Primary CTA: `https://www.signix.com/saving-and-retrieving-enotary-transactions` ([Saving and Retrieving eNotary Transactions](https://www.signix.com/saving-and-retrieving-enotary-transactions)).

## Field mapping (must match form + workflow)

| Field | Purpose |
|--------|--------|
| `first_name`, `last_name` | Identity |
| `email`, `phone` | Contact |
| `company`, `job_title` | Context |
| `product_interest` | `enotary` / `mydox` / `api` / `other` |
| `monthly_notary_volume` | `0-5` / `6-29` / `30+` (use **N/A** if not notary—form sets this automatically) |

Routing uses **only** `product_interest === enotary` plus `monthly_notary_volume` for the low/high rules.

## Business context (demo)

- **Single-notary / low-volume** servicing can be expensive relative to revenue—directing those leads to **Academy / self-serve** reduces human demo load while still converting explorers.
- **High declared volume** warrants **immediate** seller involvement.

## Files

| File | Description |
|------|-------------|
| `signix-notary-lead-demo.json` | n8n workflow export |
| `docker-compose.yml` | Local n8n service for the demo |
| `run-local-demo.sh` | Start Docker, import + activate workflow, patch `demo-form.html` |
| `.env.example` | Template for `N8N_API_KEY` (script creates `.env`) |
| `demo-form.html` | Local test form (POST JSON to webhook) |
| `sample-payload-low.json` | Example **low** route |
| `sample-payload-high.json` | Example **high** route |
| `sample-payload-review.json` | Example **default / review** route (e.g. 6–29/mo) |
