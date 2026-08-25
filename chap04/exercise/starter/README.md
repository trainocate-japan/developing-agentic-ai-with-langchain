# 演習 4-B（受講者用 / starter）: 会話を記憶するヘルプデスク【ヘルプデスク Step 3】

第4章「メモリと可観測性」の演習です。第3章で作った「ヘルプデスクエージェント v1」を、
**社員ごとに会話を記憶し、運用チームがトレースで診断できる v2** に拡張します。

## この演習で身につくこと（対応する学習目標: 章目標 2・4・5）

- `InMemorySaver`（checkpointer）と `thread_id` で、スレッド単位の会話の記憶を実装できる
- `config` の `tags` / `metadata` でトレースを整理できる
- LangSmith のトレースからエージェントの動作（周回数・ツール・トークン・記憶の効果）を読み取れる

## ヘルプデスク演習ストーリーでの位置づけ（Step 3）

| 章 | 追加する要素 | 演習後の姿 |
|---|---|---|
| 第2章 | Function Calling 手動ループ | 稼働状況に答える素朴な QA ループ |
| 第3章 | create_agent / @tool / 構造化出力 | FAQ 検索 + 稼働状況ツールを持つ単体エージェント（v1） |
| **第4章（この演習）** | **Checkpointer / LangSmith** | **社員ごとに会話を記憶し、トレースで診断できるエージェント（v2）** |

> v1 のツール・FAQ データ・`SupportAnswer` は Notebook に**同梱済み**です。第3章の演習が未完了でも、この Notebook だけで完結します。

## 取り組む TODO（3 つ）

Notebook 内の各 TODO の直前に、Markdown でヒントがあります。

- **TODO①**: `InMemorySaver` を import し、`create_agent` に `checkpointer=` を渡す
  - ヒント: `from langgraph.checkpoint.memory import InMemorySaver` / `checkpointer=InMemorySaver()`。checkpointer を渡すと会話の state が保存され、記憶できるようになります
- **TODO②**: `config` を `{"configurable": {"thread_id": <社員ID>}}` の形で構成する
  - ヒント: `thread_id` は「会話の鍵」。同じ鍵なら続き、違う鍵なら新規です
- **TODO③**: `config` に `tags` / `metadata` を追加してトレースに利用部署を記録する
  - ヒント: `tags` は `configurable` の「中」ではなく「同じ階層（兄弟キー）」に書きます

## 進め方

1. このファイルを **Google Colab** で開く（下の [Open In Colab] バッジ、または GitHub 上で `.ipynb` を開いたときに先頭に表示されるバッジから起動）

   [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/trainocate-japan/developing-agentic-ai-with-langchain/blob/main/chap04/exercise/starter/chap04_exercise_4B_starter.ipynb)

2. 「0. セットアップ」を上から実行し、`OPENAI_API_KEY` と `LANGSMITH_API_KEY` を Colab シークレットに登録する
3. TODO①〜③ を埋めてセルを実行する
4. 佐藤さんの 2 ターン会話で「人事部」と答えられること、別の社員 ID では記憶が分離されることを確認する
5. LangSmith のトレースを開き、末尾のワークシートを記入する

## 前提条件

- Google アカウント / Google Colab
- Colab シークレットに **2 つのキー**:
  - `OPENAI_API_KEY` — 第1章の演習 1-1 で登録済みのはず（未登録でも「0. セットアップ」の案内で登録できます）
  - `LANGSMITH_API_KEY` — 本章で新しく必要。Notebook の「0-3. LangSmith のセットアップ」で、無料アカウント作成 → API キー発行 → シークレット登録を行います（クレジットカード不要）

## 期待する成果物

社員別に会話を記憶し、`tags` / `metadata` 付きでトレースを記録するヘルプデスクエージェント v2 と、トレース読解の記入済みワークシート。

> 行き詰まったら、各 TODO 直前のヒントを読み返してください。答え合わせは `solution/` の Notebook で行えます。
