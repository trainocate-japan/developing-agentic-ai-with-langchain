# Agentic AI 開発実践 - LangChain 版 — 演習コードリポジトリ

このリポジトリは、研修コース **「Agentic AI 開発実践 - LangChain 版」** (2 日間) のハンズオン・演習用コード一式です。各章のフォルダ (`chap01`〜`chap08`) に、講師と一緒に動かす **ハンズオン** と、自分で完成させる **演習** が入っています。

> 受講者の皆さんがまず読むのがこの README です。**お使いの章が「Google Colab」か「Google Cloud Shell」かを確認** し、該当するセットアップに進んでください。

---

## 1. 2 つの実行環境

本コースは章によって実行環境が変わります。

| 章 | 日 | 実行環境 | 形式 |
|---|---|---|---|
| 第1〜4章 | Day 1 | **Google Colab** | Notebook (`.ipynb`) |
| 第5〜8章 | Day 2 | **Google Cloud Shell** | Python スクリプト (`.py`) |

- **第1〜4章 (Colab)**: ブラウザだけで完結します。各章の Notebook を Google Colab で開き、API キーは Colab の **[シークレット]** 機能で管理します。
- **第5〜8章 (Cloud Shell)**: このリポジトリを `git clone` し、ターミナルで `.py` を実行します。第6章以降は **Agent Chat UI** をブラウザ (Web Preview) で操作します。

---

## 2. ディレクトリ構成

```
.                              ← このリポジトリのルート
├── README.md                  ← いま読んでいるファイル
├── .env.example               ← 第5〜8章 (Cloud Shell) 用の環境変数ひな形
├── .gitignore
├── chap01/  … 第1章: Agentic AI と LangChain (座学・環境確認)
├── chap02/  … 第2章: LLM API の基礎
├── chap03/  … 第3章: エージェント開発の基本
├── chap04/  … 第4章: メモリと可観測性
├── chap05/  … 第5章: MCP サーバーの利用
├── chap06/  … 第6章: Middleware と HITL
├── chap07/  … 第7章: エージェントの評価
└── chap08/  … 第8章: マルチエージェント開発 (総合演習)
```

各章フォルダの中身は、原則として次の 3 つに分かれています。

| フォルダ | 役割 | あなたの作業 |
|---|---|---|
| `hands-on/` | **ハンズオン**。講師の解説を聞きながら、**作成済みのコードを一緒に実行** | コードは書きません。動かして観察します |
| `exercise/starter/` | **演習**。`# TODO` のコメント箇所を自分で埋めて完成させる | TODO を実装します |
| `exercise/solution/` | 演習の **正解**。答え合わせ・詰まったときの参照用 | 自力で挑戦してから見ましょう |

> 第1章は座学中心のため `hands-on/` はなく、環境確認の演習のみです。

---

## 3. セットアップ

### 第1〜4章 (Google Colab) の場合

1. 各章フォルダの `.ipynb` を **Google Colab で開く** (下の一覧の [Open In Colab] バッジ、または Colab の「GitHub から開く」「アップロード」)。

   各 Notebook の**先頭にも同じバッジが埋め込まれている**ので、GitHub 上で `.ipynb` を開いて
   そこから起動しても構いません。

   | 章 | ハンズオン | 演習 (starter) | 演習 (solution) |
   |---|---|---|---|
   | 第1章 | — (座学中心) | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/trainocate-japan/developing-agentic-ai-with-langchain/blob/main/chap01/exercise/starter/chap01_exercise_1-1_setup.ipynb) | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/trainocate-japan/developing-agentic-ai-with-langchain/blob/main/chap01/exercise/solution/chap01_exercise_1-1_setup.ipynb) |
   | 第2章 | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/trainocate-japan/developing-agentic-ai-with-langchain/blob/main/chap02/hands-on/chap02_handson_2A.ipynb) | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/trainocate-japan/developing-agentic-ai-with-langchain/blob/main/chap02/exercise/starter/chap02_exercise_2B_starter.ipynb) | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/trainocate-japan/developing-agentic-ai-with-langchain/blob/main/chap02/exercise/solution/chap02_exercise_2B_solution.ipynb) |
   | 第3章 | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/trainocate-japan/developing-agentic-ai-with-langchain/blob/main/chap03/hands-on/chap03_handson_3A.ipynb) | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/trainocate-japan/developing-agentic-ai-with-langchain/blob/main/chap03/exercise/starter/chap03_exercise_3B_starter.ipynb) | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/trainocate-japan/developing-agentic-ai-with-langchain/blob/main/chap03/exercise/solution/chap03_exercise_3B_solution.ipynb) |
   | 第4章 | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/trainocate-japan/developing-agentic-ai-with-langchain/blob/main/chap04/hands-on/chap04_handson_4A.ipynb) | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/trainocate-japan/developing-agentic-ai-with-langchain/blob/main/chap04/exercise/starter/chap04_exercise_4B_starter.ipynb) | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/trainocate-japan/developing-agentic-ai-with-langchain/blob/main/chap04/exercise/solution/chap04_exercise_4B_solution.ipynb) |

   > **solution は答えです。** starter で自力で挑戦してから開きましょう。

