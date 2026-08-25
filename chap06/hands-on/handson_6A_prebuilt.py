"""handson_6A_prebuilt.py — ハンズオン 6-A (前半): Prebuilt Middleware の組み込み

研修コース「LangChain による Agentic AI 開発実践」/ 第6章「Middleware と HITL」

============================================================================
これは「作成済みのコード」です。講師の解説を聞きながら一緒に実行します。
受講者がコードを書く必要はありません。コメントと print 出力を突き合わせ、
「Middleware を 1 行足すだけで挙動がどう変わるか」を目で確かめるのが狙いです。
============================================================================

【このスクリプトで観察すること】
  これまで育ててきたヘルプデスクエージェントに、公式提供の Prebuilt Middleware を
  2 つ組み込みます。エージェント本体 (model / tools) には一切手を入れず、
  middleware リストに足すだけで、次の 2 つの「実運用機能」が後付けされます。

  ① PIIMiddleware("email", strategy="redact", apply_to_input=True)
       → ユーザー入力に含まれるメールアドレスが、モデルに渡る前に
         [REDACTED_EMAIL] に置き換えられる (個人情報の保護)。

  ② ToolCallLimitMiddleware(run_limit=3)
       → 1 回の invoke (ユーザーの 1 発話) で許されるツール呼び出しを 3 回までに制限。
         暴走・課金の暴発を防ぐガードレール。

  「まず Prebuilt を探す」——車輪の再発明をせず、用意された部品を組み合わせるのが定石です。

【実行方法 (Google Cloud Shell / Linux)】
  README.md のセットアップ後、次を実行:
      python handson_6A_prebuilt.py
"""

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.agents.middleware import PIIMiddleware, ToolCallLimitMiddleware

# 配布ツール (search_faq / get_system_status) を読み込む。
from helpdesk_tools import get_system_status, search_faq

# .env から環境変数を読み込む (OPENAI_API_KEY など)。
load_dotenv()

# モデル名は変数に集約 ("provider:model" 形式)。研修実施時に最新へ差し替える。
MODEL = "openai:gpt-5.4"

# エージェントの役割を伝える system プロンプト。
SYSTEM_PROMPT = (
    "あなたは社内 IT ヘルプデスクの一次対応担当です。"
    "社員からの問い合わせに、丁寧かつ簡潔に答えてください。"
    "手続きややり方の質問には FAQ 検索ツール (search_faq) を、"
    "システムが動いているかなどの稼働状況の質問には稼働状況ツール (get_system_status) を使って調べます。"
)


# ----------------------------------------------------------------------
# Prebuilt Middleware を組み込んだエージェントを作る
# ----------------------------------------------------------------------
# create_agent の骨格は第3〜5章と同じ。違いは middleware=[...] が増えた点だけ。
# ガードレール的な Middleware はリストの先頭に置くのが定石なので、
# PII 保護 → ツール回数制限 の順に並べています。
agent = create_agent(
    model=MODEL,
    tools=[search_faq, get_system_status],
    system_prompt=SYSTEM_PROMPT,
    middleware=[
        # ① PII 保護: ユーザー入力中のメールアドレスを、モデルに渡る前に redact する。
        #    strategy="redact" は種別ラベル ([REDACTED_EMAIL]) への置換。
        #    apply_to_input=True で「ユーザー入力」を検査対象にする (既定でも True)。
        PIIMiddleware("email", strategy="redact", apply_to_input=True),
        # ② ツール呼び出しの回数制限: 1 回の invoke あたり 3 回まで。
        #    run_limit は invoke ごとにリセットされる制限 (スレッド累計は thread_limit)。
        ToolCallLimitMiddleware(run_limit=3),
    ],
)


def observe_pii_redaction():
    """観察 1: メールアドレスが [REDACTED_EMAIL] に置換されることを確認する。"""
    print("=" * 70)
    print("観察 1: PIIMiddleware — メールアドレスの redact")
    print("=" * 70)

    # わざとメールアドレスを含む問い合わせを送る。
    user_text = "私のメールは taro.yamada@example.com です。VPN の設定方法を教えてください。"
    print(f"[ユーザー入力(生)] {user_text}\n")

    result = agent.invoke({"messages": [{"role": "user", "content": user_text}]})

    # モデルが実際に受け取った HumanMessage を見ると、メール部分が
    # [REDACTED_EMAIL] に置き換わっている (PIIMiddleware が input を加工したため)。
    human_messages = [m for m in result["messages"] if m.__class__.__name__ == "HumanMessage"]
    if human_messages:
        print("[モデルが受け取った入力] ", human_messages[0].content)
        print("  → 'taro.yamada@example.com' が [REDACTED_EMAIL] になっていれば成功です。\n")

    print("[最終回答]")
    print(result["messages"][-1].content)
    print()


def observe_tool_call_limit():
    """観察 2: ツール呼び出しが run_limit=3 で制限されることを確認する。"""
    print("=" * 70)
    print("観察 2: ToolCallLimitMiddleware — ツール呼び出し回数の制限 (run_limit=3)")
    print("=" * 70)

    # 複数のシステムの稼働状況をまとめて尋ね、ツールが何度も呼ばれる状況を作る。
    # 4 件以上の稼働確認を求めることで、3 回の上限に当たりやすくしている。
    user_text = (
        "勤怠システム・経費精算システム・メールサーバー・VPN のすべての稼働状況を"
        "それぞれ確認して、まとめて教えてください。"
    )
    print(f"[ユーザー入力] {user_text}\n")

    result = agent.invoke({"messages": [{"role": "user", "content": user_text}]})

    # 実際に呼ばれたツールの軌跡を数える。run_limit=3 を超えた呼び出しは
    # (既定の exit_behavior="continue" のため) エラーメッセージでブロックされ、
    # モデルはその結果を踏まえて応答をまとめる。
    print("[呼ばれたツール (軌跡)]")
    tool_call_count = 0
    for msg in result["messages"]:
        for call in getattr(msg, "tool_calls", None) or []:
            tool_call_count += 1
            print(f"  - {call['name']}({call['args']})")
    print(f"  → ツール呼び出しの総数: {tool_call_count}")
    print("    (上限 3 回を超えた分はブロックされる様子をトレースでも確認できます)\n")

    print("[最終回答]")
    print(result["messages"][-1].content)
    print()


if __name__ == "__main__":
    observe_pii_redaction()
    observe_tool_call_limit()

    print("=" * 70)
    print("まとめ: エージェント本体 (model / tools) は変えず、middleware リストに")
    print("        2 行足すだけで『PII 保護』と『ツール回数制限』を後付けできました。")
    print("        LangSmith を有効化していれば、トレースでも同じ挙動を確認できます。")
    print("=" * 70)
