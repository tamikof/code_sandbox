"""ノック91: Runtime 最小デプロイ — BedrockAgentCoreApp でエージェントを公開

ここまではローカルで agent(...) を呼んできた。AgentCore Runtime は、
このエージェントを「HTTP で叩けるマネージドなサーバ」にしてくれる。
やることは @app.entrypoint でハンドラを1つ書くだけ。

ローカル確認:
  uv run knocks/k091_agentcore_deploy.py   # http://localhost:8080 で起動
  curl -X POST http://localhost:8080/invocations \\
    -H 'Content-Type: application/json' -d '{"prompt": "こんにちは"}'

本番デプロイ(agentcore CLI を使う):
  uv add bedrock-agentcore-starter-toolkit
  agentcore configure --entrypoint knocks/k091_agentcore_deploy.py
  agentcore launch    # コンテナ化 → ECR → Runtime へデプロイ
"""

from common import make_model

from strands import Agent
from bedrock_agentcore.runtime import BedrockAgentCoreApp

app = BedrockAgentCoreApp()

# エージェントはモジュールロード時に1度だけ作る(リクエストごとに作らない)
agent = Agent(
    model=make_model(),
    system_prompt="あなたは親切なアシスタントです。簡潔に答えてください。",
)


@app.entrypoint
def invoke(payload: dict) -> dict:
    """Runtime のエントリポイント。payload はリクエストの JSON。"""
    user_message = payload.get("prompt", "")
    result = agent(user_message)
    # 戻り値の dict がそのまま JSON レスポンスになる
    return {"result": str(result)}


if __name__ == "__main__":
    # ローカルでは開発サーバとして起動(本番は agentcore launch がこれを担う)
    app.run()
