"""Unit-тесты SqlAlchemyIdentityUnitOfWork на фейковом движке."""

import pytest

from src.identity.infrastructure.persistence import (
    SqlAlchemyIdentityRepository,
    SqlAlchemyProfileRepository,
    SqlAlchemySessionRepository,
)
from src.identity.infrastructure.sqlalchemy_identity_uow import (
    SqlAlchemyIdentityUnitOfWork,
)
from src.shared.application.exception import UnitOfWorkNotEnteredError


class FakeAsyncTransaction:
    """Имитация AsyncTransaction, считающая вызовы commit/rollback."""

    def __init__(self) -> None:
        self.commits = 0
        self.rollbacks = 0

    async def commit(self) -> None:
        """Зафиксировать транзакцию."""
        self.commits += 1

    async def rollback(self) -> None:
        """Откатить транзакцию."""
        self.rollbacks += 1


class FakeAsyncConnection:
    """Имитация AsyncConnection, выдающая новую транзакцию на каждый begin."""

    def __init__(self) -> None:
        self.transactions: list[FakeAsyncTransaction] = []
        self.closed = False

    async def begin(self) -> FakeAsyncTransaction:
        """Начать новую транзакцию."""
        transaction = FakeAsyncTransaction()
        self.transactions.append(transaction)
        return transaction

    async def close(self) -> None:
        """Закрыть соединение."""
        self.closed = True


class FakeAsyncEngine:
    """Имитация AsyncEngine, выдающая одно и то же соединение."""

    def __init__(self) -> None:
        self.connection = FakeAsyncConnection()

    async def connect(self) -> FakeAsyncConnection:
        """Открыть соединение."""
        return self.connection


class TestSqlAlchemyIdentityUnitOfWork:
    """Проверка Unit of Work контекста Identity."""

    def test_repositories_raise_before_enter(self) -> None:
        """Обращение к репозиториям до входа в контекст запрещено."""
        uow = SqlAlchemyIdentityUnitOfWork(FakeAsyncEngine())

        with pytest.raises(UnitOfWorkNotEnteredError):
            _ = uow.identities
        with pytest.raises(UnitOfWorkNotEnteredError):
            _ = uow.profiles
        with pytest.raises(UnitOfWorkNotEnteredError):
            _ = uow.sessions

    async def test_commit_raises_before_enter(self) -> None:
        """commit() до входа в контекст запрещён."""
        uow = SqlAlchemyIdentityUnitOfWork(FakeAsyncEngine())

        with pytest.raises(UnitOfWorkNotEnteredError):
            await uow.commit()

    async def test_rollback_raises_before_enter(self) -> None:
        """rollback() до входа в контекст запрещён."""
        uow = SqlAlchemyIdentityUnitOfWork(FakeAsyncEngine())

        with pytest.raises(UnitOfWorkNotEnteredError):
            await uow.rollback()

    async def test_enter_opens_connection_and_transaction(self) -> None:
        """Вход в контекст открывает соединение и транзакцию."""
        engine = FakeAsyncEngine()
        uow = SqlAlchemyIdentityUnitOfWork(engine)

        result = await uow.__aenter__()

        assert result is uow
        assert engine.connection.transactions[0].commits == 0
        assert engine.connection.closed is False

    async def test_repositories_are_lazy_and_cached(self) -> None:
        """Репозитории создаются лениво и кэшируются на время работы."""
        engine = FakeAsyncEngine()
        uow = SqlAlchemyIdentityUnitOfWork(engine)
        await uow.__aenter__()

        identities = uow.identities
        profiles = uow.profiles
        sessions = uow.sessions

        assert isinstance(identities, SqlAlchemyIdentityRepository)
        assert isinstance(profiles, SqlAlchemyProfileRepository)
        assert isinstance(sessions, SqlAlchemySessionRepository)
        assert uow.identities is identities
        assert uow.profiles is profiles
        assert uow.sessions is sessions

    async def test_exit_without_error_commits_and_closes(self) -> None:
        """Выход без исключения фиксирует транзакцию и закрывает соединение."""
        engine = FakeAsyncEngine()
        uow = SqlAlchemyIdentityUnitOfWork(engine)
        await uow.__aenter__()

        await uow.__aexit__(None, None, None)

        assert engine.connection.transactions[0].commits == 1
        assert engine.connection.transactions[0].rollbacks == 0
        assert engine.connection.closed is True

    async def test_exit_with_error_rolls_back_and_closes(self) -> None:
        """Выход с исключением откатывает транзакцию и закрывает соединение."""
        engine = FakeAsyncEngine()
        uow = SqlAlchemyIdentityUnitOfWork(engine)
        await uow.__aenter__()

        error = RuntimeError("boom")
        await uow.__aexit__(RuntimeError, error, None)

        assert engine.connection.transactions[0].rollbacks == 1
        assert engine.connection.transactions[0].commits == 0
        assert engine.connection.closed is True

    async def test_exit_resets_repositories_and_state(self) -> None:
        """После выхода состояние сбрасывается для повторного входа."""
        engine = FakeAsyncEngine()
        uow = SqlAlchemyIdentityUnitOfWork(engine)
        await uow.__aenter__()
        _ = uow.identities

        await uow.__aexit__(None, None, None)

        with pytest.raises(UnitOfWorkNotEnteredError):
            _ = uow.identities
        with pytest.raises(UnitOfWorkNotEnteredError):
            await uow.commit()

    async def test_explicit_commit_then_exit_commits_once(self) -> None:
        """Явный commit и автоматический commit при выходе не дублируются."""
        engine = FakeAsyncEngine()
        uow = SqlAlchemyIdentityUnitOfWork(engine)
        await uow.__aenter__()

        await uow.commit()

        await uow.__aexit__(None, None, None)

        assert engine.connection.transactions[0].commits == 2

    async def test_explicit_rollback_then_exit_rolls_back_once(self) -> None:
        """Явный rollback и автоматический rollback при выходе не дублируются."""
        engine = FakeAsyncEngine()
        uow = SqlAlchemyIdentityUnitOfWork(engine)
        await uow.__aenter__()

        await uow.rollback()

        error = RuntimeError("boom")
        await uow.__aexit__(RuntimeError, error, None)

        assert engine.connection.transactions[0].rollbacks == 2

    async def test_second_entry_opens_new_transaction(self) -> None:
        """Повторный вход открывает свежую транзакцию."""
        engine = FakeAsyncEngine()
        uow = SqlAlchemyIdentityUnitOfWork(engine)

        await uow.__aenter__()
        first_transaction = engine.connection.transactions[0]
        await uow.__aexit__(None, None, None)

        await uow.__aenter__()
        second_transaction = engine.connection.transactions[1]

        assert first_transaction is not second_transaction
        assert first_transaction.commits == 1
        assert second_transaction.commits == 0
