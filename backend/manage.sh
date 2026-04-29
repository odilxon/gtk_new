#!/bin/bash
# Утилита для управления БД GTK.
#
# Использование:
#   ./manage.sh migrate                  — накатить миграции (alembic upgrade head)
#   ./manage.sh clean                    — удалить все записи из gtk
#   ./manage.sh load <file.xlsx>         — залить данные из Excel
#   ./manage.sh enrich                   — enrich all (ISO коды + регионы)
#   ./manage.sh reload <file.xlsx>       — clean + load + enrich (полный ре-импорт)
#   ./manage.sh stats                    — счётчики по таблицам
#   ./manage.sh user <username> <pwd>    — создать/обновить пользователя
#   ./manage.sh drop                     — снести все таблицы (опасно)
#   ./manage.sh fresh <file.xlsx>        — drop + migrate + load + enrich (с нуля)
#   ./manage.sh fix-prices               — РАЗОВО умножить gtk.price_thousand на 1000

set -e

cd "$(dirname "$0")"
source env/Scripts/activate

cmd="${1:-}"

case "$cmd" in
  migrate)
    alembic upgrade head
    ;;

  clean)
    python -m scripts.db_load clean
    ;;

  load)
    if [ -z "${2:-}" ]; then
      echo "Укажи путь к xlsx: ./manage.sh load <file.xlsx>"
      exit 1
    fi
    python -m scripts.db_load load "$2"
    ;;

  enrich)
    python -m scripts.enrich all
    ;;

  reload)
    if [ -z "${2:-}" ]; then
      echo "Укажи путь к xlsx: ./manage.sh reload <file.xlsx>"
      exit 1
    fi
    echo "==> clean"
    python -m scripts.db_load clean
    echo "==> load $2"
    python -m scripts.db_load load "$2"
    echo "==> enrich all"
    python -m scripts.enrich all
    echo "Готово."
    ;;

  stats)
    python -c "
from sqlalchemy.orm import sessionmaker
from app.database import sync_engine
from app.models import GTK, Country, Region, Category, Product, CompanyUzb, CompanyForeign, User
S = sessionmaker(bind=sync_engine)()
for m in (GTK, Country, Region, Category, Product, CompanyUzb, CompanyForeign, User):
    print(f'  {m.__tablename__:22s} {S.query(m).count()}')
"
    ;;

  user)
    if [ -z "${2:-}" ] || [ -z "${3:-}" ]; then
      echo "Использование: ./manage.sh user <username> <password>"
      exit 1
    fi
    python -m scripts.set_password "$2" "$3"
    ;;

  drop)
    read -p "Точно снести все таблицы? [y/N] " ans
    [ "$ans" = "y" ] || { echo "Отменено."; exit 0; }
    python -m scripts.db_load drop
    ;;

  fresh)
    if [ -z "${2:-}" ]; then
      echo "Укажи путь к xlsx: ./manage.sh fresh <file.xlsx>"
      exit 1
    fi
    read -p "Снести все таблицы и залить заново из $2? [y/N] " ans
    [ "$ans" = "y" ] || { echo "Отменено."; exit 0; }
    echo "==> drop"
    python -m scripts.db_load drop
    echo "==> migrate"
    alembic upgrade head
    echo "==> load $2"
    python -m scripts.db_load load "$2"
    echo "==> enrich all"
    python -m scripts.enrich all
    echo "Готово."
    ;;

  fix-prices)
    echo "ВНИМАНИЕ: операция ОДНОРАЗОВАЯ. Запуск дважды умножит цены"
    echo "ещё раз на 1000 и испортит данные."
    read -p "Умножить все gtk.price_thousand на 1000? [y/N] " ans
    [ "$ans" = "y" ] || { echo "Отменено."; exit 0; }
    python -m scripts.fix_prices
    ;;

  *)
    sed -n '2,16p' "$0"
    exit 1
    ;;
esac
