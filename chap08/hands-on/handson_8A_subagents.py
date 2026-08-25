"""handson_8A_subagents.py — 最小 Subagents サンプル (エージェントのツール化)

ハンズオン 8-A: エージェントのツール化を動かす
研修コース「LangChain による Agentic AI 開発実践」/ 第8章「マルチエージェント開発」

============================================================================
このスクリプトは「作成済みのコードを講師と一緒に実行する」ハンズオン教材です。
受講者がコードを書く必要はありません (書く側は総合演習)。

Subagents 型マルチエージェントのコアメカニズム——「エージェントをツールとして
ラップする」——を、最小構成 (research サブエージェント 1 体) で体験します。
中身は第3章で学んだ create_agent / @tool / invoke の組み合わせだけで、
新しい API は 1 つも登場しません。
============================================================================

【このサンプルの構成 (PM と専門チームのアナロジー)】

    ユーザー
       │
       ▼
  supervisor (メインエージェント)        ← 窓口に立つプロジェクトマネージャ
       │  research ツールを呼ぶ
       ▼
  research_agent (サブエージェント)       ← 調査だけを担当する専門チーム
       │  search_docs ツールを呼ぶ
       ▼
  最終メッセージ (調査結果) を supervisor に返す

  supervisor から見れば research は「ただのツール」です。
  「このタスクは research の説明に合う」と判断したら呼び出し、戻り値を
  受け取って続きを考える——第3章のエージェントループがそのまま動きます。

【同期 (sync) で実装している理由】
  ここでは supervisor がサブの結果を待ってから応答を組み立てる必要があるため、
  既定の同期呼び出し (invoke) を使います。async は使いません
  (公式の「sync vs async」は、長時間タスクをバックグラウンド化する発展形の話で、
   Python の async/await とは別概念です)。
"""

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.tools import tool

# .env から環境変数を読み込む (OPENAI_API_KEY / LANGSMITH_* など)。
# load_dotenv() は実行位置から上位ディレクトリを遡るため、リポジトリのルートに
# 置いた共通 .env を読み込む (5-A で設定済み)。
load_dotenv()

# モデル名は変数に集約 ("provider:model" 形式)。研修実施時に最新へ差し替える。
MODEL = "openai:gpt-5.4"


# ----------------------------------------------------------------------
# サブエージェントが使う「素のツール」(第3章で学んだ @tool)
# ----------------------------------------------------------------------
# 調査の題材となるダミーのナレッジ。実務では Web 検索や社内 DB 検索に相当する。
DOCS = {
    "langchain": "LangChain は LLM アプリ開発のフレームワーク。v1 で create_agent に一本化された。",
    "langgraph": "LangGraph はエージェントのランタイム。State / Node / Edge でフローを記述する。",
    "subagents": "Subagents はサブエージェントをツールとして呼ぶマルチエージェントの方式。"
                 "ルーティングはすべてメインエージェント (supervisor) を経由する。",
}


@tool
def search_docs(keyword: str) -> str:
    """技術トピックのドキュメントをキーワード検索し、要点を返す。

    Args:
        keyword: 調べたいトピック (例: langchain, langgraph, subagents)
    """
    hits = [text for key, text in DOCS.items() if keyword.lower() in key or key in keyword.lower()]
    if hits:
        return "\n".join(hits)
    return "該当するドキュメントが見つかりませんでした。"


