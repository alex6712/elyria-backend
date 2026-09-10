from typing import Any

from sqlalchemy import RowMapping, case, func, select, text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncConnection

from src.users.application.dto.read_models import UserSearchReadModel
from src.users.infrastructure.read_models import user_search_read_model

TRIGRAM_THRESHOLD = 0.2
"""Нижняя граница сходства триграмм для нечёткого совпадения username.

Задаётся через GUC ``pg_trgm.similarity_threshold``, который использует
индексируемый оператор ``text % text``. Значение подобрано на характерных
username'ах: при пороге 0.2 поиск ``alex`` находит ``alix`` (0.25),
а заведомо нерелевантные пары (например, ``alice``/``john``) отсекаются.
"""


class SqlAlchemyUserSearchReader:
    """Источник данных read model поиска пользователей на основе SQLAlchemy Core.

    Реализует операции записи (обслуживание read model обработчиками
    доменных событий) и чтения (нечёткий поиск по имени пользователя)
    над таблицей ``user_search_read_model``.

    Parameters
    ----------
    connection : AsyncConnection
        Асинхронное подключение к базе данных SQLAlchemy.

    Notes
    -----
    Удовлетворяет протоколу ``UserSearchReader`` структурно
    (duck typing) без явного наследования.
    """

    def __init__(self, connection: AsyncConnection) -> None:
        self._connection = connection

    async def upsert(self, read_model: UserSearchReadModel) -> None:
        """Создать либо обновить строку read model для учётной записи.

        Выполняет upsert (``INSERT ... ON CONFLICT``) по естественному
        ключу ``identity_id``. Операция идемпотентна: при существующей
        строке обновляются профильные данные и метка изменения.

        Parameters
        ----------
        read_model : UserSearchReadModel
            Денормализованные данные учётной записи и профиля.
        """
        _ = await self._connection.execute(
            pg_insert(user_search_read_model)
            .values(
                identity_id=read_model.identity_id,
                profile_id=read_model.profile_id,
                username=read_model.username,
                display_name=read_model.display_name,
                avatar_url=read_model.avatar_url,
            )
            .on_conflict_do_update(
                index_elements=[user_search_read_model.c.identity_id],
                set_={
                    "profile_id": read_model.profile_id,
                    "username": read_model.username,
                    "display_name": read_model.display_name,
                    "avatar_url": read_model.avatar_url,
                },
            )
        )

    async def _apply_trigram_threshold(self) -> None:
        """Установить порог сходства триграмм в рамках текущей транзакции.

        Оператор ``text % text`` сравнивает сходство с GUC
        ``pg_trgm.similarity_threshold``. Значение приложения отлично
        от глобального порога сервера, поэтому оно выставляется через
        ``SET LOCAL``: действует только до конца текущей транзакции и
        не влияет на другие запросы соединения.

        Notes
        -----
        Метод обязан вызываться внутри транзакции (``SET LOCAL`` вне
        транзакционного блока приводит к ошибке PostgreSQL). Гарантию
        обеспечивает единица работы ``UsersUnitOfWork``.
        """
        _ = await self._connection.execute(
            text(f"SET LOCAL pg_trgm.similarity_threshold = {TRIGRAM_THRESHOLD}")
        )

    @staticmethod
    def _escape_like_pattern(query: str) -> Any:
        """Экранировать спецсимволы подстроки для ``ILIKE``.

        Экранирует обратный слэш, ``%`` и ``_``, чтобы они трактовались
        как литералы при использовании в ``ILIKE ... ESCAPE '\\'``.

        Parameters
        ----------
        query : str
            Подстрока поиска, введённая пользователем.

        Returns
        -------
        Any
            Выражение экранированной подстроки для подстановки в паттерн.
        """
        return func.replace(
            func.replace(func.replace(query, "\\", "\\\\"), "%", "\\%"), "_", "\\_"
        )

    async def search_by_username(
        self, query: str, limit: int, offset: int
    ) -> list[UserSearchReadModel]:
        """Выполнить нечёткий поиск учётных записей по имени пользователя.

        Кандидаты определяются двумя условиями, объединёнными через ``OR``:

        * подстрока - ``username ILIKE '%<query>%'`` (с экранированием
          спецсимволов), что сохраняет подстрочный поиск, в том числе для
          коротких запросов, где триграммное сходство неприменимо;
        * сходство триграмм - ``username % <query>``, использующее
          триграммный GIN-индекс при пороге ``pg_trgm.similarity_threshold``.

        Результаты упорядочиваются так: сначала точное совпадение имени
        пользователя без учёта регистра (``lower(username) = lower(query)``),
        затем - по убыванию триграммного сходства ``similarity()``.

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
        escaped = self._escape_like_pattern(query)
        pattern = func.concat("%", func.concat(escaped, "%"))

        await self._apply_trigram_threshold()

        result = await self._connection.execute(
            select(user_search_read_model)
            .where(
                user_search_read_model.c.username.ilike(pattern, escape="\\")
                | user_search_read_model.c.username.op("%")(query)
            )
            .order_by(
                case(
                    (
                        func.lower(user_search_read_model.c.username)
                        == func.lower(query),
                        0,
                    ),
                    else_=1,
                ),
                func.similarity(user_search_read_model.c.username, query).desc(),
            )
            .limit(limit)
            .offset(offset)
        )

        return [self._row_to_read_model(row) for row in result.mappings()]

    async def count_by_username(self, query: str) -> int:
        """Посчитать количество учётных записей, соответствующих запросу.

        Применяет тот же набор кандидатов, что и
        :meth:`search_by_username`: подстрочное совпадение либо
        триграммное сходство выше ``pg_trgm.similarity_threshold``.

        Parameters
        ----------
        query : str
            Подстрока имени пользователя для поиска.

        Returns
        -------
        int
            Количество строк read model, соответствующих запросу.
        """
        escaped = self._escape_like_pattern(query)
        pattern = func.concat("%", func.concat(escaped, "%"))

        await self._apply_trigram_threshold()

        result = await self._connection.execute(
            select(func.count())
            .select_from(user_search_read_model)
            .where(
                user_search_read_model.c.username.ilike(pattern, escape="\\")
                | user_search_read_model.c.username.op("%")(query)
            )
        )

        return int(result.scalar_one())

    @staticmethod
    def _row_to_read_model(row: RowMapping) -> UserSearchReadModel:
        """Преобразовать строку результата запроса в read model.

        Parameters
        ----------
        row : RowMapping
            Строка результата запроса (mapping).

        Returns
        -------
        UserSearchReadModel
            Денормализованный read model учётной записи и профиля.
        """
        return UserSearchReadModel(
            identity_id=row["identity_id"],
            profile_id=row["profile_id"],
            username=row["username"],
            display_name=row["display_name"],
            avatar_url=row["avatar_url"],
        )
