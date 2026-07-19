class SessionNotFoundException(Exception):
    """Сессия не найдена.

    Возникает при попытке обращения к несуществующей сессии
    пользователя.
    """

    pass


class SessionExpiredException(Exception):
    """Срок действия сессии истёк.

    Возникает при попытке использования сессии, срок действия
    которой истёк.
    """

    pass


class TokenExpiredException(Exception):
    """Срок действия токена истёк.

    Возникает при попытке верификации токена, срок действия
    которого истёк.
    """

    pass


class TokenSignatureInvalidException(Exception):
    """Подпись токена недействительна.

    Возникает при попытке верификации токена, подпись которого
    не прошла проверку.
    """

    pass


class TokenInvalidException(Exception):
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
