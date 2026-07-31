"""Unit-тесты доменной сущности :class:`Session`."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from src.identity.domain.entities import Session
from src.identity.domain.exceptions import SessionInvalidError

IDENTITY_ID = uuid4()
SESSION_SECRET = "session-secret"
EXPIRES_AT = datetime(2026, 12, 31, tzinfo=UTC)
FUTURE = datetime(2027, 1, 1, tzinfo=UTC)
PAST = datetime(2026, 1, 1, tzinfo=UTC)


@pytest.fixture
def session() -> Session:
    """Сессия, созданная через фабричный метод."""
    return Session.issue(
        id=uuid4(),
        identity_id=IDENTITY_ID,
        session_secret=SESSION_SECRET,
        expires_at=EXPIRES_AT,
    )


class TestSessionIssue:
    """Проверка фабричного метода выпуска сессии."""

    def test_issue_sets_defaults(self, session: Session) -> None:
        """Новая сессия не отозвана и имеет начальные значения."""
        assert session.revoked_at is None
        assert session.version == 1
        assert session.updated_at is None
        assert session.last_used_at == session.created_at
        assert session.ip_address is None
        assert session.user_agent is None

    def test_issue_preserves_id(self) -> None:
        """Идентификатор сессии совпадает с переданным (claims токена)."""
        session_id = uuid4()

        session = Session.issue(
            id=session_id,
            identity_id=IDENTITY_ID,
            session_secret=SESSION_SECRET,
            expires_at=EXPIRES_AT,
        )

        assert session.id == session_id

    def test_issue_with_client_metadata(self) -> None:
        """Метаданные клиента сохраняются при передаче."""
        session = Session.issue(
            id=uuid4(),
            identity_id=IDENTITY_ID,
            session_secret=SESSION_SECRET,
            expires_at=EXPIRES_AT,
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
        )

        assert session.ip_address == "192.168.1.1"
        assert session.user_agent == "Mozilla/5.0"


class TestSessionStateChecks:
    """Проверка методов состояния сессии."""

    def test_is_revoked_false_for_fresh_session(self, session: Session) -> None:
        """Свежая сессия не считается отозванной."""
        assert session.is_revoked() is False

    def test_is_revoked_true_after_revoke(self, session: Session) -> None:
        """Отозванная сессия считается отозванной."""
        session.revoke()

        assert session.is_revoked() is True

    def test_is_expired_before_expiration(self, session: Session) -> None:
        """До момента истечения сессия не считается истёкшей."""
        assert session.is_expired(PAST) is False

    def test_is_expired_at_exact_moment(self, session: Session) -> None:
        """В точный момент истечения сессия считается истёкшей."""
        assert session.is_expired(EXPIRES_AT) is True

    def test_is_expired_after_expiration(self, session: Session) -> None:
        """После момента истечения сессия считается истёкшей."""
        assert session.is_expired(FUTURE) is True

    def test_is_valid_for_active_session(self, session: Session) -> None:
        """Активная неистёкшая сессия валидна."""
        assert session.is_valid(PAST) is True

    def test_is_valid_for_revoked_session(self, session: Session) -> None:
        """Отозванная сессия невалидна."""
        session.revoke()

        assert session.is_valid(PAST) is False

    def test_is_valid_for_expired_session(self, session: Session) -> None:
        """Истёкшая сессия невалидна."""
        assert session.is_valid(FUTURE) is False

    def test_is_valid_for_revoked_and_expired_session(self, session: Session) -> None:
        """Отозванная и истёкшая сессия невалидна."""
        session.revoke()

        assert session.is_valid(FUTURE) is False


class TestSessionMarkUsed:
    """Проверка фиксации факта использования сессии."""

    def test_mark_used_updates_last_used_at(self, session: Session) -> None:
        """Время последнего использования обновляется."""
        moment = datetime(2026, 6, 1, tzinfo=UTC)

        session.mark_used(at=moment)

        assert session.last_used_at == moment
        assert session.updated_at == moment

    def test_mark_used_does_not_validate(self, session: Session) -> None:
        """Метод не проверяет валидность сессии (по контракту)."""
        session.revoke()

        moment = datetime(2026, 6, 1, tzinfo=UTC)

        session.mark_used(at=moment)

        assert session.last_used_at == moment


class TestSessionRotateSecret:
    """Проверка ротации секрета сессии."""

    def test_rotate_secret_for_valid_session(self, session: Session) -> None:
        """Валидной сессии секрет и срок действия меняются."""
        moment = datetime(2026, 6, 1, tzinfo=UTC)
        new_expires_at = datetime(2027, 6, 1, tzinfo=UTC)

        session.rotate_secret("new-secret", new_expires_at, at=moment)

        assert session.session_secret == "new-secret"
        assert session.expires_at == new_expires_at
        assert session.updated_at == moment

    def test_rotate_secret_raises_for_revoked_session(self, session: Session) -> None:
        """Отозванной сессии секрет ротировать запрещено."""
        session.revoke()

        with pytest.raises(SessionInvalidError) as exc_info:
            session.rotate_secret("new-secret", FUTURE)

        assert exc_info.value.session_id == session.id
        assert session.session_secret == SESSION_SECRET

    def test_rotate_secret_raises_for_expired_session(self, session: Session) -> None:
        """Истёкшей сессии секрет ротировать запрещено."""
        with pytest.raises(SessionInvalidError):
            session.rotate_secret("new-secret", FUTURE, at=FUTURE)

    def test_rotate_secret_checks_expiration_against_passed_at(
        self, session: Session
    ) -> None:
        """Проверка истечения выполняется относительно переданного at."""
        with pytest.raises(SessionInvalidError):
            session.rotate_secret("new-secret", FUTURE, at=FUTURE)


class TestSessionRevoke:
    """Проверка отзыва сессии."""

    def test_revoke_active_session(self, session: Session) -> None:
        """Активная сессия отзывается и обновляет updated_at."""
        moment = datetime(2026, 6, 1, tzinfo=UTC)

        session.revoke(at=moment)

        assert session.revoked_at == moment
        assert session.updated_at == moment

    def test_revoke_is_idempotent(self, session: Session) -> None:
        """Повторный отзыв не изменяет состояние и updated_at."""
        session.revoke()
        revoked_at = session.revoked_at
        updated_at = session.updated_at

        session.revoke()

        assert session.revoked_at == revoked_at
        assert session.updated_at == updated_at

    def test_revoke_allowed_for_expired_session(self, session: Session) -> None:
        """Истёкшую сессию можно отозвать без исключения."""
        session.revoke(at=FUTURE)

        assert session.is_revoked() is True


class TestSessionRepresentation:
    """Проверка строкового представления."""

    def test_repr_contains_key_fields(self, session: Session) -> None:
        """Представление содержит ключевые поля сессии."""
        assert "Session(" in repr(session)
        assert str(session.id) in repr(session)
        assert str(session.identity_id) in repr(session)
