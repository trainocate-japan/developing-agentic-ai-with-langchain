"""agent.py — ハンズオン 6-B (Agent Chat UI 版): langgraph dev 用のエージェント定義

研修コース「Agentic AI 開発実践 - LangChain 版」/ 第6章「Middleware と HITL」

============================================================================
これは「作成済みのコード」です。編集する必要はありません。
`langgraph dev` がこのファイルを読み込み、トップレベル変数 `agent` を
langgraph.json の graphs ("expense") から参照します。
CLI 版 (handson_6B_hitl.py) と同じ承認フローを、ブラウザの Agent Chat UI から
操作するために使います。
============================================================================

【CLI 版との決定的な違い: checkpointer を「コードで渡さない」】
  CLI 版 (handson_6B_hitl.py) は、自分のプロセスだけで動く単体スクリプトなので、
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

【UI に Edit ボタンが出ます】
  transfer_money は allowed_decisions に "edit" を含めているため、
  Agent Chat UI の承認ダイアログに Approve / Edit / Reject の 3 つが並びます。
  CLI 版の観察 4 で Command(resume={"decisions": [{"type": "edit", ...}]}) と
  書いた操作が、そのままボタンと入力欄になっている——これを見比べてください。
"""

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.agents.middleware import HumanInTheLoopMiddleware

# 配布ツール (get_expense / transfer_money) を読み込む。
from expense_tools import get_expense, transfer_money

# .env から環境変数を読み込む。
# (langgraph dev はこの agent.py を import するため、ここで load_dotenv() を呼べば
#  リポジトリのルートの .env が読み込まれ、OpenAI / LangSmith のキーが供給される。
#  そのため langgraph.json に "env" 指定は不要。単体 import 時にも環境変数が揃って安全。)
load_dotenv()

# モデル名は変数に集約 ("provider:model" 形式)。研修実施時に最新へ差し替える。
MODEL = "openai:gpt-5.4"

# SYSTEM_PROMPT は CLI 版 (handson_6B_hitl.py) と同じ文面にそろえてある。
# 「必ず呼び出してください」の指示がないと、モデルが聞き返しで会話を終えてしまい、
# transfer_money が呼ばれず承認ダイアログが出ない。
SYSTEM_PROMPT = (
    "あなたは社内の経費精算を担当するアシスタントです。"
    "社員からの依頼に、丁寧かつ簡潔に答えてください。"
    "経費申請の状況を尋ねられたら get_expense で照会します。"
    "送金の依頼には transfer_money を使います。"
    "送金を依頼されたら、確認の聞き返しや案内文で代替せず、"
    "依頼文に書かれた宛先を to に、金額を amount に渡して transfer_money を必ず呼び出してください。"
    "実行してよいかどうかは人間の承認者が承認フローで判断するので、あなたが遠慮する必要はありません。"
)

# 承認ポリシーは CLI 版と完全に同じ。
#   - transfer_money … approve / edit / reject
#   - get_expense    … 承認不要 (False)
hitl = HumanInTheLoopMiddleware(
    interrupt_on={
        "transfer_money": {"allowed_decisions": ["approve", "edit", "reject"]},
        "get_expense": False,
    },
)

# トップレベル変数 `agent` として公開する。
# langgraph.json の graphs ("expense": "./agent.py:agent") がこの変数を参照する。
#
# 注意: ここでは checkpointer を渡さない (上の docstring の理由)。
#       Agent Chat UI から interrupt の承認ダイアログが正しく出るのは、
#       langgraph dev (Agent Server) が永続化を提供しているおかげ。
agent = create_agent(
    model=MODEL,
    tools=[get_expense, transfer_money],
    system_prompt=SYSTEM_PROMPT,
    middleware=[hitl],
)
