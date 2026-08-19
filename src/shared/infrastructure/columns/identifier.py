from typing import Literal
from uuid import UUID

from sqlalchemy import Column, text
from sqlalchemy.types import Uuid

_IDENTIFIER_GENERATION_MODE = Literal["random", "time-ordered"]
"""Допустимые режимы генерации UUID в колонке идентификатора."""


def identifier_column(mode: _IDENTIFIER_GENERATION_MODE) -> Column[UUID]:
    """Создать колонку идентификатора сущности (identifier).

    Добавляет в таблицу первичный ключ ``id`` типа `UUID`,
    соответствующий полю ``id`` примеси ``Identifiable`` из
    shared kernel. Значение генерируется на стороне БД выбранной
    функцией генерации, поэтому вставка записи без явного указания
    идентификатора корректно инициализирует агрегат.

    Каждый вызов возвращает новый объект `Column`, поскольку
    SQLAlchemy привязывает колонку к конкретной таблице при первом
    использовании.

    Parameters
    ----------
    mode : Literal["random", "time-ordered"]
        Режим генерации идентификатора:

        - **random** - случайный UUID через ``gen_random_uuid()``;
          подходит для большинства таблиц;
        - **time-ordered** - упорядоченный во времени UUID v7
          через ``uuidv7()``; снижает фрагментацию первичного
          ключа при высокой интенсивности вставок.

    Returns
    -------
    Column[UUID]
        Колонка ``id``: `UUID`, primary key. ``server_default``
        равен ``gen_random_uuid()`` либо ``uuidv7()`` в зависимости
        от переданного режима.

    Notes
    -----
    Функция ``uuidv7()`` доступна в PostgreSQL 18 и новее, а на
    более ранних версиях - при установленном расширении ``pg_uuidv7``.
    """
    match mode:
        case "random":
            default = text("gen_random_uuid()")
        case "time-ordered":
            default = text("uuidv7()")

    return Column(
        "id",
        Uuid(),
        primary_key=True,
        server_default=default,
        comment="Уникальный идентификатор записи",
    )
