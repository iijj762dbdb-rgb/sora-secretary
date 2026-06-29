# assistant_memory.db reset schema plan

## Purpose

Aster / SORA Secretary の `assistant_memory.db` はまだ本運用していないため、既存データ保持migrationではなく、バックアップ後に長期記憶policy対応schemaへリセットする方針をここに記録する。

この文書は設計と手順案のみであり、DB reset、migration、schema変更、systemd変更はまだ実行しない。

## Current read-only inventory

- DB path: `/home/okota/code/sora-secretary/data/assistant_memory.db`
- Config default: `ASSISTANT_MEMORY_DB=./data/assistant_memory.db`
- Current tables: `memories`, `memories_fts`, `todos`, `reminders`
- FTS5 shadow tables: `memories_fts_config`, `memories_fts_data`, `memories_fts_docsize`, `memories_fts_idx`
- FTS triggers: `memories_ai`, `memories_ad`, `memories_au`
- Read-only counts checked on 2026-06-29:
  - `memories`: 0
  - `memories_fts`: 0
  - `todos`: 12
  - `reminders`: 23

The current `init_db()` creates the policy-field-aware base tables, `memories_fts`, and the three FTS synchronization triggers for new DBs. `export_memories_to_markdown()` now exports only GPT-safe sanitized summaries and does not write raw `body`.

## Reset principle

- Existing records may be discarded because Aster is not in production yet.
- A full DB-file backup must be created before any reset.
- The preferred reset path is DB-file replacement, then `init_db()` recreation, because it recreates FTS5 and triggers as a coherent set.
- Table drop / recreate is a fallback only. It is easier to leave FTS shadow tables or triggers inconsistent, so it should not be the first choice.
- Reset must be performed while Bot/API processes are stopped by a human-approved operation, to avoid concurrent SQLite access.
- Do not display `.env`, token, secret, or raw memory body during verification.

## Target memories schema

The next clean schema should keep the current operational fields and add long-term policy fields.

```sql
CREATE TABLE memories (
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
```

FTS should continue to index human-readable searchable text, not secret-control metadata.

```sql
CREATE VIRTUAL TABLE memories_fts
USING fts5(title, summary, gpt_summary, body, tags, content='memories', content_rowid='rowid');
```

The `memories_ai`, `memories_ad`, and `memories_au` triggers must be updated to insert/delete/update `gpt_summary` in addition to `title`, `summary`, `body`, and `tags`.

`todos` and `reminders` can remain structurally compatible with the current schema for the reset MVP.

## Backup plan

Future execution should create a DB-file backup before any reset.

```bash
mkdir -p /home/okota/code/sora-secretary/data/backups
ts="$(date +%Y%m%d_%H%M%S)"
cp -p /home/okota/code/sora-secretary/data/assistant_memory.db \
  "/home/okota/code/sora-secretary/data/backups/assistant_memory_${ts}.db"
sqlite3 "file:/home/okota/code/sora-secretary/data/backups/assistant_memory_${ts}.db?mode=ro" "PRAGMA integrity_check;"
```

Expected integrity result:

```text
ok
```

The backup must not be committed to Git.

## Preferred reset plan: DB-file replacement

This is a future human-approved operation, not a command to run during design.

1. Stop Bot/API processes through the established operations procedure.
2. Create and integrity-check the timestamped backup.
3. Create a new empty DB at a temporary path, using the updated `init_db()` after code review.
4. Verify the temporary DB schema, FTS table, triggers, and empty counts.
5. Replace the active DB file with the verified new DB.
6. Run the verification SQL again against the active DB in read-only mode.
7. Restart Bot/API processes through the established operations procedure.
8. Keep the backup until at least one successful restart and verification cycle has passed.

This path avoids manually dropping FTS shadow tables and makes it clear that the previous DB was preserved.

## Fallback reset plan: table drop / recreate

Use only if DB-file replacement is not acceptable. This must be reviewed carefully because FTS5 shadow tables and triggers must be removed in the right order.

Conceptual order:

```sql
DROP TRIGGER IF EXISTS memories_ai;
DROP TRIGGER IF EXISTS memories_ad;
DROP TRIGGER IF EXISTS memories_au;
DROP TABLE IF EXISTS memories_fts;
DROP TABLE IF EXISTS memories;
DROP TABLE IF EXISTS todos;
DROP TABLE IF EXISTS reminders;
```

Then run the updated `init_db()` to recreate `memories`, `memories_fts`, `todos`, `reminders`, and triggers. Do not execute this path without a fresh DB-file backup and explicit human confirmation.

## Reset verification SQL

Use SQLite read-only mode for post-reset verification.

```bash
sqlite3 "file:/home/okota/code/sora-secretary/data/assistant_memory.db?mode=ro" ".tables"
sqlite3 "file:/home/okota/code/sora-secretary/data/assistant_memory.db?mode=ro" ".schema memories"
sqlite3 "file:/home/okota/code/sora-secretary/data/assistant_memory.db?mode=ro" \
  "SELECT name, type FROM sqlite_master WHERE type IN ('table','trigger','index') ORDER BY type, name;"
sqlite3 "file:/home/okota/code/sora-secretary/data/assistant_memory.db?mode=ro" \
  "SELECT (SELECT COUNT(*) FROM memories), (SELECT COUNT(*) FROM todos), (SELECT COUNT(*) FROM reminders), (SELECT COUNT(*) FROM memories_fts);"
sqlite3 "file:/home/okota/code/sora-secretary/data/assistant_memory.db?mode=ro" \
  "PRAGMA integrity_check;"
```

Expected counts after reset:

```text
0|0|0|0
```

Expected policy columns:

```sql
PRAGMA table_info(memories);
```

Must include at least:

- `visibility`
- `gpt_summary`
- `confidence`
- `review_at`
- `redaction_status`
- `export_allowed`
- `supersedes_id`
- `superseded_by_id`

## Export behavior after schema reset

`export_memories_to_markdown()` is implemented as a GPT-safe export path.

- Local/admin export may include `body`, but should clearly mark visibility and sensitivity.
- GPT-facing export must include only records where:
  - `visibility = 'gpt_safe'`
  - `export_allowed = 1`
  - `redaction_status = 'sanitized'`
  - `sensitivity != 'secret'`
- GPT-facing export prefers `gpt_summary` and omits raw `body`.
- Repo-safe export should require `visibility IN ('repo_safe', 'public')`, `export_allowed = 1`, and `redaction_status = 'sanitized'`.
- `local_only`, `private`, and `secret` records must not be exported to GPT/GitHub targets.

## ai-memory-capture import mapping impact

`ai-memory-capture import-to-sora-db --dry-run` currently checks for some policy columns and maps only the old core fields. After reset, its mapping should be updated before real import is enabled.

Recommended mapping:

| candidate field | memories field |
| --- | --- |
| `memory_type` | `memory_type` |
| `title` | `title` |
| `summary` | `summary` |
| `reasoning_summary` + `next_action` | `body` or structured body section |
| `summary` or sanitized short form | `gpt_summary` |
| `project` | `project` |
| `visibility` | `visibility` |
| `sensitivity` | `sensitivity` |
| CLI lint status | `redaction_status` and import allow/skip decision |
| reviewed export decision | `export_allowed` |
| candidate hash | `source_id` |
| candidate path on sora inbox | `source_path` |
| fixed value | `source_type='memory_candidate'` |
| optional template value | `review_at`, `confidence`, `status` |

Real import should continue to reject `blocked`, `invalid`, `local_only_required` for external paths, and any `secret` candidate.

## Implementation sequence

1. Done: update `assistant_memory.py:init_db()` with the target schema and updated FTS triggers.
2. Done: update `remember_memory()` to provide safe defaults for new fields.
3. Done: update read paths and API serialization for policy fields.
4. Done: update Markdown export to enforce visibility/export filters.
5. Next: update ai-memory-capture import dry-run/real mapping for the new schema.
6. Next: add or extend dedicated tests for import mapping and backup/reset execution.
7. Only after review, run the backup and reset plan.

## Non-goals for this design step

- No DB reset execution.
- No migration execution.
- No assistant_memory.db writes.
- No `.env` display.
- No raw memory body display.
- No systemd changes.
- No Git commit or push.
