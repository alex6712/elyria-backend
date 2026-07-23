from pydantic import BaseModel, ConfigDict, Field


class RefreshResult(BaseModel):
    """Результат успешного продления сессии.

    Содержит access и refresh токены, возвращаемые пользователю
    для дальнейшей авторизации.

    Attributes
    ----------
    access_token : str
        Access JWT для аутентификации запросов.
    refresh_token : str
        Refresh JWT для обновления сессии.
    """

    access_token: str = Field(description="Access JWT для авторизации")
    refresh_token: str = Field(description="Refresh JWT для обновления сессии")

    model_config = ConfigDict(frozen=True)
