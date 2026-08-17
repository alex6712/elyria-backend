import hashlib

from httpx import AsyncClient, HTTPError

from src.users.domain.value_objects import Password

_HIBP_API_URL = "https://api.pwnedpasswords.com"
"""Базовый URL API Pwned Passwords сервиса Have I Been Pwned."""

_HIBP_PREFIX_LENGTH = 5
"""Количество первых hex-символов SHA-1, передаваемых в API
(принцип k-anonymity: полный хеш наружу не уходит)."""

_HIBP_USER_AGENT = "elyria-backend"
"""User-Agent, идентифицирующий приложение (требование HIBP)."""


class HibpCompromisedPasswordChecker:
    """Реализация порта ``CompromisedPasswordChecker`` на основе
    HIBP Pwned Passwords Range API.

    Реализует проверку пароля через k-anonymity диапазонный запрос:
    на внешний сервис отправляется только префикс SHA-1 пароля
    (``_HIBP_PREFIX_LENGTH`` символов), полный хеш остаётся
    в границах приложения.

    Notes
    -----
    Адаптер реализует стратегию fail-open: при любой ошибке
    транспорта или неожиданном HTTP-статусе (включая 404) возвращает
    ``False``, полагая пароль не скомпрометированным. Это исключает
    блокировку регистрации из-за недоступности внешнего сервиса.
    """

    def __init__(self, client: AsyncClient) -> None:
        """Инициализировать адаптер переданным HTTP-клиентом.

        Parameters
        ----------
        client : AsyncClient
            Асинхронный HTTP-клиент с настроенным таймаутом.
            Должен быть общим для всего приложения (как клиент Redis).
        """
        self._client = client

    async def is_compromised(self, password: Password) -> bool:
        """Проверить, встречается ли пароль в базе утечек HIBP.

        Parameters
        ----------
        password : Password
            Пароль в виде объект-значения для проверки.

        Returns
        -------
        bool
            ``True``, если суффикс SHA-1 пароля найден в ответе
            сервиса, иначе ``False``.

        Notes
        -----
        При ошибке транспорта или HTTP-статусе, отличном от 200,
        возвращается ``False`` (fail-open).
        """
        sha1_hash = hashlib.sha1(password.reveal().encode("utf-8")).hexdigest().upper()

        prefix = sha1_hash[:_HIBP_PREFIX_LENGTH]
        suffix = sha1_hash[_HIBP_PREFIX_LENGTH:]

        try:
            response = await self._client.get(
                f"{_HIBP_API_URL}/range/{prefix}",
                headers={"Add-Padding": "true", "User-Agent": _HIBP_USER_AGENT},
            )
        except HTTPError:
            return False

        if response.status_code != 200:
            return False

        return suffix in {
            line.split(":", maxsplit=1)[0].upper()
            for line in response.text.splitlines()
        }
