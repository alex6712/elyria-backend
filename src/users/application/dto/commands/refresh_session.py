from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RefreshSessionCommand:
    """Команда обновления пары access/refresh токенов.

    Содержит текущий refresh-токен пользователя, на основе которого
    выпускается новая пара ключей доступа с аннулированием предыдущей
    сессии.

    Attributes
    ----------
    refresh_token : str
        Refresh-токен. Должен быть выдан ранее эндпоинтом
        аутентификации и не должен быть отозван.
    """

    refresh_token: str
