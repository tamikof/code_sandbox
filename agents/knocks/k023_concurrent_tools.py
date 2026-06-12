"""ノック23: 並列ツール実行 — ConcurrentToolExecutor

モデルが1ターンで複数のツールを呼んだとき、デフォルトでは並列に実行される。
async ツール(ノック15)と組み合わせると I/O 待ちが重なって速くなる。

実行: uv run knocks/k023_concurrent_tools.py
"""

import asyncio
import time

from common import make_model

from strands import Agent, tool
from strands.tools.executors import ConcurrentToolExecutor


@tool
async def check_weather(city: str) -> str:
    """都市の天気を調べる(1秒かかる外部API想定)。"""
    await asyncio.sleep(1)
    return f"{city}: 晴れ"


@tool
async def check_traffic(city: str) -> str:
    """都市の交通情報を調べる(1秒かかる外部API想定)。"""
    await asyncio.sleep(1)
    return f"{city}: 渋滞なし"


if __name__ == "__main__":
    agent = Agent(
        model=make_model(),
        tools=[check_weather, check_traffic],
        tool_executor=ConcurrentToolExecutor(),  # デフォルトでもこれが使われる
    )

    start = time.perf_counter()
    agent("東京の天気と交通情報を両方、ツールを同時に使って調べて。")
    print(f"\n所要時間: {time.perf_counter() - start:.1f}秒")
    # 2つのツールが同一ターンで呼ばれれば、合計2秒ではなく約1秒+モデル時間で済む
