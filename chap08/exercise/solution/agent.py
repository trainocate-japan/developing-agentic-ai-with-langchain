"""agent.py 【正解 (solution)】 — Agent Chat UI / langgraph dev 用の supervisor 定義

総合演習: ヘルプデスク・マルチエージェント — ヘルプデスク Step 7 (最終)
研修コース「Agentic AI 開発実践 - LangChain 版」/ 第8章「マルチエージェント開発」

============================================================================
このファイルは `langgraph dev` が読み込む supervisor 定義です。
トップレベル変数 `supervisor` を公開し、langgraph.json の graphs から参照させます。
CLI 版 (capstone_helpdesk_multiagent.py) と同じ Subagents 構成 (faq_agent / ops_agent を
supervisor が呼び分ける) を、ブラウザの Agent Chat UI から操作するために使います。

これが本コースの最終成果物「Web UI から操作できるヘルプデスク・マルチエージェント」です。
============================================================================

【CLI 版との決定的な違い: supervisor に checkpointer を「渡さない」】
  CLI 版は単体スクリプトなので、HITL に必要な checkpointer を
  create_agent(checkpointer=InMemorySaver()) と「自分で」supervisor に渡していました。

  一方この agent.py は `langgraph dev` (= Agent Server) の上で動きます。
  Agent Server は永続化 (persistence) をプラットフォーム側で提供するため、コード内で
  checkpointer を渡す必要はありません (渡さないのが推奨)。サーバーが thread 単位の
  状態保存・復元を裏で行うので、ops_agent 内の HITL interrupt の中断・再開もそのまま機能し、
  Agent Chat UI に承認ダイアログが表示されます。

  まとめると (第6章と同じ扱い):
    - 単体スクリプトで動かす → checkpointer を自分で渡す (CLI 版)
    - langgraph dev で動かす → 渡さない。プラットフォームが提供 (この agent.py)

【faq_agent はローカルツール (search_faq) を使う / async は使わない】
  faq_agent は本来「ナレッジ担当」で、第5章で作った MCP ナレッジサーバーに差し替えられます
  (発展)。ただし MCP は async であり、HITL + Agent Chat UI を統合するこの集大成に同時に
  組むと相互作用が壊れやすいため、capstone 全体を同期で実装しています (詳細は README)。
"""

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.agents.middleware import HumanInTheLoopMiddleware, SummarizationMiddleware
from langchain.tools import tool

# 配布ツール (読み取り系 + 副作用あり) を読み込む。
from helpdesk_tools import create_ticket, get_system_status, reset_password, search_faq

# .env から環境変数を読み込む。
# (langgraph dev はこの agent.py を import するため、ここで load_dotenv() を呼べば
#  リポジトリのルートの .env が読み込まれ、OpenAI / LangSmith のキーが供給される。
#  そのため langgraph.json に "env" 指定は不要。単体 import 時にも環境変数が揃って安全。)
load_dotenv()

# モデル名は変数に集約 ("provider:model" 形式)。研修実施時に最新へ差し替える。
MODEL = "openai:gpt-5.4"


# ----------------------------------------------------------------------
# サブエージェント (CLI 版と同じ構成。name 引数 + 「結果は最終メッセージに」)
# ----------------------------------------------------------------------
faq_agent = create_agent(
    model=MODEL,
    tools=[search_faq, get_system_status],
    system_prompt=(
        "あなたは社内 IT ヘルプデスクの FAQ・ナレッジ担当です。"
        "社内の手続きややり方の質問には search_faq、システムの稼働状況の質問には "
        "get_system_status を使って調べ、分かりやすく回答してください。"
        "回答は必ずあなたの最終メッセージに含めてください。"
    ),
    name="faq_agent",
)

# ops_agent には HITL を付ける (reset_password / create_ticket は要承認)。
# checkpointer はサブには渡さない。HITL の中断・再開は langgraph dev (Agent Server) が
# プラットフォームとして提供する永続化に乗る。
ops_hitl = HumanInTheLoopMiddleware(
    interrupt_on={
        "reset_password": {"allowed_decisions": ["approve", "reject"]},
        "create_ticket": {"allowed_decisions": ["approve", "edit", "reject"]},
    },
)

ops_agent = create_agent(
    model=MODEL,
    tools=[create_ticket, reset_password],
    system_prompt=(
        "あなたは社内 IT ヘルプデスクのオペレーション担当です。"
        "チケット起票には create_ticket、パスワードリセット依頼には reset_password を使います。"
        "これらは副作用のある操作で、人間のオペレーターの承認を得てから実行されます。"
        "実行結果は必ずあなたの最終メッセージに含めてください。"
    ),
    name="ops_agent",
    middleware=[ops_hitl],
)


# ----------------------------------------------------------------------
# サブエージェントを @tool でラップする (description は supervisor のルーティング判断材料)
# ----------------------------------------------------------------------
@tool(
    "faq",
    description=(
        "FAQ・ナレッジ担当に問い合わせる。VPN・パスワード・経費精算・メールなどの"
        "「やり方・手続き」の質問や、社内システムの稼働状況の確認に使う。"
        "情報を調べて答えるだけで、副作用のある操作はしない。"
    ),
)
def call_faq_agent(query: str) -> str:
    result = faq_agent.invoke({"messages": [{"role": "user", "content": query}]})
    return result["messages"][-1].content


@tool(
    "ops",
    description=(
        "オペレーション担当に作業を依頼する。サポートチケットの起票や"
        "パスワードのリセットなど、副作用のある実行操作が必要なときに使う"
        "(これらの操作は人間のオペレーターの承認を経て実行される)。"
    ),
)
def call_ops_agent(query: str) -> str:
    result = ops_agent.invoke({"messages": [{"role": "user", "content": query}]})
    return result["messages"][-1].content


# ----------------------------------------------------------------------
# supervisor を公開する (langgraph.json の graphs がこの変数を参照する)
# ----------------------------------------------------------------------
# 注意: ここでは checkpointer を渡さない (上の docstring の理由)。
#       Agent Chat UI から HITL の承認ダイアログが正しく出るのは、
#       langgraph dev (Agent Server) が永続化を提供しているおかげ。
supervisor = create_agent(
    model=MODEL,
    tools=[call_faq_agent, call_ops_agent],
    system_prompt=(
        "あなたは社内 IT ヘルプデスクの司令塔 (supervisor) です。"
        "社員からの問い合わせを読み、適切な担当に振り分けてください。"
        "・手続き/やり方の質問、稼働状況の確認 → faq ツール (FAQ 担当)"
        "・チケット起票やパスワードリセットなど実行を伴う依頼 → ops ツール (オペレーション担当)"
        "担当からの回答を踏まえ、社員に丁寧かつ簡潔にまとめて返答してください。"
    ),
    middleware=[
        SummarizationMiddleware(
            model=MODEL,
            trigger=("tokens", 4000),
            keep=("messages", 20),
        ),
    ],
)
