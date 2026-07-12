from datetime import datetime, timezone
from typing import Self
from uuid import UUID, uuid4

from src.domain.exceptions.user import InactiveUserException
from src.domain.value_objects import DisplayName, E2EECredentials, Username


class User:
    """Доменная сущность пользователя.

    Представляет зарегистрированного пользователя системы и содержит
    информацию, необходимую для аутентификации, криптографических
    операций и отображения профиля.

    Экземпляр класса гарантирует соблюдение доменных инвариантов при
    создании и изменении своего состояния. При нарушении инвариантов
    возбуждаются специализированные доменные исключения.

    Parameters
    ----------
    id : UUID
        Уникальный идентификатор пользователя.
    username : Username
        Value object с уникальным именем пользователя для входа в систему.
    password_hash : str
        Хэш пароля пользователя.
    e2ee_credentials : E2EECredentials | None
        Данные пользователя для сквозного шифрования.
    display_name : DisplayName
        Value object с отображаемым именем пользователя.
    avatar_url : str | None
        URL изображения аватара пользователя.
    is_active : bool
        Признак активности учётной записи.
    updated_at : datetime
        Дата и время последнего изменения данных пользователя.
    created_at : datetime
        Дата и время регистрации пользователя.

    Notes
    -----
    Согласно ADR-0004 (принят), все методы изменения состояния,
    кроме ``activate``, запрещены для пользователя с
    ``is_active=False``. При нарушении возбуждается
    ``InactiveUserException``.
    """

    def __init__(
        self,
        id: UUID,
        username: Username,
        password_hash: str,
        e2ee_credentials: E2EECredentials | None,
        display_name: DisplayName,
        avatar_url: str | None,
        is_active: bool,
        updated_at: datetime,
        created_at: datetime,
    ) -> None:
        self.id = id
        self.username = username
        self.password_hash = password_hash
        self.e2ee_credentials = e2ee_credentials
        self.display_name = display_name
        self.avatar_url = avatar_url
        self.is_active = is_active
        self.updated_at = updated_at
        self.created_at = created_at

    @classmethod
    def register(
        cls,
        username: Username,
        password_hash: str,
        display_name: DisplayName,
        avatar_url: str | None = None,
    ) -> Self:
        """Создать нового пользователя со значениями по умолчанию.

        Parameters
        ----------
        username : Username
            Value object с именем пользователя для входа в систему.
        password_hash : str
            Хэш пароля, полученный из Infrastructure Layer
            (Password Hash Service порт).
        display_name : DisplayName
            Value object с отображаемым именем пользователя.
        avatar_url : str | None, optional
            URL изображения аватара. По умолчанию отсутствует.

        Returns
        -------
        User
            Новый экземпляр пользователя в активном состоянии,
            без E2EE-credentials.

        Notes
        -----
        E2EE-credentials не выпускаются на этапе регистрации и
        устанавливаются отдельным сценарием использования через
        ``rotate_e2ee_credentials``.
        """
        return cls(
            id=uuid4(),
            username=username,
            password_hash=password_hash,
            e2ee_credentials=None,
            display_name=display_name,
            avatar_url=avatar_url,
            is_active=True,
            updated_at=(now := datetime.now(timezone.utc)),
            created_at=now,
        )

    def change_password(self, new_password_hash: str) -> None:
        """Изменить хэш пароля пользователя.

        Parameters
        ----------
        new_password_hash : str
            Новый хэш пароля, полученный из Infrastructure Layer.

        Raises
        ------
        InactiveUserException
            Если пользователь деактивирован.
        """
        self._ensure_active()
        self.password_hash = new_password_hash
        self._touch()

    def change_display_name(self, new_display_name: DisplayName) -> None:
        """Изменить отображаемое имя пользователя.

        Parameters
        ----------
        new_display_name : DisplayName
            Новое отображаемое имя.

        Raises
        ------
        InactiveUserException
            Если пользователь деактивирован.
        """
        self._ensure_active()
        self.display_name = new_display_name
        self._touch()

    def change_avatar(self, new_avatar_url: str | None) -> None:
        """Изменить URL аватара пользователя.

        Parameters
        ----------
        new_avatar_url : str | None
            Новый URL изображения аватара. ``None`` соответствует
            отсутствию аватара.

        Raises
        ------
        InactiveUserException
            Если пользователь деактивирован.
        """
        self._ensure_active()
        self.avatar_url = new_avatar_url
        self._touch()

    def change_username(self, new_username: Username) -> None:
        """Изменить имя пользователя для входа в систему.

        Parameters
        ----------
        new_username : Username
            Новое имя пользователя.

        Raises
        ------
        InactiveUserException
            Если пользователь деактивирован.

        Notes
        -----
        Уникальность ``username`` в рамках системы обеспечивается
        на уровне Application Layer (проверка через репозиторий),
        так как Entity не имеет доступа к данным других пользователей.
        """
        self._ensure_active()
        self.username = new_username
        self._touch()

    def rotate_e2ee_credentials(self, credentials: E2EECredentials) -> None:
        """Заменить данные пользователя для сквозного шифрования.

        Parameters
        ----------
        credentials : E2EECredentials
            Новые E2EE-credentials пользователя.

        Raises
        ------
        InactiveUserException
            Если пользователь деактивирован.
        """
        self._ensure_active()
        self.e2ee_credentials = credentials
        self._touch()

    def deactivate(self) -> None:
        """Деактивировать учётную запись пользователя.

        Notes
        -----
        Операция идемпотентна: повторный вызов для уже неактивного
        пользователя не изменяет состояние и не обновляет
        ``updated_at``.
        """
        if not self.is_active:
            return

        self.is_active = False
        self._touch()

    def activate(self) -> None:
        """Активировать учётную запись пользователя.

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
        self._touch()

    def has_e2ee_enabled(self) -> bool:
        """Проверить, установлены ли у пользователя E2EE-credentials.

        Returns
        -------
        bool
            ``True``, если E2EE-credentials установлены,
            иначе ``False``.
        """
        return self.e2ee_credentials is not None

    def _touch(self) -> None:
        """Обновить временную метку последнего изменения.

        Notes
        -----
        Вызывается всеми методами изменения состояния сущности
        для поддержания консистентности ``updated_at``.
        """
        self.updated_at = datetime.now(timezone.utc)

    def _ensure_active(self) -> None:
        """Проверить, что пользователь активен.

        Raises
        ------
        InactiveUserException
            Если ``is_active`` равен ``False``.

        Notes
        -----
        Реализует инвариант из ADR-0004: все методы изменения
        состояния, кроме ``activate``, запрещены для неактивного
        пользователя.
        """
        if not self.is_active:
            raise InactiveUserException(self.id)

    def __eq__(self, other: object) -> bool:
        """Сравнить пользователей по идентификатору.

        Parameters
        ----------
        other : object
            Объект для сравнения.

        Returns
        -------
        bool
            ``True``, если ``other`` является ``User`` с тем же
            ``id``, иначе ``False`` или ``NotImplemented``.
        """
        if not isinstance(other, User):
            return NotImplemented

        return self.id == other.id

    def __repr__(self) -> str:
        """Построить отладочное строковое представление пользователя.

        Returns
        -------
        str
            Строка вида ``User(id=..., username=..., is_active=...)``.
        """
        return f"User(id={self.id!r}, username={self.username!r}, is_active={self.is_active!r})"
