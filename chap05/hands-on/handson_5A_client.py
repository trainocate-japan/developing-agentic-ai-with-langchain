"""handson_5A_client.py — MultiServerMCPClient で 2 つの MCP サーバーに接続する

ハンズオン 5-A のクライアント本体です。
2 種類の MCP サーバー (transport が異なる) に同時に接続し、両方のツールを
1 つのエージェントに持たせて動かします。

  - math サーバー    : stdio で接続 (このスクリプトが自動でサブプロセス起動)
  - weather サーバー : HTTP で接続 (別ターミナルで先に起動しておく必要あり)

----------------------------------------------------------------------
この章のいちばん大事なこと
----------------------------------------------------------------------
MCP を使っても、エージェントの作り方は何も変わりません。
変わるのは「tools リストに入れるツールの調達方法」だけです。
  第3章: 自作ツールを tools に入れた
  本章 : MCP サーバーから取得したツールを tools に入れる
取得さえ済めば、create_agent への渡し方は第3章とまったく同じです。

----------------------------------------------------------------------
実行する前に (2 ターミナル手順)
----------------------------------------------------------------------
  ターミナル 1: HTTP の weather サーバーを起動しておく
      python servers/weather_server.py
  ターミナル 2: このクライアントを実行する
      python handson_5A_client.py
  (math サーバーは stdio なので手動起動は不要。このスクリプトが起動する)
"""

import asyncio
import os

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_mcp_adapters.client import MultiServerMCPClient

# .env ファイルから環境変数を読み込む (OPENAI_API_KEY など)。
# これで os.environ["OPENAI_API_KEY"] が使えるようになる。
load_dotenv()

# モデル名は変数に集約 ("provider:model" 形式)。研修実施時に最新へ差し替える。
MODEL = "openai:gpt-5.4"

# math_server.py の絶対パスを求めておく。
# stdio の args にはサーバースクリプトのパスを渡すが、相対パスだと
# 「どのディレクトリから実行したか」でパスがずれて起動に失敗する。
# os.path.abspath で絶対パスにしておくのが鉄則 (__file__ はこのファイルの場所)。
HERE = os.path.dirname(os.path.abspath(__file__))
MATH_SERVER_PATH = os.path.join(HERE, "servers", "math_server.py")


# ----------------------------------------------------------------------
# async/await の 3 点セット
# ----------------------------------------------------------------------
# MCP アダプタの API は「非同期 (async) 関数」として提供されています。
# そのため、それらを呼ぶ処理は async def の関数の中に書く必要があります。
# 覚えることは 3 つだけ:
#   ① async def main():        … 非同期の関数を定義する
#   ② await ...                 … 非同期の関数を呼ぶときは await を付ける
#   ③ asyncio.run(main())       … main() を起動する (ファイル末尾)
# さらにエージェント呼び出しは invoke ではなく ainvoke (非同期版) を使い、
# これにも await を付けます。
async def main():
    # サーバー名をキーにした辞書で、複数サーバーの接続設定を一度に渡す。
    client = MultiServerMCPClient(
        {
            "math": {
                "transport": "stdio",        # ローカル: サブプロセスとして起動して通信
                "command": "python",         # 起動コマンド
                "args": [MATH_SERVER_PATH],  # 起動するスクリプト (絶対パス)
            },
            "weather": {
                "transport": "http",                     # リモート: HTTP で接続
                "url": "http://127.0.0.1:8000/mcp",      # weather_server.py の待ち受け先
            },
        }
    )

    # 全サーバーのツールをまとめて取得する。この 1 行が本章の主役。
    # get_tools() は非同期関数なので await を付ける。
    #   → await を付けないと、ツール取得は実行されず「予約券 (coroutine)」が
    #     返るだけで、後続でエラーになる。「I/O を待つ処理 = await」と覚える。
    # 取得結果は LangChain の Tool オブジェクトのリスト。
    # MCP サーバーのツールが、第3章の自作ツールと同じ形に変換されて返ってくる。
    tools = await client.get_tools()

    print("取得したツール:", [t.name for t in tools])

    # ここから先は第3章とまったく同じ。tools をそのまま create_agent に渡すだけ。
    agent = create_agent(MODEL, tools)

    # エージェントを呼び出す。非同期コードの中では invoke ではなく ainvoke を使う。
    #   → MCP のツールは非同期で動くため、同期の invoke で呼ぶと実行時エラーになる。
    #   → ainvoke も非同期関数なので、やはり await を付けて「終わるまで待つ」。
    result = await agent.ainvoke(
        {"messages": [{"role": "user", "content": "(3 + 5) × 12 はいくつ?"}]}
    )

    # 最終メッセージ (エージェントの回答) を表示する。
    print("\n=== エージェントの回答 ===")
    print(result["messages"][-1].content)

    # weather サーバーのツールも試してみる (HTTP 接続が効いているか確認)。
    result2 = await agent.ainvoke(
        {"messages": [{"role": "user", "content": "東京の天気を教えて"}]}
    )
    print("\n=== エージェントの回答 (天気) ===")
    print(result2["messages"][-1].content)


# ③ asyncio.run() で main() を起動する。
#    これは「.py スクリプトとして実行する場合」の起動方法。
#    (Jupyter / Colab では裏でイベントループが動いているため asyncio.run は使えず、
#     セルで直接 await を書く。本章は .py なのでこの形が標準。)
if __name__ == "__main__":
    asyncio.run(main())
