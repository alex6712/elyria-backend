from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class ProfileChangedEvent:
    """Доменное событие изменения профиля пользователя.

    Публикуется после успешного изменения отображаемого имени или
    аватара профиля. Содержит актуальные значения полей, влияющих
    на производные представления (read model) профиля, например
    read model поиска по имени пользователя.

    Parameters
    ----------
    identity_id : UUID
        Идентификатор учётной записи (Identity), чей профиль изменён.
    profile_id : UUID
        Идентификатор изменённого профиля (Profile).
    username : str
        Имя пользователя (логин) учётной записи.
    display_name : str
        Актуальное отображаемое имя профиля после изменения.
    avatar_url : str | None
        Актуальный URL изображения аватара профиля либо ``None``,
        если аватар не установлен (в том числе удалён).
    """

    identity_id: UUID
    profile_id: UUID
    username: str
    display_name: str
    avatar_url: str | None
