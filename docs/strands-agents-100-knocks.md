# Strands Agents 100本ノック

Strands Agents (Python SDK) を基礎から本番運用まで網羅的に理解するための演習リスト。
1本 = 1エージェント(または1機能追加)。番号順に進めると、公式ドキュメントの
ユーザーガイドをほぼ一周できる構成になっている。

## 前提アーキテクチャ

- **エージェント**: Python + `strands-agents` SDK。最終的に Amazon Bedrock AgentCore Runtime にデプロイ
- **WebUI**: TypeScript(超シンプル構成。Vite + React + fetch のみ、テストは Vitest 最小限)。ローカル実行
- 第1〜9章はローカル実行で完結。第10章で AgentCore Runtime + WebUI に統合する

## 進め方の目安

- ★ = 基礎(写経レベル) / ★★ = 機能の組み合わせ / ★★★ = 設計判断が必要
- 各章の冒頭に対応する公式ドキュメントのセクションを書いてあるので、先に流し読みしてから手を動かす

---

## 第1章 エージェントの基礎(1〜10)

> 対応ドキュメント: Quickstart / Agents / Structured Output

| No | タイトル | 学ぶこと | 難易度 |
|---|---|---|---|
| 1 | Hello Agent | `Agent()` の生成と呼び出し。最小3行のエージェント | ★ |
| 2 | ペルソナエージェント | `system_prompt` でキャラクター・役割を固定する | ★ |
| 3 | モデル設定 | `BedrockModel` の `model_id` / `temperature` / `max_tokens` | ★ |
| 4 | モデル比較 | 同じプロンプトを Claude / Nova など複数モデルに投げて挙動比較 | ★ |
| 5 | 非同期呼び出し | `invoke_async` と asyncio の基本 | ★ |
| 6 | マルチターン会話 | `agent.messages` を確認しながら複数ターンの対話を続ける | ★ |
| 7 | 構造化出力 | Pydantic モデルを使った `structured_output`(例: レシピをJSONで) | ★★ |
| 8 | 画像入力 | マルチモーダル入力(画像を渡して説明させる) | ★★ |
| 9 | ドキュメント入力 | PDF などのドキュメントを渡して要約させる | ★★ |
| 10 | 結果の解剖 | `AgentResult` の `stop_reason` / トークン使用量 / メトリクスを観察 | ★ |

## 第2章 ツールの基礎(11〜20)

> 対応ドキュメント: Tools Overview / Python Tools / Community Tools Package

| No | タイトル | 学ぶこと | 難易度 |
|---|---|---|---|
| 11 | 電卓エージェント | `@tool` デコレータで最初の自作ツール | ★ |
| 12 | 型ヒントと docstring | 型ヒント・docstring がツール仕様(スキーマ)になる仕組み | ★ |
| 13 | ツールの使い分け | 天気・時刻など複数ツールを持たせ、モデルの選択を観察 | ★ |
| 14 | ツールのエラー処理 | ツール内で例外を起こし、エージェントのリカバリを観察 | ★★ |
| 15 | 非同期ツール | `async def` のツール定義 | ★★ |
| 16 | ToolContext | ツール内から `tool_use_id` やエージェント状態にアクセス | ★★ |
| 17 | クラスベースツール | `TOOL_SPEC` / モジュール形式でのツール定義(デコレータを使わない方法) | ★★ |
| 18 | コミュニティツール入門 | `strands-agents-tools` の `calculator` / `current_time` | ★ |
| 19 | HTTP リクエスト | `http_request` ツールで外部 API(例: 為替レート)を叩く | ★★ |
| 20 | ファイル操作エージェント | `file_read` / `file_write` / `python_repl` でローカル作業をさせる | ★★ |

## 第3章 ツール応用と MCP(21〜30)

> 対応ドキュメント: MCP Tools / Tool Executors / Advanced Tool Usage

