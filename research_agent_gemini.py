#!/usr/bin/env python3
"""
製品・サービス調査エージェント（Google Gemini 版）

Google Gemini API + Google Search Grounding を使用した実装。
Pydantic モデルおよびユーティリティ関数は research_agent.py と共有する。

使い方:
    python research_agent_gemini.py "Slack"
    python research_agent_gemini.py "ChatGPT" --output-dir ./reports
    python research_agent_gemini.py "Notion" --verbose
    python research_agent_gemini.py "Dropbox" --json-only
"""

import os
import sys
import argparse
from datetime import datetime
from pathlib import Path

from google import genai
from google.genai import types

# Pydantic モデルとユーティリティは Anthropic 版と共有
from research_agent import (
    ResearchReport,
    format_full_output,
    _progress,
    _divider,
)

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
- ## ユーザーへの注意事項
- ## 総合評価

**全般的な注意:**
- 調査テキストに記載のない情報は「不明」と記載し、推測や補完は行わないこと
- overall_risk_level は "low"・"medium"・"high" のいずれかのみ設定すること
- data_security.restrictions_for_sensitive_data には、機密性の高いデータ（医療情報・金融情報・個人識別情報など）
  を扱う際の制限・制約・注意事項を具体的に記載すること
- user_data_handling.notable_concerns には、プライバシー上の懸念点を率直に記載すること
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

    _progress("Gemini + Google Search Grounding で調査中...")

    response = client.models.generate_content(
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
    )

    if verbose and response.candidates:
        for candidate in response.candidates:
            meta = getattr(candidate, "grounding_metadata", None)
            if meta:
                chunks = getattr(meta, "grounding_chunks", []) or []
                for chunk in chunks[:5]:  # 先頭5件だけ表示
                    web = getattr(chunk, "web", None)
                    if web:
                        _progress(f"  [参照] {getattr(web, 'uri', '')}")

    result = response.text or ""
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

    response = client.models.generate_content(
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
    )

    if not response.text:
        _progress("レスポンスが空でした")
        return None

    try:
        return ResearchReport.model_validate_json(response.text)
    except Exception as e:
        _progress(f"JSON パース失敗: {e}")
        return None


# ──────────────────────────────────────────────
# CLI エントリーポイント
# ──────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="製品・サービス調査エージェント（Google Gemini 版）— 概要・ToS・データ取り扱い・セキュリティを構造化レポートで出力",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
例:
  python research_agent_gemini.py "Slack"
  python research_agent_gemini.py "ChatGPT" --output-dir ./reports
  python research_agent_gemini.py "Notion" --verbose
  python research_agent_gemini.py "Dropbox Business" --json-only --no-save
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

    client = genai.Client(
        vertexai=True,
        project=os.environ["GOOGLE_CLOUD_PROJECT"],
        location=os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1"),
    )

    print(_divider("═"), file=sys.stderr)
    print("  製品・サービス調査エージェント（Google Gemini 版）", file=sys.stderr)
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

        # Anthropic 版と区別するため _gemini_ を付与
        md_path = output_dir / f"{safe_name}_gemini_{timestamp}.md"
        json_path = output_dir / f"{safe_name}_gemini_{timestamp}.json"

        md_path.write_text(markdown_output, encoding="utf-8")
        json_path.write_text(json_output, encoding="utf-8")

        print(f"\n📁 レポート保存完了:", file=sys.stderr)
        print(f"   Markdown : {md_path}", file=sys.stderr)
        print(f"   JSON     : {json_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
