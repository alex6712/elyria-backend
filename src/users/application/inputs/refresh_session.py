from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RefreshSessionInput:
    """Класс с входными данными для обновления пары access/refresh токенов.

    Содержит текущий refresh-токен пользователя.
    На основе этого токена сервис выпустит новую пару ключей доступа,
    аннулировав при этом предыдущую сессию во избежание replay-атак.

    Attributes
    ----------
    refresh_token : str
        Refresh-токен. Должен быть выдан ранее эндпоинтом
        аутентификации и не должен быть отозван.
    """

    refresh_token: str
