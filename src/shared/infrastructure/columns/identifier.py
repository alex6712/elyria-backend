from uuid import UUID

from sqlalchemy import Column, text
from sqlalchemy.types import Uuid


def identifier_column() -> Column[UUID]:
    """Создать колонку идентификатора сущности (identifier).

    Добавляет в таблицу первичный ключ ``id`` типа `UUID`,
    соответствующий полю ``id`` примеси ``Identifiable`` из
    shared kernel. Значение генерируется на стороне БД через
    ``gen_random_uuid()``, поэтому вставка записи без явного
    указания идентификатора корректно инициализирует агрегат.

    Каждый вызов возвращает новый объект `Column`, поскольку
    SQLAlchemy привязывает колонку к конкретной таблице при первом
    использовании.

    Returns
    -------
    Column[UUID]
        Колонка ``id``: `UUID`, primary key,
        ``server_default='gen_random_uuid()'``.
    """
    return Column(
        "id",
        Uuid(),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        comment="Уникальный идентификатор записи",
    )
