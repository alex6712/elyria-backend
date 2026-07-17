from datetime import datetime, timezone
from typing import Self
from uuid import UUID, uuid4

from src.domain.shared.entities import Auditable, Identifiable
from src.domain.users.exceptions import InactiveUserException
from src.domain.users.value_objects import DisplayName, E2EECredentials


class Profile(Identifiable[UUID], Auditable):
    """Доменная сущность пользователя.

    Представляет зарегистрированного пользователя системы и содержит
    информацию, необходимую для криптографических операций и отображения
    профиля.

    Экземпляр класса гарантирует соблюдение доменных инвариантов при
    создании и изменении своего состояния. При нарушении инвариантов
    возбуждаются специализированные доменные исключения.

    Parameters
    ----------
    id : UUID
        Уникальный идентификатор пользователя.
    e2ee_credentials : E2EECredentials | None
        Данные пользователя для сквозного шифрования.
    display_name : DisplayName
        Value object с отображаемым именем пользователя.
    avatar_url : str | None
        URL изображения аватара пользователя.
    is_active : bool
        Признак активности учётной записи.
    created_at : datetime
        Дата и время регистрации пользователя.
    updated_at : datetime | None
        Дата и время последнего изменения данных пользователя.

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
        e2ee_credentials: E2EECredentials | None,
        display_name: DisplayName,
        avatar_url: str | None,
        is_active: bool,
        created_at: datetime,
        updated_at: datetime | None,
    ) -> None:
        self.id = id
        self.e2ee_credentials = e2ee_credentials
        self.display_name = display_name
        self.avatar_url = avatar_url
        self.is_active = is_active
        self.created_at = created_at
        self.updated_at = updated_at

    @classmethod
    def create(cls, display_name: DisplayName, avatar_url: str | None = None) -> Self:
        """Создать нового пользователя со значениями по умолчанию.

        Parameters
        ----------
        display_name : DisplayName
            Value object с отображаемым именем пользователя.
        avatar_url : str | None, optional
            URL изображения аватара. По умолчанию отсутствует.

        Returns
        -------
        Profile
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
            e2ee_credentials=None,
            display_name=display_name,
            avatar_url=avatar_url,
            is_active=True,
            updated_at=(now := datetime.now(timezone.utc)),
            created_at=now,
        )

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

    def rotate_e2ee_credentials(self, new_e2ee_credentials: E2EECredentials) -> None:
        """Заменить данные пользователя для сквозного шифрования.

        Parameters
        ----------
        new_e2ee_credentials : E2EECredentials
            Новые E2EE-credentials пользователя.

        Raises
        ------
        InactiveUserException
            Если пользователь деактивирован.
        """
        self._ensure_active()
        self.e2ee_credentials = new_e2ee_credentials
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
            ``True``, если ``other`` является ``Profile`` с тем же
            ``id``, иначе ``False`` или ``NotImplemented``.
        """
        if not isinstance(other, Profile):
            return NotImplemented

        return self.id == other.id

    def __repr__(self) -> str:
        """Построить отладочное строковое представление пользователя.

        Returns
        -------
        str
            Строка вида ``Profile(id=..., display_name=..., is_active=...)``.
        """
        return f"Profile(id={self.id!r}, display_name={self.display_name!r}, is_active={self.is_active!r})"
