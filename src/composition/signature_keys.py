from dataclasses import dataclass
from functools import lru_cache

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ec import (
    EllipticCurvePrivateKey,
    EllipticCurvePublicKey,
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
    private : EllipticCurvePrivateKey
        Приватный EC P-256 ключ, используемый для подписи JWT.
    public : EllipticCurvePublicKey
        Публичный EC P-256 ключ, используемый для проверки подписи JWT.
    """

    private: EllipticCurvePrivateKey
    public: EllipticCurvePublicKey


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

    if not isinstance(public_key, EllipticCurvePublicKey):
        raise ValueError(f"Expected EC public key, got {type(public_key).__name__}.")

    with PRIVATE_SIGNATURE_KEY_PATH.open("rb") as file:
        try:
            private_key = serialization.load_pem_private_key(
                file.read(),
                password=settings.PRIVATE_SIGNATURE_KEY_PASSWORD.encode("utf-8"),
            )
        except Exception as e:
            raise ValueError(f"Failed to decrypt private key: {e}") from e

    if not isinstance(private_key, EllipticCurvePrivateKey):
        raise ValueError(f"Expected EC private key, got {type(private_key).__name__}.")

    return SignatureKeys(private=private_key, public=public_key)
