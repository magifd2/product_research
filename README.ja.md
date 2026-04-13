# 製品・サービス調査エージェント

[English README is here](README.md)

特定の製品・サービスを指定すると、Web を自律的に調査し、概要・利用規約・プライバシー・データセキュリティを **Markdown レポート** と **構造化 JSON** で出力する CLI ツール。

Google Gemini API + Google Search Grounding (Vertex AI) を使用。

## 特徴

- **自律的な Web 調査** — 複数の検索クエリを自動生成し、公式ドキュメント（利用規約・プライバシーポリシー）を含む情報を収集
- **構造化 JSON 出力** — Pydantic スキーマで型安全に抽出。プログラムから直接扱える
- **データ取り扱い・セキュリティに特化した項目** — ユーザーデータの収集・利用・共有、暗号化、認証、機密データ利用時の制限を専用フィールドで出力
- **リスクレベル評価** — `low / medium / high` の3段階で総合評価

## 動作フロー

```
[入力] 製品・サービス名
    │
    ▼
[Phase 1] Google Search Grounding
    │  Gemini 2.5 Pro + Google Search（Vertex AI 経由）
    │  調査テキストをストリーミングで収集・表示
    │
    ▼
[Phase 2] 構造化データ抽出
    │  Gemini 2.5 Pro + response_schema による JSON 生成
    │  収集テキストを JSON に変換 & Markdown レポートを生成
    │
    ▼
[出力] Markdown レポート + JSON ブロック（標準出力）
       .md / .json ファイル（./reports/ に保存）
```

## セットアップ

**前提条件:** Python 3.11+、[uv](https://docs.astral.sh/uv/)、Google Cloud プロジェクト（Vertex AI API 有効化済み）

```bash
# CLI ツールとしてインストール
uv tool install git+https://github.com/nlink-jp/product-research.git

# またはローカルにクローンしてインストール
git clone https://github.com/nlink-jp/product-research.git
cd product-research
uv tool install .
```

### 認証設定

Google Cloud プロジェクトと [gcloud CLI](https://cloud.google.com/sdk/docs/install) が必要です。

```bash
# Application Default Credentials を設定
gcloud auth application-default login
```

### 設定ファイル（推奨）

`~/.config/product-research/config.toml` を作成:

```toml
[gcp]
project  = "your-project-id"
location = "us-central1"
```

サンプルは `config.example.toml` を参照。

### 環境変数

環境変数は設定ファイルより優先されます。

```bash
# ツール固有（最優先）
export PRODUCT_RESEARCH_PROJECT="your-project-id"
export PRODUCT_RESEARCH_LOCATION="us-central1"

# 他ツール共通のフォールバック
export GOOGLE_CLOUD_PROJECT="your-project-id"
export GOOGLE_CLOUD_LOCATION="us-central1"  # 省略可（デフォルト: us-central1）
```

**優先順位:** 環境変数 > config.toml > デフォルト値

## 使い方

```bash
# 基本的な調査
product-research "Slack"

# 保存先ディレクトリを指定
product-research "ChatGPT" --output-dir ./reports

# 検索クエリ・進行状況の詳細ログを表示
product-research "Notion" --verbose

# JSON のみ stdout に出力（ファイル保存なし）
product-research "Dropbox" --json-only --no-save

# jq と組み合わせて特定フィールドだけ取り出す
product-research "GitHub Copilot" --json-only --no-save | jq '.data_security'
```

ツールとしてインストールしていない場合は直接実行も可能:

```bash
uv run research_agent.py "Slack"
```

### オプション一覧

| オプション | 省略形 | デフォルト | 説明 |
|---|---|---|---|
| `--output-dir` | `-o` | `./reports` | レポート保存ディレクトリ |
| `--verbose` | `-v` | off | 検索クエリ・参照 URL 等の詳細ログを表示 |
| `--json-only` | — | off | JSON のみ stdout に出力（Markdown は出力しない） |
| `--no-save` | — | off | ファイルに保存しない |

## 出力形式

### 保存ファイル

```
reports/
├── Slack_20260314_120000.md    # Markdown レポート
└── Slack_20260314_120000.json  # 構造化 JSON
```

### JSON スキーマ

```jsonc
{
  "product_name": "Slack",
  "research_date": "2026-03-14",
  "natural_language_summary": "## 製品概要\n...",  // Markdown レポート本文

  "overview": {
    "description": "...",
    "category": "ビジネスコミュニケーション",
    "provider": "Salesforce",
    "website": "https://slack.com",
    "main_features": ["チャンネル", "DM", "ワークフロー", ...],
    "pricing": {
      "model": "フリーミアム",
      "tiers": ["Free", "Pro", "Business+", "Enterprise Grid"],
      "free_tier_available": true,
      "notes": "..."
    },
    "target_users": "..."
  },

  "terms_of_service": { ... },
  "cautions": [ ... ],
  "user_data_handling": { ... },
  "data_security": { ... },

  "overall_risk_level": "low",  // "low" | "medium" | "high"
  "risk_assessment_notes": "...",
  "sources": ["https://...", ...]
}
```

## 開発者向け

開発ポリシー・コーディング規約・コミットルールは [AGENTS.md](./AGENTS.md) を参照。

## 注意事項

- 調査結果は Web 上の公開情報に基づきます。最新の利用規約・プライバシーポリシーは必ず公式サイトで確認してください
- 情報が見つからない項目は `"不明"` と記載されます。推測による補完は行いません
- Vertex AI の利用料金が発生します（Gemini 2.5 Pro 使用）。Google Cloud プロジェクトの課金設定を確認してください
