from dataclasses import dataclass
from urllib.parse import urlparse

from src.users.domain.exceptions import (
    InvalidAvatarUrlError,
    InvalidAvatarUrlLengthError,
)

AVATAR_URL_MIN_LENGTH = 1
"""Минимальная длина URL изображения аватара (включительно)."""

AVATAR_URL_MAX_LENGTH = 512
"""Максимальная длина URL изображения аватара (включительно)."""

AVATAR_URL_ALLOWED_SCHEMES = ("http", "https")
"""Схемы URL, разрешённые для изображений аватаров."""


@dataclass(frozen=True, slots=True)
class AvatarUrl:
    """Объект-значение, представляющий URL изображения аватара пользователя.

    Инкапсулирует строковое представление URL и гарантирует соблюдение
    связанных с ним доменных инвариантов. Экземпляр класса всегда находится
    в корректном состоянии и может безопасно использоваться в других
    доменных сущностях.

    Parameters
    ----------
    value : str
        URL изображения аватара.

    Raises
    ------
    InvalidAvatarUrlLengthError
        Если длина URL выходит за допустимые пределы.
    InvalidAvatarUrlError
        Если строка не является корректным абсолютным URL либо использует
        схему, отличную от ``http`` и ``https``.

    Notes
    -----
    URL должен удовлетворять следующим требованиям:

    - содержать от ``AVATAR_URL_MIN_LENGTH`` до ``AVATAR_URL_MAX_LENGTH``
      символов включительно;
    - быть абсолютным URL со схемой ``http`` или ``https`` и непустым
      сетевым идентификатором (хостом).
    """

    value: str

    def __post_init__(self) -> None:
        if not AVATAR_URL_MIN_LENGTH <= len(self.value) <= AVATAR_URL_MAX_LENGTH:
            raise InvalidAvatarUrlLengthError(
                "Avatar URL must contain from "
                + f"{AVATAR_URL_MIN_LENGTH} to "
                + f"{AVATAR_URL_MAX_LENGTH} characters."
            )

        parsed = urlparse(self.value)

        if parsed.scheme not in AVATAR_URL_ALLOWED_SCHEMES or not parsed.netloc:
            raise InvalidAvatarUrlError(
                "Avatar URL must be an absolute URL with "
                + " or ".join(AVATAR_URL_ALLOWED_SCHEMES)
                + " scheme."
            )
