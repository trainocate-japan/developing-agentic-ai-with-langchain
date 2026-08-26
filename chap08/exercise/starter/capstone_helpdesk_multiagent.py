"""capstone_helpdesk_multiagent.py 【演習 (starter)】 — CLI 版 総合演習

総合演習: ヘルプデスク・マルチエージェント — ヘルプデスク Step 7 (最終)
研修コース「Agentic AI 開発実践 - LangChain 版」/ 第8章「マルチエージェント開発」

============================================================================
これは総合演習 (CLI 版) の「演習用 (starter)」です。
**TODO①〜④** を自分で埋めて、ヘルプデスク・マルチエージェント (v5) を完成させてください。
完成版は solution/ にあります。まずは自力で挑戦しましょう。

  - 2 シナリオの実行・interrupt の resume・トレース検証シートの骨格は「完成状態」で配布しています。
  - あなたが埋めるのは TODO①〜④ の 4 か所 (サブエージェント構成・ラッパー・supervisor・HITL) です。
============================================================================

【この演習で作るもの: ヘルプデスク・マルチエージェント (完成版 v5)】
  FAQ 担当 (faq_agent) と オペレーション担当 (ops_agent) の 2 体のサブエージェントを、
  supervisor が問い合わせに応じて使い分ける Subagents 型に再構成します。

    ユーザー
       │
       ▼
  supervisor (メインエージェント)
   ├── faq ツール  → faq_agent  (search_faq / get_system_status)        … 読み取り系・承認不要
   └── ops ツール  → ops_agent  (create_ticket / reset_password + HITL)  … 副作用あり・要承認

  これまでの全章の要素を総動員する集大成です:
    - Tools (第3章) / Checkpointer (第4章) / Middleware・HITL (第6章) / LangSmith (第4・7章)

【★ checkpointer が「supervisor」だけにある理由 (この演習の肝)】
  ops_agent は supervisor の「ツールの中」で invoke されるサブグラフです。サブには
  checkpointer を渡しません (Subagents は stateless が原則)。サブグラフは既定で
  「継承 (inherited) チェックポインタ」モードで動くため、ops_agent 内で発生した HITL の
  interrupt は、トップレベルの supervisor が持つ checkpointer によって保存・再開されます。
  つまり「supervisor の 1 つの checkpointer が、入れ子の ops_agent の HITL 中断・再開まで
  まとめて面倒を見る」——これが checkpointer を supervisor だけに置く理由です。

【faq_agent はローカルツール (search_faq) を使う / async は使わない】
  faq_agent は本来「ナレッジ担当」で、第5章で作った MCP ナレッジサーバーに差し替えられます
  (発展。README 参照)。ただし MCP は async であり、この集大成に同時に組むと相互作用が
  壊れやすいため、capstone 全体を同期 (invoke / Command(resume)) で実装しています。
"""

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.agents.middleware import HumanInTheLoopMiddleware, SummarizationMiddleware
from langchain.tools import tool
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

# 配布ツール (読み取り系 + 副作用あり) を読み込む。
from helpdesk_tools import create_ticket, get_system_status, reset_password, search_faq

# .env から環境変数を読み込む (リポジトリのルートの .env。5-A で設定済み)。
load_dotenv()

# モデル名は変数に集約 ("provider:model" 形式)。研修実施時に最新へ差し替える。
MODEL = "openai:gpt-5.4"


# ======================================================================
# [TODO④] ops_agent 用の HumanInTheLoopMiddleware を構成する
# ======================================================================
# 副作用ツールを呼ぶ瞬間に実行を止め、人間の承認を待つようにします。
# interrupt_on は「ツール名 → 承認ポリシー」の辞書です。運用要件:
#   - reset_password … approve / reject のみ (高リスクなので引数の編集 edit は許さない)
#   - create_ticket  … approve / edit / reject (起票内容の修正も許す)
# 書き方のヒント (第6章 演習 6-B と同じ API):
#   HumanInTheLoopMiddleware(
#       interrupt_on={
#           "reset_password": {"allowed_decisions": ["approve", "reject"]},
#           "create_ticket": {"allowed_decisions": ["approve", "edit", "reject"]},
#       },
#   )
ops_hitl = None  # ★TODO④: 上記ヒントを参考に HumanInTheLoopMiddleware(...) を構成する


