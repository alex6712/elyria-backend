"""Фикстуры интеграционных тестов: реальные PostgreSQL и Redis.

Тесты помечаются маркером ``integration`` и пропускаются, если
сервисы недоступны (нет ``make services`` или отсутствует Docker).
Схема создаётся применением Alembic-миграций к выделенной тестовой
базе данных ``ELYRIA_TEST_DB_NAME`` (по умолчанию
``elyria_integration_test``).
"""

import asyncio
import os
import subprocess
import sys
from collections.abc import AsyncGenerator
from pathlib import Path

import pytest
from redis.asyncio import Redis as AsyncRedis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from src.composition.settings import Settings

TEST_DB_NAME = os.environ.get("ELYRIA_TEST_DB_NAME", "elyria_integration_test")
TEST_REDIS_DB = 15

BASE_DIR = Path(__file__).resolve().parent.parent.parent


def _settings_kwargs() -> dict:
    """Поля Settings, управляемые переменными окружения (без .env).

    :class:`Settings` не имеет поля ``POSTGRES_HOST`` — хост
    содержится в ``POSTGRES_DSN``, поэтому компоненты подключения
    извлекаются из DSN и хранятся отдельно.
    """
    dsn = os.environ.get(
        "POSTGRES_DSN",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres",
    )
    host, port, user, password = _parse_dsn(dsn)
    env = os.environ
    PG_COMPONENTS["host"] = host
    PG_COMPONENTS["port"] = port
    PG_COMPONENTS["user"] = env.get("POSTGRES_USER", user)
    PG_COMPONENTS["password"] = env.get("POSTGRES_PASSWORD", password)
    return {
        "BACKEND_CORS_ORIGINS": ["http://localhost"],
        "CURRENT_API_PATH": "v1",
        "POSTGRES_USER": PG_COMPONENTS["user"],
        "POSTGRES_PASSWORD": PG_COMPONENTS["password"],
        "POSTGRES_PORT": int(env.get("POSTGRES_PORT", port)),
        "POSTGRES_DB": env.get("POSTGRES_DB", "postgres"),
        "POSTGRES_DSN": "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres",
        "REDIS_HOST": env.get("REDIS_HOST", "localhost"),
        "REDIS_PASSWORD": env.get("REDIS_PASSWORD", ""),
        "REDIS_PORT": int(env.get("REDIS_PORT", "6379")),
        "REDIS_DB": 0,
        "REDIS_URL": "redis://:password@localhost:6379/0",
        "MINIO_HOST": "https://storage.example.com",
        "MINIO_ROOT_USER": "minio",
        "MINIO_ROOT_PASSWORD": "minio-password",
        "MINIO_BUCKET_NAME": "bucket",
        "PRESIGNED_URL_EXPIRATION": 3600,
        "PRIVATE_SIGNATURE_KEY_PASSWORD": "key-password",
        "JWS_ALGORITHM": "EdDSA",
        "ACCESS_TOKEN_LIFETIME_MINUTES": 15,
        "REFRESH_TOKEN_LIFETIME_DAYS": 30,
        "HMAC_SECRET_KEY": "test-hmac-secret",
        "REFRESH_TOKEN_COOKIE_NAME": "elyria_rt",
        "AUTH_COOKIE_PATH": "/v1/auth/refresh",
        "AUTH_COOKIE_SECURE": True,
        "AUTH_COOKIE_SAMESITE": "lax",
        "AUTH_COOKIE_DOMAIN": ".example.com",
    }


PG_COMPONENTS: dict[str, str] = {
    "host": "localhost",
    "port": "5432",
    "user": "postgres",
    "password": "postgres",
}
"""Компоненты подключения к PostgreSQL, извлечённые из POSTGRES_DSN."""


def _parse_dsn(dsn: str) -> tuple[str, str, str, str]:
    """Разобрать postgresql+asyncpg DSN на компоненты подключения.

    Returns
    -------
    tuple[str, str, str, str]
        Хост, порт, пользователь, пароль.
    """
    rest = dsn.split("://", 1)[1]
    credentials, host_part = rest.rsplit("@", 1)
    user, _, password = credentials.partition(":")
    host, _, port = host_part.partition(":")
    port = port.split("/", 1)[0] if "/" in port else port
    return host, port or "5432", user, password or ""


def _build_dsn(*, host: str, port: int, user: str, password: str, db: str) -> str:
    """Собрать строку подключения postgresql+asyncpg."""
    return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db}"


def _admin_dsn(settings: Settings) -> str:
    """Строка подключения к серверу PostgreSQL (база postgres)."""
    return _build_dsn(
        host=PG_COMPONENTS["host"],
        port=settings.POSTGRES_PORT,
        user=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD,
        db="postgres",
    )


