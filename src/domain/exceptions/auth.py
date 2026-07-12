from src.domain.domain_context import DomainContext
from src.domain.exceptions.base import BaseDomainException


class AuthException(BaseDomainException):
    """Базовое исключение домена аутентификации.

    Attributes
    ----------
    context : Literal[DomainContext.AUTH]
        Bounded context предметной области, к которому относится
        данный тип исключения.

    Notes
    -----
    Все исключения категории аутентификации должны наследоваться
    от этого класса.
    """

    context = DomainContext.AUTH


class SessionNotFoundException(AuthException):
    """Сессия не найдена.

    Возникает при попытке обращения к несуществующей сессии
    пользователя.
    """

    pass


class SessionExpiredException(AuthException):
    """Срок действия сессии истёк.

    Возникает при попытке использования сессии, срок действия
    которой истёк.
    """

    pass
