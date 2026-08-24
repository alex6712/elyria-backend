from dataclasses import dataclass

from src.shared.application.unset import UNSET, Maybe
from src.users.domain.value_objects import AvatarUrl, DisplayName


@dataclass(frozen=True, slots=True)
class ChangeProfileInput:
    """Класс с входными данными для изменения профиля пользователя.

    Содержит данные для изменения профиля: access-токен пользователя
    и обновляемые поля профиля. Поля ``display_name`` и ``avatar_url``
    используют sentinel-значение :data:`UNSET`, позволяющее отличить
    поле, не переданное в запросе (изменение не требуется), от явно
    переданного значения (в том числе ``None`` - удаление аватара).

    Parameters
    ----------
    access_token : str
        Access JWT пользователя, выполняющего операцию.
    display_name : Maybe[DisplayName], optional
        Новое отображаемое имя профиля либо ``UNSET``, если имя
        изменять не требуется.
    avatar_url : Maybe[AvatarUrl | None], optional
        Новый URL изображения аватара либо ``UNSET``, если аватар
        изменять не требуется. Значение ``None`` означает удаление
        аватара из профиля.

    Notes
    -----
    Объект неизменяем после создания (``frozen``).
    """

    access_token: str
    display_name: Maybe[DisplayName] = UNSET
    avatar_url: Maybe[AvatarUrl | None] = UNSET
