"""handson_6B_hitl.py — ハンズオン 6-B (CLI 版): HITL による承認フロー

研修コース「Agentic AI 開発実践 - LangChain 版」/ 第6章「Middleware と HITL」

============================================================================
これは「作成済みのコード」です。講師の解説を聞きながら一緒に実行します。
受講者がコードを書く必要はありません。コメントと print 出力を突き合わせ、
「エージェントを途中で止めて、人間の決定で再開する」流れを目で確かめるのが狙いです。
============================================================================

【このスクリプトで観察すること】
  題材は教科書 6-4 節と同じ経費精算エージェントです。ツールは 2 つだけ。

    - get_expense    … 経費申請の照会 (読み取り系)。承認不要で素通しする
    - transfer_money … 送金 (書き込み系・やり直しが効かない)。必ず人間の承認を要求する

  この仕分けを HumanInTheLoopMiddleware の interrupt_on に書くと、モデルが
  transfer_money を呼ぼうとした瞬間にエージェントが停止 (interrupt) します。
  停止した時点の状態は checkpointer に保存され、人間が決定を下したあとに
  同じ thread_id で Command(resume=...) を invoke すると、続きから再開します。

  観察 1: 照会は止まらない        — get_expense は素通しで完走する
  観察 2: 送金は止まる            — interrupt の中身 (誰に・いくら) を読み解く
  観察 3: approve                 — 承認してそのまま送金する
  観察 4: edit                    — 金額を修正してから送金する
  観察 5: reject                  — 理由を添えて送金を拒否する
  観察 6: (発展) つまずきの実演   — checkpointer を渡し忘れると何が起きるか

【4 つ目の決定タイプ respond をここで試さない理由】
  決定タイプは approve / edit / reject / respond の 4 つですが、このハンズオンで
  実演するのは前の 3 つだけです。respond は「人間の回答をツールの実行結果として
  モデルに渡す」決定で、送金のような副作用のあるツールに使うと、モデルが
  「送金は成功した」と誤認します。respond の正しい用途は ask_user 系ツール専用です。
  詳しくは教科書 6-4 節の「落とし穴」を参照してください。

【async は使いません】
  ツールはローカル @tool (同期) です。HITL の中断・再開は同期の invoke と
  Command(resume) で完結するため、async は使いません。

【実行方法 (Google Cloud Shell / Linux)】
  README.md のセットアップ後、次を実行:
      python handson_6B_hitl.py
"""

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.agents.middleware import HumanInTheLoopMiddleware
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

# 配布ツール (get_expense / transfer_money) を読み込む。
from expense_tools import get_expense, transfer_money

# .env から環境変数を読み込む (OPENAI_API_KEY など)。
load_dotenv()

# モデル名は変数に集約 ("provider:model" 形式)。研修実施時に最新へ差し替える。
MODEL = "openai:gpt-5.4"

# エージェントの役割を伝える system プロンプト。
SYSTEM_PROMPT = (
    "あなたは社内の経費精算を担当するアシスタントです。"
    "社員からの依頼に、丁寧かつ簡潔に答えてください。"
    "経費申請の状況を尋ねられたら get_expense で照会します。"
    "送金の依頼には transfer_money を使います。"
    # ↓ ここが HITL ハンズオンの生命線。モデルが「念のため確認させてください」と
    #   聞き返して会話を終えてしまうと、transfer_money が呼ばれず interrupt が
    #   起きない (= 承認フローに入れない)。
    "送金を依頼されたら、確認の聞き返しや案内文で代替せず、"
    "依頼文に書かれた宛先を to に、金額を amount に渡して transfer_money を必ず呼び出してください。"
    "実行してよいかどうかは人間の承認者が承認フローで判断するので、あなたが遠慮する必要はありません。"
)


def build_agent(with_checkpointer: bool = True):
    """承認フロー付きの経費精算エージェントを構成して返す。

    Args:
        with_checkpointer: False にすると checkpointer を渡さない
            (観察 6 で「渡し忘れると何が起きるか」を実演するために使う)
    """
    # ------------------------------------------------------------------
    # interrupt_on = ツール名 → 承認ポリシーの辞書
    # ------------------------------------------------------------------
    # 値は 3 段階で書けます。
    #   True                         : 必ず停止し、全決定タイプを許可
    #   {"allowed_decisions": [...]} : 停止し、許可する決定タイプを限定
    #   False                        : 承認不要。停止せず素通し
    hitl = HumanInTheLoopMiddleware(
        interrupt_on={
            # 送金は止める。approve / edit / reject の 3 つを許可する
            # (edit を許可しているので、あとで金額の修正を試せる)。
            "transfer_money": {"allowed_decisions": ["approve", "edit", "reject"]},
            # 照会は何度実行しても状態が変わらないので、承認不要で素通しさせる。
            "get_expense": False,
        },
    )

    # create_agent の骨格は第3〜5章と同じ。middleware に hitl を足しただけ。
    kwargs = {}
    if with_checkpointer:
        # HITL に必須。interrupt で停止した時点の state をここに保存し、
        # Command(resume=...) のときに同じ thread_id で復元する (第4章の伏線回収)。
        # 学習用は InMemorySaver で十分 (本番は AsyncPostgresSaver などを使う)。
        kwargs["checkpointer"] = InMemorySaver()

    return create_agent(
        model=MODEL,
        tools=[get_expense, transfer_money],
        system_prompt=SYSTEM_PROMPT,
        middleware=[hitl],
        **kwargs,
    )


