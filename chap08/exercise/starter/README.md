# 総合演習【演習 (starter)】: ヘルプデスク・マルチエージェント — ヘルプデスク Step 7 (最終)

研修コース「Agentic AI 開発実践 - LangChain 版」/ 第8章「マルチエージェント開発」

このディレクトリは総合演習の**演習用 (starter)** です。`capstone_helpdesk_multiagent.py` の
**TODO①〜④** を自分で埋めて、ヘルプデスク・マルチエージェント (v5) を完成させてください。
完成版は `solution/` にあります。まずは自力で挑戦しましょう。

---

## 総合演習の狙い (コース全体目標 2・3・4・5 を統合)

これは**コースの集大成**です。第1章から積み上げてきたすべての要素を 1 つに組み合わせます。

- **目標 2** (create_agent で単体エージェント): faq_agent / ops_agent / supervisor を構成
- **目標 3** (Middleware・MCP・HITL): supervisor に Summarization、ops_agent に HITL
- **目標 4** (LangSmith で評価): supervisor → サブエージェントの入れ子をトレースで読む
- **目標 5** (マルチエージェントの比較・選択・実装): Subagents 型を実装する

最後は `langgraph dev` で起動して **Agent Chat UI (Web Preview) から操作できる Web アプリ**として
完成させます。これが本コースの最終成果物「**Web UI から操作できるヘルプデスク・マルチエージェント
(完成版 v5)**」です。

---

## ヘルプデスク Step 7 の位置づけ (最終形)

| 章 | 追加する要素 | 演習後の姿 |
|---|---|---|
| 第6章 | Middleware / HITL / Agent Chat UI | PII 保護 + 要承認 + ブラウザ操作 (v4) |
| 第7章 | 評価 | トラジェクトリ評価による回帰テスト付き |
| **第8章 (この総合演習)** | **Multi-agent** | **FAQ 担当・オペレーション担当を束ねる supervisor (v5)。Agent Chat UI から操作できる Web アプリとして完成** |

```
ユーザー
   │
   ▼
supervisor (司令塔)
 ├── faq ツール → faq_agent (search_faq / get_system_status)        … 読み取り系・承認不要
 └── ops ツール → ops_agent (create_ticket / reset_password + HITL)  … 副作用あり・要承認
```

---

## ファイル構成

```
starter/
├── README.md                          # この説明
├── requirements.txt                   # 依存パッケージ (langgraph-cli[inmem] 含む)
├── helpdesk_tools.py                  # 配布: search_faq / get_system_status / create_ticket / reset_password
├── capstone_helpdesk_multiagent.py    # CLI 版。★TODO①〜④ をあなたが埋める
├── agent.py                           # langgraph dev 用 supervisor (完成状態で配布)
└── langgraph.json                     # supervisor を登録 ("env" キーなし)
```

- あなたが編集するのは **`capstone_helpdesk_multiagent.py` の TODO①〜④** だけです。
- 2 シナリオの実行・interrupt の resume・トレース検証シートの骨格は**完成状態**で配布しています。
- `agent.py` は Agent Chat UI 用に完成状態で配布しています (CLI 版で仕組みを理解してから起動します)。

---

## セットアップ (第5章ハンズオン 5-A の続き)

実行環境は **Google Cloud Shell** (Linux) です。**第5章ハンズオン (5-A) で、リポジトリの
clone・仮想環境 (venv) の作成・`.env` の設定 (OpenAI + LangSmith) は完了している前提**です
(本演習はそこに新しい clone や `.env` 作成を足しません)。

ブラウザで **<https://shell.cloud.google.com/>** を開き (Cloud Shell を開く手順は
第5章ハンズオン 5-A の README「ステップ 0」を参照)、ターミナルで次の 4 行を上から順に実行します。
**新しいターミナルを開いた直後や、しばらく放置して再接続したあとも、この 4 行をそのまま実行すれば
作業を再開できます。**

```bash
cd ~/developing-agentic-ai-with-langchain   # (1) リポジトリのルートへ
source .venv/bin/activate                   # (2) venv を有効化 (必ずルートで。プロンプトに (.venv) が付く)
cd chap08/exercise/starter                  # (3) このディレクトリへ
pip install -r requirements.txt             # (4) 依存をインストール (このディレクトリで 1 回でよい)
```

> - **venv の有効化はリポジトリのルートで行います。** 章のディレクトリには `.venv` がないため、
>   そこで `source .venv/bin/activate` を実行すると `No such file or directory` になります。
> - リポジトリを `~` 以外に clone した場合は、`~/developing-agentic-ai-with-langchain` を実際の場所に読み替えてください。

以降のコマンドは、断りがない限り**すべてこのディレクトリ (`chap08/exercise/starter`) で実行します**。

> **API キー / LangSmith について:** API キーはリポジトリのルートの共通 `.env` に記入済みです
> (5-A で設定)。各スクリプトは先頭で `load_dotenv()` を呼び、ルートの `.env` を読み込みます。
> `LANGSMITH_TRACING=true` により、実行は自動的に LangSmith に記録されます。

---

## TODO①〜④ とヒント

