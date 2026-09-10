from typing import Annotated

from fastapi import Depends, Request

from src.users.application.handlers.query import SearchUsersQueryHandler


def _get_search_users_query_handler(request: Request) -> SearchUsersQueryHandler:
    """Получить query handler поиска пользователей из DI-контейнера.

    Доступ к нетипизированному ``request.app.state.container``
    выполняется напрямую - Starlette не поддерживает типизацию
    ``State`` нативно, поэтому возвращаемый тип принудительно
    объявляется сигнатурой функции.

    Parameters
    ----------
    request : Request
        Объект HTTP-запроса FastAPI. Используется для доступа
        к глобальному DI-контейнеру приложения через ``app.state``.

    Returns
    -------
    SearchUsersQueryHandler
        Query handler нечёткого поиска пользователей по имени пользователя.
    """
    return request.app.state.container.users.search_users_query_handler


SearchUsersDependency = Annotated[
    SearchUsersQueryHandler, Depends(_get_search_users_query_handler)
]
"""Типизированная FastAPI-зависимость query handler поиска пользователей.

Инкапсулирует доступ к ``request.app.state.container`` и предоставляет
роутам готовый экземпляр :class:`SearchUsersQueryHandler` без ручного
приведения типов. Используется как аннотация параметра обработчика:

```python
@router.get("/users/search")
async def search_users(
    search_users_query_handler: SearchUsersDependency,
    ...,
) -> UserSearchResponse:
    result = await search_users_query_handler.execute(...)
```
"""
