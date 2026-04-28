"""Установить пароль пользователю.

Использование:
    python -m scripts.set_password <username> <new_password>
    python -m scripts.set_password admin SuperSecret123

Если пользователя нет — будет создан с правами админа.
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone

from sqlalchemy.orm import sessionmaker

from app.database import sync_engine
from app.models import User
from app.security import hash_password


def set_password(username: str, password: str) -> None:
    Session = sessionmaker(bind=sync_engine)
    session = Session()
    try:
        user = session.query(User).filter(User.username == username).one_or_none()
        if user is None:
            user = User(
                username=username,
                email=f"{username}@local",
                password_hash=hash_password(password),
                full_name=username,
                is_active=1,
                is_admin=1,
                created_at=datetime.now(timezone.utc),
            )
            session.add(user)
            session.commit()
            print(f"Создан админ '{username}'.")
            return

        user.password_hash = hash_password(password)
        user.updated_at = datetime.now(timezone.utc)
        session.commit()
        print(f"Пароль пользователя '{username}' обновлён.")
    finally:
        session.close()


def main() -> None:
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)
    set_password(sys.argv[1], sys.argv[2])


if __name__ == "__main__":
    main()
