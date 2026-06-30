from uuid import UUID

from pydantic import Field

from app.core.enums import DeleteErrorCode
from app.schemas.dto.base import BaseErrorDTO


class DeleteItemErrorDTO(BaseErrorDTO[DeleteErrorCode]):
    """DTO для представления ошибки при удалении сущности.

    Расширяет :class:`BaseErrorDTO`, фиксируя тип кода ошибки как
    :class:`DeleteErrorCode` и добавляя идентификатор сущности,
    при удалении которой возникла ошибка.

    Attributes
    ----------
    id : UUID
        Идентификатор сущности, удаление которой завершилось ошибкой.
    """

    id: UUID = Field(
        description="Идентификатор сущности, удаление которой завершилось ошибкой.",
    )
