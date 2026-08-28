# 総合演習【正解 (solution)】: ヘルプデスク・マルチエージェント — ヘルプデスク Step 7 (最終)

研修コース「Agentic AI 開発実践 - LangChain 版」/ 第8章「マルチエージェント開発」

このディレクトリは総合演習の**正解 (solution)** です。`capstone_helpdesk_multiagent.py` の
**TODO①〜④** がすべて埋まった完成版です。**まずは `starter/` で自力で挑戦**し、詰まったとき・
答え合わせのときにこちらを参照してください。

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
| 第7章 | 評価 | 回帰評価つき: プロンプト修正の前後を Experiment で比較できる |
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
solution/
├── README.md                          # この説明
├── requirements.txt                   # 依存パッケージ (langgraph-cli[inmem] 含む)
├── helpdesk_tools.py                  # 配布: search_faq / get_system_status / create_ticket / reset_password
├── capstone_helpdesk_multiagent.py    # CLI 版 (TODO①〜④ が完成)。HITL の承認フローを Command(resume) で体験
├── agent.py                           # langgraph dev 用 supervisor (Agent Chat UI)
└── langgraph.json                     # supervisor を登録 ("env" キーなし)
```

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
cd chap08/exercise/solution                 # (3) このディレクトリへ
pip install -r requirements.txt             # (4) 依存をインストール (このディレクトリで 1 回でよい)
```

> - **venv の有効化はリポジトリのルートで行います。** 章のディレクトリには `.venv` がないため、
>   そこで `source .venv/bin/activate` を実行すると `No such file or directory` になります。
> - リポジトリを `~` 以外に clone した場合は、`~/developing-agentic-ai-with-langchain` を実際の場所に読み替えてください。

以降のコマンドは、断りがない限り**すべてこのディレクトリ (`chap08/exercise/solution`) で実行します**。

> **API キー / LangSmith について:** API キーはリポジトリのルートの共通 `.env` に記入済みです
> (5-A で設定)。各スクリプトは先頭で `load_dotenv()` を呼び、ルートの `.env` を読み込みます。
> `LANGSMITH_TRACING=true` により、実行は自動的に LangSmith に記録されます。

---

## 実行する

### 1. CLI 版 (HITL 承認フローを体験)

```bash
python capstone_helpdesk_multiagent.py
```

2 シナリオを順に実行します。

- **シナリオ 1: 「VPN の設定方法を教えて」** → supervisor が `faq` ツールに振り分け、faq_agent が
  `search_faq` で手順を返します (副作用なし、承認なし)。
- **シナリオ 2: 「パスワードをリセットして」** → supervisor が `ops` ツールに振り分け、ops_agent が
  `reset_password` を呼ぼうとした瞬間に **HITL の interrupt で停止**します。承認待ちの中身
  (`action_requests`) を表示し、`Command(resume={"decisions": [{"type": "approve"}]})` で再開して
  リセットを実行します。

実行の最後に**トレース検証シート**が表示されます。LangSmith を開いて記入してください。

### 2. Web アプリとして完成 (Agent Chat UI / langgraph dev) ← 本コースの最終成果物

CLI 版で仕組みを理解したら、同じ supervisor を Web UI から動かします。使うターミナルは
**1 つだけ**で、**UI はブラウザで開くだけ**です (第6章 演習 6-C とまったく同じ流れです)。

| | **【ターミナル】** | **【ブラウザ】** |
|---|---|---|
| 用意のしかた | **CLI 版で使ったターミナルをそのまま使う** | 新しいタブを開くだけ |
| 作業ディレクトリ | `chap08/exercise/solution` (`langgraph.json` がある場所) | — |
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
> (詳細は第6章 6-C の README)。

#### ブラウザ: Agent Chat UI を開いて接続する

1. ブラウザの新しいタブで **<https://agentchat.vercel.app>** を開きます
   (LangChain 公式がホスティングする Agent Chat UI。**インストールも起動も不要**です。
   UI をローカルに立てたい場合は第6章 6-C の README の補足を参照)。
