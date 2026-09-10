from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from src.users.domain.value_objects import AvatarUrl, DisplayName


@dataclass(frozen=True, slots=True)
class GetProfileResult:
    """Результат успешного получения профиля пользователя.

    Содержит отображаемые данные профиля, возвращаемые клиенту.
    Технические атрибуты агрегата (версия для optimistic locking,
    идентификатор учётной записи) в результат не включаются.

    Attributes
    ----------
    id : UUID
        Уникальный идентификатор профиля.
    display_name : DisplayName
        Value object с отображаемым именем профиля.
    avatar_url : AvatarUrl | None
        URL изображения аватара профиля либо ``None``, если аватар
        не установлен.
    created_at : datetime
        Дата и время создания профиля.
    updated_at : datetime | None
        Дата и время последнего изменения профиля либо ``None``,
        если профиль не изменялся после создания.
    """

    id: UUID
    display_name: DisplayName
    avatar_url: AvatarUrl | None
    created_at: datetime
    updated_at: datetime | None
