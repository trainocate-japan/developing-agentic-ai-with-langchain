"""run_regression.py 【正解 (solution)】 — ステップ 2〜4: 回帰評価の実行 (TODO②③ + 発展 埋め済み)

演習 7-B: ヘルプデスクの回帰評価 — ヘルプデスク Step 6
研修コース「LangChain による Agentic AI 開発実践」/ 第7章「エージェントの評価」

============================================================================
これは演習 7-B の「正解 (solution)」です。TODO②③ と発展 TODO が埋まった完成版です。
まずは starter/ で自力で挑戦し、詰まったとき・答え合わせのときに参照してください。
============================================================================

【このスクリプトがやること】
  1. helpdesk_agent.build_eval_agent() で評価対象 (Target) を構成する
     (--prompt base / --prompt v2 でシステムプロンプトを切り替え)
  2. TODO②: 最終応答の正確性を採点する LLM-as-a-judge evaluator を組み立てる
  3. TODO③: client.evaluate で Dataset 全体に対する Experiment を実行する
  4. base と v2 の 2 つの Experiment を LangSmith の比較ビューで見比べ、回帰を検出する

【実行方法】
  python run_regression.py                # ステップ 3: 修正前 (base) の Experiment
  python run_regression.py --prompt v2    # ステップ 4: 修正後 (v2) の Experiment

【TODO②③ の解答ポイント】
  - TODO②: create_llm_as_judge(prompt=CORRECTNESS_PROMPT, feedback_key="correctness",
            model=JUDGE_MODEL)。feedback_key はそのまま Experiment 画面の列名になり、
            judge の model は被評価エージェントとは別 (「書いた本人に採点させない」)。
  - TODO③: client.evaluate(target, data=..., evaluators=..., experiment_prefix=...,
            max_concurrency=...)。openevals の evaluator は key / score / comment という
            LangSmith と共通の契約で結果を返すため、変換コードなしでそのまま渡せます
            (langsmith>=0.3.11)。
"""

import argparse

from dotenv import load_dotenv
from langsmith import Client
from openevals import create_llm_as_judge
from openevals.prompts import CORRECTNESS_PROMPT

from helpdesk_agent import build_eval_agent

# .env から環境変数を読み込む (OPENAI_API_KEY / LANGSMITH_API_KEY など)。
load_dotenv()

# Dataset 名は create_dataset.py と共通。
DATASET_NAME = "helpdesk-agent-evals"

# 採点役 (judge) のモデル。被評価エージェント (helpdesk_agent.MODEL) とは別のモデルを
# 充てるのが定石です——「書いた本人に採点させない」(教科書 7-2)。
# 研修実施時に最新のモデル名を確認し、適宜差し替えてください。
JUDGE_MODEL = "openai:o3-mini"


# ======================================================================
# TODO②【解答】: 最終応答の正確性を採点する evaluator を組み立てる
# ======================================================================
# CORRECTNESS_PROMPT は「入力に対する出力が、参照出力に照らして正確か」を判定する
# プリビルトプロンプト (模範応答と比較する reference-based)。
correctness_evaluator = create_llm_as_judge(
    prompt=CORRECTNESS_PROMPT,   # プリビルトの正確性評価プロンプト
    feedback_key="correctness",  # 評価結果 (feedback) に付く名前 = Experiment 画面の列名
    model=JUDGE_MODEL,           # 採点役を務める LLM (被評価エージェントとは別)
)


