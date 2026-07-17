import re
from dataclasses import dataclass

from src.domain.iam.exceptions import (
    InvalidUsernameFormatException,
    InvalidUsernameLengthException,
)

USERNAME_MIN_LENGTH = 3
"""Минимальная длина имени пользователя (включительно)."""

USERNAME_MAX_LENGTH = 32
"""Максимальная длина имени пользователя (включительно)."""

USERNAME_PATTERN = r"[a-zA-Z0-9_-]+"
"""Регулярное выражение, допускающее буквы (a-z, A-Z), цифры (0-9),
дефис (-) и подчёркивание (_).
"""


@dataclass(frozen=True, slots=True)
class Username:
    """Объект-значение, представляющий имя пользователя.

    Инкапсулирует строковое представление имени пользователя и гарантирует
    соблюдение всех связанных с ним доменных инвариантов. Экземпляр класса
    всегда находится в корректном состоянии и может безопасно использоваться
    в других доменных сущностях и сервисах.

    Parameters
    ----------
    value : str
        Имя пользователя.

    Raises
    ------
    InvalidUsernameLengthException
        Если длина имени пользователя выходит за допустимые пределы.

    InvalidUsernameFormatException
        Если имя пользователя содержит недопустимые символы.

    Notes
    -----
    Имя пользователя должно удовлетворять следующим требованиям:

    - содержать от ``USERNAME_MIN_LENGTH`` до
      ``USERNAME_MAX_LENGTH`` символов включительно;
    - состоять только из латинских букв, цифр, символов ``-`` и ``_``;
    - быть неизменяемым после создания экземпляра.
    """

    value: str

    def __post_init__(self) -> None:
        if not USERNAME_MIN_LENGTH <= len(self.value) <= USERNAME_MAX_LENGTH:
            raise InvalidUsernameLengthException(
                "Username must contain from "
                f"{USERNAME_MIN_LENGTH} to "
                f"{USERNAME_MAX_LENGTH} characters."
            )

        if not re.fullmatch(USERNAME_PATTERN, self.value):
            raise InvalidUsernameFormatException(
                "Username may only contain letters (a-z, A-Z), digits (0-9), "
                "hyphens (-), and underscores (_)."
            )

    def __str__(self) -> str:
        return self.value
