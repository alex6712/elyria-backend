"""Фейки портов безопасности для unit-тестов."""

from src.shared.application.dto import TokenClaimsDTO
from src.users.domain.value_objects import Password


class FakePasswordHasher:
    """Фейк хеширования паролей для тестов.

    Детерминированный: ``hash(password)`` возвращает
    ``"hash:<password>"`` без реального криптографического хеширования.
    """

    def __init__(self) -> None:
        self.hash_calls: list[Password] = []

    def hash(self, password: Password) -> str:
        self.hash_calls.append(password)
        return f"hash:{password.reveal()}"

    def verify(self, password: Password, hash: str) -> bool:
        return hash == f"hash:{password.reveal()}"

    def verify_and_update(
        self, password: Password, hash: str
    ) -> tuple[bool, str | None]:
        return (self.verify(password, hash), None)


class FakeTokenIssuer:
    """Фейк выпуска токенов для тестов.

    Детерминированный: ``issue(claims)`` возвращает
    ``"token:<token_id>"``.
    """

    def __init__(self) -> None:
        self.issued: list[TokenClaimsDTO] = []

    def issue(self, claims: TokenClaimsDTO) -> str:
        self.issued.append(claims)
        return f"token:{claims.token_id}"


class FakeTokenHasher:
    """Фейк хеширования токенов для тестов.

    Детерминированный: ``hash(token)`` возвращает ``"hashed:<token>"``.
    """

    def hash(self, token_str: str) -> str:
        return f"hashed:{token_str}"


class FakeCompromisedPasswordChecker:
    """Фейк проверки пароля на утечки данных для тестов.

    По умолчанию пароль считается безопасным.
    Установите ``is_compromised_result = True`` для тестирования
    ``(CompromisedPasswordError)``.
    """

    def __init__(self) -> None:
        self.is_compromised_result = False

    async def is_compromised(self, password: Password) -> bool:  # noqa: ARG002
        return self.is_compromised_result
