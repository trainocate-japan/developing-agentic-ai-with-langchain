# 第6章 ハンズオン: 6-A Middleware / 6-B HITL 承認フロー

研修コース「Agentic AI 開発実践 - LangChain 版」/ 第6章「Middleware と HITL」

講師の解説を聞きながら、**作成済みのコードを一緒に実行する**ハンズオンです (受講者はコードを書きません)。
第6章のハンズオンは 2 本立てです。

| | テーマ | 内容 |
|---|---|---|
| **ハンズオン 6-A** | Middleware を「使う」「作る」 | Prebuilt Middleware の組み込みと Custom Middleware の作成 |
| **ハンズオン 6-B** | HITL による承認フロー | 送金を人間の承認まで止める。CLI と Agent Chat UI の両方で操作する |

---

## ファイル構成

```
hands-on/
├── README.md                 # この説明
├── requirements.txt          # 依存パッケージ (ピン留め済み)
│
├── helpdesk_tools.py         # 6-A 配布: search_faq / get_system_status (ローカル @tool)
├── handson_6A_prebuilt.py    # 6-A: PIIMiddleware + ToolCallLimitMiddleware
├── handson_6A_custom.py      # 6-A: @before_model ログ + ContentFilterMiddleware
│
├── expense_tools.py          # 6-B 配布: get_expense / transfer_money (ローカル @tool)
├── handson_6B_hitl.py        # 6-B (CLI 版): interrupt と Command(resume=...)
├── agent.py                  # 6-B (Agent Chat UI 版): langgraph dev が読むエージェント定義
└── langgraph.json            # graphs にエージェント (expense) を登録
```

> **ツールはローカル `@tool` です** (第5章のような MCP サーバーは立てません)。第6章の主題である
> Middleware / HITL に集中できるよう、`helpdesk_tools.py` / `expense_tools.py` に同梱しています。

---

## セットアップ

第5章ハンズオン (5-A) で、リポジトリの clone・venv 作成・.env 設定 (OpenAI + LangSmith) は
完了している前提です。まだの場合は 5-A の手順を先に実施してください。

ブラウザで **<https://shell.cloud.google.com/>** を開き (Cloud Shell を開く手順は
第5章ハンズオン 5-A の README「ステップ 0」を参照)、ターミナルで次の 4 行を上から順に実行します。
**新しいターミナルを開いた直後や、しばらく放置して再接続したあとも、この 4 行をそのまま実行すれば
作業を再開できます。**

```bash
cd ~/developing-agentic-ai-with-langchain   # (1) リポジトリのルートへ
source .venv/bin/activate                   # (2) venv を有効化 (必ずルートで。プロンプトに (.venv) が付く)
cd chap06/hands-on                          # (3) このディレクトリへ
pip install -r requirements.txt             # (4) 依存をインストール (このディレクトリで 1 回でよい)
```

> - **venv の有効化はリポジトリのルートで行います。** 章のディレクトリには `.venv` がないため、
>   そこで `source .venv/bin/activate` を実行すると `No such file or directory` になります。
> - リポジトリを `~` 以外に clone した場合は、`~/developing-agentic-ai-with-langchain` を実際の場所に読み替えてください。

