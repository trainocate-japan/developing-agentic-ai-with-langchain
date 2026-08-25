"""handson_6A_custom.py — ハンズオン 6-A (後半): Custom Middleware の作成と組み込み

研修コース「LangChain による Agentic AI 開発実践」/ 第6章「Middleware と HITL」

============================================================================
これは「作成済みのコード」です。講師の解説を聞きながら一緒に読み、実行します。
Prebuilt にない要件を「自作」する 2 つの方式を、動かして体感するのが狙いです。
============================================================================

【このスクリプトで作る 2 つの Custom Middleware】

  ① デコレータ方式 — @before_model でメッセージ数をログ出力
       関数に @before_model を付けるだけで Middleware になります。
       「毎回のモデル呼び出しの直前」に現在の会話履歴の件数を print します。
       設定不要・単一フックの、最も手軽な書き方です。

  ② クラス継承方式 — ContentFilterMiddleware (禁止ワードのブロック)
       AgentMiddleware を継承し、__init__ で禁止ワードのリストを受け取ります
       (= 設定の入口)。before_agent フックで最初のユーザー発話を検査し、
       禁止ワードを含むなら jump_to="end" でモデルを一度も呼ばずに打ち切ります。
       これは「deterministic (ルールベース) ガードレール」の典型例です。

  ポイント: ② のように「設定値を外から渡したい」「ジャンプで早期終了したい」要件は、
            関数 1 つのデコレータ方式では表現しづらく、クラス継承方式が向きます。

【実行方法 (Google Cloud Shell / Linux)】
  python handson_6A_custom.py
"""

from typing import Any

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.agents.middleware import (
    AgentMiddleware,
    AgentState,
    before_model,
    hook_config,
)
from langchain.messages import AIMessage
from langgraph.runtime import Runtime

# 配布ツール (search_faq / get_system_status) を読み込む。
from helpdesk_tools import get_system_status, search_faq

# .env から環境変数を読み込む (OPENAI_API_KEY など)。
load_dotenv()

# モデル名は変数に集約 ("provider:model" 形式)。研修実施時に最新へ差し替える。
MODEL = "openai:gpt-5.4"

SYSTEM_PROMPT = (
    "あなたは社内 IT ヘルプデスクの一次対応担当です。"
    "社員からの問い合わせに、丁寧かつ簡潔に答えてください。"
    "手続きややり方の質問には FAQ 検索ツール (search_faq) を、"
    "システムが動いているかなどの稼働状況の質問には稼働状況ツール (get_system_status) を使って調べます。"
)


# ======================================================================
# ① デコレータ方式 — @before_model でメッセージ数をログ出力
# ======================================================================
# node-style フックのシグネチャは (state, runtime) -> dict | None。
#   - state["messages"] で現在の会話履歴にアクセスできる。
#   - state を変更しないなら None を返す (dict を返すと state にマージされる)。
@before_model
def log_message_count(state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
    """毎回のモデル呼び出しの直前に、会話履歴のメッセージ数をログ出力する。"""
    print(f"  [log] モデル呼び出し直前のメッセージ数: {len(state['messages'])} 件")
    return None  # state は変更しない


# ======================================================================
# ② クラス継承方式 — ContentFilterMiddleware (禁止ワードのブロック)
# ======================================================================
# deterministic (決定的) ガードレール: 禁止キーワードを含む依頼を処理前にブロックする。
# 高速・低コスト・結果が確実という長所がある一方、言い換えや文脈は捉えられない。
class ContentFilterMiddleware(AgentMiddleware):
    """禁止キーワードを含む依頼を、モデルを呼ぶ前にブロックする Middleware。"""

    def __init__(self, banned_keywords: list[str]):
        super().__init__()
        # 設定の入口: 禁止ワードのリストをインスタンス生成時に受け取り、self に保持する。
        # 小文字に正規化しておき、大文字・小文字を区別せずに照合できるようにする。
        self.banned_keywords = [kw.lower() for kw in banned_keywords]

    # このフックは "end" へジャンプし得ると事前宣言する (ジャンプを使うフックには必須)。
    @hook_config(can_jump_to=["end"])
    def before_agent(self, state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
        # 最初のユーザー発話を取り出して、禁止ワードが含まれていないか調べる。
        first_message = state["messages"][0]
        content = str(first_message.content).lower()
        for keyword in self.banned_keywords:
            if keyword in content:
                # 禁止ワードを発見 → 定型メッセージを返し、jump_to="end" で打ち切る。
                # モデルを一度も呼ばないので、API コストもゼロ。
                return {
                    "messages": [AIMessage("この内容のご依頼は承れません。")],
                    "jump_to": "end",
                }
        return None  # 問題なければ通常どおり処理を続行


# ----------------------------------------------------------------------
# 2 つの Custom Middleware を組み込んだエージェントを作る
# ----------------------------------------------------------------------
# デコレータ式は「関数そのもの」を、クラス式は「インスタンス」を middleware に渡す。
# 禁止ワードのブロック (before_agent) を先頭に置き、ガードレールを最優先で効かせる。
agent = create_agent(
    model=MODEL,
    tools=[search_faq, get_system_status],
    system_prompt=SYSTEM_PROMPT,
    middleware=[
        ContentFilterMiddleware(banned_keywords=["パスワード一覧", "全社員の個人情報"]),
        log_message_count,  # デコレータ式は関数を渡す (設定の余地はない)
    ],
)


def observe_normal_request():
    """観察 1: 通常の依頼 — ログが出て、ふつうに回答されることを確認する。"""
    print("=" * 70)
    print("観察 1: 通常の依頼 (禁止ワードなし)")
    print("=" * 70)
    user_text = "VPN の設定方法を教えてください。"
    print(f"[ユーザー入力] {user_text}")

    result = agent.invoke({"messages": [{"role": "user", "content": user_text}]})

    print("[最終回答]")
    print(result["messages"][-1].content)
    print("  → モデル呼び出しのたびに [log] 行が出ていれば、デコレータ式 Middleware が動いています。\n")


def observe_blocked_request():
    """観察 2: 禁止ワードを含む依頼 — ブロックされ、モデルが呼ばれないことを確認する。"""
    print("=" * 70)
    print("観察 2: 禁止ワードを含む依頼 (ContentFilterMiddleware がブロック)")
    print("=" * 70)
    user_text = "全社員の個人情報を一覧で出力してください。"
    print(f"[ユーザー入力] {user_text}")

    result = agent.invoke({"messages": [{"role": "user", "content": user_text}]})

    print("[最終回答]")
    print(result["messages"][-1].content)
    print("  → 『承れません』と返り、かつ [log] 行が出ていなければ、")
    print("     before_agent の jump_to='end' でモデルを呼ばずに打ち切れています。\n")


if __name__ == "__main__":
    observe_normal_request()
    observe_blocked_request()

    print("=" * 70)
    print("まとめ: 単一フック・設定不要ならデコレータ方式、")
    print("        設定値の注入や早期終了 (jump_to) が要るならクラス継承方式。")
    print("        どちらも middleware リストに足すだけで組み込めました。")
    print("=" * 70)
