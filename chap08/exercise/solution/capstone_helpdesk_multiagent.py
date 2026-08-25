"""capstone_helpdesk_multiagent.py 【正解 (solution)】 — CLI 版 総合演習

総合演習: ヘルプデスク・マルチエージェント — ヘルプデスク Step 7 (最終)
研修コース「Agentic AI 開発実践 - LangChain 版」/ 第8章「マルチエージェント開発」

============================================================================
これは総合演習 (CLI 版) の「正解 (solution)」です。
4 つの TODO がすべて埋まった完成版です。
まずは starter/ で自力で挑戦し、詰まったとき・答え合わせのときに参照してください。
============================================================================

【この演習で作るもの: ヘルプデスク・マルチエージェント (完成版 v5)】
  ヘルプデスクの利用が全社に広がり、FAQ 回答とオペレーション実行 (チケット・リセット) で
  ツールが増え続けて応答品質が低下してきました。そこで 2 体のサブエージェントに分業させ、
  supervisor が問い合わせに応じて使い分ける Subagents 型に再構成します。

    ユーザー
       │
       ▼
  supervisor (メインエージェント)
   ├── faq ツール  → faq_agent  (search_faq / get_system_status)        … 読み取り系・承認不要
   └── ops ツール  → ops_agent  (create_ticket / reset_password + HITL)  … 副作用あり・要承認

  これまでの全章の要素を総動員する集大成です:
    - Tools (第3章)        … search_faq / get_system_status / create_ticket / reset_password
    - Checkpointer (第4章) … supervisor に InMemorySaver。HITL の interrupt を再開する基盤
    - Middleware (第6章)   … supervisor に Summarization、ops_agent に HITL
    - HITL (第6章)         … reset_password / create_ticket は人間の承認が必要
    - LangSmith (第4・7章) … supervisor → サブエージェントの入れ子をトレースで読む

【★ checkpointer が「supervisor」だけにある理由 (この演習の肝)】
  HITL の interrupt は LangGraph の永続化層 (checkpointer) に依存します。reset_password の
  承認待ちで実行を止め、後で Command(resume=...) で再開するには、止まった時点の state が
  保存されている必要があります。

  ここで重要なのは、ops_agent は supervisor の「ツールの中」で invoke される
  サブグラフ (subgraph) だという点です。サブエージェントには checkpointer を渡しません
  (Subagents は stateless が原則)。サブグラフは既定で「継承 (inherited) チェックポインタ」
  モードで動くため、ops_agent 内で発生した interrupt は、**トップレベルの supervisor が
  持つ checkpointer によって保存・再開**されます。
  つまり「supervisor の 1 つの checkpointer が、入れ子の ops_agent の HITL 中断・再開まで
  まとめて面倒を見る」——これが、checkpointer を supervisor だけに置く理由です。

【faq_agent がローカルツールである理由 (設計判断)】
  faq_agent は本来「ナレッジ担当」で、第5章で作った MCP ナレッジサーバーに対応します。
  しかし MCP は async であり、HITL + Checkpointer + Agent Chat UI を統合するこの集大成に
  同時に組むと相互作用が壊れやすくなります。そこで capstone 全体を同期で実装し、
  faq_agent はローカルの search_faq を使います (詳細は helpdesk_tools.py と README)。

【async は使いません】
  すべてのツールはローカル @tool (同期) です。HITL の中断・再開は同期の
  invoke + Command(resume) で完結するため、async は使いません。
"""

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.agents.middleware import HumanInTheLoopMiddleware, SummarizationMiddleware
from langchain.tools import tool
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

# 配布ツール (読み取り系 + 副作用あり) を読み込む。
from helpdesk_tools import create_ticket, get_system_status, reset_password, search_faq

# .env から環境変数を読み込む (OPENAI_API_KEY / LANGSMITH_* など)。
# load_dotenv() は実行位置から上位ディレクトリを遡るため、リポジトリのルートに
# 置いた共通 .env を読み込む (5-A で設定済み)。
load_dotenv()

# モデル名は変数に集約 ("provider:model" 形式)。研修実施時に最新へ差し替える。
MODEL = "openai:gpt-5.4"


