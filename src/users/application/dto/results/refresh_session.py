from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RefreshSessionResult:
    """Результат успешного обновления пары токенов.

    Содержит access и refresh токены, возвращаемые пользователю
    для дальнейшей авторизации.

    Attributes
    ----------
    access_token : str
        Access JWT для аутентификации запросов.
    refresh_token : str
        Refresh JWT для обновления сессии.
    """

    access_token: str
    refresh_token: str
