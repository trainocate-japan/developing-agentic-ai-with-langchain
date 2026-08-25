# 演習 5-B【演習 (starter)】: 社内ナレッジ MCP サーバーの接続 — ヘルプデスク Step 4

研修コース「LangChain による Agentic AI 開発実践」/ 第5章「MCP サーバーの利用」

`exercise_5B_helpdesk.py` の中にある **TODO①・TODO②** を自分で埋めて、
ヘルプデスクエージェント **v3** を完成させる演習です。
詰まったとき・答え合わせのときは `../solution/` を参照してください。

---

## 演習の狙い (対応する章目標 2・3・4)

- **章目標 2**: `MultiServerMCPClient` で MCP サーバーからツールを取得し、`create_agent` に接続する
- **章目標 3**: stdio transport の接続設定 (`command` / `args` の絶対パス指定) を書ける
- **章目標 4**: デフォルトのステートレス動作を理解する (発展課題で `client.session()` に触れる)

あわせて、配布された **async の骨格** (`async def main` / `await` / `asyncio.run` / `ainvoke`) を
コードリーディングし、「`await` が付いている箇所」と「`invoke` ではなく `ainvoke` を使う理由」を
自分の言葉で説明できることを確認します。

---

## ヘルプデスク Step 4 の位置づけ (search_faq 廃止 → MCP 調達 v3)

本コースの演習は「社内 IT ヘルプデスクエージェント」を段階的に拡張します。本演習はその **Step 4**。

| 章 | 追加する要素 | 演習後の姿 |
|---|---|---|
| 第3章 | create_agent / @tool / 構造化出力 | FAQ 検索 + 稼働状況ツールを持つ単体エージェント (v1) |
| 第4章 | Checkpointer / LangSmith | 社員ごとに会話を記憶するエージェント (v2) |
| **第5章 (この演習)** | **MCP** | **FAQ を MCP サーバーから調達するエージェント (v3)** |

これまで**自前のコード**で持っていた FAQ 検索 (`search_faq`) を廃止し、情報システム部門が公開した
**社内ナレッジ MCP サーバー**から FAQ ツールを「調達」します。
一方、稼働状況ツール `get_system_status` は**自作 `@tool` のまま手元に残します**。
v3 は「**MCP で借りたツール + 自作ツール**」を 1 つの `tools` リストに混在させたエージェントです。

---

## ファイル構成

```
starter/
├── README.md                    # この説明
├── requirements.txt             # 依存パッケージ (ピン留め済み)
├── servers/
│   └── knowledge_server.py      # 社内ナレッジ MCP サーバー (配布・完成版。編集不要)
└── exercise_5B_helpdesk.py      # ← あなたが TODO①② を埋めるファイル
```

- `servers/knowledge_server.py` は**情報システム部門が用意した既製品**という想定の配布物です。
  編集する必要はありません。
- `get_system_status` (自作ツール)・async の骨格・実行部分も**すべて記述済み**です。

---

## セットアップ

第5章ハンズオン (5-A) で、リポジトリの clone・venv 作成・.env 設定 (OpenAI + LangSmith) は
完了している前提です。まだの場合は 5-A の手順を先に実施してください。

1. (同じターミナルセッションなら venv は有効なまま。新しいタブの場合は) リポジトリ直下の venv を有効化:
   ```bash
   source <リポジトリ>/.venv/bin/activate
   ```
2. このディレクトリへ移動:
   ```bash
   cd <リポジトリ>/chap05/exercise/starter
   ```
3. このディレクトリの依存を追加インストール (前章までと共通なら差分のみ入ります):
   ```bash
   pip install -r requirements.txt
   ```
