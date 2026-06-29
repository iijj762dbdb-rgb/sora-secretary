from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from assistant_memory import (
    get_exportable_memories,
    get_memory,
    get_recent_memories,
    list_memories_by_type,
    list_reminders,
    list_todos_for_api,
    search_memories,
)
from status_info import build_status_report


app = FastAPI(
    title="SORA Secretary UI API",
    version="0.1.0",
    description="Read-only local API gateway for aster-ui.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)


def _error_response(status_code: int, detail: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"status": "error", "detail": detail},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
    return _error_response(exc.status_code, str(exc.detail))


@app.exception_handler(Exception)
async def unhandled_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    return _error_response(500, f"internal server error: {type(exc).__name__}")


def _serialize_memory(memory: dict) -> dict:
    return {
        "id": memory.get("id"),
        "title": memory.get("title"),
        "summary": memory.get("summary"),
        "gpt_summary": memory.get("gpt_summary"),
        "body": memory.get("body"),
        "tags": memory.get("tags"),
        "memory_type": memory.get("memory_type"),
        "visibility": memory.get("visibility"),
        "sensitivity": memory.get("sensitivity"),
        "confidence": memory.get("confidence"),
        "review_at": memory.get("review_at"),
        "redaction_status": memory.get("redaction_status"),
        "export_allowed": memory.get("export_allowed"),
        "supersedes_id": memory.get("supersedes_id"),
        "superseded_by_id": memory.get("superseded_by_id"),
        "source_type": memory.get("source_type"),
        "source_id": memory.get("source_id"),
        "status": memory.get("status"),
        "archived": memory.get("archived"),
        "created_at": memory.get("created_at"),
        "updated_at": memory.get("updated_at"),
    }


def _serialize_todo(todo: dict) -> dict:
    return {
        "id": todo.get("id"),
        "text": todo.get("title"),
        "status": todo.get("status"),
        "priority": todo.get("priority"),
        "due_at": todo.get("due_at"),
        "created_at": todo.get("created_at"),
        "updated_at": todo.get("updated_at"),
        "completed_at": todo.get("completed_at"),
    }


def _serialize_reminder(reminder: dict) -> dict:
    return {
        "id": reminder.get("id"),
        "text": reminder.get("text"),
        "remind_at": reminder.get("remind_at"),
        "status": reminder.get("status"),
        "created_at": reminder.get("created_at"),
        "updated_at": reminder.get("updated_at"),
        "sent_at": reminder.get("sent_at"),
        "source": reminder.get("source"),
        "related_todo_id": reminder.get("related_todo_id"),
    }


@app.get("/api/health")
async def health() -> dict:
    return {
        "status": "ok",
        "service": "sora-secretary-api",
        "mode": "read-only",
    }


@app.get("/api/status")
async def status() -> dict:
    report = await build_status_report()
    return {
        "status": "ok",
        "report": report,
    }


@app.get("/api/memories/recent")
async def recent_memories(limit: int = Query(default=20, ge=1, le=100)) -> dict:
    items = [_serialize_memory(memory) for memory in get_recent_memories(limit)]
    return {
        "status": "ok",
        "items": items,
    }


@app.get("/api/memories/search")
async def search_memory_endpoint(
    q: str = Query(..., min_length=1),
    limit: int = Query(default=20, ge=1, le=100),
) -> dict:
    query = q.strip()
    if not query:
        raise HTTPException(status_code=400, detail="query must not be empty")

    items = [_serialize_memory(memory) for memory in search_memories(query, limit)]
    return {
        "status": "ok",
        "items": items,
    }


@app.get("/api/memories/exportable")
async def exportable_memories(limit: int = Query(default=20, ge=1, le=100)) -> dict:
    items = [_serialize_memory(memory) for memory in get_exportable_memories(limit)]
    return {
        "status": "ok",
        "items": items,
    }


@app.get("/api/memories/{memory_id}")
async def memory_detail(memory_id: str) -> dict:
    memory = get_memory(memory_id)
    if memory is None:
        raise HTTPException(status_code=404, detail="memory not found")

    return {
        "status": "ok",
        "item": _serialize_memory(memory),
    }


@app.get("/api/todos")
async def todos(
    status: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
) -> dict:
    status_filter = status or "active"
    allowed = {"todo", "doing", "done", "all", "active"}
    if status_filter not in allowed:
        raise HTTPException(status_code=400, detail="invalid todo status filter")

    items = [_serialize_todo(todo) for todo in list_todos_for_api(status_filter, limit)]
    return {
        "status": "ok",
        "items": items,
    }


@app.get("/api/reminders")
async def reminders(
    status: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
) -> dict:
    status_filter = status or "pending"
    allowed = {"pending", "sent", "cancelled", "all"}
    if status_filter not in allowed:
        raise HTTPException(status_code=400, detail="invalid reminder status filter")

    items = [_serialize_reminder(reminder) for reminder in list_reminders(status_filter, limit)]
    return {
        "status": "ok",
        "items": items,
    }


@app.get("/api/daily-reports")
async def daily_reports(limit: int = Query(default=20, ge=1, le=100)) -> dict:
    items = [
        _serialize_memory(memory)
        for memory in list_memories_by_type("daily_report", limit)
    ]
    return {
        "status": "ok",
        "items": items,
    }
