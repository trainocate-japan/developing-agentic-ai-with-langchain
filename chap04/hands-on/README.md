# ハンズオン 4-A: Checkpointer と LangSmith トレース

研修コース「Agentic AI 開発実践 - LangChain 版」 / **第4章「メモリと可観測性」** のハンズオン用コードです。

- **ファイル**: [`chap04_handson_4A.ipynb`](./chap04_handson_4A.ipynb)
- **形式**: Google Colab Notebook (Jupyter nbformat 4)
- **対応する学習トピック**: Checkpointer (`InMemorySaver` / `thread_id`) / LangSmith トレース (有効化・tags・metadata・3 点チェック)
- **演習設計**: ハンズオン 4-A (手順 1〜4。4-2 checkpointer / thread_id、4-4 トレース有効化 / 読解ワークシート)

## 概要

このハンズオンは、講師の解説を聞きながら**作成済みのセルを上から順に一緒に実行する**形式です
(受講者がコードを書く場面はありません。コードを書くのは演習 4-B です)。
第3章で未解決だった「会話を覚えない」問題を **checkpointer の 2 行**で解決し、さらに
「エージェントの頭の中が見えない」問題を **環境変数 2 つ**で解決します。
題材は中立な教材として**天気エージェント** (`get_weather`) を使い、ヘルプデスクへの応用は演習 4-B に回します。

## Google Colab での開き方

GitHub リポジトリに配置した `.ipynb` は、次の **[Google Colab で開く] バッジ**から直接起動できます。

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/trainocate-japan/developing-agentic-ai-with-langchain/blob/main/chap04/hands-on/chap04_handson_4A.ipynb)

> **バッジの仕組み**: Colab は `https://colab.research.google.com/github/<OWNER>/<REPO>/blob/<BRANCH>/<パス>.ipynb`
> という URL で GitHub 上の Notebook を直接読み込みます。
> 本リポジトリでは `<OWNER>` = `trainocate-japan`、`<REPO>` = `developing-agentic-ai-with-langchain`、`<BRANCH>` = `main` です。
>
> **Notebook 自体の先頭にも同じバッジを埋め込んであります**。GitHub 上で `.ipynb` を開けば、
> この README を経由しなくても [Open In Colab] ボタンから直接起動できます。
>
> バッジを使わない場合は、Colab のメニュー `ファイル > ノートブックを開く > GitHub` タブに
> リポジトリ URL を貼り付けても開けます。

## 前提条件

- **Google アカウント**を持っていること
- **Google Colab** が使えること (ブラウザのみで OK。インストール不要)
- Colab の **[シークレット]** (左サイドバーの鍵アイコン 🔑) に **2 種類のキー**が登録されていること

  | シークレット名 | 用途 | 準備方法 |
  |---|---|---|
  | `OPENAI_API_KEY` | OpenAI API 認証 | 第1章の演習 1-1 で登録済みのはず。未登録でも Notebook 冒頭 (0-2) の手順で登録できます |
  | `LANGSMITH_API_KEY` | **本章で新規に必要**。トレース送信の認証 | Notebook 冒頭 (0-3) の手順で、無料アカウント作成 → API キー発行 → シークレット登録 |

- インターネット接続 (API を呼び出します)

