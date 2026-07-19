from dataclasses import dataclass
from typing import Any

from src.identity.domain.exceptions import (
    EmptyEncryptedPrivateKeyException,
    EmptyKdfParamsException,
    EmptyKdfSaltException,
    EmptyPrivateKeyNonceException,
    EmptyPublicKeyException,
)


@dataclass(frozen=True, slots=True)
class E2EECredentials:
    """Объект-значение, представляющий криптографические учётные данные E2EE.

    Инкапсулирует материал, необходимый для end-to-end шифрования: публичный
    ключ, зашифрованный приватный ключ и параметры KDF, использованные для
    получения ключа шифрования приватного ключа. Экземпляр класса всегда
    находится в корректном состоянии и может безопасно использоваться в
    других доменных сущностях и сервисах.

    Parameters
    ----------
    public_key : bytes
        Публичный ключ в бинарном представлении.
    encrypted_private_key : bytes
        Приватный ключ, зашифрованный на ключе, производном от KDF.
    private_key_nonce : bytes
        Nonce, использованный при шифровании приватного ключа.
    kdf_salt : bytes
        Соль, использованная функцией деривации ключа.
    kdf_params : dict[str, Any]
        Параметры функции деривации ключа.

    Raises
    ------
    EmptyPublicKeyException
        Если публичный ключ пуст.
    EmptyEncryptedPrivateKeyException
        Если зашифрованный приватный ключ пуст.
    EmptyPrivateKeyNonceException
        Если nonce приватного ключа пуст.
    EmptyKdfSaltException
        Если соль KDF пуста.
    EmptyKdfParamsException
        Если параметры KDF не заданы.

    Notes
    -----
    Домен намеренно не осведомлён о конкретном алгоритме KDF (Argon2id,
    scrypt и т.п.) или конкретной эллиптической кривой (X25519 и т.п.) -
    эти детали принадлежат инфраструктурному слою. Поэтому проверяются
    только структурные инварианты (непустота полей), но не их длина,
    формат или состав ``kdf_params``.

    Экземпляр класса неизменяем после создания.
    """

    public_key: bytes
    encrypted_private_key: bytes
    private_key_nonce: bytes
    kdf_salt: bytes
    kdf_params: dict[str, Any]

    def __post_init__(self) -> None:
        if not self.public_key:
            raise EmptyPublicKeyException("Public key must not be empty.")

        if not self.encrypted_private_key:
            raise EmptyEncryptedPrivateKeyException(
                "Encrypted private key must not be empty."
            )

        if not self.private_key_nonce:
            raise EmptyPrivateKeyNonceException("Private key nonce must not be empty.")

        if not self.kdf_salt:
            raise EmptyKdfSaltException("KDF salt must not be empty.")

        if not self.kdf_params:
            raise EmptyKdfParamsException("KDF params must not be empty.")
