# 演習 7-B【演習 (starter)】: ヘルプデスクの回帰評価 — ヘルプデスク Step 6

研修コース「Agentic AI 開発実践 - LangChain 版」/ 第7章「エージェントの評価」

このディレクトリは演習 7-B の**演習用 (starter)** です。**TODO①②③** (と発展 TODO) を
自分で埋めて完成させてください。完成版は `solution/` にあります。まずは自力で挑戦しましょう。

**所要時間の目安: 50 分** (発展 TODO を除く)

---

## シナリオ

第6章までに構築したヘルプデスクエージェント v4 は、プロンプトを直すたびに Agent Chat UI から
手で叩いて確認してきました。しかしケースが増えるにつれ、**手動確認はスケールしない**ことが
はっきりしてきます。そこでこの演習では、**代表的な問い合わせケースの Dataset と evaluator を
整備し、プロンプト修正の前後で Experiment を比較して回帰を検出できる状態**を作ります。
教科書冒頭の「プロンプトを直したら別のケースが壊れた」を、自分の手で捕まえるのがゴールです。

## 演習の狙い (対応する章目標 2・3)

- **章目標 2**: 評価の 3 要素 (Dataset・Target・evaluator) を、自分のエージェントに対して組み立てる
- **章目標 3**: LangSmith のオフライン評価 (Dataset 作成 → evaluator 定義 → Experiment 実行 →
  結果分析) を実行し、比較ビューで回帰を検出する

---

## ヘルプデスク Step 6 の位置づけ (UI 手動確認の限界 → 回帰評価)

| 章 | 追加する要素 | 演習後の姿 |
|---|---|---|
| 第6章 | Middleware / HITL / Agent Chat UI | PII 保護 + 要承認 + ブラウザ操作 (v4) |
| **第7章 (この演習)** | **評価 (LangSmith オフライン評価)** | **回帰評価つきエージェント: プロンプト修正の前後を Experiment で比較できる** |

> **v4 はそのまま使います。** `helpdesk_agent.py` にはステップ 0 用の v4 完成品 (トップレベル変数
> `agent`) と、回帰評価用の `build_eval_agent()` (読み取り系 2 ツール・プロンプト切り替え付き) の
> 両方が入っています。評価用が読み取り系 2 ツール構成である理由 (HITL の interrupt は自動一括評価と
> 相性が悪い) は、`helpdesk_agent.py` の docstring を読んでください。

---

## ファイル構成

```
starter/
├── README.md            # この説明
├── requirements.txt     # 依存パッケージ (openevals / langsmith / langgraph-cli 等)
├── helpdesk_tools.py    # 配布: 第6章から引き継いだ 4 ツール (編集不要)
├── helpdesk_agent.py    # 配布: v4 完成品 + 評価用 build_eval_agent (編集不要)
├── langgraph.json       # ステップ 0 用: langgraph dev がエージェントを読み込む
├── create_dataset.py    # ステップ 1: Dataset 作成。★TODO① をあなたが埋める
└── run_regression.py    # ステップ 2〜4: 回帰評価。★TODO②③ (+ 発展 TODO) をあなたが埋める
```

- あなたが編集するのは **`create_dataset.py` の TODO①** と **`run_regression.py` の TODO②③**
  (+ 任意の発展 TODO) だけです。
- starter は **TODO を埋めるまで動きません** (実行すると NotImplementedError で止まります)。

---

## セットアップ (第5章ハンズオン 5-A の続き)

実行環境は **Google Cloud Shell** (Linux) です。**第5章ハンズオン (5-A) で、リポジトリの
clone・仮想環境 (venv) の作成・`.env` の設定 (OpenAI + LangSmith) は完了している前提**です。

ブラウザで **<https://shell.cloud.google.com/>** を開き (Cloud Shell を開く手順は
第5章ハンズオン 5-A の README「ステップ 0」を参照)、ターミナルで次の 4 行を上から順に実行します。
**新しいターミナルを開いた直後や、しばらく放置して再接続したあとも、この 4 行をそのまま実行すれば
作業を再開できます。**

```bash
cd ~/developing-agentic-ai-with-langchain   # (1) リポジトリのルートへ
source .venv/bin/activate                   # (2) venv を有効化 (必ずルートで。プロンプトに (.venv) が付く)
cd chap07/exercise/starter                  # (3) このディレクトリへ
pip install -r requirements.txt             # (4) 依存をインストール (このディレクトリで 1 回でよい)
                                            #     (この章では openevals が追加で入ります)
```

> - **venv の有効化はリポジトリのルートで行います。** 章のディレクトリには `.venv` がないため、
>   そこで `source .venv/bin/activate` を実行すると `No such file or directory` になります。
> - リポジトリを `~` 以外に clone した場合は、`~/developing-agentic-ai-with-langchain` を実際の場所に読み替えてください。