# ======================================================================
# [TODO①] 2 体のサブエージェントを構成する (name 引数 + system_prompt)
# ======================================================================
# create_agent はこれまでと同じ。ポイントは 2 つ:
#   - name=... を付ける … LangSmith トレース上の表示名になる (入れ子の識別に必須)。
#   - system_prompt に「結果は必ず最終メッセージに含める」を書く … supervisor に返るのは
#       「最終メッセージの content だけ」。書かないと「対応しました」だけ返り中身が消える。
#
# --- FAQ 担当 (faq_agent): 読み取り系ツール search_faq / get_system_status を持つ。承認は不要。 ---
#   ヒント: create_agent(model=MODEL, tools=[search_faq, get_system_status],
#                        system_prompt="...回答は必ず最終メッセージに含める...", name="faq_agent")
faq_agent = None  # ★TODO①: faq_agent を create_agent(...) で構成する (name="faq_agent")

# --- オペレーション担当 (ops_agent): create_ticket / reset_password を持つ。HITL で承認を要求。 ---
#   ヒント: create_agent(model=MODEL, tools=[create_ticket, reset_password],
#                        system_prompt="...結果は必ず最終メッセージに含める...",
#                        name="ops_agent", middleware=[ops_hitl])
#   ※ system_prompt には「依頼を聞き返しや代替案内で済ませず、該当ツールを必ず呼び出す」も
#      書いておく。ツールが呼ばれないと interrupt が起きず、承認フローを体験できない。
#   ※ checkpointer はここ (サブ) には渡さない。HITL の interrupt は上位の supervisor が
#      持つ checkpointer によって保存・再開される (冒頭の docstring 参照)。
ops_agent = None  # ★TODO①: ops_agent を create_agent(...) で構成する (name="ops_agent", middleware=[ops_hitl])


# ======================================================================
# [TODO②] 2 体のサブエージェントを @tool でラップする
# ======================================================================
# - name と description は supervisor のルーティング判断材料 (prompting levers)。
#     「何をするか + いつ使うか」を具体的に書く (悪い例: "エージェントを呼ぶ")。
# - 中で サブを invoke し、result["messages"][-1].content (最終メッセージだけ) を返す。
#
# ヒント (faq の例):
#   @tool("faq", description="FAQ・ナレッジ担当に問い合わせる。やり方/手続きの質問や稼働状況の確認に使う。")
#   def call_faq_agent(query: str) -> str:
#       result = faq_agent.invoke({"messages": [{"role": "user", "content": query}]})
#       return result["messages"][-1].content

@tool(
    "faq",
    description="★TODO②: FAQ 担当をいつ・何のために呼ぶかを具体的に書く",
)
def call_faq_agent(query: str) -> str:
    # ★TODO②: faq_agent を invoke し、最終メッセージの content を返す
    raise NotImplementedError("TODO②: faq_agent を invoke して result['messages'][-1].content を返す")


@tool(
    "ops",
    description="★TODO②: オペレーション担当をいつ・何のために呼ぶかを具体的に書く",
)
def call_ops_agent(query: str) -> str:
    # ★TODO②: ops_agent を invoke し、最終メッセージの content を返す
    raise NotImplementedError("TODO②: ops_agent を invoke して result['messages'][-1].content を返す")


# ======================================================================
# [TODO③] supervisor を構成する (2 ラッパーツール + checkpointer + Middleware)
# ======================================================================
SUPERVISOR_PROMPT = (
    "あなたは社内 IT ヘルプデスクの司令塔 (supervisor) です。"
    "社員からの問い合わせを読み、適切な担当に振り分けてください。"
    "・手続き/やり方の質問、稼働状況の確認 → faq ツール (FAQ 担当)"
    "・チケット起票やパスワードリセットなど実行を伴う依頼 → ops ツール (オペレーション担当)"
    "担当からの回答を踏まえ、社員に丁寧かつ簡潔にまとめて返答してください。"
)


