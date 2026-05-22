import os
import pytest
from datetime import datetime, timedelta
from assistant_memory import (
    init_db, create_reminder, list_pending_reminders,
    list_due_reminders, mark_reminder_sent, cancel_reminder,
    get_reminder_stats
)
from bot import run_chat_flow

def test_reminder_crud():
    init_db()

    now = datetime.now()
    due_at = (now - timedelta(minutes=5)).isoformat()
    future_at = (now + timedelta(minutes=5)).isoformat()

    rem1 = create_reminder(text="Past due", remind_at=due_at)
    rem2 = create_reminder(text="Future due", remind_at=future_at)

    assert rem1.startswith("rem_")

    pending = list_pending_reminders()
    assert any(x["id"] == rem1 for x in pending)
    assert any(x["id"] == rem2 for x in pending)

    current_time = now.isoformat()
    due = list_due_reminders(current_time)
    assert any(x["id"] == rem1 for x in due)
    assert not any(x["id"] == rem2 for x in due)

    mark_reminder_sent(rem1)
    pending_after = list_pending_reminders()
    assert not any(x["id"] == rem1 for x in pending_after)

    cancel_reminder(rem2)
    pending_after_cancel = list_pending_reminders()
    assert not any(x["id"] == rem2 for x in pending_after_cancel)

    stats = get_reminder_stats()
    assert "pending" in stats
    assert "sent" in stats
    assert "cancelled" in stats

@pytest.mark.asyncio
async def test_reminder_routing():
    res = await run_chat_flow("リマインドして 2026-05-20T21:00:00+09:00 会議準備")
    assert any("追加しました" in r for r in res)
    
    # Test without seconds
    res_no_sec = await run_chat_flow("リマインドして 2026-05-21T11:00+09:00 テスト通知")
    assert any("追加しました" in r for r in res_no_sec)
    assert any("2026-05-21T11:00:00+09:00" in r for r in res_no_sec)
