# Инструкция по запуску после рефакторинга

Документ описывает, как развернуть проект после переезда на новую структуру (FastAPI app/, Alembic, JWT + bcrypt, TanStack Query). Если БД с данными уже есть — следуй шагам в порядке.

---

## 1. Бэкенд

### 1.1. Установить зависимости

В `backend/requirements.txt` добавлены **новые** пакеты:

- `pydantic-settings`
- `alembic`
- `python-jose[cryptography]`
- `passlib[bcrypt]`
- `email-validator`
- `psycopg2-binary` (нужен для Alembic — он работает синхронно)

```bash
cd backend
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 1.2. Создать `.env`

Скопировать шаблон и отредактировать:

```bash
cp .env.example .env
```

Минимальный набор переменных:

```env
DATABASE_URL=postgresql+asyncpg://user:password@host:port/gtk_data
SYNC_DATABASE_URL=postgresql://user:password@host:port/gtk_data
SECRET_KEY=замени-на-случайную-строку-минимум-32-символа
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
CORS_ORIGINS=http://localhost:3000
APP_PORT=8005
DEBUG=false
```

**Важные тонкости:**

- `DATABASE_URL` — async URL **с** `+asyncpg`. Используется FastAPI.
- `SYNC_DATABASE_URL` — sync URL **без** `+asyncpg`. Используется Alembic и ETL.
  Если перепутать — Alembic упадёт с `ModuleNotFoundError: No module named 'asyncpg'`
  или `InvalidRequestError`.
- `SECRET_KEY` — **обязательно сменить**. Сгенерировать можно так:
  ```bash
  python -c "import secrets; print(secrets.token_urlsafe(48))"
  ```
- `CORS_ORIGINS` — через запятую. Для прода: `https://your-domain.com`.

### 1.3. Применить миграции Alembic

#### Вариант А — БД уже существует с таблицами (есть данные)

Раньше таблицы создавались через `Base.metadata.create_all`. Теперь — через
Alembic. Чтобы он не пытался накатить миграцию поверх существующих таблиц,
нужно «отметить» БД как уже смигрированную:

```bash
alembic stamp head
```

Эта команда **не меняет схему**, только записывает в служебную таблицу
`alembic_version`, что миграция `0001_initial` уже применена. После этого
будущие `alembic revision --autogenerate` будут работать корректно.

#### Вариант Б — БД пустая или без таблиц

```bash
alembic upgrade head
```

Это создаст всю схему заново.

#### Проверка

```bash
alembic current     # должен показать: 0001_initial (head)
alembic history     # список ревизий
```

### 1.4. Пересоздать пароли пользователей

Старые пароли в `users.password_hash` хранятся как **SHA-256 без соли**.
Новый код использует **bcrypt** — старые хеши не пройдут проверку
`pwd_context.verify(...)`, логин будет падать с `Invalid credentials`.

Выбери один из вариантов:

#### Вариант А — удалить старых и зарегистрировать заново

```sql
TRUNCATE users RESTART IDENTITY;
```

Затем через API:

```bash
curl -X POST http://localhost:8005/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","email":"admin@example.com","password":"strong-password","full_name":"Admin"}'
```

После регистрации — выставить `is_admin=1` вручную в SQL:

```sql
UPDATE users SET is_admin = 1 WHERE username = 'admin';
```

#### Вариант Б — установить пароль через CLI-скрипт (рекомендуется)

```bash
python -m scripts.set_password admin Admin123!
```

Если пользователь не существует — будет создан с правами админа.
Если существует — пароль перезапишется.

#### Вариант В — сгенерировать хеш и вставить вручную

```bash
python -c "from app.security import hash_password; print(hash_password('новый-пароль'))"
```

```sql
UPDATE users SET password_hash = '$2b$12$...' WHERE username = 'admin';
```

### 1.5. Загрузка данных из Excel (если БД пустая)

```bash
python -m scripts.db_load load gtk_data_2020.xlsx
```

Запускать **после** `alembic upgrade head`.

### 1.5.1. Обогащение данных (для страницы аналитики)

После загрузки нужно проставить ISO-коды стран и извлечь область из адресов:

```bash
python -m scripts.enrich all
# или по отдельности:
python -m scripts.enrich countries
python -m scripts.enrich regions
```

