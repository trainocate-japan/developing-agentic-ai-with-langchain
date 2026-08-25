# 演習 1-1【starter / 受講者用】: 環境疎通確認 + 公式ドキュメント検索

研修コース「LangChain による Agentic AI 開発実践」 / **第1章「Agentic AI と LangChain」** の演習用 Notebook (受講者用) です。

- **ファイル**: [`chap01_exercise_1-1_setup.ipynb`](./chap01_exercise_1-1_setup.ipynb)
- **形式**: Google Colab Notebook (Jupyter nbformat 4)
- **対応する学習目標**: 章目標 5 (公式ドキュメントの活用)

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/trainocate-japan/developing-agentic-ai-with-langchain/blob/main/chap01/exercise/starter/chap01_exercise_1-1_setup.ipynb)

> 上のバッジ、または GitHub 上で `.ipynb` を開いたときに先頭に表示されるバッジから、この Notebook を
> Colab で直接開けます。

## 演習の狙い

第1章は座学中心の章です。この演習は、研修で使う環境を整える準備運動と、
**公式ドキュメント docs.langchain.com を一次情報として引く最初の体験**を兼ねています
(章目標 5: 公式ドキュメントの活用)。

本格的なコード実装は第2章から始まります。ここでは環境の疎通確認とドキュメントの引き方に集中します。

## やること

1. Google Colab の **[シークレット]** に `OPENAI_API_KEY` を登録する
2. **疎通確認セル**を実行し、キーが読み込めることを確認する (キーの存在チェックのみ。**API は呼び出しません**)
3. 公式ドキュメント **docs.langchain.com** で **3 ページ**を検索し、その URL を提出する
   - create_agent の解説ページ
   - Middleware の組み込み一覧 (Prebuilt) のページ
   - リリース changelog のページ

## 埋めるべき TODO (3 か所)

Notebook の最後のコードセルに、URL を貼り付ける **3 つの `# TODO`** があります。

| TODO | 変数 | 内容 |
|---|---|---|
| ① | `create_agent_url` | create_agent の解説ページの URL |
| ② | `middleware_list_url` | Middleware 組み込み一覧 (Prebuilt) のページの URL |
| ③ | `changelog_url` | リリース changelog のページの URL |

3 つの `# TODO` を埋めてセルを実行すると、各 URL が `docs.langchain.com` ドメインかどうかを自動チェックします。

## 前提条件

- **Google アカウント** (Colab を使うため)
- **事前配布された OpenAI API キー** (この演習では存在確認のみに使います)

## 提出物

- シークレット登録済みの Colab 環境 (疎通確認セルで **✅** の成功メッセージが出た状態)
- **3 つの URL** (create_agent / Middleware 組み込み一覧 / changelog)

## 評価のポイント

- **環境準備**: シークレットへの `OPENAI_API_KEY` 登録と、疎通確認セルの成功メッセージが確認できたか。
- **ドキュメント検索**: 3 ページとも、**現行ドキュメント `docs.langchain.com` ドメインから特定**できたか。旧サイト `python.langchain.com` と混同していないか。

## ヒント

- 検索エンジンからだと旧サイト `python.langchain.com` に着地しがちです。**URL のドメインが `docs.langchain.com` か**を必ず確認してください。
- Python 向けページは URL に `/oss/python/` を含みます。
- 行き詰まったら、まずブラウザで https://docs.langchain.com を直接開き、ナビゲーションから辿るのが確実です。
