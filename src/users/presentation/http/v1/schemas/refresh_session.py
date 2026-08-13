from pydantic import Field

from src.shared.presentation.http.schemas import StandardResponse


class RefreshSessionResponse(StandardResponse):
    """Модель ответа на успешное обновление пары токенов.

    Содержит access-токен для дальнейшей аутентификации запросов.
    Refresh-токен передаётся клиенту не в теле ответа, а в HttpOnly-cookie,
    поэтому в модели отсутствует.

    Attributes
    ----------
    access_token : str
        Access JWT для аутентификации последующих запросов.

    See Also
    --------
    :class:`StandardResponse`
        Базовая модель ответа с полями ``code`` и ``detail``.
    """

    access_token: str = Field(
        description="Токен доступа, предоставляемый пользователю.",
        examples=[
            "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9."
            + "eyJzdWIiOiIxMjNlNDU2Ny1lODliLTEyZDMtYTQ1Ni00MjY2MTQxNzQwMDAiLCJpc3M"
            + "iOiJodHRwczovL2FwaS5lbHlyaWEucnUiLCJpYXQiOjE3NTY4MTI4MDAsImV4cCI6MT"
            + "c1NjgxNjQwMCwianRpIjoiMTIzZTQ1NjctZTg5Yi0xMmQzLWE0NTYtNDI2NjE0MTc0M"
            + "DAxIiwic2lkIjoiMTIzZTQ1NjctZTg5Yi0xMmQzLWE0NTYtNDI2NjE0MTc0MDAyIn0."
            + "5FbYeYiWaFIh18XlVGRMIbcQBrh3PJlU0wdmpnOAShy"
            + "TuqukDqMV8bfz2_8SMdbnQz0gvst56uz2Tq6l-RMDBw",
        ],
    )
