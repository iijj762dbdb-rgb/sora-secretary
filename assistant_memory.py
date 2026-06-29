import sqlite3
import os
import uuid
from datetime import datetime, timezone
from config import ASSISTANT_MEMORY_DB, MEMORY_DIR

def _get_conn():
    db_path = ASSISTANT_MEMORY_DB
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = _get_conn()
    try:
        cursor = conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS memories (
            id TEXT PRIMARY KEY,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,

            memory_type TEXT NOT NULL,
            title TEXT NOT NULL,
            summary TEXT NOT NULL,
            gpt_summary TEXT,
            body TEXT,

            tags TEXT,
            project TEXT,
            importance INTEGER DEFAULT 3,
            confidence REAL DEFAULT NULL,
            sensitivity TEXT NOT NULL DEFAULT 'normal'
                CHECK (sensitivity IN ('normal', 'private', 'secret')),
            visibility TEXT NOT NULL DEFAULT 'local_only'
                CHECK (visibility IN ('local_only', 'gpt_safe', 'repo_safe', 'public')),
            redaction_status TEXT NOT NULL DEFAULT 'unchecked'
                CHECK (redaction_status IN ('unchecked', 'sanitized', 'needs_redaction', 'blocked')),
            export_allowed INTEGER NOT NULL DEFAULT 0
                CHECK (export_allowed IN (0, 1)),

            valid_from TEXT,
            valid_until TEXT,
            expires_at TEXT,
            review_at TEXT,
            last_accessed_at TEXT,
            access_count INTEGER NOT NULL DEFAULT 0,

            supersedes_id TEXT,
            superseded_by_id TEXT,

            source_type TEXT,
            source_id TEXT,
            source_path TEXT,
            source_updated_at TEXT,

            status TEXT NOT NULL DEFAULT 'active',
            version INTEGER NOT NULL DEFAULT 1,
            archived INTEGER NOT NULL DEFAULT 0 CHECK (archived IN (0, 1))
        );
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS reminders (
            id TEXT PRIMARY KEY,
            text TEXT NOT NULL,
            remind_at TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            sent_at TEXT,
            source TEXT,
            related_todo_id TEXT
        );
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS todos (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            body TEXT,
            status TEXT NOT NULL DEFAULT 'todo',
            priority TEXT NOT NULL DEFAULT 'normal',
            due_at TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            completed_at TEXT,
            source TEXT,
            related_memory_id TEXT
        );
        ''')

        # FTS5 virtual table
        cursor.execute('''
        CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts
        USING fts5(title, summary, gpt_summary, body, tags, content='memories', content_rowid='rowid');
        ''')

        # Triggers for FTS5 synchronization
        cursor.execute('''
        CREATE TRIGGER IF NOT EXISTS memories_ai AFTER INSERT ON memories BEGIN
            INSERT INTO memories_fts(rowid, title, summary, gpt_summary, body, tags)
            VALUES (new.rowid, new.title, new.summary, new.gpt_summary, new.body, new.tags);
        END;
        ''')
        cursor.execute('''
        CREATE TRIGGER IF NOT EXISTS memories_ad AFTER DELETE ON memories BEGIN
            INSERT INTO memories_fts(memories_fts, rowid, title, summary, gpt_summary, body, tags)
            VALUES ('delete', old.rowid, old.title, old.summary, old.gpt_summary, old.body, old.tags);
        END;
        ''')
        cursor.execute('''
        CREATE TRIGGER IF NOT EXISTS memories_au AFTER UPDATE ON memories BEGIN
            INSERT INTO memories_fts(memories_fts, rowid, title, summary, gpt_summary, body, tags)
            VALUES ('delete', old.rowid, old.title, old.summary, old.gpt_summary, old.body, old.tags);
            INSERT INTO memories_fts(rowid, title, summary, gpt_summary, body, tags)
            VALUES (new.rowid, new.title, new.summary, new.gpt_summary, new.body, new.tags);
        END;
        ''')

        conn.commit()
    finally:
        conn.close()

def _now_str() -> str:
    return datetime.now(timezone.utc).isoformat()


def _table_exists(cursor, table_name: str) -> bool:
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name = ?",
        (table_name,),
    )
    return cursor.fetchone() is not None


def _table_columns(cursor, table_name: str) -> set[str]:
    cursor.execute(f"PRAGMA table_info({table_name})")
    return {row[1] for row in cursor.fetchall()}


MEMORY_BASE_COLUMNS = (
    "id",
    "title",
    "summary",
    "tags",
    "memory_type",
    "created_at",
    "updated_at",
)
MEMORY_POLICY_COLUMNS = (
    "visibility",
    "gpt_summary",
    "confidence",
    "review_at",
    "redaction_status",
    "export_allowed",
    "supersedes_id",
    "superseded_by_id",
    "source_type",
    "source_id",
)


def _memory_select_clause(cursor, *, include_body: bool = False) -> str:
    existing = _table_columns(cursor, "memories")
    columns = list(MEMORY_BASE_COLUMNS)
    if include_body:
        columns.append("body")
    columns.extend(("sensitivity", "status", "archived"))

    select_parts: list[str] = []
    for column in columns:
        if column in existing:
            select_parts.append(column)
    for column in MEMORY_POLICY_COLUMNS:
        if column in existing:
            select_parts.append(column)
        else:
            select_parts.append(f"NULL AS {column}")
    return ", ".join(select_parts)


def remember_memory(
    title: str,
    body: str,
    tags: str = "",
    memory_type: str = "conversation_note",
    sensitivity: str = "normal",
    visibility: str = "local_only",
    gpt_summary: str | None = None,
    confidence: float | None = None,
    review_at: str | None = None,
    redaction_status: str = "unchecked",
    export_allowed: int = 0,
    supersedes_id: str | None = None,
    superseded_by_id: str | None = None,
) -> str:
    conn = _get_conn()
    try:
        mem_id = f"mem_{datetime.now().strftime('%Y%m%d')}_{uuid.uuid4().hex[:8]}"
        now = _now_str()
        summary = body[:200]

        cursor = conn.cursor()
        values = {
            "id": mem_id,
            "created_at": now,
            "updated_at": now,
            "memory_type": memory_type,
            "title": title,
            "summary": summary,
            "gpt_summary": gpt_summary or summary,
            "body": body,
            "tags": tags,
            "sensitivity": sensitivity,
            "visibility": visibility,
            "confidence": confidence,
            "review_at": review_at,
            "redaction_status": redaction_status,
            "export_allowed": int(bool(export_allowed)),
            "supersedes_id": supersedes_id,
            "superseded_by_id": superseded_by_id,
        }
        existing = _table_columns(cursor, "memories")
        insert_columns = [column for column in values if column in existing]
        placeholders = ", ".join("?" for _ in insert_columns)
        cursor.execute(
            f"INSERT INTO memories ({', '.join(insert_columns)}) VALUES ({placeholders})",
            tuple(values[column] for column in insert_columns),
        )
        conn.commit()
        return mem_id
    finally:
        conn.close()

def search_memories(query: str, limit: int = 5) -> list[dict]:
    conn = _get_conn()
    try:
        cursor = conn.cursor()
        select_clause = _memory_select_clause(cursor)
        memory_columns = _table_columns(cursor, "memories")
        like_parts = ["title LIKE ?", "summary LIKE ?", "body LIKE ?", "tags LIKE ?"]
        like_values = [f"%{query}%"] * len(like_parts)
        if "gpt_summary" in memory_columns:
            like_parts.append("gpt_summary LIKE ?")
            like_values.append(f"%{query}%")

        # Using FTS5
        sql = f'''
        SELECT {", ".join(f"m.{part}" if " AS " not in part else part for part in select_clause.split(", "))}
        FROM memories m
        JOIN memories_fts f ON m.rowid = f.rowid
        WHERE memories_fts MATCH ? AND m.archived = 0
        ORDER BY rank
        LIMIT ?
        '''

        try:
            # Escape query properly for FTS5 if it contains special characters,
            # simplest is to wrap in quotes for phrase matching.
            # However, users might use spaces, so let's just sanitize it a bit by replacing double quotes.
            safe_query = query.replace('"', '""')
            match_query = f'"{safe_query}"'
            cursor.execute(sql, (match_query, limit))
            rows = cursor.fetchall()
        except sqlite3.OperationalError:
            # Fallback to LIKE if FTS fails (e.g. malformed query)
            fallback_sql = f'''
            SELECT {select_clause}
            FROM memories
            WHERE archived = 0 AND ({' OR '.join(like_parts)})
            ORDER BY created_at DESC
            LIMIT ?
            '''
            cursor.execute(fallback_sql, tuple(like_values + [limit]))
            rows = cursor.fetchall()

        return [dict(r) for r in rows]
    finally:
        conn.close()

def get_recent_memories(limit: int = 10) -> list[dict]:
    conn = _get_conn()
    try:
        cursor = conn.cursor()
        select_clause = _memory_select_clause(cursor)
        sql = f'''
        SELECT {select_clause}
        FROM memories
        WHERE archived = 0
        ORDER BY created_at DESC
        LIMIT ?
        '''
        cursor.execute(sql, (limit,))
        rows = cursor.fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_exportable_memories(limit: int = 20) -> list[dict]:
    conn = _get_conn()
    try:
        cursor = conn.cursor()
        required_columns = {"visibility", "export_allowed", "redaction_status", "sensitivity", "archived"}
        if not required_columns <= _table_columns(cursor, "memories"):
            return []

        select_clause = _memory_select_clause(cursor)
        cursor.execute(
            f"""
            SELECT {select_clause}
            FROM memories
            WHERE visibility = 'gpt_safe'
              AND export_allowed = 1
              AND redaction_status = 'sanitized'
              AND sensitivity != 'secret'
              AND archived = 0
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        )
        return [dict(r) for r in cursor.fetchall()]
    finally:
        conn.close()


def forget_memory(memory_id: str) -> bool:
    conn = _get_conn()
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE memories SET archived = 1, updated_at = ? WHERE id = ?", (_now_str(), memory_id))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()

def get_memory(memory_id: str) -> dict | None:
    conn = _get_conn()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM memories WHERE id = ? AND archived = 0", (memory_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()

def create_reminder(text: str, remind_at: str, source: str = None, related_todo_id: str = None) -> str:
    conn = _get_conn()
    try:
        remind_id = f"rem_{datetime.now().strftime('%Y%m%d')}_{uuid.uuid4().hex[:8]}"
        now = _now_str()
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO reminders (
            id, text, remind_at, status, created_at, updated_at, source, related_todo_id
        ) VALUES (?, ?, ?, 'pending', ?, ?, ?, ?)
        ''', (remind_id, text, remind_at, now, now, source, related_todo_id))
        conn.commit()
        return remind_id
    finally:
        conn.close()

