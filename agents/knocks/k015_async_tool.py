"""ノック15: 非同期ツール — async def でツールを定義する

I/O 待ち(API 呼び出し・DB アクセス等)があるツールは async にすると、
複数ツールの並列実行(第3章のノック23)で真価を発揮する。

実行: uv run knocks/k015_async_tool.py
"""

import asyncio

from common import make_model

from strands import Agent, tool


@tool
async def slow_search(keyword: str) -> str:
    """データベースからキーワードを検索する(時間がかかる)。"""
    await asyncio.sleep(1)  # 重い I/O の代わり
    return f"「{keyword}」の検索結果: 3件ヒットしました(ダミー)"


if __name__ == "__main__":
    # 同期ツールと同じように渡すだけ。実行は Strands がイベントループで面倒を見る
    agent = Agent(model=make_model(), tools=[slow_search])
    agent("「寿司」を検索して。")
