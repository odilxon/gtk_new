# Backend

FastAPI + SQLAlchemy 2 (async) + PostgreSQL + Alembic.

## Структура

```
backend/
├── app/
│   ├── main.py              # FastAPI приложение, lifespan, CORS, роутеры
│   ├── config.py            # Pydantic Settings (читает .env)
│   ├── database.py          # async/sync engine, get_db, Base
│   ├── models.py            # ORM модели (единственный источник правды)
│   ├── security.py          # bcrypt, JWT, get_current_user
│   ├── schemas/             # Pydantic-схемы (auth, gtk, common)
│   ├── routers/             # APIRouter: auth, gtk, lookups
│   └── services/            # бизнес-логика отдельно от хендлеров
├── alembic/                 # миграции
├── scripts/
│   ├── db_load.py           # ETL из Excel в БД
│   ├── enrich.py            # обогащение: ISO коды стран + области из адресов
│   └── set_password.py      # CLI для создания/смены пароля пользователя
├── data/                    # справочники: oziqovqat.xlsx, fixes.xlsx, countries_ru_iso.json
├── requirements.txt
├── .env.example
└── run.sh
```

## Конфигурация

Все настройки — через `.env` (см. `.env.example`):

| Переменная | Описание |
|------------|----------|
| `DATABASE_URL` | async URL: `postgresql+asyncpg://...` |
| `SYNC_DATABASE_URL` | sync URL для Alembic и ETL |
| `SECRET_KEY` | JWT-ключ, от 32 символов |
| `ALGORITHM` | алгоритм JWT (по умолчанию HS256) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | срок жизни токена |
| `CORS_ORIGINS` | разрешённые origin через запятую |
| `APP_PORT` | порт uvicorn |
| `DEBUG` | echo SQL, подробные ошибки |

## Запуск

```bash
source .venv/bin/activate
./run.sh                                # или: uvicorn app.main:app --reload
```

Swagger UI: <http://localhost:8005/docs>.

## Миграции (Alembic)

```bash
alembic upgrade head                    # накатить все миграции
alembic revision --autogenerate -m "msg"  # сгенерировать миграцию из моделей
alembic downgrade -1                    # откатить последнюю
alembic history                         # список ревизий
```

`alembic/env.py` берёт URL из `app.config.settings.SYNC_DATABASE_URL` — поле
`sqlalchemy.url` в `alembic.ini` намеренно пустое.

## ETL

Загрузка `gtk_data_2020.xlsx` в БД (после `alembic upgrade head`):

```bash
python -m scripts.db_load load gtk_data_2020.xlsx
python -m scripts.db_load drop          # снести все таблицы (опасно)
```

### Обогащение для страницы аналитики

```bash
python -m scripts.enrich all            # ISO коды + области
python -m scripts.enrich countries      # только ISO
python -m scripts.enrich regions        # только regex по address_uz
```

### Управление пользователями

```bash
python -m scripts.set_password admin Admin123!
```

Создаёт пользователя с правами админа, если его нет; иначе — обновляет пароль.

## API (основные эндпоинты)

| Метод | Путь | Назначение |
|-------|------|-----------|
| POST  | `/api/auth/register` | регистрация |
| POST  | `/api/auth/login` | логин, возвращает JWT |
| GET   | `/api/auth/me` | текущий пользователь (Bearer токен) |
| GET   | `/api/gtk` | список с фильтрами и пагинацией |
| GET   | `/api/gtk/stats` | агрегаты: импорт/экспорт, топ-5 стран и категорий |
| GET   | `/api/countries` \| `/api/regions` \| `/api/categories` | справочники |
| GET   | `/api/products` | товары (фильтр `category_id`, `search`) |
| GET   | `/api/companies-uzb` \| `/api/companies-foreign` | компании |
| GET   | `/api/charts/years` | доступные годы |
| GET   | `/api/charts/monthly` | месячные ряды (импорт/экспорт + рост) |
| GET   | `/api/charts/group-summary?group=meva\|oziq` | totals по группе |
| GET   | `/api/charts/group-breakdown` | breakdown по подкатегориям |
| GET   | `/api/charts/top-organizations` | топ компаний |
| GET   | `/api/charts/top-countries` | топ стран |
| GET   | `/api/charts/regions` | для карты Узбекистана |
| GET   | `/api/charts/world` | для карты мира |
| GET   | `/health` | health-check |

Все `/api/*` (кроме `auth`) требуют заголовок `Authorization: Bearer <token>`.

## Известные особенности

- `Regime` — Python `enum.Enum` с **кириллическими** членами (`ИМ`, `ЭК`).
  Параметр `regime` API ожидает именно эти строки.
- Колонка единицы измерения в Excel — `"Eд.измерения"`, первая буква **латинская**
  `E`. Менять не надо — это так в исходном файле.
