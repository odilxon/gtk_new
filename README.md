# GTK Dashboard

Веб-приложение для просмотра данных внешнеторговой деятельности Узбекистана за 2020 год.

## Структура

```
.
├── backend/        # FastAPI + SQLAlchemy (async) + Alembic
├── frontend/       # Next.js 16 + React 19 + Tailwind v4
└── GTK.md          # описание датасета
```

## Быстрый старт

### Бэкенд

Требуется Python 3.12 и PostgreSQL.

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env                # отредактировать DATABASE_URL и SECRET_KEY

alembic upgrade head                # создать таблицы
python -m scripts.db_load load gtk_data_2020.xlsx   # загрузить данные
python -m scripts.enrich all        # ISO коды стран + области из адресов
python -m scripts.set_password admin Admin123!      # создать админа

./run.sh                            # uvicorn на :8005 (или APP_PORT из .env)
```

Документация API: <http://localhost:8005/docs>.

### Фронтенд

Требуется Node 22 (см. `frontend/.nvmrc`).

```bash
cd frontend
cp .env.example .env.local
npm install
npm run dev                         # http://localhost:3000
```

## Документация

- [`backend/README.md`](backend/README.md) — API, миграции, ETL.
- [`GTK.md`](GTK.md) — описание полей и статистика по датасету.
- [`CLAUDE.md`](CLAUDE.md) — инструкции для Claude Code.
