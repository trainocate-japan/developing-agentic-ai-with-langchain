# 演習 2-B【solution / 正解】: Function Calling 手動 1 周 — ヘルプデスク Step 1

研修コース「Agentic AI 開発実践 - LangChain 版」 / **第2章「LLM API の基礎」** の演習の**正解コード**です。

- **ファイル**: [`chap02_exercise_2B_solution.ipynb`](./chap02_exercise_2B_solution.ipynb)
- **問題 (starter)**: [`../starter/chap02_exercise_2B_starter.ipynb`](../starter/chap02_exercise_2B_starter.ipynb)
- **形式**: Google Colab Notebook (Jupyter nbformat 4)
- **対応する学習トピック**: Function Calling 手動 1 周 (エージェントループの心臓部)

> **注意**: これは正解です。TODO (`# TODO`) を埋める前に答えを見てしまわないよう、
> **まずは starter で自力で挑戦**してください。答え合わせや、詰まったときの参照に使います。

## 演習の狙い

Function Calling の 4 ステップ (ツール定義 → tool_calls 受信 → アプリ側で関数実行 → tool ロールで結果返却 →
最終応答) を、フレームワークなしで手動 1 周させ、エージェントループの心臓部を理解します。
ハンズオン 2-A の後半 (セクション 7) で動かした天気エージェント (`get_weather`) を、社内 IT ヘルプデスクの
`get_system_status(service)` ツールへ翻案した**完全動作版**です。

## ヘルプデスク演習ストーリーにおける位置づけ (Step 1)

本コースの演習ストーリー「**社内 IT ヘルプデスクエージェント**」の **Step 1** です。
ここで作る「稼働状況に答える素朴な QA ループ (openai 直接)」を土台に、第3章以降で
FAQ 検索・会話記憶・MCP・承認フロー・マルチエージェントへと段階的に拡張していきます。

## この Notebook の構成

| セクション | 内容 |
|---|---|
| 0. セットアップ | `openai` インストール、API キー、`client` / `MODEL` |
| 1. 題材の関数 | `get_system_status(service)` ダミー関数 (複数サービスの固定ステータスを dict で保持) |
| 2. ステップ① | ツール定義 (JSON Schema、丁寧な `description`) を付けて「勤怠システムは動いていますか?」を送信 |
| 3. ステップ② | `finish_reason="tool_calls"` の確認、`tool_calls[0]` から関数名・引数を取り出し |
| 4. ステップ③ | `json.loads` してアプリ側で関数を実行 |
| 5. ステップ④ | assistant (tool_calls 入り) + tool メッセージ (`tool_call_id` 一致) を積んで再送信、最終応答 |
| 6. tool_calls が返らない確認 | 「こんにちは」を送り `tool_calls` が `None` であることを確認 |
| 7. (発展) while ループ + 2 ツール | ステップ 2〜4 をループ化し、`get_system_status` + `get_maintenance_schedule` の 2 ツール構成に |

各ステップに「何を・なぜ」やっているかの Markdown 解説とコードコメントを付けています。
定番のつまずき (assistant メッセージ積み忘れ / `tool_call_id` 不一致 / `arguments` は JSON 文字列) も
注意喚起の Markdown で明示しています。

## 前提条件

- **ハンズオン 2-A を完了している**こと (同一 Colab 環境。`client` / `MODEL` の準備が前提。後半の `get_weather` デモで FC の 4 ステップを確認済み)
- Google Colab で開き、Colab シークレットに `OPENAI_API_KEY` を登録済みであること

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/trainocate-japan/developing-agentic-ai-with-langchain/blob/main/chap02/exercise/solution/chap02_exercise_2B_solution.ipynb)

> 上のバッジ、または GitHub 上で `.ipynb` を開いたときに先頭に表示されるバッジから、この Notebook を
> Colab で直接開けます。バッジの仕組みはハンズオン 2-A の README を参照してください。

## starter の TODO との対応

starter で `# TODO` になっている 3 か所が、この solution では次のように埋まっています。

- **TODO①** → セクション 2 の `tools` の `parameters` (JSON Schema: `type` / `properties` / `required`)
- **TODO②** → セクション 3 の `tool_call.function.name` 取得と `json.loads(tool_call.function.arguments)`
- **TODO③** → セクション 5 の `messages.append(response.choices[0].message)` と `role:"tool"` メッセージの追加

## 完成の目安

- ✅ 「勤怠システムは動いていますか?」への最終応答が得られる
- ✅ 「こんにちは」では `tool_calls` が返らない
- ✅ (発展) while ループ + 2 ツールで連鎖的なツール利用ができる

## この完成コードは保存してください

**完成コードは第3章で `create_agent` 版と diff 比較するため、必ず保存してください。**
手動 1 周を経験したうえでフレームワーク版と並べることで、「何が自動化されたのか」が明確になります。

## 本章 (OpenAI API) ↔ 第3章 (LangChain) 対応表

本章 (OpenAI API 直叩き) で使った語彙は、第3章の LangChain のメッセージ抽象と次のように 1 対 1 で対応します
(Notebook の末尾にも再掲しています)。

| 本章 (OpenAI API) | 第3章 (LangChain) |
|---|---|
| `{"role": "system", ...}` | `SystemMessage` |
| `{"role": "user", ...}` | `HumanMessage` |
| `{"role": "assistant", ...}` | `AIMessage` |
| `{"role": "tool", ...}` | `ToolMessage` |
| `message.tool_calls` | `AIMessage.tool_calls` |
| `tool_call_id` | `ToolMessage.tool_call_id` |
| ツール定義の `description` | `@tool` 関数の docstring |
| ステップ 2〜4 の while ループ | `create_agent` が自動実行 |
