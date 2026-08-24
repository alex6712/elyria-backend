from collections.abc import Callable
from typing import Literal

from sqlalchemy.ext.asyncio import AsyncEngine

from src.shared.application.ports.persistence import TokenBlacklist
from src.shared.application.ports.security import TokenVerifier
from src.shared.infrastructure import SignatureKeys
from src.users.application.use_cases import (
    ChangeProfileUseCase,
    LoginUseCase,
    LogoutUseCase,
    RefreshSessionUseCase,
    RegisterUserUseCase,
)
from src.users.composition.services import (
    build_auth_cookies_provider,
    build_compromised_password_checker,
    build_password_hasher,
    build_token_hasher,
    build_token_issuer,
)
from src.users.composition.use_cases import (
    build_change_profile_use_case,
    build_login_use_case,
    build_logout_use_case,
    build_refresh_session_use_case,
    build_register_user_use_case,
)
from src.users.presentation.http.services import AuthCookiesProvider


class UsersContainer:
    """Контейнер Use Case контекста Users.

    Инкапсулирует фабричные функции Use Cases за приватными атрибутами
    и предоставляет доступ к свежим экземплярам через properties.
    Каждое обращение к property вызывает соответствующую фабрику и
    возвращает новый Use Case с новой единицей работы (Unit of Work),
    что соответствует transient-семантике (ADR-0002, п. 1 ответов
    разработчику). Сами фабрики скрыты от внешнего кода: снаружи
    контейнер выглядит как набор готовых к использованию Use Cases,
    а не набор функций, которые нужно дополнительно вызывать.

    Parameters
    ----------
    register_user_use_case_factory : Callable[[], RegisterUserUseCase]
        Фабрика, создающая новый экземпляр Use Case регистрации
        пользователя при каждом вызове.
    login_use_case_factory : Callable[[], LoginUseCase]
        Фабрика, создающая новый экземпляр Use Case аутентификации
        при каждом вызове.
    refresh_session_use_case_factory : Callable[[], RefreshSessionUseCase]
        Фабрика, создающая новый экземпляр Use Case обновления пары
        токенов при каждом вызове.
    logout_use_case_factory : Callable[[], LogoutUseCase]
        Фабрика, создающая новый экземпляр Use Case завершения
        пользовательской сессии при каждом вызове.
    change_profile_use_case_factory : Callable[[], ChangeProfileUseCase]
        Фабрика, создающая новый экземпляр Use Case изменения профиля
        пользователя при каждом вызове.
    auth_cookies_provider : AuthCookiesProvider
        Готовый экземпляр провайдера auth-cookie. В отличие от
        Use Cases передаётся напрямую, а не фабрикой, поскольку
        не хранит состояние конкретного запроса и безопасен для
        повторного использования между запросами.

    Attributes
    ----------
    register_user_use_case : RegisterUserUseCase
        Use Case регистрации нового пользователя. Новый экземпляр
        при каждом обращении.
    login_use_case : LoginUseCase
        Use Case аутентификации пользователя. Новый экземпляр при
        каждом обращении.
    refresh_session_use_case : RefreshSessionUseCase
        Use Case обновления пары токенов. Новый экземпляр при каждом
        обращении.
    logout_use_case : LogoutUseCase
        Use Case завершения пользовательской сессии. Новый экземпляр
        при каждом обращении.
    change_profile_use_case : ChangeProfileUseCase
        Use Case изменения профиля пользователя. Новый экземпляр при
        каждом обращении.
    auth_cookies_provider : AuthCookiesProvider
        Провайдер установки и удаления HttpOnly-cookie refresh-токена.
        В отличие от Use Cases, единственный экземпляр на время жизни
        контейнера (singleton), а не фабрика.
    """

    __slots__ = (
        "_change_profile_use_case_factory",
        "_login_use_case_factory",
        "_logout_use_case_factory",
        "_refresh_session_use_case_factory",
        "_register_user_use_case_factory",
        "auth_cookies_provider",
    )

    def __init__(
        self,
        register_user_use_case_factory: Callable[[], RegisterUserUseCase],
        login_use_case_factory: Callable[[], LoginUseCase],
        refresh_session_use_case_factory: Callable[[], RefreshSessionUseCase],
        logout_use_case_factory: Callable[[], LogoutUseCase],
        change_profile_use_case_factory: Callable[[], ChangeProfileUseCase],
        auth_cookies_provider: AuthCookiesProvider,
    ) -> None:
        self._register_user_use_case_factory = register_user_use_case_factory
        self._login_use_case_factory = login_use_case_factory
        self._refresh_session_use_case_factory = refresh_session_use_case_factory
        self._logout_use_case_factory = logout_use_case_factory
        self._change_profile_use_case_factory = change_profile_use_case_factory

        self.auth_cookies_provider = auth_cookies_provider

    @property
    def register_user_use_case(self) -> RegisterUserUseCase:
        """Получить новый экземпляр Use Case регистрации пользователя.

        Returns
        -------
        RegisterUserUseCase
            Новый экземпляр Use Case, созданный вызовом приватной
            фабрики.
        """
        return self._register_user_use_case_factory()

    @property
    def login_use_case(self) -> LoginUseCase:
        """Получить новый экземпляр Use Case аутентификации пользователя.

        Returns
        -------
        LoginUseCase
            Новый экземпляр Use Case, созданный вызовом приватной
            фабрики.
        """
        return self._login_use_case_factory()

    @property
    def refresh_session_use_case(self) -> RefreshSessionUseCase:
        """Получить новый экземпляр Use Case обновления пары токенов.

        Returns
        -------
        RefreshSessionUseCase
            Новый экземпляр Use Case, созданный вызовом приватной
            фабрики.
        """
        return self._refresh_session_use_case_factory()

    @property
    def logout_use_case(self) -> LogoutUseCase:
        """Получить новый экземпляр Use Case завершения пользовательской сессии.

        Returns
        -------
        LogoutUseCase
            Новый экземпляр Use Case, созданный вызовом приватной
            фабрики.
        """
        return self._logout_use_case_factory()

    @property
    def change_profile_use_case(self) -> ChangeProfileUseCase:
        """Получить новый экземпляр Use Case изменения профиля пользователя.

        Returns
        -------
        ChangeProfileUseCase
            Новый экземпляр Use Case, созданный вызовом приватной
            фабрики.
        """
        return self._change_profile_use_case_factory()