4. 実行 (LangSmith は 5-A で設定済みのルート `.env` により自動で有効。トレースは
   [smith.langchain.com](https://smith.langchain.com) で確認できます)。

> ナレッジサーバーは **stdio** なので、HTTP サーバーのような「別ターミナルで先に起動」は
> 不要です。クライアントが自動でサブプロセス起動します。

---

## やること: TODO①・TODO② を埋める

`exercise_5B_helpdesk.py` を開き、`async def main()` の中の 2 か所を埋めます。

### TODO①: `MultiServerMCPClient` の接続設定 (stdio transport)

サーバー名 `"knowledge"` をキーにした接続設定の辞書を書きます。必要なキーは 3 つ:

- `"transport"`: stdio で接続することを表す値
- `"command"` : サーバーを起動するコマンド (Python スクリプトを動かすコマンド)
- `"args"`   : 起動するスクリプトのパスのリスト

> **ヒント**: `args` はサーバースクリプトの**絶対パス**で指定します
> (`os.path.abspath` が便利)。ファイル冒頭で用意済みの `KNOWLEDGE_SERVER_PATH` を
> リストに入れて使ってください。相対パスだと実行ディレクトリ次第で起動に失敗します。

### TODO②: `get_tools()` の呼び出しと、自作ツールとの結合

- (1) `client` から MCP ツールを取得します。**`await` はすでに書いてあります**——
  あなたが書くのは `await` の右側、「ツールを取得するメソッド呼び出し」だけです。
  > **ヒント**: クライアントの `get_tools()` を呼びます (全サーバーのツールを一括取得)。
- (2) MCP ツールと手元の自作ツールを結合します。
  > **ヒント**: ツールリストは Python のリスト結合で混在できます
  > (`mcp_tools + [get_system_status]`)。

> **async 構文は埋めません**。`await` / `ainvoke` / `asyncio.run` は最初から書かれています。
> TODO は MCP の学習対象 (接続設定・ツール取得・結合) だけです。

---

## 実行と期待される成果物

```bash
python exercise_5B_helpdesk.py
```

### 期待される出力 (例)

```
使用するツール: ['search_faq', 'get_document', 'get_system_status']

=== 最終回答 ===
経費精算は経費精算システムから申請します（領収書は PDF で添付、月末締め翌月 10 日払い）。
なお勤怠システムは現在「正常稼働中」です。

=== 呼ばれたツール (軌跡) ===
  - search_faq({'keyword': '経費精算'})
  - get_system_status({'service': '勤怠システム'})
```

**期待する成果物**: 「経費精算のやり方を教えて。あと勤怠システムは動いてる?」という 1 つの質問に対し、
**FAQ (MCP ツール)** と **稼働状況 (自作ツール)** の**両方**を呼ぶヘルプデスク v3。

---

## 完成の目安 (チェックリスト)

- [ ] `使用するツール` に `search_faq` / `get_document` / `get_system_status` が並ぶ
- [ ] 最終回答に「経費精算のやり方」と「勤怠システムの稼働状況」の両方が含まれる
- [ ] 軌跡に MCP ツール (`search_faq`) と自作ツール (`get_system_status`) の両方の呼び出しが出る
- [ ] (説明) `await` が付いている箇所と、`ainvoke` を使う理由を自分の言葉で言える

---

## (発展) ステートフル版に挑戦する

デフォルトの `get_tools()` は「ステートレス」で、ツールを呼ぶたびに MCP セッションを生成・破棄します
(stdio ではサーバープロセスが毎回起動・終了)。`client.session()` で永続セッションを張ると、
ブロックの間はプロセスが起動したままになり、セッションを再利用できます。

完成版 (`../solution/exercise_5B_helpdesk.py`) には `main_stateful()` という
ステートフル版 (`client.session()` + `load_mcp_tools`) が用意されています。
それを参考に、応答速度の違いを体感してみましょう。

---

## トラブルシューティング

| 症状 | 確認すること |
|---|---|
| ツールが取れない / 接続エラー | TODO① の `args` は絶対パス (`KNOWLEDGE_SERVER_PATH`) を渡しているか |
| `OPENAI_API_KEY` 関連のエラー | リポジトリのルートに `.env` を作成し、キーを記入したか (5-A のセットアップ) |
| FAQ は呼ばれるが稼働状況が呼ばれない | TODO②-(2) で `tools` に `get_system_status` を結合できているか |
| `NameError` などで止まる | TODO 内の `___` (穴) をすべて実際のコードに置き換えたか |

> **実務で Windows を使う場合の参考**: 本演習は Cloud Shell (Linux) 前提です。
> Windows で stdio サーバーを起動するとイベントループ等の固有の罠があります
> (詳細は教材の早見表を参照。Cloud Shell では発生しません)。
