# AI / Codex Brief

## First steps
- Do not read all docs at once.
- First run:
  mdq search --q "<task keyword>" --paths "docs/**"
- Then inspect only relevant docs and source files.

## Source of truth
- Current state: docs/mvp-status.md
- Next tasks: docs/remaining-tasks.md
- Workflow: docs/development-workflow.md
- Safety policy: docs/safety-policy.md
- Discord behavior: docs/discord-bot.md
- Memory design: docs/memory-design.md
- Model routing: docs/model-routing.md
- Architecture: docs/architecture.md

## Hard safety rules
- Do not connect to Document Inbox yet.
- Do not touch Document Inbox app.db.
- Do not implement dangerous operations.
- No file deletion.
- No restore execution.
- No fsck.
- No rsync --delete.
- No pCloud import execute.
- No large backfill.
- Message Content Intent is not used.
- Normal Discord message monitoring is not used.
- Only assistant_memory.db may be updated by this project.

## Development rules
- Keep changes focused and small.
- Preserve existing slash commands unless explicitly changing them.
- Update matching docs when behavior changes.
- Run syntax checks before reporting.
- Prefer read-only or candidate/confirmation flows for risky behavior.
- For memory deletion, use archived=1 rather than physical deletion.

## Report format
- Summary
- Changed files
- What changed
- Docs / mdq
- Verification
- Remaining risks
- Next step
