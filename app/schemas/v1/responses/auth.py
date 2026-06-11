from typing import Literal

from pydantic import Field

from app.schemas.v1.responses.standard import StandardResponse


class AccessTokenResponse(StandardResponse):
    """Модель ответа сервера с access-токеном.

    Возвращается после успешного входа в систему или обновления
    токенов. Access-токен должен передаваться в заголовке
    `Authorization: Bearer <token>` для доступа к защищённым
    эндпоинтам. Refresh-токен устанавливается в HttpOnly-cookie
    (см. `app.core.cookies.set_refresh_token_cookie`).

    Attributes
    ----------
    access_token : str
        JWT access-токен для авторизации запросов.
    token_type : Literal["bearer"]
        Тип токена (всегда `"bearer"`).
    expires_in : int
        Время жизни токена в секундах.
    """

    access_token: str = Field(
        description="Значение токена доступа",
        examples=[
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
            ".eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ"
            ".SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
        ],
    )
    token_type: Literal["bearer"] = Field(
        default="bearer",
        description="Тип токенов",
        examples=["bearer"],
    )
    expires_in: int = Field(
        description="Количество секунд, через которое токен будет считаться недействительным",
        examples=[900],
    )
