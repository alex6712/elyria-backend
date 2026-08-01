from sqlalchemy.ext.asyncio import AsyncEngine

from src.users.application.ports.persistence import TokenBlacklist
from src.users.application.ports.security import (
    PasswordHasher,
    TokenHasher,
    TokenIssuer,
    TokenVerifier,
)
from src.users.application.use_cases import (
    LoginUseCase,
    LogoutUseCase,
    RefreshSessionUseCase,
    RegisterUserUseCase,
)
from src.users.infrastructure import SqlAlchemyUsersUnitOfWork


def build_register_user_use_case(
    *,
    engine: AsyncEngine,
    password_hasher: PasswordHasher,
    token_issuer: TokenIssuer,
    token_hasher: TokenHasher,
    at_lifetime_minutes: int,
    rt_lifetime_days: int,
) -> RegisterUserUseCase:
    """Создать Use Case регистрации нового пользователя.

    Каждый вызов фабрики создаёт новый экземпляр Use Case
    и новую единицу работы (Unit of Work), что соответствует
    transient-семантике: один вызов Use Case — одна транзакция
    (ADR-0002, п. 1 ответов разработчику).

    Parameters
    ----------
    engine : AsyncEngine
        Асинхронный движок SQLAlchemy для открытия транзакций.
    password_hasher : PasswordHasher
        Сервис хеширования паролей.
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
    transient-семантике: один вызов Use Case — одна транзакция
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
    transient-семантике: один вызов Use Case — одна транзакция
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
    transient-семантике: один вызов Use Case — одна транзакция
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
