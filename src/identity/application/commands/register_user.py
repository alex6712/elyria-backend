from pydantic import BaseModel, ConfigDict, Field

from src.identity.domain.value_objects.display_name import (
    DISPLAY_NAME_MAX_LENGTH,
    DISPLAY_NAME_MIN_LENGTH,
)
from src.identity.domain.value_objects.username import (
    USERNAME_MAX_LENGTH,
    USERNAME_MIN_LENGTH,
    USERNAME_PATTERN,
)


class RegisterUserCommand(BaseModel):
    """Запрос на регистрацию нового пользователя.

    Содержит данные, необходимые для создания учётной записи,
    профиля и первой пользовательской сессии.

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
    display_name : str
        Отображаемое имя пользователя. Длина от
        ``DISPLAY_NAME_MIN_LENGTH`` до
        ``DISPLAY_NAME_MAX_LENGTH`` символов.
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
    display_name: str = Field(
        description="Отображаемое имя пользователя",
        examples=["John Doe"],
        min_length=DISPLAY_NAME_MIN_LENGTH,
        max_length=DISPLAY_NAME_MAX_LENGTH,
    )

    model_config = ConfigDict(frozen=True)
