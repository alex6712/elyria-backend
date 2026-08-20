from pathlib import Path

from redis.asyncio import Redis as AsyncRedis

from src.shared.infrastructure.adapters.persistence import RedisTokenBlacklist
from src.shared.infrastructure.adapters.security import (
    JwtTokenVerifier,
    SignatureKeys,
    SignatureKeysProvider,
)


def build_signature_keys_provider(
    *, public_key_path: Path, private_key_path: Path, private_signature_password: str
) -> SignatureKeysProvider:
    """Создать провайдер ключей подписи JWT.

    Провайдер загружает и расшифровывает пару ключей Ed25519
    из PEM-файлов при первом обращении к его методу
    ``get_signature_keys``. Является общим ресурсом уровня
    Composition (ADR-0001, дополнение, п. 3): один экземпляр
    используется всеми bounded contexts.

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


def build_token_verifier(
    *, issuer: str, algorithm: str, signature_keys: SignatureKeys
) -> JwtTokenVerifier:
    """Создать сервис проверки JWT-токенов.

    Сервис проверяет подпись токена, срок его действия и наличие
    обязательных утверждений. Общий для всех bounded contexts:
    access-токены выпускаются контекстом Users, а потребляются
    любым контекстом приложения.

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


def build_token_blacklist(*, redis_client: AsyncRedis) -> RedisTokenBlacklist:
    """Создать хранилище отозванных токенов на основе Redis.

    Общее для всех bounded contexts хранилище отозванных access-токенов:
    токен отзывается контекстом Users (logout), а проверка статуса
    отзыва выполняется любым контекстом при потреблении токена.

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
