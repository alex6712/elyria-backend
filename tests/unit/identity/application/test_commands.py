"""Unit-тесты команд Application Layer."""

import pytest
from pydantic import ValidationError

from src.identity.application.commands import (
    LoginCommand,
    LogoutCommand,
    RefreshSessionCommand,
    RegisterUserCommand,
)
from src.identity.application.dto import TokenClaimsDTO
from src.identity.domain.value_objects.username import USERNAME_MAX_LENGTH


class TestLoginCommand:
    """Проверка валидации команды входа в систему."""

    def test_valid_command(self) -> None:
        """Корректная команда создаётся успешно."""
        command = LoginCommand(username="john_doe", password="secureP@ss1!")

        assert command.username == "john_doe"
        assert command.password == "secureP@ss1!"

    @pytest.mark.parametrize("username", ["ab", "a" * (USERNAME_MAX_LENGTH + 1)])
    def test_invalid_username_length(self, username: str) -> None:
        """Username вне допустимой длины отклоняется."""
        with pytest.raises(ValidationError):
            LoginCommand(username=username, password="secureP@ss1!")

    @pytest.mark.parametrize("username", ["user name", "привет", "user@mail"])
    def test_invalid_username_format(self, username: str) -> None:
        """Username с недопустимыми символами отклоняется."""
        with pytest.raises(ValidationError):
            LoginCommand(username=username, password="secureP@ss1!")

    def test_short_password_rejected(self) -> None:
        """Пароль короче 12 символов отклоняется."""
        with pytest.raises(ValidationError):
            LoginCommand(username="john_doe", password="short")

    def test_command_is_frozen(self) -> None:
        """Команда неизменяема после создания."""
        command = LoginCommand(username="john_doe", password="secureP@ss1!")

        with pytest.raises(ValidationError):
            command.password = "another_password"


class TestRegisterUserCommand:
    """Проверка валидации команды регистрации."""

    def test_valid_command(self) -> None:
        """Корректная команда создаётся успешно."""
        command = RegisterUserCommand(
            username="john_doe", password="secureP@ss1!", display_name="John Doe"
        )

        assert command.display_name == "John Doe"

    def test_empty_display_name_rejected(self) -> None:
        """Пустое отображаемое имя отклоняется."""
        with pytest.raises(ValidationError):
            RegisterUserCommand(
                username="john_doe", password="secureP@ss1!", display_name=""
            )

    def test_long_display_name_rejected(self) -> None:
        """Отображаемое имя длиннее 32 символов отклоняется."""
        with pytest.raises(ValidationError):
            RegisterUserCommand(
                username="john_doe",
                password="secureP@ss1!",
                display_name="a" * 33,
            )

    def test_short_password_rejected(self) -> None:
        """Пароль короче 12 символов отклоняется."""
        with pytest.raises(ValidationError):
            RegisterUserCommand(
                username="john_doe", password="short", display_name="John Doe"
            )

    def test_command_is_frozen(self) -> None:
        """Команда неизменяема после создания."""
        command = RegisterUserCommand(
            username="john_doe", password="secureP@ss1!", display_name="John Doe"
        )

        with pytest.raises(ValidationError):
            command.display_name = "Jane Doe"


class TestLogoutCommand:
    """Проверка валидации команды выхода из системы."""

    def test_empty_token_is_valid(self) -> None:
        """Пустой access-токен проходит валидацию схемы
        (решение на стороне use case)."""
        command = LogoutCommand(access_token="")

        assert command.access_token == ""

    def test_command_is_frozen(self) -> None:
        """Команда неизменяема после создания."""
        command = LogoutCommand(access_token="token")

        with pytest.raises(ValidationError):
            command.access_token = "other_token"


class TestRefreshSessionCommand:
    """Проверка валидации команды обновления сессии."""

    def test_empty_token_is_valid(self) -> None:
        """Пустой refresh-токен проходит валидацию схемы."""
        command = RefreshSessionCommand(refresh_token="")

        assert command.refresh_token == ""

    def test_command_is_frozen(self) -> None:
        """Команда неизменяема после создания."""
        command = RefreshSessionCommand(refresh_token="token")

        with pytest.raises(ValidationError):
            command.refresh_token = "other_token"


class TestTokenClaimsDTO:
    """Проверка DTO утверждений токена."""

    def test_created_from_fields(self) -> None:
        """DTO создаётся из всех полей."""
        claims = TokenClaimsDTO(
            user_id="11111111-1111-1111-1111-111111111111",
            expires_at="2026-12-31T00:00:00Z",
            issued_at="2026-01-01T00:00:00Z",
            token_id="22222222-2222-2222-2222-222222222222",
            session_id="33333333-3333-3333-3333-333333333333",
        )

        assert str(claims.user_id) == "11111111-1111-1111-1111-111111111111"
        assert str(claims.session_id) == "33333333-3333-3333-3333-333333333333"

    def test_dto_is_frozen(self) -> None:
        """DTO неизменяемо после создания."""
        claims = TokenClaimsDTO(
            user_id="11111111-1111-1111-1111-111111111111",
            expires_at="2026-12-31T00:00:00Z",
            issued_at="2026-01-01T00:00:00Z",
            token_id="22222222-2222-2222-2222-222222222222",
            session_id="33333333-3333-3333-3333-333333333333",
        )

        with pytest.raises(ValidationError):
            claims.user_id = "44444444-4444-4444-4444-444444444444"
