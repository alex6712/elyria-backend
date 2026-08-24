from typing import Annotated

from fastapi import Depends, Request

from src.users.application.use_cases import ChangeProfileUseCase, GetProfileUseCase


def _get_change_profile_use_case(request: Request) -> ChangeProfileUseCase:
    """Получить Use Case изменения профиля из DI-контейнера.

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
    ChangeProfileUseCase
        Use Case изменения профиля пользователя.
    """
    return request.app.state.container.users.change_profile_use_case


ChangeProfileDependency = Annotated[
    ChangeProfileUseCase, Depends(_get_change_profile_use_case)
]
"""Типизированная FastAPI-зависимость Use Case изменения профиля.

Инкапсулирует доступ к ``request.app.state.container`` и предоставляет
роутам готовый экземпляр :class:`ChangeProfileUseCase` без ручного
приведения типов. Используется как аннотация параметра обработчика:

```python
@router.patch("/profiles")
async def change_profile(
    change_profile_use_case: ChangeProfileDependency,
    ...,
) -> None:
    await change_profile_use_case.execute(...)
```
"""


def _get_get_profile_use_case(request: Request) -> GetProfileUseCase:
    """Получить Use Case получения профиля из DI-контейнера.

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
    GetProfileUseCase
        Use Case получения профиля пользователя.
    """
    return request.app.state.container.users.get_profile_use_case


GetProfileDependency = Annotated[GetProfileUseCase, Depends(_get_get_profile_use_case)]
"""Типизированная FastAPI-зависимость Use Case получения профиля.

Инкапсулирует доступ к ``request.app.state.container`` и предоставляет
роутам готовый экземпляр :class:`GetProfileUseCase` без ручного
приведения типов. Используется как аннотация параметра обработчика:

```python
@router.get("/profiles/me")
async def get_my_profile(
    get_profile_use_case: GetProfileDependency,
    ...,
) -> ProfileResponse:
    result = await get_profile_use_case.execute(...)
```
"""
