from pydantic import Field

from app.schemas.dto.couple import CoupleRequestDTO, UserCoupleDTO
from app.schemas.v1.responses.standard import StandardResponse


class CoupleResponse(StandardResponse):
    """Модель ответа сервера с информацией о паре пользователя.

    Используется в качестве ответа на запрос получения данных
    о паре текущего пользователя.

    Attributes
    ----------
    couple : UserCoupleDTO | None
        DTO пары пользователя. None, если пользователь не состоит в паре.
    """

    couple: UserCoupleDTO | None = Field(
        description="DTO пары пользователя. None, если пользователь не состоит в паре."
    )


class CoupleRequestsResponse(StandardResponse):
    """Модель ответа сервера с вложенным списком запросов на создание пары.

    Используется в качестве ответа с сервера на запрос о получении
    запросов на создание пары.

    Attributes
    ----------
    requests : list[CoupleRequestDTO]
        Список всех запросов, подходящих под фильтры.
    """

    requests: list[CoupleRequestDTO] = Field(
        description="Список всех запросов, подходящих под фильтры.",
    )
