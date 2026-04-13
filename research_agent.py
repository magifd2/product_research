#!/usr/bin/env python3
"""
製品・サービス調査エージェント

Google Gemini API + Google Search Grounding (Vertex AI) を使用して、
製品・サービスの概要・利用規約・プライバシー・データセキュリティを調査し、
構造化レポートを出力する。

使い方:
    python research_agent.py "Slack"
    python research_agent.py "ChatGPT" --output-dir ./reports
    python research_agent.py "Notion" --verbose
    python research_agent.py "Dropbox" --json-only
"""

import json
import os
import random
import sys
import time
import argparse
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Optional, TypeVar

from google import genai
from google.genai import types
from pydantic import BaseModel, Field

_T = TypeVar("_T")


# ──────────────────────────────────────────────
# Pydantic モデル定義
# ──────────────────────────────────────────────

class PricingInfo(BaseModel):
    model: str = Field(description="料金体系 (例: サブスクリプション、フリーミアム、買い切り)")
    tiers: list[str] = Field(description="利用可能なプランの一覧")
    free_tier_available: bool = Field(description="無料プランの有無")
    notes: str = Field(description="料金に関する補足情報")


class Overview(BaseModel):
    description: str = Field(description="製品・サービスの説明")
    category: str = Field(description="カテゴリ (例: コラボレーションツール、クラウドストレージ)")
    provider: str = Field(description="提供企業・組織名")
    website: Optional[str] = Field(default=None, description="公式サイト URL")
    main_features: list[str] = Field(description="主要機能のリスト")
    pricing: PricingInfo
    target_users: str = Field(description="主な対象ユーザー層")


class TermsOfService(BaseModel):
    summary: str = Field(description="利用規約の要約")
    key_points: list[str] = Field(description="重要な条項のリスト")
    user_obligations: list[str] = Field(description="ユーザーの義務・責任")
    restrictions: list[str] = Field(description="禁止事項・制限事項")
    intellectual_property: str = Field(description="知的財産権に関する規定")
    termination_conditions: str = Field(description="アカウント停止・解約条件")
    governing_law: Optional[str] = Field(default=None, description="準拠法・管轄裁判所")
    last_updated: Optional[str] = Field(default=None, description="最終更新日")
    url: Optional[str] = Field(default=None, description="利用規約 URL")


class UserDataHandling(BaseModel):
    data_collected: list[str] = Field(description="収集されるユーザーデータの種類")
    data_usage_purposes: list[str] = Field(description="データ利用目的")
    third_party_sharing: list[str] = Field(description="データ共有先の第三者・パートナー")
    data_retention_period: str = Field(description="データ保持期間")
    user_rights: list[str] = Field(description="ユーザーのデータ権利 (GDPR・CCPA 等)")
    opt_out_options: list[str] = Field(description="データ収集・利用のオプトアウト方法")
    children_data_policy: str = Field(description="未成年者データに関するポリシー")
    privacy_policy_url: Optional[str] = Field(default=None, description="プライバシーポリシー URL")
    notable_concerns: list[str] = Field(description="プライバシー上の懸念点・注意事項")


class DataSecurity(BaseModel):
    encryption_at_rest: str = Field(description="保存データの暗号化方式")
    encryption_in_transit: str = Field(description="転送データの暗号化方式")
    security_certifications: list[str] = Field(description="取得済みセキュリティ認証 (SOC2, ISO27001 等)")
    compliance_frameworks: list[str] = Field(description="準拠する規制・フレームワーク (GDPR, HIPAA, CCPA 等)")
    data_storage_location: str = Field(description="データの保存地域・データセンター所在地")
    access_controls: str = Field(description="アクセス制御の仕組み")
    incident_response: str = Field(description="セキュリティインシデント対応方針")
    known_breaches: list[str] = Field(description="既知のデータ漏洩・セキュリティインシデント")
    restrictions_for_sensitive_data: list[str] = Field(description="機密データ利用時の制限・制約事項")
    vulnerability_disclosure_program: bool = Field(description="脆弱性開示プログラムの有無")


class AIAgentBehavior(BaseModel):
    has_autonomous_behavior: bool = Field(
        description="目的達成のために自律的に実行計画を構築・実行する AI エージェント的動作の有無"
    )
    autonomous_capabilities: list[str] = Field(
        description="自律動作の具体的な能力・機能 (例: タスク分解、ツール呼び出し、外部サービス操作、コード実行)"
    )
    action_scope: str = Field(
        description="自律動作が及ぶ範囲 (例: 読み取り専用、ファイル操作、外部 API 呼び出し、メール送信等)"
    )
    user_control_mechanisms: list[str] = Field(
        description="ユーザーが自律動作を制御・監視・介入するための手段 (例: 承認フロー、一時停止、スコープ制限)"
    )
    approval_required_actions: list[str] = Field(
        description="実行前にユーザー承認が必要なアクション"
    )
    audit_log_available: bool = Field(description="自律動作の実行ログ・監査ログの提供有無")
    rollback_capability: str = Field(description="自律動作の取り消し・ロールバック手段")
    notable_risks: list[str] = Field(description="自律動作に伴うリスク・懸念点")


