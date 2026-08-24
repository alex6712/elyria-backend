from sqlalchemy.ext.asyncio import AsyncEngine

from src.shared.application.ports.persistence import TokenBlacklist
from src.shared.application.ports.security import TokenVerifier
from src.users.application.ports.security import (
    CompromisedPasswordChecker,
    PasswordHasher,
    TokenHasher,
    TokenIssuer,
)
from src.users.application.use_cases import (
    ChangePasswordUseCase,
    ChangeProfileUseCase,
    GetProfileUseCase,
    LoginUseCase,
    LogoutUseCase,
    RefreshSessionUseCase,
    RegisterUserUseCase,
)
from src.users.infrastructure.adapters import SqlAlchemyUsersUnitOfWork


def build_register_user_use_case(
    *,
    engine: AsyncEngine,
    password_hasher: PasswordHasher,
    compromised_password_checker: CompromisedPasswordChecker,
    token_issuer: TokenIssuer,
    token_hasher: TokenHasher,
    at_lifetime_minutes: int,
    rt_lifetime_days: int,
) -> RegisterUserUseCase:
    """Создать Use Case регистрации нового пользователя.

    Каждый вызов фабрики создаёт новый экземпляр Use Case
    и новую единицу работы (Unit of Work), что соответствует
    transient-семантике: один вызов Use Case - одна транзакция
    (ADR-0002, п. 1 ответов разработчику).

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
    at_lifetime_minutes : int
        Время жизни выдаваемого access-токена в минутах.
    rt_lifetime_days : int
        Время жизни выдаваемого refresh-токена и связанной с ним сессии в днях.

    Returns
    -------
    RegisterUserUseCase
        Готовый к использованию Use Case регистрации.
    """
    return RegisterUserUseCase(
        uow=SqlAlchemyUsersUnitOfWork(engine),
        password_hasher=password_hasher,
        compromised_password_checker=compromised_password_checker,
        token_issuer=token_issuer,
        token_hasher=token_hasher,
        at_lifetime_minutes=at_lifetime_minutes,
        rt_lifetime_days=rt_lifetime_days,
    )


def build_login_use_case(
    *,
    engine: AsyncEngine,
    password_hasher: PasswordHasher,
    token_issuer: TokenIssuer,
    token_hasher: TokenHasher,
    at_lifetime_minutes: int,
    rt_lifetime_days: int,
) -> LoginUseCase:
    """Создать Use Case аутентификации пользователя.

    Каждый вызов фабрики создаёт новый экземпляр Use Case
    и новую единицу работы (Unit of Work), что соответствует
    transient-семантике: один вызов Use Case - одна транзакция
    (ADR-0002, п. 1 ответов разработчику).

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
    LoginUseCase
        Готовый к использованию Use Case входа в систему.
    """
    return LoginUseCase(
        uow=SqlAlchemyUsersUnitOfWork(engine),
        password_hasher=password_hasher,
        token_issuer=token_issuer,
        token_hasher=token_hasher,
        at_lifetime_minutes=at_lifetime_minutes,
        rt_lifetime_days=rt_lifetime_days,
    )


def build_refresh_session_use_case(
    *,
    engine: AsyncEngine,
    token_issuer: TokenIssuer,
    token_verifier: TokenVerifier,
    token_hasher: TokenHasher,
    at_lifetime_minutes: int,
    rt_lifetime_days: int,
) -> RefreshSessionUseCase:
    """Создать Use Case обновления пары токенов.

    Каждый вызов фабрики создаёт новый экземпляр Use Case
    и новую единицу работы (Unit of Work), что соответствует
    transient-семантике: один вызов Use Case - одна транзакция
    (ADR-0002, п. 1 ответов разработчику).

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
    RefreshSessionUseCase
        Готовый к использованию Use Case обновления токенов.
    """
    return RefreshSessionUseCase(
        uow=SqlAlchemyUsersUnitOfWork(engine),
        token_issuer=token_issuer,
        token_verifier=token_verifier,
        token_hasher=token_hasher,
        at_lifetime_minutes=at_lifetime_minutes,
        rt_lifetime_days=rt_lifetime_days,
    )


def build_logout_use_case(
    *,
    engine: AsyncEngine,
    token_verifier: TokenVerifier,
    token_blacklist: TokenBlacklist,
) -> LogoutUseCase:
    """Создать Use Case завершения пользовательской сессии.

    Каждый вызов фабрики создаёт новый экземпляр Use Case
    и новую единицу работы (Unit of Work), что соответствует
    transient-семантике: один вызов Use Case - одна транзакция
    (ADR-0002, п. 1 ответов разработчику).

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
    LogoutUseCase
        Готовый к использованию Use Case выхода из системы.
    """
    return LogoutUseCase(
        uow=SqlAlchemyUsersUnitOfWork(engine),
        token_verifier=token_verifier,
        token_blacklist=token_blacklist,
    )


def build_change_password_use_case(
    *,
    engine: AsyncEngine,
    password_hasher: PasswordHasher,
    compromised_password_checker: CompromisedPasswordChecker,
    token_verifier: TokenVerifier,
    token_blacklist: TokenBlacklist,
) -> ChangePasswordUseCase:
    """Создать Use Case смены пароля пользователя.

    Каждый вызов фабрики создаёт новый экземпляр Use Case
    и новую единицу работы (Unit of Work), что соответствует
    transient-семантике: один вызов Use Case - одна транзакция
    (ADR-0002, п. 1 ответов разработчику).

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
    ChangePasswordUseCase
        Готовый к использованию Use Case смены пароля.
    """
    return ChangePasswordUseCase(
        uow=SqlAlchemyUsersUnitOfWork(engine),
        password_hasher=password_hasher,
        compromised_password_checker=compromised_password_checker,
        token_verifier=token_verifier,
        token_blacklist=token_blacklist,
    )


def build_change_profile_use_case(
    *,
    engine: AsyncEngine,
    token_verifier: TokenVerifier,
    token_blacklist: TokenBlacklist,
) -> ChangeProfileUseCase:
    """Создать Use Case изменения профиля пользователя.

    Каждый вызов фабрики создаёт новый экземпляр Use Case
    и новую единицу работы (Unit of Work), что соответствует
    transient-семантике: один вызов Use Case - одна транзакция
    (ADR-0002, п. 1 ответов разработчику).

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
    ChangeProfileUseCase
        Готовый к использованию Use Case изменения профиля.
    """
    return ChangeProfileUseCase(
        uow=SqlAlchemyUsersUnitOfWork(engine),
        token_verifier=token_verifier,
        token_blacklist=token_blacklist,
    )


def build_get_profile_use_case(
    *,
    engine: AsyncEngine,
    token_verifier: TokenVerifier,
    token_blacklist: TokenBlacklist,
) -> GetProfileUseCase:
    """Создать Use Case получения профиля пользователя.

    Каждый вызов фабрики создаёт новый экземпляр Use Case
    и новую единицу работы (Unit of Work), что соответствует
    transient-семантике: один вызов Use Case - одна транзакция
    (ADR-0002, п. 1 ответов разработчику).

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
    GetProfileUseCase
        Готовый к использованию Use Case получения профиля.
    """
    return GetProfileUseCase(
        uow=SqlAlchemyUsersUnitOfWork(engine),
        token_verifier=token_verifier,
        token_blacklist=token_blacklist,
    )
