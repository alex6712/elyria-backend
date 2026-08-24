from dataclasses import dataclass

from src.users.domain.value_objects import DisplayName, Password, Username


@dataclass(frozen=True, slots=True)
class RegisterUserInput:
    """Класс с входными данными для регистрации нового пользователя.

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

    username: Username
    password: Password
    display_name: DisplayName
