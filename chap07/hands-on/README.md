# ハンズオン 7-A: LangSmith のオフライン評価を一通り動かす

研修コース「Agentic AI 開発実践 - LangChain 版」/ 第7章「エージェントの評価」

教科書 7-3 で学んだオフライン評価の 4 ステップ——**① Dataset 作成 → ② evaluator 定義 →
③ Experiment 実行 → ④ 結果分析**——を、天気エージェントを題材に一通り実行するハンズオンです。
仕上げに pytest 統合 (`@pytest.mark.langsmith`) での実行も試します。

> **この章のキーメッセージ**: エージェントの評価は、まったく新しい基盤をゼロから覚えることでは
> ありません。第4章でトレーシングのために設定済みの **LangSmith** と、使い慣れた **pytest** の上に、
> 「LLM 特有の採点方法 (LLM-as-a-judge など)」を載せるだけです。

**所要時間の目安: 40 分** (講師と一緒に進めます)

---

## このハンズオンで動かすもの

```
hands-on/
├── README.md            # この手順書
├── requirements.txt     # 依存パッケージ (openevals / langsmith / pytest 等)
├── weather_agent.py     # 配布: 評価対象の天気エージェント (通常版 / 劣化版プロンプト)
├── create_dataset.py    # ステップ1: Dataset 作成 (client.create_dataset / create_examples)
├── run_evaluation.py    # ステップ2〜4: evaluator 3 本 + client.evaluate (--degraded で劣化版)
└── test_weather_eval.py # ステップ5: pytest 統合 (@pytest.mark.langsmith)
```

| ファイル | 何をするか | 観察するポイント |
|---|---|---|
| `create_dataset.py` | Dataset `weather-agent-evals` と Example 4 件を登録 | UI で Example の inputs / outputs スキーマ |
| `run_evaluation.py` | correctness / conciseness / trajectory_strict の 3 本で `client.evaluate` | スコア・judge の `comment`・比較ビューの赤/緑 |
| `test_weather_eval.py` | 同じ evaluator を pytest から実行 | 既存の pytest 資産にそのまま載ること |

evaluator 3 本の構成 (教科書 7-2 の「何を測るか × どう測るか」):

| evaluator | 何を測るか | どう測るか | 参照出力 |
|---|---|---|---|
| `correctness` | 最終応答の正確性 (主軸) | LLM-as-a-judge (`CORRECTNESS_PROMPT`) | 必要 (reference-based) |
| `conciseness` | 最終応答の簡潔性 | LLM-as-a-judge (`CONCISENESS_PROMPT`) | 不要 (reference-free) |
| `trajectory_strict` | 実行経路 (補助) | 決定的マッチ (`strict` モード) | コード内の参照トラジェクトリ |

---

## セットアップ (第5章ハンズオン 5-A の続き)

実行環境は **Google Cloud Shell** (Linux) です。**第5章ハンズオン (5-A) で、リポジトリの
clone・仮想環境 (venv) の作成・`.env` の設定 (OpenAI + LangSmith) は完了している前提**です。
まだの場合は 5-A の手順を先に実施してください。

1. (新しいタブの場合は) リポジトリ直下の venv を有効化:
   ```bash
   source <リポジトリ>/.venv/bin/activate
   ```
2. このハンズオンのディレクトリへ移動:
   ```bash
   cd <リポジトリ>/chap07/hands-on
   ```
3. このディレクトリの依存をインストール (この章では **openevals** が追加で入ります):
   ```bash
   pip install -r requirements.txt
   # (個別に入れる場合は: pip install openevals)
   ```

> **API キー / LangSmith について:** API キーはリポジトリのルートの共通 `.env` に記入済みです
> (5-A で設定)。各スクリプトは先頭で `load_dotenv()` を呼び、ルートの `.env` を読み込みます。
> 評価機能の入口は、第4章で設定した `LANGSMITH_TRACING` / `LANGSMITH_API_KEY` そのものです——
> 追加のセットアップはありません。

---

## 実行する

### ステップ 1: Dataset を作成する (①)

```bash
python create_dataset.py
```

期待する出力:

```text
======================================================================
Dataset 'weather-agent-evals' を作成し、Example を 4 件登録しました。
ブラウザで https://smith.langchain.com を開き、[Datasets & Experiments] から
'weather-agent-evals' を選んで、Example の inputs / outputs を確認してください。
======================================================================
```

LangSmith の UI で Dataset を開き、**Example が「質問 (inputs) + 模範応答 (outputs)」のペア**に
なっていることを確認します。この `question` / `answer` というキー名は、次のステップの
Target 関数・evaluator と揃えた「スキーマの契約」です。

### ステップ 2〜3: evaluator を定義して Experiment を実行する (②③)

```bash
python run_evaluation.py
```

`client.evaluate` が Dataset の Example を 1 件ずつ Target 関数に流し、3 本の evaluator で採点して、
結果を 1 つの **Experiment** として記録します。期待する出力 (抜粋):

```text
View the evaluation results for experiment: 'weather-agent-v1-xxxxxxxx' at:
https://smith.langchain.com/o/.../datasets/.../compare?selectedSessions=...

4it [00:xx, ...]
======================================================================
Experiment を作成しました: weather-agent-v1-xxxxxxxx
...
======================================================================
```

### ステップ 4 (前半): Experiment 画面で結果を読む (④)

表示された URL をブラウザで開き、次を確認します。

- Example ごとに **Inputs / Reference Output / Outputs** とスコア 3 列
  (`correctness` / `conciseness` / `trajectory_strict_match`) が表で並ぶこと
  (**列名は evaluator の `feedback_key` がそのまま使われます**)