2. 接続設定に次の 3 項目を入力します。

   | 設定項目 | 入力する値 |
   |---|---|
   | **Deployment URL** | 【ターミナル】の **`🚀 API:` に表示された URL** (`https://....trycloudflare.com`)。Web Preview (ポート 2024) の URL は**使えません** |
   | **Graph ID** | `helpdesk` (`langgraph.json` の `graphs` のキー) |
   | **LangSmith API キー** | (空欄で可。ローカル Agent Server への接続では不要) |

   > **`http://localhost:2024` では繋がりません。** Agent Chat UI は**あなたのブラウザの中**で
   > 動いており、そこから見た `localhost` は Cloud Shell ではなく「あなたの PC」を指すためです。

3. ブラウザから 2 シナリオを操作します:
   - 「VPN の設定方法を教えて」→ faq_agent が回答 (承認ダイアログは出ない)。
   - 「パスワードをリセットして」→ ops_agent の reset_password で**承認ダイアログ**が表示される。
     承認するとリセットが実行され、案内が返る。

> **なぜ Web で承認ダイアログが出るのか:** `agent.py` の supervisor には checkpointer を
> 渡していません。`langgraph dev` (Agent Server) が永続化をプラットフォームとして提供し、
> ops_agent (サブグラフ) 内の HITL interrupt の中断・再開を裏で処理してくれるためです
> (第6章と同じ扱い)。

---

## 解答ポイント (TODO①〜④)

すべて `capstone_helpdesk_multiagent.py` の中にあります。`agent.py` は CLI 版の TODO が
埋まった状態と同じ構成 (ただし checkpointer は渡さない) です。

| TODO | 内容 | 解答の要点 |
|---|---|---|
| **①** | 2 体のサブエージェントの構成 | `faq_agent` / `ops_agent` を `create_agent(..., name=...)` で作る。`name` はトレースの識別名。system_prompt に「**結果は必ず最終メッセージに含める**」を明記 (supervisor は最終メッセージしか見ない) |
| **②** | 2 つの `@tool` ラッパー | `@tool("faq", description=...)` / `@tool("ops", description=...)`。description は supervisor のルーティング判断材料なので「**何をするか + いつ使うか**」を具体的に。中で `result["messages"][-1].content` を返す |
| **③** | supervisor の構成 | `create_agent(MODEL, tools=[faq, ops], middleware=[SummarizationMiddleware(...)], checkpointer=InMemorySaver())`。**トップレベルの checkpointer が、ops_agent 内の HITL interrupt を伝播・再開する基盤**になる (下記参照) |
| **④** | ops_agent の HITL | `HumanInTheLoopMiddleware(interrupt_on={"reset_password": {"allowed_decisions": ["approve","reject"]}, "create_ticket": {"allowed_decisions": ["approve","edit","reject"]}})`。reset は高リスクなので edit を許さない |

### なぜ checkpointer は「supervisor だけ」に置くのか (この演習の肝)

HITL の interrupt は LangGraph の永続化層 (checkpointer) に依存します。reset_password の承認待ちで
止め、後で `Command(resume=...)` で再開するには、止まった時点の state が保存されている必要があります。

ここで重要なのは、**ops_agent は supervisor の「ツールの中」で invoke されるサブグラフ (subgraph)**
だという点です。サブエージェントには checkpointer を渡しません (Subagents は stateless が原則)。
サブグラフは既定で「継承 (inherited) チェックポインタ」モードで動くため、ops_agent 内で発生した
interrupt は、**トップレベルの supervisor が持つ checkpointer によって保存・再開**されます。

つまり「**supervisor の 1 つの checkpointer が、入れ子の ops_agent の HITL 中断・再開までまとめて
面倒を見る**」——これが、checkpointer を supervisor だけに置く理由です。HITL の API
(`version="v2"` / `result.interrupts` / `Command(resume=...)`) は第6章 演習 6-C と同一です。

---

## トレース検証シート (期待成果物の 1 つ)

CLI 版の実行末尾に表示される検証シートを、LangSmith のトレースを読んで記入してください。読むべきは
**[1] 入れ子構造**、**[2] name による識別**、**[3] モデル呼び出し回数**、**[4] HITL interrupt の伝播**、
**[5] stateless との接続**の 5 点です。これが期待成果物「トレース検証シート」になります。

