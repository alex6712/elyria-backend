from dataclasses import dataclass

from src.users.domain.value_objects import Password, Username


@dataclass(frozen=True, slots=True)
class LoginCommand:
    """Команда аутентификации пользователя.

    Содержит данные, необходимые для входа в систему и создания
    новой пользовательской сессии.

    Attributes
    ----------
    username : Username
        Имя пользователя (логин).
    password : Password
        Пароль пользователя в открытом виде.
    """

    username: Username
    password: Password