- `countries` — заполняет `iso_code` и `name_uz` по `data/countries_ru_iso.json`
- `regions` — создаёт 14 областей и сматчивает `gtk.region_id` regex'ом
  по `address_uz`

### 1.6. Запуск сервера

```bash
./run.sh
# либо: uvicorn app.main:app --reload --port 8005
```

Проверка:

- Health: <http://localhost:8005/health>
- Swagger UI: <http://localhost:8005/docs>

---

## 2. Фронтенд

### 2.1. Установить зависимости

В `frontend/package.json` уже был `@tanstack/react-query`, но раньше он
не использовался. Теперь подключён через `Providers`. Просто установить:

```bash
cd frontend
npm install
```

### 2.2. Создать `.env.local`

```bash
cp .env.example .env.local
```

Содержимое:

```env
NEXT_PUBLIC_API_URL=http://localhost:8005
```

**Должен совпадать с `APP_PORT` бэка.** Раньше был дефолт `8001` — теперь `8005`.

### 2.3. Запуск

```bash
npm run dev
```

Открыть <http://localhost:3000>.

---

## 3. Проверка работоспособности

1. Открыть <http://localhost:3000> → должен редиректнуть на `/login`.
2. Залогиниться созданным пользователем.
3. Перейти на `/dashboard/gtk` → загрузится таблица записей.
4. Проверить фильтры (страна, категория, режим, дата) — обновляются без перезагрузки.
5. Пагинация — работает.
6. Кнопка «Выйти» в сайдбаре — чистит токен и возвращает на логин.

---

## 4. Частые проблемы

| Симптом | Причина | Решение |
|---------|---------|---------|
| `ModuleNotFoundError: No module named 'app'` | Запуск из неверной папки | `cd backend` перед `uvicorn`/`alembic` |
| `relation "users" already exists` | Alembic пытается создать таблицы поверх существующих | `alembic stamp head` |
| `ModuleNotFoundError: asyncpg` при alembic | В `SYNC_DATABASE_URL` указан `+asyncpg` | Убрать `+asyncpg` из sync URL |
| Логин выдаёт `Invalid credentials` | Старые SHA-256 хеши паролей | Пересоздать пароли (см. 1.4) |
| `CORS error` в браузере | `CORS_ORIGINS` не содержит origin фронта | Добавить `http://localhost:3000` в `.env` бэка, перезапустить uvicorn |
| `Network Error` в фронте | Бэк не запущен или порт не совпадает | Проверить `APP_PORT` бэка и `NEXT_PUBLIC_API_URL` фронта |
| `401 Unauthorized` на каждом запросе | JWT просрочен или `SECRET_KEY` сменился | Перелогиниться (старый токен в `localStorage` уже не валиден) |
| Фронт вечно крутит спиннер | Бэкенд возвращает 500, токен битый | DevTools → Network: посмотреть, какой запрос падает |

---

## 5. Чек-лист перед деплоем

- [ ] `SECRET_KEY` сгенерирован случайно, не лежит в репо
- [ ] `.env` в `.gitignore` (уже есть)
- [ ] `CORS_ORIGINS` указан для прод-домена, не `*`
- [ ] `DEBUG=false`
- [ ] Alembic применён (`alembic current` → head)
- [ ] У всех пользователей пароли в bcrypt
- [ ] `NEXT_PUBLIC_API_URL` указывает на прод-бэк
- [ ] Фронт собран: `npm run build && npm run start`

---

## 6. Команды-шпаргалка

### Бэкенд

```bash
# Установка
pip install -r requirements.txt

# Миграции
alembic upgrade head                           # накатить
alembic stamp head                             # отметить как применённые
alembic revision --autogenerate -m "msg"       # сгенерировать новую
alembic downgrade -1                           # откатить одну
alembic current                                # текущая ревизия
alembic history                                # история

# ETL
python -m scripts.db_load load gtk_data_2020.xlsx
python -m scripts.db_load drop                 # снести все таблицы (опасно)

# Обогащение (для страницы аналитики)
python -m scripts.enrich all                   # ISO-коды + области
python -m scripts.enrich countries
python -m scripts.enrich regions

# Управление пользователями
python -m scripts.set_password admin Admin123! # создать/обновить пароль

# Сервер
./run.sh
uvicorn app.main:app --reload --port 8005
```

### Фронтенд

```bash
npm install
npm run dev          # http://localhost:3000
npm run build
npm run start
npm run lint
```
