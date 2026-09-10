from dataclasses import dataclass

from src.users.application.dto.read_models import UserSearchReadModel


@dataclass(frozen=True, slots=True)
class SearchUsersResult:
    """Результат нечёткого поиска учётных записей по имени пользователя.

    Содержит найденные строки read model и общее количество
    результатов, соответствующее запросу (без учёта пагинации).

    Attributes
    ----------
    items : list[UserSearchReadModel]
        Найденные строки read model учётных записей и профилей.
    total : int
        Общее количество строк read model, соответствующих запросу,
        без учёта ограничений пагинации.
    """

    items: list[UserSearchReadModel]
    total: int
