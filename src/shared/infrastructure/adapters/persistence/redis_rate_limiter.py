import hashlib
import hmac
import re

from redis.asyncio import Redis as AsyncRedis

from src.shared.application.dto import RateLimitDecision
from src.shared.application.exceptions import InvalidRateLimitParametersError

_RATE_LIMIT_KEY_PREFIX = "rate-limit:"
"""Префикс Redis-ключа ограничителя частоты запросов."""

_RATE_LIMIT_KEY_SEPARATOR = ":"
"""Разделитель названия операции и идентификатора источника в ключе."""

_OPERATION_PATTERN = re.compile(r"^[a-z0-9]+(?:[-_][a-z0-9]+)*$")
"""Регулярное выражение, допускающее обозначение операции.

Название операции сохраняется в Redis в открытом виде, поэтому
допускаются только строчные буквы, цифры и одиночные разделители
``-`` либо ``_``. Ограничение исключает попадание в ключ
произвольных пользовательских данных и сохраняет однозначное
разделение ключа по ``:``.
"""


class RedisRateLimiter:
    """Реализация порта ``RateLimiter`` на основе Redis.

    Использует неподвижное окно: счётчик запросов хранится
    в Redis под ключом, производным от операции и источника запроса.
    Продолжительность окна задаётся временем жизни (TTL) счётчика,
    поэтому отдельная метка окончания окна в хранилище
    не требуется.

    Окно устанавливается одной командой ``SET ... NX EX``, которая
    создаёт счётчик только если ключ отсутствует. Таким образом
    окно не продлевается активностью внутри него, а его создание
    атомарно. Последующие обращения по тому же ключу только
    увеличивают значение счётчика.

    Parameters
    ----------
    client : AsyncRedis
        Асинхронный клиент Redis.
    key_secret : bytes
        Секретный ключ, которым подписывается обозначение источника
        запроса при вычислении идентификатора счётчика.

    Notes
    -----
    Реализация удовлетворяет протоколу ``RateLimiter``
    структурно (duck typing) без явного наследования.

    Идентификатор счётчика образуется как HMAC-SHA256 от обозначения
    источника запроса: обычный хеш здесь непригоден, поскольку
    множество допустимых значений источника невелико (адреса
    электронной почты, адреса узлов) и открытый хеш поддаётся
    исчерпывающему перебору. Ключевая подпись делает перебор
    невозможным без знания секрета.

    Смена ``key_secret`` обесценивает все существующие счётчики:
    источники получают полное окно заново. Вращение секрета
    допустимо и не требует пересоздания самих счётчиков.
    """

    def __init__(self, client: AsyncRedis, *, key_secret: bytes) -> None:
        self._client = client
        self._key_secret = key_secret

    @staticmethod
    def _build_rate_limit_key(
        operation: str, subject: str, *, key_secret: bytes
    ) -> str:
        """Сформировать Redis-ключ счётчика запросов.

        Название операции включается в ключ в открытом виде, чтобы
        по перечню ключей Redis было видно, какая операция
        ограничивается. Обозначение источника запроса включается
        только в виде HMAC-SHA256, что не позволяет восстановить
        исходное значение по идентификатору счётчика.

        Parameters
        ----------
        operation : str
            Обозначение ограничиваемой операции.
        subject : str
            Обозначение источника запроса.
        key_secret : bytes
            Секретный ключ подписи идентификатора источника.

        Returns
        -------
        str
            Redis-ключ вида ``rate-limit:{операция}:{подпись}``.

        Raises
        ------
        InvalidRateLimitParametersError
            Если ``operation`` не соответствует допустимому формату
            либо ``operation`` или ``subject`` пусты.
        """
        normalized_operation = operation.strip()

        if not _OPERATION_PATTERN.fullmatch(normalized_operation):
            raise InvalidRateLimitParametersError(
                "Rate limit operation must match "
                + f"{_OPERATION_PATTERN.pattern}, got {operation!r}."
            )

        normalized_subject = subject.strip()

        if not normalized_subject:
            raise InvalidRateLimitParametersError(
                "Rate limit subject must be a non-empty string."
            )

        digest = hmac.new(
            key_secret, normalized_subject.encode("utf-8"), hashlib.sha256
        ).hexdigest()

        return _RATE_LIMIT_KEY_PREFIX + _RATE_LIMIT_KEY_SEPARATOR.join(
            (normalized_operation, digest)
        )

    @staticmethod
    def _resolve_window_remaining(ttl: int | None, *, window_seconds: int) -> int:
        """Нормализовать ответ ``TTL`` к остатку окна ограничения.

        Redis сообщает об отсутствии заданного срока значением ``-1``,
        а об отсутствии ключа - ``-2``. Оба отрицательных значения
        означают, что остаток окна неизвестен, и трактуются как полная
        продолжительность окна: ограничение по времени в этом случае
        не действует. Отсутствующий ответ (``None``) не является
        допустимым результатом ``TTL`` и обрабатывается так же.

        Parameters
        ----------
        ttl : int | None
            Ответ команды ``TTL`` на ключ счётчика.
        window_seconds : int
            Продолжительность окна ограничения в секундах.

        Returns
        -------
        int
            Остаток окна в секундах.
        """
        if ttl is None or ttl < 0:
            return window_seconds

        return ttl

    async def acquire(
        self,
        operation: str,
        subject: str,
        *,
        limit: int,
        window_seconds: int,
    ) -> RateLimitDecision:
        """Зарегистрировать запрос и получить решение по лимиту.

        Parameters
        ----------
        operation : str
            Обозначение ограничиваемой операции: сохраняется
            в ключе счётчика в открытом виде.
        subject : str
            Обозначение источника запроса: сохраняется в ключе
            счётчика только в виде HMAC-SHA256.
        limit : int
            Максимальное количество запросов, разрешённое в окне.
        window_seconds : int
            Продолжительность окна ограничения в секундах.

        Returns
        -------
        RateLimitDecision
            Вердикт по текущему запросу и значения счётчиков.
            Поле ``retry_after`` заполняется только при превышении
            лимита: для разрешённого запроса оно равно нулю.

        Raises
        ------
        InvalidRateLimitParametersError
            Если ``limit`` или ``window_seconds`` не являются
            положительными целыми числами, ``operation`` не
            соответствует допустимому формату либо ``operation``
            или ``subject`` пусты.
        """
        if limit <= 0 or window_seconds <= 0:
            raise InvalidRateLimitParametersError(
                "Rate limit parameters must be positive integers: "
                + f"limit={limit}, window_seconds={window_seconds}"
            )

        redis_key = self._build_rate_limit_key(
            operation, subject, key_secret=self._key_secret
        )

        async with self._client.pipeline(transaction=True) as pipeline:
            _ = pipeline.set(redis_key, 0, ex=window_seconds, nx=True)
            _ = pipeline.incr(redis_key)
            _ = pipeline.ttl(redis_key)

            _, count, ttl = await pipeline.execute()

        window_remaining = self._resolve_window_remaining(
            ttl, window_seconds=window_seconds
        )
        count = int(count)
        allowed = count <= limit

        return RateLimitDecision(
            allowed=allowed,
            limit=limit,
            remaining=max(0, limit - count),
            retry_after=0 if allowed else max(1, window_remaining),
            reset_after=max(1, window_remaining),
        )
