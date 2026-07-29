from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, MemoryRecord, ReminderRecord
from app.memory import MemoryStore
from app.services.files import DocumentService


@pytest.fixture()
def memory_store(tmp_path):
    db_path = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    store = MemoryStore(session_factory=Session)
    return store


def test_clear_user_history_removes_user_messages(memory_store):
    memory_store.append_memory("user-1", "user", "hello")
    memory_store.append_memory("user-1", "assistant", "hi")
    memory_store.append_memory("user-2", "user", "another")

    memory_store.clear_user_history("user-1")

    assert memory_store.get_recent_messages("user-1", limit=10) == []
    assert len(memory_store.get_recent_messages("user-2", limit=10)) == 1


def test_docx_roundtrip(tmp_path):
    service = DocumentService()
    file_path = tmp_path / "sample.docx"

    output = service.write_docx(str(file_path), "Hello Eva")

    assert Path(output).exists()
    assert service.read_docx(str(file_path)) == "Hello Eva"
