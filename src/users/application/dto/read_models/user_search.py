from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class UserSearchReadModel:
    """Строка read model поиска пользователей по имени пользователя.

    Денормализованное представление, объединяющее данные учётной
    записи (Identity) и профиля (Profile) для нечёткого поиска
    по ``username``. Обслуживается обработчиками проекций
    доменных событий (eventual consistency, пост-коммит).

    Attributes
    ----------
    identity_id : UUID
        Идентификатор учётной записи (Identity).
    profile_id : UUID
        Идентификатор профиля (Profile).
    username : str
        Имя пользователя (логин) учётной записи.
    display_name : str
        Отображаемое имя профиля.
    avatar_url : str | None
        URL изображения аватара профиля либо ``None``, если аватар
        не установлен.
    """

    identity_id: UUID
    profile_id: UUID
    username: str
    display_name: str
    avatar_url: str | None