def list_pending_reminders(limit: int = 50) -> list[dict]:
    conn = _get_conn()
    try:
        cursor = conn.cursor()
        if not _table_exists(cursor, "reminders"):
            return []
        cursor.execute("SELECT * FROM reminders WHERE status = 'pending' ORDER BY remind_at ASC LIMIT ?", (limit,))
        return [dict(r) for r in cursor.fetchall()]
    finally:
        conn.close()


def list_reminders(status: str = "pending", limit: int = 50) -> list[dict]:
    conn = _get_conn()
    try:
        cursor = conn.cursor()
        if not _table_exists(cursor, "reminders"):
            return []

        if status == "all":
            cursor.execute(
                "SELECT * FROM reminders ORDER BY remind_at ASC LIMIT ?",
                (limit,),
            )
        else:
            cursor.execute(
                "SELECT * FROM reminders WHERE status = ? ORDER BY remind_at ASC LIMIT ?",
                (status, limit),
            )
        return [dict(r) for r in cursor.fetchall()]
    finally:
        conn.close()

def list_due_reminders(current_time: str) -> list[dict]:
    conn = _get_conn()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM reminders WHERE status = 'pending' AND remind_at <= ? ORDER BY remind_at ASC", (current_time,))
        return [dict(r) for r in cursor.fetchall()]
    finally:
        conn.close()

