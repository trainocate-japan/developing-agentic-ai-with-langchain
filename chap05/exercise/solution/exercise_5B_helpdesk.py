"""exercise_5B_helpdesk.py 【正解 (solution)】

演習 5-B: 社内ナレッジ MCP サーバーの接続 — ヘルプデスク Step 4
研修コース「LangChain による Agentic AI 開発実践」/ 第5章「MCP サーバーの利用」

============================================================================
これは演習 5-B の「正解 (solution)」です。
TODO を埋める前に答えを見てしまわないよう、まずは starter で自力で挑戦してください。
詰まったとき・答え合わせのときにこちらを参照しましょう。
============================================================================

【この演習で作るもの: ヘルプデスクエージェント v3】
  これまでのヘルプデスク (v2) は、FAQ 検索ツール search_faq を「自前のコード」で
  持っていました。本演習では情報システム部門が「社内ナレッジ検索 MCP サーバー」を
  公開したという設定で、自作の search_faq を廃止し、MCP サーバーから FAQ ツールを
  「調達」する構成に切り替えます。

  ポイント: 稼働状況ツール get_system_status は引き続き「自作 @tool」のまま手元に残します。
  つまり v3 は——
      MCP から借りたツール (FAQ 検索・文書取得) + 自作ツール (稼働状況)
  ——を 1 つの tools リストに混在させたエージェントになります。

【ヘルプデスク演習ストーリーにおける位置づけ (Step 4)】
  | 章 | 追加する要素 | 演習後の姿 |
  |---|---|---|
  | 第3章 | create_agent / @tool / 構造化出力 | FAQ 検索 + 稼働状況ツールを持つ単体エージェント (v1) |
  | 第4章 | Checkpointer / LangSmith | 社員ごとに会話を記憶するエージェント (v2) |
  | 第5章 (この演習) | MCP | FAQ を MCP サーバーから調達するエージェント (v3) |

【非同期 (async) について — 大事な前提】
  MCP アダプタの API は非同期 (async) です。そのため main() は async def で書き、
  ツール取得やエージェント呼び出しには await を付けます。
  この async の骨格 (async def main / await / asyncio.run / ainvoke) は
  すべて記述済みです。あなたが書く必要はありません。
  「どこに await が付いているか」「なぜ invoke ではなく ainvoke なのか」を
  コメントと突き合わせて読み解いてください (演習の狙いの 1 つです)。
"""

import asyncio
import os

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.tools import tool
from langchain_mcp_adapters.client import MultiServerMCPClient

# (発展課題で使う) ステートフル版でツールをロードするための関数。
from langchain_mcp_adapters.tools import load_mcp_tools

# .env から環境変数を読み込む (OPENAI_API_KEY など)。
load_dotenv()

# モデル名は変数に集約 ("provider:model" 形式)。研修実施時に最新へ差し替える。
MODEL = "openai:gpt-5.4"

# knowledge_server.py の絶対パスを求めておく。
# stdio の args にはサーバースクリプトのパスを渡すが、相対パスだと実行ディレクトリ次第で
# ずれて起動に失敗する。os.path.abspath で絶対パス化しておくのが鉄則。
HERE = os.path.dirname(os.path.abspath(__file__))
KNOWLEDGE_SERVER_PATH = os.path.join(HERE, "servers", "knowledge_server.py")


# ----------------------------------------------------------------------
# 手元ツール (自作 @tool) — 稼働状況の確認
# ----------------------------------------------------------------------
# FAQ は MCP サーバーに任せますが、「自社システムの稼働状況」は自作ツールのままにします。
# こうした自社固有のロジックは、外部サーバー化せず手元に持つのが向いています
# (第3章・第4章から引き継いだツールです)。

SYSTEM_STATUS = {
    "勤怠システム": "正常稼働中",
    "経費精算システム": "正常稼働中",
    "メールサーバー": "一部遅延あり (調査中)",
    "VPN": "メンテナンス中 (本日 22:00 まで)",
}


@tool
def get_system_status(service: str) -> str:
    """指定された社内システムの現在の稼働状況を取得する。

    システムが「動いているか」「障害が出ていないか」「メンテナンス中か」といった
    稼働状態の問い合わせに使う。

    Args:
        service: 稼働状況を知りたい社内システムの名称 (例: 勤怠システム, VPN)
    """
    status = SYSTEM_STATUS.get(service, "不明 (登録されていないシステムです)")
    return f"{service}の稼働状況: {status}"


# エージェントの役割を伝える system プロンプト (FAQ は MCP ツールで調べる旨を含む)。
SYSTEM_PROMPT = (
    "あなたは社内 IT ヘルプデスクの一次対応担当です。"
    "社員からの問い合わせに、丁寧かつ簡潔に答えてください。"
    "手続きややり方の質問には社内ナレッジの FAQ 検索ツール (search_faq) を、"
    "システムが動いているかなどの稼働状況の質問には稼働状況ツール (get_system_status) を使って調べます。"
    "必要に応じて文書取得ツール (get_document) で詳細手順も案内してください。"
)


