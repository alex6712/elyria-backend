from collections.abc import Callable
from typing import Literal

from sqlalchemy.ext.asyncio import AsyncEngine

from src.shared.application.ports.persistence import TokenBlacklist
from src.shared.application.ports.security import TokenVerifier
from src.shared.infrastructure import SignatureKeys
from src.shared.infrastructure.adapters.messaging import InMemoryEventDispatcher
from src.users.application.handlers.command import (
    ChangePasswordCommandHandler,
    ChangeProfileCommandHandler,
    LoginCommandHandler,
    LogoutCommandHandler,
    RefreshSessionCommandHandler,
    RegisterUserCommandHandler,
)
from src.users.application.handlers.query import (
    GetProfileQueryHandler,
    SearchUsersQueryHandler,
)
from src.users.composition.handlers import (
    build_change_password_command_handler,
    build_change_profile_command_handler,
    build_get_profile_query_handler,
    build_login_command_handler,
    build_logout_command_handler,
    build_refresh_session_command_handler,
    build_register_user_command_handler,
    build_search_users_query_handler,
)
from src.users.composition.services import (
    build_auth_cookies_provider,
    build_compromised_password_checker,
    build_password_hasher,
    build_token_hasher,
    build_token_issuer,
)
from src.users.domain.events import ProfileChangedEvent, UserRegisteredEvent
from src.users.infrastructure.projections import UserSearchProjection
from src.users.presentation.http.services import AuthCookiesProvider