def build_supervisor():
    """ヘルプデスク・マルチエージェント (v5) の supervisor を構成して返す。"""
    # ★TODO③: 下記を満たす supervisor を create_agent(...) で構成して return する。
    #   - tools=[call_faq_agent, call_ops_agent]        … 2 つのラッパーツール
    #   - system_prompt=SUPERVISOR_PROMPT
    #   - middleware=[SummarizationMiddleware(model=MODEL, trigger=("tokens", 4000), keep=("messages", 20))]
    #       (長い会話の要約。PIIMiddleware に差し替えても可)
    #   - checkpointer=InMemorySaver()                  … HITL interrupt を伝播・再開する基盤 (この演習の肝)
    #
    # ヒント:
    #   return create_agent(
    #       model=MODEL,
    #       tools=[call_faq_agent, call_ops_agent],
    #       system_prompt=SUPERVISOR_PROMPT,
    #       middleware=[SummarizationMiddleware(model=MODEL, trigger=("tokens", 4000), keep=("messages", 20))],
    #       checkpointer=InMemorySaver(),
    #   )
    raise NotImplementedError("TODO③: supervisor を create_agent(...) で構成して return する")


# ----------------------------------------------------------------------
# 以下は「完成状態」で配布。TODO①〜④ を埋めれば、変更せずそのまま動く。
# ----------------------------------------------------------------------
def print_interrupt(result) -> bool:
    """interrupt の中身 (action_requests) を取り出して表示する。

    version="v2" で invoke すると、戻り値は GraphOutput になり、状態は .value に、
    中断情報は .interrupts に分かれて入る。
    .interrupts は Interrupt のタプルで、value["action_requests"] に「何のツールが・
    どんな引数 (args) で呼ばれようとしているか」が、value["review_configs"] に
    「許された決定タイプ」が入っている。

    中断が起きたら True、起きずに完走していたら False を返す。
    """
    # 承認対象のツールが呼ばれなければ interrupt は起きず、.interrupts は空タプルのまま
    # 完走する。確認せずに [0] を取ると IndexError になるので、原因が読める形で切り分ける。
    if not result.interrupts:
        print("\n[注意] interrupt が発生しませんでした (result.interrupts が空)。")
        print("       ops_agent の承認対象ツール (reset_password / create_ticket) が")
        print("       呼ばれないまま完走しています。supervisor の最終メッセージ:")
        print(f"       {result.value['messages'][-1].content}")
        print("       → supervisor / ops_agent の system_prompt を見直す。")
        return False

    print("\n--- 承認待ち (interrupt) の中身 ---")
    interrupt = result.interrupts[0]  # 今回は 1 件なので先頭を読む
    payload = interrupt.value  # dict: action_requests / review_configs を持つ
    for req in payload["action_requests"]:
        # 引数のキーは "args" (dict)。"arguments" ではない点に注意。
        print(f"  ツール名 : {req['name']}")
        print(f"  引数     : {req['args']}")
    for cfg in payload["review_configs"]:
        print(f"  許可された決定: {cfg['allowed_decisions']}")
    print("-" * 36)
    return True


def scenario_faq(supervisor) -> None:
    """シナリオ 1: 「VPN の設定方法を教えて」→ supervisor が faq_agent に振り分ける。"""
    print("=" * 70)
    print("シナリオ 1: VPN の設定方法を教えて (→ faq_agent ルート / 承認なし)")
    print("=" * 70)
    config = {"configurable": {"thread_id": "capstone-faq"}}
    result = supervisor.invoke(
        {"messages": [{"role": "user", "content": "VPN の設定方法を教えて"}]},
        config=config,
        version="v2",
    )
    print("[supervisor の最終回答]")
    # version="v2" の戻り値は GraphOutput。状態は .value から取り出す。
    print(result.value["messages"][-1].content)
    print("  → faq_agent が search_faq を呼び、VPN 手順が返れば成功です。")
    print("  → このシナリオは副作用がないため interrupt は発生しません。\n")


