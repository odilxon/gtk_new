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
│   ├── db_load.py           # CLI-обёртка над app/services/gtk_etl
│   ├── enrich.py            # обогащение: ISO коды стран + области из адресов
│   ├── fix_prices.py        # одноразовая миграция gtk.price_thousand × 1000
│   └── set_password.py      # CLI для создания/смены пароля пользователя
├── data/                    # справочники: oziqovqat.xlsx, fixes.xlsx, countries_ru_iso.json
├── requirements.txt
├── .env.example
├── manage.sh                # обёртка над всеми операциями (migrate/load/reload/...)
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
source env/Scripts/activate             # Linux/Mac: source env/bin/activate
./run.sh                                # или: uvicorn app.main:app --reload
```

Swagger UI: <http://localhost:8005/docs>.

## manage.sh — обёртка над всеми операциями

Скрипт активирует venv (`env/Scripts/activate`) и пробрасывает аргументы
дальше. Запускать из `backend/`.

| Команда | Что делает |
|---------|------------|
| `./manage.sh migrate` | `alembic upgrade head` |
| `./manage.sh load <file.xlsx>` | залить данные из Excel |
| `./manage.sh clean` | удалить все записи из `gtk` (справочники остаются) |
| `./manage.sh enrich` | `enrich all` — ISO коды + регионы |
| `./manage.sh reload <file.xlsx>` | `clean` → `load` → `enrich` (ре-импорт без дублей) |
| `./manage.sh stats` | количество записей по всем таблицам |
| `./manage.sh user <name> <pwd>` | создать/обновить пользователя (админ) |
| `./manage.sh drop` | снести все таблицы (с подтверждением) |
| `./manage.sh fresh <file.xlsx>` | `drop` → `migrate` → `load` → `enrich` (с нуля) |
| `./manage.sh fix-prices` | **одноразовая** миграция `price_thousand × 1000` для старых данных |

Типичные сценарии:

```bash
# Первая установка
./manage.sh migrate
./manage.sh load data/gtk_data_2020.xlsx
./manage.sh enrich
./manage.sh user admin Admin123!

# Повторная заливка того же файла (или нового среза за тот же период)
./manage.sh reload data/gtk_data_2020.xlsx

# Перезалить с нуля, включая структуру
./manage.sh fresh data/gtk_data_2020.xlsx
```

> `load` сам по себе **не отсекает дубли** на уровне таблицы `gtk` — повторный
> запуск удвоит записи. Для ре-импорта используй `reload` (или `fresh`).

## Миграции (Alembic)

```bash
alembic upgrade head                    # накатить все миграции
alembic revision --autogenerate -m "msg"  # сгенерировать миграцию из моделей
alembic downgrade -1                    # откатить последнюю
alembic history                         # список ревизий
```

`alembic/env.py` берёт URL из `app.config.settings.SYNC_DATABASE_URL` — поле
`sqlalchemy.url` в `alembic.ini` намеренно пустое.

## Низкоуровневые команды

`manage.sh` покрывает основные сценарии. При необходимости подкоманды доступны
напрямую:

```bash
python -m scripts.db_load load <file.xlsx>
python -m scripts.db_load clean         # удалить только записи gtk
python -m scripts.db_load drop          # снести все таблицы (опасно)

python -m scripts.enrich all            # ISO коды + области
python -m scripts.enrich countries      # только ISO
python -m scripts.enrich regions        # только regex по address_uz

