# 演習 1-1【solution / 講師用】: 環境疎通確認 + 公式ドキュメント検索

研修コース「Agentic AI 開発実践 - LangChain 版」 / **第1章「Agentic AI と LangChain」** の演習 1-1 の**解答 (講師用)** です。

- **ファイル**: [`chap01_exercise_1-1_setup.ipynb`](./chap01_exercise_1-1_setup.ipynb)
- **問題 (starter)**: [`../starter/chap01_exercise_1-1_setup.ipynb`](../starter/chap01_exercise_1-1_setup.ipynb)
- **形式**: Google Colab Notebook (Jupyter nbformat 4)
- **対応する学習目標**: 章目標 5 (公式ドキュメントの活用)

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/trainocate-japan/developing-agentic-ai-with-langchain/blob/main/chap01/exercise/solution/chap01_exercise_1-1_setup.ipynb)

> 上のバッジ、または GitHub 上で `.ipynb` を開いたときに先頭に表示されるバッジから、この Notebook を
> Colab で直接開けます。

## 演習の狙い

第1章は座学中心の章です。この演習は、研修で使う環境を整える準備運動と、
**公式ドキュメント docs.langchain.com を一次情報として引く最初の体験**を兼ねています
(章目標 5: 公式ドキュメントの活用)。

## starter との違い

- starter の **3 つの `# TODO`** (URL 提出欄) を、本解答では**参照 URL 記入済み**にしています。
- さらに、**新旧サイトの見分け方**と、**3 ページがそれぞれ何のページか**の一言解説を Markdown で追加しています (Notebook の最後のセル)。

## 記入済みの 3 つの参照 URL

いずれも現行ドキュメント `docs.langchain.com` 上に実在することを確認済みです。

| ページ | 参照 URL | 何のページか |
|---|---|---|
| **create_agent** | `https://docs.langchain.com/oss/python/langchain/agents` | エージェント本体を作る中心関数 `create_agent` の解説 (Agents)。第3章で本格使用 |
| **Middleware 組み込み一覧 (Prebuilt)** | `https://docs.langchain.com/oss/python/langchain/middleware/built-in` | 組み込み Middleware の一覧 (Prebuilt middleware)。第6章で本格使用 |
| **changelog** | `https://docs.langchain.com/oss/python/releases/changelog` | v1.0 以降の変更点をまとめたリリース履歴 |

> **これらは参考です。** docs.langchain.com の URL 体系 (パス構成) は改訂されることがあります。
> **重要なのは、旧サイト `python.langchain.com` ではなく現行サイト `docs.langchain.com` で見つけられること自体**です。
> 研修実施時は、講師が docs.langchain.com を開いて最新の URL を最終確認してください。

## 前提条件

- **Google アカウント** (Colab を使うため)
- **事前配布された OpenAI API キー** (この演習では存在確認のみに使います)

## 提出物 (受講者から)

- シークレット登録済みの Colab 環境 (疎通確認セルで **✅** の成功メッセージ)
- **3 つの URL** (create_agent / Middleware 組み込み一覧 / changelog)

## 評価のポイント (採点指針)

- **環境準備**: シークレットへの `OPENAI_API_KEY` 登録と、疎通確認セルの成功メッセージが確認できたか。
- **ドキュメント検索**: 3 ページとも、**現行ドキュメント `docs.langchain.com` ドメインから特定**できたか。
  - 旧サイト `python.langchain.com` の URL を出していたら、新旧の見分け方 (ドメイン確認) を再説明する。
  - パスが上表と多少異なっても、現行ドメインで該当ページに到達できていれば可とする (URL 体系は変わりうるため)。
