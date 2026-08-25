"""weather_server.py — FastMCP 製の MCP サーバー (HTTP transport)

このファイルも「MCP サーバー側の中の人」ですが、math_server.py とは
通信方式 (transport) が違います。こちらは HTTP で通信します。

----------------------------------------------------------------------
transport (接続方式) = streamable HTTP
----------------------------------------------------------------------
HTTP サーバーは、stdio と違って「あらかじめ自分で起動しておく」必要があります。
クライアントは「すでにどこかで動いている HTTP サーバー」に URL で接続するだけだからです。

  起動方法 (別ターミナルで先に実行しておく):
      python servers/weather_server.py

  起動すると、このサーバーは http://localhost:8000/mcp で待ち受けます。
  (FastMCP の streamable HTTP は、デフォルトで /mcp というパスにマウントされます)

  クライアント側 (handson_5A_client.py) は、この URL に
      {"transport": "http", "url": "http://localhost:8000/mcp"}
  という設定で接続します。

「社内で共有するサーバー」や「SaaS として提供される MCP サーバー」は、
このように HTTP で公開されているのが一般的です。
(本ハンズオンでは学習のため localhost で動かしますが、url を差し替えれば
 リモートのサーバーにもそのまま接続できます)
"""

from mcp.server.fastmcp import FastMCP

# host / port を指定してサーバーを作る。
# これにより streamable HTTP は http://localhost:8000/mcp で待ち受ける。
mcp = FastMCP("Weather", host="127.0.0.1", port=8000)


@mcp.tool()
def get_weather(city: str) -> str:
    """指定された都市の現在の天気を返す。

    天気・気温など「その都市の今の天候」を尋ねられたときに使う。

    Args:
        city: 天気を知りたい都市名 (例: 東京, 大阪)
    """
    # 学習用のダミー実装: 実際の API は呼ばず、固定の天気を返す。
    # 本物の天気サーバーなら、ここで気象 API を呼ぶことになる。
    weather_db = {
        "東京": "晴れ、気温 24℃",
        "大阪": "くもり、気温 22℃",
        "札幌": "雨、気温 18℃",
        "那覇": "晴れ、気温 29℃",
    }
    return weather_db.get(city, f"{city} の天気データは見つかりませんでした。")


if __name__ == "__main__":
    # transport="streamable-http" で HTTP サーバーとして起動する。
    # このプロセスは Ctrl+C で止めるまで起動し続け、リクエストを待ち受ける。
    print("Weather MCP サーバーを起動します: http://127.0.0.1:8000/mcp")
    print("(このターミナルは起動したままにし、別ターミナルでクライアントを実行してください)")
    mcp.run(transport="streamable-http")
