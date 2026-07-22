from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RegisterUserResult(BaseModel):
    """Результат успешной регистрации пользователя.

    Содержит идентификатор созданной учётной записи, а также
    access и refresh токены для немедленной аутентификации.

    Attributes
    ----------
    user_id : UUID
        Идентификатор созданной учётной записи.
    access_token : str
        Access JWT для аутентификации запросов.
    refresh_token : str
        Refresh JWT для обновления сессии.
    """

    user_id: UUID = Field(description="Идентификатор созданной учётной записи")
    access_token: str = Field(description="Access JWT для авторизации")
    refresh_token: str = Field(description="Refresh JWT для обновления сессии")

    model_config = ConfigDict(frozen=True)
