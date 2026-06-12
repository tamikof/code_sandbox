"""ノック97: WebUI から呼ぶ — 最小チャットUIのバックエンド側メモ

ノック97〜100 のメインは TypeScript(webui/)側にある。この Python ファイルは
「WebUI が何を叩くのか」を1枚にまとめたガイド。

【全体像】
  ブラウザ (webui/) ──HTTP POST /invocations──> AgentCore Runtime (k091/k092)
            <──SSE ストリーム───────────────

【ローカルでの繋ぎ方】
  1. このリポジトリの agents/ で Runtime をローカル起動:
       uv run knocks/k092_agentcore_streaming.py   # http://localhost:8080
  2. 別ターミナルで webui/ を起動:
       cd ../webui && npm install && npm run dev     # http://localhost:5173
  3. ブラウザで開いてチャット

【本番 (AgentCore Runtime) での繋ぎ方】
  - エンドポイントは InvokeAgentRuntime の URL になる
  - 認証は AWS SigV4 署名が必要(ローカルの localhost:8080 は署名不要)
  - webui/src/agentClient.ts の endpoint と、fetch のヘッダに署名を足す

WebUI 側の対応ファイル:
  webui/src/agentClient.ts  ← ノック97(リクエスト組み立て)・99(セッション)
  webui/src/sseParser.ts    ← ノック98(SSE パース)
  webui/src/App.tsx         ← 画面
"""

print(__doc__)
