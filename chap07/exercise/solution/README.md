# 演習 7-B【正解 (solution)】: ヘルプデスクの回帰評価 — ヘルプデスク Step 6

研修コース「Agentic AI 開発実践 - LangChain 版」/ 第7章「エージェントの評価」

このディレクトリは演習 7-B の**正解 (solution)** です。`create_dataset.py` (TODO①) と
`run_regression.py` (TODO②③ + 発展 TODO) がすべて埋まった完成版です。
**まずは `starter/` で自力で挑戦**し、詰まったとき・答え合わせのときにこちらを参照してください。
(セットアップ手順・評価基準は `starter/README.md` と共通です)

---

## 演習の狙い (対応する章目標 2・3)

- **章目標 2**: 評価の 3 要素 (Dataset・Target・evaluator) を、自分のエージェントに対して組み立てる
- **章目標 3**: LangSmith のオフライン評価 (Dataset 作成 → evaluator 定義 → Experiment 実行 →
  結果分析) を実行し、比較ビューで回帰を検出する

完成すると、**プロンプト修正の前後で Experiment を比較して回帰を検出できる**回帰評価の
仕組みが手に入ります。「プロンプトを直したら別のケースが壊れた」を、
リリース前の比較ビューで捕まえられる状態がゴールです。

---

## ヘルプデスク Step 6 の位置づけ

| 章 | 追加する要素 | 演習後の姿 |
|---|---|---|
| 第6章 | Middleware / HITL / Agent Chat UI | PII 保護 + 要承認 + ブラウザ操作 (v4) |
| **第7章 (この演習)** | **評価 (LangSmith オフライン評価)** | **回帰評価つきエージェント: プロンプト修正の前後を Experiment で比較できる** |

> **このエージェントは使い捨てではありません。** 第8章 (マルチエージェント) でも、ここで作った
> 「回帰評価で品質を確かめながら変更できるエージェント」を土台に拡張していきます。

---

## ファイル構成

```
solution/
├── README.md            # この説明
├── requirements.txt     # 依存パッケージ (openevals / langsmith 等)
├── helpdesk_tools.py    # 配布: 第6章から引き継いだ 4 ツール (starter と同一)
├── helpdesk_agent.py    # 配布: v4 完成品 + 評価用 build_eval_agent (starter と同一)
├── create_dataset.py    # ステップ 1: Dataset 作成 (完成版・TODO① 埋め済み)
└── run_regression.py    # ステップ 2〜4: 回帰評価 (完成版・TODO②③ + 発展 埋め済み)
```

---

## TODO①②③ + 発展 の解答ポイント

| TODO | 内容 | 解答の要点 |
|---|---|---|
| **①** Example のスキーマ組み立て | `client.create_examples` に渡すリスト | 1 件 = `{"inputs": {"question": 問い合わせ文}, "outputs": {"answer": 模範応答}}`。キー名は Target・evaluator と揃える「契約」 |
| **②** correctness evaluator | `create_llm_as_judge` の 3 引数 | `prompt=CORRECTNESS_PROMPT` (reference-based) / `feedback_key="correctness"` (= 列名) / `model=JUDGE_MODEL` (被評価エージェントとは別のモデル) |
| **③** Experiment 実行 | `client.evaluate` の呼び出し | 第 1 引数に Target 関数、`data=DATASET_NAME`、`evaluators=[...]`、`experiment_prefix` にバージョン名、`max_concurrency=2`。openevals の evaluator は `key`/`score`/`comment` の共通契約なのでそのまま渡せる |
| **発展** 独自基準の evaluator | カスタムプロンプト + reference-free | 採点基準 (敬語チェック) を自然言語で書き、`{inputs}` / `{outputs}` プレースホルダを入れる。`{reference_outputs}` を使わないので reference-free。`feedback_key="politeness"` で新しい列が増える |

つまずきやすいポイント:

- **①のキー名ずれ**: `inputs` を `{"query": ...}` などにすると Target 関数 (`inputs["question"]`) が
  KeyError になります。スキーマは「Dataset ↔ Target ↔ evaluator」の 3 者で揃える契約です。
- **②の judge モデル**: 被評価エージェントと同じモデルを指定しても動きますが、
  「書いた本人に採点させない」という定石に反します。solution では
  `JUDGE_MODEL` 定数で分離しています。
