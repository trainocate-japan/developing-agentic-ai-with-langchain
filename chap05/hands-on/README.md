# ハンズオン 5-A: MultiServerMCPClient で 2 サーバー接続

研修コース「Agentic AI 開発実践 - LangChain 版」/ 第5章「MCP サーバーの利用」

`MultiServerMCPClient` を使い、**2 種類の MCP サーバー** (stdio と HTTP) に同時接続して、
両方のツールを 1 つのエージェントに持たせて動かすハンズオンです。

> **この章のキーメッセージ**: MCP を使ってもエージェントの作り方は変わりません。
> 変わるのは「`tools` リストに入れるツールの**調達方法**」だけ——
> 第3章では自分で書き、本章では MCP サーバーから取得して入れます。

---

## このハンズオンで動かすもの

```
hands-on/
├── README.md               # この手順書
├── requirements.txt        # 依存パッケージ (ピン留め済み)
├── servers/
│   ├── math_server.py      # FastMCP の stdio サーバー (add / multiply)
│   └── weather_server.py   # FastMCP の HTTP サーバー (get_weather)
└── handson_5A_client.py    # 2 サーバーに接続するクライアント本体
```

| ファイル | transport | 役割 |
|---|---|---|
| `servers/math_server.py` | stdio | 足し算・掛け算ツールを公開。クライアントがサブプロセスとして**自動起動** |
| `servers/weather_server.py` | HTTP | 天気ツールを公開。**別ターミナルで先に起動**しておく必要がある |
| `handson_5A_client.py` | — | 上記 2 つに接続し、`get_tools()` → `create_agent` → `ainvoke` |

---

## 初回セットアップ (第5〜8章で 1 回だけ)

本章から実行環境は **Google Cloud Shell** (Linux) です。リポジトリを clone し、
`.py` スクリプトをターミナルで実行します。

> **この clone・venv・.env は第5〜8章で共通です。** ここで 1 回だけ作れば、
> 以降の章 (5-B / 6-A / 6-B …) では**作り直さず使い回します**。次章からは
> 「ディレクトリを移動して `pip install -r requirements.txt` するだけ」になります。

### 1. リポジトリを取得して、リポジトリのルートへ移動

```bash
git clone https://github.com/trainocate-japan/developing-agentic-ai-with-langchain.git
cd developing-agentic-ai-with-langchain   # ← リポジトリのルート (chap05 などの章フォルダと .env.example がある場所)
```

### 2. リポジトリのルートで仮想環境 (venv) を作って有効化

```bash
python -m venv .venv
source .venv/bin/activate
```

> この `.venv` は**リポジトリのルートに 1 つだけ**作り、第5〜8章で使い回します
> (章ごとに作り直しません)。

### 3. リポジトリのルートで .env を作成し、キーを記入

ルートの `.env.example` を `.env` という名前でコピーし、`OPENAI_API_KEY` と
`LANGSMITH_API_KEY` (第4章で発行したキー) を記入します。

```bash
cp .env.example .env
# エディタで .env を開き、OPENAI_API_KEY=... と LANGSMITH_API_KEY=... に実際のキーを記入する
```

> **LangSmith はコース全体で有効化しています。** ルートの `.env` に `LANGSMITH_TRACING=true` と
> `LANGSMITH_API_KEY` を入れておけば、第5〜8章の各 `.py` スクリプトの実行が**自動的に
> LangSmith に記録**されます (コード変更は不要)。各章のスクリプトは実行位置から上位ディレクトリを
> 遡ってこのルートの `.env` を読み込むため、`.env` はルートに 1 つあれば全章で参照できます。
>
> **`.env` はコミットしない**でください (キーが漏れます)。リポジトリに置くのは
> 値の入っていない `.env.example` だけです。

### 4. このハンズオンのディレクトリへ移動して依存をインストール

```bash
cd chap05/hands-on
pip install -r requirements.txt
```

---

## 実行する (2 ターミナル手順)

HTTP の weather サーバーは「あらかじめ起動しておく」必要があるため、ターミナルを 2 つ使います。
(stdio の math サーバーはクライアントが自動起動するので、手動起動は不要です)

