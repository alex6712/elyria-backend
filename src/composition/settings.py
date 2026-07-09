from functools import lru_cache
from pathlib import Path
from typing import Any, Literal, Self

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ec import (
    EllipticCurvePrivateKey,
    EllipticCurvePublicKey,
)
from pydantic import (
    AnyHttpUrl,
    EmailStr,
    PostgresDsn,
    RedisDsn,
    SkipValidation,
    TypeAdapter,
    ValidationError,
    field_validator,
    model_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent
"""Абсолютный путь к корню проекта.

Вычисляется от расположения текущего модуля (``src/composition/settings.py``),
а не от текущей рабочей директории процесса (``os.getcwd()``). Это гарантирует
корректное разрешение путей до ``.env`` и файлов ключей независимо от того,
откуда запущен процесс (напрямую, через systemd с другим ``WorkingDirectory``,
из Docker-контейнера или из тестов).

Используется как база для построения путей к ``.env`` и директории ``keys/``.
"""

_CORS_LIST_ADAPTER = TypeAdapter(list[str])
"""Валидатор для приведения сырых данных к ``list[str]``.

Используется в :func:`Settings._assemble_cors_origins` для валидации
JSON-массива (``validate_json``) или уже готового списка (``validate_python``)
источников CORS. Вынесен на уровень модуля, чтобы не создавать адаптер
заново при каждом вызове валидатора.

При несоответствии данных типу ``list[str]`` выбрасывает
``pydantic.ValidationError``.
"""


class Settings(BaseSettings):
    """Конфигурация приложения.

    Загружает и валидирует настройки из ``.env``-файла в корне проекта.
    Разделена на логические группы:

    * **Application** - метаданные приложения (имя, версия, описание);
    * **Administration** - контактная информация ответственного лица;
    * **API** - CORS, текущий путь версии API;
    * **Database** - параметры подключения к PostgreSQL;
    * **Cache** - параметры подключения к Redis;
    * **Storage** - параметры подключения к MinIO (S3-совместимое хранилище);
    * **Auth** - JWT-токены, куки, ключи подписи.

    Поля с грифом безопасности (пароли, ключи) должны быть исключены
    из VCS и задаваться исключительно через переменные окружения
    или ``.env``-файл.

    See Also
    --------
    get_settings : Фабрика с кешированием для получения единственного
                   экземпляра настроек.
    """

    APP_NAME: str
    """Название приложения."""

    APP_VERSION: str
    """Текущая версия приложения."""

    APP_DESCRIPTION: str
    """Полное описание приложения."""

    APP_SUMMARY: str
    """Краткое описание приложения."""

    ADMIN_NAME: str
    """Имя ответственного лица."""

    ADMIN_EMAIL: EmailStr
    """Email для связи с ответственным лицом."""

    ROBOTS_CONTENT: str
    """Текст файла robots.txt."""

    BACKEND_CORS_ORIGINS: list[str]
    """Список источников для CORS Middleware.

    Принимает JSON-массив (``'["https://a.com"]'``) или строку
    с разделителями-запятыми (``'https://a.com, https://b.com'``).
    """

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def _assemble_cors_origins(cls, value: Any) -> list[str]:
        """Нормализует список CORS-источников.

        Допускает два формата ввода:

        * **JSON-массив** - ``'["https://a.com","https://b.com"]'``;
        * **Строка с разделителями-запятыми** - ``'https://a.com, https://b.com'``.

        Поскольку ``enable_decoding=False`` отключает встроенный JSON-декодинг
        pydantic-settings, парсинг и валидация JSON-массива делегируются
        отдельному ``TypeAdapter(list[str])``, что даёт строго типизированный
        результат без ``Any`` в теле функции.

        Parameters
        ----------
        value : Any
            Сырое значение из переменной окружения.

        Returns
        -------
        list[str]
            Нормализованный список разрешённых источников.

        Raises
        ------
        ValueError
            Если значение - невалидный JSON, JSON/список содержит не-строки,
            либо тип значения не поддерживается.
        """
        if isinstance(value, str):
            stripped = value.strip()

            if stripped.startswith("["):
                try:
                    return _CORS_LIST_ADAPTER.validate_json(stripped)
                except ValidationError as e:
                    raise ValueError(f"Invalid BACKEND_CORS_ORIGINS JSON: {e}") from e

            return [i.strip() for i in stripped.split(",") if i.strip()]

        try:
            return _CORS_LIST_ADAPTER.validate_python(value)
        except ValidationError as e:
            raise ValueError(f"Invalid BACKEND_CORS_ORIGINS: {e}") from e

    CURRENT_API_PATH: str
    """Префикс URL для всех эндпоинтов текущей версии API."""

    POSTGRES_USER: str
    """Пользователь базы данных для подключения."""

    POSTGRES_PASSWORD: str
    """Пароль пользователя для подключения к базе данных."""

    POSTGRES_PORT: int
    """Порт базы данных."""

    POSTGRES_DB: str
    """Название базы данных."""

    POSTGRES_DSN: PostgresDsn
    """Строка подключения (ссылка) к базе данных."""

    REDIS_HOST: str
    """Хост Redis."""

    REDIS_PASSWORD: str
    """Пароль для подключения к Redis."""

    REDIS_PORT: int
    """Порт Redis."""

    REDIS_DB: int
    """Номер базы данных Redis."""

    REDIS_URL: RedisDsn
    """URL Redis."""

    MINIO_HOST: AnyHttpUrl
    """Наименование хоста, на котором размещён сервер MinIO."""

    MINIO_ROOT_USER: str
    """MinIO Access key (root пользователь)."""

    MINIO_ROOT_PASSWORD: str
    """MinIO Secret key (пароль root пользователя)."""

    MINIO_BUCKET_NAME: str
    """Наименование бакета на сервере MinIO."""

    PRESIGNED_URL_EXPIRATION: int
    """Базовое время жизни Presigned URL на загрузку файлов (в секундах)."""

    PRIVATE_SIGNATURE_KEY_PASSWORD: str
    """Пароль для дешифровки зашифрованного приватного ключа подписи JWT."""

    JWT_ALGORITHM: str
    """Алгоритм кодирования JWT."""

    ACCESS_TOKEN_LIFETIME_MINUTES: int
    """Время жизни access-токена в минутах."""

    REFRESH_TOKEN_LIFETIME_DAYS: int
    """Время жизни refresh-токена в днях."""

    HMAC_SECRET_KEY: str
    """Секретный ключ хеширования токенов обновления."""

    REFRESH_TOKEN_COOKIE_NAME: str
    """Имя cookie, в котором хранится JWT refresh-токен."""

    AUTH_COOKIE_PATH: str
    """Значение атрибута ``Path`` для auth-cookie."""

    AUTH_COOKIE_SECURE: bool
    """Значение атрибута ``Secure`` для auth-cookie.

    Должно быть ``True`` в production-окружении.
    """

    AUTH_COOKIE_SAMESITE: Literal["lax", "strict", "none"]
    """Значение атрибута ``SameSite`` для auth-cookie.

    Допустимые значения: ``"lax"``, ``"strict"``, ``"none"``.
    """

    AUTH_COOKIE_DOMAIN: str | None
    """Значение атрибута ``Domain`` для auth-cookie.

    При ``None`` cookie устанавливается только на текущий хост.
    Для шаринга между поддоменами используется значение
    вида ``".example.com"``.
    """

    @field_validator("AUTH_COOKIE_SAMESITE", mode="before")
    @classmethod
    def _validate_auth_cookie_samesite(cls, value: Any) -> str:
        """Нормализует и валидирует значение ``SameSite`` для auth-cookie.

        Приводит значение к нижнему регистру и обрезает пробелы.
        Допустимы только три значения: ``"lax"``, ``"strict"``, ``"none"``.

        Parameters
        ----------
        value : Any
            Сырое значение из переменной окружения.

        Returns
        -------
        str
            Нормализованная строка ``SameSite``.

        Raises
        ------
        ValueError
            Если значение не является строкой или не входит в список
            допустимых значений.
        """
        if not isinstance(value, str):
            raise ValueError(
                f"AUTH_COOKIE_SAMESITE must be a string, got {type(value).__name__}."
            )

        normalized = value.strip().lower()

        if normalized not in {"lax", "strict", "none"}:
            raise ValueError(
                f"AUTH_COOKIE_SAMESITE must be one of 'lax', 'strict', 'none'; got {value!r}."
            )

        return normalized

    @field_validator("AUTH_COOKIE_DOMAIN", mode="before")
    @classmethod
    def _normalize_auth_cookie_domain(cls, value: Any | None) -> str | None:
        """Нормализует значение ``Domain`` для auth-cookie.

        ``None`` (или отсутствие переменной) пропускается без изменений -
        в этом случае cookie устанавливается только на текущий хост.
        Строковые значения обрезаются по краям; пустая строка после обрезки
        приводится к ``None``.

        Parameters
        ----------
        value : Any | None
            Сырое значение из переменной окружения.

        Returns
        -------
        str | None
            Домен для cookie или ``None``.

        Raises
        ------
        ValueError
            Если значение не является строкой и не ``None``.
        """
        if value is None:
            return None

        if not isinstance(value, str):
            raise ValueError(
                f"AUTH_COOKIE_DOMAIN must be a string or null, got {type(value).__name__}."
            )

        return value.strip() or None

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        enable_decoding=False,
        extra="ignore",
    )

    PRIVATE_SIGNATURE_KEY: SkipValidation[EllipticCurvePrivateKey] = None  # type: ignore
    """Приватный ключ подписи JWT (EC P-256).

    Загружается из ``keys/private_key.pem.enc`` в ``load_keys``.
    Расшифровывается с использованием ``PRIVATE_SIGNATURE_KEY_PASSWORD``.
    """

    PUBLIC_SIGNATURE_KEY: SkipValidation[EllipticCurvePublicKey] = None  # type: ignore
    """Публичный ключ подписи JWT (EC P-256).

    Загружается из ``keys/public_key.pem`` в ``load_keys``.
    """

    @model_validator(mode="after")
    def load_keys(self) -> Self:
        """Загружает и дешифрует ключи подписи JWT с диска.

        Выполняется после инициализации всех полей модели:

        1. Читает публичный ключ из ``keys/public_key.pem``;
        2. Читает и дешифрует приватный ключ из ``keys/private_key.pem.enc``
           с использованием ``PRIVATE_SIGNATURE_KEY_PASSWORD``;
        3. Сохраняет полученные объекты ключей в соответствующие поля.

        Оба файла должны существовать и содержать корректные ключи
        в формате PEM (алгоритм EC P-256). Зашифрованный приватный ключ
        должен быть зашифрован алгоритмом, поддерживаемым OpenSSL.

        Raises
        ------
        ValueError
            Если файл ключа не найден, не удалось расшифровать приватный
            ключ или тип загруженного ключа не соответствует ожидаемому
            (``EllipticCurvePrivateKey`` / ``EllipticCurvePublicKey``).
        """
        public_key_path = BASE_DIR / "keys" / "public_key.pem"

        with open(public_key_path, "rb") as public_key_file:
            public_key = serialization.load_pem_public_key(public_key_file.read())

            if not isinstance(public_key, EllipticCurvePublicKey):
                raise ValueError(
                    f"Expected EC public key, got {type(public_key).__name__}"
                )

        self.PUBLIC_SIGNATURE_KEY = public_key  # type: ignore

        if not self.PRIVATE_SIGNATURE_KEY_PASSWORD:
            raise ValueError(
                "PRIVATE_SIGNATURE_KEY_PASSWORD is required to load the private key"
            )

        private_key_path = BASE_DIR / "keys" / "private_key.pem.enc"

        with open(private_key_path, "rb") as private_key_file:
            try:
                private_key = serialization.load_pem_private_key(
                    private_key_file.read(),
                    password=self.PRIVATE_SIGNATURE_KEY_PASSWORD.encode("utf-8"),
                )
            except Exception as e:
                raise ValueError(f"Failed to decrypt private key: {e}")

            if not isinstance(private_key, EllipticCurvePrivateKey):
                raise ValueError(
                    f"Expected EC private key, got {type(private_key).__name__}"
                )

        self.PRIVATE_SIGNATURE_KEY = private_key  # type: ignore

        return self


@lru_cache
def get_settings() -> Settings:
    """Получение объекта настроек приложения.

    Returns
    -------
    Settings
        Глобальный объект настроек приложения.
    """
    return Settings()  # type: ignore
