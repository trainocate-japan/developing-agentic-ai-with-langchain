"""test_weather_eval.py — ハンズオン 7-A オプション: pytest 統合 (配布・完成版)

ハンズオン 7-A: LangSmith のオフライン評価を一通り動かす
研修コース「Agentic AI 開発実践 - LangChain 版」/ 第7章「エージェントの評価」

============================================================================
LangSmith の pytest 統合を体験するテストファイルです。
**このファイルはオプションです。研修の時間内には実行しません**
(時間が余った場合、または各自の復習用)。

  実行方法:
    pytest test_weather_eval.py --langsmith-output

  - @pytest.mark.langsmith を付けたテストは、入出力・参照出力・評価結果が
    LangSmith に記録されます。新しいテストランナーは登場しません——
    pytest にマーカー 1 つとログ数行を足すだけです。
  - langsmith.testing の t.log_inputs / t.log_outputs / t.log_reference_outputs で
    「何を聞いたか / 何が返ったか / 何が返るべきだったか」を記録します。
  - テスト内で openevals の evaluator を呼ぶと、その結果が feedback として
    自動記録されます。
============================================================================

【client.evaluate との使い分け (教科書 7-3)】
  - CI に組み込んで毎コミット回す           → pytest 統合 (このファイル)
  - Dataset を中心に複数バージョンを比較する → client.evaluate (run_evaluation.py)

【assert について】
  「評価スコアが基準値を上回ること」を assert すると、評価をテスト (合否の関門) に
  変換できます (教科書 7-1)。ここでは score が True であることを assert しています。
  judge も LLM なので、まれに判定が揺れて失敗することがあります——それも含めて
  「評価とテストの境目」を体感してください。
"""

import pytest
from dotenv import load_dotenv
from langsmith import testing as t
from openevals import create_llm_as_judge
from openevals.prompts import CORRECTNESS_PROMPT

from weather_agent import build_weather_agent

# .env から環境変数を読み込む (OPENAI_API_KEY / LANGSMITH_API_KEY など)。
load_dotenv()

# 採点役 (judge) のモデル。被評価エージェントとは別のモデルを充てます
# (「書いた本人に採点させない」)。研修実施時に最新のモデル名を確認してください。
JUDGE_MODEL = "openai:o3-mini"

# 評価対象のエージェント (通常版プロンプト) と evaluator は、
# テスト間で使い回すためモジュールレベルで 1 回だけ構成します。
agent = build_weather_agent()

correctness_evaluator = create_llm_as_judge(
    prompt=CORRECTNESS_PROMPT,
    feedback_key="correctness",
    model=JUDGE_MODEL,
)

# テストケース (質問, 模範応答)。@pytest.mark.parametrize でケースを量産できるのが
# pytest 統合の利点です (Dataset は使わず、ケースをコードで持ちます)。
CASES = [
    ("東京の天気を教えて", "東京は晴れで、気温は 22 度です。"),
    ("大阪では今日、傘が必要ですか?", "大阪は晴れなので、傘は不要です。"),
]


@pytest.mark.langsmith  # このテストの入出力と評価結果を LangSmith に記録する
@pytest.mark.parametrize("question, reference_answer", CASES)
def test_weather_agent_correctness(question, reference_answer):
    # 1) 入力を記録する
    t.log_inputs({"question": question})

    # 2) エージェントを実行し、最終応答を取り出して記録する
    result = agent.invoke({"messages": [{"role": "user", "content": question}]})
    answer = result["messages"][-1].content
    t.log_outputs({"answer": answer})
    t.log_reference_outputs({"answer": reference_answer})

    # 3) evaluator を呼ぶと、結果が feedback として自動記録される
    eval_result = correctness_evaluator(
        inputs={"question": question},
        outputs={"answer": answer},
        reference_outputs={"answer": reference_answer},
    )

    # 4) スコアを assert して「評価をテストに変換」する (教科書 7-1)
    assert eval_result["score"] is True, (
        f"correctness 不合格: {eval_result['comment']}"
    )
