# Development Workflow

## docs正本と mdq 確認ベース
このプロジェクトでは、コードを書き始める前に「docs（ドキュメント）を正本として扱い、内容を mdq などのツールで確認する」運用を徹底します。

### ルール
- **実装前**: 関連する docs を検索し、仕様や制約を確認する。
- **実装後**: docs の記載と実装が整合しているかを確認する。
- Codex / Gemini などのLLMエージェントへの実装依頼時にも、必ず mdq (または代替手段のgrep等) を用いた確認の指示を含めます。

### コマンド例
- `mdq search --q "memory remember search forget" --paths "docs/**"`
- `mdq search --q "discord slash command safety" --paths "docs/**"`
- `mdq search --q "model routing ollama gemma qwen" --paths "docs/**"`
- mdq が使えない環境では `grep -R` などで代用し、ドキュメントの確認は絶対に省略しません。
