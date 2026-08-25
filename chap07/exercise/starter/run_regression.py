"""run_regression.py 【演習 (starter)】 — ステップ 2〜4: 回帰評価の実行 (歯抜け②③ + 発展)

演習 7-B: ヘルプデスクの回帰評価 — ヘルプデスク Step 6
研修コース「LangChain による Agentic AI 開発実践」/ 第7章「エージェントの評価」

============================================================================
これは演習 7-B の「演習用 (starter)」です。
ファイル内の「TODO②」「TODO③」(と、余力があれば「TODO 発展」) を埋めて完成させてください。
完成版が見たくなったら solution/ を参照できますが、まずは自力で挑戦しましょう。

※ このファイルは TODO②③ を埋めるまで動きません (NotImplementedError になります)。
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
# TODO②: 最終応答の正確性を採点する evaluator を組み立てる
# ======================================================================
# create_llm_as_judge に、次の 3 つの引数を渡します。
#
#   - prompt       : 採点基準のプロンプト。「入力に対する出力が、参照出力に照らして
#                    正確か」を判定するプリビルトの CORRECTNESS_PROMPT を使います
#                    (模範応答と比較する reference-based)
#   - feedback_key : 評価結果 (feedback) に付く名前。そのまま LangSmith の
#                    Experiment 画面の列名になります (例: "correctness")
#   - model        : 採点役 (judge) を務める LLM。上で定義した JUDGE_MODEL を
#                    指定します (被評価エージェントのモデルとは別)
correctness_evaluator = None  # TODO②: create_llm_as_judge(...) に置き換える


# ======================================================================
# TODO (発展): 独自基準の reference-free evaluator を追加する
# ======================================================================
# 「応答がビジネスの場にふさわしい敬語であること」のような独自の品質基準も、
# 採点基準を自然言語で書いたプロンプトを create_llm_as_judge に渡すだけで
# evaluator にできます。模範応答と比較しないので reference-free です。
#
# 書き方のヒント:
#   1) 採点基準を書いたプロンプト文字列を作る。文中に {inputs} と {outputs} という
#      プレースホルダを書くと、評価時に入力と出力が差し込まれる
#      ({reference_outputs} を使わなければ reference-free になる)。
#      例 (骨格):
#        POLITENESS_PROMPT = """あなたは、社内ヘルプデスクの応対品質を採点する評価者です。
#        以下の応答が <あなたの基準> を満たすかを判定してください。
#
#        <input>
#        {inputs}
#        </input>
#
#        <output>
#        {outputs}
#        </output>
#        """
#   2) create_llm_as_judge(prompt=POLITENESS_PROMPT, feedback_key="politeness",
#      model=JUDGE_MODEL) で evaluator にする。
#   3) 下の politeness_evaluator に代入すると、main() が自動で evaluators に加えます
#      (feedback_key "politeness" の列が Experiment 画面に増えます)。
politeness_evaluator = None  # TODO (発展・任意): 独自プロンプトの evaluator に置き換える


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

    if correctness_evaluator is None:
        raise NotImplementedError(
            "TODO②: create_llm_as_judge で correctness_evaluator を組み立ててください"
        )

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

    # 使う evaluator の一覧。(発展) politeness_evaluator を作った場合は自動で加わります。
    evaluators = [correctness_evaluator]
    if politeness_evaluator is not None:
        evaluators.append(politeness_evaluator)

    client = Client()

    # ==================================================================
    # TODO③: client.evaluate で Experiment を実行する
    # ==================================================================
    # client.evaluate は、Dataset から Example を 1 件ずつ Target 関数に流し、
    # 出力を evaluator で採点し、全結果を 1 つの Experiment として記録します。
    # 次の引数を渡してください。
    #
    #   - 第 1 引数         : Target 関数 (上で定義した target)
    #   - data              : 使用する Dataset 名 (DATASET_NAME)
    #   - evaluators        : evaluator のリスト (上で用意した evaluators)
    #   - experiment_prefix : Experiment 名の接頭辞 (上で用意した experiment_prefix)
    #   - max_concurrency   : 並列実行数 (2 程度)
    experiment_results = None  # TODO③: client.evaluate(...) に置き換える

    if experiment_results is None:
        raise NotImplementedError(
            "TODO③: client.evaluate で Experiment を実行してください"
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
