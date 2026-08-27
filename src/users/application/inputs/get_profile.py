from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class GetProfileInput:
    """Класс с входными данными для получения профиля пользователя.

    Содержит access-токен пользователя и необязательный идентификатор
    профиля, который требуется получить.

    Parameters
    ----------
    access_token : str
        Access JWT пользователя, выполняющего операцию.
    profile_id : UUID | None, optional
        Уникальный идентификатор профиля, который требуется получить.
        Значение ``None`` означает получение профиля учётной записи,
        которой принадлежит переданный access-токен (сценарий
        "мой профиль").

    Notes
    -----
    Объект неизменяем после создания (``frozen``).
    """

    access_token: str
    profile_id: UUID | None = None