# ======================================================================
# TODO (発展)【解答】: 独自基準の reference-free evaluator を追加する
# ======================================================================
# 「応答がビジネスの場にふさわしい敬語であること」という独自の品質基準を、
# 採点基準を自然言語で書いたプロンプトとして表現する。
# {inputs} と {outputs} のプレースホルダに、評価時の入力と出力が差し込まれる。
# {reference_outputs} を使っていないので、模範応答が不要な reference-free evaluator になる
# (だからこの評価軸は、模範解答のない本番トレースへのオンライン評価にも転用できる)。
POLITENESS_PROMPT = """あなたは、社内ヘルプデスクの応対品質を採点する評価者です。
以下の応答が、社内のビジネスコミュニケーションとしてふさわしい丁寧な敬語
(です・ます調) で書かれているかを判定してください。

判定基準:
- 応答全体が丁寧な敬語 (です・ます調) で書かれていれば合格です。
- 命令口調・くだけた表現 (タメ口)・利用者を突き放すような言い回しが
  含まれる場合は不合格です。
- 内容の正確さは採点対象外です (それは correctness が担当します)。
  あくまで「言葉づかい」だけを判定してください。

<input>
{inputs}
</input>

<output>
{outputs}
</output>
"""

politeness_evaluator = create_llm_as_judge(
    prompt=POLITENESS_PROMPT,    # 自作の採点基準プロンプト (reference-free)
    feedback_key="politeness",   # Experiment 画面に "politeness" 列が増える
    model=JUDGE_MODEL,
)


def main():
    parser = argparse.ArgumentParser(
        description="ヘルプデスクエージェントの回帰評価 (演習 7-B)")
    parser.add_argument(
        "--prompt",
        choices=["base", "v2"],
        default="base",
        help="評価対象のシステムプロンプト (base: 修正前 / v2: プロンプト修正パッチ適用後)",
    )
    args = parser.parse_args()

    # 評価対象 (Target) のエージェント。--prompt でプロンプトのバージョンが切り替わります。
    agent = build_eval_agent(prompt_version=args.prompt)

    # Experiment 名の接頭辞。バージョンを刻んでおくと、あとで比較ビューに並べやすい。
    # (helpdesk-agent-base-... / helpdesk-agent-v2-... という Experiment 名になります)
    experiment_prefix = f"helpdesk-agent-{args.prompt}"

    def target(inputs: dict) -> dict:
        """Dataset の inputs を受け取り、エージェントの最終応答を返す Target 関数。

        戻り値のキー "answer" は、Dataset の outputs ({"answer": 模範応答}) と
        揃えてあります (スキーマの契約)。correctness の judge は
        outputs["answer"] と reference_outputs["answer"] を突き合わせて採点します。
        """
        result = agent.invoke(
            {"messages": [{"role": "user", "content": inputs["question"]}]}
        )
        return {"answer": result["messages"][-1].content}

    # 使う evaluator の一覧。correctness (reference-based) を主軸に、
    # 発展の politeness (reference-free) を並走させる。
    evaluators = [correctness_evaluator]
    if politeness_evaluator is not None:
        evaluators.append(politeness_evaluator)

    client = Client()

    # ==================================================================
    # TODO③【解答】: client.evaluate で Experiment を実行する
    # ==================================================================
    # Dataset から Example を 1 件ずつ Target 関数に流し、出力を evaluator で採点し、
    # 全結果を 1 つの Experiment として記録する。実行すると結果閲覧用の URL が表示される。
    experiment_results = client.evaluate(
        target,                               # 評価対象 (Target 関数)
        data=DATASET_NAME,                    # 使用する Dataset 名
        evaluators=evaluators,                # TODO② (+ 発展) の evaluator をそのまま渡せる
        experiment_prefix=experiment_prefix,  # Experiment 名の接頭辞
        max_concurrency=2,                    # 並列実行数
    )

    print()
    print("=" * 70)
    print(f"Experiment を作成しました: {experiment_results.experiment_name}")
    if args.prompt == "base":
        print("これは修正前 (base) の Experiment です。次は次のコマンドで修正後の")
        print("Experiment を作成してください:")
        print("    python run_regression.py --prompt v2")
    else:
        print("これは修正後 (v2) の Experiment です。LangSmith で Dataset")
        print(f"'{DATASET_NAME}' を開き、base と v2 の 2 つの Experiment を選択して")
        print("比較ビュー (Compare) を開いてください。スコアが下がったケースは赤、")
        print("上がったケースは緑で表示されます。judge の comment から原因を読み解きましょう。")
    print("=" * 70)


if __name__ == "__main__":
    main()
