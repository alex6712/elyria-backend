from datetime import datetime
from uuid import UUID

from sqlalchemy import Column, text
from sqlalchemy.types import DateTime, Uuid


def base_columns() -> tuple[Column[UUID], Column[datetime], Column[datetime]]:
    """Создать базовые колонки, общие для всех таблиц приложения.

    Каждый вызов возвращает новые объекты `Column`, что необходимо,
    так как SQLAlchemy привязывает колонку к конкретной таблице
    при её первом использовании.

    Returns
    -------
    tuple[Column[UUID], Column[datetime], Column[datetime]]
        Кортеж из трёх колонок:

        - **id** : `UUID`, primary key.
            Генерируется на стороне БД через `gen_random_uuid()`.
        - **updated_at** : `datetime` (timezone-aware)
            Временная метка последнего обновления записи. Может быть
            ``NULL``, если запись не была изменена с момента создания.
        - **created_at** : `datetime` (timezone-aware), not null.
            Устанавливается на стороне БД в момент вставки строки
            через `TIMEZONE('UTC', NOW())`.
    """
    return (
        Column(
            "id",
            Uuid(),
            primary_key=True,
            server_default=text("gen_random_uuid()"),
            comment="Уникальный идентификатор записи",
        ),
        Column(
            "updated_at",
            DateTime(timezone=True),
            nullable=True,
            comment="Дата и время изменения записи",
        ),
        Column(
            "created_at",
            DateTime(timezone=True),
            nullable=False,
            server_default=text("TIMEZONE('UTC', NOW())"),
            comment="Дата и время создания записи",
        ),
    )
