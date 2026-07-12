from datetime import datetime, timezone
from typing import Generic, TypeVar

_IdType = TypeVar("_IdType")


class BaseEntity(Generic[_IdType]):
    """Базовый класс доменной сущности.

    Предоставляет общую для всех сущностей идентичность по полю
    ``id`` и вспомогательный метод обновления временной метки
    последнего изменения.

    Parameters
    ----------
    id : _IdType
        Уникальный идентификатор сущности. Тип параметризуется
        конкретным наследником (например, ``Entity[UUID]``).
    updated_at : datetime | None
        Дата и время последнего изменения сущности.
    created_at : datetime
        Дата и время создания сущности.

    Notes
    -----
    Класс не содержит бизнес-логики и не должен использоваться
    напрямую - только как базовый класс для конкретных доменных
    сущностей. Регистрация доменных событий (``_domain_events``,
    ``pull_domain_events``) сюда сознательно не включена и будет
    рассмотрена отдельным ADR при переходе на event-driven подход.
    """

    def __init__(
        self, id: _IdType, updated_at: datetime | None, created_at: datetime
    ) -> None:
        self.id = id
        self.updated_at = updated_at
        self.created_at = created_at

    def _touch(self, at: datetime | None = None) -> None:
        """Обновить временную метку последнего изменения.

        Parameters
        ----------
        at : datetime | None, optional
            Момент времени для установки в качестве ``updated_at``.
            Если не передан, используется текущее время. Явная
            передача нужна там, где ``updated_at`` должен быть
            согласован с другим полем, изменяемым в том же вызове
            (например, ``revoked_at`` у ``Session``).
        """
        self.updated_at = at or datetime.now(timezone.utc)

    def __eq__(self, other: object) -> bool:
        """Сравнить сущности по идентификатору.

        Parameters
        ----------
        other : object
            Объект для сравнения.

        Returns
        -------
        bool
            ``True``, если ``other`` относится к тому же классу
            и имеет тот же ``id``, иначе ``False`` или
            ``NotImplemented``.
        """
        if not isinstance(other, self.__class__):
            return NotImplemented

        return self.id == other.id

    def __hash__(self) -> int:
        """Вычислить хэш сущности на основе идентификатора.

        Returns
        -------
        int
            Хэш-значение, основанное на ``id`` сущности.
        """
        return hash(self.id)
