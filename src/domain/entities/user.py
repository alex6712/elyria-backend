from datetime import datetime
from typing import Any
from uuid import UUID

from src.domain.exceptions.user import InvalidUsernameLengthException


class User:
    """Доменная сущность пользователя.

    Представляет зарегистрированного пользователя системы и содержит
    информацию, необходимую для аутентификации, криптографических
    операций и отображения профиля.

    Экземпляр класса гарантирует соблюдение доменных инвариантов при
    создании и изменении своего состояния. При нарушении инвариантов
    возбуждаются специализированные доменные исключения.

    Parameters
    ----------
    id : UUID
        Уникальный идентификатор пользователя.
    username : str
        Уникальное имя пользователя, используемое для входа в систему.
        Должно содержать от 3 до 32 символов.
    password_hash : str
        Хэш пароля пользователя.
    public_key : bytes
        Публичный ключ пользователя.
    encrypted_private_key : bytes
        Закрытый ключ пользователя, зашифрованный мастер-ключом,
        производным от пользовательского пароля.
    private_key_nonce : bytes
        Nonce, использованный при шифровании закрытого ключа.
    kdf_salt : bytes
        Соль, использованная при выводе мастер-ключа.
    kdf_params : dict[str, Any]
        Параметры алгоритма KDF (например, Argon2id), необходимые
        для повторного получения мастер-ключа.
    display_name : str
        Отображаемое имя пользователя.
    created_at : datetime
        Дата и время регистрации пользователя.

    Raises
    ------
    InvalidUsernameLengthException
        Если длина имени пользователя выходит за допустимые пределы.
    """

    def __init__(
        self,
        id: UUID,
        username: str,
        password_hash: str,
        public_key: bytes,
        encrypted_private_key: bytes,
        private_key_nonce: bytes,
        kdf_salt: bytes,
        kdf_params: dict[str, Any],
        display_name: str,
        created_at: datetime,
    ) -> None:
        if not 3 <= len(username) <= 32:
            raise InvalidUsernameLengthException(
                "Username must contain from 3 to 32 characters."
            )

        self.id = id
        self.username = username
        self.password_hash = password_hash
        self.public_key = public_key
        self.encrypted_private_key = encrypted_private_key
        self.private_key_nonce = private_key_nonce
        self.kdf_salt = kdf_salt
        self.kdf_params = kdf_params
        self.display_name = display_name
        self.created_at = created_at
