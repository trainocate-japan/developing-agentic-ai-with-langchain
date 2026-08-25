# 演習 3-B【solution / 正解】: ヘルプデスクエージェント v1 — ヘルプデスク Step 2

研修コース「LangChain による Agentic AI 開発実践」 / **第3章「エージェント開発の基本」** の演習の**正解コード**です。

- **ファイル**: [`chap03_exercise_3B_solution.ipynb`](./chap03_exercise_3B_solution.ipynb)
- **問題 (starter)**: [`../starter/chap03_exercise_3B_starter.ipynb`](../starter/chap03_exercise_3B_starter.ipynb)
- **形式**: Google Colab Notebook (Jupyter nbformat 4)
- **対応する学習トピック**: @tool / create_agent / 構造化出力 (response_format) / 軌跡の読解

> **注意**: これは正解です。TODO (`# TODO`) を埋める前に答えを見てしまわないよう、
> **まずは starter で自力で挑戦**してください。答え合わせや、詰まったときの参照に使います。

## 演習の狙い

第2章で手動実装したヘルプデスク QA ループを `create_agent` で書き直し、FAQ 検索ツールを追加し、
応答を Pydantic で構造化した「**ヘルプデスクエージェント v1**」の**完全動作版**です。
`@tool` (docstring + 型ヒント)、`create_agent` の構成、`SupportAnswer` (Pydantic) による構造化出力、
`structured_response` の取得、軌跡の読解——本章の学習目標 3〜5 を総動員します。

## ヘルプデスク演習ストーリーにおける位置づけ (Step 2)

本コースの演習ストーリー「**社内 IT ヘルプデスクエージェント**」の **Step 2** です。
第2章の「稼働状況に答える素朴な QA ループ」を土台に、`create_agent` で書き直して FAQ 検索を足し、
第4章以降で会話記憶・MCP・承認フロー・マルチエージェントへと段階的に拡張していきます。

## この Notebook の構成

| セクション | 内容 |
|---|---|
| 0. セットアップ | `langchain` / `langchain-openai` インストール、API キー、`MODEL` |
| 1. 配布コード | `get_system_status` (`@tool` 済みダミー) と `FAQ_DATA` (FAQ 検索用の小さな dict) |
| 2. search_faq【TODO①】 | `@tool` で FAQ 検索ツールを定義 (docstring + 型ヒント) |
| 3. SupportAnswer【TODO③前半】 | Pydantic スキーマ (`category` / `answer` / `escalation_required` + Field description) |
| 4. create_agent【TODO②・③後半】 | 2 ツール + system_prompt + `response_format=SupportAnswer` |
| 5. 実行【TODO④】 | 「VPN に繋がらないんだけど」で実行し `result["structured_response"]` を取得 |
| 6. 軌跡の読解 (完成済み) | `result["messages"]` をダンプ。稼働状況の質問でツールの呼び分けも確認 |

各ステップに「何を・なぜ」やっているかの Markdown 解説とコードコメントを付けています。
**構造化出力が `result["messages"]` ではなく `result["structured_response"]` に入る**点を繰り返し強調しています。

## 前提条件

- このファイルを **Google Colab** で開き、Colab シークレットに `OPENAI_API_KEY` を登録済みであること
- **第2章の成果物は不要** (`get_system_status` 実装と FAQ データは配布済みでこの Notebook 単体で完結)

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/trainocate-japan/developing-agentic-ai-with-langchain/blob/main/chap03/exercise/solution/chap03_exercise_3B_solution.ipynb)

> 上のバッジ、または GitHub 上で `.ipynb` を開いたときに先頭に表示されるバッジから、この Notebook を
> Colab で直接開けます。バッジの仕組みはハンズオン 3-A の README を参照してください。

## starter の TODO との対応

starter で `# TODO` になっている 4 か所が、この solution では次のように埋まっています。

- **TODO①** → セクション 2 の `search_faq` の docstring (「何を・いつ使うか」) と型ヒント (`keyword: str` / `-> str`)
- **TODO②** → セクション 4 の `model=MODEL` / `tools=[search_faq, get_system_status]` / `system_prompt="あなたは社内 IT ヘルプデスクの一次対応担当です。…"`
- **TODO③** → セクション 3 の各 `Field(description=...)` と、セクション 4 の `response_format=SupportAnswer`
- **TODO④** → セクション 5 の `answer = result["structured_response"]`

## 完成の目安

- ✅ 「VPN に繋がらないんだけど」で `result["structured_response"]` から構造化回答が取り出せる
- ✅ 「勤怠システムは動いていますか?」では `get_system_status` が呼ばれる (ツールの呼び分け)
- ✅ 軌跡 `result["messages"]` を ReAct ループに対応付けて読める

## 完成成果物

FAQ 検索 + 稼働状況確認の **2 ツール**を持ち、構造化された回答 (`SupportAnswer`) を返す
**ヘルプデスクエージェント v1**。第4章で `checkpointer` を加えて、会話を記憶する v2 へ拡張します。
