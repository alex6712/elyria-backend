from pydantic import BaseModel, ConfigDict, Field

from src.users.domain.value_objects import Password, Username


class LoginCommand(BaseModel):
    """Запрос на вход в систему.

    Содержит данные, необходимые для аутентификации пользователя,
    и создания новой пользовательской сессии.

    Attributes
    ----------
    username : str
        Имя пользователя (логин).
    password : str
        Пароль пользователя в виде объект-значения.
    """

    username: Username = Field(description="Уникальное имя пользователя (логин)")
    password: Password = Field(description="Пароль пользователя в открытом виде")

    model_config = ConfigDict(frozen=True)
