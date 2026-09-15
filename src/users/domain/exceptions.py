from datetime import datetime
from uuid import UUID


class InvalidAvatarUrlLengthError(Exception):
    """Недопустимая длина URL изображения аватара.

    Возникает, если длина URL изображения аватара выходит
    за допустимые пределы, установленные правилами предметной области.
    """

    pass


class InvalidAvatarUrlError(Exception):
    """Недопустимый формат URL изображения аватара.

    Возникает, если строка не является корректным URL либо использует
    схему, не разрешённую для изображений аватаров (разрешены только
    ``http`` и ``https``).
    """

    pass


class InvalidDisplayNameLengthError(Exception):
    """Недопустимая длина отображаемого имени.

    Возникает, если длина отображаемого имени выходит за допустимые
    пределы, установленные правилами предметной области.
    """

    pass


class InvalidPasswordLengthError(Exception):
    """Недопустимая длина пароля пользователя.

    Возникает, если длина пароля пользователя выходит за допустимые
    пределы, установленные правилами предметной области.
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


class InvalidEmailLengthError(Exception):
    """Недопустимая длина адреса электронной почты.

    Возникает, если длина email выходит за допустимые пределы,
    установленные правилами предметной области.
    """

    pass


class InvalidEmailFormatError(Exception):
    """Недопустимый формат адреса электронной почты.

    Возникает, если email не соответствует разрешённому формату
    (``local-part@domain.tld``).
    """

    pass


class InactiveUserError(Exception):
    """Исключение, сигнализирующее о попытке операции, требующей
    активной учётной записи, для неактивного пользователя.

    Возникает при попытке изменить состояние неактивного
    пользователя (ADR-0004) либо аутентифицировать его (вход
    в систему или обновление сессии).

    Parameters
    ----------
    user_id : UUID
        Идентификатор пользователя, для которого была предпринята
        запрещённая операция.
    """

    def __init__(self, user_id: UUID) -> None:
        super().__init__(f"User {user_id} is inactive")

        self.user_id = user_id


class SessionRevokedError(Exception):
    """Исключение, сигнализирующее о попытке изменить состояние
    отозванной сессии.

    Возникает при попытке выполнить операцию, требующую валидной
    сессии, для сессии, которая была принудительно завершена
    (logout или административное отозвание).

    Parameters
    ----------
    session_id : UUID
        Идентификатор сессии, для которой была предпринята
        запрещённая операция.
    """

    def __init__(self, session_id: UUID) -> None:
        super().__init__(f"Session {session_id} is revoked and cannot be modified")

        self.session_id = session_id


class SessionExpiredError(Exception):
    """Исключение, сигнализирующее о попытке изменить состояние
    истёкшей сессии.

    Возникает, когда срок действия сессии истёк, хотя переданный
    refresh-токен может оставаться действительным: срок жизни сессии
    независим от срока жизни токена.

    Parameters
    ----------
    session_id : UUID
        Идентификатор сессии, для которой была предпринята
        запрещённая операция.
    """

    def __init__(self, session_id: UUID) -> None:
        super().__init__(f"Session {session_id} is expired and cannot be modified")

        self.session_id = session_id


class InvalidSessionExpirationError(Exception):
    """Попытка выпуска сессии с уже истёкшим сроком действия.

    Возникает в ``Session.issue()``, если ``expires_at`` не находится
    строго в будущем относительно момента выпуска ``now``: сессия
    не может быть выдана уже истёкшей (ADR-0005).

    Parameters
    ----------
    expires_at : datetime
        Переданный момент истечения срока действия сессии.
    now : datetime
        Момент выпуска сессии.
    """

    def __init__(self, expires_at: datetime, now: datetime) -> None:
        super().__init__(
            "Session cannot be issued: expires_at must be later than now. "
            + f"expires_at={expires_at}, now={now}"
        )

        self.expires_at = expires_at
        self.now = now


class UsernameAlreadyExistsError(Exception):
    """Исключение при попытке создать пользователя с существующим username.

    Возникает, если указанное имя пользователя уже занято
    другой учётной записью. Содержит сообщение с указанием
    конфликтующего имени пользователя.
    """

    pass


class EmailAlreadyExistsError(Exception):
    """Исключение при попытке создать пользователя с существующим email.

    Возникает, если указанный адрес электронной почты уже занят
    другой учётной записью. Уникальность email гарантируется
    ограничением базы данных ``uq_identities_email_lower``.
    """

    pass


class SessionSecretAlreadyExistsError(Exception):
    """Исключение при попытке создать сессию с существующим секретом.

    Возникает, если указанный ``session_secret`` уже занят
    другой сессией. Уникальность секрета гарантируется
    ограничением базы данных ``uq_sessions_session_secret``.
    """

    pass
