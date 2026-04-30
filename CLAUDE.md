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
│   ├── routers/       # auth, users, admin, gtk, lookups, charts (APIRouter per domain)
│   └── services/      # business logic; charts.py + tnved_groups.py + gtk_etl.py
├── alembic/           # migrations (0001_initial, 0002_country_iso, 0003_gtk_dedup_hash)
├── scripts/
│   ├── db_load.py     # ETL Excel → DB (multiplies "Цена(тыс)" by 1000 at insert)
│   ├── enrich.py      # ISO codes + region extraction from address_uz
│   ├── fix_prices.py  # one-shot migration: gtk.price_thousand × 1000 (legacy data)
│   └── set_password.py # CLI to create/update user password
├── manage.sh          # bash wrapper: migrate / load / clean / reload / fresh / fix-prices / …
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
- An admin user can also manage accounts via `/dashboard/users` (UI) or `/api/users/*` (CRUD, all guarded by `Depends(get_current_admin)`). The router refuses to let an admin deactivate, revoke `is_admin` from, or delete themselves to avoid lockout.

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
python -m venv env && source env/Scripts/activate    # Linux/Mac: source env/bin/activate
pip install -r requirements.txt
cp .env.example .env                              # then edit DB creds + SECRET_KEY

# Everything else through manage.sh (it activates the venv itself):
./manage.sh migrate                               # alembic upgrade head
./manage.sh load data/gtk_data_2020.xlsx
./manage.sh enrich
./manage.sh user admin <pwd>
./manage.sh reload <file.xlsx>                    # clean + load + enrich (idempotent re-import)
./manage.sh fresh <file.xlsx>                     # drop + migrate + load + enrich
./manage.sh stats

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
- `/totals` — single-row totals (import / export / sum) used for the
  3-card row at the top of the page
- `/group-summary?group=meva|oziq` — totals (price + mass) for the agricultural groups
- `/group-breakdown` — table rows per sub-category, sourced from `data/fixes.xlsx`
- `/top-organizations`, `/top-countries` — bar-chart data
- `/regions` — Uzbekistan regions for the choropleth (uses `gtk.region_id`)
- `/world` — countries for the world choropleth (uses `Country.iso_code`)

## Excel upload + dedup

Admins can upload Excel files via `/dashboard/upload` or `POST /api/admin/upload-gtk`. The endpoint streams the multipart file to a temp path, runs the same ETL as the CLI (`scripts/db_load.py` is now a thin wrapper around `app/services/gtk_etl.py:load_excel`), and post-processes with `enrich_countries` only — region enrichment from `address_uz` was dropped per product decision.

Dedup is enforced by a unique hash on `gtk.dedup_hash`:

- `compute_row_hash` (in `gtk_etl.py`) returns SHA-256 of `date|regime|country_id|product_id|company_uzb_id|company_foreign_id|address_uz|address_foreign|unit|weight|quantity|price_thousand`. Numbers formatted as `f"{v:.6f}"`, NULL → empty string, `regime` as enum value (`ИМ`/`ЭК`).
- Inserts go through `pg_insert(...).on_conflict_do_nothing(index_elements=['dedup_hash'])` in batches of 5000. Counts `added` vs `duplicates_skipped` (intra-batch + DB conflicts) vs `invalid_skipped` (rows missing required FKs / unparseable date).
- **Don't change the hash format** without a new migration that recomputes all existing hashes — runtime inserts and the migration backfill must stay in lockstep.
- Migration `0003_gtk_dedup_hash` adds the column nullable, backfills via the same Python function in 5000-row windows, removes pre-existing dup rows (keep oldest id), then sets NOT NULL + UNIQUE INDEX. On the existing ~3M-row dataset this takes a few minutes.
- 100 MB upload size cap is enforced both in `routers/admin.py` (chunked read) and in the frontend page (`MAX_BYTES`).

## User management

Admin-only CRUD at `/api/users` and `/dashboard/users`:

