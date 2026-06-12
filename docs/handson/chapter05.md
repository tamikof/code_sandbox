# 第5章 ハンズオン: ストリーミングとフック(ノック41〜50)

この章のテーマは「エージェントの動きをイベントとして扱う」こと。前半(41〜44)は
**観察** — ストリームに流れるイベントを受けて表示を作る。後半(45〜50)は
**介入** — フックで節目に処理を差し込み、検証・拒否・書き換え・承認を実装する。

WebUI(第10章)は前半の技術で動き、本番の安全装置(第7章)は後半の技術で作る。
この章が実質的に後半戦全体の土台になる。

## ノック41: ストリーミング基礎

📄 `knocks/k041_streaming_basics.py`

```python
async for event in agent.stream_async("..."):
    if "data" in event:
        print(event["data"], end="", flush=True)
```

**観察ポイント**

- `"data"` イベントにテキストの断片(デルタ)が入る。`flush=True` を忘れると体感が台無し
- `callback_handler=None` にしている理由: デフォルトハンドラも print するので二重表示になる

## ノック42: コールバックハンドラ

📄 `knocks/k042_callback_handler.py`

ノック1から応答が「勝手に」表示されていた種明かし。デフォルトの
`PrintingCallbackHandler` を自作関数に差し替える。

**使い分け**

| | callback_handler | stream_async |
|---|---|---|
| ループを握るのは | Strands 側 | 呼び出し側 |
| 同期呼び出し | 動く | — |
| 向いている用途 | CLI 表示・ログ | WebUI バックエンド・SSE 中継 |

## ノック43: イベントの分類

📄 `knocks/k043_event_types.py`

ストリームには text delta 以外も流れている。仕分けてタイムライン表示する。

**観察ポイント**

- 主なイベント: `init_event_loop` → `start_event_loop` → (`current_tool_use` →
  `message`)×N → `data`... → `result`
- `current_tool_use` はツール引数が**組み立てられていく途中**から流れ始める
  (input が徐々に埋まっていく)。「ツールを使おうとしている」を最速で検知できる
- `result` イベントには最終的な `AgentResult` がまるごと入っている

## ノック44: 進捗UIの素振り

📄 `knocks/k044_progress_ui.py`

「ツール実行中は ⏳ を出し、テキストが来たら ✔ に切り替える」をイベント駆動で実装。

**観察ポイント**

- 状態機械はたった1変数(`tool_running`)。イベントの種類が状態遷移のトリガー
- この構造をそのまま SSE → React に移植したものが第10章の WebUI になる

## ノック45: ライフサイクルフック

📄 `knocks/k045_lifecycle_hooks.py`

ここから「介入」編。`HookProvider` を実装して Agent に渡す。

```python
class TimingLogger(HookProvider):
    def register_hooks(self, registry, **kwargs):
        registry.add_callback(BeforeInvocationEvent, self.on_before)
        registry.add_callback(AfterInvocationEvent, self.on_after)
```

**観察ポイント**

- フックは Agent に紐づき、**全呼び出しで自動発火**する(呼び出し側が何もしなくても)
- ストリーミングとの違い: イベントオブジェクトから `event.agent` に触れる =
  状態を読み書きできる。観察を超えた介入が可能
- まずはロギング・計測のような副作用の安全な用途から始めるのが鉄則

## ノック46: ツール呼び出しの検証

📄 `knocks/k046_tool_guard.py`

**この章で一番大事なノック。** モデルが組み立てたツール引数を実行前に検査する。

```python
def check(self, event: BeforeToolCallEvent):
    if path.startswith("/etc"):
        event.cancel_tool = "ポリシー違反: アクセス禁止"   # 拒否
    elif not path.startswith("/"):
        event.tool_use["input"]["path"] = f"/workspace/{path}"  # 書き換え
```

**観察ポイント**

- `event.cancel_tool = "理由"` でツールは実行されず、理由が `status: error` の
  結果としてモデルに返る → モデルは謝罪や代替案で続行する(落ちない)
