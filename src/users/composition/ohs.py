from sqlalchemy.ext.asyncio import AsyncEngine

from src.shared.application.ohs.users import AccountExistenceChecker
from src.users.infrastructure.adapters.ohs import SqlAlchemyAccountExistenceChecker


def build_account_existence_checker(*, engine: AsyncEngine) -> AccountExistenceChecker:
    """Создать OHS-проверку существования активных учётных записей.

    Создаёт реализацию контракта OHS контекста Users
    (:class:`AccountExistenceChecker`), доступную другим bounded contexts
    для проверки существования учётных записей по их идентификаторам.
    Экземпляр не имеет состояния и может использоваться повторно.

    Parameters
    ----------
    engine : AsyncEngine
        Асинхронный движок SQLAlchemy для открытия коротких
        read-соединений проверки существования.

    Returns
    -------
    AccountExistenceChecker
        Реализация проверки существования активных учётных записей.
    """
    return SqlAlchemyAccountExistenceChecker(engine=engine)
