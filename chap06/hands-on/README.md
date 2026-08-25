# ハンズオン 6-A: Prebuilt / Custom Middleware

研修コース「LangChain による Agentic AI 開発実践」/ 第6章「Middleware と HITL」

講師の解説を聞きながら、**作成済みのコードを一緒に実行する**ハンズオンです (受講者はコードを書きません)。
Middleware を「使う」(Prebuilt) と「作る」(Custom) の両方を、ヘルプデスクエージェントで動かして体感します。

---

## このハンズオンで確認すること

| スクリプト | テーマ | 内容 |
|---|---|---|
| `handson_6A_prebuilt.py` | Prebuilt Middleware を使う | `PIIMiddleware` でメールアドレスを redact、`ToolCallLimitMiddleware` でツール呼び出しを制限 |
| `handson_6A_custom.py` | Custom Middleware を作る | `@before_model` でメッセージ数をログ出力 (デコレータ式)、禁止ワードを `jump_to="end"` でブロック (クラス継承式) |

エージェント本体 (model / tools) には手を入れず、**`middleware` リストに足すだけ**で実運用機能が
後付けされる——この「積み木」のような感覚をつかむのが目的です。

---

## ファイル構成

```
hands-on/
├── README.md                 # この説明
├── requirements.txt          # 依存パッケージ (ピン留め済み)
├── helpdesk_tools.py         # 配布: search_faq / get_system_status (ローカル @tool)
├── handson_6A_prebuilt.py    # 6-2: PIIMiddleware + ToolCallLimitMiddleware
└── handson_6A_custom.py      # 6-3: @before_model ログ + ContentFilterMiddleware
```

> **ツールはローカル `@tool` です** (第5章のような MCP サーバーは立てません)。第6章の主題である
> Middleware / HITL に集中できるよう、`helpdesk_tools.py` に同梱しています。FAQ・稼働状況の
> データは第3〜5章のヘルプデスクと同じ内容です。

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
   cd <リポジトリ>/chap06/hands-on
   ```
3. このディレクトリの依存を追加インストール (前章までと共通なら差分のみ入ります):
   ```bash
   pip install -r requirements.txt
   ```
4. 実行 (LangSmith は 5-A で設定済みのルート `.env` により自動で有効。実行後に
   [smith.langchain.com](https://smith.langchain.com) でトレースを確認できます):
   ```bash
   python handson_6A_prebuilt.py   # 前半 (Prebuilt)
   python handson_6A_custom.py     # 後半 (Custom)
   ```

> **LangSmith でトレースを確認できます。** ルートの `.env` で LangSmith を有効化済みのため、
> [smith.langchain.com](https://smith.langchain.com) を開くと、`PIIMiddleware` で隠された入力や、
> `ToolCallLimitMiddleware` でブロックされたツール呼び出しを、トレース上で確認できます
> (コード変更は不要)。

---

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

---

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

## トラブルシューティング

| 症状 | 確認すること |
|---|---|
| `ModuleNotFoundError: helpdesk_tools` | このディレクトリ (`hands-on/`) から `python handson_6A_*.py` を実行しているか |
| `OPENAI_API_KEY` 関連のエラー | リポジトリのルートに `.env` を作成し、キーを記入したか (5-A のセットアップ) |
| メールが redact されない | 入力に半角のメール形式 (`name@example.com`) が含まれているか |

> **`.env` と `__pycache__/` はコミットしないでください。** `.env` はリポジトリのルートに 1 つだけ置き、
> リポジトリに含めるのは値の入っていないルートの `.env.example` (ひな形) だけです。
