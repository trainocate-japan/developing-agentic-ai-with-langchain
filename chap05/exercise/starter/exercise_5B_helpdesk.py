"""exercise_5B_helpdesk.py 【演習 (starter)】

演習 5-B: 社内ナレッジ MCP サーバーの接続 — ヘルプデスク Step 4
研修コース「LangChain による Agentic AI 開発実践」/ 第5章「MCP サーバーの利用」

============================================================================
これは演習 5-B の「演習用 (starter)」です。
ファイル内の「TODO①」「TODO②」の 2 か所を、あなた自身で埋めて完成させてください。
完成版が見たくなったら solution/ を参照できますが、まずは自力で挑戦しましょう。
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

【あなたが埋めるのは MCP の 2 か所だけ (TODO①②)】
  - TODO①: MultiServerMCPClient の接続設定 (stdio transport)
  - TODO②: client.get_tools() の呼び出しと、自作ツールとの結合

【非同期 (async) は埋めなくてよい — すべて記述済み】
  MCP アダプタの API は非同期 (async) です。そのため main() は async def で書き、
  ツール取得やエージェント呼び出しには await を付けます。
  この async の骨格 (async def main / await / asyncio.run / ainvoke) は
  すべて記述済みです。あなたが書く必要はありません。
  TODO② でも「await は記述済み」で、あなたが書くのは await の右側だけです。
  代わりに「どこに await が付いているか」「なぜ invoke ではなく ainvoke なのか」を
  コメントと突き合わせて読み解いてください (これも演習の狙いです)。
"""

import asyncio
import os

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.tools import tool
from langchain_mcp_adapters.client import MultiServerMCPClient

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
# 手元ツール (自作 @tool) — 稼働状況の確認 【配布済み・編集不要】
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


# エージェントの役割を伝える system プロンプト 【配布済み・編集不要】。
SYSTEM_PROMPT = (
    "あなたは社内 IT ヘルプデスクの一次対応担当です。"
    "社員からの問い合わせに、丁寧かつ簡潔に答えてください。"
    "手続きややり方の質問には社内ナレッジの FAQ 検索ツール (search_faq) を、"
    "システムが動いているかなどの稼働状況の質問には稼働状況ツール (get_system_status) を使って調べます。"
    "必要に応じて文書取得ツール (get_document) で詳細手順も案内してください。"
)


async def main():
    # ==================================================================
    # TODO①: MultiServerMCPClient の接続設定を書く (stdio transport)
    # ==================================================================
    # 社内ナレッジ MCP サーバー (knowledge_server.py) に stdio で接続します。
    # MultiServerMCPClient(...) の引数に、サーバー名 "knowledge" をキーにした
    # 接続設定の辞書を渡してください。設定に必要なキーは次の 3 つです:
    #   - "transport": stdio で接続することを表す値
    #   - "command"  : サーバーを起動するコマンド (Python スクリプトを動かすコマンド)
    #   - "args"     : 起動するスクリプトのパスのリスト
    #
    # ヒント: args はサーバースクリプトの【絶対パス】で指定します。
    #         このファイル冒頭で用意した KNOWLEDGE_SERVER_PATH
    #         (= os.path.abspath で求めた絶対パス) をリストに入れて使ってください。
    #         相対パスだと「どのディレクトリから実行したか」でずれて起動に失敗します。
    client = MultiServerMCPClient(
        {
            # TODO①: ここにサーバー "knowledge" の接続設定 (transport / command / args) を書く
        }
    )

    # ==================================================================
    # TODO②: MCP ツールを取得し、自作ツールと結合する
    # ==================================================================
    # (1) client から MCP サーバーのツール (search_faq / get_document) を取得します。
    #     ※ await はすでに書いてあります。あなたが書くのは await の右側
    #        ——「ツールを取得するメソッド呼び出し」——だけです。
    #     ヒント: クライアントの get_tools() メソッドを呼びます (全サーバーのツールを一括取得)。
    mcp_tools = await ___  # TODO②-(1): client からツールを取得するメソッド呼び出しに置き換える

    # (2) MCP から借りたツールと、手元の自作ツール (get_system_status) を結合します。
    #     どちらも LangChain の Tool オブジェクトなので、Python のリスト結合で混在できます。
    #     ヒント: mcp_tools + [get_system_status] のように、リスト同士を足し算します。
    tools = ___  # TODO②-(2): mcp_tools と [get_system_status] を結合したリストに置き換える

    # ------------------------------------------------------------------
    # ここから下は【配布済み・編集不要】。TODO①② が正しく埋まれば動きます。
    # ------------------------------------------------------------------
    print("使用するツール:", [t.name for t in tools])

    # tools をそのまま create_agent に渡すだけ (第3章・第4章と同じ)。
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


if __name__ == "__main__":
    # async の起動 (記述済み)。.py スクリプトなので asyncio.run() で main() を動かす。
    asyncio.run(main())
