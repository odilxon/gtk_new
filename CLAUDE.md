# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Architecture

Two-tier app for browsing 2020 Uzbekistan foreign-trade (GTK) records.

- `backend/` — FastAPI + async SQLAlchemy on PostgreSQL (asyncpg). Modular layout under `backend/app/` (config, database, models, security, schemas/, routers/, services/). Migrations in `backend/alembic/`. ETL in `backend/scripts/db_load.py`.
- `frontend/` — Next.js 16 (App Router) + React 19 + Tailwind v4 + TanStack Query. UI is Russian-language. Auth state lives in `localStorage` and is attached via an Axios interceptor in `src/lib/api.ts`.

### Backend layout

```
backend/
├── app/
│   ├── main.py        # FastAPI(), lifespan, CORS, include_router
│   ├── config.py      # Pydantic Settings (reads .env)
│   ├── database.py    # async/sync engines, Base, get_db
│   ├── models.py      # ORM — single source of truth (also used by Alembic + ETL)
│   ├── security.py    # bcrypt (direct), JWT, get_current_user, get_current_admin
│   ├── schemas/       # Pydantic: auth, gtk, charts, common
│   ├── routers/       # auth, gtk, lookups, charts (APIRouter per domain)
│   └── services/      # business logic; charts.py + tnved_groups.py for analytics
├── alembic/           # migrations (0001_initial, 0002_country_iso)
├── scripts/
│   ├── db_load.py     # ETL Excel → DB
│   ├── enrich.py      # ISO codes + region extraction from address_uz
│   └── set_password.py # CLI to create/update user password
└── data/              # static data: oziqovqat.xlsx, fixes.xlsx, countries_ru_iso.json
```

`scripts/db_load.py` imports models from `app.models` — there is no longer a duplicated schema definition. Alembic's `env.py` also reuses `app.models` and `app.database.Base`.

### Domain model (PostgreSQL)

`gtk` is the fact table. Lookups: `countries`, `regions`, `categories`, `products` (FK→category, holds `tnved` code), `companies_uzb` (with `stir`), `companies_foreign`. Plus a `users` table for auth.

`Regime` is a Python `enum.Enum` with **Cyrillic** members: `Regime.ИМ` (import) and `Regime.ЭК` (export). The API's `regime` query parameter expects those literal Cyrillic strings — `Regime[regime]` lookup in `app/services/gtk.py` depends on this.

### Auth

- Passwords: **bcrypt** (used directly via the `bcrypt` package, not `passlib` — `passlib`
  is incompatible with `bcrypt 4.x`). See `app/security.py`.
- Token: **JWT** (HS256 by default), `sub` = user id, exp from `ACCESS_TOKEN_EXPIRE_MINUTES`.
- Read from `Authorization: Bearer <token>` header via `OAuth2PasswordBearer`.
- All `/api/*` routes except `/api/auth/*` and `/health` require auth (router-level `Depends(get_current_user)`).
- `SECRET_KEY` comes from `.env`. Rotate on deploy.
- Use `python -m scripts.set_password <user> <pwd>` to create/update users from CLI.

### Frontend ↔ backend wiring

- Backend port: `APP_PORT` from `.env` (default **8005**), started via `backend/run.sh`.
- Frontend default in `src/lib/api.ts:3` is `http://localhost:8005`. Override via `NEXT_PUBLIC_API_URL` (see `frontend/.env.example`).
- CORS origins are configured via `CORS_ORIGINS` (comma-separated) in `backend/.env`.

### Important: Next.js version

`frontend/AGENTS.md` (loaded into Claude via `frontend/CLAUDE.md`) warns this is **Next.js 16.2.4 with React 19** — APIs, conventions, and file layout differ from older versions. Before writing frontend code, consult `node_modules/next/dist/docs/` rather than relying on prior Next.js knowledge.

## Common commands

### Backend (Python 3.12, see `backend/.python-version`)

Run from `backend/`:

```bash
# Setup
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env                              # then edit DB creds + SECRET_KEY

# Migrations
alembic upgrade head                              # apply all
alembic revision --autogenerate -m "msg"          # generate from app.models
alembic downgrade -1                              # roll back one

# ETL (run after migrations)
python -m scripts.db_load load gtk_data_2020.xlsx
python -m scripts.db_load drop                    # destructive

# Dev server
./run.sh                                          # uvicorn app.main:app --reload --port 8005
```

Swagger UI: <http://localhost:8005/docs>.

### Frontend (Node 22.22.1, see `frontend/.nvmrc`)

Run from `frontend/`:

```bash
cp .env.example .env.local
npm install
npm run dev      # Next.js dev server (port 3000)
npm run build
npm run start
npm run lint
```

There is no test suite in either tier.

## Analytics page (`/dashboard/charts`)

Visualizes import/export aggregates with ECharts. Powered by `/api/charts/*`:

- `/years` — distinct years from `gtk.date`
- `/monthly` — monthly time-series per year (raw + cumulative)
- `/group-summary?group=meva|oziq` — totals (price + mass) for the agricultural groups
- `/group-breakdown` — table rows per sub-category, sourced from `data/fixes.xlsx`
- `/top-organizations`, `/top-countries` — bar-chart data
- `/regions` — Uzbekistan regions for the choropleth (uses `gtk.region_id`)
- `/world` — countries for the world choropleth (uses `Country.iso_code`)

**Group definitions** (from `app/services/tnved_groups.py`):
- `meva` — Product.tnved matches prefix `07*`, `08*`, `0904*`, `1008*`, `1202*`, or equals `1207409000` / `2008191900`
- `oziq` — Product.tnved is in the 787-code list cached from `data/oziqovqat.xlsx`

**GeoJSON** lives in `frontend/public/geo/`:
- `world.json` — Apache ECharts repo
- `uzbekistan.json` — extracted from Natural Earth admin1, names rewritten to match `Region.name`

**Required preprocessing** before the page works:
1. `alembic upgrade head` — applies `0002_country_iso` (adds `iso_code`, `name_uz` to `countries`)
2. `python -m scripts.enrich all` — fills ISO codes from `data/countries_ru_iso.json` and matches `region_id` via regex on `address_uz` (raw Excel has empty `Область`)

## Gotchas

- **Single source of truth for the schema** is `backend/app/models.py`. Both Alembic and the ETL import from it.
- `alembic.ini`'s `sqlalchemy.url` is intentionally empty — `alembic/env.py` injects `settings.SYNC_DATABASE_URL` at runtime.
- ETL script reads the Excel column `"Eд.измерения"` — note the leading **Latin "E"** (not Cyrillic "Е"). Constant `COL_UNIT` in `scripts/db_load.py` documents this.
- Auth uses bcrypt directly (no `passlib`) — any pre-existing SHA-256 password hashes from the old code are incompatible. Recreate users via `scripts/set_password.py` after migrating.
- `CORS_ORIGINS` must include the frontend origin (`http://localhost:3000` for dev). `*` is no longer the default.
- Region data isn't in raw Excel — it comes from `scripts/enrich.py regions` (regex on `address_uz`). Without this, the Uzbekistan choropleth is empty.
- Country ISO codes are populated by `scripts/enrich.py countries`. Without them the world map is empty.
