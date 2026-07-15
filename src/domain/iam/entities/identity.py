from uuid import UUID

from src.domain.shared.entities import Auditable, Identifiable


class Identity(Identifiable[UUID], Auditable):
    """Доменная сущность учётной записи пользователя.

    Представляет собой учётную запись (identity) пользователя
    в системе. Содержит идентификатор и метки аудита,
    наследуя функциональность от ``Identifiable`` и ``Auditable``.
    """
