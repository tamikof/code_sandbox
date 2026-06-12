"""ノック25: ストリーミングツール — yield で途中経過を返す

async generator のツールは、処理の途中経過を yield でストリームに流せる。
最後に yield した値がツールの最終結果としてモデルに渡る。
長時間かかるツールの進捗表示(WebUI で重要)の基礎。

実行: uv run knocks/k025_streaming_tool.py
"""

import asyncio

from common import make_model

from strands import Agent, tool


@tool
async def batch_convert(count: int):
    """ファイルを一括変換する(時間のかかるバッチ処理)。"""
    for i in range(1, count + 1):
        await asyncio.sleep(0.5)
        # 途中経過: ストリームイベントとして流れる(モデルには渡らない)
        yield f"変換中... {i}/{count}"
    # 最後の yield がツールの結果としてモデルに渡る
    yield f"{count}件のファイルを変換しました"


async def main() -> None:
    agent = Agent(model=make_model(), tools=[batch_convert])

    # stream_async でイベントを受けると、ツールの途中経過も拾える
    async for event in agent.stream_async("3件のファイルを変換して。"):
        if "data" in event:
            print(event["data"], end="", flush=True)
        elif "tool_stream_event" in event:
            chunk = event["tool_stream_event"].get("data")
            if isinstance(chunk, str):
                print(f"\n  [進捗] {chunk}", flush=True)
    print()


if __name__ == "__main__":
    asyncio.run(main())