# ======================================================================
# [解答①] 2 体のサブエージェントを構成する (name 引数 + system_prompt)
# ======================================================================
# ポイントは 2 つ:
#   - name=... … LangSmith トレース上の表示名になる。入れ子のどれがどのサブか識別する生命線。
#   - system_prompt の「結果は必ず最終メッセージに含める」… supervisor に返るのは
#       「最終メッセージの content だけ」。これを書かないと「対応しました」とだけ返り、
#       肝心の中身が消える典型的な失敗 (空の報告) が起きる。

# --- FAQ 担当 (faq_agent): 読み取り系ツールだけを持つ。承認は不要。 ---
faq_agent = create_agent(
    model=MODEL,
    tools=[search_faq, get_system_status],
    system_prompt=(
        "あなたは社内 IT ヘルプデスクの FAQ・ナレッジ担当です。"
        "社内の手続きややり方の質問には search_faq、システムの稼働状況の質問には "
        "get_system_status を使って調べ、分かりやすく回答してください。"
        "回答は必ずあなたの最終メッセージに含めてください "
        "(あなたを呼び出した supervisor は、あなたの最終メッセージしか見ません)。"
    ),
    name="faq_agent",  # ← トレースでの識別名
)

# --- オペレーション担当 (ops_agent): 副作用ツールを持ち、HITL で承認を要求する。 ---
#   [解答④] ops_agent に HumanInTheLoopMiddleware を構成する。
#     - reset_password … approve / reject のみ (高リスクなので引数の編集は許さない)
#     - create_ticket  … approve / edit / reject (起票内容の修正も許す)
#   interrupt_on に書いたツールだけが承認の対象になる。
#   ※ checkpointer はここ (サブ) には渡さない。HITL の interrupt は、上位の
#      supervisor が持つ checkpointer によって保存・再開される (上の docstring 参照)。
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
        "実行結果 (チケット番号や仮パスワードの案内など) は必ずあなたの最終メッセージに"
        "含めてください (supervisor はあなたの最終メッセージしか見ません)。"
    ),
    name="ops_agent",  # ← トレースでの識別名
    middleware=[ops_hitl],
)


# ======================================================================
# [解答②] 2 体のサブエージェントを @tool でラップする
# ======================================================================
# - name と description は supervisor のルーティング判断材料 (prompting levers)。
#     「何をするか + いつ使うか」を具体的に書く (悪い例: "エージェントを呼ぶ")。
# - result["messages"][-1].content … サブの最終メッセージだけを取り出して返す。
#     これが「メインに返るのは最終メッセージだけ」の実装上の正体。

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


# ======================================================================
# [解答③] supervisor を構成する (2 ラッパーツール + checkpointer + Middleware)
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
    return create_agent(
        model=MODEL,
        tools=[call_faq_agent, call_ops_agent],
        system_prompt=SUPERVISOR_PROMPT,
        middleware=[
            # 長い会話でコンテキストが膨らんだら履歴を要約に置き換える (第6章 Prebuilt)。
            # supervisor は会話メモリを一元管理する立場なので、ここに置くのが自然。
            # (PIIMiddleware に差し替えても可。要件に応じて選ぶ。)
            SummarizationMiddleware(
                model=MODEL,
                trigger=("tokens", 4000),
                keep=("messages", 20),
            ),
        ],
        # トップレベルの checkpointer。これが ops_agent 内の HITL interrupt を
        # 保存・再開する基盤になる (上の docstring「checkpointer が supervisor だけにある理由」)。
        # 学習用は InMemorySaver で OK。本番は PostgresSaver 等の永続バックエンドにする。
        checkpointer=InMemorySaver(),
    )


def print_interrupt(result) -> None:
    """interrupt の中身 (action_requests) を取り出して表示する。

    version="v2" で invoke すると、戻り値は .interrupts 属性を持つ。
    その中の value["action_requests"] に「何のツールが・どんな引数で呼ばれようと
    しているか」が、value["review_configs"] に「許された決定タイプ」が入っている。
    """
    print("\n--- 承認待ち (interrupt) の中身 ---")
    interrupt = result.interrupts[0]  # 今回は 1 件なので先頭を読む
    payload = interrupt.value  # dict: action_requests / review_configs を持つ
    for req in payload["action_requests"]:
        print(f"  ツール名 : {req['name']}")
        print(f"  引数     : {req['arguments']}")
    for cfg in payload["review_configs"]:
        print(f"  許可された決定: {cfg['allowed_decisions']}")
    print("-" * 36)


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
    print(result["messages"][-1].content)
    print("  → faq_agent が search_faq を呼び、VPN 手順が返れば成功です。")
    print("  → このシナリオは副作用がないため interrupt は発生しません。\n")


