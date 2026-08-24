from pydantic import BaseModel, ConfigDict, Field

from src.shared.application.unset import UNSET, Maybe
from src.users.domain.value_objects import AvatarUrl, DisplayName


class ChangeProfileCommand(BaseModel):
    """Команда на изменение профиля пользователя.

    Содержит данные для изменения профиля: access-токен пользователя
    и обновляемые поля профиля. Поля ``display_name`` и ``avatar_url``
    используют sentinel-значение :data:`UNSET`, позволяющее отличить
    поле, не переданное в запросе (изменение не требуется), от явно
    переданного значения (в том числе ``None`` - удаление аватара).

    Parameters
    ----------
    access_token : str
        Access JWT пользователя, выполняющего операцию.
    display_name : Maybe[DisplayName]
        Новое отображаемое имя профиля либо ``UNSET``, если имя
        изменять не требуется.
    avatar_url : Maybe[AvatarUrl | None]
        Новый URL изображения аватара либо ``UNSET``, если аватар
        изменять не требуется. Значение ``None`` означает удаление
        аватара из профиля.

    Notes
    -----
    Команда неизменяема после создания (``frozen``).
    """

    access_token: str = Field(
        description="Access-токен пользователя, выполняющего изменение профиля."
    )
    display_name: Maybe[DisplayName] = Field(default=UNSET)
    avatar_url: Maybe[AvatarUrl | None] = Field(default=UNSET)

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)