def mark_reminder_sent(remind_id: str) -> bool:
    conn = _get_conn()
    try:
        cursor = conn.cursor()
        now = _now_str()
        cursor.execute("UPDATE reminders SET status = 'sent', updated_at = ?, sent_at = ? WHERE id = ?", (now, now, remind_id))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()

def cancel_reminder(remind_id: str) -> bool:
    conn = _get_conn()
    try:
        cursor = conn.cursor()
        now = _now_str()
        cursor.execute("UPDATE reminders SET status = 'cancelled', updated_at = ? WHERE id = ?", (now, remind_id))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()

def get_reminder_stats() -> dict:
    conn = _get_conn()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='reminders'")
        if not cursor.fetchone():
            return {"pending": 0, "sent": 0, "cancelled": 0}

        cursor.execute("SELECT status, COUNT(*) FROM reminders GROUP BY status")
        rows = cursor.fetchall()
        stats = {"pending": 0, "sent": 0, "cancelled": 0}
        for r in rows:
            if r[0] in stats:
                stats[r[0]] = r[1]
        return stats
    finally:
        conn.close()

def export_memories_to_markdown(limit: int, memory_dir: str) -> tuple[str, int]:
    conn = _get_conn()
    try:
        cursor = conn.cursor()
        columns = _table_columns(cursor, "memories")
        required_policy_columns = {"visibility", "export_allowed", "redaction_status", "gpt_summary"}
        if not required_policy_columns <= columns:
            return "", 0

        cursor.execute(
            """
            SELECT id, title, memory_type, tags, created_at, summary, gpt_summary, visibility, sensitivity
            FROM memories
            WHERE archived = 0
              AND visibility = 'gpt_safe'
              AND export_allowed = 1
              AND redaction_status = 'sanitized'
              AND sensitivity != 'secret'
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        )
        rows = cursor.fetchall()

        if not rows:
            return "", 0

        export_dir = os.path.join(memory_dir, "exports")
        os.makedirs(export_dir, exist_ok=True)

        now_str = datetime.now().strftime("%Y-%m-%d-%H%M%S")
        filename = f"{now_str}-memory-export.md"
        filepath = os.path.join(export_dir, filename)

        count = len(rows)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"# SORA Secretary Memory Export\n\n")
            f.write(f"- **Export Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"- **Count**: {count}\n\n")
            f.write("---\n\n")

            for r in rows:
                f.write(f"## {r['title']} (`{r['id']}`)\n")
                f.write(f"- **Type**: {r['memory_type']}\n")
                f.write(f"- **Visibility**: {r['visibility']}\n")
                f.write(f"- **Sensitivity**: {r['sensitivity']}\n")
                f.write(f"- **Tags**: {r['tags']}\n")
                f.write(f"- **Created At**: {r['created_at']}\n")
                export_summary = r["gpt_summary"] or r["summary"]
                f.write(f"### GPT-safe Summary\n{export_summary}\n\n")
                f.write("---\n\n")

        return filepath, count
    finally:
        conn.close()

def create_todo(title: str, body: str = "", priority: str = "normal", due_at: str = None, source: str = None, related_memory_id: str = None) -> str:
    conn = _get_conn()
    try:
        todo_id = f"todo_{datetime.now().strftime('%Y%m%d')}_{uuid.uuid4().hex[:8]}"
        now = _now_str()
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO todos (
            id, title, body, status, priority, due_at, created_at, updated_at, source, related_memory_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (todo_id, title, body, "todo", priority, due_at, now, now, source, related_memory_id))
        conn.commit()
        return todo_id
    finally:
        conn.close()

def list_todos(status: str = None, limit: int = 50) -> list[dict]:
    conn = _get_conn()
    try:
        cursor = conn.cursor()
        if not _table_exists(cursor, "todos"):
            return []
        if status:
            cursor.execute("SELECT * FROM todos WHERE status = ? ORDER BY created_at DESC LIMIT ?", (status, limit))
        else:
            cursor.execute("SELECT * FROM todos WHERE status != 'archived' ORDER BY created_at DESC LIMIT ?", (limit,))
        return [dict(r) for r in cursor.fetchall()]
    finally:
        conn.close()


def list_todos_for_api(status: str = "active", limit: int = 50) -> list[dict]:
    conn = _get_conn()
    try:
        cursor = conn.cursor()
        if not _table_exists(cursor, "todos"):
            return []

        if status == "all":
            cursor.execute(
                "SELECT * FROM todos WHERE status IN ('todo', 'doing', 'done') ORDER BY created_at DESC LIMIT ?",
                (limit,),
            )
        elif status == "active":
            cursor.execute(
                "SELECT * FROM todos WHERE status IN ('todo', 'doing') ORDER BY created_at DESC LIMIT ?",
                (limit,),
            )
        else:
            cursor.execute(
                "SELECT * FROM todos WHERE status = ? ORDER BY created_at DESC LIMIT ?",
                (status, limit),
            )
        return [dict(r) for r in cursor.fetchall()]
    finally:
        conn.close()

def get_todo(todo_id: str) -> dict | None:
    conn = _get_conn()
    try:
        cursor = conn.cursor()
        if not _table_exists(cursor, "todos"):
            return None
        cursor.execute("SELECT * FROM todos WHERE id = ? AND status != 'archived'", (todo_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()

def update_todo_status(todo_id: str, status: str) -> bool:
    conn = _get_conn()
    try:
        cursor = conn.cursor()
        now = _now_str()
        completed_at = now if status == 'done' else None

        if status == 'done':
            cursor.execute("UPDATE todos SET status = ?, updated_at = ?, completed_at = ? WHERE id = ?", (status, now, completed_at, todo_id))
        else:
            cursor.execute("UPDATE todos SET status = ?, updated_at = ? WHERE id = ?", (status, now, todo_id))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()

def complete_todo(todo_id: str) -> bool:
    return update_todo_status(todo_id, 'done')

def archive_todo(todo_id: str) -> bool:
    return update_todo_status(todo_id, 'archived')

def get_todo_stats() -> dict:
    conn = _get_conn()
    try:
        cursor = conn.cursor()
        if not _table_exists(cursor, "todos"):
            return {"todo": 0, "doing": 0, "done": 0, "archived": 0, "expired": 0}

        cursor.execute("SELECT status, COUNT(*) FROM todos GROUP BY status")
        rows = cursor.fetchall()
        stats = {"todo": 0, "doing": 0, "done": 0, "archived": 0, "expired": 0}
        for r in rows:
            status = r[0]
            if status in stats:
                stats[status] = r[1]

        now = _now_str()
        cursor.execute("SELECT COUNT(*) FROM todos WHERE status IN ('todo', 'doing') AND due_at IS NOT NULL AND due_at < ?", (now,))
        stats["expired"] = cursor.fetchone()[0]
        return stats
    finally:
        conn.close()


def get_memory_stats() -> dict:
    conn = _get_conn()
    try:
        cursor = conn.cursor()

        # total count
        cursor.execute("SELECT COUNT(*) FROM memories")
        total_count = cursor.fetchone()[0]

        # active count
        cursor.execute("SELECT COUNT(*) FROM memories WHERE archived = 0")
        active_count = cursor.fetchone()[0]

        # archived count
        cursor.execute("SELECT COUNT(*) FROM memories WHERE archived = 1")
        archived_count = cursor.fetchone()[0]

        # latest memory
        cursor.execute("SELECT * FROM memories ORDER BY created_at DESC LIMIT 1")
        row = cursor.fetchone()
        latest_memory = dict(row) if row else None

        return {
            "total_count": total_count,
            "active_count": active_count,
            "archived_count": archived_count,
            "latest_memory": latest_memory
        }
    finally:
        conn.close()


def list_memories_by_type(memory_type: str, limit: int = 20) -> list[dict]:
    conn = _get_conn()
    try:
        cursor = conn.cursor()
        select_clause = _memory_select_clause(cursor, include_body=True)
        cursor.execute(
            f"""
            SELECT {select_clause}
            FROM memories
            WHERE archived = 0 AND memory_type = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (memory_type, limit),
        )
        return [dict(r) for r in cursor.fetchall()]
    finally:
        conn.close()


