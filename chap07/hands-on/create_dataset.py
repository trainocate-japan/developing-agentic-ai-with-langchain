"""create_dataset.py — ハンズオン 7-A ステップ①: Dataset を作成する (配布・完成版)

ハンズオン 7-A: LangSmith のオフライン評価を一通り動かす
研修コース「Agentic AI 開発実践 - LangChain 版」/ 第7章「エージェントの評価」

============================================================================
オフライン評価 4 ステップの「① Dataset 作成」を行うスクリプトです。
LangSmith SDK の Client で Dataset (Example の集まり) を作成します。

  - Dataset : 評価に使う Example の集まり
  - Example : 1 件のテストケース。inputs (アプリケーションに渡す入力) と、
              任意の reference outputs (evaluator だけが参照する期待出力) から成る

実行すると LangSmith 上に Dataset「weather-agent-evals」ができるので、
ブラウザで開いて Example の中身 (質問と模範応答のペア) を確認してください。
============================================================================

【inputs / outputs のキー名は「契約」】
  ここで決めたキー名 ("question" / "answer") は、run_evaluation.py の
  Target 関数 (inputs["question"] を読む) と evaluator (outputs["answer"] と
  reference_outputs["answer"] を突き合わせる) がそのまま前提にします。
  Dataset のスキーマと Target・evaluator のスキーマを揃えること——これが
  オフライン評価を組み立てるときの最初の約束事です。
"""

from dotenv import load_dotenv
from langsmith import Client

# .env から環境変数を読み込む (LANGSMITH_API_KEY など。第4章で設定済み)。
load_dotenv()

# Dataset 名は run_evaluation.py と共通。
DATASET_NAME = "weather-agent-evals"

# Example (テスト入力と期待出力のペア)。
#   - inputs  : エージェントに渡す入力 (質問)
#   - outputs : evaluator だけが参照する模範応答 (reference outputs)
# まずは「よくある質問」を人手で厳選した数件から始めるのが定石です (教科書 7-3)。
# 模範応答は get_weather (ダミー実装) が返す「晴れ・22 度」と整合させてあります。
EXAMPLES = [
    {
        "inputs": {"question": "東京の天気を教えて"},
        "outputs": {"answer": "東京は晴れで、気温は 22 度です。"},
    },
    {
        "inputs": {"question": "大阪では今日、傘が必要ですか?"},
        "outputs": {"answer": "大阪は晴れなので、傘は不要です。"},
    },
    {
        "inputs": {"question": "札幌の天気は?"},
        "outputs": {"answer": "札幌は晴れで、気温は 22 度です。"},
    },
    {
        "inputs": {"question": "福岡は今、何度ですか?"},
        "outputs": {"answer": "福岡の気温は 22 度です。"},
    },
]


def main():
    client = Client()

    # 同名の Dataset が既にある場合は作り直さない (再実行しても安全にするため)。
    # 作り直したい場合は、LangSmith の UI で Dataset を削除してから再実行します。
    if client.has_dataset(dataset_name=DATASET_NAME):
        print(f"Dataset '{DATASET_NAME}' は既に存在するため、作成をスキップしました。")
        print("(作り直す場合は LangSmith の UI で Dataset を削除してから再実行してください)")
        return

    # ① Dataset を作成する
    dataset = client.create_dataset(
        dataset_name=DATASET_NAME,
        description="天気エージェントの回帰評価用データセット",
    )

    # ② Example (テスト入力と期待出力のペア) を登録する
    client.create_examples(dataset_id=dataset.id, examples=EXAMPLES)

    print("=" * 70)
    print(f"Dataset '{DATASET_NAME}' を作成し、Example を {len(EXAMPLES)} 件登録しました。")
    print("ブラウザで https://smith.langchain.com を開き、[Datasets & Experiments] から")
    print(f"'{DATASET_NAME}' を選んで、Example の inputs / outputs を確認してください。")
    print("=" * 70)


if __name__ == "__main__":
    main()
