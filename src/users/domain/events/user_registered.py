from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class UserRegisteredEvent:
    """Доменное событие регистрации новой учётной записи.

    Публикуется после успешного создания учётной записи, профиля
    и начальной сессии. Содержит данные, необходимые подписчикам
    для поддержания производных представлений (read model),
    например read model поиска по имени пользователя.

    Parameters
    ----------
    identity_id : UUID
        Идентификатор созданной учётной записи (Identity).
    profile_id : UUID
        Идентификатор созданного профиля (Profile).
    username : str
        Имя пользователя (логин) учётной записи.
    display_name : str
        Отображаемое имя профиля.
    avatar_url : str | None
        URL изображения аватара профиля либо ``None``, если аватар
        не был установлен при регистрации.
    """

    identity_id: UUID
    profile_id: UUID
    username: str
    display_name: str
    avatar_url: str | None