- Create users with `username`/`email`/`password`/`full_name`/`is_active`/`is_admin`.
- Edit any field except `username` (treated as immutable identity); leaving the password blank in the edit form keeps the existing hash.
- Self-protection: the API refuses to let an admin deactivate, revoke admin from, or delete themselves; the UI mirrors this by disabling the delete button for the current user and showing a "self" badge.

All chart endpoints (and `/api/gtk`) accept `tnved: list[str]`.
`/api/products/tnved-search?q=<3+>` is the async lookup powering the
multi-select. The frontend supports a `707*` wildcard: it strips the `*`,
asks the backend with a higher `limit`, and offers a "Add all (N)" button.

The Uzbekistan choropleth and the per-group `Озиқ-овқат / Мева-сабзавот`
cards have been removed from `/dashboard/charts`. `UzbekistanMap.tsx` and
`GroupCard.tsx` are still in the repo but unused on that page.

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
- Region data isn't in raw Excel — it comes from `scripts/enrich.py regions`. The script does **bulk SQL** (one `UPDATE ... WHERE address_uz ILIKE '%alias%'` per alias), not Python-side regex; loading 2M rows into Python hung the terminal. Aliases include both Uzbek (`Тошкент шаҳри`, `Самарқанд` …) and Russian (`г. Ташкент`, `Самарканд` …) variants. Sorting by alias length DESC + filter `region_id IS NULL` reproduces longest-match semantics so city-of-Tashkent rows don't fall into the region.
- Country ISO codes are populated by `scripts/enrich.py countries`. Without them the world map is empty.
- **`gtk.price_thousand` stores actual USD**, not thousands, despite the column name. Excel column "Цена(тыс)" is in thousands; `db_load` multiplies by 1000 at insert. Legacy data was migrated once via `scripts/fix_prices.py` (≈3M rows). **Never run `fix-prices` twice** — not idempotent. The frontend `formatPrice` and the `avg = massa / total` in `group_breakdown` were both updated to match this semantics; if you see prices off by 1000×, this is the first place to look.
- ETL commits in batches of 20000 rows (was 500). `gtk` itself has no dedup, so re-running `load` on the same file double-inserts; use `manage.sh reload` (or `fresh`) for re-import.
- ECharts `world.json` has only `{name, childNum}` in feature properties — no ISO codes. `frontend/src/components/charts/worldMapNames.ts` ships a static ISO-2 → ECharts-name dictionary; do **not** try to read `iso_a2` from the geojson.
- Axios v1's default array serialization is `?key[0]=a&key[1]=b`, which doesn't bind to FastAPI `Query(list[str])`. `frontend/src/lib/api.ts` configures a custom `paramsSerializer` that emits repeated keys (`?key=a&key=b`). Keep it when adding new endpoints with array params.
- The dashboard layout uses a sticky **top header**, not a sidebar (was a sidebar). `/dashboard/charts` uses `max-w-screen-2xl` to use the freed width; `/dashboard/gtk` stays at `max-w-7xl` for the header/filters block but the table card escapes that wrapper to span the full main width.
- **Naive datetimes for the `users` table.** `users.created_at` / `users.updated_at` are `Column(DateTime)` without `timezone=True`, so the column type is `TIMESTAMP WITHOUT TIME ZONE`. asyncpg refuses to bind tz-aware values into naive columns — services write `datetime.utcnow()`, not `datetime.now(timezone.utc)`. If you ever swap to a tz-aware column, update both `services/auth.py:register_user` and `services/users.py` (`_now()`).
- The dashboard nav item "Foydalanuvchilar / Пользователи / Users" only appears when `me.is_admin === 1`; the page itself also redirects non-admins back to `/dashboard`. Backend is the source of truth via `get_current_admin` — UI guards are convenience only.
- `/dashboard/gtk` filters use a **draft + apply** pattern: editing fields updates a local draft and shows a "не применено" badge. The query only fires when the user clicks **Обновить** (or presses Enter inside the form). Pagination changes apply directly without going through the draft.
