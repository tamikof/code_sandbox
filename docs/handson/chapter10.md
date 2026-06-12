# 第10章 ハンズオン: AgentCore デプロイと WebUI 統合(ノック91〜100)

最終章。ここまでローカルで `agent(...)` と呼んできたエージェントを、
**本番(AgentCore Runtime)にデプロイ**し、**ブラウザ(TypeScript の WebUI)から呼ぶ**。

この章は2つの世界にまたがる:

- **ノック91〜96**: Python / AgentCore(Runtime デプロイ、Gateway、Identity、サンドボックスツール)
- **ノック97〜100**: TypeScript / WebUI(`webui/` ディレクトリ)

AgentCore 系(91〜96)の実行には AWS 環境が要るが、コードの「形」はこの章で確認できる。
WebUI 系(97〜100)は **AWS なしでテストまで完結**する(`cd webui && npm test`)。

## ノック91: Runtime 最小デプロイ

📄 `knocks/k091_agentcore_deploy.py`

```python
app = BedrockAgentCoreApp()
agent = Agent(model=make_model(), system_prompt="...")

@app.entrypoint
def invoke(payload: dict) -> dict:
    return {"result": str(agent(payload.get("prompt", "")))}
```

**観察ポイント**

- ローカルエージェントを HTTP サーバにするのに必要なのは `@app.entrypoint` の1関数だけ
- `app.run()` でローカル起動(`localhost:8080`)。`curl -X POST /invocations` で叩ける
- 本番化は `agentcore configure` → `agentcore launch`(コンテナ化 → ECR → Runtime)
- **エージェントはモジュールロード時に1度だけ作る**(リクエストごとに作らない)のが定石

## ノック92: Runtime ストリーミング

📄 `knocks/k092_agentcore_streaming.py`

```python
@app.entrypoint
async def invoke(payload: dict):
    async for event in agent.stream_async(payload.get("prompt", "")):
        if "data" in event:
            yield {"type": "text", "content": event["data"]}
    yield {"type": "done"}
```

**観察ポイント**

- entrypoint を **async generator** にして yield すると、Runtime が SSE で配信する
- 中身は第5章の `stream_async`(ノック41)そのもの。**WebUI が繋ぐのはこのサーバ**
- これがチャットUIの「タイプされていく」体験を支える

## ノック93: AgentCore Gateway

📄 `knocks/k093_agentcore_gateway.py`(要 Gateway)

既存の REST API / Lambda を MCP ツールに変える。

**観察ポイント**

- エージェント側のコードは第3章の MCP 接続(ノック27)に認証ヘッダを足すだけ
- 既存 API を**1行も書き換えず**にエージェントから使える。認証・スキーマ変換・
  スケーリングは Gateway がマネージドで担う

## ノック94: AgentCore Identity

📄 `knocks/k094_agentcore_identity.py`(要 Identity 設定)

エージェントがユーザーの代わりに Google / Slack 等を操作するための OAuth 管理。

```python
@tool
@requires_access_token(provider_name="google-calendar", scopes=[...])
async def list_events(access_token: str) -> str:
    ...  # access_token は Identity が用意(取得・更新を自動化)
```

**観察ポイント**

- コードに API キーや refresh token が**一切現れない**(第7章の安全性の延長)
- ユーザーごとに異なるトークンを安全に使い分け(第6章のマルチユーザーの延長)

## ノック95: Code Interpreter

📄 `knocks/k095_code_interpreter.py`(要 AgentCore 権限)

エージェントにコードを**実行**させる。第2章の `python_repl` の安全版。

**観察ポイント**

- 隔離されたマネージドサンドボックスで実行 ── 無限ループや危険な操作がホストに及ばない
- データ分析・計算・グラフ生成を「コードを書いて実行して結果を見て答える」で解ける

## ノック96: Browser ツール

📄 `knocks/k096_browser_tool.py`(要 AgentCore 権限 + Playwright)

マネージドなヘッドレスブラウザで、API のない Web サービスを操作する。

**観察ポイント**

- ログインが要るサイトやフォーム入力も「人間のように」操作できる
- 強力なぶん危険も大きい ── 第5章の承認フロー・第7章の権限最小化と必ず併用

---

## WebUI 編(ノック97〜100)── `webui/` ディレクトリ

ここから TypeScript。**初学者向けに意図的に最小構成**にしてある:
Vite + React + fetch のみ。状態管理ライブラリなし。テストは Vitest で
「壊れたら困るロジックだけ」を対象にする。

設計の肝は**ロジックを `.tsx` から切り離すこと**:

