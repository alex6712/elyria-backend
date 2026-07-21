from datetime import UTC, datetime
from typing import Self
from uuid import UUID, uuid4

from src.identity.domain.value_objects import DisplayName
from src.shared.domain.entities import Auditable, Identifiable


class Profile(Identifiable[UUID], Auditable):
    """Доменная сущность профиля пользователя.

    Представляет профиль зарегистрированного пользователя системы
    и содержит информацию, необходимую для отображения профиля.

    Экземпляр класса гарантирует соблюдение доменных инвариантов при
    создании и изменении своего состояния. При нарушении инвариантов
    возбуждаются специализированные доменные исключения.

    Attributes
    ----------
    id : UUID
        Уникальный идентификатор профиля.
    identity_id : UUID
        Идентификатор учётной записи, к которой привязан профиль.
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
        identity_id: UUID,
        display_name: DisplayName,
        avatar_url: str | None,
        created_at: datetime,
        updated_at: datetime | None,
    ) -> None:
        self.id = id
        self.identity_id = identity_id
        self.display_name = display_name
        self.avatar_url = avatar_url
        self.created_at = created_at
        self.updated_at = updated_at

    @classmethod
    def create(
        cls, identity_id: UUID, display_name: DisplayName, avatar_url: str | None = None
    ) -> Self:
        """Создать новый профиль со значениями по умолчанию.

        Parameters
        ----------
        identity_id : UUID
            Идентификатор учётной записи, к которой привязывается профиль.
        display_name : DisplayName
            Value object с отображаемым именем профиля.
        avatar_url : str | None, optional
            URL изображения аватара. По умолчанию отсутствует.

        Returns
        -------
        Profile
            Новый экземпляр профиля.
        """
        return cls(
            id=uuid4(),
            identity_id=identity_id,
            display_name=display_name,
            avatar_url=avatar_url,
            created_at=datetime.now(UTC),
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

    def __repr__(self) -> str:
        return (
            "Profile("
            f"id={self.id!r}, "
            f"identity_id={self.identity_id!r}, "
            f"display_name={self.display_name!r}, "
            f"avatar_url={self.avatar_url!r}, "
            f"created_at={self.created_at!r}, "
            f"updated_at={self.updated_at!r})"
        )
