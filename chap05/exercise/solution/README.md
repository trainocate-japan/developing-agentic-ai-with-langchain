# 演習 5-B【正解 (solution)】: 社内ナレッジ MCP サーバーの接続 — ヘルプデスク Step 4

研修コース「Agentic AI 開発実践 - LangChain 版」/ 第5章「MCP サーバーの利用」

このディレクトリは演習 5-B の**正解 (solution)** です。
`exercise_5B_helpdesk.py` は TODO がすべて埋まった完成版です。
**まずは `starter/` で自力で挑戦**し、詰まったとき・答え合わせのときにこちらを参照してください。

---

## 演習の狙い (対応する章目標 2・3・4)

- **章目標 2**: `MultiServerMCPClient` で MCP サーバーからツールを取得し、`create_agent` に接続する
- **章目標 3**: stdio transport の接続設定 (`command` / `args` の絶対パス指定) を書ける
- **章目標 4**: デフォルトのステートレス動作を理解し、発展課題で `client.session()` による
  ステートフル化を試す

あわせて、配布された **async の骨格** (`async def main` / `await` / `asyncio.run` / `ainvoke`) を
コードリーディングし、「`await` が付いている箇所」と「`invoke` ではなく `ainvoke` を使う理由」を
説明できることを確認します。

---

## ヘルプデスク Step 4 の位置づけ (search_faq 廃止 → MCP 調達 v3)

本コースの演習は「社内 IT ヘルプデスクエージェント」を段階的に拡張します。本演習はその **Step 4**。

| 章 | 追加する要素 | 演習後の姿 |
|---|---|---|
| 第3章 | create_agent / @tool / 構造化出力 | FAQ 検索 + 稼働状況ツールを持つ単体エージェント (v1) |
| 第4章 | Checkpointer / LangSmith | 社員ごとに会話を記憶するエージェント (v2) |
| **第5章 (この演習)** | **MCP** | **FAQ を MCP サーバーから調達するエージェント (v3)** |

これまで**自前のコード**で持っていた FAQ 検索 (`search_faq`) を廃止し、情報システム部門が公開した
**社内ナレッジ MCP サーバー**から FAQ ツールを「調達」する構成に切り替えます。
一方、稼働状況ツール `get_system_status` は**自作 `@tool` のまま手元に残します**。
こうして v3 は「**MCP で借りたツール + 自作ツール**」を 1 つの `tools` リストに混在させた
エージェントになります。

---

## ファイル構成

```
solution/
├── README.md                    # この説明
├── requirements.txt             # 依存パッケージ (ピン留め済み)
├── servers/
│   └── knowledge_server.py      # 社内ナレッジ MCP サーバー (配布・完成版)
└── exercise_5B_helpdesk.py      # ヘルプデスク v3 (完成版)
```

- `servers/knowledge_server.py` は**情報システム部門が用意した既製品**という想定の配布物です。
  FAQ 検索 (`search_faq`) と文書取得 (`get_document`) の 2 ツールを公開します。受講者は編集しません。
- `exercise_5B_helpdesk.py` がクライアント側 (受講者が starter で編集する対象) です。

---

## セットアップと実行

第5章ハンズオン (5-A) で、リポジトリの clone・venv 作成・.env 設定 (OpenAI + LangSmith) は
完了している前提です。まだの場合は 5-A の手順を先に実施してください。

1. (同じターミナルセッションなら venv は有効なまま。新しいタブの場合は) リポジトリ直下の venv を有効化:
   ```bash
   source <リポジトリ>/.venv/bin/activate
   ```
2. このディレクトリへ移動:
   ```bash
   cd <リポジトリ>/chap05/exercise/solution
   ```
3. このディレクトリの依存を追加インストール (前章までと共通なら差分のみ入ります):
   ```bash
   pip install -r requirements.txt
   ```
4. 実行 (ナレッジサーバーは stdio なので手動起動は不要。自動で起動される。LangSmith は
   5-A で設定済みのルート `.env` により自動で有効。トレースは
   [smith.langchain.com](https://smith.langchain.com) で確認できます):
   ```bash
   python exercise_5B_helpdesk.py
   ```

> ハンズオン 5-A と違い、ナレッジサーバーは **stdio** なので、HTTP サーバーのような
> 「別ターミナルで先に起動」は不要です。クライアントが自動でサブプロセス起動します。

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

「経費精算のやり方を教えて。あと勤怠システムは動いてる?」という 1 つの質問に対し、
**FAQ (MCP ツール)** と **稼働状況 (自作ツール)** の**両方**が呼ばれていれば成功です。

---

## TODO の解答ポイント

| 解答 | 内容 |
|---|---|
| 解答① | `MultiServerMCPClient({"knowledge": {"transport": "stdio", "command": "python", "args": [絶対パス]}})`。`args` は `os.path.abspath` で求めた絶対パスを渡す |
| 解答② | `mcp_tools = await client.get_tools()` で MCP ツールを取得し、`tools = mcp_tools + [get_system_status]` で自作ツールと結合 |

`await` / `ainvoke` / `asyncio.run` などの async 構文は**最初から記述済み**で、TODO ではありません。

---

## (発展) ステートフル版で応答速度を体感する

`exercise_5B_helpdesk.py` には `main_stateful()` を用意してあります。
これは `client.session()` で永続セッションを張り、`load_mcp_tools(session)` でツールをロードする
**ステートフル版**です。

- **デフォルト (`get_tools()`)**: ツール呼び出しのたびにセッションを生成・破棄。
  stdio ではサーバープロセスが毎回起動・終了する (高頻度だと遅い)。
- **ステートフル (`client.session()` + `load_mcp_tools`)**: `async with` ブロックの間は
  サーバープロセスが起動したままで、セッションを再利用する。

試すには、ファイル末尾の `asyncio.run(main())` をコメントアウトし、
`asyncio.run(main_stateful())` を有効にして実行を比べてください。

---

## トラブルシューティング

| 症状 | 確認すること |
|---|---|
| ツールが取れない / 接続エラー | `args` のパスは絶対パスか (本コードは `os.path.abspath` で自動解決済み) |
| `OPENAI_API_KEY` 関連のエラー | リポジトリのルートに `.env` を作成し、キーを記入したか (5-A のセットアップ) |
| FAQ は呼ばれるが稼働状況が呼ばれない | `tools` に `get_system_status` を結合できているか (解答②) |

> **実務で Windows を使う場合の参考**: 本演習は Cloud Shell (Linux) 前提です。
> Windows で stdio サーバーを起動するとイベントループ等の固有の罠があります
> (詳細は教材の早見表を参照。Cloud Shell では発生しません)。
