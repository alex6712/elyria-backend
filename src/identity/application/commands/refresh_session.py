from pydantic import BaseModel, ConfigDict, Field


class RefreshSessionCommand(BaseModel):
    """Запрос на обновление пары access/refresh токенов.

    Содержит текущий refresh-токен пользователя.
    На основе этого токена сервис выпустит новую пару ключей доступа,
    аннулировав при этом предыдущую сессию во избежание replay-атак.

    Attributes
    ----------
    refresh_token : str
        Refresh-токен. Должен быть выдан ранее эндпоинтом
        аутентификации и не должен быть отозван.
    """

    refresh_token: str = Field(description="Текущий refresh-токен пользователя")

    model_config = ConfigDict(frozen=True)