def show_interrupt(result) -> bool:
    """停止中の承認依頼 (action_requests) を表示する。

    version="v2" で invoke すると、戻り値は GraphOutput になり、
    状態は .value に、中断情報は .interrupts に分かれて入ります。

    中断が起きていれば True、起きずに完走していれば False を返します。
    """
    # 承認対象のツールが呼ばれなければ interrupt は起きず、.interrupts は空タプルの
    # ままエージェントが完走します。ここを確認せずに [0] を取ると IndexError です。
    if not result.interrupts:
        print("  [中断なし] このターンでは承認対象のツールが呼ばれませんでした。")
        return False

    # .interrupts は Interrupt のタプル。その .value (dict) に
    # "action_requests" (何が実行されようとしているか) と
    # "review_configs" (人間に許された選択肢) が入っている。
    payload = result.interrupts[0].value
    print("  --- 承認待ちの内容 ---")
    for req in payload["action_requests"]:
        # 引数のキーは "args" です ("arguments" ではありません)。
        print(f"    ツール名 : {req['name']}")
        print(f"    引数     : {req['args']}")
    for cfg in payload["review_configs"]:
        print(f"    許可された決定: {cfg['allowed_decisions']}")
    print("  ----------------------")
    return True


def observe_readonly_passthrough(agent):
    """観察 1: 照会ツールは承認不要で素通しすることを確認する。"""
    print("=" * 70)
    print("観察 1: 照会は止まらない — get_expense は承認不要 (interrupt_on=False)")
    print("=" * 70)

    config = {"configurable": {"thread_id": "handson-6b-readonly"}}
    user_text = "山田さんの経費申請の状況を教えてください。"
    print(f"[ユーザー入力] {user_text}\n")

    result = agent.invoke(
        {"messages": [{"role": "user", "content": user_text}]},
        config=config,
        version="v2",
    )

    # get_expense は interrupt_on で False にしてあるので、止まらずに完走する。
    show_interrupt(result)
    print("\n[最終回答]")
    print(result.value["messages"][-1].content)
    print("  → 承認を挟まずに回答まで到達していれば成功です。")
    print("    「止めるツール」と「素通しするツール」を仕分けるのが interrupt_on の役割です。\n")


def observe_interrupt_and_approve(agent):
    """観察 2 + 3: 送金で停止し、その中身を読んでから approve で再開する。"""
    print("=" * 70)
    print("観察 2: 送金は止まる — interrupt の中身を読み解く")
    print("=" * 70)

    # スレッドごとに会話を分けるための thread_id (第4章と同じ作法)。
    config = {"configurable": {"thread_id": "handson-6b-approve"}}
    user_text = "山田さんへ経費 5000 円を送金してください。"
    print(f"[ユーザー入力] {user_text}\n")

    # version="v2" を付けると、戻り値が .interrupts / .value を持つ形式になる。
    result = agent.invoke(
        {"messages": [{"role": "user", "content": user_text}]},
        config=config,
        version="v2",
    )

    if not show_interrupt(result):
        print("  → transfer_money が呼ばれませんでした。SYSTEM_PROMPT を確認してください。\n")
        return
    print("  → 送金は「まだ実行されていません」。[副作用] の行が出ていないことに注目。")
    print("    この時点の状態は checkpointer に保存され、人間の決定を待っています。\n")

    print("=" * 70)
    print("観察 3: approve — 承認してそのまま送金する")
    print("=" * 70)
    # decisions はリスト。止まっている tool call と同じ順序で決定を並べる。
    # 中断時と同じ thread_id (config) を渡さないと再開できない点に注意。
    print("→ 承認者が approve を選択。Command(resume=...) で再開します。")
    final = agent.invoke(
        Command(resume={"decisions": [{"type": "approve"}]}),
        config=config,
        version="v2",
    )

    print("\n[最終回答]")
    print(final.value["messages"][-1].content)
    print("  → 上に [副作用] transfer_money 実行 の行が出て、送金の報告が返れば成功です。\n")


