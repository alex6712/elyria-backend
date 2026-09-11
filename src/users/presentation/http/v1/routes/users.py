import textwrap
from typing import Annotated

from fastapi import APIRouter, Query, status
from pydantic import StringConstraints

from src.shared.presentation.http.dependencies import AccessTokenDependency
from src.users.application.dto.queries import SearchUsersQuery
from src.users.domain.value_objects.username import (
    USERNAME_MAX_LENGTH,
    USERNAME_PATTERN,
)
from src.users.presentation.http.dependencies import SearchUsersDependency
from src.users.presentation.http.exceptions import AccessTokenMissingError
from src.users.presentation.http.v1.schemas import UserSearchItem, UserSearchResponse

router = APIRouter(prefix="/users", tags=["users"])

SEARCH_DEFAULT_LIMIT = 20
"""Количество записей в выдаче поиска по умолчанию."""

SEARCH_DEFAULT_OFFSET = 0
"""Смещение начала выдачи поиска по умолчанию."""


@router.get(
    "/search",
    response_model=UserSearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Нечёткий поиск пользователей по имени пользователя.",
    description=textwrap.dedent("""\
        Выполняет нечёткий поиск пользователей
        по имени пользователя (``username``).

        Для поиска обязателен access-токен: он передаётся в заголовке
        ``Authorization`` в формате ``Bearer <token>``. Запрос поиска
        передаётся в обязательном query-параметре ``q``.

        Совпадение засчитывается, если ``username`` содержит запрос
        без учёта регистра либо близок к нему (допускаются опечатки
        и незначительные отличия). Результаты упорядочиваются так:
        сначала точные совпадения, затем по убыванию релевантности.

        Каждый элемент выдачи содержит:

        - ``identityId``: идентификатор учётной записи;
        - ``profileId``: идентификатор профиля;
        - ``username``: имя пользователя (логин);
        - ``displayName``: отображаемое имя профиля;
        - ``avatarUrl``: URL изображения аватара либо ``null``.

        Пагинация управляется query-параметрами ``limit``
        (количество записей на страницу, по умолчанию 20)
        и ``offset`` (смещение начала выдачи, по умолчанию 0).
        Поле ``total`` ответа содержит общее количество
        результатов, соответствующих запросу (без учёта
        пагинации).

        Поиск выполняется по данным, которые обновляются асинхронно
        после регистрации пользователя и изменения профиля:
        свежие изменения могут отражаться в результатах не мгновенно.

        В случае ошибки (отсутствие или недействительность
        access-токена, отзыв токена, некорректный формат
        параметров запроса) возвращается соответствующий
        HTTP-код и сообщение об ошибке.
    """),
    response_description="Результаты нечёткого поиска пользователей",
)
async def search_users(
    query: Annotated[
        str,
        StringConstraints(
            strip_whitespace=True,
            min_length=1,
            max_length=USERNAME_MAX_LENGTH,
            pattern=USERNAME_PATTERN,
        ),
        Query(
            alias="q",
            description=(
                "Запрос поиска имени пользователя. Совпадение засчитывается "
                + "при точном совпадении или вхождении без учёта регистра либо "
                + "при близком сходстве (допускаются опечатки и незначительные "
                + "отличия)."
            ),
            examples=["john", "ale", "user"],
        ),
    ],
    access_token: AccessTokenDependency,
    search_users_query_handler: SearchUsersDependency,
    limit: Annotated[
        int,
        Query(
            description="Максимальное количество записей в выдаче (страница).",
            ge=1,
            le=100,
            examples=[20],
        ),
    ] = SEARCH_DEFAULT_LIMIT,
    offset: Annotated[
        int,
        Query(description="Смещение начала выдачи для пагинации.", ge=0, examples=[0]),
    ] = SEARCH_DEFAULT_OFFSET,
) -> UserSearchResponse:
    """Найти пользователей по запросу поиска.

    Извлекает access-токен из Bearer-заголовка и возвращает
    данные найденных пользователей с применением пагинации:
    точные совпадения первыми, далее по убыванию релевантности.

    Parameters
    ----------
    query : str
        Запрос поиска имени пользователя.
    access_token : str | None
        Строка access-токена из заголовка ``Authorization``
        входящего запроса (значение после слова ``Bearer``).
        Значение ``None`` означает отсутствие заголовка либо
        некорректную схему.
    search_users_query_handler : SearchUsersQueryHandler
        Query handler поиска пользователей, полученный через
        DI-зависимость FastAPI из контейнера приложения.
    limit : int
        Максимальное количество записей в выдаче (страница).
    offset : int
        Смещение начала выдачи для пагинации.

    Returns
    -------
    UserSearchResponse
        Ответ с кодом 200, списком найденных пользователей
        и общим количеством результатов: items, total.

    Raises
    ------
    AccessTokenMissingError
        Если заголовок ``Authorization`` с Bearer-схемой отсутствует
        во входящем запросе либо имеет некорректный формат.
    """
    if access_token is None:
        raise AccessTokenMissingError(
            "Access token is missing. "
            + "Provide it in the Authorization: Bearer <token> header."
        )

    result = await search_users_query_handler.execute(
        SearchUsersQuery(
            access_token=access_token, query=query, limit=limit, offset=offset
        )
    )

    return UserSearchResponse(
        items=[
            UserSearchItem(
                identity_id=item.identity_id,
                profile_id=item.profile_id,
                username=item.username,
                display_name=item.display_name,
                avatar_url=item.avatar_url,
            )
            for item in result.items
        ],
        total=result.total,
    )
