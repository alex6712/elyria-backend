from uuid import UUID

from sqlalchemy import Column, ForeignKey
from sqlalchemy.types import Uuid


def ownership_columns() -> tuple[Column[UUID]]:
    """Создать колонки владения сущностью (ownership).

    Добавляет в таблицу ссылку на пользователя-владельца записи.
    Используется для сущностей, доступ к которым ограничен
    их создателем (например, приватные ресурсы).

    Каждый вызов возвращает новый объект `Column`, поскольку
    SQLAlchemy привязывает колонку к конкретной таблице при первом использовании.

    Returns
    -------
    tuple[Column[UUID]]
        Кортеж из одной колонки:

        - **owner_id** : `UUID`, foreign key, not null.
            Ссылается на `users.id`. Указывает пользователя,
            создавшего запись.
            При удалении пользователя связанные записи также удаляются
            за счёт `ON DELETE CASCADE`.
    """
    return (
        Column(
            "owner_id",
            Uuid(as_uuid=True),
            ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            comment="UUID пользователя-владельца ресурса",
        ),
    )