class ResearchReport(BaseModel):
    product_name: str
    research_date: str
    natural_language_summary: str = Field(
        description=(
            "Markdown 形式の日本語レポート。"
            "## 製品概要 / ## 主要機能 / ## 利用規約の要点 / "
            "## プライバシー・データ取り扱い / ## セキュリティ状況 / "
            "## ユーザーへの注意事項 / ## 総合評価 の見出しを含めること"
        )
    )
    overview: Overview
    terms_of_service: TermsOfService
    cautions: list[str] = Field(description="ユーザーへの重要な注意事項・警告")
    user_data_handling: UserDataHandling
    data_security: DataSecurity
    ai_agent_behavior: AIAgentBehavior
    overall_risk_level: str = Field(description="リスクレベル: low / medium / high")
    risk_assessment_notes: str = Field(description="リスク評価の根拠説明")
    sources: list[str] = Field(description="参照した URL・ソース一覧")


# ──────────────────────────────────────────────
# 出力フォーマット
# ──────────────────────────────────────────────

RISK_EMOJI = {"low": "🟢 Low", "medium": "🟡 Medium", "high": "🔴 High"}


def format_full_output(report: ResearchReport) -> tuple[str, str]:
    """Markdown テキストと JSON 文字列のタプルを返す"""

    # ── Markdown ──
    risk_label = RISK_EMOJI.get(report.overall_risk_level.lower(), report.overall_risk_level)
    md_lines = [
        f"# 製品・サービス調査レポート: {report.product_name}",
        "",
        f"| 項目 | 内容 |",
        f"|------|------|",
        f"| **調査日** | {report.research_date} |",
        f"| **提供元** | {report.overview.provider} |",
        f"| **カテゴリ** | {report.overview.category} |",
        f"| **リスクレベル** | {risk_label} |",
        "",
        "---",
        "",
        report.natural_language_summary,
        "",
    ]

    if report.cautions:
        md_lines += ["", "## ⚠️ 重要な注意事項"]
        for caution in report.cautions:
            md_lines.append(f"- {caution}")

    md_lines += [
        "",
        "## 📊 リスク評価の根拠",
        report.risk_assessment_notes,
    ]

    if report.sources:
        md_lines += ["", "## 📚 参照ソース"]
        for src in report.sources:
            md_lines.append(f"- {src}")

    markdown = "\n".join(md_lines)

    # ── JSON ──
    json_str = json.dumps(report.model_dump(), ensure_ascii=False, indent=2)

    return markdown, json_str


# ──────────────────────────────────────────────
# ユーティリティ
# ──────────────────────────────────────────────

def _progress(msg: str) -> None:
    print(f"  {msg}", file=sys.stderr, flush=True)


def _divider(char: str = "─", width: int = 60) -> str:
    return char * width


# ── リトライ設定 ──
_MAX_RETRIES = 5
_RETRY_BASE_DELAY = 5.0  # 秒（指数バックオフの基底）
_RATE_LIMIT_KEYWORDS = ("429", "RESOURCE_EXHAUSTED", "TOO MANY REQUESTS", "QUOTA")


def _is_rate_limit(e: Exception) -> bool:
    msg = str(e).upper()
    return any(k in msg for k in _RATE_LIMIT_KEYWORDS)


def _call_with_retry(fn: Callable[[], _T], label: str = "") -> _T:
    """429 / RESOURCE_EXHAUSTED 発生時に指数バックオフ＋ジッターでリトライする。

    リトライ間隔: base * 2^attempt + uniform(0, 1) 秒
    デフォルト上限: 5, 10, 20, 40, 80 秒
    """
    for attempt in range(_MAX_RETRIES):
        try:
            return fn()
        except Exception as e:
            if _is_rate_limit(e) and attempt < _MAX_RETRIES - 1:
                delay = _RETRY_BASE_DELAY * (2 ** attempt) + random.uniform(0, 1)
                tag = f" [{label}]" if label else ""
                print(file=sys.stderr)  # ストリーム途中の場合に改行
                _progress(
                    f"レート制限 (429){tag} — {delay:.1f} 秒後にリトライ"
                    f" ({attempt + 1}/{_MAX_RETRIES - 1})"
                )
                time.sleep(delay)
                continue
            raise
    raise RuntimeError("unreachable")