def lint_memories() -> dict:
    conn = _get_conn()
    try:
        cursor = conn.cursor()

        # 1. Counts
        cursor.execute("SELECT COUNT(*) FROM memories")
        total_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM memories WHERE archived = 0")
        active_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM memories WHERE archived = 1")
        archived_count = cursor.fetchone()[0]

        # 2. Type breakdown
        cursor.execute("SELECT memory_type, COUNT(*) FROM memories GROUP BY memory_type")
        type_rows = cursor.fetchall()
        type_breakdown = {r[0]: r[1] for r in type_rows}

        # 3. Empty tags (active only)
        cursor.execute("SELECT id, title, memory_type FROM memories WHERE archived = 0 AND (tags IS NULL OR tags = '' OR tags = '[]' OR tags = 'None') LIMIT 10")
        empty_tags = [dict(r) for r in cursor.fetchall()]

        # 4. Too short title (< 5 chars, active only)
        cursor.execute("SELECT id, title, memory_type FROM memories WHERE archived = 0 AND LENGTH(title) < 5 LIMIT 10")
        short_title = [dict(r) for r in cursor.fetchall()]

        # 5. Too short body (< 10 chars, active only)
        cursor.execute("SELECT id, title, memory_type FROM memories WHERE archived = 0 AND (body IS NULL OR LENGTH(body) < 10) LIMIT 10")
        short_body = [dict(r) for r in cursor.fetchall()]

        # 6. Too long body (> 2000 chars, active only)
        cursor.execute("SELECT id, title, memory_type FROM memories WHERE archived = 0 AND body IS NOT NULL AND LENGTH(body) > 2000 LIMIT 10")
        long_body = [dict(r) for r in cursor.fetchall()]

        # 7. Sensitivity is normal count (active only)
        cursor.execute("SELECT COUNT(*) FROM memories WHERE archived = 0 AND sensitivity = 'normal'")
        sensitivity_normal_count = cursor.fetchone()[0]

        # 8. Duplicate title candidates (active only)
        cursor.execute("SELECT title, COUNT(*) as c FROM memories WHERE archived = 0 GROUP BY title HAVING c > 1 LIMIT 10")
        duplicates = [dict(r) for r in cursor.fetchall()]

        # 9. Old active decisions / project_notes
        cursor.execute("SELECT id, title, memory_type, created_at FROM memories WHERE archived = 0 AND memory_type IN ('decision', 'project_note') ORDER BY created_at ASC LIMIT 5")
        old_memories = [dict(r) for r in cursor.fetchall()]

        return {
            "total_count": total_count,
            "active_count": active_count,
            "archived_count": archived_count,
            "type_breakdown": type_breakdown,
            "empty_tags": empty_tags,
            "short_title": short_title,
            "short_body": short_body,
            "long_body": long_body,
            "sensitivity_normal_count": sensitivity_normal_count,
            "duplicates": duplicates,
            "old_memories": old_memories
        }
    finally:
        conn.close()