python -m scripts.set_password admin Admin123!
```

## API (основные эндпоинты)

| Метод | Путь | Назначение |
|-------|------|-----------|
| POST  | `/api/auth/register` | регистрация |
| POST  | `/api/auth/login` | логин, возвращает JWT |
| GET   | `/api/auth/me` | текущий пользователь (Bearer токен) |
| GET   | `/api/users` | список пользователей (только админ) |
| POST  | `/api/users` | создать пользователя (только админ) |
| PATCH | `/api/users/{id}` | обновить (email/full_name/password/is_active/is_admin, только админ) |
| DELETE| `/api/users/{id}` | удалить пользователя (только админ) |
| POST  | `/api/admin/upload-gtk` | мультипарт-загрузка Excel в `gtk` (только админ) |
| GET   | `/api/gtk` | список с фильтрами и пагинацией |
| GET   | `/api/gtk/stats` | агрегаты: импорт/экспорт, топ-5 стран и категорий |
| GET   | `/api/countries` \| `/api/regions` \| `/api/categories` | справочники |
| GET   | `/api/products` | товары (фильтр `category_id`, `search`) |
| GET   | `/api/products/tnved-search?q=<3+>` | async-поиск ТНВЕД по префиксу |
| GET   | `/api/companies-uzb` \| `/api/companies-foreign` | компании |
| GET   | `/api/charts/years` | доступные годы |
| GET   | `/api/charts/monthly` | месячные ряды (импорт/экспорт + рост) |
| GET   | `/api/charts/totals` | сумма импорт/экспорт/всего без группы |
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
- **`gtk.price_thousand` хранит фактическую сумму в долларах**, не в тысячах,
  несмотря на «исторический» суффикс `_thousand` в имени. Excel-колонка
  «Цена(тыс)» исходно в тысячах, поэтому `db_load` множит её на 1000 при ETL,
  а старые данные были разово приведены `scripts/fix_prices.py`. Не запускай
  `fix-prices` повторно — операция не идемпотентна, второй прогон умножит ещё
  раз на 1000.
- **Дедуп `gtk` по `dedup_hash`.** В колонке лежит SHA-256 от канонической
  pipe-строки полей `(date|regime|country_id|product_id|company_uzb_id|
  company_foreign_id|address_uz|address_foreign|unit|weight|quantity|
  price_thousand)`. Числа форматируются как `f"{v:.6f}"`, NULL → пустая
  строка, дата — `isoformat()`. Эта же функция (`compute_row_hash` в
  `app/services/gtk_etl.py`) вызывается из миграции `0003_gtk_dedup_hash`
  для бэкфилла. Менять формат можно **только** новой миграцией,
  пересчитывающей все хеши, иначе runtime-инсёрты перестанут совпадать
  с уже залитыми строками.
- ETL общий: и `python -m scripts.db_load load` и `POST /api/admin/upload-gtk`
  идут через `gtk_etl.load_excel`, который вставляет `gtk` через
  `INSERT … ON CONFLICT (dedup_hash) DO NOTHING` батчами по 5000.
- Колонки `users.created_at` / `users.updated_at` объявлены как
  `Column(DateTime)` без `timezone=True`, и в БД лежат как
  `TIMESTAMP WITHOUT TIME ZONE`. asyncpg запрещает биндить tz-aware значения
  в naive колонки — поэтому `services/auth.py` и `services/users.py`
  записывают `datetime.utcnow()` (наивное), а **не** `datetime.now(timezone.utc)`.
  Если меняешь модель на `timezone=True`, нужна миграция и обратный переход.
- `/api/users/*` защищён через `Depends(get_current_admin)` на уровне роутера.
  Дополнительно роуты `PATCH`/`DELETE` запрещают админу деактивировать,
  разжаловать или удалить самого себя — иначе можно лишиться единственного
  админа в системе.
- `enrich.regions` использует bulk-UPDATE по подстроке (ILIKE) для каждого
  алиаса региона; список включает узбекские и русские варианты
  («Тошкент шаҳри», «г. Ташкент», «Самарқанд», «Самарканд» …). Сортировка
  по убыванию длины + фильтр `region_id IS NULL` дают то же поведение,
  что у regex-альтернации с longest-match семантикой.
- ТНВЕД-фильтр на странице `/dashboard/charts` принимает wildcard вида
  `707*`: фронт удаляет `*`, шлёт префикс на `/api/products/tnved-search`
  с `limit=1000`, выпадашка предлагает «Добавить все».
- `axios` v1 по умолчанию шлёт массивы как `key[0]=…&key[1]=…`, что не
  байндится в FastAPI `Query(list[str])`. В `frontend/src/lib/api.ts` стоит
  кастомный `paramsSerializer`, превращающий массивы в повторяющиеся ключи
  (`?tnved=A&tnved=B`).