# ──────────────────────────────────────────────
# モデル設定
# ──────────────────────────────────────────────

RESEARCH_MODEL = "gemini-2.5-pro"
EXTRACTION_MODEL = "gemini-2.5-pro"

# ──────────────────────────────────────────────
# システムプロンプト
# ──────────────────────────────────────────────

RESEARCH_SYSTEM_PROMPT = """\
あなたは製品・サービスの調査専門家です。
Google Search を使って以下の観点から徹底的に調査してください：

1. **製品概要**: 機能、ビジネスモデル、対象ユーザー、価格体系
2. **利用規約（ToS）**: 主要条項、ユーザーの義務、禁止事項、アカウント停止条件
3. **プライバシーポリシー**: 収集データの種類、利用目的、第三者提供先、データ保持期間
4. **データセキュリティ**: 暗号化方式、セキュリティ認証、コンプライアンス準拠
5. **ユーザーデータの権利**: アクセス権、削除権、オプトアウト方法、データポータビリティ
6. **既知の問題**: セキュリティインシデント、データ漏洩、プライバシー問題、批判
7. **利用上の注意点**: リスク、制限、特定ユーザー層への懸念
8. **AI エージェント動作**: 目的達成のために自律的に実行計画を構築・実行する機能の有無、
   自律動作が及ぶ範囲（ファイル操作・外部サービス呼び出し・コード実行 等）、
   ユーザーが自律動作を制御・監視・介入するための手段（承認フロー・一時停止・スコープ制限 等）、
   自律動作に伴うリスク・実行ログの有無

最新の情報を重点的に収集してください。
公式ドキュメント（利用規約ページ、プライバシーポリシーページ）を直接確認してください。
"""

EXTRACTION_SYSTEM_PROMPT = """\
あなたは製品・サービス調査レポートを構造化データに変換する専門家です。
提供された調査テキストから情報を正確に抽出してください。

**natural_language_summary フィールドの要件:**
Markdown 形式で、以下の見出しを含む詳細な日本語レポートを書いてください：
- ## 製品概要
- ## 主要機能
- ## 利用規約の要点
- ## プライバシー・データ取り扱い
- ## セキュリティ状況
- ## AI エージェント動作と制御
- ## ユーザーへの注意事項
- ## 総合評価

**全般的な注意:**
- 調査テキストに記載のない情報は「不明」と記載し、推測や補完は行わないこと
- overall_risk_level は "low"・"medium"・"high" のいずれかのみ設定すること
- data_security.restrictions_for_sensitive_data には、機密性の高いデータ（医療情報・金融情報・個人識別情報など）
  を扱う際の制限・制約・注意事項を具体的に記載すること
- user_data_handling.notable_concerns には、プライバシー上の懸念点を率直に記載すること
- ai_agent_behavior.has_autonomous_behavior は、AI が自律的に計画を立てて外部操作を行う機能が存在する場合のみ true とすること
"""

# ──────────────────────────────────────────────
# Phase 1: 情報収集（Google Search Grounding）
# ──────────────────────────────────────────────

def gather_information(
    client: genai.Client,
    product_name: str,
    verbose: bool = False,
) -> str:
    """Google Search Grounding を使って製品・サービス情報を収集する"""

    _progress("Gemini + Google Search Grounding で調査中...\n")

    def _run() -> str:
        parts: list[str] = []
        for chunk in client.models.generate_content_stream(
            model=RESEARCH_MODEL,
            contents=(
                f"以下の製品・サービスについて包括的な調査を実施してください：\n\n"
                f"**{product_name}**\n\n"
                "特に利用規約、プライバシーポリシー、ユーザーデータの取り扱い、"
                "データセキュリティ、既知のセキュリティインシデントについて詳しく調べてください。"
            ),
            config=types.GenerateContentConfig(
                system_instruction=RESEARCH_SYSTEM_PROMPT,
                tools=[types.Tool(google_search=types.GoogleSearch())],
            ),
        ):
            if chunk.text:
                parts.append(chunk.text)
                print(chunk.text, end="", flush=True, file=sys.stderr)

            if verbose and chunk.candidates:
                for candidate in chunk.candidates:
                    meta = getattr(candidate, "grounding_metadata", None)
                    if meta:
                        for grounding_chunk in getattr(meta, "grounding_chunks", []) or []:
                            web = getattr(grounding_chunk, "web", None)
                            if web:
                                _progress(f"\n  [参照] {getattr(web, 'uri', '')}")

        print(file=sys.stderr)  # ストリーム末尾の改行
        return "".join(parts)

    result = _call_with_retry(_run, "Phase 1")
    _progress("情報収集フェーズ完了")
    return result


