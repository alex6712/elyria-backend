from sqlalchemy import Column, text
from sqlalchemy.types import Integer


def version_column() -> Column[int]:
    """Создать колонку версии агрегата для optimistic locking.

    Колонка ``version`` является технической характеристикой записи
    и не несёт бизнес-смысла: она служит для контроля конкурентного
    доступа к агрегату (см. ADR-0007). Репозиторий увеличивает
    версию на 1 при каждом успешном обновлении записи и сверяет её
    в ``WHERE``, что исключает потерю обновлений.

    Значение по умолчанию ``1`` задаётся на стороне БД, поэтому
    вставка записи без явного указания версии корректно инициализирует
    агрегат. Каждый вызов возвращает новый объект `Column`, поскольку
    SQLAlchemy привязывает колонку к конкретной таблице при первом
    использовании.

    Returns
    -------
    Column[int]
        Колонка ``version``: `Integer`, not null,
        ``server_default='1'``.
    """
    return Column(
        "version",
        Integer(),
        nullable=False,
        server_default=text("1"),
        comment="Версия агрегата для optimistic locking",
    )
