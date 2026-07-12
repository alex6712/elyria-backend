from uuid import UUID

from src.domain.domain_context import DomainContext
from src.domain.exceptions.base import BaseDomainException


class UserException(BaseDomainException):
    """Базовое исключение домена пользователей.

    Attributes
    ----------
    context : Literal[DomainContext.USER]
        Bounded context предметной области, к которому относится
        данный тип исключения.

    Notes
    -----
    Все исключения категории пользователей должны наследоваться от этого класса.
    """

    context = DomainContext.USER


class InvalidUsernameLengthException(UserException):
    """Недопустимая длина имени пользователя.

    Возникает, если длина имени пользователя выходит за допустимые
    пределы, установленные правилами предметной области.
    """

    pass


class InvalidUsernameFormatException(UserException):
    """Недопустимый формат имени пользователя.

    Возникает, если имя пользователя содержит недопустимые символы
    (например, пробелы) или не соответствует разрешённому паттерну.
    """

    pass


class InvalidDisplayNameLengthException(UserException):
    """Недопустимая длина отображаемого имени.

    Возникает, если длина отображаемого имени выходит за допустимые
    пределы, установленные правилами предметной области.
    """

    pass


class InactiveUserException(UserException):
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


class EmptyPublicKeyException(UserException):
    """Пустой публичный ключ E2EE.

    Возникает, если публичный ключ, входящий в состав криптографических
    учётных данных пользователя, пуст.
    """

    pass


class EmptyEncryptedPrivateKeyException(UserException):
    """Пустой зашифрованный приватный ключ E2EE.

    Возникает, если зашифрованный приватный ключ, входящий в состав
    криптографических учётных данных пользователя, пуст.
    """

    pass


class EmptyPrivateKeyNonceException(UserException):
    """Пустой nonce приватного ключа E2EE.

    Возникает, если nonce, использованный при шифровании приватного
    ключа, пуст.
    """

    pass


class EmptyKdfSaltException(UserException):
    """Пустая соль KDF.

    Возникает, если соль, использованная функцией деривации ключа
    при защите приватного ключа пользователя, пуста.
    """

    pass


class EmptyKdfParamsException(UserException):
    """Пустые параметры KDF.

    Возникает, если параметры функции деривации ключа, использованной
    для защиты приватного ключа пользователя, не заданы.
    """

    pass
