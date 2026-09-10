from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SearchUsersQuery:
    """Запрос нечёткого поиска учётных записей по имени пользователя.

    Выполняет поиск по подстроке имени пользователя (``username``)
    в read model. Возвращает данные учётной записи
    (Identity) и связанного профиля (Profile).

    Parameters
    ----------
    access_token : str
        Access JWT пользователя, выполняющего операцию.
    query : str
        Подстрока имени пользователя для нечёткого поиска.
    limit : int, optional
        Максимальное количество записей в выдаче (страница).
    offset : int, optional
        Смещение начала выдачи для пагинации.

    Notes
    -----
    Объект неизменяем после создания (``frozen``).
    """

    access_token: str
    query: str
    limit: int = 20
    offset: int = 0
