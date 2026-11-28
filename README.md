# BakeMagic

A bakery management API: products, customers and orders. Understands scheduling for days and has customer logins for viewing invoices.

Built with **FastAPI**, **SQLModel** (SQLAlchemy 2 + Pydantic 2), **PostgreSQL** via psycopg 3, and **Alembic** for migrations.

## Make commands

Run `make` to list them all. The common ones:

| Command | What it does |
|---|---|
| `make setup` | `uv sync` the backend and dev tools into `.venv`, and install frontend dependencies |
| `make dev` | run the API (:8000) and frontend (:5173) dev servers together; Ctrl-C stops both |
| `make migrate` | apply pending migrations |
| `make db-reset` | drop **all** tables and data, then re-run migrations (asks first; `YES=1` skips the prompt) |
| `make seed-db` | migrate, then load the sample data in `seed/` (products, customers, orders, standing orders); `make db-reset YES=1 seed-db` gives a fresh, populated database |
| `make test` | backend tests, frontend lint and type check, then a smoke test against the real API and a production frontend build |
| `make docker-build` | build one image with the API and the built frontend, tagged `bakemagic:<commit>` and `bakemagic:latest` |
| `make docker-run` | build the image, run its migrations, then serve it on http://localhost:8080 against the local Postgres (host networking, Linux); `DOCKER_PORT=` and `DOCKER_DATABASE_URL=` override |

Seed data lives in `seed/`, a separate Alembic environment (`alembic -n seed ...`) with its own `alembic_seed_version` table, so `make migrate` never inserts data. The seed keeps the original row ids, so it expects those ids to be free; `alembic -n seed downgrade base` removes the seeded rows again.

`make test-smoke` starts its own servers on ports 8001 and 4174, so it doesn't clash with `make dev`. It reads from the database in `DATABASE_URL` but only sends GET requests.

## Setup

Python dependencies are managed with [uv](https://docs.astral.sh/uv/). `pyproject.toml` lists them and `uv.lock` pins exact versions; commit both.

```bash
uv sync                       # creates .venv with Python 3.12+, the app and the dev tools
cp .env.example .env          # then set DATABASE_URL
```

`uv run <command>` runs a command in the project environment, syncing it first if `pyproject.toml` or `uv.lock` changed, so there's no venv to activate. Add a dependency with `uv add <package>` (or `uv add --dev <package>` for a dev tool).

### Postgres

Either start the bundled container:

```bash
docker compose up -d
```

or create a database on an existing server:

```sql
CREATE USER bakemagic WITH PASSWORD 'bakemagic';
CREATE DATABASE bakemagic OWNER bakemagic;
```

Then create the tables:

```bash
uv run alembic upgrade head
```

## Run

```bash
uv run fastapi dev app/main.py
```

- Interactive docs: http://127.0.0.1:8000/docs
- Health check (includes a database round trip): http://127.0.0.1:8000/health

## Lint

[Ruff](https://docs.astral.sh/ruff/) is configured in `pyproject.toml` (installed with the `dev` dependency group):

```bash
uv run ruff check .         # report problems
uv run ruff check . --fix   # fix what can be fixed automatically
```

New Alembic migrations are run through `ruff check --fix` automatically when generated.

## Web frontend

A React + TypeScript app (Vite, React Router, TanStack Query) in `frontend/`. It needs Node.js 20.19+.

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173
```

Start the API first. The dev server forwards `/api/*` to it at `http://127.0.0.1:8000`, stripping the `/api` prefix, so there's no CORS setup. Set `BAKEMAGIC_API` to point it elsewhere.

| Page | What it does |
|---|---|
| Orders | filter by status, expand an order to see its lines, move it to the next status or cancel it |
| New order | pick a customer and products (retired products are hidden), live total, notes |
| Standing orders | recurring weekly orders: pick a customer, days (Sun–Sat) and items; filter by day, pause, edit, delete |
| Products | add, edit inline, retire or put back on sale, delete (refused if the product is on an order) |
| Customers | add, edit, search |

`npm run build` type-checks and writes static files to `frontend/dist/`. In production, `app/web.py` serves both from one origin: the API under `/api/*` and the built frontend everywhere else (unknown paths get `index.html`, so client-side routes survive a refresh). The Docker image runs it:

```sh
make docker-build
docker run -p 8000:8000 -e DATABASE_URL=postgresql+psycopg://user:pass@host:5432/bakemagic bakemagic
docker run --rm -e DATABASE_URL=... bakemagic alembic upgrade head   # migrations, as a separate step
```

`src/api.ts` holds hand-written TypeScript types that mirror `app/models.py`; update both together.

## Endpoints

| Method | Path | |
|---|---|---|
| `POST` `GET` | `/products` | create, list (`offset`, `limit`, `active_only`) |
| `GET` `PATCH` `DELETE` | `/products/{id}` | delete returns 409 if the product is on an order; deactivate it instead |
| `POST` `GET` | `/customers` | create, list |
| `GET` `PATCH` | `/customers/{id}` | |
| `POST` `GET` | `/orders` | create with lines, list (`customer_id`, `status`) |
| `GET` | `/orders/{id}` | includes lines and total |
| `PATCH` | `/orders/{id}/status` | completed and cancelled orders are locked |
| `POST` `GET` | `/standing-orders` | create, list (`customer_id`, `day`, `active_only`) |
| `GET` `PATCH` `DELETE` | `/standing-orders/{id}` | PATCH can change `days`, `notes`, `is_active`, and `lines` (replaces all lines); the customer is fixed |

Order lines store the product's price at the time of the order, so repricing a product never changes past orders.

Standing orders are recurring weekly orders for a customer on chosen days. They store products and quantities but no prices; a daily job (not yet built) will turn each day's active standing orders into regular orders at that day's prices.

## Migrations

Models live in `app/models.py`. After changing them:

```bash
uv run alembic revision --autogenerate -m "describe the change"
# review the generated file in migrations/versions/, then
uv run alembic upgrade head
```

`alembic upgrade head --sql` prints the SQL without touching the database. Alembic reads `DATABASE_URL` from the app settings, so there's no URL in `alembic.ini`.

## Tests

```bash
uv run pytest
```

The tests run against an in-memory SQLite database, so they need no server.

## Layout

```
app/
  main.py          FastAPI app and /health
  config.py        settings (pydantic-settings, reads .env)
  db.py            engine and per-request session dependency
  models.py        SQLModel tables and request/response schemas
  routers/         products, customers, orders
migrations/        Alembic environment and versions
tests/
frontend/
  src/api.ts       API client and types
  src/pages/       Orders, New order, Products, Customers
  src/index.css    styles (light and dark)
```
