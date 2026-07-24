from uuid import UUID


class ConcurrentModificationError(Exception):
    """Исключение, сигнализирующее о конфликте при optimistic locking.

    Возникает, когда репозиторий пытается сохранить изменения агрегата,
    но его версия в хранилище уже изменилась с момента загрузки.

    Исключение является доменным, так как отражает правило работы
    агрегата: ни один агрегат не может быть сохранён, если его версия
    не совпадает с актуальной версией в хранилище.

    Parameters
    ----------
    entity_id : UUID
        Идентификатор агрегата, для которого обнаружен конфликт.
    entity_type : str
        Имя класса агрегата (например, ``"Identity"``, ``"Session"``).
    """

    def __init__(self, entity_id: UUID, entity_type: str) -> None:
        self.entity_id = entity_id
        self.entity_type = entity_type

        super().__init__(
            f"{entity_type} with id={entity_id} was modified concurrently. "
            f"Reload the entity and retry the operation."
        )
