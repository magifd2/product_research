# AGENTS.md — 開発ポリシー・ルール

AI エージェント（Claude Code 等）および人間の開発者が本プロジェクトで作業する際のルールと規約を定義する。

---

## コミュニケーション

- **開発者とのやり取りは日本語をベースラインとする**
- コード中のコメント・docstring も日本語で書く
- コミットメッセージは日本語可（Conventional Commits の type 部分は英語を維持する）

---

## プロジェクト概要

製品・サービス名を入力すると、Web を自律調査して概要・利用規約・プライバシー・データセキュリティを **Markdown レポート + 構造化 JSON** で出力する CLI ツール。

- エントリーポイント: `research_agent.py`
- 実行: `uv run research_agent.py "<製品名>"`
- Python バージョン: 3.11 以上

---

## 開発環境

### uv を使うこと

パッケージ管理・仮想環境には必ず **uv** を使用する。`pip` や `poetry` は使わない。

```bash
uv sync                  # 依存パッケージのインストール
uv add <package>         # パッケージ追加
uv remove <package>      # パッケージ削除
uv run research_agent.py # スクリプト実行
```

### 環境変数

秘密情報は環境変数で渡すこと。`.env` ファイルに書く場合はリポジトリにコミットしない（`.gitignore` 済み）。

| 変数名 | 用途 | 対象スクリプト |
|---|---|---|
| `ANTHROPIC_API_KEY` | Anthropic API 認証 | `research_agent.py` |
| `GOOGLE_CLOUD_PROJECT` | GCP プロジェクト ID | `research_agent_gemini.py` |
| `GOOGLE_CLOUD_LOCATION` | Vertex AI リージョン（省略時: `us-central1`） | `research_agent_gemini.py` |

**Google 版の認証セットアップ（Vertex AI）:**

```bash
# 1. gcloud CLI をインストール済みであること
# 2. Application Default Credentials を設定
gcloud auth application-default login

# 3. 使用する GCP プロジェクトを設定
gcloud config set project YOUR_PROJECT_ID

# 4. 環境変数を設定
export GOOGLE_CLOUD_PROJECT="your-project-id"
export GOOGLE_CLOUD_LOCATION="us-central1"  # 省略可
```

---

## コーディング規約

### 全般

- **型ヒントを必ず付ける**。`Optional[str]` ではなく `str | None` を使う（Python 3.10+ 記法）
- 関数・クラスには docstring を書く（1行で十分）
- `print()` はユーザー向け出力のみ。進行状況は `_progress()` ヘルパー経由で `stderr` に出力する
- マジックナンバーは定数化する

### Pydantic モデル

- モデルフィールドには必ず `Field(description="...")` を付ける（Claude への指示として機能するため）
- モデルを追加・変更した場合は `ResearchReport` 最上位クラスへの影響を確認すること
- `Optional[str]` フィールドには `default=None` を明示する

### 型ヒント

- SDK が提供する型を積極的に使う（例: `list[dict]` ではなく `list[MessageParam]`）
- `anthropic.types` から必要な型をインポートする
- `pyright` で 0 errors を維持する

### Claude API 呼び出し（Anthropic 版）

- モデルは `claude-opus-4-6` 固定。変更する場合はコメントで理由を記載する
- Phase 1（情報収集）では `thinking={"type": "adaptive"}` を使用する
- `pause_turn` への対応を必ず実装する（サーバーサイドツールの継続処理）
- API キーをコードにハードコードしない

### Gemini API 呼び出し（Google 版）

- モデルは `gemini-2.5-pro` 固定。変更する場合はコメントで理由を記載する
- Phase 1 は `tools=[types.Tool(google_search=types.GoogleSearch())]` で Search Grounding を有効化する
- Phase 2 は `response_mime_type="application/json"` + `response_schema=ResearchReport` で構造化抽出する
- `response.text` は `None` になり得るため必ずガード処理を入れる
- API キーは `GOOGLE_API_KEY` 環境変数で渡す。コードにハードコードしない

---

## ファイル・ディレクトリ構成

