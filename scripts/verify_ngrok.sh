#!/usr/bin/env bash
# Verify ngrok tunnel is up and Django is reachable.
# Usage: NGROK_DOMAIN=your-domain.ngrok-free.dev ./scripts/verify_ngrok.sh
#   or set NGROK_DOMAIN in .env / export; default below matches repo launch.json.
# Exit 0 if /health/ returns 200; exit 1 otherwise.

set -e

DOMAIN="${NGROK_DOMAIN:-unreproachable-draftily-shanelle.ngrok-free.dev}"
URL="https://${DOMAIN}/health/"
CODE=$(curl -sS -o /dev/null -w "%{http_code}" -H "ngrok-skip-browser-warning: 1" "$URL" 2>/dev/null || echo "000")

if [ "$CODE" = "200" ]; then
  echo "OK $URL -> $CODE"
  exit 0
fi
echo "FAIL $URL -> $CODE"
exit 1