- 引数の書き換えは `event.tool_use["input"]` を直接編集するだけ
- **「LLM の判断を信用しない最後の砦」はプロンプトではなくコードで作る**。
  プロンプトで「/etc は読むな」と書いても破られうるが、フックは破れない

## ノック47: ツール結果の加工

📄 `knocks/k047_tool_audit.py`

実行**後**の介入。`AfterToolCallEvent` で監査ログを取り、`event.result` を編集して
電話番号をマスクしてからモデルに渡す。

**観察ポイント**

- モデルはマスク済みデータしか見ていないので、**応答にも履歴にも生の電話番号が残らない**。
  「モデルに見せない」ことがそのまま漏洩対策になる(第7章の PII 対策の原型)
- 監査ログには `tool / input / status` を記録。「誰が何をしたか」を答えられる状態にする

## ノック48: メッセージへの介入

📄 `knocks/k048_message_hook.py`

`MessageAddedEvent` は履歴に1件追加されるたびに発火する。会話ログの外部保存・検査の入口。

**観察ポイント**

- 1回の `agent(...)` で user / assistant の最低2回発火する(ツールを使えばさらに増える)
- 第6章のセッションマネージャも、ほぼこの仕組みで「追加されたら保存」をやっている

## ノック49: 人間の承認フロー

📄 `knocks/k049_human_approval.py`

ノック46の応用で human-in-the-loop を作る。設計のポイントは**承認の取り方を注入可能にする**こと:

```python
ApprovalHook({"send_invoice"}, console_approver)   # ターミナルでは input()
ApprovalHook({"send_invoice"}, lambda n, a: False) # テストでは固定値
```

**観察ポイント**

- 危険なツール(請求書送付)だけ確認し、安全なツールは素通し
- `n` で拒否すると、モデルは「承認されなかった」事実を受け取って引き下がる
- WebUI では approver を「確認ダイアログに出して応答を待つ」実装に差し替えるだけ。
  コミュニティツールの `handoff_to_user` も同系統の仕組み

## ノック50: スナップショット(AWS 不要)

📄 `knocks/k050_snapshot.py`

新しめの機能 `take_snapshot()` / `load_snapshot()`。messages + state + 会話マネージャの
状態を1つに固めて保存し、いつでも巻き戻せる。

**観察ポイント**

- 「献立の提案が気に入らない → チェックポイントへ巻き戻して別案」という
  **会話の分岐・やり直し**が作れる
- ノック40(手作りの保存復元)→ ノック50(公式スナップショット)→ 第6章(セッション
  マネージャで自動化)という3段階の進化として理解する

---

## この章のテスト

`tests/test_chapter05.py`(全部 AWS 不要、計 39 passed)。見どころ:

- **ガードのテスト** — `/etc/passwd` 拒否(error + 理由)と相対パス正規化(success +
  書き換え後の引数で実行)の両方を検証
- **マスキングのテスト** — モデルに渡る toolResult に生の電話番号が**含まれない**ことを検証
- **承認フローのテスト** — approver を `lambda: False / True` に差し替えて両分岐を検証。
  「承認の取り方を注入可能にする」設計がそのままテスト容易性になっている好例

## 第5章のまとめ

- 観察は2系統: `stream_async`(呼び出し側がループを握る、WebUI 向き)と
  `callback_handler`(Agent に紐づく、CLI/ログ向き)
- 介入はフック: Before/After × Invocation/ToolCall/Model、+ MessageAdded
- `event.cancel_tool = "理由"` で拒否、`event.tool_use["input"]` で書き換え、
  `event.result` で結果の加工 — **安全装置はプロンプトでなくコードで作る**
- 承認(human-in-the-loop)は「approver を注入できるフック」として作るとテストも UI 差し替えも楽
- スナップショットで会話の巻き戻し・分岐ができる

次章(第6章)はセッションとメモリ。ノック40・50でやった保存・復元を自動化し、
プロセスやマシンを跨いで会話を継続する。
