"""ノック103: トークン予算で縛る — Limits(total_tokens=) でコストを止める

回数(ノック102)ではなく「使ったトークンの合計」で止めたい場面は多い。
1周が重いエージェント(長い履歴 + 大きなツール結果)では、回数が少なくても
コストが膨らむ。Limits(total_tokens=N) は入力+出力の累計が N を超えたら止め、
stop_reason を "limit_total_tokens" にする。

注意: トークン上限は「ソフトキャップ」。1回のモデル呼び出しの途中では止まらず、
周の境界でチェックされるので、多少オーバーすることがある。

このノックは AWS 不要(モックモデルで動く)。
実行: uv run knocks/k103_bounded_budget.py
"""

from mock_model import MockModel, ToolCall

from strands import Agent, tool
from strands.types.agent import Limits


@tool
def fetch(url: str) -> str:
    """URL を取得する(毎回そこそこトークンを消費する想定)。"""
    return f"{url} の内容(長め)"


class HungryModel(MockModel):
    """毎ターン fetch を呼び続けるモデル。MockModel は 1周 totalTokens=15。"""

    async def stream(self, messages, tool_specs=None, system_prompt=None, **kw):
        n = sum(1 for m in messages if m["role"] == "assistant") + 1
        inner = MockModel([ToolCall("fetch", {"url": f"http://x/{n}"})])
        async for event in inner.stream(messages, tool_specs, system_prompt, **kw):
            yield event


if __name__ == "__main__":
    agent = Agent(model=HungryModel([]), tools=[fetch], callback_handler=None)

    # 1周あたり totalTokens=15。上限 50 なら 4 周目で超える
    result = agent("全部集めて", limits=Limits(total_tokens=50))

    usage = result.metrics.accumulated_usage
    print(f"stop_reason : {result.stop_reason}")
    print(f"cycles      : {result.metrics.cycle_count}")
    print(f"使用トークン: {usage['totalTokens']}(上限50をソフトに超える)")

    print(
        "\nポイント: turns は『何周まで』、total_tokens は『いくらまで』。"
        "コストで止めたいなら total_tokens。回数と併用もできる。"
        "第8章のコスト換算(ノック79)と組み合わせれば『1回$0.05まで』のような"
        "金額ベースの上限も、トークン上限に翻訳して実装できる。"
    )
