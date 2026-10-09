from datetime import UTC, datetime
from typing import Self, override
from uuid import UUID

from src.shared.domain.mixins import Auditable, Identifiable
from src.users.domain.exceptions import (
    InvalidVerificationTokenExpirationError,
    VerificationTokenAlreadyUsedError,
    VerificationTokenExpiredError,
)
from src.users.domain.value_objects import VerificationTokenPurpose


class VerificationToken(Identifiable[UUID], Auditable):
    """Доменная сущность токена подтверждения.

    Представляет собой одноразовый токен, подтверждающий совершение
    операции, требующей проверки её инициатора. Токен принадлежит
    конкретной учётной записи, имеет определённое назначение
    (purpose) и ограниченное время действия.

    В открытом виде токен не хранится: в сущности присутствует
    только криптографический хеш токена, вычисленный слоем
    приложения. Сам токен возвращается инициатору операции
    и передаётся по каналу, определённому внедоменным контекстом.

    Attributes
    ----------
    id : UUID
        Уникальный идентификатор токена подтверждения.
    identity_id : UUID
        Идентификатор учётной записи, которой выдан токен.
    token_hash : str
        Криптографический хеш токена. Открытое значение токена
        в сущности не сохраняется.
    purpose : VerificationTokenPurpose
        Назначение токена: операция, подтверждаемая токеном.
    expires_at : datetime
        Дата и время истечения срока действия токена.
    used_at : datetime | None
        Дата и время, когда токен перестал быть пригодным для
        использования: либо был применён (подтверждение выполнено),
        либо был аннулирован (например, при повторном запросе
        подтверждения). ``None``, если токен ещё пригоден.
    created_at : datetime
        Дата и время создания токена.
    updated_at : datetime | None
        Дата и время последнего изменения токена. ``None``, если
        токен не изменялся с момента создания.

    Notes
    -----
    Сущность не наследует примесь ``Versioned``: оптимистическая
    блокировка не применяется, поскольку переход токена в
    непригодное состояние выполняется единственным атомарным
    обновлением, идемпотентным по своей природе.

    Сущность различает два способа перехода в непригодное
    состояние - применение токена (``mark_used``) и его аннулирование
    (``invalidate``). Обе операции фиксируются в одном поле
    ``used_at``, поскольку для получателя токена оба исхода
    равнозначны: токен более не может быть использован. Различие
    сохраняется в семантике вызовов, а не в данных.

    Операции различаются также проверками: применение токена
    (``mark_used``) проверяет его пригодность и возбуждает
    ``VerificationTokenAlreadyUsedError`` либо
    ``VerificationTokenExpiredError`` (симметрично
    ``Session._ensure_valid()``, ADR-0005), тогда как аннулирование
    (``invalidate``) допустимо в любом состоянии токена и проверок
    не выполняет.

    Токен не может быть выпущен уже истёкшим: фабрический метод
    ``issue()`` возбуждает ``InvalidVerificationTokenExpirationError``,
    если ``expires_at`` не позже переданного момента выпуска ``now``
    (симметрично ``Session.issue()``, ADR-0005).
    """

    def __init__(
        self,
        id: UUID,
        identity_id: UUID,
        token_hash: str,
        purpose: VerificationTokenPurpose,
        expires_at: datetime,
        used_at: datetime | None,
        created_at: datetime,
        updated_at: datetime | None,
    ) -> None:
        self.id = id
        self.identity_id = identity_id
        self.token_hash = token_hash
        self.purpose = purpose
        self.expires_at = expires_at
        self.used_at = used_at
        self.created_at = created_at
        self.updated_at = updated_at

    @classmethod
    def issue(
        cls,
        id: UUID,
        identity_id: UUID,
        token_hash: str,
        purpose: VerificationTokenPurpose,
        expires_at: datetime,
        *,
        now: datetime,
    ) -> Self:
        """Создать новый токен подтверждения.

        Проверяет, что токен не выпускается уже истёкшим:
        ``expires_at`` должен находиться строго в будущем
        относительно переданного момента ``now``. Момент ``now``
        используется как ``created_at``: сущность не обращается
        к системному времени при создании токена (ADR-0005).

        Parameters
        ----------
        id : UUID
            Уникальный идентификатор токена подтверждения.
        identity_id : UUID
            Идентификатор учётной записи, которой выдаётся токен.
        token_hash : str
            Криптографический хеш открытого значения токена,
            вычисленный слоем приложения.
        purpose : VerificationTokenPurpose
            Назначение выпускаемого токена.
        expires_at : datetime
            Момент истечения срока действия токена.
        now : datetime
            Момент выпуска токена, вычисляемый слоем приложения.
            Точка отсчёта для проверки истечения, а также
            значение ``created_at``.

        Returns
        -------
        VerificationToken
            Новый, пригодный для использования токен.

        Raises
        ------
        InvalidVerificationTokenExpirationError
            Если ``expires_at`` не позже ``now`` (токен был бы
            выпущен уже истёкшим).
        """
        if expires_at <= now:
            raise InvalidVerificationTokenExpirationError(expires_at, now)

        return cls(
            id=id,
            identity_id=identity_id,
            token_hash=token_hash,
            purpose=purpose,
            expires_at=expires_at,
            used_at=None,
            created_at=now,
            updated_at=None,
        )

    def is_used(self) -> bool:
        """Проверить, перешёл ли токен в непригодное состояние.

        Returns
        -------
        bool
            ``True``, если токен был применён или аннулирован.
        """
        return self.used_at is not None

    def is_expired(self, now: datetime | None = None) -> bool:
        """Проверить, истёк ли срок действия токена.

        Parameters
        ----------
        now : datetime | None, optional
            Момент времени для сравнения. Если не передан,
            используется текущее время.

        Returns
        -------
        bool
            ``True``, если срок действия токена истёк.
        """
        return (now or datetime.now(UTC)) >= self.expires_at

    def is_usable(self, now: datetime | None = None) -> bool:
        """Проверить, пригоден ли токен для подтверждения операции.

        Parameters
        ----------
        now : datetime | None, optional
            Момент времени для проверки истечения. Если не передан,
            используется текущее время.

        Returns
        -------
        bool
            ``True``, если токен ещё не использован и срок его
            действия не истёк.
        """
        return not self.is_used() and not self.is_expired(now)

    def mark_used(self, at: datetime | None = None) -> None:
        """Применить токен подтверждения.

        Проверяет пригодность токена и переводит его
        в непригодное состояние, поскольку подтверждение выполнено
        и повторное использование токена недопустимо.

        Parameters
        ----------
        at : datetime | None, optional
            Временная метка применения токена. Если не передана,
            используется текущее время. Тот же момент применяется
            для проверки пригодности и для фиксации перехода,
            поэтому проверка и изменение состояния согласованы.

        Raises
        ------
        VerificationTokenAlreadyUsedError
            Если токен ранее был применён или аннулирован.
        VerificationTokenExpiredError
            Если срок действия токена истёк на момент ``at``.

        Notes
        -----
        В отличие от ``invalidate()`` операция не идемпотентна:
        повторное применение непригодного токена отвергается,
        поскольку именно оно указывает на повторное использование
        выданного токена.
        """
        if at is None:
            at = datetime.now(UTC)

        self._ensure_applicable(at)
        self._consume(at)

    def invalidate(self, at: datetime | None = None) -> None:
        """Аннулировать токен подтверждения.

        Переводит токен в непригодное состояние без применения
        подтверждаемой операции. Используется, например, при
        повторном запросе подтверждения: ранее выданный токен
        должен перестать действовать до выпуска нового.

        Parameters
        ----------
        at : datetime | None, optional
            Временная метка аннулирования токена. Если не передана,
            используется текущее время.

        Notes
        -----
        Операция идемпотентна: повторный вызов для уже непригодного
        токена не изменяет ``used_at`` и не обновляет ``updated_at``.

        Проверок пригодности не выполняется: аннулирование допустимо
        в любом состоянии токена, включая истёкший, поскольку не
        является подтверждающей операцией.
        """
        self._consume(at)

    def _ensure_applicable(self, at: datetime) -> None:
        """Проверить, что токен пригоден для применения.

        Непригодность по переходу проверяется раньше истечения
        срока действия: для уже непригодного токена причина отказа
        существеннее, а сам факт истечения не добавляет сведений.

        Parameters
        ----------
        at : datetime
            Временная метка, относительно которой проверяется
            пригодность токена.

        Raises
        ------
        VerificationTokenAlreadyUsedError
            Если токен ранее был применён или аннулирован.
        VerificationTokenExpiredError
            Если срок действия токена истёк на момент ``at``.
        """
        if self.is_used():
            raise VerificationTokenAlreadyUsedError(self.id)

        if self.is_expired(at):
            raise VerificationTokenExpiredError(self.id)

    def _consume(self, at: datetime | None = None) -> None:
        """Перевести токен в непригодное состояние.

        Общая часть реализаций ``mark_used()`` и ``invalidate()``:
        фиксирует момент перехода в поле ``used_at`` и обновляет
        метку последнего изменения. Если токен уже непригоден,
        состояние не изменяется.

        Parameters
        ----------
        at : datetime | None, optional
            Временная метка перехода токена в непригодное состояние.
            Если не передана, используется текущее время.
        """
        if self.is_used():
            return

        if at is None:
            at = datetime.now(UTC)

        self.used_at = at
        self._touch(at)

    @override
    def __repr__(self) -> str:
        return (
            "VerificationToken("
            f"id={self.id!r}, "
            f"identity_id={self.identity_id!r}, "
            f"purpose={self.purpose!r}, "
            f"expires_at={self.expires_at!r}, "
            f"used_at={self.used_at!r}, "
            f"created_at={self.created_at!r}, "
            f"updated_at={self.updated_at!r})"
        )
