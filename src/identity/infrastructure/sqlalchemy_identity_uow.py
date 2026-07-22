from types import TracebackType

from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine, AsyncTransaction

from src.identity.application.ports.persistence import (
    IdentityRepository,
    ProfileRepository,
    SessionRepository,
)
from src.identity.infrastructure.persistence import (
    SqlAlchemyIdentityRepository,
    SqlAlchemyProfileRepository,
    SqlAlchemySessionRepository,
)
from src.shared.application.exception import UnitOfWorkNotEnteredError


class SqlAlchemyIdentityUnitOfWork:
    """SQLAlchemy-реализация Unit of Work контекста Identity.

    Инкапсулирует управление соединением и транзакцией СУБД для одной
    единицы работы (Unit of Work) в ограниченном контексте Identity.
    Гарантирует, что все репозитории (``identities``, ``profiles``,
    ``sessions``), созданные в рамках одного использования этого объекта,
    работают через одно и то же соединение и одну транзакцию, что
    обеспечивает атомарность операций записи.

    Parameters
    ----------
    engine : AsyncEngine
        Асинхронный движок SQLAlchemy, используемый для открытия
        соединения при входе в контекстный менеджер.

    Attributes
    ----------
    identities : IdentityRepository
        Репозиторий учётных записей.
    profiles : ProfileRepository
        Репозиторий профилей пользователей.
    sessions : SessionRepository
        Репозиторий пользовательских сессий.

    Notes
    -----
    Все репозитории создаются лениво при первом обращении и привязываются
    к текущему открытому соединению.
    """

    def __init__(self, engine: AsyncEngine) -> None:
        self._engine = engine

        self._connection: AsyncConnection | None = None
        self._transaction: AsyncTransaction | None = None

        self._identities: IdentityRepository | None = None
        self._profiles: ProfileRepository | None = None
        self._sessions: SessionRepository | None = None

    @property
    def identities(self) -> IdentityRepository:
        """Репозиторий учётных записей.

        При первом обращении создаёт ``SqlAlchemyIdentityRepository``,
        используя текущее активное соединение, и кэширует его на всё
        время жизни единицы работы.

        Returns
        -------
        IdentityRepository
            Репозиторий, работающий в рамках текущей транзакции.

        Raises
        ------
        UnitOfWorkNotEnteredError
            Если единица работы ещё не была открыта через
            ``async with`` (соединение отсутствует).
        """
        if self._identities is None:
            self._identities = SqlAlchemyIdentityRepository(
                self._ensure_active_connection()
            )

        return self._identities

    @property
    def profiles(self) -> ProfileRepository:
        """Репозиторий профилей пользователей.

        При первом обращении создаёт ``SqlAlchemyProfileRepository``,
        используя текущее активное соединение, и кэширует его на всё
        время жизни единицы работы.

        Returns
        -------
        ProfileRepository
            Репозиторий, работающий в рамках текущей транзакции.

        Raises
        ------
        UnitOfWorkNotEnteredError
            Если единица работы ещё не была открыта через
            ``async with`` (соединение отсутствует).
        """
        if self._profiles is None:
            self._profiles = SqlAlchemyProfileRepository(
                self._ensure_active_connection()
            )

        return self._profiles

    @property
    def sessions(self) -> SessionRepository:
        """Репозиторий пользовательских сессий.

        При первом обращении создаёт ``SqlAlchemySessionRepository``,
        используя текущее активное соединение, и кэширует его на всё
        время жизни единицы работы.

        Returns
        -------
        SessionRepository
            Репозиторий, работающий в рамках текущей транзакции.

        Raises
        ------
        UnitOfWorkNotEnteredError
            Если единица работы ещё не была открыта через
            ``async with`` (соединение отсутствует).
        """
        if self._sessions is None:
            self._sessions = SqlAlchemySessionRepository(
                self._ensure_active_connection()
            )

        return self._sessions

    def _ensure_active_connection(self) -> AsyncConnection:
        """Вернуть текущее активное соединение либо выбросить ошибку.

        Внутренний метод-хелпер, вызываемый свойствами-репозиториями
        перед их ленивой инициализацией, чтобы гарантировать, что
        единица работы была открыта.

        Returns
        -------
        AsyncConnection
            Активное соединение, открытое в ``__aenter__``.

        Raises
        ------
        UnitOfWorkNotEnteredError
            Если ``self._connection`` ещё не установлено, то есть
            ``__aenter__`` не вызывался (или уже был вызван ``__aexit__``).
        """
        if self._connection is None:
            raise UnitOfWorkNotEnteredError(
                "IdentityUnitOfWork must be entered before use."
            )

        return self._connection

    def _ensure_active_transaction(self) -> AsyncTransaction:
        """Вернуть текущую активную транзакцию либо выбросить ошибку.

        Внутренний метод-хелпер, вызываемый методами фиксации и отката
        перед выполнением операции, чтобы гарантировать, что единица
        работы была открыта.

        Returns
        -------
        AsyncTransaction
            Активная транзакция, открытая в ``__aenter__``.

        Raises
        ------
        UnitOfWorkNotEnteredError
            Если ``self._transaction`` ещё не установлена, то есть
            ``__aenter__`` не вызывался (или уже был вызван ``__aexit__``).
        """
        if self._transaction is None:
            raise UnitOfWorkNotEnteredError(
                "IdentityUnitOfWork must be entered before use."
            )

        return self._transaction

    async def commit(self) -> None:
        """Зафиксировать результаты текущей единицы работы.

        Подтверждает текущую транзакцию (``COMMIT``). После вызова все
        изменения, сделанные через репозитории в рамках этой единицы
        работы, становятся постоянными в хранилище.

        Raises
        ------
        UnitOfWorkNotEnteredError
            Если единица работы не была открыта (``__aenter__`` не
            вызывался), то есть ``self._transaction is None``.

        Notes
        -----
        Обычно вызывается явно в конце бизнес-сценария, после того
        как все необходимые изменения через репозитории выполнены.
        Если исключений не было и ``commit()`` не был вызван явно,
        ``__aexit__`` всё равно выполнит commit автоматически.
        """
        await self._ensure_active_transaction().commit()

    async def rollback(self) -> None:
        """Отменить результаты текущей единицы работы.

        Откатывает текущую транзакцию (``ROLLBACK``). Все изменения,
        сделанные через репозитории в рамках этой единицы работы, не
        применяются к хранилищу.

        Raises
        ------
        UnitOfWorkNotEnteredError
            Если единица работы не была открыта (``__aenter__`` не
            вызывался), то есть ``self._transaction is None``.

        Notes
        -----
        Вызывается автоматически из ``__aexit__``, если тело блока
        ``async with`` завершилось с исключением. Также может быть
        вызван явно, если бизнес-логика решает отменить изменения
        без выброса исключения.
        """
        await self._ensure_active_transaction().rollback()

    async def __aenter__(self) -> SqlAlchemyIdentityUnitOfWork:
        """Начать новую единицу работы.

        Открывает новое соединение через движок и начинает новую
        транзакцию. До вызова этого метода обращение к свойствам
        репозиториев (``identities``, ``profiles``, ``sessions``) приведёт
        к исключению ``UnitOfWorkNotEnteredError``.

        Returns
        -------
        SqlAlchemyIdentityUnitOfWork
            Тот же экземпляр, готовый к использованию внутри блока
            ``async with``.
        """
        self._connection = await self._engine.connect()
        self._transaction = await self._connection.begin()

        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Завершить текущую единицу работы.

        Если тело блока ``async with`` завершилось без исключений -
        фиксирует транзакцию (``commit``); если возникло исключение -
        откатывает её (``rollback``). В любом случае соединение
        закрывается, а внутреннее состояние (соединение, транзакция,
        кэшированные репозитории) сбрасывается, чтобы объект нельзя
        было по ошибке переиспользовать без повторного ``__aenter__``.

        Parameters
        ----------
        exc_type : type[BaseException] | None
            Тип исключения, возникшего в теле блока ``async with``,
            либо ``None``, если исключений не было.
        exc : BaseException | None
            Экземпляр исключения, возникшего в теле блока, либо
            ``None``, если исключений не было.
        traceback : TracebackType | None
            Трассировка стека, соответствующая исключению, либо
            ``None``, если исключений не было.

        Raises
        ------
        UnitOfWorkNotEnteredError
            Если ``self._connection is None`` на момент выхода, что
            означает нарушение инварианта (``__aenter__`` должен был
            установить соединение).

        Notes
        -----
        Закрытие соединения выполняется в блоке ``finally``, поэтому
        оно произойдёт даже если ``commit()``/``rollback()`` выбросят
        исключение.
        """
        try:
            if exc is None:
                await self.commit()
            else:
                await self.rollback()
        finally:
            self._transaction = None

            self._identities = None
            self._profiles = None
            self._sessions = None

            await self._ensure_active_connection().close()

            self._connection = None
