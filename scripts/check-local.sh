#!/usr/bin/env sh
set -eu

WEB_URL="${WEB_URL:-http://127.0.0.1:5173}"
API_URL="${API_URL:-http://127.0.0.1:8000}"

curl --fail --silent --show-error "$API_URL/api/v1/health/live"
printf '\n'
curl --fail --silent --show-error "$API_URL/api/v1/health/ready"
printf '\n'

for route in / /chat /schemes /growth /studio /assessments /plans /profile; do
  status="$(curl --silent --output /dev/null --write-out '%{http_code}' "$WEB_URL$route")"
  printf '%-16s %s\n' "$route" "$status"
  test "$status" = "200"
done
