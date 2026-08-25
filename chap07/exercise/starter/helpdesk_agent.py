"""helpdesk_agent.py — 演習 7-B の評価対象: ヘルプデスクエージェント v4 (配布・完成版)

演習 7-B: ヘルプデスクの回帰評価 — ヘルプデスク Step 6
研修コース「LangChain による Agentic AI 開発実践」/ 第7章「エージェントの評価」

============================================================================
このファイルは「配布物」です。演習中に編集する必要はありません (starter / solution 共通)。
第6章で完成させたヘルプデスクエージェント v4 を引き継ぎ、2 つの役割を提供します。

  1. トップレベル変数 `agent` — v4 完成品 (第6章の agent.py と同じ構成)
       `langgraph dev` が langgraph.json 経由で読み込みます。ステップ 0 の
       「Agent Chat UI から 1 ケース手動確認」で使います。

  2. 関数 `build_eval_agent(prompt_version)` — 回帰評価用の Target
       client.evaluate の Target 関数から呼びます。--prompt base / v2 で
       システムプロンプトを切り替え、修正前後の Experiment を作り比べます。
============================================================================

【評価用エージェントはなぜ「読み取り系 2 ツール・Middleware なし」なのか】
  v4 には HITL (承認フロー) が入っており、副作用ツール (create_ticket /
  reset_password) は人間が承認するまで interrupt で停止します。自動一括評価の
  途中で人間の承認を待つことはできないため、オフライン評価では
  「読み取り系ツール (search_faq / get_system_status) で完結する一次対応の品質」を
  評価対象に絞ります。承認フロー自体の確認は、第6章のとおり Agent Chat UI で
  行います (評価を複雑にする要素を外して、測りたいものだけを測る、という設計です)。

【「プロンプト修正パッチ (v2)」とは】
  EVAL_PROMPT_BASE (修正前) に対する EVAL_PROMPT_V2 (修正後) は、次の 2 点を
  変更した「現実によくある改善パッチ」です。
    (1) VPN の問い合わせでは、FAQ に加えて現在の稼働状況も確認して案内する (改善)
    (2) 回答を要点だけに絞って短くする (簡潔化)
  ただし (2) の副作用として、これまで応答に含まれていた大事な補足 (例: パスワードの
  ロック解除は情報システム部での本人確認が必要) が落ちることがあります。
  「一部のケースを改善する修正が、別のケースを僅かに劣化させ得る」——この現象を
  Experiment の比較ビューで捕まえるのが、演習 7-B のゴールです。
"""

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.agents.middleware import HumanInTheLoopMiddleware, PIIMiddleware

# 配布ツール (読み取り系 + 副作用あり) を読み込む。
from helpdesk_tools import create_ticket, get_system_status, reset_password, search_faq

# .env から環境変数を読み込む。
# (langgraph dev はこの helpdesk_agent.py を import するため、ここで load_dotenv() を
#  呼べばリポジトリのルートの .env が読み込まれ、OpenAI / LangSmith のキーが供給される)
load_dotenv()

# モデル名は変数に集約 ("provider:model" 形式)。研修実施時に最新へ差し替える。
MODEL = "openai:gpt-5.4"

# ----------------------------------------------------------------------
# 役割 1: v4 完成品 (langgraph dev + Agent Chat UI 用。第6章から引き継ぎ)
# ----------------------------------------------------------------------

SYSTEM_PROMPT = (
    "あなたは社内 IT ヘルプデスクの一次対応担当です。"
    "社員からの問い合わせに、丁寧かつ簡潔に答えてください。"
    "やり方の質問には FAQ 検索ツール (search_faq)、稼働状況の質問には get_system_status を使います。"
    "チケットの起票が必要なら create_ticket、パスワードのリセット依頼には reset_password を使います。"
)

# HITL 承認ポリシーは第6章と完全に同じ。
#   - create_ticket  … approve / edit / reject
#   - reset_password … approve / reject のみ
#   - get_system_status … 承認不要 (False)
hitl = HumanInTheLoopMiddleware(
    interrupt_on={
        "create_ticket": {"allowed_decisions": ["approve", "edit", "reject"]},
        "reset_password": {"allowed_decisions": ["approve", "reject"]},
        "get_system_status": False,
    },
)

# トップレベル変数 `agent` として公開する。
# langgraph.json の graphs ("helpdesk": "./helpdesk_agent.py:agent") がこの変数を参照する。
# checkpointer を渡さない理由は第6章の演習どおり (Agent Server が永続化を提供する)。
agent = create_agent(
    model=MODEL,
    tools=[search_faq, get_system_status, create_ticket, reset_password],
    system_prompt=SYSTEM_PROMPT,
    middleware=[
        PIIMiddleware("email", strategy="redact", apply_to_input=True),
        hitl,
    ],
)

# ----------------------------------------------------------------------
# 役割 2: 回帰評価用エージェント (client.evaluate の Target 用)
# ----------------------------------------------------------------------

# 修正前 (base) のシステムプロンプト。
# v4 のプロンプトから、評価対象外の副作用ツールに関する文を除いたものです。
EVAL_PROMPT_BASE = (
    "あなたは社内 IT ヘルプデスクの一次対応担当です。"
    "社員からの問い合わせに、丁寧かつ簡潔に答えてください。"
    "やり方の質問には FAQ 検索ツール (search_faq)、稼働状況の質問には get_system_status を使います。"
)

# 修正後 (v2) のシステムプロンプト =「プロンプト修正パッチ」適用後。
# 変更点はファイル冒頭の docstring 参照。(1) の VPN 対応強化は改善、
# (2) の「2 文以内・補足省略」は別ケースを僅かに劣化させ得ます。
EVAL_PROMPT_V2 = (
    "あなたは社内 IT ヘルプデスクの一次対応担当です。"
    "社員からの問い合わせには、要点だけを 2 文以内で簡潔に答えてください。"
    "細かい補足や注意書きは省略して構いません。"
    "やり方の質問には FAQ 検索ツール (search_faq)、稼働状況の質問には get_system_status を使います。"
    "VPN に関する問い合わせでは、search_faq の結果に加えて、"
    "必ず get_system_status で VPN の稼働状況も確認し、あわせて案内してください。"
)

# プロンプトのバージョン名 → プロンプト本文の対応表。
EVAL_PROMPTS = {
    "base": EVAL_PROMPT_BASE,
    "v2": EVAL_PROMPT_V2,
}


def build_eval_agent(prompt_version: str = "base"):
    """回帰評価用のヘルプデスクエージェントを構成して返す。

    Args:
        prompt_version: システムプロンプトのバージョン。
            "base" (修正前) または "v2" (プロンプト修正パッチ適用後)。

    Returns:
        create_agent が返すエージェント (CompiledStateGraph)。
        読み取り系 2 ツール (search_faq / get_system_status) のみ・Middleware なしの
        構成にする理由は、ファイル冒頭の docstring 参照。
    """
    if prompt_version not in EVAL_PROMPTS:
        raise ValueError(
            f"prompt_version は {list(EVAL_PROMPTS)} のいずれかを指定してください: "
            f"{prompt_version!r}"
        )
    return create_agent(
        model=MODEL,
        tools=[search_faq, get_system_status],
        system_prompt=EVAL_PROMPTS[prompt_version],
    )
