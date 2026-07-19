import unicodedata
from dataclasses import dataclass

from src.identity.domain.exceptions import InvalidDisplayNameLengthException

DISPLAY_NAME_MIN_LENGTH = 1
"""Минимальная длина отображаемого имени (включительно)."""

DISPLAY_NAME_MAX_LENGTH = 32
"""Максимальная длина отображаемого имени (включительно)."""


@dataclass(frozen=True, slots=True)
class DisplayName:
    """Объект-значение, представляющий отображаемое имя пользователя.

    Инкапсулирует строковое представление отображаемого имени
    и гарантирует соблюдение ограничений по длине, а также
    приводит строку к нормализованной форме Unicode (NFC).

    Parameters
    ----------
    value : str
        Отображаемое имя пользователя.

    Raises
    ------
    InvalidDisplayNameLengthException
        Если длина имени выходит за пределы от
        ``DISPLAY_NAME_MIN_LENGTH`` до ``DISPLAY_NAME_MAX_LENGTH``
        символов включительно.
    """

    value: str

    def __post_init__(self) -> None:
        normalized = unicodedata.normalize("NFC", self.value)

        if self.value != normalized:
            object.__setattr__(self, "value", normalized)

        if not DISPLAY_NAME_MIN_LENGTH <= len(self.value) <= DISPLAY_NAME_MAX_LENGTH:
            raise InvalidDisplayNameLengthException(
                "Display name must contain from "
                f"{DISPLAY_NAME_MIN_LENGTH} to "
                f"{DISPLAY_NAME_MAX_LENGTH} characters."
            )

    def __str__(self) -> str:
        return self.value
