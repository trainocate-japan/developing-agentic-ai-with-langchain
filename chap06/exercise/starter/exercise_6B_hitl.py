"""exercise_6B_hitl.py 【演習 (starter)】 — CLI 版 HITL 承認フロー

演習 6-B: 要承認オペレーションの実装 — ヘルプデスク Step 5
研修コース「LangChain による Agentic AI 開発実践」/ 第6章「Middleware と HITL」

============================================================================
これは演習 6-B (CLI 版) の「演習用 (starter)」です。
ファイル内の「TODO①」〜「TODO④」を、あなた自身で埋めて完成させてください。
完成版が見たくなったら solution/ を参照できますが、まずは自力で挑戦しましょう。
============================================================================

【この演習で作るもの: ヘルプデスクエージェント v4 (CLI)】
  ヘルプデスクに「チケット起票 (create_ticket)」「パスワードリセット (reset_password)」の
  実行機能を追加します。どちらも副作用がある (やり直しが効かない) ため、
  人間のオペレーターが承認するまで実行してはならない、という運用要件があります。

  これを実現するのが HumanInTheLoopMiddleware です。モデルが副作用ツールを呼ぼうとした
  瞬間に実行を「中断 (interrupt)」し、その時点の状態を checkpointer に保存します。
  人間が承認 (approve) / 拒否 (reject) を決めたら、同じ thread_id で Command(resume=...) を
  invoke すると、保存された地点の続きから再開します。

【あなたが埋めるのは 4 か所 (TODO①〜④)】
  - TODO①: HumanInTheLoopMiddleware の interrupt_on (ツールごとの承認ポリシー)
  - TODO②: checkpointer (InMemorySaver) の設定
  - TODO③: interrupt の中身 (action_requests) の取得・表示
  - TODO④: approve / reject の Command(resume=...) による再開

【async は使いません】
  この演習のツールはローカル @tool (同期) です。HITL の中断・再開は
  同期の invoke + Command(resume) で完結するため、async は使いません。
"""

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.agents.middleware import HumanInTheLoopMiddleware, PIIMiddleware
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

# 配布ツール (読み取り系 + 副作用あり) を読み込む。
from helpdesk_tools import create_ticket, get_system_status, reset_password, search_faq

# .env から環境変数を読み込む (OPENAI_API_KEY など)。
load_dotenv()

# モデル名は変数に集約 ("provider:model" 形式)。研修実施時に最新へ差し替える。
MODEL = "openai:gpt-5.4"

SYSTEM_PROMPT = (
    "あなたは社内 IT ヘルプデスクの一次対応担当です。"
    "社員からの問い合わせに、丁寧かつ簡潔に答えてください。"
    "やり方の質問には FAQ 検索ツール (search_faq)、稼働状況の質問には get_system_status を使います。"
    "チケットの起票が必要なら create_ticket、パスワードのリセット依頼には reset_password を使います。"
)


def build_agent():
    """HITL 承認フロー付きのヘルプデスクエージェント (v4) を構成して返す。"""

    # ==================================================================
    # TODO①: HumanInTheLoopMiddleware の interrupt_on を設計する
    # ==================================================================
    # interrupt_on は「ツール名 → 承認ポリシー」の辞書です。
    # ツール名ごとにポリシーを書きます。承認不要のツールは False を指定します。
    #   - True                          : 必ず停止し、全決定タイプを許可
    #   - {"allowed_decisions": [...]}  : 停止し、許可する決定タイプを限定
    #   - False                         : 承認不要。停止せず素通し
    #
    # 運用要件に合わせて、次のように書き分けてください:
    #   - create_ticket  … approve / edit / reject を許可
    #   - reset_password … approve / reject のみ許可 (高リスクなので編集は許さない)
    #   - get_system_status … 読み取り系なので承認不要 (False)
    # (search_faq は interrupt_on に書かなければ、そもそも停止対象になりません)
    hitl = HumanInTheLoopMiddleware(
        interrupt_on={
            # TODO①: ここに create_ticket / reset_password / get_system_status の
            #         承認ポリシーを書く
        },
    )

    # PII 保護 (ハンズオン 6-A で学んだ Prebuilt) も重ねておきます。
    # ガードレールは先頭に置く定石に従い、PII → HITL の順に並べます。
    agent = create_agent(
        model=MODEL,
        tools=[search_faq, get_system_status, create_ticket, reset_password],
        system_prompt=SYSTEM_PROMPT,
        middleware=[
            PIIMiddleware("email", strategy="redact", apply_to_input=True),
            hitl,
        ],
        # ==============================================================
        # TODO②: checkpointer を設定する (HITL に必須)
        # ==============================================================
        # interrupt で停止した時点の state は checkpointer に保存されます。
        # これを忘れると、中断はできても「再開する場所」を保存できずエラーになります
        # (第4章の checkpointer の復習)。学習用は InMemorySaver で十分です。
        # ヒント: create_agent の引数に checkpointer=InMemorySaver() を足します。
        # TODO②: ここに checkpointer=... を追加する
    )
    return agent


