from typing import Self, TypeIs, override


class Unset:
    """Sentinel-тип для различия между "значение не передано" и ``None``.

    Реализован как синглтон - все экземпляры являются одним и тем же объектом,
    что позволяет использовать проверку через ``is`` и ``isinstance``.

    Notes
    -----
    Используется совместно с типом ``Maybe[T]`` в аннотациях типов, где поле или
    атрибут может быть намеренно не передан (в отличие от явной передачи ``None``).
    """

    __slots__ = ()

    _instance = None

    def __new__(cls) -> Self:
        if cls._instance is None:
            cls._instance = super().__new__(cls)

        return cls._instance

    @override
    def __str__(self) -> str:
        return "UNSET"

    @override
    def __repr__(self) -> str:
        return "<UNSET>"


UNSET = Unset()
"""Единственный экземпляр ``Unset``, представляющий отсутствие переданного значения."""

type Maybe[T] = T | Unset
"""Тип для параметров, которые могут быть не переданы.

Отличается от ``T | None`` тем, что ``None`` считается явно переданным значением
тогда как ``Unset`` означает отсутствие намерения изменить поле.
"""


def is_set[T](value: T | Unset) -> TypeIs[T]:
    """Проверяет, не является ли переданное значение ``Unset``.

    Parameters
    ----------
    value : T | Unset
        Значение, которое необходимо проверить.

    Returns
    -------
    TypeIs[T]
        ``True``, если значение не является экземпляром ``Unset``,
        то есть было явно передано (включая ``None``).
        ``False``, если значение соответствует ``UNSET`` - значение не было передано.
    """
    return not isinstance(value, Unset)
