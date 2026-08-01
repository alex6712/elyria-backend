from dataclasses import dataclass

from src.composition.app_info import APP_NAME
from src.composition.engine import build_engine
from src.composition.paths import PRIVATE_SIGNATURE_KEY_PATH, PUBLIC_SIGNATURE_KEY_PATH
from src.composition.redis import build_redis_client
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
    ресурсы (движок БД, клиент Redis), читает настройки и ключи
    подписи, после чего передаёт их в фабрики модулей ограниченных
    контекстов. Модули ничего не знают о глобальном слое композиции.

    Returns
    -------
    ApplicationContainer
        Контейнер всех собранных модулей приложения.
    """
    return ApplicationContainer(
        users=build_users_module(
            engine=build_engine(),
            redis_client=build_redis_client(),
            issuer=APP_NAME,
            jws_algorithm=(settings := get_settings()).JWS_ALGORITHM,
            hmac_secret_key=settings.HMAC_SECRET_KEY,
            public_key_path=PUBLIC_SIGNATURE_KEY_PATH,
            private_key_path=PRIVATE_SIGNATURE_KEY_PATH,
            private_signature_password=settings.PRIVATE_SIGNATURE_KEY_PASSWORD,
            access_token_lifetime_minutes=settings.ACCESS_TOKEN_LIFETIME_MINUTES,
            refresh_token_lifetime_days=settings.REFRESH_TOKEN_LIFETIME_DAYS,
        ),
    )