def build_users_module(
    *,
    engine: AsyncEngine,
    issuer: str,
    jws_algorithm: str,
    hmac_secret_key: str,
    signature_keys: SignatureKeys,
    token_verifier: TokenVerifier,
    token_blacklist: TokenBlacklist,
    access_token_lifetime_minutes: int,
    refresh_token_cookie_name: str,
    refresh_token_lifetime_days: int,
    auth_cookie_path: str,
    auth_cookie_domain: str | None,
    auth_cookie_secure: bool,
    auth_cookie_samesite: Literal["lax", "strict", "none"],
) -> UsersContainer:
    """Собрать модуль Users: контейнер Use Cases с реализациями портов.

    Единственная точка сборки Users в границах его ограниченного
    слоя композиции. Создаёт реализации портов (хеширование паролей,
    выпуск токенов, провайдер auth-cookie) и связывает их с фабриками
    Use Cases. Общие ресурсы (движок БД, ключи подписи, сервисы
    проверки и отзыва токенов, настройки) передаются параметрами:
    модуль ничего не знает о глобальном Composition Root.

    Parameters
    ----------
    engine : AsyncEngine
        Асинхронный движок SQLAlchemy для открытия транзакций.
    issuer : str
        Издатель JWT-токенов (значение утверждения ``iss``).
    jws_algorithm : str
        Алгоритм подписи JWT (например, ``"EdDSA"``).
    hmac_secret_key : str
        Секретный ключ HMAC-SHA256 для хеширования токенов.
    signature_keys : SignatureKeys
        Пара ключей Ed25519 для подписи выпускаемых токенов.
    token_verifier : TokenVerifier
        Сервис проверки подлинности refresh-токенов.
    token_blacklist : TokenBlacklist
        Хранилище отозванных access-токенов.
    access_token_lifetime_minutes : int
        Время жизни выдаваемого access-токена в минутах.
    refresh_token_cookie_name : str
        Имя cookie с refresh-токеном.
    refresh_token_lifetime_days : int
        Время жизни выдаваемого refresh-токена и связанной с ним сессии в днях.
    auth_cookie_path : str
        Значение атрибута ``Path`` auth-cookie.
    auth_cookie_domain : str | None
        Значение атрибута ``Domain`` auth-cookie.
    auth_cookie_secure : bool
        Флаг ``Secure`` auth-cookie: передавать cookie только по HTTPS.
    auth_cookie_samesite : Literal["lax", "strict", "none"]
        Значение атрибута ``SameSite`` auth-cookie.

    Returns
    -------
    UsersContainer
        Контейнер фабрик Use Cases контекста Users.

    Notes
    -----
    Реализации портов (хешеры, выпуск токенов, проверка пароля на
    утечки, провайдер auth-cookie) создаются один раз на время жизни
    контейнера; Use Cases - transient, новый экземпляр на каждый вызов
    соответствующей фабрики.
    """
    password_hasher = build_password_hasher()
    token_hasher = build_token_hasher(hmac_secret_key=hmac_secret_key)
    compromised_password_checker = build_compromised_password_checker()

    token_issuer = build_token_issuer(
        issuer=issuer,
        algorithm=jws_algorithm,
        signature_keys=signature_keys,
    )

    auth_cookies_provider = build_auth_cookies_provider(
        refresh_token_cookie_name=refresh_token_cookie_name,
        refresh_token_lifetime_days=refresh_token_lifetime_days,
        auth_cookie_path=auth_cookie_path,
        auth_cookie_domain=auth_cookie_domain,
        auth_cookie_secure=auth_cookie_secure,
        auth_cookie_samesite=auth_cookie_samesite,
    )

    return UsersContainer(
        register_user_use_case_factory=lambda: build_register_user_use_case(
            engine=engine,
            password_hasher=password_hasher,
            compromised_password_checker=compromised_password_checker,
            token_issuer=token_issuer,
            token_hasher=token_hasher,
            at_lifetime_minutes=access_token_lifetime_minutes,
            rt_lifetime_days=refresh_token_lifetime_days,
        ),
        login_use_case_factory=lambda: build_login_use_case(
            engine=engine,
            password_hasher=password_hasher,
            token_issuer=token_issuer,
            token_hasher=token_hasher,
            at_lifetime_minutes=access_token_lifetime_minutes,
            rt_lifetime_days=refresh_token_lifetime_days,
        ),
        refresh_session_use_case_factory=lambda: build_refresh_session_use_case(
            engine=engine,
            token_issuer=token_issuer,
            token_verifier=token_verifier,
            token_hasher=token_hasher,
            at_lifetime_minutes=access_token_lifetime_minutes,
            rt_lifetime_days=refresh_token_lifetime_days,
        ),
        logout_use_case_factory=lambda: build_logout_use_case(
            engine=engine,
            token_verifier=token_verifier,
            token_blacklist=token_blacklist,
        ),
        change_profile_use_case_factory=lambda: build_change_profile_use_case(
            engine=engine,
            token_verifier=token_verifier,
            token_blacklist=token_blacklist,
        ),
        auth_cookies_provider=auth_cookies_provider,
    )
