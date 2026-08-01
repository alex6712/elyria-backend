from pydantic import BaseModel, ConfigDict, Field


class LogoutCommand(BaseModel):
    """Запрос на завершение пользовательской сессии.

    Содержит текущий access-токен пользователя. На его основе сервис
    определяет идентификатор сессии, отзывает access-токен и, если
    соответствующая сессия существует, помечает её как отозванную.

    Attributes
    ----------
    access_token : str
        Access-токен пользователя. Должен быть выдан ранее
        эндпоинтом аутентификации.
    """

    access_token: str = Field(description="Текущий access-токен пользователя")

    model_config = ConfigDict(frozen=True)
