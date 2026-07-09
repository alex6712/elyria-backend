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
