from typing import Annotated

from pydantic import UUID4, Field, StringConstraints

from src.shared.presentation.http.schemas import BaseJsonModel, StandardResponse
from src.users.domain.value_objects.display_name import (
    DISPLAY_NAME_MAX_LENGTH,
    DISPLAY_NAME_MIN_LENGTH,
)
from src.users.domain.value_objects.password import (
    PASSWORD_MAX_LENGTH,
    PASSWORD_MIN_LENGTH,
)
from src.users.domain.value_objects.username import (
    USERNAME_MAX_LENGTH,
    USERNAME_MIN_LENGTH,
    USERNAME_PATTERN,
)
from src.users.presentation.http.v1.schemas._helpers import length_description


class RegisterUserRequest(BaseJsonModel):
    """Схема запроса регистрации.

    Attributes
    ----------
    username : str
        Строковое представление логина пользователя.
    password : str
        Строковое представление пароля пользователя.
    display_name : str
        Строковое представление отображаемого имени пользователя.

    Notes
    -----
    Для логина пользователя (username) и отображаемого имени пользователя (display_name)
    ведущие и завершающие пробельные символы удаляются перед обработкой.

    See Also
    --------
    :class:`BaseJsonModel`
        Базовая модель данных, сериализуемых в JSON.
    """

    username: Annotated[
        str,
        StringConstraints(
            strip_whitespace=True,
            min_length=USERNAME_MIN_LENGTH,
            max_length=USERNAME_MAX_LENGTH,
            pattern=USERNAME_PATTERN,
        ),
    ] = Field(
        description=(
            "Логин пользователя ("
            + f"{length_description(USERNAME_MIN_LENGTH, USERNAME_MAX_LENGTH)}, "
            + "латинские строчные и заглавные, цифры, дефис и нижнее подчёркивание"
            + ")."
        ),
        examples=["john_doe", "user123", "ThisIsNotAUsername"],
    )
    password: Annotated[
        str,
        StringConstraints(
            min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH
        ),
    ] = Field(
        description=(
            "Пароль ("
            + f"{length_description(PASSWORD_MIN_LENGTH, PASSWORD_MAX_LENGTH)}, "
            + "любые символы в соответствии с NIST SP 800-63B"
            + ")."
        ),
        examples=["НадёжныйP@ssword123!"],
        json_schema_extra={"sensitive": True},
    )
    display_name: Annotated[
        str,
        StringConstraints(
            strip_whitespace=True,
            min_length=DISPLAY_NAME_MIN_LENGTH,
            max_length=DISPLAY_NAME_MAX_LENGTH,
        ),
    ] = Field(
        description=(
            "Отображаемое имя пользователя ("
            + f"{
                length_description(DISPLAY_NAME_MIN_LENGTH, DISPLAY_NAME_MAX_LENGTH)
            }, "
            + "любые Unicode-символы"
            + ")."
        ),
        examples=["Александр", "7", "一只非常重要的鸡", "🍆"],
    )


class RegisterUserResponse(StandardResponse):
    """Модель ответа на успешную регистрацию пользователя.

    Содержит идентификатор созданной учётной записи и access-токен
    для немедленной аутентификации. Refresh-токен передаётся клиенту
    не в теле ответа, а в HttpOnly-cookie, поэтому в модели отсутствует.

    Attributes
    ----------
    user_id : UUID
        Публичный идентификатор созданной учётной записи.
    access_token : str
        Access JWT для аутентификации последующих запросов.

    See Also
    --------
    :class:`StandardResponse`
        Базовая модель ответа с полями ``code`` и ``detail``.
    """

    user_id: UUID4 = Field(
        description="Публичный идентификатор пользователя (UUID четвёртой версии).",
        examples=[
            "d522c9bb-d9d9-4075-bb01-fc358b4f5048",
            "0e60ab98-9cf2-43ac-b19c-021a98ed0f95",
        ],
    )
    access_token: str = Field(
        description="Токен доступа, предоставляемый пользователю.",
        examples=[
            "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9."
            + "eyJzdWIiOiIxMjNlNDU2Ny1lODliLTEyZDMtYTQ1Ni00MjY2MTQxNzQwMDAiLCJpc3M"
            + "iOiJodHRwczovL2FwaS5lbHlyaWEucnUiLCJpYXQiOjE3NTY4MTI4MDAsImV4cCI6MT"
            + "c1NjgxNjQwMCwianRpIjoiMTIzZTQ1NjctZTg5Yi0xMmQzLWE0NTYtNDI2NjE0MTc0M"
            + "DAxIiwic2lkIjoiMTIzZTQ1NjctZTg5Yi0xMmQzLWE0NTYtNDI2NjE0MTc0MDAyIn0."
            + "5FbYeYiWaFIh18XlVGRMIbcQBrh3PJlU0wdmpnOAShy"
            + "TuqukDqMV8bfz2_8SMdbnQz0gvst56uz2Tq6l-RMDBw",
        ],
    )
