---
name: run-bakemagic
description: Launch and drive the BakeMagic app locally (FastAPI API on :8000, Vite/React frontend on :5173, Postgres on :5432) to see a change working. Use when asked to run, start, smoke-test or screenshot the app.
---

# Run BakeMagic

Three pieces: Postgres, the FastAPI API, and the Vite frontend (which proxies
`/api/*` to the API). Start them in this order. All commands run from the repo
root unless noted.

## 1. Postgres

The app reads `DATABASE_URL` from `.env` or the environment, defaulting to
`postgresql+psycopg://bakemagic:bakemagic@localhost:5432/bakemagic`
(`app/config.py`). On this machine a native Postgres runs as the `postgresql`
systemd service; Docker is not installed, so ignore `docker compose` from the
README.

```bash
pg_isready -h localhost            # expect: accepting connections
uv run alembic upgrade head     # bring the schema up to date; safe to re-run
uv run alembic current          # should end with "(head)"
```

If Postgres is down, ask the user to start it (`sudo systemctl start postgresql`);
don't try to install or reconfigure it.

## 2. API (port 8000)

Run in the background (Bash `run_in_background: true`):

```bash
uv run fastapi dev app/main.py --port 8000
```

Wait for it, then smoke-test:

```bash
for i in $(seq 1 30); do curl -sf localhost:8000/health >/dev/null && break; sleep 0.5; done
curl -s localhost:8000/health      # {"status":"ok"} (includes a DB round trip)
curl -s localhost:8000/products    # 200 with a JSON list
```

Interactive docs: http://127.0.0.1:8000/docs. `fastapi dev` auto-reloads on
code changes.

## 3. Frontend (port 5173)

Node is installed in `~/.local/bin`, which is **not** on the non-login shell's
PATH, so prepend it. `node_modules` is already installed; run `npm install`
only if it's missing. Run in the background:

```bash
cd frontend && PATH=$HOME/.local/bin:$PATH npm run dev -- --port 5173 --strictPort
```

Then check the page and the proxy to the API:

```bash
for i in $(seq 1 30); do curl -sf localhost:5173 >/dev/null && break; sleep 0.5; done
curl -s -o /dev/null -w "%{http_code}\n" localhost:5173/               # 200
curl -s -o /dev/null -w "%{http_code}\n" localhost:5173/api/customers  # 200 via proxy
```

## 4. Look at it

Headless Chrome is at `/usr/bin/google-chrome`. Screenshot a page into the
scratchpad, then Read the PNG and actually look at it:

```bash
google-chrome --headless=new --disable-gpu --no-first-run --window-size=1280,900 \
  --virtual-time-budget=5000 --screenshot=<scratchpad-dir>/orders.png http://localhost:5173/
```

Use an absolute path for `--screenshot`; Chrome writes relative to its own cwd.

A dbus "GlobalShortcuts" error on stderr is harmless. Pages: `/` (orders),
`/products`, `/customers`, plus "New order". An empty database shows
"No orders yet. Take the first one."

To exercise a change, hit the affected route with `curl` (e.g. `POST /orders`,
`PATCH /products/{id}`) and read the body. Validation failures return 422 with
a `detail` message.

## Stopping

Stop the two background tasks (TaskStop, or kill the processes listening on
8000 and 5173: `ss -ltnp | grep -E ':8000|:5173'`). Leave Postgres running.
