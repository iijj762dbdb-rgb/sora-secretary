from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

import api_server
import assistant_memory
from assistant_memory import (
    cancel_reminder,
    complete_todo,
    create_reminder,
    create_todo,
    init_db,
    mark_reminder_sent,
    remember_memory,
)


@pytest.fixture
def client(tmp_path, monkeypatch):
    test_db = tmp_path / "assistant_memory.db"
    monkeypatch.setattr(assistant_memory, "ASSISTANT_MEMORY_DB", str(test_db))
    init_db()

    memory_id = remember_memory(
        title="API test memory",
        body="remembered through test setup",
        tags="test,api",
        memory_type="conversation_note",
    )
    remember_memory(
        title="Daily report sample",
        body="did a lot today",
        tags="daily,test",
        memory_type="daily_report",
    )
    exportable_id = remember_memory(
        title="Exportable memory",
        body="safe body for explicit detail",
        tags="export,test",
        memory_type="decision_trace",
        visibility="gpt_safe",
        gpt_summary="safe summary for GPT",
        redaction_status="sanitized",
        export_allowed=1,
    )

    todo_id = create_todo(title="Ship UI-1", body="Read-only gateway", priority="high")
    done_todo_id = create_todo(title="Completed task", priority="normal")
    complete_todo(done_todo_id)

    now = datetime.now()
    pending_id = create_reminder(
        text="Pending reminder",
        remind_at=(now + timedelta(minutes=30)).isoformat(),
    )
    sent_id = create_reminder(
        text="Sent reminder",
        remind_at=(now - timedelta(minutes=30)).isoformat(),
    )
    cancelled_id = create_reminder(
        text="Cancelled reminder",
        remind_at=(now + timedelta(minutes=60)).isoformat(),
    )
    mark_reminder_sent(sent_id)
    cancel_reminder(cancelled_id)

    monkeypatch.setattr(
        api_server,
        "build_status_report",
        _mock_status_report,
    )

    test_client = TestClient(api_server.app)
    return {
        "client": test_client,
        "memory_id": memory_id,
        "exportable_id": exportable_id,
        "todo_id": todo_id,
        "pending_id": pending_id,
    }


async def _mock_status_report() -> str:
    return "mocked status report"


def test_health(client):
    response = client["client"].get("/api/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "sora-secretary-api",
        "mode": "read-only",
    }


def test_recent_memories(client):
    response = client["client"].get("/api/memories/recent")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert any(item["id"] == client["memory_id"] for item in payload["items"])
    assert any("visibility" in item and "redaction_status" in item for item in payload["items"])


def test_exportable_memories(client):
    response = client["client"].get("/api/memories/exportable")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    ids = {item["id"] for item in payload["items"]}
    assert client["exportable_id"] in ids
    assert client["memory_id"] not in ids
    item = next(item for item in payload["items"] if item["id"] == client["exportable_id"])
    assert item["visibility"] == "gpt_safe"
    assert item["redaction_status"] == "sanitized"
    assert item["export_allowed"] == 1
    assert item["sensitivity"] != "secret"


def test_memory_not_found(client):
    response = client["client"].get("/api/memories/mem_missing")
    assert response.status_code == 404
    assert response.json() == {
        "status": "error",
        "detail": "memory not found",
    }


def test_todos_default_active_only(client):
    response = client["client"].get("/api/todos")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    statuses = {item["status"] for item in payload["items"]}
    assert statuses <= {"todo", "doing"}
    assert any(item["id"] == client["todo_id"] for item in payload["items"])


def test_reminders_default_pending(client):
    response = client["client"].get("/api/reminders")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert all(item["status"] == "pending" for item in payload["items"])
    assert any(item["id"] == client["pending_id"] for item in payload["items"])


def test_status(client):
    response = client["client"].get("/api/status")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "report": "mocked status report",
    }