```
webui/src/
├── sseParser.ts     # SSE→イベント変換(純粋クラス、ノック98)
├── agentClient.ts   # Runtime を叩く(ノック97・99)
├── App.tsx          # 表示だけ
└── __tests__/       # sseParser と agentClient のテスト
```

```bash
cd webui
npm install
npm test     # 10 tests、ネットワーク不要
npm run dev  # http://localhost:5173
```

## ノック97: WebUI から呼ぶ

📄 `webui/src/agentClient.ts` + `knocks/k097_webui_invoke.py`(繋ぎ方ガイド)

```typescript
const response = await fetch(`${endpoint}/invocations`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ prompt }),
});
```

**観察ポイント**

- ローカルでは `localhost:8080`(ノック92のサーバ)をそのまま叩ける。本番は
  InvokeAgentRuntime の URL + SigV4 署名に変えるだけ
- テスト(`agentClient.test.ts`)は **fetch をモック**して、リクエストの組み立てを
  ネットワークなしで検証する

## ノック98: WebUI ストリーミング

📄 `webui/src/sseParser.ts`

**この章で一番テストの価値が高い所。** fetch のレスポンスはチャンク単位で届くので、
SSE イベントが**境界で途切れる**。バッファに溜めて `\n\n` 区切りで完全なイベントだけ
切り出すパーサを書く。

```typescript
push(chunk: string): AgentEvent[] {
  this.buffer += chunk;
  // \n\n で区切れた完全なイベントだけ取り出し、残りはバッファに残す
}
```

**観察ポイント**

- テストの主役は「`data: {"type":"text","con` で切れて、次のチャンクで `tent":...}` が来る」
  ケース。ここがストリーミング UI で最もバグる箇所
- 純粋クラスなので React なしでテストできる ── だからこそ `.tsx` から切り離した

## ノック99: WebUI セッション

📄 `webui/src/agentClient.ts`(`sessionId`)+ `App.tsx`(`useRef`)

```typescript
headers: {
  "X-Amzn-Bedrock-AgentCore-Runtime-Session-Id": sessionId,
}
```

**観察ポイント**

- セッションIDをヘッダに乗せると Runtime 側で会話が継続する(第6章のセッションの WebUI 版)
- `App.tsx` では `useRef(newSessionId())` でブラウザ滞在中ずっと同じIDを保持
- テストでヘッダにIDが乗ることを検証している

## ノック100: 卒業制作

📄 自由課題

ここまでの集大成。テーマ例:

- **第9章 × 第10章**: マルチエージェント(Graph/Swarm)を Runtime にデプロイし、WebUI から呼ぶ
- **第6章 × 第10章**: ユーザーごとのセッション + メモリで「あなた専用アシスタント」
- **第3章 × 第9章 × 第10章**: 複数 MCP + 専門エージェント + WebUI の実用ツール

チェックリスト:

- [ ] エージェントは Runtime にデプロイされ、HTTP で叩ける(91・92)
- [ ] WebUI からストリーミングで応答が表示される(97・98)
- [ ] 会話が継続する(99)+ ユーザーが分離されている(第6章)
- [ ] 危険な操作に安全装置がある(第5・7章)
- [ ] メトリクス/トレースで動きが見える(第8章)
- [ ] ロジックにテストがある(各章のテスト方針)

---

## この章のテスト

`webui/` で `npm test` → **10 passed**(AWS・ネットワーク不要)。Python 側は引き続き
`agents/` で `uv run pytest` → 68 passed。見どころ:

- **SSE パーサ** — チャンク境界でイベントが途切れて結合されるケースを検証(ストリーミングの肝)
- **AgentClient** — fetch をモックして、ストリーム読み取り・セッションヘッダ・エラー処理を検証

## 第10章のまとめ

- デプロイは `@app.entrypoint` の1関数 + `agentcore launch`。ストリーミングは async generator
- Gateway(既存API→MCP)/ Identity(OAuth管理)/ Code Interpreter・Browser(サンドボックスツール)で
  本番エージェントを拡張する
- WebUI はロジック(`.ts`)と表示(`.tsx`)を分離。テストはロジックだけに集中
- SSE のチャンク境界がストリーミング UI の最重要ポイント。ここを純粋関数にしてテストする
- セッションIDで会話継続、ユーザー分離は第6章の延長

---

## 100本、完走

全10章を通して、Strands Agents を「最小のエージェント」から「本番デプロイ + WebUI」まで
一周した。各章は前章の上に積み上がっている:

ツール(2・3)→ 文脈管理(4)→ イベント介入(5)→ 永続化(6)→ 安全性(7)→
観測(8)→ 協調(9)→ デプロイ(10)。

ここからは卒業制作(ノック100)で、自分の課題を解くエージェントを作るのが次の一歩。
