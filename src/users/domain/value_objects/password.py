import re
from collections.abc import Callable
from dataclasses import dataclass
from typing import override

from src.users.domain.exceptions import InvalidPasswordError, PasswordRuleViolation

PASSWORD_MIN_LENGTH = 12
"""Минимальная длина пароля (включительно)."""

SPECIAL_CHARACTERS = "!@#$%^&*()_+-=[]{};':\"\\|,.<>/?"
"""Регулярное выражение, допускающее специальные символы пароля."""

_UPPERCASE_RE = re.compile(r"[A-Z]")
_LOWERCASE_RE = re.compile(r"[a-z]")
_DIGIT_RE = re.compile(r"\d")
_SPECIAL_RE = re.compile(f"[{re.escape(SPECIAL_CHARACTERS)}]")

_PASSWORD_MASK = "********"
"""Маска, подставляемая вместо пароля в строковых представлениях."""


@dataclass(frozen=True, slots=True)
class _PasswordRule:
    """Спецификация правила парольной политики.

    Описывает одно правило парольной политики: идентификатор,
    описание и функцию проверки.

    Parameters
    ----------
    id : str
        Уникальный идентификатор правила.
    description : str
        Человекочитаемое описание правила на английском языке.
    check : Callable[[str], bool]
        Функция проверки пароля, возвращающая ``True`` при
        соблюдении правила.
    """

    id: str
    description: str
    check: Callable[[str], bool]


_PASSWORD_RULES: tuple[_PasswordRule, ...] = (
    _PasswordRule(
        id="min_length",
        description=(
            f"Password must be at least {PASSWORD_MIN_LENGTH} characters long."
        ),
        check=lambda v: len(v) >= PASSWORD_MIN_LENGTH,
    ),
    _PasswordRule(
        id="no_space_characters",
        description="Password must not contain whitespace characters.",
        check=lambda v: not any(char.isspace() for char in v),
    ),
    _PasswordRule(
        id="require_uppercase",
        description="Password must contain at least one uppercase letter.",
        check=lambda v: bool(_UPPERCASE_RE.search(v)),
    ),
    _PasswordRule(
        id="require_lowercase",
        description="Password must contain at least one lowercase letter.",
        check=lambda v: bool(_LOWERCASE_RE.search(v)),
    ),
    _PasswordRule(
        id="require_digit",
        description="Password must contain at least one digit.",
        check=lambda v: bool(_DIGIT_RE.search(v)),
    ),
    _PasswordRule(
        id="require_special_character",
        description="Password must contain at least one special character.",
        check=lambda v: bool(_SPECIAL_RE.search(v)),
    ),
)
"""Единый источник правды для парольной политики: используется
при валидации пароля в ``Password``, чтобы исключить
дублирование и рассинхронизацию правил.
"""


@dataclass(frozen=True, slots=True)
class Password:
    """Объект-значение, представляющий пароль пользователя.

    Инкапсулирует строковое представление пароля в открытом виде
    и гарантирует соблюдение всех требований парольной политики
    (``_PASSWORD_RULES``). Экземпляр класса всегда находится
    в корректном состоянии и может безопасно использоваться
    в доменных сущностях и сервисах.

    Parameters
    ----------
    value : str
        Пароль в открытом виде.

    Raises
    ------
    InvalidPasswordError
        Если пароль нарушает одно или несколько правил
        парольной политики. Исключение содержит все нарушенные
        правила, чтобы пользователь мог исправить их за один раз.

    Notes
    -----
    Объект хранит пароль в открытом виде в памяти. Он не должен
    логироваться, сериализовываться в открытом виде или
    храниться дольше, чем это требуется для хеширования.
    Строковые представления (``__str__``, ``__repr__``) маскируют
    пароль; доступ к открытому значению - только через ``reveal()``.
    """

    _value: str

    def __post_init__(self) -> None:
        failed_rules = tuple(
            rule for rule in _PASSWORD_RULES if not rule.check(self._value)
        )

        if failed_rules:
            raise InvalidPasswordError(
                tuple(
                    PasswordRuleViolation(rule.id, rule.description)
                    for rule in failed_rules
                )
            )

    def reveal(self) -> str:
        """Раскрыть пароль в открытом виде.

        Returns
        -------
        str
            Пароль в открытом виде.

        Notes
        -----
        Единственный способ получить пароль в открытом виде.
        Вызывать только там, где пароль действительно необходим
        (например, при хешировании). Результат не должен
        логироваться или попадать в строковые представления.
        """
        return self._value

    @override
    def __str__(self) -> str:
        """Возвращает маску вместо пароля.

        Returns
        -------
        str
            Строка-маска, не содержащая пароль в открытом виде.

        Notes
        -----
        Метод намеренно не возвращает пароль: строковые
        представления объекта могут попадать в логи, трассировки
        и функции подстановки в строку. Для доступа к открытому
        значению используйте ``reveal()``.
        """
        return _PASSWORD_MASK

    @override
    def __repr__(self) -> str:
        """Возвращает строковое представление объекта без пароля.

        Returns
        -------
        str
            Строковое представление вида ``Password('********')``.

        Notes
        -----
        Пароль не включается в представление, чтобы исключить
        его попадание в логи и дампы объектов.
        """
        return f"Password({_PASSWORD_MASK!r})"
