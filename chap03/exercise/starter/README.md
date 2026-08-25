# 演習 3-B【starter / 問題】: ヘルプデスクエージェント v1 — ヘルプデスク Step 2

研修コース「Agentic AI 開発実践 - LangChain 版」 / **第3章「エージェント開発の基本」** の演習用コード (TODO 穴埋め版) です。

- **ファイル**: [`chap03_exercise_3B_starter.ipynb`](./chap03_exercise_3B_starter.ipynb)
- **正解**: [`../solution/chap03_exercise_3B_solution.ipynb`](../solution/chap03_exercise_3B_solution.ipynb)
- **形式**: Google Colab Notebook (Jupyter nbformat 4)
- **対応する学習トピック**: @tool / create_agent / 構造化出力 (response_format) / 軌跡の読解
- **対応する学習目標**: 章目標 3・4・5 (+ 章目標 1・2 はハンズオンで確認)

## 演習の狙い

第2章 (Step 1) で**手動の Function Calling ループ**として実装したヘルプデスク QA を、
本章で学んだ `create_agent` で**書き直し**、さらに **FAQ 検索ツール (`search_faq`)** を追加した
「**ヘルプデスクエージェント v1**」を構築します。応答は後続のチケット管理システムに渡せるよう、
`SupportAnswer` (Pydantic) で**構造化**します。
ハンズオン 3-A で習得した `@tool` / `create_agent` / 軌跡読解に、**構造化出力 (`response_format`)** を加えた
本章の総合演習を、TODO コード (`# TODO`) を自分で埋めて体で覚えるのが狙いです。

## ヘルプデスク演習ストーリーにおける位置づけ (Step 2)

本コースの演習は「**社内 IT ヘルプデスクエージェント**」を第2〜8章で段階的に拡張して完成させます。
この演習はその **Step 2** にあたり、第2章の「手動の QA ループ」を `create_agent` で書き直し、
FAQ 検索ツールを足して「単体エージェント」へと進化させます。

| 章 | 追加する要素 | 演習後の姿 |
|---|---|---|
| 第2章 | Function Calling 手動ループ | 稼働状況に答える素朴な QA ループ (openai 直接) |
| **第3章 (この演習)** | **create_agent / @tool / 構造化出力** | **FAQ 検索 + 稼働状況ツールを持つ単体エージェント** |
| 第4章以降 | メモリ / MCP / HITL / 評価 / マルチエージェント | … 最終的に Web UI から操作できるヘルプデスクへ |

## 前提条件

- このファイルを **Google Colab** で開き、Colab シークレットに `OPENAI_API_KEY` を登録済みであること
- **第2章の成果物は不要です。** `get_system_status` の実装と FAQ データ (`FAQ_DATA`) はこの Notebook に
  **配布済み**なので、第2章の演習が未完了でもこの Notebook だけで完結します

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/trainocate-japan/developing-agentic-ai-with-langchain/blob/main/chap03/exercise/starter/chap03_exercise_3B_starter.ipynb)

> 上のバッジ、または GitHub 上で `.ipynb` を開いたときに先頭に表示されるバッジから、この Notebook を
> Colab で直接開けます。バッジの仕組みはハンズオン 3-A の README を参照してください。

## 埋めるべき TODO (4 か所)

| TODO | 場所 (Notebook セクション) | 内容 | ヒント |
|---|---|---|---|
| **①** | 2. search_faq | `search_faq` の **docstring** と **型ヒント** | docstring はモデルへの指示文。「何を・いつ使うか」を書く。`get_system_status` がお手本 |
| **②** | 4. create_agent | `model` / `tools` / `system_prompt` の指定 | `tools` は 2 ツール `[search_faq, get_system_status]`。system_prompt は「社内 IT ヘルプデスクの一次対応担当」 |
| **③** | 3. SupportAnswer + 4. create_agent | 各 `Field` の **description** と `response_format` への指定 | 構造化出力は `result["messages"]` ではない別のキーに入る。`response_format=SupportAnswer` |
| **④** | 5. 実行 | `result["structured_response"]` の取得 | 構造化データは `structured_response` キー。Pydantic インスタンスなので属性アクセス可 |

TODO 以外のセル (配布の `get_system_status` / `FAQ_DATA`、手順 6 の軌跡ダンプなど) は完成状態です。
上の 4 か所に集中してください。

> **TODO③ は 2 か所に分かれます**: スキーマ定義側 (セクション 3 の `Field(description=...)`) と、
> エージェント構成側 (セクション 4 の `response_format=SupportAnswer`) の両方を埋めてください。

## 完成の目安

- ✅ 「**VPN に繋がらないんだけど**」で実行すると、`result["structured_response"]` から
  `category` / `answer` / `escalation_required` が取り出せる
- ✅ 「**勤怠システムは動いていますか?**」では `get_system_status` が呼ばれる (ツールの呼び分け)
- ✅ 軌跡 `result["messages"]` を ReAct ループ (Human → AI(tool_calls) → Tool → AI) に対応付けて読める

## つまずいたときのヒント

| 症状 | 原因 | 対応する TODO |
|---|---|---|
| `search_faq` が呼ばれない / ツール選択が不安定 | docstring が曖昧で「いつ使うか」が伝わっていない | ① |
| `KeyError: 'structured_response'` | `response_format` を指定していない | ③ |
| `category` 等が空・的外れ | `Field` の description が空で、何を入れるかモデルに伝わっていない | ③ |
| `Ellipsis` (`...`) が表示される / エラー | TODO の `...` を実際の値に置き換えていない | ②④ |

## 完成成果物

FAQ 検索 (`search_faq`) + 稼働状況確認 (`get_system_status`) の **2 ツール**を持ち、
`category` / `answer` / `escalation_required` の**構造化された回答**を返す
**ヘルプデスクエージェント v1** です。第4章では、これに会話の記憶 (checkpointer) を足して v2 に拡張します。
