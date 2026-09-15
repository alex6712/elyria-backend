from dataclasses import dataclass

from src.users.domain.value_objects import DisplayName, Email, Password, Username


@dataclass(frozen=True, slots=True)
class RegisterUserCommand:
    """Команда регистрации нового пользователя.

    Содержит данные, необходимые для создания учётной записи,
    профиля и первой пользовательской сессии.

    Attributes
    ----------
    username : Username
        Имя пользователя (логин).
    email : Email
        Адрес электронной почты пользователя.
    password : Password
        Пароль пользователя в открытом виде.
    display_name : DisplayName
        Отображаемое имя пользователя.
    """

    username: Username
    email: Email
    password: Password
    display_name: DisplayName
