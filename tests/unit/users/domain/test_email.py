"""Unit-тесты ``Email`` (value object)."""

import pytest

from src.users.domain.exceptions import (
    InvalidEmailFormatError,
    InvalidEmailLengthError,
)
from src.users.domain.value_objects.email import (
    EMAIL_MAX_LENGTH,
    EMAIL_MIN_LENGTH,
    EMAIL_PATTERN,
    Email,
)


class TestEmailSuccess:
    """Валидные адреса электронной почты."""

    def test_simple_local_domain(self) -> None:
        email = Email("user@example.com")
        assert email.value == "user@example.com"

    def test_digits_in_local(self) -> None:
        email = Email("123@domain.org")
        assert email.value == "123@domain.org"

    def test_special_chars_in_local(self) -> None:
        email = Email("first.last+tag@domain.co.uk")
        assert email.value == "first.last+tag@domain.co.uk"

    def test_hyphen_in_domain(self) -> None:
        email = Email("user@my-domain.com")
        assert email.value == "user@my-domain.com"

    def test_underscore_in_local(self) -> None:
        email = Email("first_name@domain.com")
        assert email.value == "first_name@domain.com"

    def test_percent_in_local(self) -> None:
        email = Email("100%real@domain.com")
        assert email.value == "100%real@domain.com"

    def test_min_length_address(self) -> None:
        email = Email("a@b.co")
        assert email.value == "a@b.co"

    def test_max_length_address(self) -> None:
        local = "a" * 64
        domain_fill = EMAIL_MAX_LENGTH - len(local) - len("@co") - 1
        full = f"{local}@{'b' * domain_fill}.co"
        assert len(full) == 254
        email = Email(full)
        assert email.value == full

    def test_uppercase_normalized_to_lowercase(self) -> None:
        email = Email("User@Example.COM")
        assert email.value == "user@example.com"

    def test_leading_trailing_whitespace_stripped(self) -> None:
        email = Email("  user@example.com  ")
        assert email.value == "user@example.com"

    def test_frozen(self) -> None:
        email = Email("user@example.com")
        with pytest.raises(AttributeError):
            email.value = "new@example.com"  # type: ignore[misc]


class TestEmailFailures:
    """Невалидные адреса электронной почты."""

    def test_too_short(self) -> None:
        with pytest.raises(InvalidEmailLengthError):
            _ = Email("")

    def test_below_min_length(self) -> None:
        with pytest.raises(InvalidEmailLengthError):
            _ = Email("a@")  # len == 2 < EMAIL_MIN_LENGTH; проверка длины идёт первой

    def test_above_max_length(self) -> None:
        local = "a" * 65
        domain = "b" * 187
        full = f"{local}@{domain}.com"
        assert len(full) > EMAIL_MAX_LENGTH
        with pytest.raises(InvalidEmailLengthError):
            _ = Email(full)

    def test_no_at_sign(self) -> None:
        with pytest.raises(InvalidEmailFormatError):
            _ = Email("userexample.com")

    def test_no_domain(self) -> None:
        with pytest.raises(InvalidEmailFormatError):
            _ = Email("user@")

    def test_no_tld(self) -> None:
        with pytest.raises(InvalidEmailFormatError):
            _ = Email("user@domain")

    def test_single_char_tld(self) -> None:
        with pytest.raises(InvalidEmailFormatError):
            _ = Email("user@domain.c")

    def test_space_in_local(self) -> None:
        with pytest.raises(InvalidEmailFormatError):
            _ = Email("user name@example.com")

    def test_spaces_not_stripped_before_validation(self) -> None:
        with pytest.raises(InvalidEmailLengthError):
            _ = Email("  ")  # strip -> "" -> too short


class TestEmailNormalization:
    """Нормализация адресов."""

    def test_whitespace_is_stripped(self) -> None:
        email = Email("  user@example.com  ")
        assert email.value == "user@example.com"

    def test_uppercase_lowered(self) -> None:
        email = Email("USER@EXAMPLE.COM")
        assert email.value == "user@example.com"

    def test_combined_normalization(self) -> None:
        email = Email("  User.Name@DOMAIN.COM  ")
        assert email.value == "user.name@domain.com"


class TestEmailConstants:
    """Проверка экспортированных констант."""

    def test_min_length(self) -> None:
        assert EMAIL_MIN_LENGTH == 3

    def test_max_length(self) -> None:
        assert EMAIL_MAX_LENGTH == 254

    def test_pattern_compiled(self) -> None:
        assert EMAIL_PATTERN.pattern is not None
