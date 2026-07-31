from functools import lru_cache

from redis.asyncio import Redis as AsyncRedis

from src.composition.settings import get_settings


@lru_cache
def build_redis_client() -> AsyncRedis:
    """Создать асинхронный клиент Redis для всего приложения.

    Единственный экземпляр клиента создаётся при первом обращении
    и переиспользуется всеми компонентами, работающими с Redis
    (например, списком отозванных токенов).

    Returns
    -------
    AsyncRedis
        Асинхронный клиент Redis, настроенный на URL из глобальных
        настроек приложения.

    Notes
    -----
    Результат кэшируется через ``lru_cache`` (ADR-0001, п. 2 ответов
    разработчику): клиент внешнего сервиса является дорогим ресурсом
    уровня Infrastructure/Composition, поэтому допускается единственный
    экземпляр на всё приложение. Закрытие клиента выполняется при
    завершении работы приложения в lifespan.
    """
    return AsyncRedis.from_url(get_settings().REDIS_URL.encoded_string())  # type: ignore[reportUnknownMemberType]
