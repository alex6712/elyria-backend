from uuid import UUID

from src.domain.domain_context import DomainContext
from src.domain.exceptions._base import BaseDomainException


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


class SessionInvalidException(AuthException):
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


class TokenExpiredException(AuthException):
    """Срок действия токена истёк.

    Возникает при попытке верификации токена, срок действия
    которого истёк.
    """

    pass


class TokenSignatureInvalidException(AuthException):
    """Подпись токена недействительна.

    Возникает при попытке верификации токена, подпись которого
    не прошла проверку.
    """

    pass


class TokenInvalidException(AuthException):
    """Токен недействителен.

    Возникает при попытке верификации токена, в котором
    отсутствуют обязательные утверждения либо нарушен формат
    данных.

    Parameters
    ----------
    detail : str
        Причина недействительности токена.
    """

    def __init__(self, detail: str) -> None:
        super().__init__(detail)

        self.detail = detail
