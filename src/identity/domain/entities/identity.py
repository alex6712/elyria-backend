from datetime import UTC, datetime
from typing import Self
from uuid import UUID, uuid4

from src.identity.domain.exceptions import InactiveUserError
from src.identity.domain.value_objects import Username
from src.shared.domain.entities import Auditable, Identifiable, Versioned


class Identity(Identifiable[UUID], Auditable, Versioned):
    """Доменная сущность учётной записи пользователя.

    Представляет собой учётную запись (identity) пользователя
    в системе. Содержит идентификатор, имя пользователя, хэш пароля,
    статус активности, версию для optimistic locking и метки аудита,
    наследуя функциональность от ``Identifiable``, ``Auditable``
    и ``Versioned``.

    Attributes
    ----------
    id : UUID
        Уникальный идентификатор учётной записи.
    username : Username
        Имя пользователя (value object).
    password_hash : str
        Хэш пароля пользователя.
    is_active : bool
        Флаг активности учётной записи.
    version : int
        Версия агрегата для optimistic locking. Увеличивается на 1
        при каждом успешном сохранении изменений через репозиторий.
    created_at : datetime
        Дата и время создания учётной записи.
    updated_at : datetime | None
        Дата и время последнего изменения учётной записи.
        ``None``, если изменений не было.
    """

    def __init__(
        self,
        id: UUID,
        username: Username,
        password_hash: str,
        is_active: bool,
        version: int,
        created_at: datetime,
        updated_at: datetime | None,
    ) -> None:
        self.id = id
        self.username = username
        self.password_hash = password_hash
        self.is_active = is_active
        self.version = version
        self.created_at = created_at
        self.updated_at = updated_at

    @classmethod
    def register(cls, username: Username, password_hash: str) -> Self:
        """Зарегистрировать новую учётную запись.

        Создаёт учётную запись с уникальным идентификатором,
        переданным именем пользователя и хэшем пароля. Учётная
        запись создаётся активной.

        Parameters
        ----------
        username : Username
            Имя пользователя.
        password_hash : str
            Хэш пароля пользователя.

        Returns
        -------
        Self
            Новая учётная запись.
        """
        return cls(
            id=uuid4(),
            username=username,
            password_hash=password_hash,
            is_active=True,
            version=1,
            created_at=datetime.now(UTC),
            updated_at=None,
        )

    def change_password_hash(
        self, new_password_hash: str, *, at: datetime | None = None
    ) -> None:
        """Изменить хэш пароля пользователя.

        Parameters
        ----------
        new_password_hash : str
            Новый хэш пароля, полученный из Infrastructure Layer.
        at : datetime | None, optional
            Временная метка изменения хеша пароля.

        Raises
        ------
        InactiveUserError
            Если пользователь деактивирован.
        """
        self._ensure_active()
        self.password_hash = new_password_hash
        self._touch(at)

    def deactivate(self, at: datetime | None = None) -> None:
        """Деактивировать учётную запись пользователя.

        Parameters
        ----------
        at : datetime | None, optional
            Временная метка деактивации учётной записи пользователя.

        Notes
        -----
        Операция идемпотентна: повторный вызов для уже неактивного
        пользователя не изменяет состояние и не обновляет
        ``updated_at``.
        """
        if not self.is_active:
            return

        self.is_active = False
        self._touch(at)

    def activate(self, at: datetime | None = None) -> None:
        """Активировать учётную запись пользователя.

        Parameters
        ----------
        at : datetime | None, optional
            Временная метка активации учётной записи пользователя.

        Notes
        -----
        Единственный метод изменения состояния, доступный для
        неактивного пользователя (см. ADR-0004). Операция
        идемпотентна: повторный вызов для уже активного пользователя
        не изменяет состояние и не обновляет ``updated_at``.
        """
        if self.is_active:
            return

        self.is_active = True
        self._touch(at)

    def _ensure_active(self) -> None:
        """Проверить, что пользователь активен.

        Raises
        ------
        InactiveUserError
            Если ``is_active`` равен ``False``.

        Notes
        -----
        Реализует инвариант из ADR-0004: все методы изменения
        состояния, кроме ``activate``, запрещены для неактивного
        пользователя.
        """
        if not self.is_active:
            raise InactiveUserError(self.id)

    def __repr__(self) -> str:
        return (
            "Identity("
            f"id={self.id!r}, "
            f"username={self.username!r}, "
            f"is_active={self.is_active!r}, "
            f"version={self.version!r}, "
            f"created_at={self.created_at!r}, "
            f"updated_at={self.updated_at!r})"
        )