def print_interrupt(result):
    """TODO③: interrupt の中身 (action_requests) を取り出して表示する。

    version="v2" で invoke すると、戻り値は .interrupts 属性を持ちます。
    その中の value["action_requests"] に「何のツールが・どんな引数で呼ばれようと
    しているか」が、value["review_configs"] に「許された決定タイプ」が入っています。
    """
    print("\n--- 承認待ち (interrupt) の中身 ---")
    # ==================================================================
    # TODO③: interrupt の中身を取り出して表示する
    # ==================================================================
    # ヒント:
    #   1) result.interrupts はタプル。先頭の Interrupt を取り出す (result.interrupts[0])。
    #   2) その .value (dict) に "action_requests" と "review_configs" が入っている。
    #   3) action_requests の各要素から "name" と "arguments" を、
    #      review_configs の各要素から "allowed_decisions" を取り出して print する。
    #
    # 下の 2 行 (interrupt と payload) を完成させ、ループで中身を表示してください。
    interrupt = ___  # TODO③: result.interrupts の先頭を取り出す
    payload = ___    # TODO③: interrupt の .value (action_requests / review_configs を持つ dict)

    for req in payload["action_requests"]:
        print(f"  ツール名 : {req['name']}")
        print(f"  引数     : {req['arguments']}")
    for cfg in payload["review_configs"]:
        print(f"  許可された決定: {cfg['allowed_decisions']}")
    print("-" * 36)


def run_approve_flow(agent):
    """承認 (approve) パターン: パスワードリセットを承認して実行させる。"""
    print("=" * 70)
    print("パターン A: approve — リセットを承認して実行する")
    print("=" * 70)

    # スレッドごとに会話を分けるための thread_id (第4章と同じ作法)。
    config = {"configurable": {"thread_id": "exercise-6b-approve"}}

    # 1) ユーザー発話で invoke。reset_password が呼ばれると interrupt で停止します。
    #    version="v2" を付けることで、戻り値が .interrupts 属性を持つ形式になります。
    result = agent.invoke(
        {"messages": [{"role": "user", "content": "私 (emp-sato) のパスワードをリセットして"}]},
        config=config,
        version="v2",
    )

    # 2) TODO③ で実装した関数で、停止した内容 (action_requests) を表示します。
    print_interrupt(result)

    # ==================================================================
    # TODO④-A: approve で再開する
    # ==================================================================
    # decisions はリストです。止まっている tool call と同じ順序で決定を並べます。
    # 今回は 1 件なので 1 要素。type="approve" で「そのまま実行」を表します。
    # 中断時と同じ thread_id (config) を渡さないと再開できない点に注意。
    # ヒント: agent.invoke(Command(resume={"decisions": [{"type": "approve"}]}),
    #                       config=config, version="v2")
    print("\n→ オペレーターが approve を選択。Command(resume=...) で再開します。")
    final = ___  # TODO④-A: Command(resume=...) で approve して再開する invoke に置き換える

    print("\n[最終回答]")
    print(final["messages"][-1].content)
    print("  → reset_password が実行され、仮パスワードを含む案内が返れば成功です。\n")


def run_reject_flow(agent):
    """拒否 (reject) パターン: 理由を添えてリセットを拒否する。"""
    print("=" * 70)
    print("パターン B: reject — リセットを理由付きで拒否する")
    print("=" * 70)

    # approve とは別スレッドにする (別の会話として扱う)。
    config = {"configurable": {"thread_id": "exercise-6b-reject"}}

    # 1) 同じ依頼で invoke。やはり reset_password で interrupt して停止します。
    result = agent.invoke(
        {"messages": [{"role": "user", "content": "私 (emp-sato) のパスワードをリセットして"}]},
        config=config,
        version="v2",
    )

    # 2) 停止内容を表示します。
    print_interrupt(result)

    # ==================================================================
    # TODO④-B: reject で再開する (message 付き)
    # ==================================================================
    # type="reject" は「実行しない」。message は会話に追加され、エージェントは
    # それを踏まえて代替案内を返します。副作用ツールの拒否では、
    # 「なぜダメか・どうすべきか」が伝わる具体的な message を書くのが実務の作法です。
    #
    # 【重要】副作用ツールの拒否に respond を使ってはいけません。
    #   respond は人間の回答を「ツールが成功した結果」としてモデルに渡すため、
    #   モデルが「リセットは実行された」と誤認します。拒否は必ず reject を使います。
    #
    # ヒント: Command(resume={"decisions": [{"type": "reject", "message": "<理由>"}]})
    print("\n→ オペレーターが reject を選択。理由付きで再開します。")
    final = ___  # TODO④-B: Command(resume=...) で reject (message 付き) して再開する invoke に置き換える

    print("\n[最終回答]")
    print(final["messages"][-1].content)
    print("  → reset_password は実行されず、本人手続きを促す代替案内が返れば成功です。\n")


if __name__ == "__main__":
    agent = build_agent()

    # 承認 → 拒否 の 2 パターンを順に体験する。
    run_approve_flow(agent)
    run_reject_flow(agent)

    print("=" * 70)
    print("まとめ: interrupt_on でツールごとの承認ポリシーを宣言し、")
    print("        checkpointer に保存された状態を Command(resume=...) で再開する。")
    print("        approve で実行・reject で理由付き代替案内、を確認できました。")
    print("        次は 6-5: agent.py + langgraph.json で、同じフローを")
    print("        Agent Chat UI のブラウザ承認ダイアログから操作します。")
    print("=" * 70)
