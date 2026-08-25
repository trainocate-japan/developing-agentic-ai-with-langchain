# 演習 2-B【starter / 問題】: Function Calling 手動 1 周 — ヘルプデスク Step 1

研修コース「Agentic AI 開発実践 - LangChain 版」 / **第2章「LLM API の基礎」** の演習用コード (TODO 穴埋め版) です。

- **ファイル**: [`chap02_exercise_2B_starter.ipynb`](./chap02_exercise_2B_starter.ipynb)
- **正解**: [`../solution/chap02_exercise_2B_solution.ipynb`](../solution/chap02_exercise_2B_solution.ipynb)
- **形式**: Google Colab Notebook (Jupyter nbformat 4)
- **対応する学習トピック**: Function Calling 手動 1 周 (エージェントループの心臓部)
- **対応する学習目標**: 章目標 1・4・5

## 演習の狙い

第1章の ReAct ループの「行動」を実現する仕組み——**Function Calling**——を、
フレームワークなし (openai パッケージ直接) で**手動で 1 周**させます。
ハンズオン 2-A の後半 (セクション 7) で `get_weather` を題材に動かして確認した
「ツール定義 → tool_calls 受信 → アプリ側で関数実行 → tool ロールで結果返却 → 最終応答」の 4 ステップを、
今度は helpdesk の `get_system_status` で、TODO コード (`# TODO`) を自分で埋めて完成させることで、体で覚えるのが狙いです。

## ヘルプデスク演習ストーリーにおける位置づけ (Step 1)

本コースの演習は「**社内 IT ヘルプデスクエージェント**」を第2〜8章で段階的に拡張して完成させます。
この演習はその **Step 1** にあたり、社内システムの稼働状況に答える `get_system_status(service)` ツール
(ダミー実装) を LLM から「呼び出させる」**素朴な QA ループ**を作ります。

| 章 | 追加する要素 | 演習後の姿 |
|---|---|---|
| **第2章 (この演習)** | **Function Calling 手動ループ** | **稼働状況に答える素朴な QA ループ (openai 直接)** |
| 第3章 | create_agent / @tool | FAQ 検索 + 稼働状況ツールを持つ単体エージェント |
| 第4章以降 | メモリ / MCP / HITL / 評価 / マルチエージェント | … 最終的に Web UI から操作できるヘルプデスクへ |

## 前提条件

- **ハンズオン 2-A を完了している**こと (同一 Colab 環境で続けて実施。`client` / `MODEL` の準備が前提)
  - 特にハンズオン後半 (セクション 7) の `get_weather` デモで、Function Calling の 4 ステップを動かして確認済みであること
- Google Colab で開き、Colab シークレットに `OPENAI_API_KEY` を登録済みであること

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/trainocate-japan/developing-agentic-ai-with-langchain/blob/main/chap02/exercise/starter/chap02_exercise_2B_starter.ipynb)

> 上のバッジ、または GitHub 上で `.ipynb` を開いたときに先頭に表示されるバッジから、この Notebook を
> Colab で直接開けます。バッジの仕組みはハンズオン 2-A の README を参照してください。

## 埋めるべき TODO (3 か所)

| TODO | 場所 (Notebook セクション) | 内容 | ヒント |
|---|---|---|---|
| **①** | 2. ステップ① ツール定義 | ツール定義の `parameters` (JSON Schema) | `service` という文字列引数を必須で定義。`type` / `properties` / `required` を埋める |
| **②** | 3. ステップ② tool_calls 受信 | `message.tool_calls[0]` から関数名・引数を取り出し `json.loads` | `arguments` は dict ではなく JSON **文字列**。`json.loads()` でパースする |
| **③** | 5. ステップ④ 結果を返す | assistant (tool_calls 入り) と tool メッセージの履歴追加 | `tool_call_id` はモデルが発行した `tool_calls[0].id` をそのまま使う。先に tool_calls 入り assistant メッセージを積む |

TODO 以外のセルは完成状態なので、上の 3 か所に集中してください。
**発展課題** (while ループ化・ツール 2 つ) も TODO 付きで用意しています (早く終わった人向け。必須ではありません)。

## 完成の目安

- ✅ 「**勤怠システムは動いていますか?**」への**最終応答**が得られる
- ✅ 「**こんにちは**」では `tool_calls` が**返らない** (モデルがツール不要と正しく判断する)

## つまずいたときのエラー早見表

| エラー | 原因 | 対応する TODO |
|---|---|---|
| `TypeError: string indices must be integers` | `arguments` を `json.loads` せず dict 扱いした | ② |
| `BadRequestError: messages with role 'tool' must be a response to a preceding message with 'tool_calls'` | assistant メッセージ (tool_calls 入り) の積み忘れ or 順序逆 | ③ |
| ツールが呼ばれない (`tool_calls` が None のまま) | `parameters` の JSON Schema が不完全 | ① |

## 完成したら必ず保存してください

**完成コードは第3章で `create_agent` 版と diff 比較するため、必ず保存してください。**
手動で書いたこのループと、フレームワークが自動化したコードを並べることで、
「LangChain が何を肩代わりしてくれているのか」を自分のコードで確認します。
