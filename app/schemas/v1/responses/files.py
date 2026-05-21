from pydantic import Field

from app.schemas.dto.file import PublicFileDTO
from app.schemas.v1.responses.standard import PaginationResponse


class FilesResponse(PaginationResponse):
    """Модель ответа сервера с вложенным списком файлов.

    Используется в качестве ответа с сервера на запрос о получении
    файлов пользователем.

    Attributes
    ----------
    files : list[PublicFileDTO]
        Список всех файлов, подходящих под фильтры.
    """

    files: list[PublicFileDTO] = Field(
        description="Список всех файлов, подходящих под фильтры.",
    )
