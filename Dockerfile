# ---------- frontend: build the static bundle ----------
FROM node:26-slim AS frontend
WORKDIR /frontend
# Install dependencies first, so this layer is reused until the lockfile changes.
COPY frontend/package.json frontend/package-lock.json ./
RUN --mount=type=cache,target=/root/.npm npm ci
COPY frontend/ ./
RUN npm run build

# ---------- app: the API, serving the frontend bundle ----------
FROM python:3.12-slim

# Install uv, pinned to match uv.lock's tooling.
COPY --from=ghcr.io/astral-sh/uv:0.13.10 /uv /uvx /bin/

# Precompile bytecode for faster startup; copy (not hardlink) from the cache mount;
# leave out the dev dependency group (pytest, ruff, ...).
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_NO_DEV=1

WORKDIR /app

# Install dependencies first, so this layer is reused until pyproject.toml or uv.lock change.
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project

# Copy the application and install it, then add the built frontend bundle
# (node_modules and any local dist/ are kept out by .dockerignore).
COPY . .
COPY --from=frontend /frontend/dist ./frontend/dist
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-editable

# Run as an unprivileged user.
RUN useradd --system --no-create-home app
USER app

# Put the venv's tools first, so one-off commands work too (e.g. `alembic upgrade head`).
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000
# app.web serves the API under /api and the frontend everywhere else.
CMD ["fastapi", "run", "app/web.py", "--port", "8000"]
