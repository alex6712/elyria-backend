from uuid import UUID


class InvalidUsernameLengthException(Exception):
    """Недопустимая длина имени пользователя.

    Возникает, если длина имени пользователя выходит за допустимые
    пределы, установленные правилами предметной области.
    """

    pass


class InvalidUsernameFormatException(Exception):
    """Недопустимый формат имени пользователя.

    Возникает, если имя пользователя содержит недопустимые символы
    (например, пробелы) или не соответствует разрешённому паттерну.
    """

    pass


class SessionInvalidException(Exception):
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
