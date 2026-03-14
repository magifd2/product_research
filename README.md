# 製品・サービス調査エージェント

特定の製品・サービスを指定すると、Web を自律的に調査し、概要・利用規約・プライバシー・データセキュリティを **Markdown レポート** と **構造化 JSON** で出力する CLI ツール。

## 特徴

- **自律的な Web 調査** — Claude が複数の検索クエリを自動生成し、公式ドキュメント（利用規約・プライバシーポリシー）を含む情報を収集
- **構造化 JSON 出力** — Pydantic スキーマで型安全に抽出。プログラムから直接扱える
- **データ取り扱い・セキュリティに特化した項目** — ユーザーデータの収集・利用・共有、暗号化、認証、機密データ利用時の制限を専用フィールドで出力
- **リスクレベル評価** — `low / medium / high` の3段階で総合評価

## 動作フロー

```
[入力] 製品・サービス名
    │
    ▼
[Phase 1] Web 検索アジェンティックループ
    │  Claude Opus 4.6 + web_search ツール（サーバーサイド実行）
    │  利用規約・プライバシーポリシー・セキュリティ情報を収集
    │
    ▼
[Phase 2] 構造化データ抽出
    │  Claude Opus 4.6 + Pydantic スキーマ
    │  収集テキストを JSON に変換 & Markdown レポートを生成
    │
    ▼
[出力] Markdown レポート + JSON ブロック（標準出力）
       .md / .json ファイル（./reports/ に保存）
```

## セットアップ

**前提条件:** [uv](https://docs.astral.sh/uv/) がインストールされていること

```bash
# リポジトリをクローン後
cd product_research

# 仮想環境の作成と依存パッケージのインストール
uv sync

# Anthropic API キーを設定
export ANTHROPIC_API_KEY="sk-ant-..."
```

## 使い方

```bash
# 基本的な調査
uv run research_agent.py "Slack"

# 保存先ディレクトリを指定
uv run research_agent.py "ChatGPT" --output-dir ./reports

# 検索クエリ・進行状況の詳細ログを表示
uv run research_agent.py "Notion" --verbose

# JSON のみ stdout に出力（ファイル保存なし）
uv run research_agent.py "Dropbox" --json-only --no-save

# jq と組み合わせて特定フィールドだけ取り出す
uv run research_agent.py "GitHub Copilot" --json-only | jq '.data_security'
uv run research_agent.py "Google Workspace" --json-only | jq '.user_data_handling.notable_concerns'
```

### オプション一覧

| オプション | 省略形 | デフォルト | 説明 |
|---|---|---|---|
| `--output-dir` | `-o` | `./reports` | レポート保存ディレクトリ |
| `--verbose` | `-v` | off | 検索クエリ・進行状況の詳細ログを表示 |
| `--json-only` | — | off | JSON のみ stdout に出力（Markdown は出力しない） |
| `--no-save` | — | off | ファイルに保存しない |

## 出力形式

### 標準出力

```
# 製品・サービス調査レポート: Slack
...（Markdown レポート）...

════════════════════════════════════════════════════════════
```json
{
  "product_name": "Slack",
  "research_date": "2026-03-14",
  ...
}
```

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

  "terms_of_service": {
    "summary": "...",
    "key_points": [...],
    "user_obligations": [...],
    "restrictions": [...],
    "intellectual_property": "...",
    "termination_conditions": "...",
    "governing_law": "カリフォルニア州法",
    "url": "https://slack.com/terms-of-service"
  },

  "cautions": [
    "無料プランではメッセージ履歴が90日に制限される",
    ...
  ],

  // ユーザーデータの取り扱い（専用セクション）
  "user_data_handling": {
    "data_collected": ["メッセージ内容", "ファイル", "利用状況", ...],
    "data_usage_purposes": ["サービス提供", "機能改善", ...],
    "third_party_sharing": [...],
    "data_retention_period": "...",
    "user_rights": ["アクセス権", "削除権", "データポータビリティ", ...],
    "opt_out_options": [...],
    "children_data_policy": "...",
    "privacy_policy_url": "https://slack.com/privacy-policy",
    "notable_concerns": [...]  // プライバシー上の懸念点
  },

  // データセキュリティ・制限（専用セクション）
  "data_security": {
    "encryption_at_rest": "AES-256",
    "encryption_in_transit": "TLS 1.2以上",
    "security_certifications": ["SOC 2 Type II", "ISO 27001", ...],
    "compliance_frameworks": ["GDPR", "CCPA", "HIPAA (Enterprise)"],
    "data_storage_location": "米国・EU",
    "access_controls": "...",
    "incident_response": "...",
    "known_breaches": [...],
    "restrictions_for_sensitive_data": [...],  // 機密データ利用時の制限・制約
    "vulnerability_disclosure_program": true
  },

  "overall_risk_level": "low",  // "low" | "medium" | "high"
  "risk_assessment_notes": "...",
  "sources": ["https://...", ...]
}
```

## 注意事項

- 調査結果は Web 上の公開情報に基づきます。最新の利用規約・プライバシーポリシーは必ず公式サイトで確認してください
- API の利用料金が発生します（Claude Opus 4.6 使用）。1回の調査で入出力合わせて数万〜10万トークン程度を消費します
- 情報が見つからない項目は `"不明"` と記載されます。推測による補完は行いません
