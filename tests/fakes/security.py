"""Фейковые реализации портов безопасности.

Позволяют тестировать Application Layer без криптографических
операций и внешних хранилищ: хеширование, выпуск/проверка токенов
и чёрный список реализуются детерминированными заменителями.
"""

from datetime import datetime
from uuid import UUID

from src.identity.application.dto import TokenClaimsDTO


class FakePasswordHasher:
    """Фейк порта :class:`PasswordHasher`.

    Хеш пароля имеет детерминированный вид ``hash:{password}``.
    Поведение ``verify`` настраивается через ``valid_hashes``.

    Attributes
    ----------
    hash_calls : list[str]
        Пароли, переданные в ``hash``, в порядке вызова.
    valid_hashes : set[str]
        Хеши, для которых ``verify`` возвращает ``True``.
    """

    def __init__(self) -> None:
        self.hash_calls: list[str] = []
        self.valid_hashes: set[str] = set()

    def hash(self, password: str) -> str:
        """Вычислить детерминированный фейковый хеш пароля."""
        self.hash_calls.append(password)
        result = f"hash:{password}"
        self.valid_hashes.add(result)
        return result

    def verify(self, password: str, hash: str) -> bool:
        """Проверить соответствие пароля хешу."""
        return f"hash:{password}" in self.valid_hashes and f"hash:{password}" == hash

    def verify_and_update(self, password: str, hash: str) -> tuple[bool, str | None]:
        """Проверить пароль без необходимости обновления хеша."""
        return self.verify(password, hash), None


class FakeTokenHasher:
    """Фейк порта :class:`TokenHasher`.

    Хеш токена имеет вид ``hashed:{token}``.
    """

    def hash(self, token_str: str) -> str:
        """Вычислить детерминированный фейковый хеш токена."""
        return f"hashed:{token_str}"


class FakeTokenIssuer:
    """Фейк порта :class:`TokenIssuer`.

    Запоминает выпущенные утверждения и возвращает токен вида
    ``token:{token_id}``.

    Attributes
    ----------
    issued : list[TokenClaimsDTO]
        Утверждения, переданные в ``issue``, в порядке вызова.
    """

    def __init__(self) -> None:
        self.issued: list[TokenClaimsDTO] = []

    def issue(self, claims: TokenClaimsDTO) -> str:
        """Выпустить фейковый токен."""
        self.issued.append(claims)
        return f"token:{claims.token_id}"


class FakeTokenVerifier:
    """Фейк порта :class:`TokenVerifier`.

    Поведение настраивается при создании: возвращает ``claims``
    либо выбрасывает ``error`` при каждом вызове ``verify``.

    Attributes
    ----------
    claims : TokenClaimsDTO | None
        Утверждения, возвращаемые ``verify``.
    error : Exception | None
        Исключение, выбрасываемое ``verify``.
    """

    def __init__(
        self,
        claims: TokenClaimsDTO | None = None,
        error: Exception | None = None,
    ) -> None:
        self.claims = claims
        self.error = error

    def verify(self, _token: str) -> TokenClaimsDTO:
        """Проверить фейковый токен."""
        if self.error is not None:
            raise self.error

        if self.claims is None:
            raise AssertionError(
                "FakeTokenVerifier must be configured with claims or error."
            )

        return self.claims


class FakeTokenBlacklist:
    """Фейк порта :class:`TokenBlacklist`.

    Хранит отозванные токены в памяти.

    Attributes
    ----------
    revoked : dict[UUID, datetime]
        Сопоставление идентификатора токена и времени истечения.
    revoke_calls : list[tuple[UUID, datetime]]
        Аргументы вызовов ``revoke`` в порядке вызова.
    """

    def __init__(self) -> None:
        self.revoked: dict[UUID, datetime] = {}
        self.revoke_calls: list[tuple[UUID, datetime]] = []

    async def revoke(self, token_id: UUID, expires_at: datetime) -> None:
        """Пометить токен как отозванный."""
        self.revoked[token_id] = expires_at
        self.revoke_calls.append((token_id, expires_at))

    async def is_revoked(self, token_id: UUID) -> bool:
        """Проверить, отозван ли токен."""
        return token_id in self.revoked