def scenario_reset_with_approval(supervisor) -> None:
    """シナリオ 2: 「パスワードをリセットして」→ ops_agent + 承認 interrupt → approve で実行。"""
    print("=" * 70)
    print("シナリオ 2: パスワードをリセットして (→ ops_agent ルート / 承認あり)")
    print("=" * 70)
    config = {"configurable": {"thread_id": "capstone-reset-approve"}}

    # 1) 依頼で invoke。supervisor が ops ツールに振り分け、ops_agent が reset_password を
    #    呼ぼうとした瞬間、HITL の interrupt で実行が止まる。version="v2" で .interrupts が付く。
    result = supervisor.invoke(
        {"messages": [{"role": "user", "content": "社員 ID emp-sato のパスワードをリセットしてください"}]},
        config=config,
        version="v2",
    )

    # 2) 止まった内容 (action_requests) を読み解いて表示する。
    #    ops_agent (サブグラフ) 内で起きた interrupt が、supervisor の checkpointer 経由で
    #    ここまで伝播してきている点に注目。中断していなければここで打ち切る。
    if not print_interrupt(result):
        return

    # 3) approve で再開する。decisions は止まっている tool call と同じ順序で並べる。
    #    再開時は中断時と同じ thread_id でなければならない (= 保存地点を特定するため)。
    print("\n→ オペレーターが approve を選択。Command(resume=...) で再開します。")
    final = supervisor.invoke(
        Command(resume={"decisions": [{"type": "approve"}]}),
        config=config,
        version="v2",
    )
    print("\n[supervisor の最終回答]")
    print(final.value["messages"][-1].content)
    print("  → reset_password が実行され、仮パスワードを含む案内が返れば成功です。\n")


# ----------------------------------------------------------------------
# トレース検証シート (実行後に LangSmith で読み取って答え合わせをする)
# ----------------------------------------------------------------------
TRACE_VERIFICATION_SHEET = """\
======================================================================
トレース検証シート (LangSmith で読み取って記入する)
======================================================================
LangSmith はコース全体で有効化済みです。実行後に smith.langchain.com で
プロジェクト (既定 langchain-training-day2) を開き、次を読み取って記入してください。

[1] 入れ子構造 (supervisor → サブエージェント)
    シナリオ 1 のトレースで、supervisor の 1 ターンの中に faq ツールがあり、
    その内側に faq_agent (name で識別) の ReAct ループが入れ子で見えるか?  → (はい / いいえ)

[2] name による識別
    入れ子で表示されているサブの名前は?
      シナリオ 1: __________________ (期待: faq_agent)
      シナリオ 2: __________________ (期待: ops_agent)

[3] モデル呼び出し回数 (Subagents は集中制御の対価で 1 手多い)
    シナリオ 1 (faq ルート) のモデル呼び出し回数: ______ 回
      (目安: ① faq 使用を決定 → ②③ サブ内で検索・要約 → ④ 最終応答 = 4 回)

[4] HITL interrupt の伝播
    シナリオ 2 で、ops_agent (サブグラフ) 内の reset_password に対する interrupt が、
    supervisor の checkpointer 経由で停止・再開できたか?  → (はい / いいえ)
    approve 後に reset_password が実際に実行されたことをトレースで確認できたか? → (はい / いいえ)

[5] Subagents の特性 (stateless) との接続
    同じ依頼を別 thread_id でもう一度実行すると、サブの呼び出し回数は変わるか?
    変わらない理由を「stateless / コンテキスト分離」の語で 1 行で説明:
      ____________________________________________________________________
======================================================================
"""


if __name__ == "__main__":
    supervisor = build_supervisor()  # ← TODO③ を埋めると動く

    # 2 シナリオを順に実行する。
    scenario_faq(supervisor)
    scenario_reset_with_approval(supervisor)

    # トレース検証シートを表示する (LangSmith を開いて記入する)。
    print(TRACE_VERIFICATION_SHEET)

    print("=" * 70)
    print("まとめ: supervisor が faq / ops の 2 サブを呼び分ける Subagents 型を、")
    print("        Tools・Checkpointer・Middleware・HITL・LangSmith を総動員して実装した。")
    print("        ops_agent 内の HITL interrupt は、supervisor の checkpointer が伝播・再開する。")
    print("        次は agent.py + langgraph.json で、同じ supervisor を langgraph dev で起動し、")
    print("        Agent Chat UI (Web Preview) から 2 シナリオを操作する = 本コースの最終成果物。")
    print("=" * 70)