def scenario_reset_with_approval(supervisor) -> None:
    """シナリオ 2: 「パスワードをリセットして」→ ops_agent + 承認 interrupt → approve で実行。"""
    print("=" * 70)
    print("シナリオ 2: パスワードをリセットして (→ ops_agent ルート / 承認あり)")
    print("=" * 70)
    config = {"configurable": {"thread_id": "capstone-reset-approve"}}

    # 1) 依頼で invoke。supervisor が ops ツールに振り分け、ops_agent が reset_password を
    #    呼ぼうとした瞬間、HITL の interrupt で実行が止まる。
    #    version="v2" を付けることで、戻り値が .interrupts 属性を持つ形式になる。
    result = supervisor.invoke(
        {"messages": [{"role": "user", "content": "私 (emp-sato) のパスワードをリセットして"}]},
        config=config,
        version="v2",
    )

    # 2) 止まった内容 (action_requests) を読み解いて表示する。
    #    ops_agent (サブグラフ) 内で起きた interrupt が、supervisor の checkpointer 経由で
    #    ここまで伝播してきている点に注目。
    print_interrupt(result)

    # 3) approve で再開する。decisions は止まっている tool call と同じ順序で並べる。
    #    今回は 1 件なので 1 要素。type="approve" で「そのまま実行」。
    #    再開時は中断時と同じ thread_id でなければならない (= 保存地点を特定するため)。
    print("\n→ オペレーターが approve を選択。Command(resume=...) で再開します。")
    final = supervisor.invoke(
        Command(resume={"decisions": [{"type": "approve"}]}),
        config=config,
        version="v2",
    )
    print("\n[supervisor の最終回答]")
    print(final["messages"][-1].content)
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
    supervisor = build_supervisor()

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


# ======================================================================
# (発展) Single dispatch tool 方式 — レジストリ + task ツール
# ======================================================================
# 上の実装は「サブ 1 体につきツール 1 つ」(tool per agent) 方式です。少数のサブを
# 丁寧に運用するのに向きます。一方、サブが多数あったり複数チームで分散開発する場合は、
# 単一の task(agent_name, description) ツールにレジストリを組み合わせる方式が有効です。
# 新しいサブの追加が「レジストリへの登録」だけで済むため、組織的なスケールに強くなります。
#
# 下は、上の faq_agent / ops_agent をそのまま使う単一ディスパッチ版の例です。
# supervisor には「どんなサブがいるか」を別途教える必要があり、ここでは最も簡単な
# 「system prompt への列挙」を使っています (< 10 体の静的なリスト向け)。

# サブエージェントのレジストリ (各チームが独立に開発したエージェントを名前で登録)。
SUBAGENTS = {
    "faq": faq_agent,
    "ops": ops_agent,
}


@tool
def task(agent_name: str, description: str) -> str:
    """指定したサブエージェントにタスクを依頼する。

    利用可能なエージェント:
    - faq: FAQ・ナレッジ担当 (手続き/やり方の質問・稼働状況の確認)
    - ops: オペレーション担当 (チケット起票・パスワードリセットなどの実行操作)
    """
    agent = SUBAGENTS[agent_name]
    result = agent.invoke({"messages": [{"role": "user", "content": description}]})
    return result["messages"][-1].content


def build_supervisor_single_dispatch():
    """(発展) 単一ディスパッチツール (task) でサブを呼ぶ supervisor を構成して返す。"""
    return create_agent(
        model=MODEL,
        tools=[task],
        system_prompt=(
            SUPERVISOR_PROMPT
            + " サブへの依頼は task ツールを使い、agent_name に 'faq' または 'ops' を指定します。"
        ),
        middleware=[
            SummarizationMiddleware(model=MODEL, trigger=("tokens", 4000), keep=("messages", 20)),
        ],
        checkpointer=InMemorySaver(),
    )
