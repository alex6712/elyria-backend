from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

http_bearer = HTTPBearer(auto_error=False)
"""Экземпляр Bearer-схемы аутентификации FastAPI.

Используется как security-схема OpenAPI для эндпоинтов, принимающих
access-токен в заголовке ``Authorization``. С ``auto_error=False``
не бросает исключение при отсутствии заголовка - возвращает ``None``,
оставляя обработку ошибки вызывающему коду.
"""


def _extract_access_token(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(http_bearer)],
) -> str | None:
    """Извлечь строковое значение access-токена из учётных данных Bearer-схемы.

    Служит внутренней FastAPI-зависимостью для :data:`AccessTokenDependency`.
    Извлекает сырую строку токена из объекта учётных данных, полученного
    в результате валидации Bearer-схемы.

    Parameters
    ----------
    credentials : HTTPAuthorizationCredentials | None
        Объект учётных данных из схемы ``HTTPBearer`` или ``None``,
        если заголовок ``Authorization`` отсутствует либо некорректен.

    Returns
    -------
    str | None
        Строка access-токена (значение после слова ``Bearer``),
        если заголовок присутствует, иначе ``None``.
    """
    return credentials.credentials if credentials is not None else None


AccessTokenDependency = Annotated[str | None, Depends(_extract_access_token)]
"""Типизированная FastAPI-зависимость access-токена из Bearer-заголовка.

Является общей зависимостью приложения и используется ограниченными
контекстами для эндпоинтов, требующих аутентификации. Извлекает учётные
данные Bearer-схемы из заголовка ``Authorization`` входящего запроса.
Значение ``None`` означает, что заголовок отсутствует либо схема не
является Bearer - в этом случае обработка ошибки выполняется вызывающим
кодом:

```python
@router.post("/logout")
async def logout(
    access_token: AccessTokenDependency,
    ...,
) -> StandardResponse:
    if access_token is None:
        raise AccessTokenMissingError(...)
```
"""
