# 演習 6-B【演習 (starter)】: 要承認オペレーションの実装 — ヘルプデスク Step 5

研修コース「Agentic AI 開発実践 - LangChain 版」/ 第6章「Middleware と HITL」

このディレクトリは演習 6-B の**演習用 (starter)** です。
`exercise_6B_hitl.py` (CLI 版) の **TODO①〜④** を自分で埋めて完成させてください。
完成版は `solution/` にあります。まずは自力で挑戦しましょう。

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
starter/
├── README.md                 # この説明
├── requirements.txt          # 依存パッケージ (langgraph-cli[inmem] 含む)
├── helpdesk_tools.py         # 配布: search_faq / get_system_status / create_ticket / reset_password (完成)
├── exercise_6B_hitl.py       # CLI 版: HITL 承認フロー (★TODO①〜④ をあなたが埋める)
├── agent.py                  # Agent Chat UI 用: langgraph dev が読むエージェント定義 (配布・完成)
└── langgraph.json            # graphs にエージェント (helpdesk) を登録 (配布・完成)
```

- あなたが編集するのは **`exercise_6B_hitl.py` の TODO①〜④だけ**です。
- `helpdesk_tools.py` の `create_ticket` / `reset_password` は**副作用ありのダミー実装** (完成済み)。
- `agent.py` + `langgraph.json` は配布・完成済みです (パート 2 でそのまま使います)。

---

## パート 1: CLI 版 `exercise_6B_hitl.py` の TODO を埋める

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
cd chap06/exercise/starter                  # (3) このディレクトリへ
pip install -r requirements.txt             # (4) 依存をインストール (このディレクトリで 1 回でよい)
```

> - **venv の有効化はリポジトリのルートで行います。** 章のディレクトリには `.venv` がないため、
>   そこで `source .venv/bin/activate` を実行すると `No such file or directory` になります。
> - リポジトリを `~` 以外に clone した場合は、`~/developing-agentic-ai-with-langchain` を実際の場所に読み替えてください。

