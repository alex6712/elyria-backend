from typing import Annotated

from pydantic import BaseModel, BeforeValidator, Field

from src.users.domain.value_objects import DisplayName, Password, Username
from src.users.domain.value_objects.display_name import (
    DISPLAY_NAME_MAX_LENGTH,
    DISPLAY_NAME_MIN_LENGTH,
)
from src.users.domain.value_objects.password import PASSWORD_MIN_LENGTH
from src.users.domain.value_objects.username import (
    USERNAME_MAX_LENGTH,
    USERNAME_MIN_LENGTH,
)


class RegisterUserRequest(BaseModel):
    """Схема запроса регистрации с валидацией.

    Attributes
    ----------
    username : Username
        Логин пользователя.
    password : Password
        Пароль пользователя.
    display_name : DisplayName
        Отображаемое имя пользователя.
    """

    username: Annotated[Username, BeforeValidator(Username)] = Field(
        description=(
            f"Логин пользователя ({USERNAME_MIN_LENGTH}-{USERNAME_MAX_LENGTH}"
            + "символа, a-z, A-Z, 0-9, _, -)"
        ),
        examples=["john_doe", "user123"],
    )
    password: Annotated[Password, BeforeValidator(Password)] = Field(
        description=(
            f"Пароль (минимум {PASSWORD_MIN_LENGTH} символов, с цифрой,"
            + "спецсимволом, верхним и нижним регистром)"
        ),
        examples=["SecureP@ss123!"],
        json_schema_extra={"sensitive": True},
    )
    display_name: Annotated[DisplayName, BeforeValidator(DisplayName)] = Field(
        description=(
            f"Отображаемое имя пользователя ({DISPLAY_NAME_MIN_LENGTH}-"
            + f"{DISPLAY_NAME_MAX_LENGTH} символа, любые Unicode-символы)"
        ),
        examples=["Александр", "7", "一只非常重要的鸡", "🍆"],
    )
