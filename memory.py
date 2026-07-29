from contextlib import contextmanager
from datetime import datetime
from typing import Iterator

from .database import MemoryRecord, ReminderRecord, SessionLocal


class MemoryStore:
    def __init__(self, session_factory=SessionLocal) -> None:
        self.session_factory = session_factory

    @contextmanager
    def _session(self) -> Iterator[object]:
        session = self.session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def append_memory(self, user_id: str, role: str, content: str) -> None:
        with self._session() as session:
            session.add(MemoryRecord(user_id=user_id, role=role, content=content))

    def get_recent_messages(self, user_id: str, limit: int = 10) -> list[MemoryRecord]:
        with self._session() as session:
            return (
                session.query(MemoryRecord)
                .filter(MemoryRecord.user_id == user_id)
                .order_by(MemoryRecord.created_at.desc())
                .limit(limit)
                .all()
            )

    def add_reminder(self, user_id: str, chat_id: str, message: str, due_at: datetime) -> ReminderRecord:
        with self._session() as session:
            reminder = ReminderRecord(user_id=user_id, chat_id=chat_id, message=message, due_at=due_at)
            session.add(reminder)
            session.flush()
            return reminder

    def clear_user_history(self, user_id: str) -> None:
        with self._session() as session:
            session.query(MemoryRecord).filter(MemoryRecord.user_id == user_id).delete(synchronize_session=False)

    def list_due_reminders(self, now: datetime) -> list[ReminderRecord]:
        with self._session() as session:
            return (
                session.query(ReminderRecord)
                .filter(ReminderRecord.due_at <= now)
                .order_by(ReminderRecord.due_at.asc())
                .all()
            )
