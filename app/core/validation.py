import re
import unicodedata
from typing import Annotated

from pydantic import AfterValidator, StringConstraints

USERNAME_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+$")
"""Регулярное выражение для проверки формата имени пользователя.

Разрешает латинские буквы (верхний и нижний регистр),
цифры, нижнее подчёркивание и дефис.
"""

USERNAME_MIN_LENGTH = 3
"""Минимальная длина имени пользователя в символах."""

USERNAME_MAX_LENGTH = 32
"""Максимальная длина имени пользователя в символах."""

DISPLAY_NAME_MIN_LENGTH = 1
"""Минимальная длина отображаемого имени пользователя в символах."""

DISPLAY_NAME_MAX_LENGTH = 64
"""Максимальная длина отображаемого имени пользователя в символах."""

PASSWORD_MIN_LENGTH = 12
"""Минимальная длина пароля в символах."""

SPECIAL_CHAR_PATTERN = r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?]"
"""Регулярное выражение для проверки наличия специальных символов."""

ValidatedUsername = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=USERNAME_MIN_LENGTH,
        max_length=USERNAME_MAX_LENGTH,
        pattern=USERNAME_PATTERN,
    ),
]
"""Типизированная аннотация для поля имени пользователя с автоматической валидацией.

Используется в Pydantic-схемах для автоматической проверки имени
пользователя при десериализации данных.
"""


def validate_password_strength(value: str) -> str:
    """Проверяет пароль на соответствие требованиям безопасности.

    Валидация включает следующие проверки:
    - Отсутствие пробелов и любых пробельных символов;
    - Наличие символов верхнего регистра (A-Z);
    - Наличие символов нижнего регистра (a-z);
    - Наличие цифр (0-9);
    - Наличие специальных символов (!@#$%^&* и т.д.).

    Parameters
    ----------
    value : str
        Пароль в виде строки для проверки.

    Returns
    -------
    str
        Пароль, прошедший все проверки.

    Raises
    ------
    ValueError
        Если пароль не соответствует одному из требований безопасности.
    """
    if any(char.isspace() for char in value):
        raise ValueError("Password must not contain whitespace characters.")

    if not re.search(r"[A-Z]", value):
        raise ValueError("Password must contain at least one uppercase letter.")

    if not re.search(r"[a-z]", value):
        raise ValueError("Password must contain at least one lowercase letter.")

    if not re.search(r"[0-9]", value):
        raise ValueError("Password must contain at least one digit.")

    if not re.search(SPECIAL_CHAR_PATTERN, value):
        raise ValueError("Password must contain at least one special character.")

    return value


def normalize_unicode_nfc(value: str) -> str:
    """Нормализует строку в каноническую форму NFC.

    Unicode допускает несколько различных представлений одного и того же
    визуального символа. Например, символ "é" может быть записан как
    единый кодовый пункт (U+00E9) либо как последовательность символов
    "e" (U+0065) и комбинируемого акцента (U+0301).

    Нормализация в форму NFC приводит эквивалентные представления к
    единому каноническому виду, что обеспечивает корректное сравнение,
    хранение и подсчёт длины строк.

    Parameters
    ----------
    value : str
        Строка для нормализации.

    Returns
    -------
    str
        Нормализованная строка в форме NFC.
    """
    return unicodedata.normalize("NFC", value)


ValidatedPassword = Annotated[
    str,
    StringConstraints(min_length=PASSWORD_MIN_LENGTH),
    AfterValidator(validate_password_strength),
]
"""Типизированная аннотация для поля пароля с автоматической валидацией.

Используется в Pydantic-схемах для автоматической проверки пароля
при десериализации данных.
"""

ValidatedDisplayName = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=DISPLAY_NAME_MIN_LENGTH,
        max_length=DISPLAY_NAME_MAX_LENGTH,
    ),
    AfterValidator(normalize_unicode_nfc),
]
"""Типизированная аннотация для поля отображаемого имени пользователя с автоматической валидацией.

Используется в Pydantic-схемах для автоматической проверки и нормализации
отображаемого имени пользователя при десериализации данных.
"""
