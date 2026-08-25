"""create_dataset.py 【正解 (solution)】 — ステップ 1: Dataset 作成 (TODO① 埋め済み)

演習 7-B: ヘルプデスクの回帰評価 — ヘルプデスク Step 6
研修コース「LangChain による Agentic AI 開発実践」/ 第7章「エージェントの評価」

============================================================================
これは演習 7-B の「正解 (solution)」です。TODO① が埋まった完成版です。
まずは starter/ で自力で挑戦し、詰まったとき・答え合わせのときに参照してください。
============================================================================

【このスクリプトがやること】
  代表的な問い合わせ 3 ケースを Example として登録した Dataset
  「helpdesk-agent-evals」を LangSmith 上に作成します。
  「プロンプトを直すたびに UI から全ケースを手動確認する」代わりに、
  この Dataset に対して Experiment を繰り返し実行できるようにする——
  回帰評価の土台づくりです。

【TODO① の解答ポイント】
  Example は 1 件ごとに {"inputs": {...}, "outputs": {...}} の辞書。
    - inputs  = {"question": <問い合わせ文>}  … Target 関数に渡る入力
    - outputs = {"answer": <模範応答>}        … evaluator だけが参照する期待出力
  キー名 ("question" / "answer") は run_regression.py の Target 関数・evaluator と
  揃えた「スキーマの契約」です。ここがずれると、Target が KeyError になるか、
  judge が参照すべき模範応答を見つけられなくなります。

【模範応答はどう決めたか】
  helpdesk_tools.py の配布データ (FAQ_DATA / SYSTEM_STATUS) を根拠に、
  「一次対応として満点」の応答を人手で書いたものです。教科書 7-2 の
  「良い例を 5〜10 個手作りして基準 (ground truth) を定める」の実践にあたります
  (演習では時間の都合で 3 件に絞っています)。
"""

from dotenv import load_dotenv
from langsmith import Client

# .env から環境変数を読み込む (LANGSMITH_API_KEY など。第4章で設定済み)。
load_dotenv()

# Dataset 名は run_regression.py と共通。
DATASET_NAME = "helpdesk-agent-evals"

# ----------------------------------------------------------------------
# 配布素材: 代表 3 ケースの「問い合わせ文」と「模範応答」
# ----------------------------------------------------------------------
# ケース 1: VPN トラブル (やり方の質問 + 実は VPN はメンテナンス中)
CASE1_QUESTION = "VPN に繋がらないのですが、どうすればいいですか?"
CASE1_ANSWER = (
    "まず社内ポータルから最新の VPN クライアントを再インストールし、"
    "二要素認証アプリの時刻同期を確認してください。"
    "なお、VPN は現在メンテナンス中 (本日 22:00 まで) のため、"
    "終了後にあらためてお試しください。解決しない場合は情報システム部にご相談ください。"
)

# ケース 2: パスワードを忘れた (やり方の質問。ロック時の補足まで含めて満点)
CASE2_QUESTION = "パスワードを忘れてしまいました。どうすればリセットできますか?"
CASE2_ANSWER = (
    "社内ポータルの『パスワード再設定』から手続きできます。"
    "アカウントがロックされている場合は、本人確認のうえ情報システム部での対応が必要です。"
)

# ケース 3: 経費精算システムの稼働確認 (稼働状況の質問)
CASE3_QUESTION = "経費精算システムは今、正常に使えますか?"
CASE3_ANSWER = "経費精算システムは現在、正常稼働中です。問題なくご利用いただけます。"


# ======================================================================
# TODO①【解答】: Example のスキーマを組み立てる
# ======================================================================
# inputs (問い合わせ文) と outputs (模範応答) のペアを、3 ケース分並べる。
EXAMPLES = [
    {
        "inputs": {"question": CASE1_QUESTION},
        "outputs": {"answer": CASE1_ANSWER},
    },
    {
        "inputs": {"question": CASE2_QUESTION},
        "outputs": {"answer": CASE2_ANSWER},
    },
    {
        "inputs": {"question": CASE3_QUESTION},
        "outputs": {"answer": CASE3_ANSWER},
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

    # Dataset を作成し、Example を登録する
    dataset = client.create_dataset(
        dataset_name=DATASET_NAME,
        description="ヘルプデスクエージェント v4 の回帰評価用データセット",
    )
    client.create_examples(dataset_id=dataset.id, examples=EXAMPLES)

    print("=" * 70)
    print(f"Dataset '{DATASET_NAME}' を作成し、Example を {len(EXAMPLES)} 件登録しました。")
    print("ブラウザで https://smith.langchain.com を開き、[Datasets & Experiments] から")
    print("Example の inputs / outputs を確認してください。")
    print("=" * 70)


if __name__ == "__main__":
    main()
