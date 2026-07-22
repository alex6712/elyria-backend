from types import TracebackType
from typing import Protocol, Self, runtime_checkable

from src.identity.application.ports.persistence import (
    IdentityRepository,
    ProfileRepository,
    SessionRepository,
)


@runtime_checkable
class IdentityUnitOfWork(Protocol):
    """Порт Unit of Work контекста Identity.

    Определяет границу атомарного выполнения операций в контексте
    Identity и предоставляет доступ к репозиториям, участвующим
    в одной единице работы.

    Все изменения, выполненные через репозитории, полученные из
    данного Unit of Work, должны быть применены или отменены как
    единое целое.

    Notes
    -----
    Реализация данного порта должна гарантировать атомарность
    операций и освобождение всех занятых ресурсов после завершения
    единицы работы.
    """

    @property
    def identities(self) -> IdentityRepository:
        """Репозиторий учётных записей.

        Returns
        -------
        IdentityRepository
            Репозиторий для работы с сущностями ``Identity``.

        Raises
        ------
        UnitOfWorkNotEnteredError
            Если единица работы ещё не была открыта через
            ``async with``.
        """
        ...

    @property
    def profiles(self) -> ProfileRepository:
        """Репозиторий профилей пользователей.

        Returns
        -------
        ProfileRepository
            Репозиторий для работы с сущностями ``Profile``.

        Raises
        ------
        UnitOfWorkNotEnteredError
            Если единица работы ещё не была открыта через
            ``async with``.
        """
        ...

    @property
    def sessions(self) -> SessionRepository:
        """Репозиторий пользовательских сессий.

        Returns
        -------
        SessionRepository
            Репозиторий для работы с сущностями ``Session``.

        Raises
        ------
        UnitOfWorkNotEnteredError
            Если единица работы ещё не была открыта через
            ``async with``.
        """
        ...

    async def commit(self) -> None:
        """Зафиксировать результаты текущей единицы работы.

        Raises
        ------
        UnitOfWorkNotEnteredError
            Если единица работы ещё не была открыта через
            ``async with``.

        Notes
        -----
        Данный метод предназначен для ручной фиксации транзакции.
        Обычно реализация вызывает его автоматически при успешном
        завершении контекстного менеджера.
        """
        ...

    async def rollback(self) -> None:
        """Отменить изменения текущей транзакции.

        Raises
        ------
        UnitOfWorkNotEnteredError
            Если единица работы ещё не была открыта через
            ``async with``.

        Notes
        -----
        Данный метод предназначен для ручной отмены транзакции.
        Обычно реализация вызывает его автоматически при возникновении
        исключения внутри контекстного менеджера.
        """
        ...

    async def __aenter__(self) -> Self:
        """Начать новую единицу работы.

        Returns
        -------
        Self
            Экземпляр текущего Unit of Work с готовыми к использованию
            репозиториями.
        """
        ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Завершить текущую единицу работы.

        Parameters
        ----------
        exc_type : type[BaseException] | None
            Тип возникшего исключения либо ``None``, если блок
            завершился успешно.
        exc : BaseException | None
            Экземпляр возникшего исключения либо ``None``.
        traceback : TracebackType | None
            Объект трассировки исключения либо ``None``.

        Notes
        -----
        При нормальном завершении единицы работы её результаты
        должны быть зафиксированы. При возникновении исключения
        все выполненные изменения должны быть отменены.
        """
        ...
