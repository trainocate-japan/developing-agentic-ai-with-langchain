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

1. (同じターミナルセッションなら venv は有効なまま。新しいタブの場合は) リポジトリ直下の venv を有効化:
   ```bash
   source <リポジトリ>/.venv/bin/activate
   ```
2. このディレクトリへ移動:
   ```bash
   cd <リポジトリ>/chap06/exercise/starter
   ```
3. このディレクトリの依存を追加インストール (前章までと共通なら差分のみ入ります):
   ```bash
   pip install -r requirements.txt
   ```
4. TODO①〜④ を埋めてから実行 (approve → reject の 2 パターンを体験。LangSmith は 5-A で
   設定済みのルート `.env` により自動で有効。トレースは
   [smith.langchain.com](https://smith.langchain.com) で確認できます):
   ```bash
   python exercise_6B_hitl.py
   ```

### TODO①〜④ とヒント

| TODO | やること | ヒント |
|---|---|---|
| **①** `interrupt_on` のポリシー設計 | `HumanInTheLoopMiddleware(interrupt_on={...})` を埋める | **ツール名ごとにポリシーを書く。承認不要は `False`**。`create_ticket`=approve/edit/reject、`reset_password`=approve/reject のみ、`get_system_status`=`False` |
| **②** checkpointer の設定 | `create_agent(...)` に checkpointer を足す | **checkpointer を忘れると interrupt 後に再開できません** (第4章の復習)。`checkpointer=InMemorySaver()` を引数に追加。invoke 時の `config={"configurable": {"thread_id": ...}}` は配布済み |
| **③** interrupt 情報の取得 | `print_interrupt` の中で `action_requests` を取り出す | `version="v2"` で invoke 済み → `result.interrupts[0]` を取り、その `.value` (dict) から `action_requests` / `review_configs` を読む |
| **④** approve / reject で再開 | `Command(resume=...)` の invoke を 2 つ書く | **decisions のリストは止まっている tool call と同じ順序**。approve: `{"type": "approve"}` / reject: `{"type": "reject", "message": "<理由>"}` |

> **`version="v2"` は配布済み**です (invoke にすでに付いています)。これにより戻り値が `.interrupts` を持ちます。
> TODO③・④はこの形を前提にしています。

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

```bash
# 0. (未導入なら) langgraph dev コマンドを導入
pip install -U "langgraph-cli[inmem]"   # requirements.txt にも含めてあります

# 1. このディレクトリ (langgraph.json がある場所) で Agent Server を起動
langgraph dev
#   → 次のような出力が出る:
#       - 🚀 API: http://127.0.0.1:2024
#       - 📚 API Docs: http://127.0.0.1:2024/docs
```

```bash
# 2. 別のターミナルで Agent Chat UI をローカル起動
npx create-agent-chat-app --project-name my-chat-ui
cd my-chat-ui
pnpm install
pnpm dev
#   (手早く試すだけなら、ホステッド版 https://agentchat.vercel.app でも可)
```

```text
3. Cloud Shell の「Web Preview」でポートを公開する
   - 画面右上の [ウェブでプレビュー] アイコン → [ポートを変更] で UI のポート (例: 3000) を開く
```

### 接続設定は 3 項目だけ

| 設定項目 | 入力する値 | 補足 |
|---|---|---|
| **Graph ID** | `helpdesk` | `langgraph.json` の `graphs` のキー |
| **Deployment URL** | `http://localhost:2024` | `langgraph dev` が表示した API の URL |
| **LangSmith API キー** | (空欄で可) | **ローカルサーバー接続時は不要** |

### ブラウザで承認フローを操作する

チャット欄に **「私 (emp-sato) のパスワードをリセットして」** と入力すると、`reset_password` を呼ぼうとした
瞬間に **承認ダイアログ** が現れます。**Approve** で実行、**Reject** で理由を入力して拒否——CLI で
`Command(resume=...)` を打って行った操作と**同じ承認フロー**が、ボタン操作で完結します。
`reset_password` は approve / reject のみ許可なので、ダイアログに Edit ボタンは出ません。

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
| Agent Chat UI で承認ダイアログが出ない | `langgraph dev` が起動しているか、Graph ID が `helpdesk`、URL が `http://localhost:2024` か |
| `langgraph: command not found` | `pip install -U "langgraph-cli[inmem]"` を実行したか (仮想環境を有効化しているか) |

> **`.env` と `__pycache__/` はコミットしないでください。** `.env` はリポジトリのルートに 1 つだけ置き、
> リポジトリに含めるのは値の入っていないルートの `.env.example` (ひな形) だけです。
>
> **実務で Windows を使う場合の参考**: 本演習は Cloud Shell (Linux) 前提です。Windows では `npx` 起動に
> 問題が出る場合があり (`cmd /c npx ...`・`PYTHONUTF8=1` で対処)、これは教材の早見表の通りですが、
> Cloud Shell では発生しません。