- **③の `experiment_prefix`**: base と v2 で同じ接頭辞にすると、比較ビューでどちらが
  どちらか分からなくなります。バージョンを接頭辞に刻むのが後で比較するコツです。

---

## 実行と結果の読み方

セットアップは `starter/README.md` と共通ですが、**移動先のディレクトリだけが違います**。
次の 4 行を上から順に実行してから、同じターミナルで実行します。

```bash
cd ~/developing-agentic-ai-with-langchain   # (1) リポジトリのルートへ
source .venv/bin/activate                   # (2) venv を有効化 (必ずルートで)
cd chap07/exercise/solution                 # (3) このディレクトリへ
pip install -r requirements.txt             # (4) 依存をインストール
```

```bash
python create_dataset.py              # ステップ 1: Dataset 作成 (初回のみ)
python run_regression.py              # ステップ 3: 修正前 (base) の Experiment
python run_regression.py --prompt v2  # ステップ 4: 修正後 (v2) の Experiment
```

その後、LangSmith で Dataset `helpdesk-agent-evals` を開き、Experiments タブで
base と v2 の 2 つを選択して比較ビュー (Compare) を開きます。

### 期待される比較結果 (典型例)

v2 プロンプトの変更点は「VPN 問い合わせで稼働状況も案内する (改善)」+「回答を 2 文以内に
簡潔化 (副作用あり)」でした (`helpdesk_agent.py` の docstring 参照)。典型的には次のようになります。

| ケース | base | v2 | 読み方 |
|---|---|---|---|
| 1. VPN トラブル | correctness **False** になりやすい | **True** (緑 = 改善) | base は FAQ の手順だけ答え、模範応答にある「メンテナンス中」の情報が欠ける。v2 は get_system_status も呼ぶため揃う |
| 2. パスワード忘れ | **True** | **False** になりやすい (赤 = 回帰) | v2 の「2 文以内・補足省略」の副作用で、模範応答にある「ロック時は情報システム部で本人確認」が落ちる。judge の comment に「参照出力にある〜が欠けている」旨が出る |
| 3. 経費精算の稼働確認 | **True** | **True** (変化なし) | どちらのプロンプトでも get_system_status で正しく答えられる安定ケース |

**「直したケース (VPN) は緑になったが、別のケース (パスワード) が赤くなった」**——これが
本章冒頭の「回帰」を比較ビューで捕まえた瞬間です。赤いスコアをクリックし、judge の
`comment` から「何が欠けたのか」を 1 行で説明できれば、この演習の山場はクリアです。

> **注意: 毎回この表のとおりになるとは限りません。** エージェントも judge も LLM なので、
> スコアは揺れ得ます (たとえば v2 でもケース 2 が 2 文に収まりきって True になることがあります)。
> 差が出なかったら再実行してみてください。「揺れるからこそ、複数ケースの Dataset で
> 継続的に測る」——それ自体が本章の学びです。

### 発展 (オプション): politeness 列

> 発展 TODO は**オプション**です。時間に余裕がある場合に取り組んでください。

solution の `run_regression.py` には、発展 TODO の解答例として「応答が丁寧な敬語か」を判定する
reference-free evaluator (`feedback_key="politeness"`) が入っています。実行すると Experiment 画面に
`politeness` 列が増えます。**プロンプトと `feedback_key` を差し替えるだけで評価軸を増やせる**こと、
そして reference-free なので**模範解答のない本番トレース (オンライン評価) にも転用できる**ことを
確認してください。

---

## トラブルシューティング

`starter/README.md` のトラブルシューティング表を参照してください。solution 固有の注意:

| 症状 | 確認すること |
|---|---|
| starter で作った Dataset と模範応答が食い違う | starter の TODO① で模範応答を変えた場合は、UI で Dataset を削除し、solution の `create_dataset.py` で作り直す |
| 比較ビューが典型例の表と違う | 正常の範囲です (上記「注意」参照)。傾向を見るには同じバージョンで Experiment をもう 1 回作って並べる |

> **`.env` と `__pycache__/` はコミットしないでください。** `.env` はリポジトリのルートに 1 つだけ置き、
> リポジトリに含めるのは値の入っていないルートの `.env.example` (ひな形) だけです。
