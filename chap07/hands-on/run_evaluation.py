"""run_evaluation.py — ハンズオン 7-A ステップ②③: evaluator 定義 + Experiment 実行 (配布・完成版)

ハンズオン 7-A: LangSmith のオフライン評価を一通り動かす
研修コース「Agentic AI 開発実践 - LangChain 版」/ 第7章「エージェントの評価」

============================================================================
オフライン評価 4 ステップの「② evaluator 定義」と「③ Experiment 実行」を行う
スクリプトです。3 本の evaluator で天気エージェントを採点します。

  - correctness       : 最終応答の正確性。openevals の CORRECTNESS_PROMPT による
                        LLM-as-a-judge (模範応答と比較する reference-based)
  - conciseness       : 最終応答の簡潔性。openevals の CONCISENESS_PROMPT による
                        LLM-as-a-judge (模範応答が不要な reference-free)
  - trajectory_strict : 実行経路の検証 (補助)。openevals のトラジェクトリマッチ
                        (strict モード: 同じツール呼び出しを同じ順序で行ったか)

実行方法:
  python run_evaluation.py              # 通常版プロンプトで Experiment を作成
  python run_evaluation.py --degraded   # 劣化版プロンプトで Experiment を作成 (ステップ④)
============================================================================

【評価の構成: 最終応答が主軸、トラジェクトリは補助線 (教科書 7-2)】
  ユーザーが受け取るのは最終応答なので、Dataset の outputs は {"answer": 模範応答}
  という「最終応答スキーマ」にしてあります (create_dataset.py 参照)。
  一方、トラジェクトリマッチ評価には「参照トラジェクトリ (あるべき実行系列)」が
  必要です。これは Dataset ではなく、このファイル内の辞書 REFERENCE_TRAJECTORIES
  として持ち、質問文をキーに引きます。
  (トラジェクトリ評価を主軸にする場合は、inputs / outputs とも {"messages": [...]}
   スキーマの専用 Dataset を作るのが教科書 7-3 の作法ですが、ここでは
   「最終応答の評価が中心、トラジェクトリは裏付け」という実務の定石に合わせ、
   1 つの Dataset に両方を併走させる構成にしています)

【なぜ evaluator に「薄いラッパー」を挟むのか】
  LangSmith は evaluator に inputs / outputs / reference_outputs の 3 つを渡します。
  openevals の evaluator は LangSmith と同じ契約 (key / score / comment) で結果を
  返すため、Target が {"answer": ...} だけを返す構成なら client.evaluate に
  **そのまま** 渡せます (教科書 7-3 の構成そのもの。langsmith>=0.3.11)。
  ただし今回の Target は、トラジェクトリ評価のために "messages" (実行系列) も
  返します。そのままだと judge のプロンプトに長大なメッセージ列まで貼り付いて
  採点がぶれるため、「judge には answer だけを見せる」「マッチ評価には messages
  だけを渡す」という交通整理を行う薄いラッパー関数を挟んでいます。
"""

import argparse

from dotenv import load_dotenv
from langsmith import Client
from openevals import create_llm_as_judge, create_trajectory_match_evaluator
from openevals.prompts import CORRECTNESS_PROMPT, CONCISENESS_PROMPT
from langchain.messages import AIMessage, HumanMessage, ToolMessage

from weather_agent import build_weather_agent

# .env から環境変数を読み込む (OPENAI_API_KEY / LANGSMITH_API_KEY など)。
load_dotenv()

# Dataset 名は create_dataset.py と共通。
DATASET_NAME = "weather-agent-evals"

# 採点役 (judge) のモデル。被評価エージェント (weather_agent.MODEL) とは別のモデルを
# 充てるのが定石です——「書いた本人に採点させない」(教科書 7-2)。
# 研修実施時に最新のモデル名を確認し、適宜差し替えてください。
JUDGE_MODEL = "openai:o3-mini"