class UsersContainer:
    """Контейнер обработчиков команд и запросов контекста Users.

    Инкапсулирует фабричные функции Command/Query Handlers за приватными
    атрибутами и предоставляет доступ к свежим экземплярам через properties.
    Каждое обращение к property вызывает соответствующую фабрику и
    возвращает новый обработчик с новой единицей работы (Unit of Work),
    что соответствует transient-семантике (ADR-0002). Сами фабрики скрыты
    от внешнего кода: снаружи контейнер выглядит как набор готовых
    к использованию обработчиков.

    Диспетчер доменных событий и обработчик проекции поиска пользователей
    создаются один раз на время жизни контейнера (singleton) и рассылаются
    соответствующим обработчикам, публикующим доменные события.

    Parameters
    ----------
    register_user_command_handler_factory : Callable[[], RegisterUserCommandHandler]
        Фабрика, создающая новый обработчик команды регистрации при каждом вызове.
    login_command_handler_factory : Callable[[], LoginCommandHandler]
        Фабрика, создающая новый обработчик команды аутентификации при каждом вызове.
    refresh_session_command_handler_factory : Callable[[], RefreshSessionCommandHandler]
        Фабрика, создающая новый обработчик команды обновления пары токенов.
    logout_command_handler_factory : Callable[[], LogoutCommandHandler]
        Фабрика, создающая новый обработчик команды завершения сессии.
    change_password_command_handler_factory : Callable[[], ChangePasswordCommandHandler]
        Фабрика, создающая новый обработчик команды смены пароля.
    change_profile_command_handler_factory : Callable[[], ChangeProfileCommandHandler]
        Фабрика, создающая новый обработчик команды изменения профиля.
    get_profile_query_handler_factory : Callable[[], GetProfileQueryHandler]
        Фабрика, создающая новый query handler получения профиля.
    search_users_query_handler_factory : Callable[[], SearchUsersQueryHandler]
        Фабрика, создающая новый query handler поиска пользователей.
    auth_cookies_provider : AuthCookiesProvider
        Готовый экземпляр провайдера auth-cookie.

    Attributes
    ----------
    register_user_command_handler : RegisterUserCommandHandler
        Обработчик команды регистрации. Новый экземпляр при каждом обращении.
    login_command_handler : LoginCommandHandler
        Обработчик команды аутентификации. Новый экземпляр при каждом обращении.
    refresh_session_command_handler : RefreshSessionCommandHandler
        Обработчик команды обновления пары токенов. Новый экземпляр при
        каждом обращении.
    logout_command_handler : LogoutCommandHandler
        Обработчик команды завершения сессии. Новый экземпляр при каждом обращении.
    change_password_command_handler : ChangePasswordCommandHandler
        Обработчик команды смены пароля. Новый экземпляр при каждом обращении.
    change_profile_command_handler : ChangeProfileCommandHandler
        Обработчик команды изменения профиля. Новый экземпляр при каждом обращении.
    get_profile_query_handler : GetProfileQueryHandler
        Query handler получения профиля. Новый экземпляр при каждом обращении.
    search_users_query_handler : SearchUsersQueryHandler
        Query handler поиска пользователей. Новый экземпляр при каждом обращении.
    auth_cookies_provider : AuthCookiesProvider
        Провайдер установки и удаления HttpOnly-cookie refresh-токена.
    """

    __slots__ = (
        "_change_password_command_handler_factory",
        "_change_profile_command_handler_factory",
        "_engine",
        "_event_dispatcher",
        "_get_profile_query_handler_factory",
        "_login_command_handler_factory",
        "_logout_command_handler_factory",
        "_refresh_session_command_handler_factory",
        "_register_user_command_handler_factory",
        "_search_users_query_handler_factory",
        "auth_cookies_provider",
    )

    def __init__(
        self,
        register_user_command_handler_factory: Callable[[], RegisterUserCommandHandler],
        login_command_handler_factory: Callable[[], LoginCommandHandler],
        refresh_session_command_handler_factory: Callable[
            [], RefreshSessionCommandHandler
        ],
        logout_command_handler_factory: Callable[[], LogoutCommandHandler],
        change_password_command_handler_factory: Callable[
            [], ChangePasswordCommandHandler
        ],
        change_profile_command_handler_factory: Callable[
            [], ChangeProfileCommandHandler
        ],
        get_profile_query_handler_factory: Callable[[], GetProfileQueryHandler],
        search_users_query_handler_factory: Callable[[], SearchUsersQueryHandler],
        engine: AsyncEngine,
        event_dispatcher: InMemoryEventDispatcher,
        auth_cookies_provider: AuthCookiesProvider,
    ) -> None:
        self._register_user_command_handler_factory = (
            register_user_command_handler_factory
        )
        self._login_command_handler_factory = login_command_handler_factory
        self._refresh_session_command_handler_factory = (
            refresh_session_command_handler_factory
        )
        self._logout_command_handler_factory = logout_command_handler_factory
        self._change_password_command_handler_factory = (
            change_password_command_handler_factory
        )
        self._change_profile_command_handler_factory = (
            change_profile_command_handler_factory
        )
        self._get_profile_query_handler_factory = get_profile_query_handler_factory
        self._search_users_query_handler_factory = search_users_query_handler_factory

        self._engine = engine
        self._event_dispatcher = event_dispatcher

        self.auth_cookies_provider = auth_cookies_provider

    async def register_event_subscriptions(self) -> None:
        """Зарегистрировать подписки обработчиков проекций на доменные события.

        Подписывает обработчик проекции поиска пользователей на события
        регистрации пользователя и изменения профиля. Диспетчер выполняет
        обработчики после успешного коммита основной транзакции.

        Notes
        -----
        Вызывается один раз на этапе инициализации приложения (lifespan),
        когда доступен работающий цикл событий для асинхронной подписки.
        """
        projection = UserSearchProjection(engine=self._engine)

        await self._event_dispatcher.subscribe(
            UserRegisteredEvent, projection.handle_user_registered
        )
        await self._event_dispatcher.subscribe(
            ProfileChangedEvent, projection.handle_profile_changed
        )

    @property
    def register_user_command_handler(self) -> RegisterUserCommandHandler:
        """Получить новый обработчик команды регистрации пользователя.

        Returns
        -------
        RegisterUserCommandHandler
            Новый экземпляр обработчика, созданный вызовом приватной фабрики.
        """
        return self._register_user_command_handler_factory()

    @property
    def login_command_handler(self) -> LoginCommandHandler:
        """Получить новый обработчик команды аутентификации пользователя.

        Returns
        -------
        LoginCommandHandler
            Новый экземпляр обработчика, созданный вызовом приватной фабрики.
        """
        return self._login_command_handler_factory()

    @property
    def refresh_session_command_handler(self) -> RefreshSessionCommandHandler:
        """Получить новый обработчик команды обновления пары токенов.

        Returns
        -------
        RefreshSessionCommandHandler
            Новый экземпляр обработчика, созданный вызовом приватной фабрики.
        """
        return self._refresh_session_command_handler_factory()

    @property
    def logout_command_handler(self) -> LogoutCommandHandler:
        """Получить новый обработчик команды завершения сессии.

        Returns
        -------
        LogoutCommandHandler
            Новый экземпляр обработчика, созданный вызовом приватной фабрики.
        """
        return self._logout_command_handler_factory()

    @property
    def change_password_command_handler(self) -> ChangePasswordCommandHandler:
        """Получить новый обработчик команды смены пароля.

        Returns
        -------
        ChangePasswordCommandHandler
            Новый экземпляр обработчика, созданный вызовом приватной фабрики.
        """
        return self._change_password_command_handler_factory()

    @property
    def change_profile_command_handler(self) -> ChangeProfileCommandHandler:
        """Получить новый обработчик команды изменения профиля.

        Returns
        -------
        ChangeProfileCommandHandler
            Новый экземпляр обработчика, созданный вызовом приватной фабрики.
        """
        return self._change_profile_command_handler_factory()

    @property
    def get_profile_query_handler(self) -> GetProfileQueryHandler:
        """Получить новый query handler получения профиля.

        Returns
        -------
        GetProfileQueryHandler
            Новый экземпляр обработчика, созданный вызовом приватной фабрики.
        """
        return self._get_profile_query_handler_factory()

    @property
    def search_users_query_handler(self) -> SearchUsersQueryHandler:
        """Получить новый query handler поиска пользователей.

        Returns
        -------
        SearchUsersQueryHandler
            Новый экземпляр обработчика, созданный вызовом приватной фабрики.
        """
        return self._search_users_query_handler_factory()


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
    """Собрать модуль Users: контейнер обработчиков с реализациями портов.

    Единственная точка сборки Users в границах его ограниченного
    слоя композиции. Создаёт реализации портов (хеширование паролей,
    выпуск токенов, провайдер auth-cookie, диспетчер доменных событий,
    обработчик проекции поиска пользователей) и связывает их с фабриками
    Command/Query Handlers.

    Диспетчер доменных событий и обработчик проекции создаются один раз
    на время жизни контейнера; на обработчик проекции регистрируются
    подписки на события регистрации и изменения профиля. Обработчики команд
    и запросов - transient, новый экземпляр на каждый вызов фабрики.

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
        Контейнер фабрик обработчиков контекста Users.

    Notes
    -----
    Реализации портов (хешеры, выпуск токенов, проверка пароля на
    утечки, провайдер auth-cookie, диспетчер событий, обработчик
    проекции) создаются один раз на время жизни контейнера;
    обработчики - transient, новый экземпляр на каждый вызов
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

    event_dispatcher = InMemoryEventDispatcher()

    return UsersContainer(
        register_user_command_handler_factory=lambda: (
            build_register_user_command_handler(
                engine=engine,
                password_hasher=password_hasher,
                compromised_password_checker=compromised_password_checker,
                token_issuer=token_issuer,
                token_hasher=token_hasher,
                event_dispatcher=event_dispatcher,
                at_lifetime_minutes=access_token_lifetime_minutes,
                rt_lifetime_days=refresh_token_lifetime_days,
            )
        ),
        login_command_handler_factory=lambda: build_login_command_handler(
            engine=engine,
            password_hasher=password_hasher,
            token_issuer=token_issuer,
            token_hasher=token_hasher,
            at_lifetime_minutes=access_token_lifetime_minutes,
            rt_lifetime_days=refresh_token_lifetime_days,
        ),
        refresh_session_command_handler_factory=lambda: (
            build_refresh_session_command_handler(
                engine=engine,
                token_issuer=token_issuer,
                token_verifier=token_verifier,
                token_hasher=token_hasher,
                at_lifetime_minutes=access_token_lifetime_minutes,
                rt_lifetime_days=refresh_token_lifetime_days,
            )
        ),
        logout_command_handler_factory=lambda: build_logout_command_handler(
            engine=engine,
            token_verifier=token_verifier,
            token_blacklist=token_blacklist,
        ),
        change_password_command_handler_factory=lambda: (
            build_change_password_command_handler(
                engine=engine,
                password_hasher=password_hasher,
                compromised_password_checker=compromised_password_checker,
                token_verifier=token_verifier,
                token_blacklist=token_blacklist,
            )
        ),
        change_profile_command_handler_factory=lambda: (
            build_change_profile_command_handler(
                engine=engine,
                token_verifier=token_verifier,
                token_blacklist=token_blacklist,
                event_dispatcher=event_dispatcher,
            )
        ),
        get_profile_query_handler_factory=lambda: build_get_profile_query_handler(
            engine=engine,
            token_verifier=token_verifier,
            token_blacklist=token_blacklist,
        ),
        search_users_query_handler_factory=lambda: build_search_users_query_handler(
            engine=engine,
            token_verifier=token_verifier,
            token_blacklist=token_blacklist,
        ),
        engine=engine,
        event_dispatcher=event_dispatcher,
        auth_cookies_provider=auth_cookies_provider,
    )
