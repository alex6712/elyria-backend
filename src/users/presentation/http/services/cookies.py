from typing import Literal

from fastapi import Response


class AuthCookiesProvider:
    """Провайдер HttpOnly-cookie для аутентификации.

    Устанавливает и удаляет HttpOnly-cookie refresh-токена
    в HTTP-ответе. Значения атрибутов cookie (имя, время жизни,
    ``Path``, ``Domain``, ``Secure``, ``SameSite``) передаются
    через DI при сборке контейнера и не зависят от глобальных
    настроек приложения.

    Attributes
    ----------
    refresh_token_cookie_name : str
        Имя cookie с refresh-токеном.
    refresh_token_lifetime_days : int
        Время жизни refresh-токена в днях, определяющее ``Max-Age``
        cookie.
    auth_cookie_path : str
        Значение атрибута ``Path`` cookie.
    auth_cookie_domain : str | None
        Значение атрибута ``Domain`` cookie.
    auth_cookie_secure : bool
        Флаг ``Secure``: передавать cookie только по HTTPS.
    auth_cookie_samesite : Literal["lax", "strict", "none"]
        Значение атрибута ``SameSite`` cookie.

    Notes
    -----
    Cookie помечается флагом ``HttpOnly`` - токен недоступен
    JavaScript-коду на клиенте, что существенно снижает поверхность
    атаки в случае XSS. Время жизни cookie привязано ко времени
    жизни самого refresh-токена, чтобы cookie истекала одновременно
    с истечением токена.
    """

    def __init__(
        self,
        refresh_token_cookie_name: str,
        refresh_token_lifetime_days: int,
        auth_cookie_path: str,
        auth_cookie_domain: str | None,
        auth_cookie_secure: bool,
        auth_cookie_samesite: Literal["lax", "strict", "none"],
    ) -> None:
        self._refresh_token_cookie_name = refresh_token_cookie_name
        self._refresh_token_lifetime_days = refresh_token_lifetime_days
        self._auth_cookie_path = auth_cookie_path
        self._auth_cookie_domain = auth_cookie_domain
        self._auth_cookie_secure = auth_cookie_secure
        self._auth_cookie_samesite: Literal["lax", "strict", "none"] = (
            auth_cookie_samesite
        )

    def set_refresh_token_cookie(self, response: Response, refresh_token: str) -> None:
        """Установить HttpOnly-cookie с refresh-токеном в HTTP-ответ.

        Добавляет в ответ заголовок ``Set-Cookie`` с refresh-токеном
        и атрибутами, переданными в конструктор. Значение ``Max-Age``
        вычисляется из времени жизни refresh-токена в днях.

        Parameters
        ----------
        response : Response
            Объект HTTP-ответа, в который добавляется заголовок
            ``Set-Cookie``.
        refresh_token : str
            Подписанный JWT refresh-токен.

        Notes
        -----
        Метод намеренно не валидирует токен - это ответственность
        вызывающего кода (как правило, Use Case). Здесь выполняется
        только низкоуровневая работа с заголовками HTTP-ответа.
        """
        response.set_cookie(
            key=self._refresh_token_cookie_name,
            value=refresh_token,
            max_age=self._refresh_token_lifetime_days * 24 * 60 * 60,
            path=self._auth_cookie_path,
            domain=self._auth_cookie_domain,
            secure=self._auth_cookie_secure,
            httponly=True,
            samesite=self._auth_cookie_samesite,
        )

    def delete_refresh_token_cookie(self, response: Response) -> None:
        """Удалить HttpOnly-cookie refresh-токена в HTTP-ответе.

        Добавляет в ответ заголовок ``Set-Cookie`` с ``Max-Age=0``
        по тем же ``Path``/``Domain``, которые были использованы
        при установке cookie, - в противном случае браузер не сможет
        корректно сопоставить cookie с операцией удаления.

        Parameters
        ----------
        response : Response
            Объект HTTP-ответа, в который добавляется заголовок
            ``Set-Cookie`` с ``Max-Age=0``.
        """
        response.delete_cookie(
            key=self._refresh_token_cookie_name,
            path=self._auth_cookie_path,
            domain=self._auth_cookie_domain,
            secure=self._auth_cookie_secure,
            samesite=self._auth_cookie_samesite,
        )
