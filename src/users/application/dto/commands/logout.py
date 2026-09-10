from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class LogoutCommand:
    """Команда завершения пользовательской сессии.

    Содержит текущий access-токен пользователя, на основе которого
    определяется идентификатор сессии для её отзыва.

    Attributes
    ----------
    access_token : str
        Access-токен пользователя. Должен быть выдан ранее
        эндпоинтом аутентификации.
    """

    access_token: str
