from typing import Annotated

from fastapi import Depends, Request

from src.users.application.handlers.command import ChangeProfileCommandHandler
from src.users.application.handlers.query import GetProfileQueryHandler


def _get_change_profile_command_handler(
    request: Request,
) -> ChangeProfileCommandHandler:
    """Получить обработчик команды изменения профиля из DI-контейнера.

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
    ChangeProfileCommandHandler
        Обработчик команды изменения профиля пользователя.
    """
    return request.app.state.container.users.change_profile_command_handler


ChangeProfileDependency = Annotated[
    ChangeProfileCommandHandler, Depends(_get_change_profile_command_handler)
]
"""Типизированная FastAPI-зависимость обработчика команды изменения профиля.

Инкапсулирует доступ к ``request.app.state.container`` и предоставляет
роутам готовый экземпляр :class:`ChangeProfileCommandHandler` без ручного
приведения типов. Используется как аннотация параметра обработчика:

```python
@router.patch("/profiles")
async def change_profile(
    change_profile_command_handler: ChangeProfileDependency,
    ...,
) -> None:
    await change_profile_command_handler.execute(...)
```
"""


def _get_get_profile_query_handler(request: Request) -> GetProfileQueryHandler:
    """Получить query handler получения профиля из DI-контейнера.

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
    GetProfileQueryHandler
        Query handler получения профиля пользователя.
    """
    return request.app.state.container.users.get_profile_query_handler


GetProfileDependency = Annotated[
    GetProfileQueryHandler, Depends(_get_get_profile_query_handler)
]
"""Типизированная FastAPI-зависимость query handler получения профиля.

Инкапсулирует доступ к ``request.app.state.container`` и предоставляет
роутам готовый экземпляр :class:`GetProfileQueryHandler` без ручного
приведения типов. Используется как аннотация параметра обработчика:

```python
@router.get("/profiles/me")
async def get_my_profile(
    get_profile_query_handler: GetProfileDependency,
    ...,
) -> ProfileResponse:
    result = await get_profile_query_handler.execute(...)
```
"""