| No | タイトル | 学ぶこと | 難易度 |
|---|---|---|---|
| 21 | ツールの直接呼び出し | `agent.tool.xxx()` でモデルを介さず強制実行する | ★★ |
| 22 | 動的ツール管理 | 実行中にツールを追加・削除(tool registry の操作) | ★★ |
| 23 | 並列ツール実行 | `ConcurrentToolExecutor` で複数ツールを同時実行 | ★★ |
| 24 | 直列ツール実行 | `SequentialToolExecutor` との挙動比較 | ★★ |
| 25 | ストリーミングツール | yield で途中経過を返すツール | ★★★ |
| 26 | MCP (stdio) | 既存 MCP サーバ(例: AWS Documentation MCP)へ stdio 接続 | ★★ |
| 27 | MCP (Streamable HTTP) | HTTP トランスポートでの MCP 接続 | ★★ |
| 28 | 自作 MCP サーバ | FastMCP で自作サーバを立てて Strands から使う | ★★★ |
| 29 | 複数 MCP の統合 | 複数 MCP サーバ + 自作ツールの混在 | ★★★ |
| 30 | 大量ツールの絞り込み | カタログ→選択の2段構えで多数のツールから動的選択(`retrieve` の考え方) | ★★★ |

## 第4章 コンテキストと会話管理(31〜40)

> 対応ドキュメント: State / Conversation Management / Prompts

| No | タイトル | 学ぶこと | 難易度 |
|---|---|---|---|
| 31 | 無管理の限界 | `NullConversationManager` で長い会話がどう破綻するか観察 | ★ |
| 32 | スライディングウィンドウ | `SlidingWindowConversationManager` で履歴を一定数に維持 | ★ |
| 33 | 要約による圧縮 | `SummarizingConversationManager`(要約モデルの差し替えも) | ★★ |
| 34 | 自作会話マネージャ | `ConversationManager` を継承してカスタム戦略を実装 | ★★★ |
| 35 | エージェント状態 | `agent.state` の get/set(会話履歴に乗らない状態の保持) | ★ |
| 36 | 呼び出しスコープの状態 | `invocation_state` でツールにリクエスト単位の値を渡す | ★★ |
| 37 | プロンプトキャッシュ | システムプロンプト/ツールのキャッシュポイントでコスト削減 | ★★ |
| 38 | 履歴の直接操作 | `messages` を直接編集して文脈を注入・改変 | ★★ |
| 39 | コンテキスト溢れ対応 | context overflow 発生時の挙動とハンドリング | ★★ |
| 40 | 会話の復元 | 保存した `messages` から会話を再開する(セッションの素振り) | ★★ |

## 第5章 ストリーミングとフック(41〜50)

> 対応ドキュメント: Streaming / Async Iterators / Callback Handlers / Hooks

| No | タイトル | 学ぶこと | 難易度 |
|---|---|---|---|
| 41 | ストリーミング基礎 | `stream_async` でトークン逐次表示 | ★ |
| 42 | コールバックハンドラ | `callback_handler` でイベントを受ける(デフォルト実装との比較) | ★ |
| 43 | イベントの分類 | text delta / tool use / lifecycle イベントを仕分けて表示 | ★★ |
| 44 | 進捗UIの素振り | ツール実行中だけスピナーを出す等、イベント駆動の表示制御 | ★★ |
| 45 | ライフサイクルフック | `BeforeInvocationEvent` / `AfterInvocationEvent` でロギング | ★★ |
| 46 | ツール呼び出しの検証 | `BeforeToolCallEvent` で引数の検証・書き換え・拒否 | ★★★ |
| 47 | ツール結果の加工 | `AfterToolCallEvent` で結果の整形・監査ログ | ★★ |
| 48 | メッセージへの介入 | `MessageAddedEvent` で履歴追加時に処理を挟む | ★★ |
| 49 | 人間の承認フロー | `handoff_to_user` / フックで危険操作の承認を求める (human-in-the-loop) | ★★★ |
| 50 | 実験的機能を試す | bidirectional streaming or agent steering(experimental) | ★★★ |

