from src.domain.domain_context import DomainContext


class BaseDomainException(Exception):
    """Базовое исключение для всех доменных исключений приложения.

    Parameters
    ----------
    *args : Any
        Стандартные аргументы исключения.
    detail : str | None
        Детальное сообщение об ошибке для пользователя или логирования.

    Attributes
    ----------
    context : ErrorCategory
        Bounded context предметной области, к которому относится
        данный тип исключения.

    Notes
    -----
    Все доменные исключения должны наследоваться от этого класса.
    Предоставляет единый интерфейс для передачи детализированных сообщений об ошибках.
    """

    context: DomainContext


class NotFoundException(BaseDomainException):
    """Базовое исключение для группировки всех исключений типа ``NotFound``.

    Notes
    -----
    Все исключения, связанные с логикой обработки ``NotFound``
    различных доменов должны наследоваться от этого исключения.
    """

    pass


class AlreadyExistsException(BaseDomainException):
    """Базовое исключение для группировки всех исключений типа ``AlreadyExists``.

    Notes
    -----
    Все исключения, связанные с логикой обработки ``AlreadyExists``
    различных доменов должны наследоваться от этого исключения.
    """

    pass
