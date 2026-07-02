USERNAME_PATTERN = r"^[a-zA-Z0-9_-]+$"
"""Регулярное выражение для проверки формата имени пользователя.

Разрешает латинские буквы (верхний и нижний регистр),
цифры, нижнее подчёркивание и дефис.
"""

USERNAME_MIN_LENGTH = 3
"""Минимальная длина имени пользователя в символах."""

USERNAME_MAX_LENGTH = 32
"""Максимальная длина имени пользователя в символах."""

if USERNAME_MIN_LENGTH > USERNAME_MAX_LENGTH:
    raise ValueError(
        f"Username min length ({USERNAME_MIN_LENGTH}) can't be larger than max length ({USERNAME_MAX_LENGTH})!"
    )

PASSWORD_MIN_LENGTH = 12
"""Минимальная длина пароля в символах."""

SPECIAL_CHAR_PATTERN = r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?]"
"""Регулярное выражение для проверки наличия специальных символов."""

DISPLAY_NAME_MIN_LENGTH = 1
"""Минимальная длина отображаемого имени пользователя в символах."""

DISPLAY_NAME_MAX_LENGTH = 32
"""Максимальная длина отображаемого имени пользователя в символах."""

if DISPLAY_NAME_MIN_LENGTH > DISPLAY_NAME_MAX_LENGTH:
    raise ValueError(
        f"Display name min length ({DISPLAY_NAME_MIN_LENGTH}) can't be larger than max length ({DISPLAY_NAME_MAX_LENGTH})!"
    )

DEFAULT_OFFSET = 0
"""Значение смещения по умолчанию для пагинации."""

MAX_OFFSET = 250
"""Максимально допустимое смещение для пагинации."""

if DEFAULT_OFFSET > MAX_OFFSET:
    raise ValueError(
        f"Default offset value ({DEFAULT_OFFSET}) can't be larger than max value ({MAX_OFFSET})!"
    )

DEFAULT_LIMIT = 10
"""Количество элементов на странице по умолчанию."""

MAX_LIMIT = 50
"""Максимально допустимое количество элементов на странице."""

if DEFAULT_LIMIT > MAX_LIMIT:
    raise ValueError(
        f"Default limit value ({DEFAULT_LIMIT}) can't be larger than max value ({MAX_LIMIT})!"
    )

HMAC_MIN_KEY_LENGTH = 32
"""Минимальная длина HMAC секретного ключа в байтах."""
