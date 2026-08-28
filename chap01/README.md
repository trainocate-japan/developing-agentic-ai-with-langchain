# 第1章「Agentic AI と LangChain」コード

研修コース「Agentic AI 開発実践 - LangChain 版」 / **第1章「Agentic AI と LangChain」** のコード一式です。

## この章のコードについて (重要)

**第1章は座学中心の章です。** エージェントの原理、LangChain の歴史と v1.0、パッケージとエコシステム、公式ドキュメントの歩き方を「知識」として身に付ける章であり、**ハンズオン用のコーディング教材 (穴埋め形式の実装演習) はありません**。

この章で実施するのは、次の **演習 1-1 のみ**です。

- **演習 1-1: 環境疎通確認 + 公式ドキュメント検索ミニ演習**
  - 研修で使う Google Colab と OpenAI API キーの**疎通を確認**し (キーの存在チェックのみ・API 呼び出しはしません)、
  - 公式ドキュメント docs.langchain.com を**一次情報として引く最初の体験**をします。

本格的なコード実装 (Function Calling やエージェント構築) は**第2章以降**で行います。第1章はその準備運動として、環境とドキュメントの引き方を整えるのが目的です。

## ディレクトリ構成

```
chap01/
├── README.md                                       # このファイル
└── exercise/
    ├── starter/
    │   ├── README.md                               # 演習の説明
    │   └── chap01_exercise_1-1_setup.ipynb         # TODO を自分で埋める版
    └── solution/
        ├── README.md                               # 解答例の説明
        └── chap01_exercise_1-1_setup.ipynb         # 解答例 (参照 URL 記入済み)
```

## 演習 1-1 の概要

| 項目 | 内容 |
|---|---|
| **狙い** | 章目標 5「公式ドキュメントを一次情報として活用できる」を、環境準備とあわせて体験する |
| **対応する学習目標** | 章目標 5 (公式ドキュメントの活用) |
| **やること** | ① Colab シークレットに `OPENAI_API_KEY` を登録 → ② 疎通確認セルを実行 (存在チェックのみ) → ③ docs.langchain.com で 3 ページを検索して URL を提出 |
| **前提条件** | Google アカウント、研修で配布される OpenAI API キー |
| **この演習のゴール** | シークレット登録済みの Colab 環境、3 つの URL (create_agent / Middleware 組み込み一覧 / changelog) |

## できたか確認しよう

- **環境準備**: Colab シークレットに `OPENAI_API_KEY` を登録し、疎通確認セルで成功メッセージが出ていれば OK です。
- **ドキュメント検索**: 3 ページ (create_agent / Middleware 組み込み一覧 / changelog) を、**いずれも現行ドキュメント `docs.langchain.com` ドメイン**で見つけられていれば OK です。旧サイト `python.langchain.com` と取り違えていないか確認しましょう。

## 環境について

- 想定環境は **Google Colab** です。Colab シークレット (鍵アイコン) に API キーを登録する方式を採用しています。
- Colab 以外 (ローカルの Jupyter など) でも動くよう、環境変数 `OPENAI_API_KEY` を読むフォールバックを入れてあります。
- この演習では **OpenAI API は呼び出しません**。キーの存在を確認するだけです。
