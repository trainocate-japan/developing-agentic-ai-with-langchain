# ハンズオン 2-A: Chat Completions API と Function Calling を動かす

研修コース「Agentic AI 開発実践 - LangChain 版」 / **第2章「LLM API の基礎」** のハンズオン用コードです。

- **ファイル**: [`chap02_handson_2A.ipynb`](./chap02_handson_2A.ipynb)
- **形式**: Google Colab Notebook (Jupyter nbformat 4)
- **対応する学習トピック**: Chat Completions API の基本 / トークンと主要パラメータ / Function Calling 手動 1 周
- **演習設計**: ハンズオン 2-A (手順 1〜7。前半 1〜5 が Chat Completions API、後半 6〜7 が Function Calling デモ)

## 概要

このハンズオンは、講師の解説を聞きながら**作成済みのセルを上から順に一緒に実行する**形式です
(コードを書く場面はありません。コードを書くのは演習 2-B です)。
OpenAI API を `openai` パッケージで直接叩き、エージェントの足元で動いている仕組み——
メッセージ配列とロール、API のステートレス性、トークンとコスト、生成パラメータ——を、
手を動かして確認します。
さらに後半では、**Function Calling 手動 1 周のデモ** (`get_weather`) を作成済みコードで通し、
LLM に「行動」をさせる仕組みの 4 ステップ (ツール定義 → `tool_calls` 受信 → アプリ側で関数実行 → 結果返却) を
「動かして理解」します (このデモで見た流れを、演習 2-B では `get_system_status` で自分の手で実装します)。

## Google Colab での開き方

GitHub リポジトリに配置した `.ipynb` は、次の **[Google Colab で開く] バッジ**から直接起動できます。

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/trainocate-japan/developing-agentic-ai-with-langchain/blob/main/chap02/hands-on/chap02_handson_2A.ipynb)

> **バッジの仕組み**: Colab は `https://colab.research.google.com/github/<OWNER>/<REPO>/blob/<BRANCH>/<パス>.ipynb`
> という URL で、GitHub 上の Notebook を直接読み込んで開きます。上のバッジ画像にこの URL をリンクしているだけです。
> 本リポジトリでは `<OWNER>` = `trainocate-japan`、`<REPO>` = `developing-agentic-ai-with-langchain`、`<BRANCH>` = `main` です。
>
> **Notebook 自体の先頭にも同じバッジを埋め込んであります**。GitHub 上で `.ipynb` を開けば、
> この README を経由しなくても [Open In Colab] ボタンから直接起動できます。
>
> バッジを使わない場合は、Colab のメニュー `ファイル > ノートブックを開く > GitHub` タブに
> リポジトリ URL を貼り付けても開けます。

## 前提条件

- **Google アカウント**を持っていること
- **Google Colab** が使えること (ブラウザのみで OK。インストール不要)
- Colab の **[シークレット]** (左サイドバーの鍵アイコン 🔑) に `OPENAI_API_KEY` を登録済みであること
  - 第1章の演習 1-1 で登録済みのはずです。未登録なら Notebook 冒頭の手順に従って登録してください
- インターネット接続 (API を呼び出します)

> **API キーの扱い**: キーはコードに直接書かず、必ず Colab シークレットで管理します。
> Notebook は「Colab シークレット方式 + 非 Colab 環境の環境変数フォールバック」の両対応です。

## 各セルの狙い

| セクション | 狙い | 期待される出力例 |
|---|---|---|
| 0. セットアップ | `openai` インストール、API キー読込、`client` と `MODEL` の準備 | `準備完了。使用モデル: gpt-5.4` |
| 1. 最小の API 呼び出し | `messages` (辞書のリスト) で質問し、`choices[0].message.content` / `finish_reason` / `usage` を読む | LLM の定義 1 文 + `finish_reason: stop` |
| 2. system プロンプト | system 1 行で口調・役割が変わる (関西弁の例 + ヘルプデスク一次対応の例) | 関西弁の回答 / ヘルプデスク口調の回答 |
| 3. ステートレス性 | 名前を伝える→新規呼び出しで聞く→**忘れている**ことを実演 | 【2回目】「お名前を伺っていません」等 |
| 4. ミニチャットボット | 履歴を `append` し全送信すれば「覚える」。(a) 対話版 `input()` と (b) スクリプト版 `turns` の両方 | スクリプト版で名前「カレン」を答える |
| 5. usage とコスト概算 | `usage` の 3 数字を読む。ターンが進むと `prompt_tokens` が増えることを実測。フェルミ推定の電卓 | トークン数の表が増加。月額概算 |
| 6. パラメータ実験 | `temperature` 0 vs 1.2 のばらつき比較。`max_completion_tokens=20` で `finish_reason="length"` | temp=0 はほぼ同じ句 / `finish_reason: length` |
| 7. Function Calling デモ | `get_weather` を題材に手動 1 周。`tool_calls` 受信 → `json.loads` → アプリ側で実行 → tool ロールで結果返却。「こんにちは」では `tool_calls` が返らないことも確認 | `finish_reason: tool_calls` → 最終応答「東京は晴れで…」 |

### ミニチャットボットの 2 形態について (セクション 4)

- **(a) 対話版**: `input()` で手入力する版。Colab で動きますが、入力待ちで自動実行できません。
  一度動かしたら停止して、(b) に進みます。
- **(b) スクリプト版**: `turns = ["私の名前はカレンです", "私の名前は?"]` を順に処理する版。
  ロジックは対話版と同一で、`input()` をループに置き換えただけ。手入力なしで「履歴を積むと覚える」対比を再現できます。

## 実行時の注意

- 本教材のモデル名 `MODEL = "gpt-5.4"` は**将来モデルの例示**です。研修で案内されるモデル名に
  準備セル 1 箇所で差し替えてください。
- `!pip install -U openai` は最新版を取りに行きます。バージョンによっては教材と挙動が変わることがあります。
- reasoning 系モデルでは `temperature` 等が指定不可の場合があります。セクション 6 でパラメータ関連の
  エラーが出たら、それは「このモデルはそのパラメータ非対応」のサインです。

## 次のステップ

このハンズオンと**同じ Colab 環境**で、演習 2-B (`../exercise/`) に進みます。
ハンズオン後半 (セクション 7) の `get_weather` デモで動かして理解した Function Calling の 4 ステップを、
演習ではヘルプデスクの `get_system_status` ツールで、自分の手で (`# TODO` を埋めて) 1 周させます。
