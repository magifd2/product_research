# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- Google Gemini 版を Google AI Studio API キー方式から Vertex AI（Application Default Credentials）方式に変更
- 環境変数を `GOOGLE_API_KEY` から `GOOGLE_CLOUD_PROJECT` / `GOOGLE_CLOUD_LOCATION` に変更
- Phase 1・2 をストリーミングに変更（Phase 1 は調査テキストをリアルタイム表示、Phase 2 はドットで進捗表示）
- Anthropic 版 Phase 1 を `client.messages.create()` から `client.messages.stream()` に変更（調査テキストをリアルタイム stderr 表示）
- Anthropic 版 Phase 2 に開始・完了メッセージを追加（`messages.parse()` はブロッキングのため呼び出し前後で進捗を表示）

### Added
- Google Gemini 版調査エージェント (`research_agent_gemini.py`)
- Google Search Grounding による情報収集（Phase 1）
- Gemini の `response_schema` による構造化 JSON 抽出（Phase 2）
- 保存ファイル名に `_gemini_` サフィックスを付与して Anthropic 版と区別

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

[Unreleased]: https://github.com/your-org/product-research/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/your-org/product-research/releases/tag/v0.1.0