### ターミナル 1: HTTP サーバーを起動して待ち受ける

```bash
source .venv/bin/activate        # venv を有効化 (新しいターミナルなので)
python servers/weather_server.py
```

次のように表示され、`Ctrl+C` で止めるまで起動し続けます。**このターミナルはそのまま**にします。

```
Weather MCP サーバーを起動します: http://127.0.0.1:8000/mcp
(このターミナルは起動したままにし、別ターミナルでクライアントを実行してください)
```

> Cloud Shell では、ターミナル右上の「+」や「ターミナルを分割」で 2 つ目のターミナルを開けます。

### ターミナル 2: クライアントを実行する

```bash
source .venv/bin/activate        # こちらの新ターミナルでも venv を有効化
python handson_5A_client.py
```

### 期待される出力 (例)

```
取得したツール: ['add', 'multiply', 'get_weather']

=== エージェントの回答 ===
(3 + 5) × 12 は 96 です。

=== エージェントの回答 (天気) ===
東京の天気は「晴れ、気温 24℃」です。
```

- `取得したツール` に **math サーバーの add / multiply** と **weather サーバーの get_weather** の
  両方が並んでいれば、2 サーバー接続が成功しています。
- 数式の質問では math のツールが、天気の質問では weather のツールが呼ばれます。

---

## コードリーディングのポイント

実行できたら、ソースを開いて次の 3 点を確認してください。

1. **`@mcp.tool()` は `@tool` とほぼ同じ** (`servers/math_server.py`)
   サーバー側のツール定義は、第3章の自作ツールとそっくりです。
   「サーバーの中の人も、誰かがこうやってツールを書いている」だけだと分かります。

2. **async の 3 点セット** (`handson_5A_client.py`)
   `async def main()` / `await client.get_tools()` / `asyncio.run(main())` の 3 つと、
   `invoke` ではなく `await agent.ainvoke(...)` を使っている点を確認します。
   「どこに `await` が付いているか」「なぜ `ainvoke` か」をコメントと突き合わせてください。

3. **`get_tools()` → `create_agent` の流れ**
   MCP から取得したツールを、第3章と寸分違わぬ形で `create_agent(MODEL, tools)` に
   渡しているだけ——これが本章の幹です。

---

## LangSmith でトレースを観察する

LangSmith は**コース全体で有効化済み**です。初回セットアップでルートの `.env` に
`LANGSMITH_TRACING=true` / `LANGSMITH_API_KEY` を記入していれば、**コードを 1 行も変えずに**
このハンズオンの MCP ツール呼び出しが [smith.langchain.com](https://smith.langchain.com) に
自動記録されます。実行後にプロジェクト (`LANGSMITH_PROJECT`、既定 `langchain-training-day2`) を
開いてトレースを確認してください。

トレースを開くと、**MCP 由来のツール呼び出しが、第3章の自作ツールとまったく同じ
`ToolMessage` の形**で記録されているのが分かります。エージェントループから見れば、
ツールが「自作」か「MCP 経由」かの区別はありません。

---

## うまくいかないときは

| 症状 | 確認すること |
|---|---|
| `get_weather` が取れない / 接続エラー | ターミナル 1 で weather サーバーが起動しているか。URL が `http://127.0.0.1:8000/mcp` か |
| `OPENAI_API_KEY` 関連のエラー | リポジトリのルートに `.env` を作成し、キーを記入したか (初回セットアップ手順 3) |
| math サーバーが起動しない | `args` のパスは絶対パスか (本コードは `os.path.abspath` で自動解決済み) |

> **実務で Windows を使う場合の参考**: 本ハンズオンは Cloud Shell (Linux) 前提です。
> 実務で Windows から stdio サーバーを起動すると、イベントループ (`NotImplementedError`)・
> `npx` 起動 ("Connection closed")・文字コード (`UnicodeEncodeError`) の 3 つの罠に
> 当たることがあります。対処は教材の早見表を参照してください (Cloud Shell では発生しません)。
