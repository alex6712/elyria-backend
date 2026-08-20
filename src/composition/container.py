from dataclasses import dataclass

from src.composition.app_info import APP_NAME
from src.composition.engine import build_engine
from src.composition.paths import PRIVATE_SIGNATURE_KEY_PATH, PUBLIC_SIGNATURE_KEY_PATH
from src.composition.redis import build_redis_client
from src.composition.security import (
    build_signature_keys_provider,
    build_token_blacklist,
    build_token_verifier,
)
from src.composition.settings import get_settings
from src.users.composition import UsersContainer, build_users_module


@dataclass(frozen=True, slots=True)
class ApplicationContainer:
    """Контейнер всех модулей (bounded contexts) приложения.

    Неизменяемая структура, объединяющая собранные модули
    ограниченных контекстов. На текущем этапе содержит единственный
    модуль Users; при появлении новых контекстов (Media, Couples,
    Notes) они добавляются соответствующими полями.

    Attributes
    ----------
    users : UsersContainer
        Собранный модуль контекста Users.
    """

    users: UsersContainer


def build_application_container() -> ApplicationContainer:
    """Собрать приложение: все модули bounded contexts.

    Единственный Composition Root приложения. Создаёт общие
    ресурсы (движок БД, клиент Redis, ключи подписи, сервисы
    проверки и отзыва токенов), читает настройки, после чего
    передаёт их в фабрики модулей ограниченных контекстов.
    Модули ничего не знают о глобальном слое композиции.

    Returns
    -------
    ApplicationContainer
        Контейнер всех собранных модулей приложения.
    """
    settings = get_settings()

    signature_keys = build_signature_keys_provider(
        public_key_path=PUBLIC_SIGNATURE_KEY_PATH,
        private_key_path=PRIVATE_SIGNATURE_KEY_PATH,
        private_signature_password=settings.PRIVATE_SIGNATURE_KEY_PASSWORD,
    ).get_signature_keys()

    token_verifier = build_token_verifier(
        issuer=APP_NAME, algorithm=settings.JWS_ALGORITHM, signature_keys=signature_keys
    )
    token_blacklist = build_token_blacklist(redis_client=build_redis_client())

    return ApplicationContainer(
        users=build_users_module(
            engine=build_engine(),
            issuer=APP_NAME,
            jws_algorithm=settings.JWS_ALGORITHM,
            hmac_secret_key=settings.HMAC_SECRET_KEY,
            signature_keys=signature_keys,
            token_verifier=token_verifier,
            token_blacklist=token_blacklist,
            access_token_lifetime_minutes=settings.ACCESS_TOKEN_LIFETIME_MINUTES,
            refresh_token_cookie_name=settings.REFRESH_TOKEN_COOKIE_NAME,
            refresh_token_lifetime_days=settings.REFRESH_TOKEN_LIFETIME_DAYS,
            auth_cookie_path=settings.AUTH_COOKIE_PATH,
            auth_cookie_domain=settings.AUTH_COOKIE_DOMAIN,
            auth_cookie_secure=settings.AUTH_COOKIE_SECURE,
            auth_cookie_samesite=settings.AUTH_COOKIE_SAMESITE,
        ),
    )
