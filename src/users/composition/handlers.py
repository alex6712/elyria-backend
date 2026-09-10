from sqlalchemy.ext.asyncio import AsyncEngine

from src.shared.application.ports.persistence import TokenBlacklist
from src.shared.application.ports.security import TokenVerifier
from src.shared.domain.ports.messaging import EventDispatcher
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
from src.users.application.ports.security import (
    CompromisedPasswordChecker,
    PasswordHasher,
    TokenHasher,
    TokenIssuer,
)
from src.users.infrastructure.adapters import SqlAlchemyUsersUnitOfWork


def build_register_user_command_handler(
    *,
    engine: AsyncEngine,
    password_hasher: PasswordHasher,
    compromised_password_checker: CompromisedPasswordChecker,
    token_issuer: TokenIssuer,
    token_hasher: TokenHasher,
    event_dispatcher: EventDispatcher,
    at_lifetime_minutes: int,
    rt_lifetime_days: int,
) -> RegisterUserCommandHandler:
    """Создать обработчик команды регистрации пользователя.

    Каждый вызов фабрики создаёт новый экземпляр обработчика
    и новую единицу работы (Unit of Work), что соответствует
    transient-семантике: один вызов обработчика - одна транзакция
    (ADR-0002).

    Parameters
    ----------
    engine : AsyncEngine
        Асинхронный движок SQLAlchemy для открытия транзакций.
    password_hasher : PasswordHasher
        Сервис хеширования паролей.
    compromised_password_checker : CompromisedPasswordChecker
        Сервис проверки пароля на утечки данных.
    token_issuer : TokenIssuer
        Сервис выпуска новых токенов.
    token_hasher : TokenHasher
        Сервис криптографического хеширования сырых токенов.
    event_dispatcher : EventDispatcher
        Диспетчер доменных событий для публикации события регистрации.
    at_lifetime_minutes : int
        Время жизни выдаваемого access-токена в минутах.
    rt_lifetime_days : int
        Время жизни выдаваемого refresh-токена и связанной с ним сессии в днях.

    Returns
    -------
    RegisterUserCommandHandler
        Готовый к использованию обработчик команды регистрации.
    """
    return RegisterUserCommandHandler(
        uow=SqlAlchemyUsersUnitOfWork(engine),
        password_hasher=password_hasher,
        compromised_password_checker=compromised_password_checker,
        token_issuer=token_issuer,
        token_hasher=token_hasher,
        event_dispatcher=event_dispatcher,
        at_lifetime_minutes=at_lifetime_minutes,
        rt_lifetime_days=rt_lifetime_days,
    )


def build_login_command_handler(
    *,
    engine: AsyncEngine,
    password_hasher: PasswordHasher,
    token_issuer: TokenIssuer,
    token_hasher: TokenHasher,
    at_lifetime_minutes: int,
    rt_lifetime_days: int,
) -> LoginCommandHandler:
    """Создать обработчик команды аутентификации пользователя.

    Каждый вызов фабрики создаёт новый экземпляр обработчика
    и новую единицу работы (Unit of Work).

    Parameters
    ----------
    engine : AsyncEngine
        Асинхронный движок SQLAlchemy для открытия транзакций.
    password_hasher : PasswordHasher
        Сервис хеширования паролей для проверки учётных данных.
    token_issuer : TokenIssuer
        Сервис выпуска новых токенов.
    token_hasher : TokenHasher
        Сервис криптографического хеширования сырых токенов.
    at_lifetime_minutes : int
        Время жизни выдаваемого access-токена в минутах.
    rt_lifetime_days : int
        Время жизни выдаваемого refresh-токена и связанной с ним сессии в днях.

    Returns
    -------
    LoginCommandHandler
        Готовый к использованию обработчик команды входа в систему.
    """
    return LoginCommandHandler(
        uow=SqlAlchemyUsersUnitOfWork(engine),
        password_hasher=password_hasher,
        token_issuer=token_issuer,
        token_hasher=token_hasher,
        at_lifetime_minutes=at_lifetime_minutes,
        rt_lifetime_days=rt_lifetime_days,
    )


def build_refresh_session_command_handler(
    *,
    engine: AsyncEngine,
    token_issuer: TokenIssuer,
    token_verifier: TokenVerifier,
    token_hasher: TokenHasher,
    at_lifetime_minutes: int,
    rt_lifetime_days: int,
) -> RefreshSessionCommandHandler:
    """Создать обработчик команды обновления пары токенов.

    Каждый вызов фабрики создаёт новый экземпляр обработчика
    и новую единицу работы (Unit of Work).

    Parameters
    ----------
    engine : AsyncEngine
        Асинхронный движок SQLAlchemy для открытия транзакций.
    token_issuer : TokenIssuer
        Сервис выпуска новых токенов.
    token_verifier : TokenVerifier
        Сервис проверки структуры, подписи и срока действия токенов.
    token_hasher : TokenHasher
        Сервис криптографического хеширования сырых токенов.
    at_lifetime_minutes : int
        Время жизни выдаваемого access-токена в минутах.
    rt_lifetime_days : int
        Время жизни выдаваемого refresh-токена и связанной с ним сессии в днях.

    Returns
    -------
    RefreshSessionCommandHandler
        Готовый к использованию обработчик команды обновления токенов.
    """
    return RefreshSessionCommandHandler(
        uow=SqlAlchemyUsersUnitOfWork(engine),
        token_issuer=token_issuer,
        token_verifier=token_verifier,
        token_hasher=token_hasher,
        at_lifetime_minutes=at_lifetime_minutes,
        rt_lifetime_days=rt_lifetime_days,
    )


