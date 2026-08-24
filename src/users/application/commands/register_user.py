from pydantic import BaseModel, ConfigDict, Field

from src.users.domain.value_objects import DisplayName, Password, Username


class RegisterUserCommand(BaseModel):
    """Запрос на регистрацию нового пользователя.

    Содержит данные, необходимые для создания учётной записи,
    профиля и первой пользовательской сессии.

    Attributes
    ----------
    username : Username
        Имя пользователя (логин).
    password : Password
        Пароль пользователя в открытом виде.
    display_name : DisplayName
        Отображаемое имя пользователя.
    """

    username: Username = Field(description="Уникальное имя пользователя (логин)")
    password: Password = Field(description="Пароль пользователя в открытом виде")
    display_name: DisplayName = Field(description="Отображаемое имя пользователя")

    model_config = ConfigDict(frozen=True)
