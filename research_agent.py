#!/usr/bin/env python3
"""
製品・サービス調査エージェント

特定の製品・サービスについて、概要・利用規約・注意点・データ取り扱い・
セキュリティ情報を調査し、Markdown レポートと構造化 JSON を出力する。

使い方:
    python research_agent.py "Slack"
    python research_agent.py "ChatGPT" --output-dir ./reports
    python research_agent.py "Notion" --verbose
    python research_agent.py "Dropbox" --json-only
"""

import json
import sys
import argparse
from datetime import datetime
from pathlib import Path
from typing import Optional

import anthropic
from pydantic import BaseModel, Field


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
    overall_risk_level: str = Field(description="リスクレベル: low / medium / high")
    risk_assessment_notes: str = Field(description="リスク評価の根拠説明")
    sources: list[str] = Field(description="参照した URL・ソース一覧")


# ──────────────────────────────────────────────
# Phase 1: 情報収集（Web 検索アジェンティックループ）
# ──────────────────────────────────────────────

RESEARCH_SYSTEM_PROMPT = """\
あなたは製品・サービスの調査専門家です。
指定された製品・サービスについて、Web 検索を使って以下の観点から徹底的に調査してください：

1. **製品概要**: 機能、ビジネスモデル、対象ユーザー、価格体系
2. **利用規約（ToS）**: 主要条項、ユーザーの義務、禁止事項、アカウント停止条件
3. **プライバシーポリシー**: 収集データの種類、利用目的、第三者提供先、データ保持期間
4. **データセキュリティ**: 暗号化方式、セキュリティ認証、コンプライアンス準拠
5. **ユーザーデータの権利**: アクセス権、削除権、オプトアウト方法、データポータビリティ
6. **既知の問題**: セキュリティインシデント、データ漏洩、プライバシー問題、批判
7. **利用上の注意点**: リスク、制限、特定ユーザー層への懸念

最新の情報を重点的に収集してください。英語・日本語の両方で検索することを推奨します。
公式ドキュメント（利用規約ページ、プライバシーポリシーページ）を直接確認してください。
"""


def gather_information(
    client: anthropic.Anthropic,
    product_name: str,
    verbose: bool = False,
) -> str:
    """Web 検索を使って製品・サービス情報を収集する（サーバーサイドツールループ）"""

    messages: list[dict] = [
        {
            "role": "user",
            "content": (
                f"以下の製品・サービスについて包括的な調査を実施してください：\n\n"
                f"**{product_name}**\n\n"
                "特に利用規約、プライバシーポリシー、ユーザーデータの取り扱い、"
                "データセキュリティ、既知のセキュリティインシデントについて詳しく調べてください。"
            ),
        }
    ]

    gathered_parts: list[str] = []
    max_continuations = 5

    for i in range(max_continuations):
        _progress(f"Web 検索中... (試行 {i + 1}/{max_continuations})")

        response = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=8192,
            thinking={"type": "adaptive"},
            system=RESEARCH_SYSTEM_PROMPT,
            tools=[{"type": "web_search_20260209", "name": "web_search"}],
            messages=messages,
        )

        for block in response.content:
            if block.type == "text":
                gathered_parts.append(block.text)
                if verbose:
                    preview = block.text[:120].replace("\n", " ")
                    _progress(f"  [テキスト] {preview}...")
            elif block.type == "server_tool_use" and verbose:
                input_data = getattr(block, "input", {})
                query = input_data.get("query", "") if isinstance(input_data, dict) else ""
                _progress(f"  [検索クエリ] {query}")

        if response.stop_reason == "end_turn":
            _progress("情報収集フェーズ完了")
            break
        elif response.stop_reason == "pause_turn":
            _progress("検索続行中...")
            # pause_turn: 元のユーザーメッセージ + アシスタント応答を維持して再送
            messages = [
                messages[0],
                {"role": "assistant", "content": response.content},
            ]
        else:
            _progress(f"停止理由: {response.stop_reason}")
            break

    return "\n\n---\n\n".join(gathered_parts)


# ──────────────────────────────────────────────
# Phase 2: 構造化データ抽出
# ──────────────────────────────────────────────

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
- ## ユーザーへの注意事項
- ## 総合評価

**全般的な注意:**
- 調査テキストに記載のない情報は「不明」と記載し、推測や補完は行わないこと
- overall_risk_level は "low"・"medium"・"high" のいずれかのみ設定すること
- data_security.restrictions_for_sensitive_data には、機密性の高いデータ（医療情報・金融情報・個人識別情報など）
  を扱う際の制限・制約・注意事項を具体的に記載すること
- user_data_handling.notable_concerns には、プライバシー上の懸念点を率直に記載すること
"""


def extract_structured_report(
    client: anthropic.Anthropic,
    product_name: str,
    research_text: str,
) -> Optional[ResearchReport]:
    """収集した調査テキストから構造化レポートを抽出する"""

    response = client.messages.parse(
        model="claude-opus-4-6",
        max_tokens=16384,
        system=EXTRACTION_SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": (
                    f"以下の調査テキストから **{product_name}** の構造化レポートを生成してください。\n\n"
                    f"調査実施日: {datetime.now().strftime('%Y-%m-%d')}\n\n"
                    f"━━━ 調査テキスト ━━━\n{research_text}"
                ),
            }
        ],
        output_format=ResearchReport,
    )

    return response.parsed_output


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
    parser.add_argument("--verbose", "-v", action="store_true", help="検索クエリ等の詳細ログを表示")
    parser.add_argument("--json-only", action="store_true", help="JSON のみ stdout に出力")
    parser.add_argument("--no-save", action="store_true", help="ファイルに保存しない")
    args = parser.parse_args()

    client = anthropic.Anthropic()

    print(_divider("═"), file=sys.stderr)
    print(f"  製品・サービス調査エージェント", file=sys.stderr)
    print(f"  対象: {args.product}", file=sys.stderr)
    print(_divider("═"), file=sys.stderr)

    # ── Phase 1: 情報収集 ──
    print("\n[Phase 1] 情報収集 (Web 検索)", file=sys.stderr)
    print(_divider(), file=sys.stderr)
    research_text = gather_information(client, args.product, args.verbose)

    if not research_text.strip():
        print("❌ 情報収集に失敗しました。製品名を確認してください。", file=sys.stderr)
        sys.exit(1)

    # ── Phase 2: 構造化抽出 ──
    print(f"\n[Phase 2] 構造化データ抽出", file=sys.stderr)
    print(_divider(), file=sys.stderr)
    _progress("Claude による構造化抽出中...")
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
