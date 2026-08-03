from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class PasswordRuleViolation:
    """Нарушенное правило парольной политики.

    Parameters
    ----------
    rule_id : str
        Идентификатор нарушенного правила.
    message : str
        Человекочитаемое описание требования, которое не выполнено.
    """

    rule_id: str
    message: str


class InvalidDisplayNameLengthError(Exception):
    """Недопустимая длина отображаемого имени.

    Возникает, если длина отображаемого имени выходит за допустимые
    пределы, установленные правилами предметной области.
    """

    pass


class EmptyPublicKeyError(Exception):
    """Пустой публичный ключ E2EE.

    Возникает, если публичный ключ, входящий в состав криптографических
    учётных данных пользователя, пуст.
    """

    pass


class EmptyEncryptedPrivateKeyError(Exception):
    """Пустой зашифрованный приватный ключ E2EE.

    Возникает, если зашифрованный приватный ключ, входящий в состав
    криптографических учётных данных пользователя, пуст.
    """

    pass


class EmptyPrivateKeyNonceError(Exception):
    """Пустой nonce приватного ключа E2EE.

    Возникает, если nonce, использованный при шифровании приватного
    ключа, пуст.
    """

    pass


class EmptyKdfSaltError(Exception):
    """Пустая соль KDF.

    Возникает, если соль, использованная функцией деривации ключа
    при защите приватного ключа пользователя, пуста.
    """

    pass


class EmptyKdfParamsError(Exception):
    """Пустые параметры KDF.

    Возникает, если параметры функции деривации ключа, использованной
    для защиты приватного ключа пользователя, не заданы.
    """

    pass


class InvalidUsernameLengthError(Exception):
    """Недопустимая длина имени пользователя.

    Возникает, если длина имени пользователя выходит за допустимые
    пределы, установленные правилами предметной области.
    """

    pass


class InvalidUsernameFormatError(Exception):
    """Недопустимый формат имени пользователя.

    Возникает, если имя пользователя содержит недопустимые символы
    (например, пробелы) или не соответствует разрешённому паттерну.
    """

    pass


class InactiveUserError(Exception):
    """Исключение, сигнализирующее о попытке изменить состояние
    неактивного пользователя.

    Parameters
    ----------
    user_id : UUID
        Идентификатор пользователя, для которого была предпринята
        запрещённая операция.
    """

    def __init__(self, user_id: UUID) -> None:
        super().__init__(f"User {user_id} is inactive and cannot be modified")

        self.user_id = user_id


class SessionInvalidError(Exception):
    """Исключение, сигнализирующее о попытке изменить состояние
    отозванной или истёкшей сессии.

    Parameters
    ----------
    session_id : UUID
        Идентификатор сессии, для которой была предпринята
        запрещённая операция.
    """

    def __init__(self, session_id: UUID) -> None:
        super().__init__(
            f"Session {session_id} is revoked or expired and cannot be modified"
        )

        self.session_id = session_id


class UsernameAlreadyExistsError(Exception):
    """Исключение при попытке создать пользователя с существующим username.

    Возникает, если указанное имя пользователя уже занято
    другой учётной записью. Содержит сообщение с указанием
    конфликтующего имени пользователя.
    """

    pass


class InvalidPasswordError(Exception):
    """Исключение, сигнализирующее о несоответствии пароля
    парольной политике.

    Агрегирует все нарушенные правила парольной политики, чтобы
    пользователь мог исправить все нарушения за один раз.

    Parameters
    ----------
    violations : tuple[PasswordRuleViolation, ...]
        Нарушенные правила в виде объектов ``PasswordRuleViolation``.

    Attributes
    ----------
    violations : tuple[PasswordRuleViolation, ...]
        Нарушенные правила в виде объектов ``PasswordRuleViolation``.
    rule_ids : tuple[str, ...]
        Идентификаторы нарушенных правил в порядке их появления.
    """

    def __init__(self, violations: tuple[PasswordRuleViolation, ...]) -> None:
        super().__init__(
            "Password does not meet security requirements: "
            + ", ".join(violation.rule_id for violation in violations)
            + "."
        )

        self.violations = violations
        self.rule_ids = tuple(violation.rule_id for violation in violations)
