# 演習 6-B【正解 (solution)】: 要承認オペレーションの実装 — ヘルプデスク Step 5

研修コース「Agentic AI 開発実践 - LangChain 版」/ 第6章「Middleware と HITL」

このディレクトリは演習 6-B の**正解 (solution)** です。
`exercise_6B_hitl.py` (CLI 版) は TODO がすべて埋まった完成版、`agent.py` + `langgraph.json` は
Agent Chat UI からブラウザ操作するための完成版です。
**まずは `starter/` で自力で挑戦**し、詰まったとき・答え合わせのときにこちらを参照してください。

---

## 演習の狙い (対応する章目標 2・4・5)

- **章目標 2**: `create_agent` に Middleware を組み込み、PII 保護 + 要承認オペレーションを備えた v4 を実装する
- **章目標 4**: `HumanInTheLoopMiddleware` と `Command(resume=...)` で、approve / reject の承認フローを実装する
- **章目標 5**: `langgraph dev` + Agent Chat UI で、同じ承認フローをブラウザの承認ダイアログから操作する

完成すると、**PII (メールアドレス) を保護**し、**チケット起票・パスワードリセットは人間の承認まで実行しない**、
かつ **Agent Chat UI の承認ダイアログから操作できる**ヘルプデスクエージェント **v4** が手に入ります。

---

## ヘルプデスク Step 5 の位置づけ (PII + 要承認 → v4)

| 章 | 追加する要素 | 演習後の姿 |
|---|---|---|
| 第4章 | Checkpointer / LangSmith | 社員ごとに会話を記憶するエージェント (v2) |
| 第5章 | MCP | FAQ を MCP サーバーから調達するエージェント (v3) |
| **第6章 (この演習)** | **Middleware / HITL / Agent Chat UI** | **PII 保護 + 要承認オペレーション + ブラウザ操作 (v4)** |

> **このエージェントは使い捨てではありません。** 第7章 (評価)・第8章 (マルチエージェント) でも、
> ここで作った「Agent Chat UI から操作できるエージェント」を土台に拡張していきます。

---

## ファイル構成

```
solution/
├── README.md                 # この説明
├── requirements.txt          # 依存パッケージ (langgraph-cli[inmem] 含む)
├── helpdesk_tools.py         # 配布: search_faq / get_system_status / create_ticket / reset_password
├── exercise_6B_hitl.py       # CLI 版: HITL 承認フロー (完成版・TODO①〜④ 埋め済み)
├── agent.py                  # Agent Chat UI 用: langgraph dev が読むエージェント定義
└── langgraph.json            # graphs にエージェント (helpdesk) を登録
```

- `helpdesk_tools.py` の `create_ticket` / `reset_password` は**副作用ありのダミー実装**です
  (本来はチケット管理システム・認証基盤を操作する「やり直しの効かない」処理。研修では print で代用)。
- `exercise_6B_hitl.py` がターミナルで承認フローを体験する版 (受講者が starter で編集する対象)。
- `agent.py` + `langgraph.json` がブラウザ (Agent Chat UI) から操作するための版。

---

## パート 1: CLI 版 `exercise_6B_hitl.py`

### 実行

第5章ハンズオン (5-A) で、リポジトリの clone・venv 作成・.env 設定 (OpenAI + LangSmith) は
完了している前提です。まだの場合は 5-A の手順を先に実施してください。

ブラウザで **<https://shell.cloud.google.com/>** を開き (Cloud Shell を開く手順は
第5章ハンズオン 5-A の README「ステップ 0」を参照)、ターミナルで次の 4 行を上から順に実行します。
**新しいターミナルを開いた直後や、しばらく放置して再接続したあとも、この 4 行をそのまま実行すれば
作業を再開できます。**

```bash
cd ~/developing-agentic-ai-with-langchain   # (1) リポジトリのルートへ
source .venv/bin/activate                   # (2) venv を有効化 (必ずルートで。プロンプトに (.venv) が付く)
cd chap06/exercise/solution                 # (3) このディレクトリへ
pip install -r requirements.txt             # (4) 依存をインストール (このディレクトリで 1 回でよい)
```

