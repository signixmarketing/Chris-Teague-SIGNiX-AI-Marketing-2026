#!/usr/bin/env bash
# Start n8n in Docker, import / activate the demo workflow, patch demo-form.html with the webhook URL.
# Requires: Docker (Desktop or engine), curl, python3.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if ! command -v docker &>/dev/null; then
  echo "ERROR: Docker is not installed or not on PATH."
  echo "Install Docker Desktop (https://www.docker.com/products/docker-desktop/), then run this script again."
  exit 1
fi

if ! docker info &>/dev/null; then
  echo "ERROR: Docker daemon is not running. Start Docker Desktop, then run this script again."
  exit 1
fi

if [[ ! -f .env ]]; then
  KEY="$(openssl rand -hex 24)"
  echo "N8N_API_KEY=${KEY}" > .env
  echo "Created .env with a random N8N_API_KEY."
fi
# shellcheck disable=SC1091
source .env
if [[ -z "${N8N_API_KEY:-}" ]]; then
  echo "ERROR: N8N_API_KEY is empty in .env"
  exit 1
fi

echo "Starting n8n (docker compose)..."
docker compose up -d

echo "Waiting for http://localhost:5678/healthz ..."
for _ in $(seq 1 40); do
  if curl -sf "http://localhost:5678/healthz" >/dev/null 2>&1; then
    break
  fi
  sleep 2
done
if ! curl -sf "http://localhost:5678/healthz" >/dev/null 2>&1; then
  echo "ERROR: n8n did not become healthy in time. Try: docker compose logs -f"
  exit 1
fi

python3 << 'PY'
import json, pathlib
src = pathlib.Path("signix-notary-lead-demo.json")
out = pathlib.Path(".import-workflow.json")
data = json.loads(src.read_text(encoding="utf-8"))
for k in ("id", "versionId", "meta", "pinData"):
    data.pop(k, None)
out.write_text(json.dumps(data), encoding="utf-8")
PY

BASE="http://localhost:5678/api/v1"
HDR=(-H "X-N8N-API-KEY: ${N8N_API_KEY}" -H "Content-Type: application/json")

EXISTING="$(curl -sS "${BASE}/workflows" "${HDR[@]}" | python3 -c "
import sys, json
r=json.load(sys.stdin)
for w in r.get('data', []):
    if w.get('name') == 'SIGNiX Notary Lead Routing Demo':
        print(w['id'])
        break
" || true)"

if [[ -n "${EXISTING}" ]]; then
  echo "Removing previous workflow id=${EXISTING}..."
  curl -sS -X DELETE "${BASE}/workflows/${EXISTING}" "${HDR[@]}" || true
fi

echo "Importing workflow..."
CREATE_RES="$(curl -sS -X POST "${BASE}/workflows" "${HDR[@]}" -d "@.import-workflow.json")"
WF_ID="$(echo "$CREATE_RES" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
except json.JSONDecodeError:
    sys.exit(1)
wid = d.get('id') or (d.get('data') or {}).get('id') or ''
print(wid)
" 2>/dev/null || true)"
if [[ -z "$WF_ID" ]]; then
  echo "ERROR: Create workflow failed. Response:"
  echo "$CREATE_RES"
  exit 1
fi

echo "Activating workflow ${WF_ID}..."
curl -sS -X PATCH "${BASE}/workflows/${WF_ID}" "${HDR[@]}" -d '{"active": true}' >/dev/null

WEBHOOK_URL="http://localhost:5678/webhook/signix-notary-lead-demo"
echo ""
echo "Production webhook URL:"
echo "  ${WEBHOOK_URL}"
echo ""

# Patch demo-form.html default webhook (macOS sed)
if [[ -f demo-form.html ]]; then
  if grep -q 'YOUR_N8N_WEBHOOK_URL' demo-form.html; then
    sed -i '' "s|YOUR_N8N_WEBHOOK_URL|${WEBHOOK_URL}|g" demo-form.html
    echo "Updated demo-form.html with the webhook URL."
  else
    echo "demo-form.html: webhook placeholder not found (already set?). Open file and confirm DEFAULT_WEBHOOK."
  fi
fi

rm -f .import-workflow.json

echo ""
echo "NEXT (manual — needs your email credentials):"
echo "  1. Open http://localhost:5678 in your browser."
echo "  2. Open workflow 'SIGNiX Notary Lead Routing Demo'."
echo "  3. On each Send email node: add SMTP credentials and set From (replace REPLACE_WITH_YOUR_ALLOWED_SENDER@yourdomain.com)."
echo "  4. Run test: curl -X POST '${WEBHOOK_URL}' -H 'Content-Type: application/json' -d @sample-payload-low.json"
echo ""