# ======================================================================
# ステップ②-1: 最終応答の evaluator (openevals の LLM-as-a-judge)
# ======================================================================

# 正確性: 「入力に対する出力が、参照出力に照らして正確か」を判定する reference-based。
# feedback_key は評価結果に付く名前で、そのまま Experiment 画面の列名になります。
correctness_judge = create_llm_as_judge(
    prompt=CORRECTNESS_PROMPT,   # プリビルトの正確性評価プロンプト
    feedback_key="correctness",  # 評価結果 (feedback) に付く名前
    model=JUDGE_MODEL,           # 採点役を務める LLM
)

# 簡潔性: 出力単体を検査する reference-free (reference_outputs は使わない)。
# プロンプトと feedback_key を差し替えるだけで評価軸を増やせるのがポイントです。
conciseness_judge = create_llm_as_judge(
    prompt=CONCISENESS_PROMPT,   # 応答が簡潔かを判定するプリビルトプロンプト
    feedback_key="conciseness",
    model=JUDGE_MODEL,
)


# ======================================================================
# ステップ②-2: トラジェクトリの evaluator (openevals のマッチ評価・補助)
# ======================================================================

# strict モード: 参照と同じツール呼び出しを同じ順序で行ったかを判定する。
# メッセージ本文の文言の違いは許容され、比較されるのはツール呼び出しの構造だけです。
trajectory_match = create_trajectory_match_evaluator(
    trajectory_match_mode="strict",
)


def _reference_trajectory(question: str, city: str, answer: str) -> list:
    """参照トラジェクトリ (あるべき実行系列) を組み立てる。

    HumanMessage → ツール呼び出しを含む AIMessage → ToolMessage → 最終応答、という
    並びは、第2章で Function Calling を学んだときのメッセージフローそのものです。
    """
    return [
        HumanMessage(content=question),
        AIMessage(content="", tool_calls=[
            {"id": "call_1", "name": "get_weather", "args": {"city": city}},
        ]),
        ToolMessage(content=f"{city} は晴れ、気温は 22 度です。", tool_call_id="call_1"),
        AIMessage(content=answer),
    ]


# 質問文 → 参照トラジェクトリの対応表。
# キーの質問文は create_dataset.py の EXAMPLES と一致させてあります
# (Dataset 側の outputs は「最終応答スキーマ」なので、トラジェクトリの参照は
#  コード側で持つ——冒頭の docstring で説明した構成です)。
REFERENCE_TRAJECTORIES = {
    "東京の天気を教えて": _reference_trajectory(
        "東京の天気を教えて", "東京", "東京は晴れで、気温は 22 度です。"),
    "大阪では今日、傘が必要ですか?": _reference_trajectory(
        "大阪では今日、傘が必要ですか?", "大阪", "大阪は晴れなので、傘は不要です。"),
    "札幌の天気は?": _reference_trajectory(
        "札幌の天気は?", "札幌", "札幌は晴れで、気温は 22 度です。"),
    "福岡は今、何度ですか?": _reference_trajectory(
        "福岡は今、何度ですか?", "福岡", "福岡の気温は 22 度です。"),
}


# ======================================================================
# ステップ②-3: client.evaluate に渡す evaluator (薄いラッパー)
# ======================================================================
# LangSmith は各 evaluator を evaluator(inputs=..., outputs=..., reference_outputs=...)
# の形で呼び出します。戻り値は {key, score, comment} の契約に従った dict です。

def correctness(inputs: dict, outputs: dict, reference_outputs: dict):
    """最終応答の正確性 (reference-based)。judge には answer だけを見せる。"""
    return correctness_judge(
        inputs=inputs,                            # 何を聞いたか
        outputs={"answer": outputs["answer"]},    # 何が返ってきたか (最終応答のみ)
        reference_outputs=reference_outputs,      # 何が返ってくるべきだったか (模範応答)
    )


