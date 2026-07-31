"""Unit-тесты конфигурации приложения (Settings)."""

import pytest
from pydantic import ValidationError

from src.composition.settings import Settings


def make_settings(**overrides) -> Settings:
    """Создать настройки с тестовыми значениями.

    Parameters
    ----------
    **overrides : dict
        Поля, переопределяемые относительно базового набора.

    Returns
    -------
    Settings
        Экземпляр настроек.
    """
    base = {
        "BACKEND_CORS_ORIGINS": ["http://localhost:5173"],
        "CURRENT_API_PATH": "v1",
        "POSTGRES_USER": "postgres",
        "POSTGRES_PASSWORD": "password",
        "POSTGRES_PORT": 5432,
        "POSTGRES_DB": "postgres",
        "POSTGRES_DSN": "postgresql+asyncpg://postgres:password@localhost:5432/postgres",
        "REDIS_HOST": "localhost",
        "REDIS_PASSWORD": "redis-password",
        "REDIS_PORT": 6379,
        "REDIS_DB": 0,
        "REDIS_URL": "redis://:redis-password@localhost:6379/0",
        "MINIO_HOST": "https://storage.example.com",
        "MINIO_ROOT_USER": "minio-user",
        "MINIO_ROOT_PASSWORD": "minio-password",
        "MINIO_BUCKET_NAME": "bucket",
        "PRESIGNED_URL_EXPIRATION": 3600,
        "PRIVATE_SIGNATURE_KEY_PASSWORD": "key-password",
        "JWS_ALGORITHM": "EdDSA",
        "ACCESS_TOKEN_LIFETIME_MINUTES": 15,
        "REFRESH_TOKEN_LIFETIME_DAYS": 30,
        "HMAC_SECRET_KEY": "hmac-secret",
        "REFRESH_TOKEN_COOKIE_NAME": "elyria_rt",
        "AUTH_COOKIE_PATH": "/v1/auth/refresh",
        "AUTH_COOKIE_SECURE": True,
        "AUTH_COOKIE_SAMESITE": "lax",
        "AUTH_COOKIE_DOMAIN": ".example.com",
    }
    base.update(overrides)
    return Settings(**base)


class TestSettingsBasics:
    """Базовые настройки загружаются и валидируются."""

    def test_all_fields_loaded(self) -> None:
        """Все поля базового набора корректно загружаются."""
        settings = make_settings()

        assert settings.CURRENT_API_PATH == "v1"
        assert settings.POSTGRES_PORT == 5432
        assert settings.ACCESS_TOKEN_LIFETIME_MINUTES == 15
        assert settings.REFRESH_TOKEN_LIFETIME_DAYS == 30
        assert settings.AUTH_COOKIE_SAMESITE == "lax"
        assert settings.AUTH_COOKIE_SECURE is True

    def test_dsn_fields_are_urls(self) -> None:
        """DSN-поля сохраняют строковые значения URL."""
        settings = make_settings()

        assert str(settings.POSTGRES_DSN) == (
            "postgresql+asyncpg://postgres:password@localhost:5432/postgres"
        )
        assert str(settings.REDIS_URL) == "redis://:redis-password@localhost:6379/0"

    def test_minio_host_requires_http(self) -> None:
        """MINIO_HOST без схемы отклоняется."""
        with pytest.raises(ValidationError):
            make_settings(MINIO_HOST="storage.example.com")

    def test_cookie_samesite_invalid_raises(self) -> None:
        """Недопустимое значение SameSite отклоняется."""
        with pytest.raises(ValidationError):
            make_settings(AUTH_COOKIE_SAMESITE="unsafe")


