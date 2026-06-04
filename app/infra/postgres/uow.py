from typing import Any, Self, TypeVar, cast

from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine

from app.core.exceptions.base import UnitOfWorkContextClosedException
from app.infra.postgres import async_engine
from app.repositories.interface import RepositoryInterface

T = TypeVar("T", bound=RepositoryInterface)


class UnitOfWork:
    """Единица работы (Unit of Work) для управления транзакцией и репозиториями.

    Класс инкапсулирует работу с асинхронным соединением SQLAlchemy, обеспечивает
    атомарность операций (commit/rollback) и управление жизненным циклом репозиториев.

    Parameters
    ----------
    engine : AsyncEngine
        Асинхронный движок SQLAlchemy. По умолчанию используется глобальный
        `async_engine`.

    Attributes
    ----------
    engine : AsyncEngine
        Асинхронный движок SQLAlchemy, используемый для получения соединений.
    _connection : AsyncConnection | None
        Текущее асинхронное соединение с активной транзакцией. Доступно только
        в пределах контекста (`async with UnitOfWork(): ...`); после выхода
        сбрасывается в `None`.
    _repos : dict[type[RepositoryInterface], RepositoryInterface]
        Кэш созданных репозиториев для повторного использования в пределах
        одной транзакции.

    Raises
    ------
    UnitOfWorkContextClosedException
        Если попытаться получить доступ к соединению вне контекстного менеджера.
    """

    def __init__(self, engine: AsyncEngine = async_engine):
        self.engine = engine
        self._connection: AsyncConnection | None = None

        self._repos: dict[type[RepositoryInterface], RepositoryInterface] = {}

    @property
    def connection(self) -> AsyncConnection:
        if self._connection is None:
            raise UnitOfWorkContextClosedException()

        return self._connection

    async def __aenter__(self) -> Self:
        """Вход в асинхронный контекст.

        Получает новое асинхронное соединение из движка, открывает на нём
        транзакцию и возвращает текущий экземпляр `UnitOfWork`.

        Returns
        -------
        UnitOfWork
            Текущий экземпляр `UnitOfWork`.
        """
        self._connection = await self.engine.connect()
        await self._connection.begin()
        return self

    async def __aexit__(self, exc_type: Any, *_: Any) -> None:
        """Выход из асинхронного контекста.

        В случае возникновения ошибки выполняется `rollback`, иначе - `commit`.
        После завершения соединение закрывается, кэш репозиториев очищается,
        а ссылка на соединение сбрасывается.

        Parameters
        ----------
        exc_type : Any
            Тип исключения, если оно возникло.
        """
        try:
            if exc_type is not None:
                await self.rollback()
            else:
                await self.commit()
        finally:
            await self.connection.close()

            self._connection = None
            self._repos.clear()

    async def commit(self) -> None:
        """Зафиксировать изменения в базе данных.

        Применяет все изменения, сделанные в рамках текущей транзакции,
        к базе данных. После успешного вызова все операции insert, update
        и delete становятся постоянными.

        Raises
        ------
        UnitOfWorkContextClosedException
            Если вызван вне контекста менеджера (когда соединение не инициализировано).
        SQLAlchemyError
            При возникновении ошибок на уровне базы данных во время фиксации.

        Notes
        -----
        Обычно этот метод вызывается автоматически при выходе из контекстного
        менеджера, если не возникло исключений. Явный вызов может потребоваться
        для промежуточных фиксаций в рамках одной транзакции.
        """
        await self.connection.commit()

    async def rollback(self) -> None:
        """Отменить все изменения в текущей транзакции.

        Откатывает все незафиксированные изменения, сделанные в рамках
        текущей транзакции. После вызова база данных возвращается в состояние,
        которое было до начала транзакции или последнего commit.

        Raises
        ------
        UnitOfWorkContextClosedException
            Если вызван вне контекста менеджера (когда соединение не инициализировано).
        SQLAlchemyError
            При возникновении ошибок на уровне базы данных во время отката.

        Notes
        -----
        Этот метод вызывается автоматически при выходе из контекстного менеджера,
        если в блоке `async with` возникло исключение. Явный вызов может быть
        полезен для отката промежуточных изменений без выхода из контекста.
        """
        await self.connection.rollback()

    def get_repository(self, repo_type: type[T]) -> T:
        """Получить экземпляр репозитория для работы с базой данных.

        Если репозиторий указанного типа ещё не был создан, он будет
        инициализирован с текущим соединением и сохранён в кэше.

        Parameters
        ----------
        repo_type : type[T]
            Класс репозитория, реализующий интерфейс `RepositoryInterface`.

        Returns
        -------
        T
            Экземпляр репозитория, связанный с текущим соединением.
        """
        if repo_type not in self._repos:
            self._repos[repo_type] = repo_type(self.connection)

        return cast(T, self._repos[repo_type])