> - **venv の有効化はリポジトリのルートで行います。** 章のディレクトリには `.venv` がないため、
>   そこで `source .venv/bin/activate` を実行すると `No such file or directory` になります。
> - リポジトリを `~` 以外に clone した場合は、`~/developing-agentic-ai-with-langchain` を実際の場所に読み替えてください。

続けて、**このディレクトリ (`chap06/exercise/solution`) にいるまま**実行します
(approve → reject の 2 パターンを順に体験。LangSmith は 5-A で設定済みのルート `.env` により自動で有効。
トレースは [smith.langchain.com](https://smith.langchain.com) で確認できます)。

```bash
python exercise_6B_hitl.py
```

### TODO①〜④ の解答ポイント

| TODO | 内容 | 解答の要点 |
|---|---|---|
| **①** `interrupt_on` のポリシー設計 | `HumanInTheLoopMiddleware(interrupt_on={...})` | `create_ticket`=approve/edit/reject、`reset_password`=approve/reject のみ、`get_system_status`=`False` (承認不要) |
| **②** checkpointer の設定 | HITL に必須の checkpointer + thread_id | `create_agent(..., checkpointer=InMemorySaver())`。invoke 時に `config={"configurable": {"thread_id": ...}}` |
| **③** interrupt 情報の取得 | `action_requests` を読み解く | `version="v2"` で invoke → `result.interrupts[0].value["action_requests"]` (および `["review_configs"]`) を読む |
| **④** approve / reject で再開 | `Command(resume=...)` の 2 パターン | approve: `Command(resume={"decisions": [{"type": "approve"}]})` / reject: `{"type": "reject", "message": "..."}` |

> **`version="v2"` は必須**です。これを付けることで、invoke の戻り値が `.interrupts` 属性を持つ形式になります。
> CLI 版・Agent Chat UI 版とも、interrupt の取得と `Command(resume=...)` での再開はこの形に従います。

### 期待される動作

- **approve パターン**: `reset_password` で interrupt → 承認 → リセットが実行され、仮パスワードを含む案内が返る。
- **reject パターン**: `reset_password` で interrupt → 理由付きで拒否 → リセットは実行されず、本人手続きを促す代替案内が返る。

### 落とし穴: 副作用ツールの拒否に `respond` を使わない

`reject` と `respond` はどちらも「ツールを実行しない」点で似ていますが、モデルへの伝わり方が**正反対**です。

- `reject` … 「この操作は拒否された」と伝わる (`message` は拒否のフィードバック)。
- `respond` … 人間の `message` が**成功した ToolMessage として**モデルに渡る。

リセットを `respond` で止めると、モデルは「リセットは実行され、その結果がこれだ」と誤認します。
**副作用ツールの拒否は必ず `reject`** を使ってください (`respond` は `ask_user` 系ツール専用)。

---

## パート 2: Agent Chat UI 版 `agent.py` + `langgraph.json` (必須)

CLI で学んだ承認フローを、業務ユーザーに見せられる**ブラウザの承認ダイアログ**から操作します。

### CLI 版との決定的な違い: checkpointer を「コードで渡さない」

| 実行形態 | checkpointer | 理由 |
|---|---|---|
| CLI 版 (`exercise_6B_hitl.py`) | `create_agent(checkpointer=InMemorySaver())` で**自分で渡す** | 単体スクリプトには永続化の担い手がいないため |
| Agent Chat UI 版 (`agent.py`) | **渡さない** | `langgraph dev` (Agent Server) が永続化をプラットフォーム側で提供するため |

> 公式ドキュメント (LangGraph persistence) の指針: 「Agent Server を使う場合、checkpointer や store を
> 手動で実装・設定する必要はない。サーバーが永続化インフラを裏で処理する」。
> このため `agent.py` では checkpointer を渡しません。それでも interrupt の中断・再開は正しく機能します。

> **`.env` と LangSmith について:** `langgraph dev` を実行すると `agent.py` が import され、
> その中の `load_dotenv()` が**リポジトリのルートの `.env`** を読み込みます。これで OpenAI /
> LangSmith のキーが供給されるため、`langgraph dev` での実行も**ルートの `.env` により
> LangSmith トレースが自動で有効**になります (実行後に [smith.langchain.com](https://smith.langchain.com)
> で確認可能)。`agent.py` が `.env` を読み込むので、`langgraph.json` に `env` 指定は不要です。

### 起動から接続までの手順 (Google Cloud Shell)

ここからは **ターミナルを 2 つ**使います。**新しく開くのは 1 つだけ**です。

| | **【ターミナル 1】** | **【ターミナル 2】** |
|---|---|---|
| 用意のしかた | **パート 1 で使ったターミナルをそのまま使う** | ツールバーの **[+]** で**新しく開く** |
| 作業ディレクトリ | `chap06/exercise/solution` (`langgraph.json` がある場所) | `~` (ホームディレクトリ) |
| venv | 有効化済み (`(.venv)` が付いている) | **不要** (Node.js のコマンドしか使わないため) |
| 役割 | **Agent Server (`langgraph dev`) を起動しっぱなしにする** | **Agent Chat UI を起動しっぱなしにする** |

#### ターミナル 1: Agent Server (`langgraph dev`) を起動する

パート 1 の続きなので、**追加の `cd` や venv 有効化は不要**です。
(ターミナルを開き直してしまった場合は、上の「セットアップ」の 4 行を先に実行してください)

```bash
langgraph dev --tunnel
```

- `langgraph dev` は `langgraph.json` を読むので、**`chap06/exercise/solution` にいることが必須**です。
- `langgraph: command not found` になる場合は `pip install -U "langgraph-cli[inmem]"`
  (`requirements.txt` にも含めてあります)。
- `--tunnel` を付けると、ローカルの Agent Server に**外から到達できる公開 URL** が発行されます
  (次の「接続設定」で必要になります)。

起動すると次のような出力が出ます。**Tunnel の URL をコピー**しておき、
**このターミナルは `Ctrl+C` で止めるまでそのまま**にします。

```
- API: http://127.0.0.1:2024
- Tunnel: https://xxxxxxxx.trycloudflare.com     <- これをコピー
- API Docs: http://127.0.0.1:2024/docs
```

> **`--tunnel` を使わない場合**は、Cloud Shell の **[ウェブでプレビュー] → [ポートを変更]** で
> ポート **2024** を公開し、開いたタブの URL (`https://2024-....cloudshell.dev`) を
> Deployment URL に使ってください。

#### ターミナル 2: Agent Chat UI を起動する (ここで新しく開く)

ツールバーの **[+]** で**新しいターミナルタブを開き**、次を上から順に実行します。
新しいタブはホームディレクトリで開きます。**UI はリポジトリの中ではなくホームに作ります**
(リポジトリを汚さないため)。このターミナルでは **venv の有効化は不要**です。

```bash
cd ~                                                  # (1) ホームディレクトリへ
npx create-agent-chat-app --project-name my-chat-ui   # (2) UI を生成 (初回のみ・数分かかります)
cd ~/my-chat-ui                                       # (3) 生成された UI のディレクトリへ
pnpm install                                          # (4) 依存をインストール (初回のみ)
pnpm dev                                              # (5) UI を起動 (ポート 3000)
```

**このターミナルも `Ctrl+C` で止めるまでそのまま**にします。

> 2 回目以降は (2) と (4) は不要で、`cd ~/my-chat-ui && pnpm dev` だけで起動できます。
> **手早く試すだけなら**、この【ターミナル 2】の作業をすべて省略し、ホステッド版
> <https://agentchat.vercel.app> をブラウザで開いても構いません。

#### ブラウザ: Web Preview で UI を開く

Cloud Shell 上部ツールバーの **[ウェブでプレビュー]** アイコン → **[ポートを変更]** で
**3000** を指定して開きます。Agent Chat UI の画面が新しいタブで表示されます。

### 接続設定は 3 項目だけ

UI を開くと接続設定の入力画面が出ます。次の 3 項目を入力します。

| 設定項目 | 入力する値 | 補足 |
|---|---|---|
| **Deployment URL** | 【ターミナル 1】に表示された **Tunnel の URL** (`https://xxxxxxxx.trycloudflare.com`) | `--tunnel` を使わない場合はポート 2024 の Web Preview URL |
| **Graph ID** | `helpdesk` | `langgraph.json` の `graphs` のキー |
| **LangSmith API キー** | (空欄で可) | **ローカルサーバー接続時は不要**。LangSmith 上のデプロイ済みエージェントに接続するときだけ使う |

> **`http://localhost:2024` は入力しても繋がりません。** Agent Chat UI は**あなたのブラウザの中**で
> 動いており、そこから見た `localhost` は「Cloud Shell」ではなく「あなたの PC」を指すためです。
> 必ず **Cloud Shell の外から到達できる URL** (Tunnel URL またはポート 2024 の Web Preview URL) を
> 入力してください。

### ブラウザで承認フローを操作する

接続できたら、チャット欄に **「私 (emp-sato) のパスワードをリセットして」** と入力します。
エージェントが `reset_password` を呼ぼうとした瞬間に interrupt が発生し、画面に**承認ダイアログ**が現れます。

```text
┌──────────────────────────────────────────────┐
│  ⏸ Tool execution pending approval           │
│                                              │
│  Tool: reset_password                        │
│  Args: { "employee_id": "emp-sato" }         │
│                                              │
│  [ ✅ Approve ]  [ ❌ Reject ]                │
└──────────────────────────────────────────────┘
```

- **Approve** を押す → `reset_password` が実行され、会話が続く。
- **Reject** を押す → 理由を入力して拒否。リセットは実行されない。

CLI で `Command(resume={"decisions": [...]})` を打って行った操作と**完全に同じ承認フロー**が、
ボタン操作で完結します (UI の裏側で、ボタンが `Command(resume=...)` に変換されています)。
`reset_password` は `approve` / `reject` のみ許可なので、ダイアログに Edit ボタンは出ません
(`create_ticket` を呼ばせると Edit も出ます)。

> **以降の章でもこの UI を使います。** 第7・8章でも `langgraph dev` + Agent Chat UI でエージェントを操作し、
> 最終章では「Web UI から操作できるヘルプデスク・マルチエージェント」として完成させます。

---

## 期待成果物 (この演習のゴール)

- **PII 保護**: メールアドレスを含む入力が `[REDACTED_EMAIL]` に置換される。
- **要承認オペレーション**: `create_ticket` / `reset_password` が、人間の承認まで実行されない。
- **Agent Chat UI 操作**: ブラウザの承認ダイアログから approve / reject を操作できる。

これらを満たすヘルプデスクエージェント **v4** が完成です。

---

## トラブルシューティング

| 症状 | 確認すること |
|---|---|
| `ModuleNotFoundError: helpdesk_tools` | このディレクトリから実行しているか (`agent.py` と同じ場所に `helpdesk_tools.py` がある) |
| interrupt 後に再開できずエラー | **CLI 版**は checkpointer を渡したか (TODO②)。再開時の `thread_id` が中断時と同じか |
| Agent Chat UI で承認ダイアログが出ない | 【ターミナル 1】で `langgraph dev` が起動したままか。Graph ID が `helpdesk` か |
| UI から Agent Server に繋がらない | Deployment URL に `http://localhost:2024` を入れていないか。Tunnel URL (またはポート 2024 の Web Preview URL) を使う |
| `langgraph: command not found` | `pip install -U "langgraph-cli[inmem]"` を実行したか (仮想環境を有効化しているか) |
| メールが redact されない | 入力に半角のメール形式 (`name@example.com`) が含まれているか |

> **`.env` と `__pycache__/` はコミットしないでください。** `.env` はリポジトリのルートに 1 つだけ置き、
> リポジトリに含めるのは値の入っていないルートの `.env.example` (ひな形) だけです。
>
> **実務で Windows を使う場合の参考**: 本演習は Cloud Shell (Linux) 前提です。Windows では `npx` 起動に
> 問題が出る場合があり (`cmd /c npx ...` 形式・`PYTHONUTF8=1` で対処)、これは教材の早見表の通りですが、
> Cloud Shell では発生しません。