以降のコマンドは、断りがない限り**すべてこのディレクトリ (`chap07/exercise/starter`) で実行します**。

> **API キー / LangSmith について:** API キーはリポジトリのルートの共通 `.env` に記入済みです
> (5-A で設定)。各スクリプトは先頭で `load_dotenv()` を呼び、ルートの `.env` を読み込みます。
> LangSmith の環境変数 (`LANGSMITH_TRACING` / `LANGSMITH_API_KEY`) は第4章で設定したものが
> そのまま評価機能の入口になります。

---

## ステップ 0 (導入): Agent Chat UI で 1 ケース手動確認

TODO に入る前に、「手動確認」を 1 回だけ体験しておきます。第6章の演習と同じ手順で
`langgraph dev` を起動し、Agent Chat UI から v4 に 1 ケース聞いてみてください。

**【ターミナル 1】** (= セットアップで使ったターミナル) で、`chap07/exercise/starter`
(`langgraph.json` がある場所) にいることを確認してから起動します。

```bash
langgraph dev --tunnel
```

起動後のバナーの **`🚀 API:` の行**に出る URL (`https://....trycloudflare.com`) が
Tunnel の URL です (`--tunnel` を付けると API の URL がそのまま公開 URL になります)。
**Cloud Shell の Web Preview でポート 2024 を公開した URL は、認証で弾かれるため使えません**
(理由は第6章 6-B の README を参照)。

**【ターミナル 2】** をツールバーの **[+]** で新しく開き、Agent Chat UI を起動します
(詳しい手順・接続設定は第6章 演習 6-B の README「起動から接続までの手順」と同じです)。

```bash
cd ~                                                  # ホームディレクトリへ (venv は不要)
npx create-agent-chat-app@latest --project-name my-chat-ui --package-manager npm --framework nextjs --include-agent react --install-deps true   # 6-B で作成済みならこの行は不要
cd ~/my-chat-ui/apps/web                              # UI (web) のディレクトリへ
npm run dev                                           # UI を起動 (ポート 3000)
```

> **起動するのは `apps/web` だけです。** ルート (`~/my-chat-ui`) で `npm run dev` すると、使わない
> 同梱 Agent Server (`apps/agents`) も起動して `ERR_PACKAGE_PATH_NOT_EXPORTED` が出ます
> (理由は第6章 6-B の README と同じ)。

Cloud Shell の **[ウェブでプレビュー] → [ポートを変更]** で **3000** を開き、
接続設定に次を入力します。

| 設定項目 | 入力する値 |
|---|---|
| **Deployment URL** | 【ターミナル 1】の **`🚀 API:` に表示された URL** (`https://xxxxxxxx.trycloudflare.com`) |
| **Graph ID** | `helpdesk` |
| **LangSmith API キー** | (空欄で可) |

> **`http://localhost:2024` では繋がりません。** UI はあなたのブラウザの中で動いているため、
> そこから見た `localhost` は Cloud Shell ではなくあなたの PC を指します (第6章 6-B と同じ理由)。

接続できたら、たとえば **「VPN に繋がらないのですが、どうすればいいですか?」** と入力して
応答を確認します。

1 ケースなら簡単です。しかし「プロンプトを 1 行直すたびに、VPN もパスワードも稼働確認も
全部 UI から打ち直す」のは現実的ではありません。ここから先、この確認を**自動評価**に置き換えます。
(確認できたら `langgraph dev` は Ctrl+C で止めて構いません)

---

## 課題ステップと TODO

### ステップ 1 (`create_dataset.py` / TODO①): 代表 3 ケースの Example を完成させる

代表的な問い合わせ 3 ケース (VPN トラブル / パスワード忘れ / 経費精算システムの稼働確認) の
問い合わせ文と模範応答は、配布素材としてファイル内に用意してあります。あなたの仕事は、それを
`client.create_examples` に渡す **Example のスキーマ**——`{"inputs": {...}, "outputs": {...}}` の
リスト——に組み立てることです。

- `inputs` は Target 関数に渡る入力、`outputs` は **evaluator だけが参照する期待出力**です
- キー名は `run_regression.py` の Target・evaluator と揃える必要があります (スキーマの契約)

完成したら実行して、LangSmith の UI で Dataset を確認します:

```bash
python create_dataset.py
```

### ステップ 2 (`run_regression.py` / TODO②): correctness evaluator を組み立てる

`create_llm_as_judge` に `prompt` / `feedback_key` / `model` の 3 引数を渡して、
最終応答の正確性を採点する LLM-as-a-judge を組み立てます。

