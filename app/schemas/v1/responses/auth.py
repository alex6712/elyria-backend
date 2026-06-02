from pydantic import Field

from app.schemas.dto.base import BaseDTO
from app.schemas.v1.responses.standard import StandardResponse


class LoggedInUserDTO(BaseDTO):
    """Публичное DTO пользователя в ответе на вход в систему.

    Содержит минимальный набор полей, необходимых фронтенду
    для инициализации пользовательской сессии сразу после
    успешной аутентификации. Чувствительные данные
    (например, `password_hash`) намеренно не включаются.

    Attributes
    ----------
    id : str
        UUID пользователя в строковом представлении -
        используется как стабильный идентификатор в
        клиентских сторах.
    username : str
        Логин пользователя, отображённый в интерфейсе.
    """

    id: str = Field(
        description="UUID идентификатор пользователя в строковом представлении.",
        examples=["3fa85f64-5717-4562-b3fc-2c963f66afa6"],
    )
    username: str = Field(
        description="Логин пользователя.",
        examples=["john_doe"],
    )


class LoginResponse(StandardResponse):
    """Модель ответа сервера на успешный вход в систему.

    Тело ответа намеренно не содержит JWT - access- и
    refresh-токены передаются в HttpOnly-cookie
    (см. `app.core.cookies.set_auth_cookies`).
    Фронтенд использует `user` для первичной инициализации
    состояния после успешной аутентификации.

    Attributes
    ----------
    user : LoggedInUserDTO
        DTO вошедшего пользователя.
    """

    user: LoggedInUserDTO = Field(
        description="DTO вошедшего пользователя.",
    )
