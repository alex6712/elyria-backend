from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class GetProfileInput:
    """Класс с входными данными для получения профиля пользователя.

    Содержит access-токен пользователя и необязательный идентификатор
    учётной записи, профиль которой требуется получить.

    Parameters
    ----------
    access_token : str
        Access JWT пользователя, выполняющего операцию.
    identity_id : UUID | None, optional
        Идентификатор учётной записи, профиль которой требуется получить.
        Значение ``None`` означает получение профиля учётной записи,
        которой принадлежит переданный access-токен (сценарий
        «мой профиль»).

    Notes
    -----
    Объект неизменяем после создания (``frozen``).
    """

    access_token: str
    identity_id: UUID | None = None