2. Colab の左サイドバーの **鍵アイコン 🔑 [シークレット]** に、次のキーを登録します。
   - `OPENAI_API_KEY` (全章で必要)
   - `LANGSMITH_API_KEY` (**第4章から** 必要。第4章で発行手順を案内します)
3. ハンズオンは Notebook を上から実行。演習は `starter` の TODO を埋めます。

> API キーは**コードに直接書かず**、必ず [シークレット] に登録してください。

### 第5〜8章 (Google Cloud Shell) の場合

第5〜8章は **Google Cloud Shell** (ブラウザ上で使える Linux ターミナル) で `.py` を実行します。
自分の PC へのインストール作業は不要で、**ブラウザと Google アカウントだけ**で始められます。

#### 手順 0. ブラウザで Cloud Shell を開く

1. ブラウザ (Chrome 推奨) で **Google アカウントにログイン**します。
2. **<https://shell.cloud.google.com/>** にアクセスします。
   (Google Cloud コンソール <https://console.cloud.google.com/> を開き、画面右上のツールバーにある
   **[Cloud Shell をアクティブにする]** アイコン `>_` をクリックしても同じです)
3. 初回は確認ダイアログが出るので **[続行]** (または [承認]) をクリックします。
4. 数十秒のプロビジョニングののち、画面にターミナルが開けば準備完了です。
   次のコマンドで動作確認できます。

   ```bash
   pwd              # /home/<ユーザー名> と表示される (= ホームディレクトリ)
   python3 --version
   ```

#### この先で使う Cloud Shell の操作

| やりたいこと | 操作 |
|---|---|
| **新しいターミナルを開く** | ターミナル上部のツールバーの **[+]** (新しいタブを開く) をクリック |
| **ブラウザでアプリを開く** (第6・8章) | 上部ツールバーの **[ウェブでプレビュー]** アイコン → **[ポートを変更]** でポート番号を指定 |
| **ファイルを編集する** | `nano <ファイル名>` (保存 = `Ctrl+O` → `Enter`、終了 = `Ctrl+X`)。または `cloudshell edit <ファイル名>` でエディタが開く |

> **ホームディレクトリの中身 (clone したリポジトリ・`.env`・venv) は保存されますが、
> ターミナルの「状態」は保存されません。** 新しいタブを開いたときや、しばらく放置して
> 再接続したときは、**ディレクトリ移動 (`cd`) と venv の有効化をやり直す**必要があります。
> 各章の README には、そのまま貼れるコマンドを載せています。

#### 手順 1. 初回セットアップ (第5〜8章で 1 回だけ)

第5章のハンズオン (5-A) で次を **1 回だけ** 行えば、第6〜8章ではこのセットアップを
**使い回します** (作り直しません)。Cloud Shell のターミナルに上から順に貼り付けてください。

```bash
# 1. ホームディレクトリでリポジトリを取得し、リポジトリのルートへ移動 (この 1 回だけ)
cd ~
git clone https://github.com/trainocate-japan/developing-agentic-ai-with-langchain.git
cd ~/developing-agentic-ai-with-langchain   # ← chap01〜chap08 と .env.example がある場所

# 2. リポジトリのルートで仮想環境 (venv) を作って有効化 (第5〜8章で共通)
python3 -m venv .venv
source .venv/bin/activate                   # プロンプトの先頭に (.venv) が付けば成功

# 3. リポジトリのルートで .env を作成し、キーを記入 (第5〜8章で共通)
cp .env.example .env
nano .env                                   # OPENAI_API_KEY と LANGSMITH_API_KEY を記入
                                            #   → 保存は Ctrl+O → Enter、終了は Ctrl+X
```

> リポジトリを `~` (ホームディレクトリ) 以外に clone した場合は、以降に出てくる
> `~/developing-agentic-ai-with-langchain` を実際の場所に読み替えてください。

#### 手順 2. 各章での作業 (章が変わるたび・ターミナルを開き直すたび)

以降、各章では **「リポジトリのルートで venv を有効化 → その章のディレクトリへ移動 →
依存をインストール」** の 3 ステップだけです。次の 4 行は、どのターミナルでもそのまま貼れます。

```bash
# 例: 第5章ハンズオン
cd ~/developing-agentic-ai-with-langchain   # ① リポジトリのルートへ
source .venv/bin/activate                   # ② venv を有効化 (新しいターミナルでは毎回必要)
cd chap05/hands-on                          # ③ その章の作業ディレクトリへ
pip install -r requirements.txt             # ④ 依存をインストール (章ごとに 1 回でよい)
```

