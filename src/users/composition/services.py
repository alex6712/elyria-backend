from pathlib import Path

from redis.asyncio import Redis as AsyncRedis

from src.users.infrastructure.persistence import RedisTokenBlacklist
from src.users.infrastructure.security import (
    Argon2idPasswordHasher,
    HmacSha256TokenHasher,
    JwtTokenIssuer,
    JwtTokenVerifier,
    SignatureKeys,
    SignatureKeysProvider,
)


def build_password_hasher() -> Argon2idPasswordHasher:
    """Создать сервис хеширования паролей Argon2id.

    Returns
    -------
    Argon2idPasswordHasher
        Сервис хеширования и проверки паролей.
    """
    return Argon2idPasswordHasher()


def build_signature_keys_provider(
    *, public_key_path: Path, private_key_path: Path, private_signature_password: str
) -> SignatureKeysProvider:
    """Создать провайдер ключей подписи JWT.

    Провайдер загружает и расшифровывает пару ключей Ed25519
    из PEM-файлов при первом обращении к его методу
    ``get_signature_keys``.

    Parameters
    ----------
    public_key_path : Path
        Путь к PEM-файлу публичного ключа Ed25519.
    private_key_path : Path
        Путь к PEM-файлу приватного ключа Ed25519.
    private_signature_password : str
        Пароль для расшифровки приватного ключа.

    Returns
    -------
    SignatureKeysProvider
        Провайдер пары ключей Ed25519 (публичный и приватный).
    """
    return SignatureKeysProvider(
        public_key_path=public_key_path,
        private_key_path=private_key_path,
        private_signature_password=private_signature_password,
    )


def build_token_issuer(
    *, issuer: str, algorithm: str, signature_keys: SignatureKeys
) -> JwtTokenIssuer:
    """Создать сервис выпуска JWT-токенов.

    Parameters
    ----------
    issuer : str
        Издатель токена (значение утверждения ``iss``).
    algorithm : str
        Алгоритм подписи JWT (например, ``"EdDSA"``).
    signature_keys : SignatureKeys
        Пара ключей Ed25519 для подписи токенов.

    Returns
    -------
    JwtTokenIssuer
        Сервис подписи токенов приватным ключом Ed25519.
    """
    return JwtTokenIssuer(
        issuer=issuer, private_key=signature_keys.private, algorithm=algorithm
    )


def build_token_verifier(
    *, issuer: str, algorithm: str, signature_keys: SignatureKeys
) -> JwtTokenVerifier:
    """Создать сервис проверки JWT-токенов.

    Parameters
    ----------
    issuer : str
        Издатель токена (значение утверждения ``iss``).
    algorithm : str
        Алгоритм подписи JWT (например, ``"EdDSA"``).
    signature_keys : SignatureKeys
        Пара ключей Ed25519 для проверки подписи токенов.

    Returns
    -------
    JwtTokenVerifier
        Сервис проверки подписи токенов публичным ключом Ed25519.
    """
    return JwtTokenVerifier(
        issuer=issuer, public_key=signature_keys.public, algorithm=algorithm
    )


def build_token_hasher(*, hmac_secret_key: str) -> HmacSha256TokenHasher:
    """Создать сервис криптографического хеширования токенов.

    Parameters
    ----------
    hmac_secret_key : str
        Секретный ключ HMAC-SHA256 для хеширования токенов.

    Returns
    -------
    HmacSha256TokenHasher
        Сервис HMAC-SHA256 хеширования сырых токенов.
    """
    return HmacSha256TokenHasher(secret_key=hmac_secret_key.encode("utf-8"))


def build_token_blacklist(*, redis_client: AsyncRedis) -> RedisTokenBlacklist:
    """Создать хранилище отозванных токенов на основе Redis.

    Parameters
    ----------
    redis_client : AsyncRedis
        Асинхронный клиент Redis.

    Returns
    -------
    RedisTokenBlacklist
        Хранилище отозванных access-токенов.
    """
    return RedisTokenBlacklist(client=redis_client)
