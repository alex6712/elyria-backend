import textwrap
from typing import Annotated

from fastapi import APIRouter, Body, status

from src.shared.application.unset import UNSET, Maybe
from src.users.application.inputs import ChangeProfileInput
from src.users.domain.value_objects import AvatarUrl, DisplayName
from src.users.presentation.http.dependencies import (
    AccessTokenDependency,
    ChangeProfileDependency,
)
from src.users.presentation.http.exceptions import AccessTokenMissingError
from src.users.presentation.http.v1.schemas import ChangeProfileRequest

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
    access_token: AccessTokenDependency,
    body: Annotated[
        ChangeProfileRequest,
        Body(description="Схема частичного изменения профиля пользователя."),
    ],
    change_profile_use_case: ChangeProfileDependency,
) -> None:
    """Изменение профиля пользователя.

    Применяет к профилю аутентифицированного пользователя только те
    поля тела запроса, которые были явно переданы, и сохраняет
    изменения атомарно.

    Parameters
    ----------
    access_token : str | None
        Строка access-токена из заголовка ``Authorization``
        входящего запроса (значение после слова ``Bearer``).
        Значение ``None`` означает отсутствие заголовка либо
        некорректную схему.
    body : ChangeProfileRequest
        Валидированная схема тела запроса, содержащая обновляемые
        поля профиля: displayName (str | None) и avatarUrl
        (str | None).
    change_profile_use_case : ChangeProfileUseCase
        Use Case изменения профиля, полученный через DI-зависимость
        FastAPI из контейнера приложения.

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

    await change_profile_use_case.execute(
        ChangeProfileInput(
            access_token=access_token,
            display_name=new_display_name,
            avatar_url=new_avatar_url,
        )
    )
