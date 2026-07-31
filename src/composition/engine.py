from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from src.composition.settings import get_settings


@lru_cache
def build_engine() -> AsyncEngine:
    """Создать асинхронный движок SQLAlchemy для подключения к PostgreSQL.

    Единственный экземпляр движка создаётся при первом обращении
    и переиспользуется всеми компонентами приложения на протяжении
    всего времени жизни процесса. Движок инкапсулирует пул соединений,
    поэтому его повторное создание привело бы к неоправданному
    расходу ресурсов.

    Returns
    -------
    AsyncEngine
        Асинхронный движок SQLAlchemy, настроенный на DSN из
        глобальных настроек приложения.

    Notes
    -----
    Результат кэшируется через ``lru_cache`` (ADR-0001, п. 2 ответов
    разработчику): пул соединений с БД является дорогим ресурсом уровня
    Infrastructure/Composition, поэтому допускается единственный
    экземпляр на всё приложение. Закрытие движка (``dispose``)
    выполняется при завершении работы приложения в lifespan.
    """
    return create_async_engine(get_settings().POSTGRES_DSN.encoded_string())
