import textwrap
from typing import Annotated

from fastapi import APIRouter, Body, Path, status
from pydantic import UUID4

from src.shared.application.unset import UNSET, Maybe
from src.shared.presentation.http.dependencies import AccessTokenDependency
from src.users.application.dto.commands import ChangeProfileCommand
from src.users.application.dto.queries import GetProfileQuery
from src.users.domain.value_objects import AvatarUrl, DisplayName
from src.users.presentation.http.dependencies import (
    ChangeProfileDependency,
    GetProfileDependency,
)
from src.users.presentation.http.exceptions import AccessTokenMissingError
from src.users.presentation.http.v1.schemas import (
    ChangeProfileRequest,
    ProfileResponse,
)

router = APIRouter(prefix="/profiles", tags=["profiles"])


@router.patch(
    "",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Изменение профиля пользователя.",
    description=textwrap.dedent("""\
        Частично обновляет профиль аутентифицированного пользователя.

        Access-токен передаётся в заголовке ``Authorization``
        в формате ``Bearer <token>``.

        Запрос следует семантике PATCH: обновляются только поля,
        явно переданные в теле запроса:

        - ``displayName``: новое отображаемое имя;
        - ``avatarUrl``: новый URL изображения аватара; значение
          ``null`` удаляет аватар из профиля.

        Поля, отсутствующие в теле запроса, остаются без изменений.
        Запрос без единого обновляемого поля отклоняется с кодом
        ``400 Bad Request`` (``NOTHING_TO_UPDATE``).

        При успешном изменении возвращается ответ без тела
        (``204 No Content``).

        В случае ошибки (отсутствие или недействительность access-токена,
        отзыв токена, нарушение ограничений значений, отсутствие профиля)
        возвращается соответствующий HTTP-код и сообщение об ошибке.
    """),
    response_description="Профиль успешно изменён (тело ответа отсутствует)",
)
async def change_profile(
    body: Annotated[
        ChangeProfileRequest,
        Body(description="Схема частичного изменения профиля пользователя."),
    ],
    access_token: AccessTokenDependency,
    change_profile_command_handler: ChangeProfileDependency,
) -> None:
    """Изменение профиля пользователя.

    Применяет к профилю аутентифицированного пользователя только те
    поля тела запроса, которые были явно переданы, и сохраняет
    изменения атомарно.

    Parameters
    ----------
    body : ChangeProfileRequest
        Валидированная схема тела запроса, содержащая обновляемые
        поля профиля: displayName (str | None) и avatarUrl
        (str | None).
    access_token : str | None
        Строка access-токена из заголовка ``Authorization``
        входящего запроса (значение после слова ``Bearer``).
        Значение ``None`` означает отсутствие заголовка либо
        некорректную схему.
    change_profile_command_handler : ChangeProfileCommandHandler
        Обработчик команды изменения профиля, полученный через
        DI-зависимость FastAPI из контейнера приложения.

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

    new_display_name: Maybe[DisplayName] = (
        DisplayName(body.display_name) if body.display_name is not None else UNSET
    )

    new_avatar_url: Maybe[AvatarUrl | None] = (
        (AvatarUrl(body.avatar_url) if body.avatar_url is not None else None)
        if "avatar_url" in body.model_fields_set
        else UNSET
    )

    await change_profile_command_handler.execute(
        ChangeProfileCommand(
            access_token=access_token,
            display_name=new_display_name,
            avatar_url=new_avatar_url,
        )
    )


@router.get(
    "/me",
    response_model=ProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Получение профиля текущего пользователя.",
    description=textwrap.dedent("""\
        Возвращает профиль учётной записи, выполнившей запрос.

        Access-токен передаётся в заголовке ``Authorization``
        в формате ``Bearer <token>``. Профиль выбирается по учётной
        записи, указанной в утверждении ``sub`` токена, поэтому
        путь запроса дополнительных параметров не содержит.

        Для получения профиля другого пользователя используйте
        эндпоинт ``GET /v1/profiles/{profileId}``.

        В случае ошибки (отсутствие или недействительность access-токена,
        отзыв токена, отсутствие профиля) возвращается соответствующий
        HTTP-код и сообщение об ошибке.
    """),
    response_description="Профиль текущего пользователя",
)
async def get_my_profile(
    access_token: AccessTokenDependency,
    get_profile_query_handler: GetProfileDependency,
) -> ProfileResponse:
    """Получить профиль текущего пользователя.

    Извлекает access-токен из Bearer-заголовка и возвращает профиль
    учётной записи, которой токен был выпущен.

    Parameters
    ----------
    access_token : str | None
        Строка access-токена из заголовка ``Authorization``
        входящего запроса (значение после слова ``Bearer``).
        Значение ``None`` означает отсутствие заголовка либо
        некорректную схему.
    get_profile_query_handler : GetProfileQueryHandler
        Обработчик запроса получения профиля, полученный через
        DI-зависимость FastAPI из контейнера приложения.

    Returns
    -------
    ProfileResponse
        Ответ с кодом 200 и данными профиля текущего пользователя:
        id, displayName, avatarUrl, createdAt, updatedAt.

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

    result = await get_profile_query_handler.execute(
        GetProfileQuery(access_token=access_token)
    )

    return ProfileResponse(
        id=result.id,
        display_name=result.display_name.value,
        avatar_url=result.avatar_url.value if result.avatar_url is not None else None,
        created_at=result.created_at,
        updated_at=result.updated_at,
    )