## 第6章 セッションとメモリ(51〜60)

> 対応ドキュメント: Sessions / Session Managers / AgentCore Memory

| No | タイトル | 学ぶこと | 難易度 |
|---|---|---|---|
| 51 | ファイルセッション | `FileSessionManager` で会話と状態をローカル永続化 | ★ |
| 52 | プロセス再起動テスト | スクリプトを再起動して同じ session_id で会話が続くことを確認 | ★ |
| 53 | S3 セッション | `S3SessionManager` でクラウド永続化 | ★★ |
| 54 | 自作リポジトリ | `SessionRepository` を実装(例: SQLite / DynamoDB) | ★★★ |
| 55 | メモリツール | community の `memory` / mem0 系ツールで長期記憶 | ★★ |
| 56 | AgentCore Memory 短期 | AgentCore Memory(short-term)でセッション内の文脈保持 | ★★ |
| 57 | AgentCore Memory 長期 | long-term memory でユーザーの嗜好を会話横断で記憶 | ★★★ |
| 58 | パーソナライズ | 記憶した嗜好に基づいて応答を変えるエージェント | ★★★ |
| 59 | マルチユーザー分離 | ユーザーごとの session / memory の分離設計 | ★★★ |
| 60 | 記憶戦略の比較 | 「全部保存 / 要約 / 抽出」のメモリ戦略を比較する | ★★★ |

## 第7章 モデルプロバイダと安全性(61〜70)

> 対応ドキュメント: Model Providers / Safety & Security / Guardrails

| No | タイトル | 学ぶこと | 難易度 |
|---|---|---|---|
| 61 | Anthropic 直接続 | `AnthropicModel` で Bedrock を経由せず API 直叩き | ★ |
| 62 | OpenAI プロバイダ | `OpenAIModel`(互換APIへの接続も) | ★ |
| 63 | ローカルLLM | Ollama でローカルモデルを使う | ★★ |
| 64 | LiteLLM | LiteLLM 経由で各社モデルを統一インターフェースで切替 | ★★ |
| 65 | カスタムプロバイダ | `Model` インターフェースを実装して独自プロバイダを作る | ★★★ |
| 66 | Bedrock Guardrails | ガードレール設定(NGトピック・単語フィルタ)と発動時の挙動 | ★★ |
| 67 | PII マスキング | ガードレール/フックで個人情報をマスクする | ★★★ |
| 68 | プロンプトインジェクション | ツール結果経由のインジェクションを試し、防御を実装 | ★★★ |
| 69 | ツール権限の最小化 | 許可リスト方式のツール制御(read-only モード等) | ★★ |
| 70 | 出力の制約 | structured output + バリデーションで安全な出力を保証 | ★★ |

## 第8章 観測性と評価(71〜80)

> 対応ドキュメント: Observability / Metrics / Traces / Evaluation

| No | タイトル | 学ぶこと | 難易度 |
|---|---|---|---|
| 71 | ロギング | `strands` ロガーの設定とデバッグログの読み方 | ★ |
| 72 | メトリクス取得 | `EventLoopMetrics`(トークン・レイテンシ・ツール呼び出し回数) | ★ |
| 73 | OTel トレース | OpenTelemetry を有効化してエージェントループを可視化 | ★★ |
| 74 | トレースの送信 | OTLP exporter で Langfuse / Jaeger 等にトレースを送る | ★★ |
| 75 | トレース属性 | `trace_attributes` でユーザーID等のカスタム属性を付与 | ★★ |
| 76 | LLM-as-a-Judge | 別エージェントに出力を採点させる評価器を作る | ★★★ |
| 77 | ツール選択の評価 | 「正しいツールを呼べたか」のテストケース集と自動評価 | ★★★ |
| 78 | 回帰テスト | プロンプト変更時に評価スイートを回す仕組み(pytest 統合) | ★★★ |
| 79 | コスト集計 | 会話ごとのトークン→コスト換算レポート | ★★ |
| 80 | CloudWatch 連携 | AWS 上での GenAI Observability ダッシュボード | ★★★ |

