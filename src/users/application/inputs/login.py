from dataclasses import dataclass

from src.users.domain.value_objects import Password, Username


@dataclass(frozen=True, slots=True)
class LoginInput:
    """Класс с входными данными для входа в систему.

    Содержит данные, необходимые для аутентификации пользователя,
    и создания новой пользовательской сессии.

    Attributes
    ----------
    username : str
        Имя пользователя (логин).
    password : str
        Пароль пользователя в виде объект-значения.
    """

    username: Username
    password: Password