# ──────────────────────────────────────────────
# Phase 2: 構造化データ抽出
# ──────────────────────────────────────────────

def extract_structured_report(
    client: genai.Client,
    product_name: str,
    research_text: str,
) -> ResearchReport | None:
    """収集した調査テキストから構造化レポートを抽出する"""

    def _run() -> str:
        parts: list[str] = []
        for chunk in client.models.generate_content_stream(
            model=EXTRACTION_MODEL,
            contents=(
                f"以下の調査テキストから **{product_name}** の構造化レポートを生成してください。\n\n"
                f"調査実施日: {datetime.now().strftime('%Y-%m-%d')}\n\n"
                f"━━━ 調査テキスト ━━━\n{research_text}"
            ),
            config=types.GenerateContentConfig(
                system_instruction=EXTRACTION_SYSTEM_PROMPT,
                response_mime_type="application/json",
                response_schema=ResearchReport,
            ),
        ):
            if chunk.text:
                parts.append(chunk.text)
                print(".", end="", flush=True, file=sys.stderr)  # JSON なので内容でなくドットで進捗表示

        print(file=sys.stderr)  # ストリーム末尾の改行
        return "".join(parts)

    full_text = _call_with_retry(_run, "Phase 2")

    if not full_text:
        _progress("レスポンスが空でした")
        return None

    try:
        return ResearchReport.model_validate_json(full_text)
    except Exception as e:
        _progress(f"JSON パース失敗: {e}")
        return None


# ──────────────────────────────────────────────
# CLI エントリーポイント
# ──────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="製品・サービス調査エージェント — 概要・ToS・データ取り扱い・セキュリティを構造化レポートで出力",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
例:
  python research_agent.py "Slack"
  python research_agent.py "ChatGPT" --output-dir ./reports
  python research_agent.py "Notion" --verbose
  python research_agent.py "Dropbox Business" --json-only --no-save
        """,
    )
    parser.add_argument("product", help="調査する製品・サービス名")
    parser.add_argument(
        "--output-dir", "-o",
        default="./reports",
        help="レポート保存ディレクトリ (デフォルト: ./reports)",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="参照 URL 等の詳細ログを表示")
    parser.add_argument("--json-only", action="store_true", help="JSON のみ stdout に出力")
    parser.add_argument("--no-save", action="store_true", help="ファイルに保存しない")
    args = parser.parse_args()

    from config import get_config
    cfg = get_config()
    client = genai.Client(
        vertexai=True,
        project=cfg["project"],
        location=cfg["location"],
    )

    print(_divider("═"), file=sys.stderr)
    print("  製品・サービス調査エージェント", file=sys.stderr)
    print(f"  対象: {args.product}", file=sys.stderr)
    print(_divider("═"), file=sys.stderr)

    # ── Phase 1: 情報収集 ──
    print("\n[Phase 1] 情報収集 (Google Search Grounding)", file=sys.stderr)
    print(_divider(), file=sys.stderr)
    research_text = gather_information(client, args.product, args.verbose)

    if not research_text.strip():
        print("❌ 情報収集に失敗しました。製品名を確認してください。", file=sys.stderr)
        sys.exit(1)

    # ── Phase 2: 構造化抽出 ──
    print(f"\n[Phase 2] 構造化データ抽出", file=sys.stderr)
    print(_divider(), file=sys.stderr)
    _progress("Gemini による構造化抽出中...")
    report = extract_structured_report(client, args.product, research_text)

    if report is None:
        print("❌ 構造化データの抽出に失敗しました。", file=sys.stderr)
        sys.exit(1)

    print(f"\n✅ 調査完了: {args.product}", file=sys.stderr)
    print(_divider("═"), file=sys.stderr)

    # ── 出力 ──
    markdown_output, json_output = format_full_output(report)

    if args.json_only:
        print(json_output)
    else:
        print(markdown_output)
        print()
        print(_divider("═"))
        print("```json")
        print(json_output)
        print("```")

    # ── ファイル保存 ──
    if not args.no_save:
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        safe_name = "".join(
            c if c.isalnum() or c in "-_" else "_"
            for c in args.product
        ).strip("_")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        md_path = output_dir / f"{safe_name}_{timestamp}.md"
        json_path = output_dir / f"{safe_name}_{timestamp}.json"

        md_path.write_text(markdown_output, encoding="utf-8")
        json_path.write_text(json_output, encoding="utf-8")

        print(f"\n📁 レポート保存完了:", file=sys.stderr)
        print(f"   Markdown : {md_path}", file=sys.stderr)
        print(f"   JSON     : {json_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