@router.get(
    "/{profile_id}",
    response_model=ProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Получение профиля по идентификатору.",
    description=textwrap.dedent("""\
        Возвращает профиль пользователя с указанным идентификатором.

        Access-токен передаётся в заголовке ``Authorization``
        в формате ``Bearer <token>``. Идентификатор запрашиваемого
        профиля передаётся в пути запроса как UUID
        (``profileId``); передача строки, не являющейся UUID,
        отклоняется с кодом ``422 Unprocessable Content``
        (``VALIDATION_ERROR``).

        Для получения собственного профиля без указания идентификатора
        используйте эндпоинт ``GET /v1/profiles/me``.

        В случае ошибки (отсутствие или недействительность access-токена,
        отзыв токена, некорректный формат идентификатора, отсутствие
        профиля) возвращается соответствующий HTTP-код и сообщение
        об ошибке.
    """),
    response_description="Профиль запрашиваемого пользователя",
)
async def get_profile_by_id(
    profile_id: Annotated[
        UUID4,
        Path(
            description=(
                "Уникальный идентификатор профиля, который требуется получить."
            ),
            examples=["a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d"],
        ),
    ],
    access_token: AccessTokenDependency,
    get_profile_query_handler: GetProfileDependency,
) -> ProfileResponse:
    """Получить профиль по идентификатору.

    Извлекает access-токен из Bearer-заголовка и возвращает профиль
    пользователя, указанного в пути запроса.

    Parameters
    ----------
    profile_id : UUID
        Уникальный идентификатор профиля, который требуется получить.
    access_token : str | None
        Строка access-токена из заголовка ``Authorization``
        входящего запроса (значение после слова ``Bearer``).
        Значение ``None`` означает отсутствие заголовка либо
        некорректную схему.
    get_profile_query_handler : GetProfileQueryHandler
        Обработчик запроса получения профиля, полученный через
        DI-зависимость FastAPI из контейнера приложения.

    Returns
    -------
    ProfileResponse
        Ответ с кодом 200 и данными профиля запрашиваемого
        пользователя: id, displayName, avatarUrl, createdAt,
        updatedAt.

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

    result = await get_profile_query_handler.execute(
        GetProfileQuery(access_token=access_token, profile_id=profile_id)
    )

    return ProfileResponse(
        id=result.id,
        display_name=result.display_name.value,
        avatar_url=result.avatar_url.value if result.avatar_url is not None else None,
        created_at=result.created_at,
        updated_at=result.updated_at,
    )
