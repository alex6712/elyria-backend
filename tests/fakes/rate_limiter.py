"""Фейк порта ``RateLimiter`` для unit-тестов.

Позволяет программно задать решение ограничителя и зафиксировать
вызовы, не обращаясь к реальному хранилищу счётчиков.
"""

from src.shared.application.dto import RateLimitDecision


class FakeRateLimiter:
    """Фейк ограничителя частоты запросов.

    По умолчанию любой запрос разрешается. Установите
    ``is_allowed_result = False``, чтобы смоделировать
    исчерпание лимита.

    Attributes
    ----------
    calls : list[str]
        Обозначения источников запросов, по которым были выполнены
        вызовы, в порядке вызова.
    is_allowed_result : bool
        Значение поля ``allowed`` в возвращаемом решении.
    """

    def __init__(self, is_allowed_result: bool = True) -> None:
        self.calls: list[str] = []
        self.is_allowed_result = is_allowed_result

    async def acquire(
        self,
        operation: str,  # noqa: ARG002
        subject: str,
        *,
        limit: int,
        window_seconds: int,
    ) -> RateLimitDecision:
        """Зарегистрировать вызов и вернуть настроенное решение.

        Parameters
        ----------
        operation : str
            Обозначение ограничиваемой операции (не используется фейком).
        subject : str
            Обозначение источника запроса (не используется фейком).
        limit : int
            Лимит.
        window_seconds : int
            Продолжительность окна.

        Returns
        -------
        RateLimitDecision
            Решение с ``allowed``, равным ``is_allowed_result``,
            и ``retry_after``, равным 60 секундам при отказе.
        """
        self.calls.append(subject)

        return RateLimitDecision(
            allowed=self.is_allowed_result,
            limit=limit,
            remaining=limit - 1 if self.is_allowed_result else 0,
            retry_after=0 if self.is_allowed_result else 60,
            reset_after=window_seconds,
        )
