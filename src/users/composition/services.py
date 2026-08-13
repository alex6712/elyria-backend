from functools import lru_cache
from pathlib import Path
from typing import Literal

from httpx import AsyncClient
from redis.asyncio import Redis as AsyncRedis

from src.users.infrastructure.adapters.persistence import RedisTokenBlacklist
from src.users.infrastructure.adapters.security import (
    Argon2idPasswordHasher,
    HibpCompromisedPasswordChecker,
    HmacSha256TokenHasher,
    JwtTokenIssuer,
    JwtTokenVerifier,
    SignatureKeys,
    SignatureKeysProvider,
)
from src.users.presentation.http.services import AuthCookiesProvider

_HIBP_TIMEOUT_SECONDS = 5.0
"""Максимальное время ожидания ответа от API HIBP в секундах."""


def build_auth_cookies_provider(
    refresh_token_cookie_name: str,
    refresh_token_lifetime_days: int,
    auth_cookie_path: str,
    auth_cookie_domain: str | None,
    auth_cookie_secure: bool,
    auth_cookie_samesite: Literal["lax", "strict", "none"],
) -> AuthCookiesProvider:
    """Создать провайдер HttpOnly-cookie refresh-токена.

    Провайдер управляет auth-cookie: устанавливает и удаляет
    HttpOnly-cookie refresh-токена в HTTP-ответах роутеров.
    Все атрибуты cookie передаются параметрами, что позволяет
    модулю Users не зависеть от глобального Composition Root.

    Parameters
    ----------
    refresh_token_cookie_name : str
        Имя cookie с refresh-токеном.
    refresh_token_lifetime_days : int
        Время жизни refresh-токена в днях, определяющее ``Max-Age``
        cookie.
    auth_cookie_path : str
        Значение атрибута ``Path`` cookie.
    auth_cookie_domain : str | None
        Значение атрибута ``Domain`` cookie.
    auth_cookie_secure : bool
        Флаг ``Secure``: передавать cookie только по HTTPS.
    auth_cookie_samesite : Literal["lax", "strict", "none"]
        Значение атрибута ``SameSite`` cookie.

    Returns
    -------
    AuthCookiesProvider
        Провайдер установки и удаления auth-cookie refresh-токена.
    """
    return AuthCookiesProvider(
        refresh_token_cookie_name=refresh_token_cookie_name,
        refresh_token_lifetime_days=refresh_token_lifetime_days,
        auth_cookie_path=auth_cookie_path,
        auth_cookie_domain=auth_cookie_domain,
        auth_cookie_secure=auth_cookie_secure,
        auth_cookie_samesite=auth_cookie_samesite,
    )


@lru_cache
def build_hibp_http_client() -> AsyncClient:
    """Создать асинхронный HTTP-клиент для запросов к HIBP.

    Returns
    -------
    AsyncClient
        Асинхронный HTTP-клиент с таймаутом ``_HIBP_TIMEOUT_SECONDS``.

    Notes
    -----
    Результат кэшируется через ``lru_cache`` (ADR-0001, п. 2 ответов
    разработчику): клиент внешнего сервиса является дорогим ресурсом
    уровня Infrastructure/Composition, поэтому допускается единственный
    экземпляр на всё приложение. Закрытие клиента выполняется
    при завершении работы приложения в lifespan.
    """
    return AsyncClient(timeout=_HIBP_TIMEOUT_SECONDS)


def build_compromised_password_checker() -> HibpCompromisedPasswordChecker:
    """Создать сервис проверки пароля на утечки данных.

    Returns
    -------
    HibpCompromisedPasswordChecker
        Сервис проверки пароля через HIBP Pwned Passwords.
    """
    return HibpCompromisedPasswordChecker(client=build_hibp_http_client())


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
