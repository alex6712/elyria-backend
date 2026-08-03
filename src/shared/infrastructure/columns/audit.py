from datetime import datetime

from sqlalchemy import Column, text
from sqlalchemy.types import DateTime


def audit_columns() -> tuple[Column[datetime], Column[datetime]]:
    """Создать колонки аудита записи (audit).

    Добавляет в таблицу временные метки создания и последнего
    изменения записи, соответствующие полям ``created_at`` и
    ``updated_at`` примеси ``Auditable`` из shared kernel.

    ``created_at`` устанавливается на стороне БД в момент вставки
    строки через ``TIMEZONE('UTC', NOW())``. ``updated_at`` не
    заполняется при вставке и остаётся ``NULL``, если запись не
    была изменена с момента создания; обновление метки выполняется
    на уровне приложения.

    Каждый вызов возвращает новые объекты `Column`, поскольку
    SQLAlchemy привязывает колонку к конкретной таблице при первом
    использовании.

    Returns
    -------
    tuple[Column[datetime], Column[datetime]]
        Кортеж из двух колонок:

        - **created_at** : `datetime` (timezone-aware), not null.
            Дата и время создания записи. Устанавливается на
            стороне БД через ``TIMEZONE('UTC', NOW())``.
        - **updated_at** : `datetime` (timezone-aware).
            Дата и время изменения записи. Может быть ``NULL``,
            если запись не была изменена с момента создания.
    """
    return (
        Column(
            "created_at",
            DateTime(timezone=True),
            nullable=False,
            server_default=text("TIMEZONE('UTC', NOW())"),
            comment="Дата и время создания записи",
        ),
        Column(
            "updated_at",
            DateTime(timezone=True),
            nullable=True,
            comment="Дата и время изменения записи",
        ),
    )
