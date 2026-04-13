# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.1] - 2026-04-14

### Added

- TOML config file support (`~/.config/product-research/config.toml`)
- `PRODUCT_RESEARCH_PROJECT` / `PRODUCT_RESEARCH_LOCATION` tool-specific env vars
- `GOOGLE_CLOUD_*` env var fallback for cross-tool consistency
- Configuration priority: env vars > config.toml > defaults

## [0.3.0] - 2026-03-29

### Changed
- **Anthropic backend removed** — `research_agent.py` (Anthropic/Claude) has been removed.
  The Gemini backend is now the sole implementation, renamed from `research_agent_gemini.py`
  to `research_agent.py`.
- **`anthropic` dependency removed** from `pyproject.toml`.
- **`[project.scripts]` added** — `uv tool install .` now provides the `product-research` command.
- Output filenames no longer include `_gemini_` suffix (single backend).

## [0.2.0] - 2026-03-28

### Added
- **Gemini agent** (`research_agent_gemini.py`): Google Search Grounding for Phase 1 research, `response_schema`-based structured JSON extraction for Phase 2. Output filenames include `_gemini_` suffix to distinguish from the Anthropic variant.
- **`AIAgentBehavior` model**: Structured fields for AI-agent behaviour presence, autonomous scope, user controls, audit logging, rollback, and risk. Exposed as investigation axis 8 with a dedicated `## AI Agent Behaviour and Controls` section in Markdown reports.
- **Gemini retry logic** (`_call_with_retry`): Handles `429 / RESOURCE_EXHAUSTED` with exponential back-off + jitter (up to 5 retries, initial wait 5 s).

### Changed
- **Gemini backend switched to Vertex AI (ADC)** — replaced Google AI Studio API key authentication. Environment variables changed from `GOOGLE_API_KEY` to `GOOGLE_CLOUD_PROJECT` / `GOOGLE_CLOUD_LOCATION`.
- **`research_agent_gemini.py` is now self-contained** — Pydantic models and utility functions are inlined; dependency on `research_agent.py` removed.
- **Streaming output**: Phase 1 research text streams to stderr in real time; Phase 2 shows dot progress. Applied to both Gemini and Anthropic variants.
- Anthropic Phase 1 switched from `client.messages.create()` to `client.messages.stream()`; Phase 2 gained start/completion messages around the blocking `messages.parse()` call.
- Migrated to nlink-jp organisation; `pyproject.toml` description translated to English and `[project.urls]` added.

## [0.1.0] - 2026-03-14

### Added
- 製品・サービス名を指定して Web 調査を実行する CLI ツール (`research_agent.py`)
- Phase 1: Claude Opus 4.6 + `web_search_20260209` によるアジェンティックな情報収集
- Phase 2: Pydantic スキーマ + `client.messages.parse()` による構造化 JSON 抽出
- `natural_language_summary` フィールドへの Markdown レポート自動生成
- `user_data_handling` セクション（収集データ・利用目的・オプトアウト・ユーザー権利）
- `data_security` セクション（暗号化・認証・コンプライアンス・機密データ利用制限）
- `overall_risk_level` による `low / medium / high` の3段階リスク評価
- Markdown (.md) と JSON (.json) のファイル保存（`--output-dir` で保存先指定可）
- `--verbose` オプション（検索クエリ・進行状況の詳細ログ）
- `--json-only` オプション（JSON のみ stdout 出力、`jq` との連携向け）
- `--no-save` オプション（ファイル保存なし）
- uv による Python 仮想環境・依存関係管理

[Unreleased]: https://github.com/nlink-jp/product-research/compare/v0.3.1...HEAD
[0.3.1]: https://github.com/nlink-jp/product-research/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/nlink-jp/product-research/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/nlink-jp/product-research/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/nlink-jp/product-research/releases/tag/v0.1.0
