from sqlalchemy import RowMapping, case, func, or_, select, text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncConnection
from sqlalchemy.sql.elements import ColumnElement

from src.users.application.dto.read_models import UserSearchReadModel
from src.users.infrastructure.read_models import user_search_read_model

_TRIGRAM_MIN_LEN = 3
"""Минимальная длина запроса для использования триграммного сходства.

pg_trgm не формирует триграммы для строк короче трёх символов, поэтому
запросы меньшей длины обрабатываются через ``LIKE '%query%'`` без
привлечения оператора ``%`` и индекса ``ix_user_search_username_trgm``.
"""

_ESCAPE_LIKE_CHAR = "\\"
"""Символ экранирования спецсимволов в паттернах ``LIKE``/``ILIKE``.

Используется как значение параметра ``escape`` при построении паттерна
в :meth:`SqlAlchemyUserSearchReader._escape_like_pattern` и в вызовах
``ilike(..., escape=_ESCAPE_LIKE_CHAR)``. Позволяет трактовать символы
``%`` и ``_`` в пользовательском запросе как литералы, а не как
спецсимволы шаблона ``LIKE``.

Notes
-----
Сам символ обратного слэша при подстановке в паттерн экранируется
первым (удваивается), чтобы он не был ошибочно воспринят как начало
управляющей последовательности.
"""

_TRIGRAM_THRESHOLD = 0.2
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
            text(f"SET LOCAL pg_trgm.similarity_threshold = {_TRIGRAM_THRESHOLD}"),
        )

    @staticmethod
    def _escape_like_pattern(query: str) -> str:
        """Экранировать спецсимволы подстроки для ``ILIKE``.

        Экранирует обратный слэш, ``%`` и ``_``, чтобы они трактовались
        как литералы при использовании в ``ILIKE ... ESCAPE '\\'``.

        Parameters
        ----------
        query : str
            Подстрока поиска, введённая пользователем.

        Returns
        -------
        str
            Строковое представление экранированной подстроки для подстановки в паттерн.
        """
        return (
            query.replace(_ESCAPE_LIKE_CHAR, _ESCAPE_LIKE_CHAR * 2)
            .replace("%", f"{_ESCAPE_LIKE_CHAR}%")
            .replace("_", f"{_ESCAPE_LIKE_CHAR}_")
        )

    @staticmethod
    def _build_candidates_predicate(
        normalized: str, escaped: str
    ) -> ColumnElement[bool]:
        """Построить предикат отбора кандидатов для поиска.

        Для запросов короче :data:`_TRIGRAM_MIN_LEN` символов используется
        только подстрочное совпадение ``ILIKE '%query%'``. Для запросов
        от трёх символов предикат расширяется триграммным оператором
        ``%`` (``username % query``), что задействует индекс
        ``ix_user_search_username_trgm`` и возвращает кандидатов с
        ``similarity >= pg_trgm.similarity_threshold``.

        Parameters
        ----------
        normalized : str
            Нормализованная (``.strip().lower()``) строка поиска,
            используемая для сравнений без учёта регистра и в операторе
            триграммного сходства.
        escaped : str
            Экранированная строка поиска, безопасная для подстановки в
            ``ILIKE`` с параметром ``escape``.

        Returns
        -------
        ColumnElement[bool]
            Предикат для ``WHERE``-клаузы SQLAlchemy.
        """
        lower_username = func.lower(user_search_read_model.c.username)

        if len(normalized) < _TRIGRAM_MIN_LEN:
            return lower_username.like(f"%{escaped}%", escape=_ESCAPE_LIKE_CHAR)

        return or_(
            lower_username.op("%")(normalized),
            lower_username.like(f"{escaped}%", escape=_ESCAPE_LIKE_CHAR),
        )

    async def search_by_username(
        self, query: str, limit: int, offset: int
    ) -> list[UserSearchReadModel]:
        """Выполнить нечёткий поиск учётных записей по имени пользователя.

        Кандидаты определяются предикатом :meth:`_build_candidates_predicate`:

        * подстрока - ``username ILIKE '%<query>%'`` (с экранированием
          спецсимволов), что сохраняет подстрочный поиск, в том числе для
          коротких запросов (короче трёх символов), где триграммное
          сходство неприменимо;
        * сходство триграмм - ``username % <query>``, подключаемое для
          запросов от трёх символов и использующее триграммный GIN-индекс
          при пороге ``pg_trgm.similarity_threshold``.

        Результаты упорядочиваются так: сначала точное совпадение имени
        пользователя без учёта регистра (``lower(username) = lower(query)``),
        затем - по наличию поисковой подстроки в имени пользователя
        (``username % query``), по убыванию триграммного сходства
        ``similarity()``, напоследок - по самому ``username`` для детерминированного
        вывода.

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
        if not (normalized := query.strip().lower()):
            return []

        escaped = self._escape_like_pattern(normalized)
        lower_username = func.lower(user_search_read_model.c.username)

        await self._apply_trigram_threshold()

        rank = case(
            (lower_username == normalized, 0.0),
            (lower_username.like(f"{escaped}%", escape=_ESCAPE_LIKE_CHAR), 1.0),
            (lower_username.like(f"%{escaped}%", escape=_ESCAPE_LIKE_CHAR), 2.0),
            else_=3.0,
        )
        similarity_score = func.similarity(lower_username, normalized)

        result = await self._connection.execute(
            select(
                user_search_read_model.c.identity_id,
                user_search_read_model.c.profile_id,
                user_search_read_model.c.username,
                user_search_read_model.c.display_name,
                user_search_read_model.c.avatar_url,
            )
            .where(self._build_candidates_predicate(normalized, escaped))
            .order_by(rank, similarity_score.desc(), user_search_read_model.c.username)
            .slice(offset, offset + limit)
        )

        return [self._row_to_read_model(row) for row in result.mappings()]

    async def count_by_username(self, query: str) -> int:
        """Посчитать количество учётных записей, соответствующих запросу.

        Применяет тот же набор кандидатов, что и
        :meth:`search_by_username` (через :meth:`_build_candidates_predicate`):
        подстрочное совпадение либо, для запросов от трёх символов,
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
        if not (normalized := query.strip().lower()):
            return 0

        escaped = self._escape_like_pattern(normalized)

        await self._apply_trigram_threshold()

        result = await self._connection.scalar(
            select(func.count())
            .select_from(user_search_read_model)
            .where(self._build_candidates_predicate(normalized, escaped))
        )

        return result or 0

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
