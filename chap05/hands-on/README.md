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
| `servers/weather_server.py` | HTTP | 天気ツールを公開。**【ターミナル 1】で先に起動**しておく必要がある |
| `handson_5A_client.py` | — | 上記 2 つに接続し、`get_tools()` → `create_agent` → `ainvoke` |

---

## ステップ 0: ブラウザで Google Cloud Shell を開く

本章から実行環境は **Google Cloud Shell** (ブラウザ上で使える Linux ターミナル) です。
自分の PC へのインストール作業は不要で、**ブラウザと Google アカウントだけ**で始められます。

1. ブラウザ (Chrome 推奨) で **Google アカウントにログイン**します。
2. **<https://shell.cloud.google.com/>** にアクセスします。
   (Google Cloud コンソール <https://console.cloud.google.com/> を開き、画面右上のツールバーにある
   **[Cloud Shell をアクティブにする]** アイコン `>_` をクリックしても同じです)
3. 初回は確認ダイアログが出るので **[続行]** (または [承認]) をクリックします。
4. 数十秒のプロビジョニングののち、画面にターミナルが開けば準備完了です。
   次のコマンドで動作確認しておきましょう。

   ```bash
   pwd              # /home/<ユーザー名> と表示される (= ホームディレクトリ)
   python3 --version
   ```

**このターミナルを、以降 【ターミナル 1】 と呼びます。** 次の「初回セットアップ」は
すべて【ターミナル 1】で実行してください。

### この先で使う Cloud Shell の操作

| やりたいこと | 操作 |
|---|---|
| **新しいターミナルを開く** (このハンズオンで使います) | ターミナル上部のツールバーの **[+]** (新しいタブを開く) をクリック |
| **ファイルを編集する** | `nano <ファイル名>` (保存 = `Ctrl+O` → `Enter`、終了 = `Ctrl+X`)。または `cloudshell edit <ファイル名>` |
| **実行中のコマンドを止める** | そのターミナルで `Ctrl+C` |

> **ホームディレクトリの中身 (clone したリポジトリ・`.env`・venv) は保存されますが、
> ターミナルの「状態」は保存されません。** 新しいタブを開いたときや、しばらく放置して
> 再接続したときは、**ディレクトリ移動 (`cd`) と venv の有効化をやり直す**必要があります。

---

## 初回セットアップ (第5〜8章で 1 回だけ) — 【ターミナル 1】で実行

> **この clone・venv・.env は第5〜8章で共通です。** ここで 1 回だけ作れば、
> 以降の章 (5-B / 6-A / 6-B …) では**作り直さず使い回します**。次章からは
> 「ディレクトリを移動して `pip install -r requirements.txt` するだけ」になります。

### 1. リポジトリを取得して、リポジトリのルートへ移動

```bash
cd ~
git clone https://github.com/trainocate-japan/developing-agentic-ai-with-langchain.git
cd ~/developing-agentic-ai-with-langchain   # ← リポジトリのルート (chap05 などの章フォルダと .env.example がある場所)
```

> リポジトリを `~` (ホームディレクトリ) 以外に clone した場合は、以降に出てくる
> `~/developing-agentic-ai-with-langchain` を実際の場所に読み替えてください。

### 2. リポジトリのルートで仮想環境 (venv) を作って有効化

```bash
python3 -m venv .venv
source .venv/bin/activate
```

プロンプトの先頭に `(.venv)` が付けば成功です。

> この `.venv` は**リポジトリのルートに 1 つだけ**作り、第5〜8章で使い回します
> (章ごとに作り直しません)。**有効化はいつもリポジトリのルートで行います**——
> `chap05/hands-on` などの章フォルダには `.venv` がないため、そこで
> `source .venv/bin/activate` を実行すると `No such file or directory` になります。

### 3. リポジトリのルートで .env を作成し、キーを記入

ルートの `.env.example` を `.env` という名前でコピーし、`OPENAI_API_KEY` と
`LANGSMITH_API_KEY` (第4章で発行したキー) を記入します。

```bash
cp .env.example .env
nano .env          # OPENAI_API_KEY=... と LANGSMITH_API_KEY=... に実際のキーを記入
                   #   → 保存は Ctrl+O → Enter、終了は Ctrl+X
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
cd ~/developing-agentic-ai-with-langchain/chap05/hands-on
pip install -r requirements.txt
```

**ここまでで【ターミナル 1】は「venv が有効 (`(.venv)` 表示) + `chap05/hands-on` にいる」状態です。**
次の実行手順では、この【ターミナル 1】を**閉じずにそのまま使います**。

---