> **LangSmith は本章で初めて使います。** [smith.langchain.com](https://smith.langchain.com) で**無料アカウント**を作成し
> (クレジットカード不要)、Settings → API Keys から API キーを発行して、Colab シークレットに
> `LANGSMITH_API_KEY` として登録してください。詳しい手順は Notebook の「0-3. LangSmith のセットアップ」にあります。
>
> **API キーの扱い**: キーはコードに直接書かず、必ず Colab シークレットで管理します。
> Notebook は「Colab シークレット方式 + 非 Colab 環境の環境変数フォールバック」の両対応です。

## 各セクションの狙い

| セクション | 狙い | 期待される出力 / トレースで見えること |
|---|---|---|
| 0. セットアップ | パッケージ導入、OpenAI / LangSmith のキー設定、`MODEL` 準備、トレース有効化 (環境変数 2 つ + プロジェクト) | `LANGSMITH_TRACING: true` / 各キー設定済みの表示 |
| 1. 天気ツール | 第3章の `get_weather` (`@tool`) を用意 (動かすだけ) | `東京の天気: 晴れ、気温 24 度` |
| 2. checkpointer なし | **対比の出発点**。記憶しないエージェントが名前を忘れることを再確認 | 2 回目の invoke で名前を覚えていない |
| 3. checkpointer あり (4-2) | `InMemorySaver` を **2 行**追加。同じ `thread_id` で継続、変えると分離、戻すと残る | thread 1 は名前を記憶 / thread 2 は白紙 / thread 1 復帰で記憶あり |
| 4. messages の累積 | invoke のたびに messages 件数が増えるのを観察 (= 履歴全体が毎回送られる証拠) | 件数が `2 → 4 → …` と増える。config なしはエラー |
| 5. トレース有効化 (4-4) | **コード変更ゼロ**でトレース送信。`config` の `tags` / `metadata` で整理 | smith.langchain.com にトレースが出現。タグ・メタデータが付く |
| 6. ループが増える例 | 「東京と大阪を比べて」で `get_weather` が 2 回呼ばれ、ループが増える | 呼ばれたツールに `get_weather` が 2 回 |
| 7. 読解ワークシート | 3 点チェック (周回数 / ツールと引数 / トークン) を記入。checkpointer の効果も入力で確認 | ワークシートが埋まる / 2 回目入力に 1 回目の会話が含まれる |

## このハンズオンのキーポイント

- **追加は実質 2 行**: `from langgraph.checkpoint.memory import InMemorySaver` と
  `create_agent(..., checkpointer=InMemorySaver())`。これだけで会話を記憶します。
- **thread_id は「会話の鍵」**: 同じ鍵なら続き、違う鍵なら新規、元の鍵に戻れば元の続き。
  checkpoint は thread ごとに独立して保存されます。
- **トレースの有効化はコード変更ゼロ**: 環境変数 `LANGSMITH_TRACING` と `LANGSMITH_API_KEY` の 2 つだけ。
  `LANGSMITH_PROJECT` でプロジェクトを分け、`config` の `tags` / `metadata` で整理します
  (`tags` / `metadata` は `configurable` と**同じ階層**に書きます)。
- **3 点チェック**: ①ループ周回数 ②ツールと引数 ③トークン消費。
  2 回目の invoke のモデル入力に過去の会話が含まれること (checkpointer の効果) もトレースで確認できます。

## 実行時の注意

- 本教材のモデル名 `MODEL = "openai:gpt-5.4"` は**将来モデルの例示**です。研修実施時は講師が指定する
  最新モデル名に準備セル 1 箇所で差し替えてください (`"provider:model"` 形式)。
- `!pip install -U langchain langchain-openai` は最新版を取りに行きます。再現性が必要な研修では
  バージョンのピン留め (langchain 1.3.x / langchain-openai 1.3.x) を推奨します。
  `InMemorySaver` は `langgraph` 同梱、LangSmith のトレースも追加パッケージなしで動きます。
- `LANGSMITH_API_KEY` をまだ用意できなくても、checkpointer の実験 (セクション 2〜4) はそのまま動きます。
  トレース部分 (セクション 5〜7) だけ後で実施しても構いません。
- LLM の応答は実行のたびに多少変わります。トークン数やループ周回数の**正確な値は実行・モデルにより変動**します
  (ワークシートには「あなたのトレースで見えた値」を記入してください)。

## 次のステップ

このハンズオンで習得した部品 (checkpointer / thread_id / tags / metadata / トレース読解) を総動員して、
演習 4-B (`../exercise/`) で「**社内 IT ヘルプデスクエージェント v2**」を構築します (ヘルプデスク Step 3)。
問い合わせのたびに会話を忘れる v1 を、**社員ごとに会話を記憶し、運用チームがトレースで診断できる v2** へ
拡張します。`# TODO` を埋める形式です。