def observe_edit(agent):
    """観察 4: edit で引数 (金額) を修正してから実行する。"""
    print("=" * 70)
    print("観察 4: edit — 金額を修正してから送金する")
    print("=" * 70)

    # 観察 3 とは別のスレッドにする (別の会話として扱う)。
    config = {"configurable": {"thread_id": "handson-6b-edit"}}
    user_text = "山田さんへ経費 5000 円を送金してください。"
    print(f"[ユーザー入力] {user_text}\n")

    result = agent.invoke(
        {"messages": [{"role": "user", "content": user_text}]},
        config=config,
        version="v2",
    )
    if not show_interrupt(result):
        print("  → transfer_money が呼ばれませんでした。SYSTEM_PROMPT を確認してください。\n")
        return

    # edit は「引数を差し替えて実行する」決定。edited_action にツール名と
    # 差し替え後の引数一式を渡す (一部だけでなく args 全体を書く)。
    print("\n→ 承認者が edit を選択。金額を 5000 円から 3000 円に減額して実行します。")
    final = agent.invoke(
        Command(resume={"decisions": [{
            "type": "edit",
            "edited_action": {"name": "transfer_money", "args": {"to": "山田", "amount": 3000}},
        }]}),
        config=config,
        version="v2",
    )

    print("\n[最終回答]")
    print(final.value["messages"][-1].content)
    print("  → [副作用] の行が 3000 円になっていれば成功です。")
    print("    なお引数を大幅に書き換えるとモデルが再判断して予期しない動きをすることがあります。")
    print("    編集は保守的に、が原則です。\n")


def observe_reject(agent):
    """観察 5: reject で理由を添えて拒否する。"""
    print("=" * 70)
    print("観察 5: reject — 理由を添えて送金を拒否する")
    print("=" * 70)

    config = {"configurable": {"thread_id": "handson-6b-reject"}}
    user_text = "山田さんへ経費 5000 円を送金してください。"
    print(f"[ユーザー入力] {user_text}\n")

    result = agent.invoke(
        {"messages": [{"role": "user", "content": user_text}]},
        config=config,
        version="v2",
    )
    if not show_interrupt(result):
        print("  → transfer_money が呼ばれませんでした。SYSTEM_PROMPT を確認してください。\n")
        return

    # reject は「実行しない」。message は拒否のフィードバックとして会話に追加され、
    # エージェントはそれを踏まえて代替の案内を返す。
    # 「なぜダメか・どうすべきか」が伝わる具体的な message を書くのが実務の作法。
    print("\n→ 承認者が reject を選択。理由を添えて再開します。")
    final = agent.invoke(
        Command(resume={"decisions": [{
            "type": "reject",
            "message": "今月の精算は締め切り済みです。来月分として申請し直してください。",
        }]}),
        config=config,
        version="v2",
    )

    print("\n[最終回答]")
    print(final.value["messages"][-1].content)
    print("  → [副作用] の行が出ず、来月分の申請を促す代替案内が返れば成功です。")
    print("    ここで respond を使うと、モデルは『送金は成功した』と誤認します。")
    print("    副作用ツールの拒否には必ず reject を使ってください。\n")


def observe_missing_checkpointer():
    """観察 6 (発展): checkpointer を渡し忘れると何が起きるかを実演する。"""
    print("=" * 70)
    print("観察 6 (発展): つまずきの実演 — checkpointer を渡し忘れると")
    print("=" * 70)
    print("interrupt は『state を保存して止まる』仕組みなので、保存先である")
    print("checkpointer が無いと成立しません。わざと外して実行してみます。\n")

    broken = build_agent(with_checkpointer=False)
    config = {"configurable": {"thread_id": "handson-6b-no-checkpointer"}}

    try:
        broken.invoke(
            {"messages": [{"role": "user", "content": "山田さんへ経費 5000 円を送金してください。"}]},
            config=config,
            version="v2",
        )
    except Exception as exc:
        print(f"  [発生した例外] {type(exc).__name__}: {exc}")
        print("\n  → これが『checkpointer 忘れ』のエラーです。")
        print("    HITL に checkpointer が必須な理由は、この仕組みそのものにあります。\n")
        return

    # 環境によっては invoke 自体は通り、再開の段で失敗することもある。
    print("  invoke は通りました。続けて Command(resume=...) で再開できるか試します。")
    try:
        broken.invoke(
            Command(resume={"decisions": [{"type": "approve"}]}),
            config=config,
            version="v2",
        )
        print("  (この環境では再開まで通りました)\n")
    except Exception as exc:
        print(f"  [発生した例外] {type(exc).__name__}: {exc}")
        print("\n  → 中断はできても『再開する場所』が保存されていないため失敗します。")
        print("    HITL に checkpointer が必須な理由は、この仕組みそのものにあります。\n")


if __name__ == "__main__":
    agent = build_agent()

    observe_readonly_passthrough(agent)
    observe_interrupt_and_approve(agent)
    observe_edit(agent)
    observe_reject(agent)
    observe_missing_checkpointer()

    print("=" * 70)
    print("まとめ: interrupt_on でツールごとの承認ポリシーを宣言し、")
    print("        checkpointer に保存された状態を Command(resume=...) で再開する。")
    print("        approve でそのまま実行、edit で引数を直して実行、reject で理由付き拒否。")
    print("        次は agent.py + langgraph.json で、同じ承認フローを")
    print("        Agent Chat UI のブラウザ承認ダイアログから操作します。")
    print("=" * 70)
