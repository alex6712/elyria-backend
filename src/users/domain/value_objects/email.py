import re
from dataclasses import dataclass
from typing import override

from src.users.domain.exceptions import InvalidEmailFormatError, InvalidEmailLengthError

EMAIL_MIN_LENGTH = 3
"""Минимальная длина email (включительно)."""

EMAIL_MAX_LENGTH = 254
"""Максимальная длина email (включительно).

Соответствует максимальной длине почтового адреса (mailbox),
заданной в RFC 5321.
"""

EMAIL_PATTERN = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
"""Регулярное выражение, допускающее классический формат почтового
адреса: локальная часть, символ ``@``, доменное имя с точкой
и доменом верхнего уровня не короче двух букв.
"""


@dataclass(frozen=True, slots=True)
class Email:
    """Объект-значение, представляющий адрес электронной почты.

    Инкапсулирует строковое представление почтового адреса
    и гарантирует соблюдение связанных с ним доменных инвариантов.
    Экземпляр класса всегда находится в корректном состоянии
    и может безопасно использоваться в других доменных сущностях
    и сервисах.

    Parameters
    ----------
    value : str
        Адрес электронной почты.

    Raises
    ------
    InvalidEmailLengthError
        Если длина email выходит за допустимые пределы.
    InvalidEmailFormatError
        Если email не соответствует допустимому формату.

    Notes
    -----
    Адрес приводится к нормализованной форме: удаляются ведущие
    и завершающие пробельные символы, все буквы переводятся
    в нижний регистр. Доменная часть адреса не нормализуется
    по правилам IDN (Punycode) - допускается только ASCII.
    """

    value: str

    def __post_init__(self) -> None:
        normalized = self.value.strip().lower()

        if not EMAIL_MIN_LENGTH <= len(normalized) <= EMAIL_MAX_LENGTH:
            raise InvalidEmailLengthError(
                "Email must contain from "
                + f"{EMAIL_MIN_LENGTH} to "
                + f"{EMAIL_MAX_LENGTH} characters."
            )

        if not EMAIL_PATTERN.fullmatch(normalized):
            raise InvalidEmailFormatError(
                "Email must match the pattern "
                + "local-part@domain.tld (e.g. user@example.com)."
            )

        object.__setattr__(self, "value", normalized)

    @override
    def __str__(self) -> str:
        return self.value