> シナリオ 1 のモデル呼び出しは 4 回が目安 (① faq 使用を決定 → ②③ サブ内で検索・要約 → ④ 最終応答)。
> Subagents がサブの結果を必ず supervisor 経由で返す「集中制御の対価」の実測です。

---

## 期待成果物 (この総合演習のゴール)

- **Agent Chat UI (Web UI) から操作できるヘルプデスク・マルチエージェント (完成版 v5)**。
  「VPN の設定方法を教えて」(→ faq_agent) と「パスワードをリセットして」(→ ops_agent + 承認ダイアログ)
  の 2 シナリオがブラウザから動く。
- **トレース検証シート** (入れ子構造・name・呼出回数・HITL 伝播・stateless の 5 点を記入)。

---

## (発展 1) Single dispatch tool 方式への書き換え

`capstone_helpdesk_multiagent.py` の末尾に、`task(agent_name, description)` + レジストリ (`SUBAGENTS`)
による**単一ディスパッチ版** (`build_supervisor_single_dispatch`) を用意しています。サブ 1 体につき
ツール 1 つの「tool per agent」方式に対し、単一ディスパッチは**新しいサブの追加がレジストリ登録だけ**で
済むため、サブが多数・複数チームで分散開発する場合に有効です。supervisor へサブを知らせる方法は
「system prompt への列挙 / Enum 制約 / ツールによる動的発見」の 3 つがあり、ここでは最も簡単な
列挙を使っています。

## (発展 2) faq_agent を MCP ナレッジに差し替える

この演習で faq_agent はローカルの `search_faq` を使っていますが、本来の設計意図では faq_agent は
「ナレッジ担当」で、**第5章 (ヘルプデスク Step 4) で構築した MCP ナレッジサーバー**に対応します。

- **なぜ今はローカルなのか**: 総合演習は HITL + Middleware + Checkpointer + マルチエージェント +
  Agent Chat UI を統合する集大成です。ここに MCP (async) まで同時に組むと、`langgraph dev` や
  HITL の interrupt 伝播との相互作用が壊れやすく、検証が難しくなります。そこで capstone 全体を
  **同期 (invoke / Command(resume))** で実装し、堅牢に保っています。
- **差し替え方 (概略)**: `MultiServerMCPClient` で MCP ナレッジサーバーに接続し、`get_tools()` で
  取得したツールを faq_agent の `tools` に渡します。その場合 faq_agent は `ainvoke` (async) になり、
  faq ラッパーと supervisor も async 化が必要です。詳しくは第5章 演習 5-B を参照してください。

---

## トラブルシューティング

| 症状 | 確認すること |
|---|---|
| `OPENAI_API_KEY` 関連のエラー | リポジトリのルートの `.env` に `OPENAI_API_KEY` を記入したか (5-A の手順) |
| interrupt 後に再開できない (CLI) | supervisor に checkpointer を渡したか (TODO③)。再開時の thread_id が中断時と同じか |
| Agent Chat UI で承認ダイアログが出ない | `agent.py` の ops_agent に HITL を付けたか。`langgraph dev` でサーバーが起動しているか |
| サブが呼ばれない / 呼び分けが変 | `@tool` の description が具体的か (TODO②)。supervisor の system_prompt の振り分け指示を確認 |
| サブが「対応しました」だけ返す | サブの system_prompt に「結果は必ず最終メッセージに含める」を書いたか (TODO①) |
| UI から Agent Server に繋がらない (`Failed to connect...`) | Deployment URL に `http://localhost:2024` や Web Preview (ポート 2024) の URL を入れていないか。`--tunnel` で発行された `https://....trycloudflare.com` を使う。Graph ID は `helpdesk` か |
| `langgraph: command not found` | venv が有効か (`(.venv)` 表示)。`pip install -U "langgraph-cli[inmem]"` を実行したか |

> **`.env` と `__pycache__/` はコミットしないでください。** `.env` はリポジトリのルートに 1 つだけ置きます。
