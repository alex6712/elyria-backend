from dataclasses import dataclass
from functools import lru_cache

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

from src.composition.paths import (
    PRIVATE_SIGNATURE_KEY_PATH,
    PUBLIC_SIGNATURE_KEY_PATH,
)
from src.composition.settings import get_settings


@dataclass(frozen=True, slots=True)
class SignatureKeys:
    """Пара ключей подписи JWT.

    Attributes
    ----------
    private : Ed25519PrivateKey
        Приватный ключ Ed25519, используемый для подписи JWT.
    public : Ed25519PublicKey
        Публичный ключ Ed25519, используемый для проверки подписи JWT.
    """

    private: Ed25519PrivateKey
    public: Ed25519PublicKey


@lru_cache
def get_signature_keys() -> SignatureKeys:
    """Загружает и кеширует пару ключей подписи JWT.

    Выполняет следующие действия:

    1. Загружает публичный ключ из ``PUBLIC_SIGNATURE_KEY_PATH``.
    2. Загружает и дешифрует приватный ключ из
       ``PRIVATE_SIGNATURE_KEY_PATH``.
    3. Проверяет типы загруженных ключей.
    4. Возвращает неизменяемый объект ``SignatureKeys``.

    Повторные вызовы не выполняют чтение файлов благодаря
    ``functools.lru_cache``.

    Returns
    -------
    SignatureKeys
        Пара ключей подписи JWT.

    Raises
    ------
    FileNotFoundError
        Если один из файлов ключей отсутствует.
    ValueError
        Если не удалось дешифровать приватный ключ либо загруженный
        ключ имеет неверный тип.
    """
    settings = get_settings()

    with PUBLIC_SIGNATURE_KEY_PATH.open("rb") as file:
        public_key = serialization.load_pem_public_key(file.read())

    if not isinstance(public_key, Ed25519PublicKey):
        raise ValueError(
            f"Expected Ed25519 public key, got {type(public_key).__name__}."
        )

    with PRIVATE_SIGNATURE_KEY_PATH.open("rb") as file:
        try:
            private_key = serialization.load_pem_private_key(
                file.read(),
                password=settings.PRIVATE_SIGNATURE_KEY_PASSWORD.encode("utf-8"),
            )
        except Exception as e:
            raise ValueError(f"Failed to decrypt private key: {e}") from e

    if not isinstance(private_key, Ed25519PrivateKey):
        raise ValueError(
            f"Expected Ed25519 private key, got {type(private_key).__name__}."
        )

    return SignatureKeys(private=private_key, public=public_key)
