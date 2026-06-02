from fastapi import Request, Response

from app.config import Settings


def set_auth_cookies(
    response: Response, *, access_token: str, refresh_token: str, settings: Settings
) -> None:
    """Устанавливает HttpOnly cookie с access- и refresh-токенами.

    Оба cookie помечаются флагом `HttpOnly` - токены недоступны
    JavaScript-коду на клиенте, что существенно снижает
    поверхность атаки в случае XSS. Значения `Secure`,
    `SameSite`, `Path` и `Domain` берутся из `Settings`.

    Время жизни cookie привязано к соответствующему
    `lifetime`-параметру из настроек, чтобы cookie истекли
    одновременно с истечением самого токена.

    Parameters
    ----------
    response : Response
        Объект HTTP-ответа, в который будут добавлены
        заголовки `Set-Cookie`.
    access_token : str
        Подписанный JWT access-токен.
    refresh_token : str
        Подписанный JWT refresh-токен.
    settings : Settings
        Конфигурация приложения, описывающая имена,
        атрибуты и времена жизни cookie.

    Notes
    -----
    Функция намеренно не валидирует токены - это ответственность
    вызывающего кода (как правило, сервисного слоя). Здесь
    выполняется только низкоуровневая работа с заголовками
    HTTP-ответа.
    """
    response.set_cookie(
        key=settings.ACCESS_TOKEN_COOKIE_NAME,
        value=access_token,
        max_age=settings.ACCESS_TOKEN_LIFETIME_MINUTES * 60,
        path=settings.AUTH_COOKIE_PATH,
        domain=settings.AUTH_COOKIE_DOMAIN,
        secure=settings.AUTH_COOKIE_SECURE,
        httponly=True,
        samesite=settings.AUTH_COOKIE_SAMESITE,
    )
    response.set_cookie(
        key=settings.REFRESH_TOKEN_COOKIE_NAME,
        value=refresh_token,
        max_age=settings.REFRESH_TOKEN_LIFETIME_DAYS * 24 * 60 * 60,
        path=settings.AUTH_COOKIE_PATH,
        domain=settings.AUTH_COOKIE_DOMAIN,
        secure=settings.AUTH_COOKIE_SECURE,
        httponly=True,
        samesite=settings.AUTH_COOKIE_SAMESITE,
    )


def delete_auth_cookies(response: Response, *, settings: Settings) -> None:
    """Очищает auth-cookie на стороне клиента.

    Удаляет cookie по тем же `Path`/`Domain`, что были
    использованы при установке - в противном случае браузер
    не сможет корректно сопоставить cookie с операцией
    удаления.

    Parameters
    ----------
    response : Response
        Объект HTTP-ответа, в который будут добавлены
        заголовки `Set-Cookie` с `Max-Age=0`.
    settings : Settings
        Конфигурация приложения, описывающая имена,
        атрибуты cookie.
    """
    response.delete_cookie(
        key=settings.ACCESS_TOKEN_COOKIE_NAME,
        path=settings.AUTH_COOKIE_PATH,
        domain=settings.AUTH_COOKIE_DOMAIN,
    )
    response.delete_cookie(
        key=settings.REFRESH_TOKEN_COOKIE_NAME,
        path=settings.AUTH_COOKIE_PATH,
        domain=settings.AUTH_COOKIE_DOMAIN,
    )


def get_access_token(request: Request, settings: Settings) -> str | None:
    """Извлекает access-токен из cookie запроса.

    Parameters
    ----------
    request : Request
        Объект входящего HTTP-запроса.
    settings : Settings
        Конфигурация приложения, описывающая имя cookie
        для access-токена.

    Returns
    -------
    str | None
        Значение access-токена либо `None`, если cookie
        отсутствует.
    """
    return request.cookies.get(settings.ACCESS_TOKEN_COOKIE_NAME)


def get_refresh_token(request: Request, settings: Settings) -> str | None:
    """Извлекает refresh-токен из cookie запроса.

    Parameters
    ----------
    request : Request
        Объект входящего HTTP-запроса.
    settings : Settings
        Конфигурация приложения, описывающая имя cookie
        для refresh-токена.

    Returns
    -------
    str | None
        Значение refresh-токена либо `None`, если cookie
        отсутствует.
    """
    return request.cookies.get(settings.REFRESH_TOKEN_COOKIE_NAME)
