from pydantic import BaseModel, ConfigDict, Field

from src.identity.domain.value_objects.username import (
    USERNAME_MAX_LENGTH,
    USERNAME_MIN_LENGTH,
    USERNAME_PATTERN,
)


class LoginCommand(BaseModel):
    """Запрос на вход в систему.

    Содержит данные, необходимые для аутентификации пользователя,
    и создания новой пользовательской сессии.

    Attributes
    ----------
    username : str
        Имя пользователя (логин). Длина от
        ``USERNAME_MIN_LENGTH`` до ``USERNAME_MAX_LENGTH`` символов.
        Допускаются латинские буквы, цифры, дефис и подчёркивание.
    password : str
        Пароль пользователя в открытом виде.
        Минимальная длина определяется требованиями политики
        безопасности приложения.
    """

    username: str = Field(
        description="Уникальное имя пользователя (логин)",
        examples=["john_doe"],
        pattern=USERNAME_PATTERN,
        min_length=USERNAME_MIN_LENGTH,
        max_length=USERNAME_MAX_LENGTH,
    )
    password: str = Field(
        description="Пароль пользователя в открытом виде",
        examples=["secureP@ss1"],
        min_length=12,
    )

    model_config = ConfigDict(frozen=True)