def _test_dsn(settings: Settings) -> str:
    """Строка подключения к тестовой базе данных."""
    return _build_dsn(
        host=PG_COMPONENTS["host"],
        port=settings.POSTGRES_PORT,
        user=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD,
        db=TEST_DB_NAME,
    )


async def _services_available(settings: Settings) -> bool:
    """Проверить доступность PostgreSQL и Redis."""
    engine = create_async_engine(_admin_dsn(settings))
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
    except Exception:
        await engine.dispose()
        return False
    await engine.dispose()

    redis_client = AsyncRedis.from_url(
        settings.REDIS_URL.encoded_string(), db=TEST_REDIS_DB
    )
    try:
        await redis_client.ping()
    except Exception:
        await redis_client.aclose()
        return False
    await redis_client.aclose()
    return True


async def _ensure_test_database(settings: Settings) -> None:
    """Создать тестовую базу данных, если она отсутствует."""
    admin_engine = create_async_engine(_admin_dsn(settings))
    async with admin_engine.connect() as connection:
        exists = await connection.scalar(
            text("SELECT 1 FROM pg_database WHERE datname = :name"),
            {"name": TEST_DB_NAME},
        )
        if not exists:
            await connection.execute(text(f'CREATE DATABASE "{TEST_DB_NAME}"'))
    await admin_engine.dispose()


def _run_migrations(settings: Settings) -> None:
    """Применить Alembic-миграции в подпроцессе с переопределённым DSN.

    ``alembic/env.py`` берёт DSN из :func:`get_settings`, поэтому
    переменные окружения переопределяются перед запуском: переменные
    окружения имеют приоритет над ``.env`` в pydantic-settings.
    """
    env = dict(os.environ)
    env.update(
        POSTGRES_PORT=str(settings.POSTGRES_PORT),
        POSTGRES_USER=settings.POSTGRES_USER,
        POSTGRES_PASSWORD=settings.POSTGRES_PASSWORD,
        POSTGRES_DB=TEST_DB_NAME,
        POSTGRES_DSN=_test_dsn(settings),
    )

    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=BASE_DIR,
        env=env,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"Миграции не применились:\n{result.stdout}\n{result.stderr}"
        )


async def _drop_test_database(settings: Settings) -> None:
    """Удалить тестовую базу данных."""
    admin_engine = create_async_engine(_admin_dsn(settings))
    async with admin_engine.connect() as connection:
        await connection.execute(
            text(f'DROP DATABASE IF EXISTS "{TEST_DB_NAME}" WITH (FORCE)')
        )
    await admin_engine.dispose()


@pytest.fixture(scope="session")
def integration_settings() -> Settings:
    """Настройки приложения для интеграционных тестов.

    Управляются переменными окружения (``POSTGRES_HOST`` и т. п.),
    файл ``.env`` не используется.
    """
    return Settings(**_settings_kwargs())


@pytest.fixture(scope="session")
def pg_engine(integration_settings: Settings) -> AsyncEngine:
    """Движок к тестовой базе с применёнными миграциями.

    Пропускает сессию, если PostgreSQL или Redis недоступны.
    """
    if not asyncio.run(_services_available(integration_settings)):
        pytest.skip("PostgreSQL/Redis недоступны: запустите make services")

    asyncio.run(_ensure_test_database(integration_settings))
    _run_migrations(integration_settings)

    engine = create_async_engine(_test_dsn(integration_settings))

    yield engine

    asyncio.run(engine.dispose())
    asyncio.run(_drop_test_database(integration_settings))


@pytest.fixture(autouse=True)
async def clean_db(pg_engine: AsyncEngine) -> AsyncGenerator[None]:
    """Очистить все таблицы перед каждым интеграционным тестом."""
    async with pg_engine.begin() as connection:
        table_names = await connection.scalars(
            text(
                "SELECT tablename FROM pg_tables "
                "WHERE schemaname = 'public' AND tablename != 'alembic_version'"
            )
        )
        tables = ", ".join(f'"{name}"' for name in table_names)
        await connection.execute(
            text(f"TRUNCATE TABLE {tables} RESTART IDENTITY CASCADE")
        )

    yield


@pytest.fixture
async def redis_client(integration_settings: Settings) -> AsyncGenerator[AsyncRedis]:
    """Клиент Redis с очисткой выделенной тестовой базы.

    Пропускает тест, если Redis недоступен.
    """
    client = AsyncRedis.from_url(
        integration_settings.REDIS_URL.encoded_string(),
        db=TEST_REDIS_DB,
    )
    try:
        await client.ping()
    except Exception:
        await client.aclose()
        pytest.skip("Redis недоступен: запустите make services")

    await client.flushdb()

    yield client

    await client.flushdb()
    await client.aclose()