def build_logout_command_handler(
    *,
    engine: AsyncEngine,
    token_verifier: TokenVerifier,
    token_blacklist: TokenBlacklist,
) -> LogoutCommandHandler:
    """Создать обработчик команды завершения пользовательской сессии.

    Каждый вызов фабрики создаёт новый экземпляр обработчика
    и новую единицу работы (Unit of Work).

    Parameters
    ----------
    engine : AsyncEngine
        Асинхронный движок SQLAlchemy для открытия транзакций.
    token_verifier : TokenVerifier
        Сервис проверки подлинности access-токенов.
    token_blacklist : TokenBlacklist
        Хранилище отозванных access-токенов.

    Returns
    -------
    LogoutCommandHandler
        Готовый к использованию обработчик команды выхода из системы.
    """
    return LogoutCommandHandler(
        uow=SqlAlchemyUsersUnitOfWork(engine),
        token_verifier=token_verifier,
        token_blacklist=token_blacklist,
    )


def build_change_password_command_handler(
    *,
    engine: AsyncEngine,
    password_hasher: PasswordHasher,
    compromised_password_checker: CompromisedPasswordChecker,
    token_verifier: TokenVerifier,
    token_blacklist: TokenBlacklist,
) -> ChangePasswordCommandHandler:
    """Создать обработчик команды смены пароля пользователя.

    Каждый вызов фабрики создаёт новый экземпляр обработчика
    и новую единицу работы (Unit of Work).

    Parameters
    ----------
    engine : AsyncEngine
        Асинхронный движок SQLAlchemy для открытия транзакций.
    password_hasher : PasswordHasher
        Сервис хеширования паролей для проверки текущего пароля
        и хеширования нового.
    compromised_password_checker : CompromisedPasswordChecker
        Сервис проверки нового пароля на утечки данных.
    token_verifier : TokenVerifier
        Сервис проверки подлинности access-токенов.
    token_blacklist : TokenBlacklist
        Хранилище отозванных access-токенов.

    Returns
    -------
    ChangePasswordCommandHandler
        Готовый к использованию обработчик команды смены пароля.
    """
    return ChangePasswordCommandHandler(
        uow=SqlAlchemyUsersUnitOfWork(engine),
        password_hasher=password_hasher,
        compromised_password_checker=compromised_password_checker,
        token_verifier=token_verifier,
        token_blacklist=token_blacklist,
    )


def build_change_profile_command_handler(
    *,
    engine: AsyncEngine,
    token_verifier: TokenVerifier,
    token_blacklist: TokenBlacklist,
    event_dispatcher: EventDispatcher,
) -> ChangeProfileCommandHandler:
    """Создать обработчик команды изменения профиля пользователя.

    Каждый вызов фабрики создаёт новый экземпляр обработчика
    и новую единицу работы (Unit of Work).

    Parameters
    ----------
    engine : AsyncEngine
        Асинхронный движок SQLAlchemy для открытия транзакций.
    token_verifier : TokenVerifier
        Сервис проверки подлинности access-токенов.
    token_blacklist : TokenBlacklist
        Хранилище отозванных access-токенов.
    event_dispatcher : EventDispatcher
        Диспетчер доменных событий для публикации события изменения профиля.

    Returns
    -------
    ChangeProfileCommandHandler
        Готовый к использованию обработчик команды изменения профиля.
    """
    return ChangeProfileCommandHandler(
        uow=SqlAlchemyUsersUnitOfWork(engine),
        token_verifier=token_verifier,
        token_blacklist=token_blacklist,
        event_dispatcher=event_dispatcher,
    )


def build_get_profile_query_handler(
    *,
    engine: AsyncEngine,
    token_verifier: TokenVerifier,
    token_blacklist: TokenBlacklist,
) -> GetProfileQueryHandler:
    """Создать query handler получения профиля пользователя.

    Каждый вызов фабрики создаёт новый экземпляр обработчика
    и новую единицу работы (Unit of Work).

    Parameters
    ----------
    engine : AsyncEngine
        Асинхронный движок SQLAlchemy для открытия транзакций.
    token_verifier : TokenVerifier
        Сервис проверки подлинности access-токенов.
    token_blacklist : TokenBlacklist
        Хранилище отозванных access-токенов.

    Returns
    -------
    GetProfileQueryHandler
        Готовый к использованию query handler получения профиля.
    """
    return GetProfileQueryHandler(
        uow=SqlAlchemyUsersUnitOfWork(engine),
        token_verifier=token_verifier,
        token_blacklist=token_blacklist,
    )


def build_search_users_query_handler(
    *,
    engine: AsyncEngine,
    token_verifier: TokenVerifier,
    token_blacklist: TokenBlacklist,
) -> SearchUsersQueryHandler:
    """Создать query handler нечёткого поиска пользователей.

    Каждый вызов фабрики создаёт новый экземпляр обработчика
    и новую единицу работы (Unit of Work).

    Parameters
    ----------
    engine : AsyncEngine
        Асинхронный движок SQLAlchemy для открытия транзакций.
    token_verifier : TokenVerifier
        Сервис проверки подлинности access-токенов.
    token_blacklist : TokenBlacklist
        Хранилище отозванных access-токенов.

    Returns
    -------
    SearchUsersQueryHandler
        Готовый к использованию query handler поиска пользователей.
    """
    return SearchUsersQueryHandler(
        uow=SqlAlchemyUsersUnitOfWork(engine),
        token_verifier=token_verifier,
        token_blacklist=token_blacklist,
    )