class TestCorsOrigins:
    """Проверка валидатора BACKEND_CORS_ORIGINS."""

    def test_comma_separated_string(self) -> None:
        """Строка с запятыми разбивается на список."""
        settings = make_settings(
            BACKEND_CORS_ORIGINS="http://a.com, https://b.com, http://a.com"
        )

        assert settings.BACKEND_CORS_ORIGINS == [
            "http://a.com",
            "https://b.com",
            "http://a.com",
        ]

    def test_json_array_string(self) -> None:
        """JSON-массив строк разбирается в список."""
        settings = make_settings(
            BACKEND_CORS_ORIGINS='["http://a.com", "https://b.com"]'
        )

        assert settings.BACKEND_CORS_ORIGINS == ["http://a.com", "https://b.com"]

    def test_empty_string_yields_empty_list(self) -> None:
        """Пустая строка даёт пустой список."""
        settings = make_settings(BACKEND_CORS_ORIGINS="   ")

        assert settings.BACKEND_CORS_ORIGINS == []

    def test_invalid_json_raises(self) -> None:
        """Некорректный JSON-массив отклоняется."""
        with pytest.raises(ValidationError, match="BACKEND_CORS_ORIGINS"):
            make_settings(BACKEND_CORS_ORIGINS='["http://a.com"')

    def test_list_with_non_strings_raises(self) -> None:
        """Список с не-строками отклоняется."""
        with pytest.raises(ValidationError):
            make_settings(BACKEND_CORS_ORIGINS=["http://a.com", 42])

    def test_non_string_non_list_raises(self) -> None:
        """Неподдерживаемый тип значения отклоняется."""
        with pytest.raises(ValidationError):
            make_settings(BACKEND_CORS_ORIGINS=42)


class TestCookieSamesite:
    """Проверка валидатора AUTH_COOKIE_SAMESITE."""

    def test_uppercase_normalized(self) -> None:
        """Верхний регистр приводится к нижнему."""
        settings = make_settings(AUTH_COOKIE_SAMESITE="LAX")

        assert settings.AUTH_COOKIE_SAMESITE == "lax"

    def test_surrounding_whitespace_stripped(self) -> None:
        """Пробелы вокруг значения обрезаются."""
        settings = make_settings(AUTH_COOKIE_SAMESITE="  strict  ")

        assert settings.AUTH_COOKIE_SAMESITE == "strict"

    def test_none_accepted(self) -> None:
        """Значение ``none`` допустимо."""
        settings = make_settings(AUTH_COOKIE_SAMESITE="none")

        assert settings.AUTH_COOKIE_SAMESITE == "none"

    def test_invalid_value_raises(self) -> None:
        """Значение вне списка отклоняется с понятным сообщением."""
        with pytest.raises(ValidationError, match="AUTH_COOKIE_SAMESITE"):
            make_settings(AUTH_COOKIE_SAMESITE="unsafe")

    def test_non_string_raises(self) -> None:
        """Не-строка отклоняется."""
        with pytest.raises(ValidationError, match="AUTH_COOKIE_SAMESITE"):
            make_settings(AUTH_COOKIE_SAMESITE=123)


class TestCookieDomain:
    """Проверка валидатора AUTH_COOKIE_DOMAIN."""

    def test_none_preserved(self) -> None:
        """None остаётся None."""
        settings = make_settings(AUTH_COOKIE_DOMAIN=None)

        assert settings.AUTH_COOKIE_DOMAIN is None

    def test_whitespace_stripped(self) -> None:
        """Пробелы вокруг домена обрезаются."""
        settings = make_settings(AUTH_COOKIE_DOMAIN="  .example.com  ")

        assert settings.AUTH_COOKIE_DOMAIN == ".example.com"

    def test_empty_string_yields_none(self) -> None:
        """Пустая строка приводится к None."""
        settings = make_settings(AUTH_COOKIE_DOMAIN="")

        assert settings.AUTH_COOKIE_DOMAIN is None

    def test_non_string_raises(self) -> None:
        """Не-строка отклоняется."""
        with pytest.raises(ValidationError, match="AUTH_COOKIE_DOMAIN"):
            make_settings(AUTH_COOKIE_DOMAIN=123)
