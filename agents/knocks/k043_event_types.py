"""ノック43: イベントの分類 — ストリームに流れる全イベントを仕分ける

stream_async には text delta 以外にも多くのイベントが流れている。
ライフサイクル(ループ開始)、ツール組み立て、メッセージ確定、最終結果 ——
種類ごとに仕分けてタイムラインとして観察する。

実行: uv run knocks/k043_event_types.py
"""

import asyncio

from common import make_model

from strands import Agent, tool


@tool
def lookup_price(item: str) -> str:
    """商品の価格を調べる。"""
    return f"{item}: 480円"


async def main() -> None:
    agent = Agent(model=make_model(), tools=[lookup_price], callback_handler=None)

    text_chars = 0
    async for event in agent.stream_async("おにぎりの価格を調べて一言コメントして。"):
        if "init_event_loop" in event:
            print("⏱  ループ初期化")
        elif "start_event_loop" in event:
            print("▶  ループ開始(サイクル)")
        elif "current_tool_use" in event and event["current_tool_use"].get("name"):
            tool_use = event["current_tool_use"]
            print(f"🔧 ツール入力を組み立て中: {tool_use['name']} {tool_use.get('input', '')}")
        elif "message" in event:
            print(f"✉  メッセージ確定: role={event['message']['role']}")
        elif "data" in event:
            text_chars += len(event["data"])  # テキストは量だけ数える
        elif "result" in event:
            print(f"✅ 最終結果: stop_reason={event['result'].stop_reason}")

    print(f"(テキストデルタ合計: {text_chars}文字)")


if __name__ == "__main__":
    asyncio.run(main())
