# 第6章 ハンズオン: セッションとメモリ(ノック51〜60)

「覚える」には2種類ある:

1. **セッション**(51〜54) — 会話の**全文**を自動保存し、プロセスやサーバーを跨いで再開する
2. **メモリ**(55〜58) — 会話から**要点だけ**を取り出し、会話を跨いで引き継ぐ

最後に、マルチユーザー設計(59)と戦略の使い分け(60)で締める。
ノック54・59・60は AWS 不要(モックで動く)。

## ノック51: ファイルセッション

📄 `knocks/k051_file_session.py`

```python
agent = Agent(
    model=make_model(),
    session_manager=FileSessionManager(session_id="knock51", storage_dir="/tmp/knock-sessions"),
)
```

**観察ポイント**

- ノック40で手作りした保存・復元が、引数1つで全自動になる
- 保存される構造: `session.json` / `agents/<id>/agent.json` / `messages/message_N.json`。
  覗くと「何が保存されているか」が具体的に分かる
- `agent.state` も保存対象。ただし**ターン終了時に同期**されるので、
  最後の呼び出しの後に set した値は保存されないことに注意

## ノック52: プロセス再起動テスト

📄 `knocks/k052_session_restart.py` — **2回実行する**ノック

**観察ポイント**

- 1回目は名前を教えて終了。2回目の起動でプロセスは別物なのに会話が続く
- `Agent` 生成時に session_id のデータが自動ロードされる(`agent.messages` が最初から埋まっている)
- リセットは保存ディレクトリを消すだけ

## ノック53: S3 セッション

📄 `knocks/k053_s3_session.py`(要 S3 バケット)

**観察ポイント**

- 変わるのは `FileSessionManager` → `S3SessionManager` の1箇所だけ
- 意味は大きい: **どのサーバー/コンテナからでも同じ会話を継続できる**。
  AgentCore Runtime(第10章)のようなステートレス実行環境で会話を持続させる基本形

## ノック54: 自作リポジトリ(AWS 不要)

📄 `knocks/k054_sqlite_repository.py`

`SessionRepository` の9メソッド(session/agent/message × create/read/update 系)を
SQLite で実装し、`RepositorySessionManager` に渡す。

**観察ポイント**

- File も S3 も同じインターフェースの実装に過ぎない。DynamoDB でも Redis でも同じ要領
- ハマりどころ: **Strands は同期呼び出しでも内部でワーカースレッドを使う**ので、
  `sqlite3.connect(..., check_same_thread=False)` が必要(テストで実際に踏んで修正した)

## ノック55: メモリツール

📄 `knocks/k055_memory_tool.py`

ここから「メモリ」編。`remember` / `recall` という最小のメモ帳ツールを自作し、
**エージェント自身に「何を覚えるべきか」を判断させる**。

**観察ポイント**

- 会話1で「エビアレルギー」が `remember` される(システムプロンプトで促している)
- 会話2は**履歴ゼロの新しいエージェント**なのに、`recall` で思い出して提案を変える
- セッションとの本質的な違い: 会話全文ではなく**要点だけ**が残る = 次の会話に
  持ち込むトークンが少ない
- 本格版はコミュニティツールの `memory`(Bedrock KB)や `mem0_memory`(セマンティック検索)

## ノック56: AgentCore Memory 短期(要 AWS リソース)

📄 `knocks/k056_agentcore_memory_short.py`

ノック55の自作メモ帳のマネージド版。`AgentCoreMemoryToolProvider` が
record/retrieve 系ツール一式を提供する。

**観察ポイント**

- `memory_id`(リソース)/ `actor_id`(誰の記憶)/ `session_id`(どの会話)/
  `namespace`(検索の名前空間)という4層の識別子で記憶が整理される
- 短期メモリは「会話の生イベント」をサービス側に記録するもの

## ノック57: AgentCore Memory 長期(要 AWS リソース)

📄 `knocks/k057_agentcore_memory_long.py`

長期メモリは、生イベントから嗜好・事実を**サービス側が自動抽出**する。

