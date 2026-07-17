from dataclasses import dataclass
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)


@dataclass(frozen=True, slots=True)
class SignatureKeys:
    """Пара ключей подписи JWT.

    Attributes
    ----------
    public : Ed25519PublicKey
        Публичный ключ Ed25519, используемый для проверки подписи JWT.
    private : Ed25519PrivateKey
        Приватный ключ Ed25519, используемый для подписи JWT.
    """

    public: Ed25519PublicKey
    private: Ed25519PrivateKey


class SignatureKeysProvider:
    """Провайдер ключей подписи JWT.

    Загружает и кэширует пару ключей Ed25519 из PEM-файлов.
    Ключи загружаются однократно при первом обращении к
    ``get_signature_keys`` и кэшируются на всё время жизни
    экземпляра.

    Notes
    -----
    Объект является потокобезопасным только при условии, что
    файлы ключей не изменяются во время работы приложения.
    """

    _signature_keys: SignatureKeys | None = None

    def __init__(
        self,
        public_key_path: Path,
        private_key_path: Path,
        private_signature_password: str,
    ) -> None:
        """Инициализировать провайдер путями к файлам ключей.

        Parameters
        ----------
        public_key_path : Path
            Путь к PEM-файлу публичного ключа Ed25519.
        private_key_path : Path
            Путь к PEM-файлу приватного ключа Ed25519.
        private_signature_password : str
            Пароль для расшифровки приватного ключа.
        """
        self._public_key_path = public_key_path
        self._private_key_path = private_key_path
        self._private_signature_password = private_signature_password

    def get_signature_keys(self) -> SignatureKeys:
        """Получить пару ключей подписи JWT.

        При первом вызове загружает ключи из PEM-файлов;
        последующие вызовы возвращают кэшированный экземпляр.

        Returns
        -------
        SignatureKeys
            Пара ключей Ed25519 (публичный и приватный).

        Raises
        ------
        ValueError
            Если загруженный ключ не является ключом Ed25519
            или не удалось расшифровать приватный ключ.
        FileNotFoundError
            Если один из файлов ключей не найден.
        """
        if not self._signature_keys:
            self._signature_keys = self._load_signature_keys()

        return self._signature_keys

    def _load_signature_keys(self) -> SignatureKeys:
        """Загрузить и расшифровать ключи из PEM-файлов.

        Returns
        -------
        SignatureKeys
            Загруженная пара ключей Ed25519.

        Raises
        ------
        ValueError
            Если загруженный ключ не является Ed25519
            или не удалось расшифровать приватный ключ.
        """
        with self._public_key_path.open("rb") as file:
            public_key = serialization.load_pem_public_key(file.read())

        if not isinstance(public_key, Ed25519PublicKey):
            raise ValueError(
                f"Expected Ed25519 public key, got {type(public_key).__name__}."
            )

        with self._private_key_path.open("rb") as file:
            try:
                private_key = serialization.load_pem_private_key(
                    file.read(),
                    password=self._private_signature_password.encode("utf-8"),
                )
            except Exception as e:
                raise ValueError(f"Failed to decrypt private key: {e}") from e

        if not isinstance(private_key, Ed25519PrivateKey):
            raise ValueError(
                f"Expected Ed25519 private key, got {type(private_key).__name__}."
            )

        return SignatureKeys(private=private_key, public=public_key)
