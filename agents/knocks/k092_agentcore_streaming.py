"""ノック92: Runtime ストリーミング — Runtime からトークンを逐次返す

ノック91は完成した応答を1つの JSON で返した。チャット UI では
トークンを逐次返したい。entrypoint を async generator にして yield すると、
Runtime が SSE (Server-Sent Events) ストリームとして配信してくれる。

ローカル確認:
  uv run knocks/k092_agentcore_streaming.py
  curl -N -X POST http://localhost:8080/invocations \\
    -H 'Content-Type: application/json' -d '{"prompt": "俳句を詠んで"}'
  → data: ... が逐次流れてくる
"""

from common import make_model

from strands import Agent
from bedrock_agentcore.runtime import BedrockAgentCoreApp

app = BedrockAgentCoreApp()
agent = Agent(model=make_model(), callback_handler=None)


@app.entrypoint
async def invoke(payload: dict):
    """async generator で yield した値が SSE で配信される。"""
    user_message = payload.get("prompt", "")

    # 第5章の stream_async と同じ。テキストデルタだけを取り出して流す
    async for event in agent.stream_async(user_message):
        if "data" in event:
            yield {"type": "text", "content": event["data"]}
    yield {"type": "done"}


if __name__ == "__main__":
    app.run()
