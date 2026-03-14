# AGENTS.md — 開発ポリシー・ルール

AI エージェント（Claude Code 等）および人間の開発者が本プロジェクトで作業する際のルールと規約を定義する。

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

`ANTHROPIC_API_KEY` を環境変数で渡すこと。`.env` ファイルに書く場合はリポジトリにコミットしない（`.gitignore` 済み）。

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

### Claude API 呼び出し

- モデルは `claude-opus-4-6` 固定。変更する場合はコメントで理由を記載する
- Phase 1（情報収集）では `thinking={"type": "adaptive"}` を使用する
- `pause_turn` への対応を必ず実装する（サーバーサイドツールの継続処理）
- API キーをコードにハードコードしない

---

## ファイル・ディレクトリ構成

```
product_research/
├── research_agent.py   # メインスクリプト（単一ファイル構成を維持する）
├── pyproject.toml      # プロジェクト定義・依存パッケージ
├── uv.lock             # ロックファイル（コミット対象）
├── .python-version     # Python バージョン固定（コミット対象）
├── .gitignore
├── README.md
├── CHANGELOG.md
├── AGENTS.md           # 本ファイル
└── reports/            # 生成レポートの保存先（.gitignore 済み）
```

**単一ファイル構成を維持する**: 機能追加でファイルを分割したい場合は、先に設計を検討してから行う。

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

## やってはいけないこと

- `ANTHROPIC_API_KEY` 等の秘密情報をコードや設定ファイルにハードコードしない
- `reports/` 以下のファイルをコミットしない
- `uv.lock` を手動編集しない（`uv add/remove` に任せる）
- `pip install` を使わない
- `overall_risk_level` を `low/medium/high` 以外の値で設定しない
- Claude API のモデル名を日付サフィックス付きで指定しない（例: `claude-opus-4-6-20251101` は不可。`claude-opus-4-6` を使う）
