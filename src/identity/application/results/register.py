from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RegisterResult(BaseModel):
    """Результат успешной регистрации пользователя.

    Содержит идентификатор созданной учётной записи, имя
    пользователя, отображаемое имя, а также access и refresh
    токены для немедленной аутентификации.

    Attributes
    ----------
    user_id : UUID
        Идентификатор созданной учётной записи.
    access_token : str
        JWT access-токен для аутентификации запросов.
    refresh_token : str
        Refresh-токен для обновления сессии.
    """

    user_id: UUID = Field(description="Идентификатор созданной учётной записи")
    access_token: str = Field(description="JWT access-токен")
    refresh_token: str = Field(description="Refresh-токен для обновления сессии")

    model_config = ConfigDict(frozen=True)