すべて `capstone_helpdesk_multiagent.py` の中にあります。コメントの「★TODO」を順に埋めてください。

### TODO①: 2 体のサブエージェントを構成する (`faq_agent` / `ops_agent`)

`create_agent(...)` で 2 体を作ります。**2 つの必須ポイント**:

- **`name` 引数**を付ける (`name="faq_agent"` / `name="ops_agent"`)。LangSmith トレースの表示名になり、
  入れ子のどれがどのサブか識別できるようになります。
- **system_prompt に「結果は必ず最終メッセージに含める」を明記**する。supervisor に返るのは
  サブの**最終メッセージの content だけ**です。これを書かないと「対応しました」とだけ返り、
  肝心の中身が消える典型的な失敗 (空の報告) が起きます。
- `faq_agent` は `tools=[search_faq, get_system_status]`、`ops_agent` は
  `tools=[create_ticket, reset_password]` と `middleware=[ops_hitl]` (TODO④ で作るもの)。

### TODO②: 2 体のサブエージェントを `@tool` でラップする

`call_faq_agent` / `call_ops_agent` を完成させます。

- `@tool("faq", description=...)` / `@tool("ops", description=...)` の **description は supervisor の
  ルーティング判断材料**です。「**何をするか + いつ使うか**」を具体的に書きます
  (悪い例: `"エージェントを呼ぶ"` ← いつ使うか分からない)。
- 関数の中でサブを `invoke` し、**`result["messages"][-1].content`** (最終メッセージだけ) を返します。

### TODO③: supervisor を構成する (`build_supervisor`)

`create_agent(...)` で supervisor を作って `return` します。

- `tools=[call_faq_agent, call_ops_agent]` … 2 つのラッパーツール。
- `middleware=[SummarizationMiddleware(model=MODEL, trigger=("tokens", 4000), keep=("messages", 20))]`
  … 長い会話を要約に置き換える (`PIIMiddleware` に差し替えても可)。
- **`checkpointer=InMemorySaver()`** … この演習の肝。**トップレベルの checkpointer が、
  ops_agent 内の HITL interrupt を伝播・再開する基盤**になります (下記参照)。

### TODO④: ops_agent 用の `HumanInTheLoopMiddleware` を構成する (`ops_hitl`)

副作用ツールを呼ぶ瞬間に止めて承認を待たせます (第6章 演習 6-B と同じ API)。

- `interrupt_on={"reset_password": {"allowed_decisions": ["approve", "reject"]},
  "create_ticket": {"allowed_decisions": ["approve", "edit", "reject"]}}`
- reset_password は高リスクなので **edit を許さない** (approve / reject のみ)。

### なぜ checkpointer は「supervisor だけ」に置くのか (この演習の肝)

ops_agent は supervisor の「ツールの中」で invoke される**サブグラフ (subgraph)** です。サブには
checkpointer を渡しません (Subagents は stateless が原則)。サブグラフは既定で「継承 (inherited)
チェックポインタ」モードで動くため、ops_agent 内で発生した HITL の interrupt は、**トップレベルの
supervisor が持つ checkpointer によって保存・再開**されます。「supervisor の 1 つの checkpointer が、
入れ子の ops_agent の HITL 中断・再開までまとめて面倒を見る」——これが理由です。

---

## 実行する

### 1. CLI 版 (TODO①〜④ を埋めてから)

```bash
python capstone_helpdesk_multiagent.py
```

- **シナリオ 1: 「VPN の設定方法を教えて」** → supervisor が faq_agent に振り分け、手順が返る (承認なし)。
- **シナリオ 2: 「パスワードをリセットして」** → ops_agent の reset_password で **interrupt 停止** →
  `Command(resume={"decisions": [{"type": "approve"}]})` で承認して実行。

実行の最後に**トレース検証シート**が表示されます。LangSmith を開いて記入してください
(これが期待成果物の 1 つです)。

### 2. Web アプリとして完成 (Agent Chat UI / langgraph dev) ← 本コースの最終成果物

CLI 版で仕組みを理解したら、同じ supervisor を Web UI から動かします。使うターミナルは
**1 つだけ**で、**UI はブラウザで開くだけ**です (第6章 演習 6-B とまったく同じ流れです)。

| | **【ターミナル】** | **【ブラウザ】** |
|---|---|---|
| 用意のしかた | **CLI 版で使ったターミナルをそのまま使う** | 新しいタブを開くだけ |
| 作業ディレクトリ | `chap08/exercise/starter` (`langgraph.json` がある場所) | — |
| venv | 有効化済み (`(.venv)` が付いている) | — |
| 役割 | **Agent Server を起動しっぱなしにする** | **Agent Chat UI (ホステッド版) を開く** |

#### ターミナル: Agent Server を起動する

CLI 版の続きなので、**追加の `cd` や venv 有効化は不要**です
(ターミナルを開き直した場合は「セットアップ」の 4 行を先に実行してください)。

```bash
langgraph dev --tunnel
```

