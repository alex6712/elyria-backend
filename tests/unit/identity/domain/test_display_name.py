"""Unit-тесты объекта-значения :class:`DisplayName`."""

from dataclasses import FrozenInstanceError

import pytest

from src.identity.domain.exceptions import InvalidDisplayNameLengthError
from src.identity.domain.value_objects import DisplayName
from src.identity.domain.value_objects.display_name import DISPLAY_NAME_MAX_LENGTH


class TestDisplayNameNormalization:
    """Проверка NFC-нормализации отображаемого имени."""

    def test_nfc_normalization_applied(self) -> None:
        """Разложенная форма символа приводится к составной."""
        display_name = DisplayName("e\u0301")

        assert display_name.value == "é"

    def test_nfc_normalization_for_precomposed(self) -> None:
        """Уже нормализованная строка не изменяется."""
        display_name = DisplayName("Élyria")

        assert display_name.value == "Élyria"

    def test_nfc_normalization_length_after_normalization(self) -> None:
        """Длина проверяется после нормализации."""
        raw = "e\u0301" * (DISPLAY_NAME_MAX_LENGTH + 1)

        with pytest.raises(InvalidDisplayNameLengthError):
            DisplayName(raw)


class TestDisplayNameValidation:
    """Проверка ограничений длины отображаемого имени."""

    @pytest.mark.parametrize(
        "value",
        [
            "A",
            " ",
            "a" * DISPLAY_NAME_MAX_LENGTH,
            "John Doe",
            "Света",
        ],
    )
    def test_valid_display_names(self, value: str) -> None:
        """Отображаемое имя допустимой длины создаётся успешно."""
        display_name = DisplayName(value)

        assert display_name.value == value

    @pytest.mark.parametrize(
        "value",
        [
            "",
            "a" * (DISPLAY_NAME_MAX_LENGTH + 1),
        ],
    )
    def test_invalid_length_raises(self, value: str) -> None:
        """Отображаемое имя вне допустимого диапазона длины отклоняется."""
        with pytest.raises(InvalidDisplayNameLengthError):
            DisplayName(value)

    def test_length_boundary_maximum(self) -> None:
        """Максимальная длина отображаемого имени допустима."""
        display_name = DisplayName("a" * DISPLAY_NAME_MAX_LENGTH)

        assert display_name.value == "a" * DISPLAY_NAME_MAX_LENGTH


class TestDisplayNameImmutability:
    """Проверка неизменяемости отображаемого имени."""

    def test_value_cannot_be_changed(self) -> None:
        """Попытка изменить значение замороженного объекта отклоняется."""
        display_name = DisplayName("John")

        with pytest.raises(FrozenInstanceError):
            display_name.value = "Jane"

    def test_str_returns_value(self) -> None:
        """Строковое представление совпадает со значением."""
        display_name = DisplayName("John")

        assert str(display_name) == "John"

    def test_equality_by_value(self) -> None:
        """Два экземпляра с одинаковым значением равны."""
        assert DisplayName("John") == DisplayName("John")
