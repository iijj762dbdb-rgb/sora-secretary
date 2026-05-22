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
            body TEXT,

            tags TEXT,
            importance INTEGER DEFAULT 3,
            sensitivity TEXT DEFAULT 'normal',

            source_type TEXT,
            source_id TEXT,
            source_path TEXT,
            source_updated_at TEXT,

            status TEXT DEFAULT 'active',
            version INTEGER DEFAULT 1,
            archived INTEGER DEFAULT 0
        );
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS todos (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            body TEXT,
            status TEXT DEFAULT 'todo',
            priority TEXT DEFAULT 'normal',
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
        USING fts5(title, summary, body, tags, content='memories', content_rowid='rowid');
        ''')

        # Triggers for FTS5 synchronization
        cursor.execute('''
        CREATE TRIGGER IF NOT EXISTS memories_ai AFTER INSERT ON memories BEGIN
            INSERT INTO memories_fts(rowid, title, summary, body, tags)
            VALUES (new.rowid, new.title, new.summary, new.body, new.tags);
        END;
        ''')
        cursor.execute('''
        CREATE TRIGGER IF NOT EXISTS memories_ad AFTER DELETE ON memories BEGIN
            INSERT INTO memories_fts(memories_fts, rowid, title, summary, body, tags)
            VALUES ('delete', old.rowid, old.title, old.summary, old.body, old.tags);
        END;
        ''')
        cursor.execute('''
        CREATE TRIGGER IF NOT EXISTS memories_au AFTER UPDATE ON memories BEGIN
            INSERT INTO memories_fts(memories_fts, rowid, title, summary, body, tags)
            VALUES ('delete', old.rowid, old.title, old.summary, old.body, old.tags);
            INSERT INTO memories_fts(rowid, title, summary, body, tags)
            VALUES (new.rowid, new.title, new.summary, new.body, new.tags);
        END;
        ''')

        conn.commit()
    finally:
        conn.close()

def _now_str() -> str:
    return datetime.now(timezone.utc).isoformat()

def remember_memory(title: str, body: str, tags: str = "", memory_type: str = "conversation_note", sensitivity: str = "normal") -> str:
    conn = _get_conn()
    try:
        mem_id = f"mem_{datetime.now().strftime('%Y%m%d')}_{uuid.uuid4().hex[:8]}"
        now = _now_str()
        summary = body[:200]

        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO memories (
            id, created_at, updated_at, memory_type, title, summary, body, tags, sensitivity
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (mem_id, now, now, memory_type, title, summary, body, tags, sensitivity))
        conn.commit()
        return mem_id
    finally:
        conn.close()

def search_memories(query: str, limit: int = 5) -> list[dict]:
    conn = _get_conn()
    try:
        cursor = conn.cursor()

        # Using FTS5
        sql = '''
        SELECT m.id, m.title, m.summary, m.tags, m.created_at
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
            like_query = f"%{query}%"
            fallback_sql = '''
            SELECT id, title, summary, tags, created_at
            FROM memories
            WHERE archived = 0 AND (title LIKE ? OR summary LIKE ? OR body LIKE ? OR tags LIKE ?)
            ORDER BY created_at DESC
            LIMIT ?
            '''
            cursor.execute(fallback_sql, (like_query, like_query, like_query, like_query, limit))
            rows = cursor.fetchall()

        return [dict(r) for r in rows]
    finally:
        conn.close()

def get_recent_memories(limit: int = 10) -> list[dict]:
    conn = _get_conn()
    try:
        cursor = conn.cursor()
        sql = '''
        SELECT id, title, summary, tags, created_at
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

def export_memories_to_markdown(limit: int, memory_dir: str) -> tuple[str, int]:
    conn = _get_conn()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM memories WHERE archived = 0 ORDER BY created_at DESC LIMIT ?", (limit,))
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
                f.write(f"- **Tags**: {r['tags']}\n")
                f.write(f"- **Created At**: {r['created_at']}\n")
                f.write(f"### Summary\n{r['summary']}\n\n")
                if r['body']:
                    f.write(f"### Body\n{r['body']}\n\n")
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
        if status:
            cursor.execute("SELECT * FROM todos WHERE status = ? ORDER BY created_at DESC LIMIT ?", (status, limit))
        else:
            cursor.execute("SELECT * FROM todos WHERE status != 'archived' ORDER BY created_at DESC LIMIT ?", (limit,))
        return [dict(r) for r in cursor.fetchall()]
    finally:
        conn.close()

def get_todo(todo_id: str) -> dict | None:
    conn = _get_conn()
    try:
        cursor = conn.cursor()
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
        # Ensure table exists in case init_db hasn't run yet in some flows
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='todos'")
        if not cursor.fetchone():
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


