"""ノック102: 反復回数で縛る — Limits(turns=) で暴走を有界化する

ループ設計の第1原則「有界であれ」。ツールを使うエージェントは、条件次第で
延々とループしうる(検索→検索→検索…)。Limits(turns=N) を渡すと、
N 周でループが止まり stop_reason が "limit_turns" になる。

重要な性質: 上限で止まっても agent.messages は「再開可能な状態」で残る。
だから「まず3周、様子を見て続きをもう3周」のような分割実行ができる。

このノックは AWS 不要(モックモデルで動く)。
実行: uv run knocks/k102_bounded_turns.py
"""

from mock_model import MockModel, ToolCall

from strands import Agent, tool
from strands.types.agent import Limits


@tool
def search(page: int) -> str:
    """検索結果の次のページを取得する(いくらでも続けられる)。"""
    return f"ページ{page}の結果"


class EndlessSearcher(MockModel):
    """満足せず次々に検索を続けるモデル(自力では止まらない)。"""

    async def stream(self, messages, tool_specs=None, system_prompt=None, **kw):
        page = sum(
            1
            for m in messages
            for b in m["content"]
            if isinstance(b, dict) and "toolResult" in b
        ) + 1
        inner = MockModel([ToolCall("search", {"page": page})])
        async for event in inner.stream(messages, tool_specs, system_prompt, **kw):
            yield event


if __name__ == "__main__":
    agent = Agent(model=EndlessSearcher([]), tools=[search], callback_handler=None)

    # --- まず3周だけ回す ---
    result = agent("すべての結果を集めて", limits=Limits(turns=3))
    print(f"1回目: stop_reason={result.stop_reason} / cycles={result.metrics.cycle_count}")
    print(f"       履歴 {len(agent.messages)}件(このまま再開できる)")

    # --- 続きをさらに2周(同じ agent を再呼び出し。ループの続きから) ---
    result = agent("続けて", limits=Limits(turns=2))
    print(f"2回目: stop_reason={result.stop_reason}")
    print(f"       累計 cycles={result.metrics.cycle_count}(agent 生涯の累計)")

    print(
        "\nポイント: limits を付けない同じコードは無限ループになりうる。"
        "『上限で止める → 状態を見て → 続けるか決める』が有界ループの基本形。"
        "turns は1呼び出しごとにリセットされる(累計ではない)。"
    )
