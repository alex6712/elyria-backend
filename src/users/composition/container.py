from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from redis.asyncio import Redis as AsyncRedis
from sqlalchemy.ext.asyncio import AsyncEngine

from src.users.application.use_cases import (
    LoginUseCase,
    LogoutUseCase,
    RefreshSessionUseCase,
    RegisterUserUseCase,
)
from src.users.composition.services import (
    build_compromised_password_checker,
    build_password_hasher,
    build_signature_keys_provider,
    build_token_blacklist,
    build_token_hasher,
    build_token_issuer,
    build_token_verifier,
)
from src.users.composition.use_cases import (
    build_login_use_case,
    build_logout_use_case,
    build_refresh_session_use_case,
    build_register_user_use_case,
)


@dataclass(frozen=True, slots=True)
class UsersContainer:
    """Контейнер Use Case контекста Users.

    Неизменяемая структура фабричных функций, создающих свежие
    экземпляры Use Cases. Каждый вызов поля-фабрики возвращает
    новый Use Case с новой единицей работы (Unit of Work), что
    соответствует transient-семантике (ADR-0002, п. 1 ответов
    разработчику).

    Attributes
    ----------
    register_user : Callable[[], RegisterUserUseCase]
        Фабрика Use Case регистрации нового пользователя.
    login : Callable[[], LoginUseCase]
        Фабрика Use Case аутентификации пользователя.
    refresh_session : Callable[[], RefreshSessionUseCase]
        Фабрика Use Case обновления пары токенов.
    logout : Callable[[], LogoutUseCase]
        Фабрика Use Case завершения пользовательской сессии.
    """

    register_user: Callable[[], RegisterUserUseCase]
    login: Callable[[], LoginUseCase]
    refresh_session: Callable[[], RefreshSessionUseCase]
    logout: Callable[[], LogoutUseCase]


def build_users_module(
    *,
    engine: AsyncEngine,
    redis_client: AsyncRedis,
    issuer: str,
    jws_algorithm: str,
    hmac_secret_key: str,
    public_key_path: Path,
    private_key_path: Path,
    private_signature_password: str,
    access_token_lifetime_minutes: int,
    refresh_token_lifetime_days: int,
) -> UsersContainer:
    """Собрать модуль Users: контейнер Use Cases с реализациями портов.

    Единственная точка сборки Users в границах его ограниченного
    слоя композиции. Создаёт реализации портов (хеширование паролей,
    выпуск и проверка токенов, чёрный список) и связывает их с
    фабриками Use Cases. Внешние ресурсы (движок БД, клиент Redis,
    ключи подписи, настройки) передаются параметрами: модуль ничего
    не знает о глобальном Composition Root.

    Parameters
    ----------
    engine : AsyncEngine
        Асинхронный движок SQLAlchemy для открытия транзакций.
    redis_client : AsyncRedis
        Асинхронный клиент Redis для чёрного списка токенов.
    issuer : str
        Издатель JWT-токенов (значение утверждения ``iss``).
    jws_algorithm : str
        Алгоритм подписи JWT (например, ``"EdDSA"``).
    hmac_secret_key : str
        Секретный ключ HMAC-SHA256 для хеширования токенов.
    public_key_path : Path
        Путь к PEM-файлу публичного ключа Ed25519.
    private_key_path : Path
        Путь к PEM-файлу приватного ключа Ed25519.
    private_signature_password : str
        Пароль для расшифровки приватного ключа.
    access_token_lifetime_minutes : int
        Время жизни выдаваемого access-токена в минутах.
    refresh_token_lifetime_days : int
        Время жизни выдаваемого refresh-токена и связанной с ним сессии в днях.

    Returns
    -------
    UsersContainer
        Контейнер фабрик Use Cases контекста Users.

    Notes
    -----
    Реализации портов (хешеры, выпуск и проверка токенов, чёрный
    список, проверка пароля на утечки) создаются один раз на время
    жизни контейнера; Use Cases - transient, новый экземпляр на каждый
    вызов соответствующей фабрики.
    """
    password_hasher = build_password_hasher()
    token_hasher = build_token_hasher(hmac_secret_key=hmac_secret_key)
    compromised_password_checker = build_compromised_password_checker()

    signature_keys = build_signature_keys_provider(
        public_key_path=public_key_path,
        private_key_path=private_key_path,
        private_signature_password=private_signature_password,
    ).get_signature_keys()

    token_issuer = build_token_issuer(
        issuer=issuer,
        algorithm=jws_algorithm,
        signature_keys=signature_keys,
    )
    token_verifier = build_token_verifier(
        issuer=issuer,
        algorithm=jws_algorithm,
        signature_keys=signature_keys,
    )
    token_blacklist = build_token_blacklist(redis_client=redis_client)

    return UsersContainer(
        register_user=lambda: build_register_user_use_case(
            engine=engine,
            password_hasher=password_hasher,
            compromised_password_checker=compromised_password_checker,
            token_issuer=token_issuer,
            token_hasher=token_hasher,
            at_lifetime_minutes=access_token_lifetime_minutes,
            rt_lifetime_days=refresh_token_lifetime_days,
        ),
        login=lambda: build_login_use_case(
            engine=engine,
            password_hasher=password_hasher,
            token_issuer=token_issuer,
            token_hasher=token_hasher,
            at_lifetime_minutes=access_token_lifetime_minutes,
            rt_lifetime_days=refresh_token_lifetime_days,
        ),
        refresh_session=lambda: build_refresh_session_use_case(
            engine=engine,
            token_issuer=token_issuer,
            token_verifier=token_verifier,
            token_hasher=token_hasher,
            at_lifetime_minutes=access_token_lifetime_minutes,
            rt_lifetime_days=refresh_token_lifetime_days,
        ),
        logout=lambda: build_logout_use_case(
            engine=engine,
            token_verifier=token_verifier,
            token_blacklist=token_blacklist,
        ),
    )
