# 演習 4-B（正解 / solution）: 会話を記憶するヘルプデスク【ヘルプデスク Step 3】

演習 4-B の**正解**です。`starter/` の TODO①〜③ を自力で埋めてから、答え合わせ・詰まったときの参照に使ってください。

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/trainocate-japan/developing-agentic-ai-with-langchain/blob/main/chap04/exercise/solution/chap04_exercise_4B_solution.ipynb)

> 上のバッジ、または GitHub 上で `.ipynb` を開いたときに先頭に表示されるバッジから、この Notebook を
> Colab で直接開けます。

## 解答のポイント

- **TODO①（checkpointer）**: `from langgraph.checkpoint.memory import InMemorySaver` を import し、`create_agent(..., checkpointer=InMemorySaver())` を渡す。これで会話の state が保存され、エージェントが記憶を持つ。第3章の v1 への追加は実質この 1 要素だけ
- **TODO②（thread_id）**: `config = {"configurable": {"thread_id": EMP_SATO}}`。社員 ID を `thread_id` に対応させると「社員ごとに会話を分離して記憶する」が自然に実現する。同じ ID なら継続、別 ID なら分離
- **TODO③（tags / metadata）**: `tags` と `metadata` は `configurable` の中ではなく**同じ階層（兄弟キー）**に書く。`tags=["day1","helpdesk"]` で検索用ラベル、`metadata={"department":"人事部"}` で利用部署を記録し、運用調査に使える

## 動作確認の到達点

- 佐藤さん（`emp-sato`）の 2 ターンで、2 ターン目に「人事部」と答えられる（記憶の継続）
- 別の社員 ID（`emp-tanaka`）では所属を答えられない（記憶の分離）
- トレースに `tags` / `metadata` が付き、2 ターン目のモデル入力に 1 ターン目の会話が含まれる（checkpointer の効果）

> トレースのワークシートの数値（周回数・トークン等）は実行・モデルにより変わります。Notebook には参考値の記入例を載せていますが、実際に観察した値を読み取れることが目的です。

## 前提条件

- Google Colab
- Colab シークレットに `OPENAI_API_KEY` と `LANGSMITH_API_KEY`（後者は本章で新規。Notebook の「0-3. LangSmith のセットアップ」で発行・登録）

## 期待する成果物

社員別に会話を記憶し、`tags` / `metadata` 付きでトレースを記録するヘルプデスクエージェント v2。
