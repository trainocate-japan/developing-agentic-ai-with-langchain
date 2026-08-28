# ハンズオン 3-A: create_agent で最初のエージェント

研修コース「Agentic AI 開発実践 - LangChain 版」 / **第3章「エージェント開発の基本」** のハンズオン用コードです。

- **ファイル**: [`chap03_handson_3A.ipynb`](./chap03_handson_3A.ipynb)
- **形式**: Google Colab Notebook (Jupyter nbformat 4)
- **対応する学習トピック**: init_chat_model / Messages / create_agent / @tool
- **演習設計**: ハンズオン 3-A (手順 1〜4。3-1 モデル初期化 / 3-2 Messages / 3-3 create_agent / 3-4 @tool)

## 概要

このハンズオンは、講師の解説を聞きながら**作成済みのセルを上から順に一緒に実行する**形式です
(コードを書く場面はありません。コードを書くのは演習 3-B です)。
第2章で**手書き**した Function Calling の while ループが、LangChain の `create_agent` でわずか数行になる——
その「消えたコード」の行方を、軌跡を読み解きながら 1 つずつ突き止めます。
題材は公式 quickstart 準拠の**天気エージェント** (`get_weather`) で、ヘルプデスクへの応用は演習 3-B に回します。

## Google Colab での開き方

GitHub リポジトリに配置した `.ipynb` は、次の **[Google Colab で開く] バッジ**から直接起動できます。

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/trainocate-japan/developing-agentic-ai-with-langchain/blob/main/chap03/hands-on/chap03_handson_3A.ipynb)

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
- Colab の **[シークレット]** (左サイドバーの鍵アイコン 🔑) に `OPENAI_API_KEY` を登録済みであること
  - 第1章の演習 1-1 で登録済みのはずです。未登録なら Notebook 冒頭の手順に従って登録してください
- インターネット接続 (API を呼び出します)

> **API キーの扱い**: キーはコードに直接書かず、必ず Colab シークレットで管理します。
> Notebook は「Colab シークレット方式 + 非 Colab 環境の環境変数フォールバック」の両対応です。

## 各セクションの狙い

| 節 | 狙い | 期待される出力例 |
|---|---|---|
| 0. セットアップ | `langchain` / `langchain-openai` のインストール、API キー読込、`MODEL` の準備 | `準備完了。使用モデル: openai:gpt-5.4` |
| 3-1. init_chat_model | `"provider:model"` 形式で初期化。戻り値が `AIMessage` (文字列でない) ことを確認。`temperature` 0/1 の揺れ比較 | `戻り値の型: <class '...AIMessage'>` / temp=0 はほぼ同じ句 |
| 3-2. Messages | `SystemMessage`/`HumanMessage`/`AIMessage` で会話構成。dict 形式も等価。`usage_metadata` / `content_blocks` を観察 | 翻訳結果 / `{'input_tokens': .., ..}` / `[{'type': 'text', ..}]` |
| 3-3. create_agent | 天気エージェントを構築し軌跡をダンプ。第2章の手動ループと対比。戻り値 `CompiledStateGraph`。ステートレス実験 | `HumanMessage → AIMessage(tool_calls) → ToolMessage → AIMessage` |
| 3-4. @tool | `@tool` でスキーマ生成を確認。docstring 品質 (明確 vs 曖昧) がツール選択に与える影響を比較 | 明確版は `get_news_clear` を安定選択 |

## 実行時の注意

- 本教材のモデル名 `MODEL = "openai:gpt-5.4"` は**将来モデルの例示**です。研修で案内されるモデル名に
  準備セル 1 箇所で差し替えてください (`"provider:model"` 形式)。
- `!pip install -U langchain langchain-openai` は最新版を取りに行きます。本教材は
  langchain 1.3.x / langchain-openai 1.3.x を前提としており、バージョンによっては挙動が変わることがあります。
- reasoning 系モデルでは `temperature` 等が指定不可の場合があります。3-1 でパラメータ関連の
  エラーが出たら、それは「このモデルはそのパラメータ非対応」のサインです。
- 3-4 の docstring 比較実験は LLM の判断に依存するため、**実行のたびに結果が多少変わる**ことがあります
  (それ自体が「曖昧な docstring は選択が不安定になる」という学びです)。

## 次のステップ

このハンズオンで習得した部品 (`init_chat_model` / Messages / `create_agent` / `@tool`) を総動員して、
演習 3-B (`../exercise/`) で「**社内 IT ヘルプデスクエージェント v1**」を構築します。
FAQ 検索ツールの追加と、`SupportAnswer` (Pydantic) による構造化出力 (`response_format`) を、
`# TODO` を埋めながら自分の手で実装します。
