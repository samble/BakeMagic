#!/usr/bin/env bash
# Smoke test: start the real API and a production build of the frontend on spare
# ports, check that the main pages and endpoints respond, then shut both down.
# Uses the database from DATABASE_URL / .env and only sends GET requests.
set -euo pipefail

API_PORT=${SMOKE_API_PORT:-8001}
WEB_PORT=${SMOKE_WEB_PORT:-4174}
NPM=${NPM:-npm}
cd "$(dirname "$0")/.."

# Each server runs in its own process group (setsid) so cleanup also stops the
# children npm and fastapi spawn, not just the top-level process.
pids=()
cleanup() { for pid in "${pids[@]}"; do kill -- "-$pid" 2>/dev/null || true; done; }
trap cleanup EXIT

wait_for() { # url
  for _ in $(seq 1 60); do
    curl -sf -o /dev/null "$1" && return 0
    sleep 0.5
  done
  echo "FAIL: $1 did not come up" >&2
  exit 1
}

failures=0
check() { # expected-status url [text that must appear in the body]
  local body status
  body=$(curl -s -w '\n%{http_code}' "$2")
  status=${body##*$'\n'}
  body=${body%$'\n'*}
  if [[ $status != "$1" ]] || [[ -n ${3:-} && $body != *"$3"* ]]; then
    echo "FAIL  $2 -> $status (expected $1${3:+ with \"$3\"})"
    failures=$((failures + 1))
  else
    echo "ok    $2 -> $status"
  fi
}

echo "Starting API on :$API_PORT"
setsid .venv/bin/fastapi run app/main.py --port "$API_PORT" >/tmp/bakemagic-smoke-api.log 2>&1 &
pids+=($!)

echo "Building frontend"
(cd frontend && "$NPM" run build --silent >/dev/null)
echo "Starting frontend preview on :$WEB_PORT"
(cd frontend && BAKEMAGIC_API="http://127.0.0.1:$API_PORT" exec setsid "$NPM" exec -- vite preview --port "$WEB_PORT" --strictPort) \
  >/tmp/bakemagic-smoke-web.log 2>&1 &
pids+=($!)

wait_for "http://127.0.0.1:$API_PORT/health"
wait_for "http://127.0.0.1:$WEB_PORT/"

api="http://127.0.0.1:$API_PORT"
web="http://127.0.0.1:$WEB_PORT"
check 200 "$api/health" '"status":"ok"'
check 200 "$api/docs"
for path in products customers orders standing-orders; do
  check 200 "$api/$path"
done
check 404 "$api/products/2147483647"
check 422 "$api/products/2147483648"
check 200 "$web/" '<div id="root">'
check 200 "$web/standing-orders" '<div id="root">'  # client-side route falls back to index.html
check 200 "$web/api/health" '"status":"ok"'      # frontend -> API proxy

if ((failures)); then
  echo "$failures smoke check(s) failed. Logs: /tmp/bakemagic-smoke-api.log, /tmp/bakemagic-smoke-web.log"
  exit 1
fi
echo "All smoke checks passed."
