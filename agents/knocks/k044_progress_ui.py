"""ノック44: 進捗UIの素振り — イベント駆動で表示を制御する

「考え中はテキストを流し、ツール実行中はスピナー風の行を出す」 ——
WebUI(第10章)でやることを、まずターミナルで素振りする。

実行: uv run knocks/k044_progress_ui.py
"""

import asyncio

from common import make_model

from strands import Agent, tool


@tool
async def search_db(keyword: str) -> str:
    """データベースを検索する(2秒かかる)。"""
    await asyncio.sleep(2)
    return f"「{keyword}」: 5件ヒット"


async def main() -> None:
    agent = Agent(model=make_model(), tools=[search_db], callback_handler=None)

    tool_running = None
    async for event in agent.stream_async("「味噌」をDBで検索して結果を一言でまとめて。"):
        if "current_tool_use" in event and event["current_tool_use"].get("name"):
            name = event["current_tool_use"]["name"]
            if name != tool_running:
                tool_running = name
                print(f"\n⏳ {name} を実行中...", flush=True)
        elif "data" in event:
            if tool_running:
                print("✔ ツール完了\n", flush=True)  # テキストが来た = ツールは終わった
                tool_running = None
            print(event["data"], end="", flush=True)
    print()


if __name__ == "__main__":
    asyncio.run(main())