準備ができたら **TODO①〜④ を埋め**、**このディレクトリ (`chap06/exercise/starter`) にいるまま**
実行します (approve → reject の 2 パターンを体験。LangSmith は 5-A で設定済みのルート `.env` により
自動で有効。トレースは [smith.langchain.com](https://smith.langchain.com) で確認できます)。

```bash
python exercise_6B_hitl.py
```

### TODO①〜④ とヒント

| TODO | やること | ヒント |
|---|---|---|
| **①** `interrupt_on` のポリシー設計 | `HumanInTheLoopMiddleware(interrupt_on={...})` を埋める | **ツール名ごとにポリシーを書く。承認不要は `False`**。`create_ticket`=approve/edit/reject、`reset_password`=approve/reject のみ、`get_system_status`=`False` |
| **②** checkpointer の設定 | `create_agent(...)` に checkpointer を足す | **checkpointer を忘れると interrupt 後に再開できません** (第4章の復習)。`checkpointer=InMemorySaver()` を引数に追加。invoke 時の `config={"configurable": {"thread_id": ...}}` は配布済み |
| **③** interrupt 情報の取得 | `print_interrupt` の中で `action_requests` を取り出す | `version="v2"` で invoke 済み → `result.interrupts[0]` を取り、その `.value` (dict) から `action_requests` / `review_configs` を読む。引数キーは **`args`** |
| **④** approve / reject で再開 | `Command(resume=...)` の invoke を 2 つ書く | **decisions のリストは止まっている tool call と同じ順序**。approve: `{"type": "approve"}` / reject: `{"type": "reject", "message": "<理由>"}` |

> **`version="v2"` は配布済み**です (invoke にすでに付いています)。これにより戻り値が `.interrupts` を持ちます。
> TODO③・④はこの形を前提にしています。

> **`version="v2"` の戻り値は `GraphOutput`** です。状態は `.value`、中断情報は `.interrupts` に
> 分かれて入ります (最終回答は `final.value["messages"][-1].content`)。
> `action_requests` の引数キーは **`args`** です (`arguments` ではありません)。

### 想定どおり動かないとき: `result.interrupts` が空

`result.interrupts` は**中断が起きなかった場合は空タプル**です。モデルが `reset_password` を呼ばず、
`search_faq` の案内や本人確認の聞き返しで会話を完結させてしまうと、承認フローに入らないまま完走します
(この状態で `result.interrupts[0]` を読むと `IndexError: tuple index out of range` になります)。

配布コードは空タプルを検出して原因を表示するようになっています。表示が出た場合は、
`SYSTEM_PROMPT` の「リセット依頼では必ず `reset_password` を呼ぶ」という指示と、
ユーザー発話に社員 ID が含まれているかを確認してください。
**副作用ツールを「呼ぶかどうか」をモデルの遠慮に任せない**——実行の可否は承認フローで人間が決める、
というのが HITL の設計思想です。

### つまずきポイントを「あえて」体験する

ヒントに「**checkpointer を忘れると interrupt 後に再開できません**」とあります。
TODO② を**わざと空のまま**実行すると、interrupt で停止したあと `Command(resume=...)` で再開する段で
エラーになります。**エラーメッセージを読んで**、「なぜ checkpointer が要るのか」を体感してから
TODO② を埋めると、HITL と checkpointer の関係 (中断時に state を保存 → 同じ thread から再開) が
腑に落ちます。

### 期待される動作 (完成後)

- **approve パターン**: `reset_password` で interrupt → 承認 → リセットが実行され、仮パスワードを含む案内が返る。
- **reject パターン**: `reset_password` で interrupt → 理由付きで拒否 → リセットは実行されず、本人手続きを促す代替案内が返る。

### 落とし穴: 副作用ツールの拒否に `respond` を使わない

`reject` と `respond` はどちらも「ツールを実行しない」点で似ていますが、モデルへの伝わり方が**正反対**です。

- `reject` … 「この操作は拒否された」と伝わる (`message` は拒否のフィードバック)。
- `respond` … 人間の `message` が**成功した ToolMessage として**モデルに渡る。

リセットを `respond` で止めると、モデルは「リセットは実行された」と誤認します。
**副作用ツールの拒否は必ず `reject`** を使ってください (`respond` は `ask_user` 系ツール専用)。

---

## パート 2: Agent Chat UI 版 `agent.py` + `langgraph.json` (必須)

CLI で学んだ承認フローを、業務ユーザーに見せられる**ブラウザの承認ダイアログ**から操作します。
`agent.py` と `langgraph.json` は**配布・完成済み**なので、編集は不要です (そのまま起動します)。

### CLI 版との決定的な違い: checkpointer を「コードで渡さない」

| 実行形態 | checkpointer | 理由 |
|---|---|---|
| CLI 版 (`exercise_6B_hitl.py`) | `create_agent(checkpointer=InMemorySaver())` で**自分で渡す** (TODO②) | 単体スクリプトには永続化の担い手がいないため |
| Agent Chat UI 版 (`agent.py`) | **渡さない** | `langgraph dev` (Agent Server) が永続化をプラットフォーム側で提供するため |

> 公式ドキュメント (LangGraph persistence) の指針: 「Agent Server を使う場合、checkpointer や store を
> 手動で実装・設定する必要はない。サーバーが永続化インフラを裏で処理する」。
> このため `agent.py` では checkpointer を渡しません。CLI 版とは扱いが異なる点に注意してください。

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
| 作業ディレクトリ | `chap06/exercise/starter` (`langgraph.json` がある場所) | `~` → `~/agent-chat-ui` |
| venv | 有効化済み (`(.venv)` が付いている) | **不要** (Node.js のコマンドしか使わないため) |
| 役割 | **Agent Server (`langgraph dev`) を起動しっぱなしにする** | **Agent Chat UI を起動しっぱなしにする** |

#### ターミナル 1: Agent Server (`langgraph dev`) を起動する

パート 1 の続きなので、**追加の `cd` や venv 有効化は不要**です。
(ターミナルを開き直してしまった場合は、上の「セットアップ」の 4 行を先に実行してください)

```bash
langgraph dev --tunnel
```

- `langgraph dev` は `langgraph.json` を読むので、**`chap06/exercise/starter` にいることが必須**です。
- `langgraph: command not found` になる場合は `pip install -U "langgraph-cli[inmem]"`
  (`requirements.txt` にも含めてあります)。
- `--tunnel` を付けると、ローカルの Agent Server に**外から到達できる公開 URL**
  (`https://....trycloudflare.com`) が発行され、**API の URL がその公開 URL に置き換わります**
  (次の「接続設定」で必要になります)。

起動すると、まず Cloudflare Tunnel のログが数十行流れ、最後に次のバナーが出ます。
**`🚀 API:` の行の URL をコピー**しておき、
**このターミナルは `Ctrl+C` で止めるまでそのまま**にします。

```
INFO:langgraph_api.cli:Starting Cloudflare Tunnel...
INFO:langgraph_api.tunneling.cloudflare:[cloudflared] ... Requesting new quick Tunnel on trycloudflare.com...
    (Cloudflare のログが数十行流れます)

        Welcome to

╦  ┌─┐┌┐┌┌─┐╔═╗┬─┐┌─┐┌─┐┬ ┬
║  ├─┤││││ ┬║ ╦├┬┘├─┤├─┘├─┤
╩═╝┴ ┴┘└┘└─┘╚═╝┴└─┴ ┴┴  ┴ ┴

- 🚀 API: https://compatibility-offerings-bite-measured.trycloudflare.com     <- これをコピー
- 🎨 Studio UI: https://smith.langchain.com/studio/?baseUrl=https://compatibility-offerings-bite-measured.trycloudflare.com
- 📚 API Docs: https://compatibility-offerings-bite-measured.trycloudflare.com/docs
```

> **`API` と `Tunnel` が 2 行並んで表示されるわけではありません。** `--tunnel` を付けると
> **`🚀 API:` の行そのものが Tunnel の URL** (`https://....trycloudflare.com`) になります
> (付けない場合は `🚀 API: http://127.0.0.1:2024` と表示されます)。
> ランダムな英単語をつないだ URL で、**起動するたびに変わります**。
> 途中に流れる Cloudflare のログの枠囲みにも同じ URL が出ますが、
> **バナーの `🚀 API:` の行をコピーすれば OK** です。

> **⚠ Cloud Shell の [ウェブでプレビュー] でポート 2024 を公開した URL は使えません。**
> その URL (`https://2024-cs-....cloudshell.dev`) は「HTTPS 経由で**あなたのユーザーアカウントのみ**に
> アクセスを制限する」仕様のため
> ([公式ドキュメント](https://cloud.google.com/shell/docs/using-web-preview))、
> **別サイトである Agent Chat UI からの API 呼び出しは認証で弾かれ**、
> `Failed to connect to LangGraph server` になります。
> Agent Server の公開には**必ず `--tunnel` を使ってください**
> (Web Preview を使うのは、【ターミナル 2】の UI をポート 3000 で開くときだけです)。

#### ターミナル 2: Agent Chat UI を起動する (ここで新しく開く)

ツールバーの **[+]** で**新しいターミナルタブを開き**、次を上から順に実行します。
新しいタブはホームディレクトリで開きます。**UI はリポジトリの中ではなくホームに作ります**
(リポジトリを汚さないため)。このターミナルでは **venv の有効化は不要**です。

```bash
cd ~                                                  # (1) ホームディレクトリへ
export COREPACK_ENABLE_DOWNLOAD_PROMPT=0              # (2) pnpm 取得時の確認 (Y/n) を省く
corepack enable                                       # (3) pnpm を使えるようにする (初回のみ)
git clone https://github.com/langchain-ai/agent-chat-ui.git   # (4) UI を取得 (初回のみ)
cd ~/agent-chat-ui                                    # (5) UI のディレクトリへ
pnpm install                                          # (6) 依存をインストール (初回のみ・数分かかります)
pnpm dev                                              # (7) UI を起動 (ポート 3000)
```

> **(2)(3) は pnpm を使えるようにする準備です。** Cloud Shell に pnpm は入っていませんが、
> Node.js 同梱の **corepack** で有効化できます (`pnpm: command not found` はこれを飛ばしたとき)。
> Agent Chat UI は `package.json` で pnpm を指定しているため、pnpm でインストールします。
> `COREPACK_ENABLE_DOWNLOAD_PROMPT=0` は、pnpm 本体を取得するときに出る確認
> (`? Do you want to continue? [Y/n]`) を省くための設定です。
>
> **`npx create-agent-chat-app` は使いません。** この生成コマンドが配るテンプレートは少し古く、
> LangChain 1.x の承認要求 (`action_requests` / `review_configs`) を認識できません。
> そのため**承認ダイアログが出ず、interrupt の中身が JSON のまま表示されます**。
> 上のように公式リポジトリを clone した最新版なら、この形式に対応しています。

**このターミナルも `Ctrl+C` で止めるまでそのまま**にします。

> 2 回目以降は (4)(6) は不要で、`cd ~/agent-chat-ui && pnpm dev` だけで起動できます。
> **手早く試すだけなら**、この【ターミナル 2】の作業をすべて省略し、ホステッド版
> <https://agentchat.vercel.app> をブラウザで開いても構いません
> (ホステッド版も最新版なので、承認ダイアログは正しく表示されます)。

#### ブラウザ: Web Preview で UI を開く

Cloud Shell 上部ツールバーの **[ウェブでプレビュー]** アイコン → **[ポートを変更]** で
**3000** を指定して開きます。Agent Chat UI の画面が新しいタブで表示されます。

### 接続設定は 3 項目だけ

UI を開くと接続設定の入力画面が出ます。次の 3 項目を入力します。

| 設定項目 | 入力する値 | 補足 |
|---|---|---|
| **Deployment URL** | 【ターミナル 1】の **`🚀 API:` に表示された URL** (`https://xxxxxxxx.trycloudflare.com`) | Web Preview (ポート 2024) の URL は**使えません** |
| **Graph ID** | `helpdesk` | `langgraph.json` の `graphs` のキー |
| **LangSmith API キー** | (空欄で可) | **ローカルサーバー接続時は不要** |

> **`http://localhost:2024` は入力しても繋がりません。** Agent Chat UI は**あなたのブラウザの中**で
> 動いており、そこから見た `localhost` は「Cloud Shell」ではなく「あなたの PC」を指すためです。
> 必ず **`--tunnel` で発行された `https://....trycloudflare.com`** (【ターミナル 1】の `🚀 API:` の行) を
> 入力してください。Cloud Shell の Web Preview (ポート 2024) の URL も、
> あなたのアカウントでの認証が必要なため UI からは接続できません。

### ブラウザで承認フローを操作する

チャット欄に **「社員 ID emp-sato のパスワードをリセットしてください」** と入力すると、
`reset_password` を呼ぼうとした瞬間に **承認ダイアログ** が現れます。**Approve** で実行、**Reject** で
理由を入力して拒否——CLI で `Command(resume=...)` を打って行った操作と**同じ承認フロー**が、
ボタン操作で完結します。
`reset_password` は approve / reject のみ許可なので、ダイアログに Edit ボタンは出ません。

> **依頼文には社員 ID を入れてください。** 「私のパスワードをリセットして」のように ID が曖昧だと、
> モデルが本人確認の聞き返しや案内文で会話を終えてしまい、`reset_password` が呼ばれません
> (= interrupt が起きず、承認ダイアログも出ません)。**呼ぶかどうかをモデルの遠慮に任せない**——
> 実行の可否は承認フローで人間が決める、というのが HITL の設計思想です (CLI 版と同じ)。

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
| `___` のままでエラー / 構文エラー | TODO①〜④の `___` を実際のコードに置き換えたか |
| interrupt 後に再開できずエラー | **CLI 版**は checkpointer を渡したか (TODO②)。再開時の `thread_id` が中断時と同じか |
| `ModuleNotFoundError: helpdesk_tools` | このディレクトリから実行しているか (`helpdesk_tools.py` と同じ場所) |
| Agent Chat UI で承認ダイアログが出ない | 【ターミナル 1】で `langgraph dev` が起動したままか。Graph ID が `helpdesk` か |
| ダイアログが出ず「承認が必要です」と**文章で**返る | 依頼文に社員 ID を入れたか (例: 社員 ID emp-sato のパスワードをリセットしてください)。`agent.py` の `SYSTEM_PROMPT` に「聞き返しで代替せず `reset_password` を必ず呼ぶ」指示があるか |
| `Failed to connect to LangGraph server` と出る | Deployment URL に `http://localhost:2024` や Web Preview の URL (`https://2024-cs-....cloudshell.dev`) を入れていないか。`--tunnel` で発行された `https://....trycloudflare.com` を使う |
| Tunnel の URL が見つからない | 出力の **`🚀 API:` の行**がそれ (`--tunnel` を付け忘れると `http://127.0.0.1:2024` になる)。起動のたびに URL は変わる |
| `langgraph: command not found` | `pip install -U "langgraph-cli[inmem]"` を実行したか (仮想環境を有効化しているか) |
| `pnpm: command not found` | UI 手順の (2)(3) (`export ...` と `corepack enable`) を実行したか (Cloud Shell に pnpm は同梱されていない) |
| 承認ダイアログの代わりに `action_requests` / `review_configs` が JSON で表示される | `npx create-agent-chat-app` で作った UI を使っていないか。`git clone` した `~/agent-chat-ui` かホステッド版を使う (旧 UI は LangChain 1.x の承認要求形式に未対応) |
| `next: command not found` | 依存のインストールが終わっていない。`~/agent-chat-ui` で `pnpm install` をやり直す |

> **`.env` と `__pycache__/` はコミットしないでください。** `.env` はリポジトリのルートに 1 つだけ置き、
> リポジトリに含めるのは値の入っていないルートの `.env.example` (ひな形) だけです。
>
> **実務で Windows を使う場合の参考**: 本演習は Cloud Shell (Linux) 前提です。Windows では `npx` 起動に
> 問題が出る場合があり (`cmd /c npx ...`・`PYTHONUTF8=1` で対処)、これは教材の早見表の通りですが、
> Cloud Shell では発生しません。
