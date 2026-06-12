"""ノック41: ストリーミング基礎 — stream_async でトークン逐次表示

agent(...) は完了まで待つが、stream_async はイベントを逐次返す。
"data" イベントにテキストの断片(デルタ)が入る。

実行: uv run knocks/k041_streaming_basics.py
"""

import asyncio

from common import make_model

from strands import Agent


async def main() -> None:
    # ストリーミングは自前で表示するので、デフォルトの自動表示は切る
    agent = Agent(model=make_model(), callback_handler=None)

    async for event in agent.stream_async("味噌汁の作り方を3ステップで教えて。"):
        if "data" in event:
            # トークンの断片が届くたびに即表示(flush が大事)
            print(event["data"], end="", flush=True)
    print()


if __name__ == "__main__":
    asyncio.run(main())
