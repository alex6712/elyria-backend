"""Общие фикстуры для unit-тестов."""

from collections.abc import Callable
from pathlib import Path

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
)

from src.identity.infrastructure.security import SignatureKeysProvider

PRIVATE_KEY_PASSWORD = "test-signature-password"


@pytest.fixture
def ed25519_key_pair(tmp_path: Path) -> tuple[Path, Path, str, Ed25519PrivateKey]:
    """Создать пару ключей Ed25519 в PEM-файлах во временной директории.

    Приватный ключ шифруется паролем
    ``PRIVATE_KEY_PASSWORD`` и сохраняется в формате PKCS8.

    Returns
    -------
    tuple[Path, Path, str, Ed25519PrivateKey]
        Публичный PEM-путь, приватный PEM-путь, пароль приватного
        ключа и сам приватный ключ.
    """
    private_key = Ed25519PrivateKey.generate()

    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.BestAvailableEncryption(
            PRIVATE_KEY_PASSWORD.encode("utf-8")
        ),
    )
    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    public_key_path = tmp_path / "public_key.pem"
    private_key_path = tmp_path / "private_key.pem"

    public_key_path.write_bytes(public_pem)
    private_key_path.write_bytes(private_pem)

    return public_key_path, private_key_path, PRIVATE_KEY_PASSWORD, private_key


@pytest.fixture
def reset_signature_keys_cache() -> None:
    """Сбросить класс-кэш провайдера ключей до и после теста.

    :class:`SignatureKeysProvider` кэширует ключи в атрибуте класса,
    поэтому без сброса тесты влияют друг на друга.
    """
    SignatureKeysProvider._signature_keys = None
    yield
    SignatureKeysProvider._signature_keys = None


@pytest.fixture
def make_signature_keys_provider(
    reset_signature_keys_cache: None,  # noqa: ARG001
) -> Callable[..., SignatureKeysProvider]:
    """Создать экземпляр :class:`SignatureKeysProvider` с чистым кэшем."""

    def factory(*, public_key_path: Path, private_key_path: Path, password: str):
        return SignatureKeysProvider(
            public_key_path=public_key_path,
            private_key_path=private_key_path,
            private_signature_password=password,
        )

    return factory
