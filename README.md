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
python -m venv env
source env/Scripts/activate         # Linux/Mac: source env/bin/activate
pip install -r requirements.txt

cp .env.example .env                # отредактировать DATABASE_URL и SECRET_KEY
```

Дальше всё через `manage.sh` — обёртка активирует venv сама:

```bash
./manage.sh migrate                 # alembic upgrade head
./manage.sh load data/gtk_data_2020.xlsx
./manage.sh enrich                  # ISO коды стран + области из адресов
./manage.sh user admin Admin123!    # создать/обновить админа

./run.sh                            # uvicorn на :8005 (или APP_PORT из .env)
```

Команды `manage.sh`:

| Команда | Что делает |
|---------|------------|
| `migrate` | накатить миграции (`alembic upgrade head`) |
| `load <file.xlsx>` | залить данные из Excel |
| `clean` | очистить таблицу `gtk` (справочники остаются) |
| `enrich` | `enrich all` — ISO коды + регионы |
| `reload <file.xlsx>` | `clean` → `load` → `enrich` (ре-импорт без дублей) |
| `stats` | количество записей по всем таблицам |
| `user <name> <pwd>` | создать/обновить пользователя |
| `drop` | снести все таблицы (с подтверждением) |
| `fresh <file.xlsx>` | `drop` → `migrate` → `load` → `enrich` (с нуля, с подтверждением) |
| `fix-prices` | **РАЗОВО** — умножить `gtk.price_thousand * 1000` для старых данных |

> Повторный импорт того же файла — `./manage.sh reload <file.xlsx>`. Простой
> `load` дубли не отсекает на уровне `gtk`, так что для пере-загрузки используй
> `reload` или `fresh`.

> ⚠️ `fix-prices` — одноразовая миграция. Ранние версии ETL складывали колонку
> Excel «Цена(тыс)» как есть, поэтому в БД лежали значения в *тысячах* долларов.
> Сейчас `db_load` сам множит на 1000 при загрузке, а `fix-prices` приводит
> уже залитые данные. Запуск дважды испортит данные — он не идемпотентен.

Документация API: <http://localhost:8005/docs>.

### Фронтенд

Требуется Node 22 (см. `frontend/.nvmrc`).

```bash
cd frontend
cp .env.example .env.local
npm install
npm run dev                         # http://localhost:3000
```

## Возможности

- `/dashboard/gtk` — постраничная таблица записей с фильтрами (страна, область,
  ТНВЕД, режим, диапазон дат, поиск). Фильтры применяются по кнопке «Янгилаш».
- `/dashboard/charts` — аналитическая страница с картой мира, помесячными
  графиками, топ-чартами, итоговыми карточками. ТНВЕД-фильтр поддерживает
  wildcard вида `707*` (выпадашка предлагает «Добавить все»).
- `/dashboard/users` — управление пользователями (доступно только админам).
- Переключатель языка в хедере: узбекский (кириллица), русский, английский.
  Выбор сохраняется в `localStorage`.

## Документация

- [`backend/README.md`](backend/README.md) — API, миграции, ETL.
- [`GTK.md`](GTK.md) — описание полей и статистика по датасету.
- [`CLAUDE.md`](CLAUDE.md) — инструкции для Claude Code.