def conciseness(inputs: dict, outputs: dict):
    """最終応答の簡潔性 (reference-free)。reference_outputs は受け取らない。"""
    return conciseness_judge(
        inputs=inputs,
        outputs={"answer": outputs["answer"]},    # reference_outputs は渡さない
    )


def trajectory_strict(inputs: dict, outputs: dict):
    """実行経路の strict マッチ (補助)。参照トラジェクトリはコード側の辞書から引く。"""
    reference = REFERENCE_TRAJECTORIES.get(inputs["question"])
    if reference is None:
        # Dataset に質問を追加したのに参照トラジェクトリを足し忘れたケースへの備え。
        return {
            "key": "trajectory_strict_match",
            "score": None,
            "comment": "この質問の参照トラジェクトリが REFERENCE_TRAJECTORIES に未定義です。",
        }
    return trajectory_match(
        outputs=outputs["messages"],     # エージェントの実際のトラジェクトリ
        reference_outputs=reference,     # あるべき実行系列
    )


# ======================================================================
# ステップ③: Experiment の実行
# ======================================================================

def main():
    parser = argparse.ArgumentParser(
        description="天気エージェントのオフライン評価 (ハンズオン 7-A)")
    parser.add_argument(
        "--degraded",
        action="store_true",
        help="劣化版プロンプトで実行する (ステップ④: 回帰を比較ビューで観察する用)",
    )
    args = parser.parse_args()

    # 評価対象 (Target) のエージェント。--degraded でプロンプトが切り替わります。
    agent = build_weather_agent(degraded=args.degraded)

    # Experiment 名の接頭辞。バージョンを刻んでおくと、あとで比較ビューに並べやすい。
    # ここでは劣化版を「v2 (改修に失敗したバージョン)」という体で記録します。
    experiment_prefix = "weather-agent-v2" if args.degraded else "weather-agent-v1"

    def target(inputs: dict) -> dict:
        """Dataset の inputs を受け取り、エージェントを実行する Target 関数。

        戻り値のスキーマ:
          - "answer"   : 最終応答。Dataset の outputs ({"answer": 模範応答}) と対になり、
                         correctness / conciseness の judge が採点する
          - "messages" : 実行系列 (トラジェクトリ)。trajectory_strict だけが参照する
        """
        result = agent.invoke(
            {"messages": [{"role": "user", "content": inputs["question"]}]}
        )
        return {
            "answer": result["messages"][-1].content,
            "messages": result["messages"],
        }

    client = Client()

    # client.evaluate は、Dataset から Example を 1 件ずつ Target に流し、
    # 出力を evaluators で採点し、全結果を 1 つの Experiment として記録します。
    # 実行するとターミナルに結果閲覧用の URL が表示されます。
    experiment_results = client.evaluate(
        target,                          # 評価対象 (Target 関数)
        data=DATASET_NAME,               # 使用する Dataset 名
        evaluators=[                     # ② で定義した 3 本の evaluator
            correctness,
            conciseness,
            trajectory_strict,
        ],
        experiment_prefix=experiment_prefix,  # Experiment 名の接頭辞
        max_concurrency=2,               # 並列実行数
    )

    print()
    print("=" * 70)
    print(f"Experiment を作成しました: {experiment_results.experiment_name}")
    if args.degraded:
        print("これは劣化版プロンプト (v2) の Experiment です。")
        print("Dataset 'weather-agent-evals' の画面で v1 と v2 の 2 つの Experiment を")
        print("選択して比較ビューを開き、スコアが下がったケースが赤く表示されることを")
        print("確認してください (上がったケースは緑になります)。")
    else:
        print("上に表示された URL から Experiment 画面を開き、Example ごとの")
        print("Inputs / Reference Output / Outputs と 3 つのスコア列を確認してください。")
        print("スコアをクリックすると judge の comment (判定理由) が読めます。")
    print("=" * 70)


if __name__ == "__main__":
    main()
