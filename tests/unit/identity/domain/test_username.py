"""Unit-тесты объекта-значения :class:`Username`."""

from dataclasses import FrozenInstanceError

import pytest

from src.identity.domain.exceptions import (
    InvalidUsernameFormatError,
    InvalidUsernameLengthError,
)
from src.identity.domain.value_objects import Username
from src.identity.domain.value_objects.username import (
    USERNAME_MAX_LENGTH,
    USERNAME_MIN_LENGTH,
)


class TestUsernameValidation:
    """Проверка инвариантов длины и формата имени пользователя."""

    @pytest.mark.parametrize(
        "value",
        [
            "abc",
            "a" * USERNAME_MAX_LENGTH,
            "user_123",
            "user-123",
            "ABC",
            "a0_-",
        ],
    )
    def test_valid_usernames(self, value: str) -> None:
        """Имя пользователя допустимой длины и формата создаётся успешно."""
        username = Username(value)

        assert username.value == value

    @pytest.mark.parametrize(
        "value",
        [
            "ab",
            "a" * (USERNAME_MAX_LENGTH + 1),
            "",
        ],
    )
    def test_invalid_length_raises(self, value: str) -> None:
        """Имя пользователя вне допустимого диапазона длины отклоняется."""
        with pytest.raises(InvalidUsernameLengthError):
            Username(value)

    @pytest.mark.parametrize(
        "value",
        [
            "has space",
            "привет",
            "user@mail",
            "user.name",
            "user!",
            "пользователь_1",
        ],
    )
    def test_invalid_format_raises(self, value: str) -> None:
        """Имя пользователя с недопустимыми символами отклоняется."""
        with pytest.raises(InvalidUsernameFormatError):
            Username(value)

    def test_length_checked_before_format(self) -> None:
        """Проверка длины выполняется до проверки формата."""
        with pytest.raises(InvalidUsernameLengthError):
            Username("н")

    def test_length_boundary_minimum(self) -> None:
        """Минимальная длина имени пользователя допустима."""
        username = Username("a" * USERNAME_MIN_LENGTH)

        assert username.value == "a" * USERNAME_MIN_LENGTH

    def test_length_boundary_maximum(self) -> None:
        """Максимальная длина имени пользователя допустима."""
        username = Username("a" * USERNAME_MAX_LENGTH)

        assert username.value == "a" * USERNAME_MAX_LENGTH


class TestUsernameImmutability:
    """Проверка неизменяемости и представления имени пользователя."""

    def test_value_cannot_be_changed(self) -> None:
        """Попытка изменить значение замороженного объекта отклоняется."""
        username = Username("john_doe")

        with pytest.raises(FrozenInstanceError):
            username.value = "another_name"

    def test_str_returns_value(self) -> None:
        """Строковое представление совпадает со значением."""
        username = Username("john_doe")

        assert str(username) == "john_doe"

    def test_equality_by_value(self) -> None:
        """Два экземпляра с одинаковым значением равны."""
        assert Username("john_doe") == Username("john_doe")

    def test_hash_by_value(self) -> None:
        """Хеш зависит только от значения."""
        assert hash(Username("john_doe")) == hash(Username("john_doe"))
