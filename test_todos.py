import os
import sqlite3
import pytest
from datetime import datetime
from config import ASSISTANT_MEMORY_DB
from assistant_memory import (
    init_db, create_todo, list_todos, get_todo, 
    complete_todo, archive_todo, get_todo_stats
)
from bot import run_chat_flow
import asyncio

def test_todo_crud():
    # Remove existing db if tests run isolated, or just let it use the current db for a quick test
    # Better to create a test DB, but the config uses ASSISTANT_MEMORY_DB directly.
    # We will just test with the real DB since it's local development.
    init_db()

    # 1. Create
    todo_id = create_todo(title="Test Task", body="Test Body", priority="high")
    assert todo_id.startswith("todo_")

    # 2. Get
    t = get_todo(todo_id)
    assert t is not None
    assert t["title"] == "Test Task"
    assert t["status"] == "todo"

    # 3. List
    todos = list_todos(status="todo")
    assert any(x["id"] == todo_id for x in todos)

    # 4. Complete
    success = complete_todo(todo_id)
    assert success is True
    t2 = get_todo(todo_id)
    assert t2["status"] == "done"
    assert t2["completed_at"] is not None

    # 5. Archive
    success_arc = archive_todo(todo_id)
    assert success_arc is True
    t3 = get_todo(todo_id)
    assert t3 is None # get_todo filters out archived

    # 6. Stats
    stats = get_todo_stats()
    assert "todo" in stats
    assert "done" in stats
    assert "archived" in stats

@pytest.mark.asyncio
async def test_todo_routing():
    # Add
    res = await run_chat_flow("これToDoに入れて:牛乳を買う")
    assert any("ToDoに追加しました" in r for r in res)
    
    # List
    res_list = await run_chat_flow("タスク一覧")
    assert any("現在のタスク" in r for r in res_list)

    # Done (needs ID)
    res_done_ambiguous = await run_chat_flow("終わった")
    assert any("IDを含めて指示してください" in r for r in res_done_ambiguous)

    res_done = await run_chat_flow("todo_dummy123 を完了")
    assert any("見つかりませんでした" in r for r in res_done) # because it's dummy