```
product_research/
├── research_agent.py          # Anthropic 版メインスクリプト
├── research_agent_gemini.py   # Google Gemini 版メインスクリプト
├── pyproject.toml             # プロジェクト定義・依存パッケージ
├── uv.lock                    # ロックファイル（コミット対象）
├── .python-version            # Python バージョン固定（コミット対象）
├── .gitignore
├── README.md
├── CHANGELOG.md
├── AGENTS.md                  # 本ファイル
└── reports/                   # 生成レポートの保存先（.gitignore 済み）
```

**モデル・ユーティリティの共有:** Pydantic モデルおよびユーティリティ関数は `research_agent.py` で定義し、`research_agent_gemini.py` からインポートして再利用する。重複定義しない。

---

## Git・バージョン管理

### コミットメッセージ

[Conventional Commits](https://www.conventionalcommits.org/) に従う。

```
<type>: <概要（日本語可）>

[本文（任意）]
```

| type | 用途 |
|---|---|
| `feat` | 新機能 |
| `fix` | バグ修正 |
| `docs` | ドキュメントのみの変更 |
| `refactor` | 動作を変えないコード変更 |
| `chore` | ビルド・ツール・依存関係の変更 |

例:
```
feat: --markdown-only オプションを追加
fix: pause_turn 時に無限ループになるバグを修正
docs: README にjqの使用例を追記
chore: anthropic を 0.84.0 に更新
```

### ブランチ

| ブランチ | 用途 |
|---|---|
| `main` | リリース済みの安定版 |
| `feat/<name>` | 機能開発 |
| `fix/<name>` | バグ修正 |

### タグ・リリース

セマンティックバージョニング (`vX.Y.Z`) でタグを打つ。

- `PATCH (Z)`: バグ修正・ドキュメント更新
- `MINOR (Y)`: 後方互換のある機能追加
- `MAJOR (X)`: 後方互換のない変更（CLI オプション変更・JSON スキーマ変更など）

---

## CHANGELOG の更新ルール

**機能追加・変更・修正を行ったら必ず CHANGELOG.md を同じコミットで更新する。**

1. 変更内容を `[Unreleased]` セクションの該当カテゴリに追記する
2. リリース時は `[Unreleased]` を `[x.y.z] - YYYY-MM-DD` に切り出す
3. `pyproject.toml` の `version` と合わせる

カテゴリ:
- `Added` — 新機能
- `Changed` — 既存機能の変更
- `Fixed` — バグ修正
- `Removed` — 削除された機能
- `Security` — セキュリティ修正

---

## 変更手順のルール

コードを修正する際は、以下のステップを厳守する。

### 1. 小さく変更する

- 1つのコミットで変更する範囲は最小限にとどめる
- 複数の目的を1つの変更にまとめない（例: バグ修正と機能追加を同時に行わない）
- 大きな変更が必要な場合は、先に変更計画をユーザーに提示して合意を得てから進める

### 2. 動作確認してから次へ進む

変更ごとに必ず動作確認を行い、問題がないことを確認してから次の変更に進む。

```bash
# 構文エラーがないか確認
uv run python -m py_compile research_agent.py

# 型チェック
uv run pyright research_agent.py

# ヘルプが表示されるか（基本的な動作確認）
uv run research_agent.py --help

# 実際に動作するか（API キーが必要）
uv run research_agent.py "テスト対象" --no-save
```

### 3. 確認できたらコミットする

動作確認が取れた段階でコミットする。未確認の状態でコミットしない。

---

## やってはいけないこと

- `ANTHROPIC_API_KEY` 等の秘密情報をコードや設定ファイルにハードコードしない
- `reports/` 以下のファイルをコミットしない
- `uv.lock` を手動編集しない（`uv add/remove` に任せる）
- `pip install` を使わない
- `overall_risk_level` を `low/medium/high` 以外の値で設定しない
- Claude API のモデル名を日付サフィックス付きで指定しない（例: `claude-opus-4-6-20251101` は不可。`claude-opus-4-6` を使う）