> - **venv は必ずリポジトリのルート (`~/developing-agentic-ai-with-langchain`) で有効化します。**
>   章のディレクトリには `.venv` はないので、`chap05/hands-on` などで `source .venv/bin/activate`
>   を実行しても `No such file or directory` になります。
> - `.env` はリポジトリのルートに **1 つ** あれば十分です。各章のスクリプトは、実行位置から上位ディレクトリを遡ってこの `.env` を読み込みます。
> - **`.env` は Git にコミットしないでください** (キーが漏れます)。`.gitignore` で除外済みです。リポジトリに置くのは値の入っていない `.env.example` だけです。

---

## 4. LangSmith トレーシング (第4章以降は常時有効)

第4章以降のハンズオン・演習は、実行すると自動的に **LangSmith** にトレースが記録されます。エージェントの「ループ周回数・呼ばれたツールと引数・トークン消費」を [smith.langchain.com](https://smith.langchain.com) で確認できます。

- Colab (第1〜4章): シークレットに `LANGSMITH_API_KEY` を登録すれば有効になります。
- Cloud Shell (第5〜8章): ルートの `.env` に `LANGSMITH_TRACING=true` と `LANGSMITH_API_KEY` を入れておけば、コード変更なしで有効です (`.env.example` に設定済み)。

> **動かしたら、必ずトレースを見る** — これが本コースを通じての合言葉です。

---

## 5. 演習ストーリー: 社内 IT ヘルプデスクエージェント

第2章以降の演習は、1 つの **「社内 IT ヘルプデスクエージェント」** を章ごとに育てていきます (各章の演習はそれ単独でも完結します)。

| 章 | 追加する要素 | 演習後の姿 |
|---|---|---|
| 第2章 (Step 1) | Function Calling 手動ループ | 稼働状況に答える素朴な QA ループ |
| 第3章 (Step 2) | create_agent / @tool / 構造化出力 | FAQ 検索 + 稼働状況ツールを持つ単体エージェント |
| 第4章 (Step 3) | Checkpointer / LangSmith | 社員ごとに会話を記憶し、トレースで診断できる |
| 第5章 (Step 4) | MCP | 社内ナレッジ MCP サーバーからツールを調達 |
| 第6章 (Step 5) | Middleware / HITL / Agent Chat UI | PII 保護と要承認オペを備え、UI から操作できる |
| 第7章 (Step 6) | 評価 | 回帰評価つき: プロンプト修正の前後を Experiment で比較できる |
| 第8章 (Step 7) | Multi-agent | FAQ 担当・オペ担当を束ねる **Web アプリとして完成** |

最終成果物は「**Agent Chat UI から操作できるヘルプデスク・マルチエージェント**」です。

---

## 6. 各章の概要

| 章 | テーマ | ハンズオン | 演習 |
|---|---|---|---|
| 1 | Agentic AI と LangChain | — (座学) | 環境疎通確認 + 公式ドキュメント検索 |
| 2 | LLM API の基礎 | Chat Completions / Function Calling を動かす | Function Calling 手動 1 周 |
| 3 | エージェント開発の基本 | create_agent で最初のエージェント | ヘルプデスクエージェント v1 |
| 4 | メモリと可観測性 | Checkpointer と LangSmith トレース | 会話を記憶するヘルプデスク v2 |
| 5 | MCP サーバーの利用 | MultiServerMCPClient で 2 サーバー接続 | 社内ナレッジ MCP の接続 v3 |
| 6 | Middleware と HITL | Prebuilt / Custom Middleware | 要承認オペレーション + Agent Chat UI v4 |
| 7 | エージェントの評価 | LangSmith のオフライン評価を一通り (Dataset → Experiment → 比較) | ヘルプデスクの回帰評価 |
| 8 | マルチエージェント開発 | エージェントのツール化 | 総合演習 (最終成果物) |

---

## 7. 前提・補足

- **Python**: 3.10 以上 (Colab / Cloud Shell の標準環境で動作します)。
- **モデル名**: 教材中のモデル名は変数 `MODEL` に集約しています (例 `MODEL = "openai:gpt-5.4"`)。研修実施時には講師が指定する最新のモデル名に読み替えてください。1 箇所を直すだけで全体に反映されます。
- **主要ライブラリ**: langchain 1.3 系 / langchain-openai / langgraph 1.2 系 / langchain-mcp-adapters (第5章) / openevals (第7章) など。各章の `requirements.txt` に記載しています。研修実施時は再現性のためバージョンのピン留めを推奨します。
- **公式ドキュメント**: 現行は [docs.langchain.com](https://docs.langchain.com) です (旧 python.langchain.com はアーカイブ)。変化の速い領域なので、困ったら一次情報を参照する習慣をつけましょう。

---

困ったときは、各章フォルダの `README.md` に手順・前提・期待される出力が書かれています。まずはそちらを確認してください。良い学習を！
