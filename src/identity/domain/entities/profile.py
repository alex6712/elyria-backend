from datetime import datetime, timezone
from typing import Self
from uuid import UUID, uuid4

from src.identity.domain.value_objects import DisplayName, E2EECredentials
from src.shared.domain.entities import Auditable, Identifiable


class Profile(Identifiable[UUID], Auditable):
    """Доменная сущность профиля пользователя.

    Представляет профиль зарегистрированного пользователя системы
    и содержит информацию, необходимую для криптографических
    операций и отображения профиля.

    Экземпляр класса гарантирует соблюдение доменных инвариантов при
    создании и изменении своего состояния. При нарушении инвариантов
    возбуждаются специализированные доменные исключения.

    Attributes
    ----------
    id : UUID
        Уникальный идентификатор профиля.
    e2ee_credentials : E2EECredentials | None
        Данные профиля для сквозного шифрования.
    display_name : DisplayName
        Value object с отображаемым именем профиля.
    avatar_url : str | None
        URL изображения аватара профиля.
    created_at : datetime
        Дата и время создания профиля.
    updated_at : datetime | None
        Дата и время последнего изменения профиля.
    """

    def __init__(
        self,
        id: UUID,
        e2ee_credentials: E2EECredentials | None,
        display_name: DisplayName,
        avatar_url: str | None,
        created_at: datetime,
        updated_at: datetime | None,
    ) -> None:
        self.id = id
        self.e2ee_credentials = e2ee_credentials
        self.display_name = display_name
        self.avatar_url = avatar_url
        self.created_at = created_at
        self.updated_at = updated_at

    @classmethod
    def create(cls, display_name: DisplayName, avatar_url: str | None = None) -> Self:
        """Создать новый профиль со значениями по умолчанию.

        Parameters
        ----------
        display_name : DisplayName
            Value object с отображаемым именем профиля.
        avatar_url : str | None, optional
            URL изображения аватара. По умолчанию отсутствует.

        Returns
        -------
        Profile
            Новый экземпляр профиля без E2EE-credentials.

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
            created_at=datetime.now(timezone.utc),
            updated_at=None,
        )

    def change_display_name(self, new_display_name: DisplayName) -> None:
        """Изменить отображаемое имя профиля.

        Parameters
        ----------
        new_display_name : DisplayName
            Новое отображаемое имя профиля.
        """
        self.display_name = new_display_name
        self._touch()

    def rotate_e2ee_credentials(self, new_e2ee_credentials: E2EECredentials) -> None:
        """Заменить данные профиля для сквозного шифрования.

        Parameters
        ----------
        new_e2ee_credentials : E2EECredentials
            Новые E2EE-credentials профиля.
        """
        self.e2ee_credentials = new_e2ee_credentials
        self._touch()

    def has_e2ee_enabled(self) -> bool:
        """Проверить, установлены ли у профиля E2EE-credentials.

        Returns
        -------
        bool
            ``True``, если E2EE-credentials установлены,
            иначе ``False``.
        """
        return self.e2ee_credentials is not None

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Profile):
            return NotImplemented

        return self.id == other.id

    def __repr__(self) -> str:
        return f"Profile(id={self.id!r}, display_name={self.display_name!r}, created_at={self.created_at!r})"
