"""agent.py 【正解 (solution)】 — Agent Chat UI / langgraph dev 用のエージェント定義

演習 6-B: Agent Chat UI で承認フローを体験 — ヘルプデスク Step 5
研修コース「Agentic AI 開発実践 - LangChain 版」/ 第6章「Middleware と HITL」

============================================================================
このファイルは `langgraph dev` が読み込むエージェント定義です。
トップレベル変数 `agent` を公開し、langgraph.json の graphs から参照させます。
CLI 版 (exercise_6B_hitl.py) と同じ HITL 承認フローを、ブラウザの Agent Chat UI から
操作するために使います。
============================================================================

【CLI 版との決定的な違い: checkpointer を「コードで渡さない」】
  CLI 版 (exercise_6B_hitl.py) は、自分のプロセスだけで動く単体スクリプトなので、
  HITL に必要な checkpointer を create_agent(checkpointer=InMemorySaver()) と
  「自分で」渡していました。

  一方この agent.py は `langgraph dev` (= Agent Server) の上で動きます。
  Agent Server は永続化 (persistence) をプラットフォーム側で提供するため、
  コード内で checkpointer を渡す必要はありません (渡さないのが推奨)。
  サーバーが thread 単位の状態保存・復元を裏で行ってくれるので、
  interrupt の中断・再開もそのまま機能します。

  まとめると:
    - 単体スクリプトで動かす → checkpointer を自分で渡す (CLI 版)
    - langgraph dev で動かす → 渡さない。プラットフォームが提供 (この agent.py)

  公式ドキュメント (LangGraph persistence) より:
    「Agent Server を使う場合、checkpointer や store を手動で実装・設定する必要はない。
      サーバーが永続化インフラを裏で処理する。」
"""

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.agents.middleware import HumanInTheLoopMiddleware, PIIMiddleware

# 配布ツール (読み取り系 + 副作用あり) を読み込む。
from helpdesk_tools import create_ticket, get_system_status, reset_password, search_faq

# .env から環境変数を読み込む。
# (langgraph dev はこの agent.py を import するため、ここで load_dotenv() を呼べば
#  リポジトリのルートの .env が読み込まれ、OpenAI / LangSmith のキーが供給される。
#  そのため langgraph.json に "env" 指定は不要。単体 import 時にも環境変数が揃って安全。)
load_dotenv()

# モデル名は変数に集約 ("provider:model" 形式)。研修実施時に最新へ差し替える。
MODEL = "openai:gpt-5.4"

SYSTEM_PROMPT = (
    "あなたは社内 IT ヘルプデスクの一次対応担当です。"
    "社員からの問い合わせに、丁寧かつ簡潔に答えてください。"
    "やり方の質問には FAQ 検索ツール (search_faq)、稼働状況の質問には get_system_status を使います。"
    "チケットの起票が必要なら create_ticket、パスワードのリセット依頼には reset_password を使います。"
)

# HITL 承認ポリシーは CLI 版と完全に同じ。
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
# langgraph.json の graphs ("helpdesk": "./agent.py:agent") がこの変数を参照する。
#
# 注意: ここでは checkpointer を渡さない (上の docstring の理由)。
#       Agent Chat UI から interrupt の承認ダイアログが正しく出るのは、
#       langgraph dev (Agent Server) が永続化を提供しているおかげ。
agent = create_agent(
    model=MODEL,
    tools=[search_faq, get_system_status, create_ticket, reset_password],
    system_prompt=SYSTEM_PROMPT,
    middleware=[
        PIIMiddleware("email", strategy="redact", apply_to_input=True),
        hitl,
    ],
)
