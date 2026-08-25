"""create_dataset.py 【演習 (starter)】 — ステップ 1: Dataset 作成 (歯抜け①)

演習 7-B: ヘルプデスクの回帰評価 — ヘルプデスク Step 6
研修コース「LangChain による Agentic AI 開発実践」/ 第7章「エージェントの評価」

============================================================================
これは演習 7-B の「演習用 (starter)」です。
ファイル内の「TODO①」を、あなた自身で埋めて完成させてください。
完成版が見たくなったら solution/ を参照できますが、まずは自力で挑戦しましょう。

※ このファイルは TODO① を埋めるまで動きません (NotImplementedError になります)。
============================================================================

【このスクリプトがやること】
  代表的な問い合わせ 3 ケースを Example として登録した Dataset
  「helpdesk-agent-evals」を LangSmith 上に作成します。
  「プロンプトを直すたびに UI から全ケースを手動確認する」代わりに、
  この Dataset に対して Experiment を繰り返し実行できるようにする——
  回帰評価の土台づくりです。

【あなたが埋めるのは 1 か所 (TODO①)】
  - TODO①: client.create_examples に渡す Example のスキーマ組み立て
            (inputs = 問い合わせ文 / outputs = 模範応答)

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
# TODO①: Example のスキーマを組み立てる
# ======================================================================
# client.create_examples に渡す examples は、1 件ごとに次の形の辞書です。
#
#     {"inputs": {...}, "outputs": {...}}
#
#   - inputs  : Target 関数に渡る入力。ここでは {"question": <問い合わせ文>}
#   - outputs : evaluator だけが参照する期待出力。ここでは {"answer": <模範応答>}
#
# キー名 ("question" / "answer") は run_regression.py の Target 関数
# (inputs["question"] を読む) と correctness evaluator (outputs["answer"] と
# reference_outputs["answer"] を突き合わせる) がそのまま前提にする「契約」です。
#
# 上の配布素材 (CASE1〜CASE3) を使って、3 件分のリストを組み立ててください。
EXAMPLES = None  # TODO①: [{"inputs": {...}, "outputs": {...}}, ...] のリストに置き換える


def main():
    if EXAMPLES is None:
        raise NotImplementedError(
            "TODO①: EXAMPLES を組み立ててください (このファイルのコメントと README のヒント参照)"
        )

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
