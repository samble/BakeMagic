# BakeMagic

A bakery management API: products, customers and orders. Understands scheduling for days and has customer logins for viewing invoices.

Built with **FastAPI**, **SQLModel** (SQLAlchemy 2 + Pydantic 2), **PostgreSQL** via psycopg 3, and **Alembic** for migrations.

## Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
cp .env.example .env          # then set DATABASE_URL
```

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
.venv/bin/alembic upgrade head
```

## Run

```bash
.venv/bin/fastapi dev app/main.py
```

- Interactive docs: http://127.0.0.1:8000/docs
- Health check (includes a database round trip): http://127.0.0.1:8000/health

## Lint

[Ruff](https://docs.astral.sh/ruff/) is configured in `pyproject.toml` (installed with the `dev` extra):

```bash
.venv/bin/ruff check .         # report problems
.venv/bin/ruff check . --fix   # fix what can be fixed automatically
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

`npm run build` type-checks and writes static files to `frontend/dist/`. In production, serve those and route `/api/*` to the API from the same origin, for example with nginx.

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
.venv/bin/alembic revision --autogenerate -m "describe the change"
# review the generated file in migrations/versions/, then
.venv/bin/alembic upgrade head
```

`alembic upgrade head --sql` prints the SQL without touching the database. Alembic reads `DATABASE_URL` from the app settings, so there's no URL in `alembic.ini`.

## Tests

```bash
.venv/bin/pytest
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
