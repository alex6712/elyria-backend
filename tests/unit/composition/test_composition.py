"""Unit-тесты Composition Root: сборка контейнеров и общих ресурсов."""

import tomllib

import pytest
from redis.asyncio import Redis as AsyncRedis
from sqlalchemy.ext.asyncio import AsyncEngine

from src.composition.app_info import (
    APP_NAME,
    APP_SUMMARY,
    APP_VERSION,
    _load_app_version,
)
from src.composition.container import (
    ApplicationContainer,
    build_application_container,
)
from src.composition.engine import build_engine
from src.composition.paths import BASE_DIR
from src.composition.redis import build_redis_client
from src.composition.settings import get_settings
from src.identity.application.use_cases import (
    LoginUseCase,
    LogoutUseCase,
    RefreshSessionUseCase,
    RegisterUserUseCase,
)
from src.identity.composition import IdentityContainer, build_identity_module


class TestAppInfo:
    """Проверка метаданных приложения."""

    def test_app_name(self) -> None:
        """Название приложения задано."""
        assert APP_NAME == "Elyria Backend"

    def test_app_summary(self) -> None:
        """Краткое описание задано."""
        assert APP_SUMMARY

    def test_version_matches_pyproject(self) -> None:
        """Версия приложения совпадает с pyproject.toml."""
        with open(BASE_DIR / "pyproject.toml", "rb") as f:
            expected = str(tomllib.load(f)["project"]["version"])

        assert expected == APP_VERSION

    def test_load_app_version_missing_file_fallback(self, monkeypatch) -> None:
        """Отсутствие pyproject.toml даёт запасную версию."""
        import src.composition.app_info as app_info

        monkeypatch.setattr(app_info, "BASE_DIR", BASE_DIR / "nonexistent")

        assert _load_app_version() == "0.0.0-unknown"


class TestSharedResources:
    """Проверка общих ресурсов приложения."""

    def test_build_engine_cached(self) -> None:
        """build_engine возвращает один и тот же движок."""
        first = build_engine()
        second = build_engine()

        assert first is second
        assert isinstance(first, AsyncEngine)

    def test_build_redis_client_cached(self) -> None:
        """build_redis_client возвращает один и тот же клиент."""
        first = build_redis_client()
        second = build_redis_client()

        assert first is second
        assert isinstance(first, AsyncRedis)

    def test_settings_loaded(self) -> None:
        """Настройки загружаются и содержат API-путь."""
        settings = get_settings()

        assert settings.CURRENT_API_PATH


class TestIdentityModule:
    """Проверка сборки модуля Identity."""

    @pytest.fixture
    def module(self, ed25519_key_pair: tuple) -> IdentityContainer:
        """Собранный модуль Identity на тестовых ключах."""
        public_path, private_path, password, _ = ed25519_key_pair
        return build_identity_module(
            engine=build_engine(),
            redis_client=build_redis_client(),
            issuer=APP_NAME,
            jws_algorithm="EdDSA",
            hmac_secret_key="test-hmac-secret",
            public_key_path=public_path,
            private_key_path=private_path,
            private_signature_password=password,
            access_token_lifetime_minutes=15,
            refresh_token_lifetime_days=30,
        )

    def test_use_case_factories_produce_correct_types(
        self, module: IdentityContainer
    ) -> None:
        """Фабрики возвращают корректные типы Use Cases."""
        assert isinstance(module.register_user(), RegisterUserUseCase)
        assert isinstance(module.login(), LoginUseCase)
        assert isinstance(module.refresh_session(), RefreshSessionUseCase)
        assert isinstance(module.logout(), LogoutUseCase)

    def test_factories_create_fresh_instances(self, module: IdentityContainer) -> None:
        """Каждый вызов фабрики возвращает новый Use Case (transient)."""
        assert module.register_user() is not module.register_user()
        assert module.login() is not module.login()
        assert module.refresh_session() is not module.refresh_session()
        assert module.logout() is not module.logout()


class TestApplicationContainer:
    """Проверка глобального Composition Root."""

    def test_build_application_container(self) -> None:
        """Контейнер приложения собирается и содержит модуль Identity."""
        app_container = build_application_container()

        assert isinstance(app_container, ApplicationContainer)
        assert isinstance(app_container.identity, IdentityContainer)
        assert isinstance(app_container.identity.login(), LoginUseCase)
