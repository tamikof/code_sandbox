# strands-knocks-webui

100本ノック第10章の WebUI。AgentCore Runtime(または `app.run()` のローカルサーバ)に
ブラウザから繋ぐ最小チャット。TypeScript 初学者向けに**意図的に最小構成**にしてある。

## 構成方針(なぜこの形か)

- **Vite + React + fetch のみ**。状態管理ライブラリ・UIライブラリ・ルーターなし
- ロジック(fetch / SSE パース)を `.tsx` から切り離し、純粋な `.ts` に置く
  → テストしやすく、React を知らなくても読める
- テストは Vitest で**ロジックだけ**を対象にする(画面の見た目はテストしない)

```
src/
├── sseParser.ts        # SSE を AgentEvent に変換する純粋クラス(ノック98)
├── agentClient.ts      # Runtime を叩いてイベントを yield する(ノック97・99)
├── App.tsx             # 表示だけの React コンポーネント
├── main.tsx            # エントリポイント
└── __tests__/
    ├── sseParser.test.ts
    └── agentClient.test.ts
```

## セットアップと実行

```bash
cd webui
npm install
npm test          # Vitest(ネットワーク不要、10 tests)
npm run dev       # 開発サーバ(http://localhost:5173)
```

## エージェントと繋ぐ

別ターミナルで Python 側のローカル Runtime を起動しておく:

```bash
cd ../agents
uv run knocks/k092_agentcore_streaming.py   # http://localhost:8080
```

`App.tsx` の `ENDPOINT` がこれを指している。`npm run dev` でブラウザを開けばチャットできる。

## なぜテストが2つだけなのか

UI(`App.tsx`)はブラウザと React に強く依存し、テストが重くなる割に壊れやすい。
代わりに、**壊れたら確実に困るロジック**だけをテストしている:

- `sseParser.test.ts` — チャンク境界でイベントが途切れるケース(SSE で一番バグる所)
- `agentClient.test.ts` — fetch をモックして、リクエスト組み立てとストリーム読み取りを検証

この「ロジックを純粋関数に逃がしてそこだけテストする」型は、TypeScript に限らず有効。
