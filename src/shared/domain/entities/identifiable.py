from typing import override


class Identifiable[IdT]:
    """Класс-примесь, предоставляющий сущности идентичность по полю ``id``.

    Позволяет вынести логику идентификации в отдельный класс-примесь
    и использовать её в нескольких иерархиях наследования без привязки
    к конкретному базовому классу.

    Attributes
    ----------
    id : IdT
        Уникальный идентификатор сущности. Тип параметризуется
        конкретным наследником (например, ``Identifiable[UUID]``).

    Notes
    -----
    Класс не содержит бизнес-логики и предназначен исключительно для
    обеспечения идентичности. Не управляет временными метками и не должен
    использоваться как единственный базовый класс - применяется в качестве
    примеси совместно с другими классами (например, ``Auditable``).
    """

    def __init__(self, id: IdT) -> None:
        self.id = id

    @override
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, self.__class__):
            return NotImplemented

        return self.id == other.id

    @override
    def __hash__(self) -> int:
        return hash(self.id)