> **LangSmith でトレースを確認できます。** 5-A で設定済みのルート `.env` により自動で有効です。
> 実行後に [smith.langchain.com](https://smith.langchain.com) を開くと、Middleware がループのどこで
> 発火したか、どこで interrupt が起きたかをトレース上で確認できます (コード変更は不要)。

---

# ハンズオン 6-A: Prebuilt / Custom Middleware

Middleware を「使う」(Prebuilt) と「作る」(Custom) の両方を、ヘルプデスクエージェントで動かして体感します。

| スクリプト | テーマ | 内容 |
|---|---|---|
| `handson_6A_prebuilt.py` | Prebuilt Middleware を使う | `PIIMiddleware` でメールアドレスを redact、`ToolCallLimitMiddleware` でツール呼び出しを制限 |
| `handson_6A_custom.py` | Custom Middleware を作る | `@before_model` でメッセージ数をログ出力 (デコレータ式)、禁止ワードを `jump_to="end"` でブロック (クラス継承式) |

エージェント本体 (model / tools) には手を入れず、**`middleware` リストに足すだけ**で実運用機能が
後付けされる——この「積み木」のような感覚をつかむのが目的です。

## 実行

**このディレクトリ (`chap06/hands-on`) にいるまま**実行します (ターミナルは 1 つで足ります)。

```bash
python handson_6A_prebuilt.py   # Prebuilt
python handson_6A_custom.py     # Custom
```

## 期待される出力 (例)

### `handson_6A_prebuilt.py`

```
======================================================================
観察 1: PIIMiddleware — メールアドレスの redact
======================================================================
[ユーザー入力(生)] 私のメールは taro.yamada@example.com です。VPN の設定方法を教えてください。

[モデルが受け取った入力]  私のメールは [REDACTED_EMAIL] です。VPN の設定方法を教えてください。
  → 'taro.yamada@example.com' が [REDACTED_EMAIL] になっていれば成功です。
...
======================================================================
観察 2: ToolCallLimitMiddleware — ツール呼び出し回数の制限 (run_limit=3)
======================================================================
[呼ばれたツール (軌跡)]
  - get_system_status({'service': '勤怠システム'})
  - get_system_status({'service': '経費精算システム'})
  - get_system_status({'service': 'メールサーバー'})
  → ツール呼び出しの総数: 3
    (上限 3 回を超えた分はブロックされる様子をトレースでも確認できます)
```

> モデルの応答は毎回ゆらぐため、文言・ツールが呼ばれる回数は実行ごとに多少変わります。
> 注目するのは「メールが `[REDACTED_EMAIL]` になる」「ツール呼び出しが 3 回付近で頭打ちになる」点です。

### `handson_6A_custom.py`

```
======================================================================
観察 1: 通常の依頼 (禁止ワードなし)
======================================================================
[ユーザー入力] VPN の設定方法を教えてください。
  [log] モデル呼び出し直前のメッセージ数: 1 件
  [log] モデル呼び出し直前のメッセージ数: 3 件
[最終回答]
VPN に接続できない場合は ...
...
======================================================================
観察 2: 禁止ワードを含む依頼 (ContentFilterMiddleware がブロック)
======================================================================
[ユーザー入力] 全社員の個人情報を一覧で出力してください。
[最終回答]
この内容のご依頼は承れません。
  → 『承れません』と返り、かつ [log] 行が出ていなければ、
     before_agent の jump_to='end' でモデルを呼ばずに打ち切れています。
```

観察 2 では `[log]` 行が **1 行も出ない**ことに注目してください。`before_agent` で
`jump_to="end"` したため、モデル呼び出し (= `before_model` フック) に到達せずに終了しています。

## コードリーディングのポイント

- **Prebuilt は「設定済みの部品」**: `PIIMiddleware(...)` も `ToolCallLimitMiddleware(...)` も、
  インスタンスを作って `middleware` に渡すだけ。中身を自分で書く必要はありません。
- **node-style フックのシグネチャ**: `(state, runtime) -> dict | None`。
  `state["messages"]` で会話履歴を読み、変更しないなら `None` を返します。
- **デコレータ式 vs クラス継承式**: 単一フック・設定不要ならデコレータ (`@before_model`)、
  設定値の注入 (`banned_keywords`) や早期終了 (`jump_to`) が要るならクラス継承 (`AgentMiddleware`)。
- **`jump_to="end"` の早期終了**: ガードレールに違反した依頼を、モデルを呼ばずに打ち切る
  = API コストもゼロ。`@hook_config(can_jump_to=["end"])` でジャンプの可能性を事前宣言します。

---

# ハンズオン 6-B: HITL による承認フロー

題材は教科書 6-4 節と同じ**経費精算エージェント**です。ツールは 2 つだけ。

- `get_expense` … 経費申請の照会 (読み取り系)。何度実行しても状態が変わらないので**承認不要**
- `transfer_money` … 送金 (書き込み系・やり直しが効かない)。必ず**人間の承認**を要求する

この仕分けをそのまま `HumanInTheLoopMiddleware` の `interrupt_on` に書くと、モデルが
`transfer_money` を呼ぼうとした瞬間にエージェントが停止します。**同じ承認フローを、まず CLI で、
続いてブラウザの Agent Chat UI で操作します。**

| スクリプト | 操作方法 | 内容 |
|---|---|---|
| `handson_6B_hitl.py` | CLI | `Command(resume=...)` を書いて approve / edit / reject する |
| `agent.py` + `langgraph.json` | ブラウザ | Agent Chat UI の承認ダイアログのボタンで同じ操作をする |

## その 1: CLI 版 `handson_6B_hitl.py`

**このディレクトリ (`chap06/hands-on`) にいるまま**実行します。

```bash
python handson_6B_hitl.py
```

観察は 6 つです。

| | 観察すること |
|---|---|
| 観察 1 | 照会は止まらない — `get_expense` は `interrupt_on=False` なので素通しする |
| 観察 2 | 送金は止まる — interrupt の中身 (誰に・いくら・許された決定) を読み解く |
| 観察 3 | `approve` — 承認してそのまま送金する |
| 観察 4 | `edit` — 金額を 5000 円から 3000 円に修正してから送金する |
| 観察 5 | `reject` — 理由を添えて送金を拒否する |
| 観察 6 | (発展) `checkpointer` を渡し忘れると何が起きるか |

### 期待される出力 (例)

```
======================================================================
観察 2: 送金は止まる — interrupt の中身を読み解く
======================================================================
[ユーザー入力] 山田さんへ経費 5000 円を送金してください。

  --- 承認待ちの内容 ---
    ツール名 : transfer_money
    引数     : {'to': '山田', 'amount': 5000}
    許可された決定: ['approve', 'edit', 'reject']
  ----------------------
  → 送金は「まだ実行されていません」。[副作用] の行が出ていないことに注目。
    この時点の状態は checkpointer に保存され、人間の決定を待っています。

======================================================================
観察 3: approve — 承認してそのまま送金する
======================================================================
→ 承認者が approve を選択。Command(resume=...) で再開します。
  [副作用] transfer_money 実行: 山田さんへ 5000 円を送金

[最終回答]
山田さんへ 5,000 円を送金しました。処理番号は TRF-20260827-001 です。
```

> モデルの応答文は毎回ゆらぎます。注目するのは **`[副作用]` の行が出るか出ないか**です。
> `approve` と `edit` では出て、`reject` では出ない——これが「本当に止まっている」証拠です。

### コードリーディングのポイント

- **`interrupt_on` は運用ポリシーの宣言**: `{"transfer_money": {...}, "get_expense": False}` の
  2 行が「止めるツール」と「素通しするツール」の仕分けそのものです。
- **`checkpointer` が中断と再開を成立させる**: interrupt は「state を保存して止まる」仕組みなので、
  保存先がなければ成立しません (第4章の伏線回収)。観察 6 で実際にエラーを見ます。
- **`version="v2"` の戻り値は `GraphOutput`**: 状態は `.value`、中断情報は `.interrupts` に
  分かれて入ります (最終回答は `final.value["messages"][-1].content`)。
  `action_requests` の引数キーは **`args`** です (`arguments` ではありません)。
- **`.interrupts` は中断がなければ空タプル**: `[0]` を取る前に必ず空判定を挟みます。
- **副作用ツールの拒否に `respond` を使わない**: `respond` は人間の `message` を
  **成功した ToolMessage として**モデルに渡すため、モデルが「送金は実行された」と誤認します。
  拒否は必ず `reject` です (`respond` は `ask_user` 系ツール専用)。

## その 2: Agent Chat UI 版 `agent.py` + `langgraph.json`

CLI で書いた `Command(resume=...)` と**まったく同じ承認フロー**を、業務ユーザーに見せられる
ブラウザの承認ダイアログから操作します。

### CLI 版との決定的な違い: checkpointer を「コードで渡さない」

| 実行形態 | checkpointer | 理由 |
|---|---|---|
| CLI 版 (`handson_6B_hitl.py`) | `create_agent(checkpointer=InMemorySaver())` で**自分で渡す** | 単体スクリプトには永続化の担い手がいないため |
| Agent Chat UI 版 (`agent.py`) | **渡さない** | `langgraph dev` (Agent Server) が永続化をプラットフォーム側で提供するため |

> 公式ドキュメント (LangGraph persistence) の指針: 「Agent Server を使う場合、checkpointer や store を
> 手動で実装・設定する必要はない。サーバーが永続化インフラを裏で処理する」。

> **`.env` と LangSmith について:** `langgraph dev` を実行すると `agent.py` が import され、
> その中の `load_dotenv()` が**リポジトリのルートの `.env`** を読み込みます。これで OpenAI /
> LangSmith のキーが供給されるため、`langgraph.json` に `env` 指定は不要です。

### 起動から接続までの手順 (Google Cloud Shell)

使うターミナルは **1 つだけ**です。**UI はブラウザで開くだけなので、インストールは要りません。**

| | **【ターミナル】** | **【ブラウザ】** |
|---|---|---|
| 用意のしかた | **CLI 版で使ったターミナルをそのまま使う** | 新しいタブを開くだけ |
| 作業ディレクトリ | `chap06/hands-on` (`langgraph.json` がある場所) | — |
| venv | 有効化済み (`(.venv)` が付いている) | — |
| 役割 | **Agent Server (`langgraph dev`) を起動しっぱなしにする** | **Agent Chat UI (ホステッド版) を開く** |

#### ターミナル: Agent Server (`langgraph dev`) を起動する

CLI 版の続きなので、**追加の `cd` や venv 有効化は不要**です。
(ターミナルを開き直してしまった場合は、上の「セットアップ」の 4 行を先に実行してください)

```bash
langgraph dev --tunnel
```

- `langgraph dev` は `langgraph.json` を読むので、**`chap06/hands-on` にいることが必須**です。
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

> **⚠ Cloud Shell の [ウェブでプレビュー] でポート 2024 を公開した URL は使えません。**
> その URL (`https://2024-cs-....cloudshell.dev`) は「HTTPS 経由で**あなたのユーザーアカウントのみ**に
> アクセスを制限する」仕様のため
> ([公式ドキュメント](https://cloud.google.com/shell/docs/using-web-preview))、
> **別サイトである Agent Chat UI からの API 呼び出しは認証で弾かれ**、
> `Failed to connect to LangGraph server` になります。
> Agent Server の公開には**必ず `--tunnel` を使ってください**。

#### ブラウザ: Agent Chat UI を開く

ブラウザの新しいタブで **<https://agentchat.vercel.app>** を開きます。
LangChain 公式がホスティングしている Agent Chat UI で、**インストールも起動も不要**です。

> **これは「公式サイトに自分のエージェントを繋ぐ」のではありません。** Agent Chat UI は
> **あなたのブラウザの中だけで動く**アプリで、そこから【ターミナル】の Tunnel URL に直接つなぎます。
> 会話の中身が LangChain 側のサーバーを経由することはありません。

### 接続設定は 3 項目だけ

UI を開くと接続設定の入力画面が出ます。次の 3 項目を入力します。

| 設定項目 | 入力する値 | 補足 |
|---|---|---|
| **Deployment URL** | 【ターミナル】の **`🚀 API:` に表示された URL** (`https://xxxxxxxx.trycloudflare.com`) | Web Preview (ポート 2024) の URL は**使えません** |
| **Graph ID** | `expense` | `langgraph.json` の `graphs` のキー |
| **LangSmith API キー** | (空欄で可) | **ローカルサーバー接続時は不要** |

> **Graph ID は固定値ではありません。** ここで `expense` と入れるのは、このハンズオンの
> `langgraph.json` に `"graphs": {"expense": "./agent.py:agent"}` と書いてあるからです。
> 演習 6-C では `helpdesk` になります。**自分の `langgraph.json` を見て決める値**だと覚えてください。

> **`http://localhost:2024` は入力しても繋がりません。** Agent Chat UI は**あなたのブラウザの中**で
> 動いており、そこから見た `localhost` は「Cloud Shell」ではなく「あなたの PC」を指すためです。
> 必ず **`--tunnel` で発行された `https://....trycloudflare.com`** を入力してください。

### ブラウザで承認フローを操作する

チャット欄に **「山田さんへ経費 5000 円を送金してください」** と入力すると、
`transfer_money` を呼ぼうとした瞬間に **承認ダイアログ** が現れます。

**`transfer_money` は `allowed_decisions` に `edit` を含めているので、
ダイアログには Approve / Edit / Reject の 3 つが並びます。**
CLI 版の観察 4 で `Command(resume={"decisions": [{"type": "edit", ...}]})` と書いた操作が、
そのままボタンと入力欄になっている——ここを見比べてください。

- **Approve** … そのまま送金する (観察 3 と同じ)
- **Edit** … 金額を書き換えてから送金する (観察 4 と同じ)
- **Reject** … 理由を入力して拒否する (観察 5 と同じ)

「照会だけ」の依頼 (「山田さんの経費申請の状況を教えて」) では**ダイアログが出ない**ことも
確認してください。`get_expense` は `interrupt_on=False` で素通しに設定されているためです。

> **依頼文には宛先と金額を入れてください。** 「経費を精算して」のように曖昧だと、
> モデルが聞き返しで会話を終えてしまい、`transfer_money` が呼ばれません
> (= interrupt が起きず、承認ダイアログも出ません)。**呼ぶかどうかをモデルの遠慮に任せない**——
> 実行の可否は承認フローで人間が決める、というのが HITL の設計思想です (CLI 版と同じ)。

### 終わったらサーバーを止める

**ハンズオンを終えたら、ターミナルで `Ctrl+C` を押して `langgraph dev` を停止してください。**
起動したままにすると、演習 6-C で自分のエージェントのサーバーを起動するときにポートが塞がり、
起動に失敗します。

> **以降の章でもこの UI を使います。** 第7・8章でも `langgraph dev` + Agent Chat UI でエージェントを操作し、
> 最終章では「Web UI から操作できるヘルプデスク・マルチエージェント」として完成させます。

---

## トラブルシューティング

| 症状 | 確認すること |
|---|---|
| `ModuleNotFoundError: helpdesk_tools` / `expense_tools` | このディレクトリ (`hands-on/`) から `python handson_*.py` を実行しているか |
| `OPENAI_API_KEY` 関連のエラー | リポジトリのルートに `.env` を作成し、キーを記入したか (5-A のセットアップ) |
| (6-A) メールが redact されない | 入力に半角のメール形式 (`name@example.com`) が含まれているか |
| (6-B) `[中断なし]` と出て承認フローに入らない | 依頼文に宛先と金額が入っているか (例: 山田さんへ経費 5000 円を送金してください) |
| (6-B) 承認ダイアログが出ない | 【ターミナル】で `langgraph dev` が起動したままか。Graph ID が `expense` か |
| (6-B) `Failed to connect to LangGraph server` | Deployment URL に `http://localhost:2024` や Web Preview の URL (`https://2024-cs-....cloudshell.dev`) を入れていないか。`--tunnel` で発行された `https://....trycloudflare.com` を使う |
| (6-B) Tunnel の URL が見つからない | 出力の **`🚀 API:` の行**がそれ (`--tunnel` を付け忘れると `http://127.0.0.1:2024` になる)。起動のたびに URL は変わる |
| (6-B) `langgraph: command not found` | `pip install -U "langgraph-cli[inmem]"` を実行したか (仮想環境を有効化しているか) |
| (6-B) 演習でサーバーが起動しない | ハンズオンの `langgraph dev` を `Ctrl+C` で停止したか (ポートが塞がっている) |

> **`.env` と `__pycache__/` はコミットしないでください。** `.env` はリポジトリのルートに 1 つだけ置き、
> リポジトリに含めるのは値の入っていないルートの `.env.example` (ひな形) だけです。
