"""ノック5: 非同期呼び出し — invoke_async と asyncio

2つのエージェントを並行に走らせて、直列実行との時間差を確認する。

実行: uv run knocks/k005_async.py
"""

import asyncio
import time

from strands import Agent


async def ask(name: str, prompt: str) -> str:
    # 並行実行時に出力が混ざらないよう callback_handler=None でストリーミング表示を切る
    agent = Agent(callback_handler=None)
    result = await agent.invoke_async(prompt)
    return f"[{name}]\n{result}"


async def main() -> None:
    start = time.perf_counter()
    # gather で2つの呼び出しを同時に開始する
    answers = await asyncio.gather(
        ask("和食担当", "肉じゃがの作り方を3ステップで"),
        ask("洋食担当", "カルボナーラの作り方を3ステップで"),
    )
    elapsed = time.perf_counter() - start

    for answer in answers:
        print(answer)
        print("-" * 40)
    print(f"並行実行の所要時間: {elapsed:.2f}秒")


asyncio.run(main())
