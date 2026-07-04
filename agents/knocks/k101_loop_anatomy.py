"""ノック101: ループの解剖 — stop_reason でループの止まり方を全分類する

エージェント = 観察→行動→観察 の反復ループ。第1章 ノック10 で cycle_count と
stop_reason に触れたが、ここでは「ループがどう止まるか」を体系的に並べる。
ループエンジニアリングの出発点は「なぜ止まったか」を区別できること。

  end_turn            : モデルが「もう話すことはない」と判断(正常終了)
  max_tokens          : 1回の出力が max_tokens に達した(出力の頭打ち)
  tool_use            : ツールを呼ぶために一旦停止(ループはこの後も続く)
  limit_turns         : Limits(turns=) の反復上限に達した(ノック102)
  limit_total_tokens  : Limits(total_tokens=) の予算上限に達した(ノック103)

このノックは AWS 不要(モックモデルで動く)。
実行: uv run knocks/k101_loop_anatomy.py
"""

from mock_model import MockModel, ToolCall

from strands import Agent, tool
from strands.types.agent import Limits


@tool
def noop(n: int) -> str:
    """何もしないダミーツール(ループを進めるためだけ)。"""
    return f"tick {n}"


class ForeverModel(MockModel):
    """毎ターン必ずツールを呼ぶ = 自力では止まらないモデル。"""

    async def stream(self, messages, tool_specs=None, system_prompt=None, **kw):
        turn = sum(1 for m in messages if m["role"] == "assistant") + 1
        inner = MockModel([ToolCall("noop", {"n": turn})])
        async for event in inner.stream(messages, tool_specs, system_prompt, **kw):
            yield event


if __name__ == "__main__":
    print("===== 正常終了(end_turn) =====")
    r = Agent(model=MockModel(["こんにちは!"]), callback_handler=None)("やあ")
    print(f"stop_reason={r.stop_reason} / cycles={r.metrics.cycle_count}")

    print("\n===== 反復上限で停止(limit_turns) =====")
    agent = Agent(model=ForeverModel([]), tools=[noop], callback_handler=None)
    r = agent("ずっと回して", limits=Limits(turns=3))
    print(f"stop_reason={r.stop_reason} / cycles={r.metrics.cycle_count}")

    print("\n===== 予算上限で停止(limit_total_tokens) =====")
    agent2 = Agent(model=ForeverModel([]), tools=[noop], callback_handler=None)
    r = agent2("ずっと回して", limits=Limits(total_tokens=40))
    print(f"stop_reason={r.stop_reason} / cycles={r.metrics.cycle_count}")

    print(
        "\nポイント: stop_reason を見れば『タスクが終わった』のか"
        "『ハーネスが止めた』のかを区別できる。この区別が、止まった後の"
        "振る舞い(再開する? 報告する? 人間に聞く?)を決める(ノック102 以降)。"
    )