## 第9章 マルチエージェント(81〜90)

> 対応ドキュメント: Multi-agent — Agents as Tools / Swarm / Graph / Workflow / A2A

| No | タイトル | 学ぶこと | 難易度 |
|---|---|---|---|
| 81 | Agents as Tools | オーケストレーター + 専門エージェント(調査係・計算係)構成 | ★★ |
| 82 | Swarm 入門 | `Swarm` で自律的なハンドオフを観察 | ★★ |
| 83 | Swarm 制御 | entry point / handoff メッセージ / 終了条件のカスタマイズ | ★★★ |
| 84 | Graph 直列 | `GraphBuilder` でリサーチ→分析→執筆のパイプライン | ★★ |
| 85 | Graph 条件分岐 | 条件付きエッジで内容によりルートを変える | ★★★ |
| 86 | Graph 並列集約 | 並列ノード(複数の専門家)+集約ノード | ★★★ |
| 87 | Workflow ツール | `workflow` ツールでタスク依存関係つきの実行 | ★★ |
| 88 | A2A サーバ | 自分のエージェントを A2A プロトコルで公開する | ★★★ |
| 89 | A2A クライアント | リモート A2A エージェントを呼ぶ(Graph のノードにもしてみる) | ★★★ |
| 90 | マルチエージェント観測 | ネストしたトレースで multi-agent の動きを追う | ★★★ |

## 第10章 AgentCore デプロイと WebUI 統合(91〜100)

> 対応ドキュメント: Deploy to Bedrock AgentCore / AgentCore Gateway・Identity・Tools

| No | タイトル | 学ぶこと | 難易度 |
|---|---|---|---|
| 91 | Runtime 最小デプロイ | `BedrockAgentCoreApp` でエージェントを Runtime にデプロイ | ★★ |
| 92 | Runtime ストリーミング | Runtime 上からのストリーミング応答 | ★★ |
| 93 | AgentCore Gateway | 既存 API(Lambda / OpenAPI)を MCP ツール化して接続 | ★★★ |
| 94 | AgentCore Identity | OAuth で外部サービス(例: Google Calendar)に安全にアクセス | ★★★ |
| 95 | Code Interpreter | AgentCore Code Interpreter でコード実行ツールを使う | ★★ |
| 96 | Browser ツール | AgentCore Browser でWeb操作エージェント | ★★★ |
| 97 | WebUI から呼ぶ | TS(fetch)から `InvokeAgentRuntime` を呼ぶ最小チャットUI | ★★ |
| 98 | WebUI ストリーミング | SSE をパースしてトークン逐次表示 | ★★★ |
| 99 | WebUI セッション | `runtimeSessionId` の管理で会話継続できる UI | ★★ |
| 100 | 卒業制作 | 自分の課題を解くマルチエージェント+WebUI を一気通貫で構築 | ★★★ |

---

## リポジトリ構成案

```
.
├── agents/                 # Python (uv 管理)
│   ├── pyproject.toml
│   └── knocks/
│       ├── k001_hello_agent.py
│       ├── k002_persona.py
│       └── ...
├── webui/                  # TypeScript (Vite + React)。第10章まで出番なし
│   ├── package.json
│   └── src/
└── docs/
    ├── strands-agents-100-knocks.md   # このファイル
    └── handson/
        ├── chapter01.md               # 章ごとのハンズオン解説
        └── ...
```

- Python は `uv init` + `uv add strands-agents strands-agents-tools` で開始
- WebUI は TS 初学者向けに最小構成: Vite + React、状態管理ライブラリなし、テストは Vitest で「fetch のラッパー」と「SSE パーサ」だけテストする
- 第1〜9章は `uv run knocks/k0XX_*.py` でローカル完結。AWS 認証情報(Bedrock 呼び出し権限)だけ用意すれば OK
