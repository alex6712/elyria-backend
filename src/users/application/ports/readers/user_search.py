from typing import Protocol, runtime_checkable

from src.users.application.dto.read_models import UserSearchReadModel


@runtime_checkable
class UserSearchReader(Protocol):
    """Порт доступа к read model поиска пользователей по username.

    Определяет контракт доступа к denormalized read model
    (таблица ``user_search_read_model``), объединяющему
    данные учётной записи (Identity) и профиля (Profile).

    Порт разделяет обязанности записи (обслуживание read model
    обработчиками доменных событий) и чтения (нечёткий поиск
    для query handler).

    Notes
    -----
    Реализация должна гарантировать идемпотентность операции
    :meth:`upsert`: повторная запись для одной и той же учётной
    записи обновляет существующую строку, не создавая дубликатов.
    """

    async def upsert(self, read_model: UserSearchReadModel) -> None:
        """Создать либо обновить строку read model для учётной записи.

        Выполняет вставку новых данных либо обновление существующей
        строки по идентификатору учётной записи (``identity_id``).
        Операция идемпотентна.

        Parameters
        ----------
        read_model : UserSearchReadModel
            Денормализованные данные учётной записи и профиля
            для сохранения в read model.
        """
        ...

    async def search_by_username(
        self, query: str, limit: int, offset: int
    ) -> list[UserSearchReadModel]:
        """Выполнить нечёткий поиск учётных записей по имени пользователя.

        Кандидаты определяются подстрочным совпадением имени пользователя
        (без учёта регистра) либо триграммным сходством выше порога
        ``pg_trgm.similarity_threshold``. Результаты упорядочиваются так:
        сначала полные (точные) вхождения, затем по убыванию степени
        сходства. Применяется пагинация.

        Parameters
        ----------
        query : str
            Подстрока имени пользователя для поиска.
        limit : int
            Максимальное количество записей в выдаче.
        offset : int
            Смещение начала выдачи.

        Returns
        -------
        list[UserSearchReadModel]
            Найденные строки read model: полные вхождения первыми,
            далее по убыванию степени сходства.
        """
        ...

    async def count_by_username(self, query: str) -> int:
        """Посчитать количество учётных записей, соответствующих запросу.

        Применяет тот же набор кандидатов, что и
        :meth:`search_by_username`: подстрочное совпадение либо
        триграммное сходство выше порога.

        Parameters
        ----------
        query : str
            Подстрока имени пользователя для поиска.

        Returns
        -------
        int
            Количество строк read model, соответствующих запросу.
        """
        ...