async def main():
    # ------------------------------------------------------------------
    # [解答①] MultiServerMCPClient の接続設定 (stdio transport)
    # ------------------------------------------------------------------
    # 社内ナレッジ MCP サーバー (knowledge_server.py) に stdio で接続する。
    #   - transport: "stdio" … クライアントがサーバーをサブプロセスとして起動
    #   - command  : "python" … 起動コマンド
    #   - args     : [サーバースクリプトの絶対パス] … os.path.abspath で求めた値
    client = MultiServerMCPClient(
        {
            "knowledge": {
                "transport": "stdio",
                "command": "python",
                "args": [KNOWLEDGE_SERVER_PATH],
            },
        }
    )

    # ------------------------------------------------------------------
    # [解答②] MCP ツールの取得と、自作ツールとの結合
    # ------------------------------------------------------------------
    # client.get_tools() で MCP サーバーのツール (search_faq / get_document) を取得する。
    # get_tools() は非同期関数なので await を付ける (await は記述済み)。
    mcp_tools = await client.get_tools()

    # MCP から借りたツールと、手元の自作ツール (get_system_status) を結合する。
    # どちらも LangChain の Tool オブジェクトなので、Python のリスト結合で混在できる。
    tools = mcp_tools + [get_system_status]

    print("使用するツール:", [t.name for t in tools])

    # ここから先は第3章・第4章と同じ。tools をそのまま create_agent に渡すだけ。
    agent = create_agent(MODEL, tools, system_prompt=SYSTEM_PROMPT)

    # エージェントを呼び出す。非同期コードの中なので invoke ではなく ainvoke を使い、
    # await で「終わるまで待つ」。MCP ツールは非同期で動くため、同期の invoke だと
    # 実行時エラーになる、というのがここで ainvoke を使う理由。
    result = await agent.ainvoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "経費精算のやり方を教えて。あと勤怠システムは動いてる?",
                }
            ]
        }
    )

    # 軌跡を表示する。FAQ (MCP ツール) と稼働状況 (自作ツール) の両方が
    # 呼ばれていることを、ツール呼び出しのログで確認できる。
    print("\n=== 最終回答 ===")
    print(result["messages"][-1].content)

    print("\n=== 呼ばれたツール (軌跡) ===")
    for msg in result["messages"]:
        tool_calls = getattr(msg, "tool_calls", None)
        if tool_calls:
            for call in tool_calls:
                print(f"  - {call['name']}({call['args']})")


# ============================================================================
# (発展) ステートフル版 — client.session() + load_mcp_tools
# ============================================================================
# デフォルトの get_tools() は「ステートレス」で、ツールを呼ぶたびに MCP セッションを
# 生成・破棄します。stdio ではこれが「ツール呼び出しのたびにサーバープロセスが起動・終了」
# を意味し、高頻度呼び出しでは遅くなります。
#
# client.session() で永続セッションを明示的に張ると、その with ブロックの間は
# サーバープロセスが起動したままになり、セッションが再利用されます。
# ツールの取得が get_tools() (全サーバー一括) から load_mcp_tools(session)
# (特定セッションから) に変わる点に注目してください。
#
# 発展課題: main() の代わりにこの main_stateful() を asyncio.run で呼び、
# 応答速度の違いを体感してみましょう (ファイル末尾の呼び出しを差し替える)。
async def main_stateful():
    client = MultiServerMCPClient(
        {
            "knowledge": {
                "transport": "stdio",
                "command": "python",
                "args": [KNOWLEDGE_SERVER_PATH],
            },
        }
    )

    # async with でセッションを 1 本張り、ブロックを抜けるときに確実に解放する。
    # (async with は第4章までに見た with の非同期版。役割は同じ)
    async with client.session("knowledge") as session:
        # このセッションからツールをロードする (ステートフル)。
        mcp_tools = await load_mcp_tools(session)
        tools = mcp_tools + [get_system_status]
        agent = create_agent(MODEL, tools, system_prompt=SYSTEM_PROMPT)

        # この with ブロックの間、サーバープロセスは起動したまま。
        # 何度 ainvoke してもセッションは再利用される。
        result = await agent.ainvoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": "経費精算のやり方を教えて。あと勤怠システムは動いてる?",
                    }
                ]
            }
        )
        print("\n=== (ステートフル版) 最終回答 ===")
        print(result["messages"][-1].content)


if __name__ == "__main__":
    # 通常版を実行する。
    asyncio.run(main())

    # 発展課題を試すときは、上の行をコメントアウトし、下の行を有効にする:
    # asyncio.run(main_stateful())
