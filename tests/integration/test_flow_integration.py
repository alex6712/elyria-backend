"""Интеграционный сквозной тест: регистрация → вход → обновление → выход."""

import pytest
from redis.asyncio import Redis as AsyncRedis
from sqlalchemy.ext.asyncio import AsyncEngine

from src.composition.app_info import APP_NAME
from src.identity.application.commands import (
    LoginCommand,
    LogoutCommand,
    RefreshSessionCommand,
    RegisterUserCommand,
)
from src.identity.application.exceptions import (
    IncorrectUsernameOrPasswordError,
    SessionNotFoundError,
)
from src.identity.application.use_cases import (
    LoginUseCase,
    LogoutUseCase,
    RefreshSessionUseCase,
    RegisterUserUseCase,
)
from src.identity.composition import build_identity_module
from src.identity.infrastructure.persistence.redis_token_blacklist import (
    RedisTokenBlacklist,
)
from src.identity.infrastructure.security import JwtTokenVerifier

pytestmark = pytest.mark.integration

USERNAME = "e2e_user"
PASSWORD = "secureP@ss1!"


class TestEndToEndFlow:
    """Сквозной сценарий аутентификации на реальных сервисах."""

    @pytest.fixture
    def use_cases(
        self,
        pg_engine: AsyncEngine,
        redis_client: AsyncRedis,
        ed25519_key_pair: tuple,
    ) -> dict[str, object]:
        """Реальные Use Cases на тестовой БД, Redis и ключах."""
        public_path, private_path, password, private_key = ed25519_key_pair
        module = build_identity_module(
            engine=pg_engine,
            redis_client=redis_client,
            issuer=APP_NAME,
            jws_algorithm="EdDSA",
            hmac_secret_key="test-hmac-secret",
            public_key_path=public_path,
            private_key_path=private_path,
            private_signature_password=password,
            access_token_lifetime_minutes=15,
            refresh_token_lifetime_days=30,
        )
        return {
            "register": module.register_user(),
            "login": module.login(),
            "refresh": module.refresh_session(),
            "logout": module.logout(),
            "public_key": private_key.public_key(),
        }

    async def test_full_flow(
        self, use_cases: dict[str, object], redis_client: AsyncRedis
    ) -> None:
        """Регистрация, вход, обновление пары и выход работают вместе."""
        register: RegisterUserUseCase = use_cases["register"]
        login: LoginUseCase = use_cases["login"]
        refresh: RefreshSessionUseCase = use_cases["refresh"]
        logout: LogoutUseCase = use_cases["logout"]

        registered = await register.execute(
            RegisterUserCommand(username=USERNAME, password=PASSWORD)
        )
        assert registered.access_token
        assert registered.refresh_token

        logged_in = await login.execute(
            LoginCommand(username=USERNAME, password=PASSWORD)
        )
        assert logged_in.access_token != registered.access_token

        refreshed = await refresh.execute(
            RefreshSessionCommand(refresh_token=logged_in.refresh_token)
        )
        assert refreshed.access_token
        assert refreshed.refresh_token != logged_in.refresh_token

        await logout.execute(LogoutCommand(access_token=refreshed.access_token))

        verifier = JwtTokenVerifier(APP_NAME, use_cases["public_key"], "EdDSA")
        claims = verifier.verify(refreshed.access_token)
        blacklist = RedisTokenBlacklist(redis_client)
        assert await blacklist.is_revoked(claims.token_id) is True

    async def test_wrong_password_rejected(self, use_cases: dict[str, object]) -> None:
        """Неверный пароль отклоняется при входе."""
        register: RegisterUserUseCase = use_cases["register"]
        login: LoginUseCase = use_cases["login"]

        await register.execute(
            RegisterUserCommand(username=USERNAME, password=PASSWORD)
        )

        with pytest.raises(IncorrectUsernameOrPasswordError):
            await login.execute(
                LoginCommand(username=USERNAME, password="wrong-password")
            )

    async def test_refresh_rotation_invalidates_old_token(
        self, use_cases: dict[str, object]
    ) -> None:
        """Повторное использование старого refresh-токена отклоняется."""
        register: RegisterUserUseCase = use_cases["register"]
        login: LoginUseCase = use_cases["login"]
        refresh: RefreshSessionUseCase = use_cases["refresh"]

        await register.execute(
            RegisterUserCommand(username=USERNAME, password=PASSWORD)
        )
        logged_in = await login.execute(
            LoginCommand(username=USERNAME, password=PASSWORD)
        )

        await refresh.execute(
            RefreshSessionCommand(refresh_token=logged_in.refresh_token)
        )

        with pytest.raises(SessionNotFoundError):
            await refresh.execute(
                RefreshSessionCommand(refresh_token=logged_in.refresh_token)
            )

    async def test_double_logout_is_idempotent(
        self, use_cases: dict[str, object]
    ) -> None:
        """Повторный выход с тем же токеном не падает."""
        register: RegisterUserUseCase = use_cases["register"]
        logout: LogoutUseCase = use_cases["logout"]

        registered = await register.execute(
            RegisterUserCommand(username=USERNAME, password=PASSWORD)
        )

        await logout.execute(LogoutCommand(access_token=registered.access_token))
        await logout.execute(LogoutCommand(access_token=registered.access_token))