**観察ポイント**

- セッションA で「辛いもの好き・パクチー苦手」と話す → 抽出には少し時間がかかる →
  **完全に別のセッションB** で夕食を聞くと、嗜好を踏まえた提案になる
- ノック55で手作りした「会話から事実を抽出して保存」を、メモリ戦略
  (userPreferenceMemoryStrategy 等)としてマネージドにやってくれる

## ノック58: パーソナライズ

📄 `knocks/k058_personalize.py`(ノック55の後に実行)

記憶の使い方のもう1つの定石: **会話開始時にシステムプロンプトへ焼き込む**。

**観察ポイント**

- ツール方式(55〜57)との使い分け:
  - 記憶が少ない/毎回使う → **焼き込み**(ツール往復ゼロ、最初の応答から効く)
  - 記憶が大量 → **ツールで都度検索**(コンテキスト節約)
- 実務では両方使う: プロフィール要約は焼き込み、詳細はツール検索

## ノック59: マルチユーザー分離(AWS 不要)

📄 `knocks/k059_multi_user.py`

WebUI バックエンドの形を先取りする重要ノック。

```python
def agent_for(user_id, conversation_id, model):
    return Agent(model=model, session_manager=FileSessionManager(
        session_id=f"{user_id}--{conversation_id}", storage_dir=STORAGE))
```

**観察ポイント**

- **エージェントは毎リクエスト作り直してよい**(生成は安い)。会話の実体は
  ストレージにあるので何も失われない — これがステートレスなバックエンドの基本形
- session_id は `user_id × conversation_id`。アリスの履歴にボブの発言は混ざらない
  (テストで「釣り」がアリスの履歴に**ない**ことまで検証している)
- 第10章の WebUI はこの関数の model を実モデルに、呼び出し元を FastAPI/Runtime にしたもの

## ノック60: 記憶戦略の比較(AWS 不要)

📄 `knocks/k060_memory_strategies.py`

| 戦略 | 実装 | 残るもの | コスト | 向き |
|---|---|---|---|---|
| 全部保存 | SessionManager(51〜54) | 会話の全文 | 高い | 同一会話の継続 |
| 要約 | SummarizingManager(33) | 圧縮した文章 | 中 | 長い1会話 |
| 抽出 | メモリツール(55〜57)/本ノック | 構造化された事実 | 低い | 会話を跨ぐ記憶 |

仕上げに「会話の終わりに `save_fact` で要点だけ取り出す」抽出フローを実装する。

**観察ポイント**

- 抽出フェーズで雑談(今日は暑い)は保存されない — 「何が長期的に有用か」の判断も
  モデルの仕事にできる
- 実務は併用が基本: **会話中はセッション、会話を跨ぐ事実は抽出メモリ**

---

## この章のテスト

`tests/test_chapter06.py`(全部 AWS 不要、計 45 passed)。見どころ:

- セッションの再起動テスト — 同じ session_id で新しい Agent を作ると messages と state が
  復元されること、**別の session_id とは混ざらない**ことを検証
- SQLite リポジトリの往復テスト — 自作リポジトリ経由で保存→復元
- マルチユーザー分離 — アリスの履歴にボブの発言が含まれないこと(漏洩がないこと)を検証
- 抽出戦略 — 雑談が抽出されず、profile/constraint の2件だけ残ることを検証

## 第6章のまとめ

- セッション = 会話全文の自動永続化。`session_manager` を渡すだけ。File / S3 / 自作リポジトリ
- エージェントは使い捨て、会話はストレージに — ステートレスなバックエンドの基本形
- メモリ = 要点の抽出と再利用。自作ツール → AgentCore Memory(短期=生ログ、長期=自動抽出)
- 記憶の注入は「ツールで都度」と「プロンプトに焼き込み」の2方式
- session_id は `user × conversation` で分離。これが第10章の WebUI の土台

次章(第7章)はモデルプロバイダと安全性。Bedrock 以外のモデルへの差し替えと、
ガードレール・インジェクション対策を扱う。