- スコアをクリックすると、judge の **`comment` (判定理由)** と実行トレースまで掘り下げられること。
  文字列は一致していなくても意味的に正しければ correctness が True になる——7-1 で学んだ
  「非決定性への回答」を実物で確認してください

### ステップ 4 (後半): 劣化版プロンプトで再実行し、比較ビューで回帰を見る

「プロンプト改修がうっかり品質を下げてしまった」状況を再現します。`--degraded` を付けると、
評価対象が劣化版プロンプト (ペルソナ改修で応答が長くなり、ツールを使わないことがある版) に
切り替わり、`experiment_prefix` も `weather-agent-v2` に変わります。

```bash
python run_evaluation.py --degraded
```

実行後、LangSmith で Dataset `weather-agent-evals` を開き、**Experiments タブで
`weather-agent-v1-...` と `weather-agent-v2-...` の 2 つを選択して比較ビュー (Compare)** を開きます。

- スコアが**下がったケースは赤**、**上がったケースは緑**でハイライトされます
- 「どのケースが・どの評価軸で悪化したか」を特定し、judge の `comment` で原因を読みます
  (conciseness の悪化・trajectory の不一致が典型です)

これが教科書冒頭の「プロンプトを直したら別のケースが壊れた」を**リリース前に捕まえる**画面です。

### ステップ 5: pytest 統合で実行する (⑤)

```bash
pytest test_weather_eval.py --langsmith-output
```

- `@pytest.mark.langsmith` を付けたテストの**入出力・参照出力・評価スコア**が LangSmith に
  記録されます。ターミナルには LangSmith の結果 URL とテスト結果のテーブルが表示されます。
- 期待する出力: `2 passed` (judge も LLM なので、まれに判定が揺れて失敗することがあります。
  それ自体が「評価をテストに変換するとはどういうことか」の教材です)
- 使い分けの目安: **CI で毎コミット回すなら pytest 統合、Dataset を中心に複数バージョンを
  じっくり比較するなら `client.evaluate`** (教科書 7-3)。

### ステップ 6: 講師デモ (コードなし)

続けて講師が、**オンライン評価** (Tracing Project への自動ルール設定)・**Multi-turn Evals**
(Thread = 会話単位の評価)・**Insights** (本番トレースの自動分析) の画面を紹介します。
手元での操作はありません。オフライン評価 (リリース前) とオンライン評価 (本番監視) が
改善ループとして噛み合う全体像は、教科書 7-3 を参照してください。

---

## コードリーディングのポイント

実行できたら、ソースを開いて次を確認してください。

1. **スキーマの契約** (`create_dataset.py` ↔ `run_evaluation.py`)
   Dataset の `inputs["question"]` を Target 関数が読み、Target の戻り値 `{"answer": ...}` と
   Dataset の `outputs["answer"]` を evaluator が突き合わせる。キー名を揃えることが
   オフライン評価の組み立ての第一歩です。

2. **evaluator の契約は `key` / `score` / `comment`** (`run_evaluation.py`)
   openevals の evaluator は、LLM-as-a-judge もトラジェクトリマッチも LangSmith と
   共通の契約で結果を返します。だからこそ、
   手元のスクリプトで試した evaluator が `client.evaluate` にそのまま載ります
   (このハンズオンでは Target が `messages` も返すため、judge に `answer` だけを見せる
   薄いラッパーを挟んでいます。理由はソース冒頭の docstring 参照)。

3. **`feedback_key` = Experiment 画面の列名** (`run_evaluation.py`)
   `correctness` / `conciseness` という列名は `create_llm_as_judge` の `feedback_key` そのものです。
   プロンプトと `feedback_key` を差し替えるだけで、評価軸はいくらでも増やせます。

4. **judge は被評価エージェントと別モデル** (`run_evaluation.py` / `test_weather_eval.py`)
   評価対象は `weather_agent.MODEL`、採点役は `JUDGE_MODEL`。「書いた本人に採点させない」
   という定石をコード上の定数分離で表現しています。

---

## うまくいかないときは

| 症状 | 確認すること |
|---|---|
| `ModuleNotFoundError: openevals` | このディレクトリで `pip install -r requirements.txt` を実行したか (venv を有効化しているか) |
| `ModuleNotFoundError: weather_agent` | このディレクトリ (`weather_agent.py` のある場所) から実行しているか |
| `create_dataset.py` が「既に存在」と表示する | 正常です (再実行対策)。作り直す場合は UI で Dataset を削除してから再実行 |
| `client.evaluate` で Dataset が見つからない | 先に `python create_dataset.py` を実行したか。`DATASET_NAME` が一致しているか |
| `OPENAI_API_KEY` 関連のエラー | リポジトリのルートの `.env` に `OPENAI_API_KEY` を記入したか (5-A の手順) |
| LangSmith に記録されない | ルートの `.env` に `LANGSMITH_TRACING=true` と `LANGSMITH_API_KEY` があるか。pytest は `--langsmith-output` を付けたか |
| スコアが実行ごとに変わる | 正常です。エージェントも judge も LLM なので判定は揺れ得ます。だからこそ複数ケース・複数軸で継続的に測ります |

> **`.env` と `__pycache__/` はコミットしないでください。** `.env` はリポジトリのルートに 1 つだけ置き、
> リポジトリに含めるのは値の入っていないルートの `.env.example` (ひな形) だけです。

---

## 次のステップ

ハンズオンで評価の「動かし方」を体験したら、演習 7-B (`../exercise/`) で、**ヘルプデスク
エージェント v4 の回帰評価**を自分で組み立てます。Dataset と evaluator を整備し、プロンプト修正の
前後で Experiment を比較して、「直したケースは通ったが、別のケースが壊れた」を自分の手で捕まえます。
