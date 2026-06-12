"""ノック24: 直列ツール実行 — SequentialToolExecutor との比較

並列実行が困るケースもある: 同じリソースを触るツール、順序依存がある操作、
レート制限のある API など。SequentialToolExecutor は1つずつ順番に実行する。

実行: uv run knocks/k024_sequential_tools.py
"""

import asyncio
import time

from common import make_model
from k023_concurrent_tools import check_traffic, check_weather

from strands import Agent
from strands.tools.executors import SequentialToolExecutor

if __name__ == "__main__":
    agent = Agent(
        model=make_model(),
        tools=[check_weather, check_traffic],
        tool_executor=SequentialToolExecutor(),
    )

    start = time.perf_counter()
    agent("東京の天気と交通情報を両方、ツールを同時に使って調べて。")
    print(f"\n所要時間: {time.perf_counter() - start:.1f}秒")
    # ノック23と同じプロンプトでも、ツール実行が直列なので約2秒+モデル時間かかる