# ----------------------------------------------------------------------
# (1) サブエージェントを作る — name 引数で命名するのが重要
# ----------------------------------------------------------------------
# create_agent はこれまでと全く同じ。ポイントは 2 つ:
#   - name="research_agent" … LangSmith トレース上の表示名になる。
#       複数エージェントが入れ子になるトレースで「どれがどのエージェントか」を
#       識別する生命線。
#   - system_prompt の「調査結果は必ず最終メッセージに含める」… supervisor に
#       返るのは「最終メッセージの content だけ」。途中のツール結果や推論過程は
#       一切伝わらない。だからサブに「結果を最終メッセージに書け」と明示しないと、
#       「調査しました」とだけ言って肝心の中身が消える典型的な失敗が起きる。
research_agent = create_agent(
    model=MODEL,
    tools=[search_docs],
    system_prompt=(
        "あなたは技術調査の専門家です。search_docs ツールでトピックを調べ、"
        "分かったことを要約してください。"
        "調査結果は必ずあなたの最終メッセージに含めてください "
        "(あなたを呼び出した側は、あなたの最終メッセージしか見ません)。"
    ),
    name="research_agent",  # ← トレースでの識別名
)


# ----------------------------------------------------------------------
# (2) サブエージェントを @tool でラップする — エージェントのツール化
# ----------------------------------------------------------------------
# 第3章で @tool にした関数の「中身」が、サブエージェントの呼び出しに変わるだけ。
#   - name と description は supervisor のルーティング判断材料 (prompting levers)。
#       「何をするか + いつ使うか」を具体的に書く。
#   - result["messages"][-1].content … サブの最終メッセージだけを取り出して返す。
#       これが「メインに返るのは最終メッセージだけ」の実装上の正体。
@tool("research", description="トピックを調査して要点を返す。事実確認・情報収集が必要なときに使う")
def call_research_agent(query: str) -> str:
    result = research_agent.invoke({"messages": [{"role": "user", "content": query}]})
    return result["messages"][-1].content


# ----------------------------------------------------------------------
# (3) supervisor (メインエージェント) — サブをツールとして渡すだけ
# ----------------------------------------------------------------------
# supervisor には checkpointer を付けていない (このサンプルは 1 ターンの観察用)。
# Subagents の「サブは stateless」という特性を実測するのが目的なので、
# サブ側にも checkpointer は付けない (毎回まっさらなコンテキストで起動する)。
supervisor = create_agent(
    model=MODEL,
    tools=[call_research_agent],
    system_prompt=(
        "あなたは調査を取りまとめる担当者です。"
        "事実確認や情報収集が必要なときは research ツールに調査を依頼し、"
        "その結果を踏まえてユーザーに分かりやすく回答してください。"
    ),
)


def run_once(label: str, query: str) -> None:
    """同じ依頼を 1 回実行し、最終回答を表示する。"""
    print("=" * 70)
    print(f"{label}: {query}")
    print("=" * 70)
    result = supervisor.invoke({"messages": [{"role": "user", "content": query}]})
    print("[supervisor の最終回答]")
    print(result["messages"][-1].content)
    print()


if __name__ == "__main__":
    # ------------------------------------------------------------------
    # 同じ依頼を 2 回実行して「Subagents は毎回同コスト (stateless)」を観察する
    # ------------------------------------------------------------------
    # supervisor に checkpointer を付けていないため、1 回目と 2 回目は完全に
    # 独立した会話です (会話履歴は引き継がれません)。仮に checkpointer を付けて
    # 同じ thread_id で続けても、サブエージェント自体は stateless なので、
    # サブを呼ぶたびに同じフロー (調査の最初からやり直し) を繰り返します。
    query = "subagents というマルチエージェントの方式について教えて"
    run_once("1 回目", query)
    run_once("2 回目 (同じ依頼)", query)

    print("=" * 70)
    print("LangSmith トレースで確認すること (README 参照):")
    print("  1. supervisor の 1 ターンの中に research ツール呼び出しがあり、")
    print("     その内側に research_agent (name で識別) の ReAct ループが")
    print("     入れ子で表示されること。")
    print("  2. モデル呼び出しが 1 回の依頼で 4 回になること")
    print("     (① research 使用を決定 → ②③ サブ内で検索・要約 → ④ 最終応答)。")
    print("  3. 1 回目と 2 回目で呼び出し回数が変わらないこと")
    print("     = Subagents は stateless で毎回同コスト (8-2 の定量比較の裏取り)。")
    print("=" * 70)
