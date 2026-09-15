from datetime import UTC, datetime
from typing import Self, override
from uuid import UUID, uuid4

from src.shared.domain.mixins import Auditable, Identifiable, Versioned
from src.users.domain.exceptions import InactiveUserError
from src.users.domain.value_objects import Email, Username


class Identity(Identifiable[UUID], Auditable, Versioned):
    """Доменная сущность учётной записи пользователя.

    Представляет собой учётную запись (identity) пользователя
    в системе. Содержит идентификатор, имя пользователя, адрес
    электронной почты, хэш пароля, статус активности, признак
    подтверждения email, версию для optimistic locking и метки
    аудита, наследуя функциональность от ``Identifiable``,
    ``Auditable`` и ``Versioned``.

    Attributes
    ----------
    id : UUID
        Уникальный идентификатор учётной записи.
    username : Username
        Имя пользователя (value object).
    email : Email
        Адрес электронной почты (value object).
    email_verified : bool
        Признак подтверждения адреса электронной почты.
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
        email: Email,
        email_verified: bool,
        password_hash: str,
        is_active: bool,
        version: int,
        created_at: datetime,
        updated_at: datetime | None,
    ) -> None:
        self.id = id
        self.username = username
        self.email = email
        self.email_verified = email_verified
        self.password_hash = password_hash
        self.is_active = is_active
        self.version = version
        self.created_at = created_at
        self.updated_at = updated_at

    @classmethod
    def register(cls, username: Username, password_hash: str, email: Email) -> Self:
        """Зарегистрировать новую учётную запись.

        Создаёт учётную запись с уникальным идентификатором,
        переданным именем пользователя, адресом электронной почты
        и хэшем пароля. Учётная запись создаётся активной, а её
        email - неподтверждённым (``email_verified=False``).

        Parameters
        ----------
        username : Username
            Имя пользователя.
        password_hash : str
            Хэш пароля пользователя.
        email : Email
            Адрес электронной почты пользователя.

        Returns
        -------
        Self
            Новая учётная запись.
        """
        return cls(
            id=uuid4(),
            username=username,
            email=email,
            email_verified=False,
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

    def verify_email(self, at: datetime | None = None) -> None:
        """Подтвердить адрес электронной почты пользователя.

        Устанавливает признак ``email_verified`` в значение ``True``
        и обновляет метку ``updated_at``.

        Parameters
        ----------
        at : datetime | None, optional
            Временная метка подтверждения адреса электронной почты.

        Raises
        ------
        InactiveUserError
            Если пользователь деактивирован.

        Notes
        -----
        Операция идемпотентна: повторный вызов для уже подтвердившего
        email пользователя не изменяет состояние и не обновляет
        ``updated_at``.
        """
        if self.email_verified:
            return

        self._ensure_active()
        self.email_verified = True
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

    @override
    def __repr__(self) -> str:
        return (
            "Identity("
            f"id={self.id!r}, "
            f"username={self.username!r}, "
            f"email={self.email!r}, "
            f"email_verified={self.email_verified!r}, "
            f"is_active={self.is_active!r}, "
            f"version={self.version!r}, "
            f"created_at={self.created_at!r}, "
            f"updated_at={self.updated_at!r})"
        )