## 実行する (ターミナルを 2 つ使います)

HTTP の weather サーバーは「あらかじめ起動しておく」必要があるため、ターミナルを 2 つ使います。
(stdio の math サーバーはクライアントが自動起動するので、手動起動は不要です)

**新しく開くのは 1 つだけ**です。全体像は次のとおりです。

| | **【ターミナル 1】** | **【ターミナル 2】** |
|---|---|---|
| 用意のしかた | **初回セットアップで使ったターミナルをそのまま使う** (新しく開かない) | ツールバーの **[+]** で**新しく開く** |
| 作業ディレクトリ | `~/developing-agentic-ai-with-langchain/chap05/hands-on` | 同左 (開いた直後はホームなので移動が必要) |
| venv | 有効化済み (`(.venv)` が付いている) | **これから有効化する** |
| 役割 | **weather HTTP サーバーを起動しっぱなしにする** | **クライアントを実行する** |

### ターミナル 1: HTTP サーバーを起動して待ち受ける

初回セットアップの続きなので、**追加の `cd` や venv 有効化は不要**です。そのまま実行します。

```bash
python servers/weather_server.py
```

次のように表示され、`Ctrl+C` で止めるまで起動し続けます。**このターミナルはそのまま**にします。

```
Weather MCP サーバーを起動します: http://127.0.0.1:8000/mcp
(このターミナルは起動したままにし、別ターミナルでクライアントを実行してください)
```

> プロンプトに `(.venv)` が付いていない、または別のディレクトリにいる場合は、
> 下の「**どのターミナルでも通用する 3 行**」を先に実行してから上のコマンドを打ってください。

### ターミナル 2: 新しいターミナルを開いてクライアントを実行する

1. ターミナル上部のツールバーの **[+]** をクリックして、**新しいターミナルタブを開きます**。
2. 新しいタブは **ホームディレクトリ・venv が無効** の状態で開きます。
   そのため、次の 3 行を**必ず**実行してから、クライアントを起動します。

```bash
cd ~/developing-agentic-ai-with-langchain   # ① リポジトリのルートへ
source .venv/bin/activate                   # ② venv を有効化 (ルートで行う)
cd chap05/hands-on                          # ③ このハンズオンのディレクトリへ
python handson_5A_client.py                 # ④ クライアントを実行
```

> **どのターミナルでも通用する 3 行**: 上の ①〜③ は「今どのターミナルにいるか分からなくなったとき」の
> 復帰手順としてもそのまま使えます。すでにルートにいても・すでに venv が有効でも、実行して問題ありません。

### 期待される出力 (例) — 【ターミナル 2】に表示されます

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

### 後片付け

確認が終わったら、**【ターミナル 1】で `Ctrl+C`** を押して weather サーバーを停止します
(起動したままでも次の演習 5-B に進めますが、止めておくとポート 8000 が解放されます)。

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
| `.venv/bin/activate: No such file or directory` | venv の有効化は**リポジトリのルート**で行います。`cd ~/developing-agentic-ai-with-langchain` してから `source .venv/bin/activate` |
| `ModuleNotFoundError: langchain_mcp_adapters` など | プロンプトに `(.venv)` が付いているか (venv が有効か)。付いていなければ「どのターミナルでも通用する 3 行」を実行 |
| `python: command not found` | venv が有効になっていません。同上の 3 行を実行してください (venv を有効化すると `python` が使えます) |
| `get_weather` が取れない / 接続エラー | **【ターミナル 1】** で weather サーバーが起動したままか。URL が `http://127.0.0.1:8000/mcp` か |
| `Address already in use` (ポート 8000) | weather サーバーを二重に起動しています。**【ターミナル 1】** 以外で起動したものを `Ctrl+C` で止める |
| `python: can't open file 'servers/weather_server.py'` | そのターミナルが `chap05/hands-on` にいません。`cd ~/developing-agentic-ai-with-langchain/chap05/hands-on` |
| `OPENAI_API_KEY` 関連のエラー | リポジトリのルートに `.env` を作成し、キーを記入したか (初回セットアップ手順 3) |
| math サーバーが起動しない | `args` のパスは絶対パスか (本コードは `os.path.abspath` で自動解決済み) |

> **実務で Windows を使う場合の参考**: 本ハンズオンは Cloud Shell (Linux) 前提です。
> 実務で Windows から stdio サーバーを起動すると、イベントループ (`NotImplementedError`)・
> `npx` 起動 ("Connection closed")・文字コード (`UnicodeEncodeError`) の 3 つの罠に
> 当たることがあります。対処は教材の早見表を参照してください (Cloud Shell では発生しません)。