> **ヒント:**
> - `feedback_key` は、そのまま Experiment 画面の**列名**になります。
> - judge の `model` には、被評価エージェントとは**別のモデル**を指定します
>   (「書いた本人に採点させない」——教科書 7-2 参照)。ファイル内の `JUDGE_MODEL` を使ってください。

### ステップ 3 (`run_regression.py` / TODO③): 修正前 (base) の Experiment を実行する

`client.evaluate` に Target 関数・Dataset 名・`evaluators`・`experiment_prefix` を渡して、
Experiment を実行します。完成したら:

```bash
python run_regression.py
```

表示された URL から Experiment 画面を開き、3 ケースのスコアと judge の `comment` を読みます。

### ステップ 4: プロンプト修正パッチを適用して再実行し、比較ビューで読解する

配布の `helpdesk_agent.py` には「プロンプト修正パッチ適用後」の v2 プロンプトが入っています
(VPN 対応の強化 + 回答の簡潔化。詳細は同ファイルの docstring)。`--prompt v2` で切り替えて
`experiment_prefix` の異なる 2 つ目の Experiment を作ります:

```bash
python run_regression.py --prompt v2
```

> **ヒント:** 比較ビューは、Dataset の画面で **2 つの Experiment を選択**すると開けます
> (Experiments タブ → base と v2 にチェック → Compare)。

比較ビューで、**どのケースが改善し (緑)、どのケースが劣化したか (赤)** を特定し、
judge の `comment` から**原因を 1 行で説明**してください。「一部を改善する修正が別のケースを
僅かに劣化させる」——現実のプロンプト修正で起きるこの現象を捕まえられたら、この演習は合格です。

### ステップ 5 (発展・任意): 独自基準の evaluator を追加する

「応答がビジネスにふさわしい敬語であること」のような独自基準を、カスタムプロンプトの
reference-free evaluator として追加します (`run_regression.py` の「TODO 発展」)。
追加して再実行すると、Experiment 画面に新しい列 (例: `politeness`) が増えます。

---

## 評価基準 (この演習で身についたかの確認観点)

1. **Dataset の構成**: Example の `inputs` / `outputs` スキーマを、Target 関数・evaluator と
   整合する形で組み立てられている (TODO①)
2. **evaluator の組み立て**: `prompt` / `feedback_key` / `model` それぞれの役割を理解して
   `create_llm_as_judge` を構成できている (TODO②)
3. **回帰の読解**: 比較ビューでスコアが変化したケースを特定し、judge の `comment` から
   「なぜ改善 / 劣化したのか」を説明できる (ステップ 4)

---

## 期待成果物 (この演習のゴール)

- LangSmith 上の Dataset **`helpdesk-agent-evals`** (代表 3 ケースの Example 入り)
- **base / v2 の 2 つの Experiment** と、その比較ビュー
- 比較ビューの読解メモ: 改善したケース・劣化したケースと、`comment` から読み取った原因

---

## トラブルシューティング

| 症状 | 確認すること |
|---|---|
| `NotImplementedError: TODO...` | その TODO をまだ埋めていません。メッセージ中の TODO 番号の箇所を実装してください |
| `ModuleNotFoundError: openevals` | このディレクトリで `pip install -r requirements.txt` を実行したか (venv を有効化しているか) |
| `ModuleNotFoundError: helpdesk_agent` / `helpdesk_tools` | このディレクトリから実行しているか (同じ場所に対象の `.py` がある) |
| `client.evaluate` で Dataset が見つからない | 先に `python create_dataset.py` を実行したか (TODO① を埋めてから) |
| Dataset の Example が 0 件 / スキーマが変 | TODO① の形が `{"inputs": {"question": ...}, "outputs": {"answer": ...}}` になっているか。UI で Dataset を削除して作り直せます |
| 比較ビューで差が出ない | 2 つの Experiment が同じ Dataset に対するものか。スコアの揺れで差が消えることもあります (再実行してみる) |
| スコアが実行ごとに変わる | 正常です。エージェントも judge も LLM なので判定は揺れ得ます。だからこそ複数ケースで継続的に測ります |
| `langgraph: command not found` (ステップ 0) | `pip install -U "langgraph-cli[inmem]"` を実行したか (仮想環境を有効化しているか) |
| Agent Chat UI から Agent Server に繋がらない (ステップ 0) | Deployment URL に `http://localhost:2024` や Web Preview (ポート 2024) の URL を入れていないか。`--tunnel` で発行された `https://....trycloudflare.com` (出力の `🚀 API:` の行) を使う |

> **`.env` と `__pycache__/` はコミットしないでください。** `.env` はリポジトリのルートに 1 つだけ置き、
> リポジトリに含めるのは値の入っていないルートの `.env.example` (ひな形) だけです。
