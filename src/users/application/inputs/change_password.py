from dataclasses import dataclass

from src.users.domain.value_objects import Password


@dataclass(frozen=True, slots=True)
class ChangePasswordInput:
    """Класс с входными данными для смены пароля пользователя.

    Содержит данные, необходимые для смены пароля: access-токен
    пользователя, текущий пароль для подтверждения операции
    и новый пароль.

    Attributes
    ----------
    access_token : str
        Access JWT пользователя, выполняющего операцию.
    current_password : Password
        Текущий пароль пользователя (value object).
    new_password : Password
        Новый пароль пользователя (value object).
    """

    access_token: str
    current_password: Password
    new_password: Password