`langgraph dev` が `agent.py` の `supervisor` を読み込み、ローカルの Agent Server を起動します。
起動後のバナーの **`🚀 API:` の行**に出る URL
(`https://....trycloudflare.com`) を**コピー**しておきます
(`--tunnel` を付けると、API の URL がそのまま Tunnel の公開 URL になります。
付けない場合は `http://127.0.0.1:2024` と表示され、UI からは接続できません)。
**このターミナルは `Ctrl+C` で止めるまでそのまま**にします。

> **Cloud Shell の Web Preview でポート 2024 を公開した URL は使えません。**
> あなたのユーザーアカウントでの認証が必要な URL のため、Agent Chat UI からの呼び出しは弾かれます
> (詳細は第6章 6-B の README)。

#### ブラウザ: Agent Chat UI を開いて接続する

1. ブラウザの新しいタブで **<https://agentchat.vercel.app>** を開きます
   (LangChain 公式がホスティングする Agent Chat UI。**インストールも起動も不要**です。
   UI をローカルに立てたい場合は第6章 6-B の README の補足を参照)。
2. 接続設定に次の 3 項目を入力します。

   | 設定項目 | 入力する値 |
   |---|---|
   | **Deployment URL** | 【ターミナル】の **`🚀 API:` に表示された URL** (`https://....trycloudflare.com`)。Web Preview (ポート 2024) の URL は**使えません** |
   | **Graph ID** | `helpdesk` (`langgraph.json` の `graphs` のキー) |
   | **LangSmith API キー** | (空欄で可。ローカル Agent Server への接続では不要) |

   > **`http://localhost:2024` では繋がりません。** Agent Chat UI は**あなたのブラウザの中**で
   > 動いており、そこから見た `localhost` は Cloud Shell ではなく「あなたの PC」を指すためです。

3. ブラウザから 2 シナリオを操作します。「パスワードをリセットして」では **承認ダイアログ**が
   出るので、承認するとリセットが実行されます。

> **なぜ Web で承認ダイアログが出るのか:** `agent.py` の supervisor には checkpointer を
> 渡していません。`langgraph dev` (Agent Server) が永続化をプラットフォームとして提供し、
> ops_agent 内の HITL interrupt の中断・再開を裏で処理するためです (第6章と同じ扱い)。

---

## 期待成果物 (この総合演習のゴール)

- **Agent Chat UI (Web UI) から操作できるヘルプデスク・マルチエージェント (完成版 v5)**。
  「VPN の設定方法を教えて」(→ faq_agent) と「パスワードをリセットして」(→ ops_agent + 承認ダイアログ)
  の 2 シナリオがブラウザから動く。
- **トレース検証シート** (入れ子構造・name・呼出回数・HITL 伝播・stateless の 5 点を記入)。

---

## (発展) さらに先へ

- **Single dispatch tool 方式**: サブ 1 体につきツール 1 つ (tool per agent) ではなく、
  `task(agent_name, description)` + レジストリの単一ツールに書き換える。サブの追加がレジストリ登録
  だけで済む。解答例は `solution/capstone_helpdesk_multiagent.py` の末尾を参照。
- **faq_agent を MCP ナレッジに差し替える**: faq_agent は本来「ナレッジ担当」で、第5章で作った
  MCP ナレッジサーバーに対応します。`MultiServerMCPClient` で接続して `get_tools()` のツールを
  faq_agent に渡せば差し替えられます (その場合 faq_agent は async になり、ラッパーと supervisor も
  async 化が必要)。今ローカルツールにしているのは、HITL + Checkpointer + Agent Chat UI を統合する
  集大成で MCP (async) の相互作用を避け、capstone 全体を同期で堅牢に保つためです (詳細は solution README)。

---

## トラブルシューティング

| 症状 | 確認すること |
|---|---|
| `NotImplementedError: TODO...` | 対応する TODO をまだ埋めていない。エラーメッセージの番号の箇所を完成させる |
| `AttributeError: 'NoneType' ... invoke` | TODO① で faq_agent / ops_agent を `None` のままにしている。create_agent(...) を書く |
| interrupt 後に再開できない (CLI) | TODO③ で supervisor に checkpointer を渡したか。再開時の thread_id が中断時と同じか |
| Agent Chat UI で承認ダイアログが出ない | 【ターミナル】で `langgraph dev` が起動したままか。Graph ID は `helpdesk` か |
| UI から Agent Server に繋がらない (`Failed to connect...`) | Deployment URL に `http://localhost:2024` や Web Preview (ポート 2024) の URL を入れていないか。`--tunnel` で発行された `https://....trycloudflare.com` を使う |
| `langgraph: command not found` | venv が有効か (`(.venv)` 表示)。`pip install -U "langgraph-cli[inmem]"` を実行したか |
| サブが呼ばれない / 呼び分けが変 | TODO② の description が具体的か。supervisor の system_prompt の振り分け指示を確認 |
| サブが「対応しました」だけ返す | TODO① でサブの system_prompt に「結果は必ず最終メッセージに含める」を書いたか |
| `OPENAI_API_KEY` 関連のエラー | リポジトリのルートの `.env` に `OPENAI_API_KEY` を記入したか (5-A の手順) |

> **`.env` と `__pycache__/` はコミットしないでください。** `.env` はリポジトリのルートに 1 つだけ置きます。
