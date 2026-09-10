from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class RegisterUserResult:
    """Результат успешной регистрации пользователя.

    Содержит идентификаторы созданных учётной записи и профиля,
    а также access и refresh токены для немедленной аутентификации.

    Attributes
    ----------
    identity_id : UUID
        Уникальный идентификатор созданной учётной записи.
    profile_id : UUID
        Уникальный идентификатор созданного профиля.
    access_token : str
        Access JWT для аутентификации запросов.
    refresh_token : str
        Refresh JWT для обновления сессии.
    """

    identity_id: UUID
    profile_id: UUID
    access_token: str
    refresh_token: str
