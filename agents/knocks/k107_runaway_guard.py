"""ノック107: 暴走ガード — 同一アクションの反復を検出して止める

Limits(102・103)は「回数/予算」で止める外側の安全網。だが、上限内でも
「同じツールを同じ引数で何度も呼ぶ」空回りは起きる(前進していないループ)。
これはループ設計の第2原則「各周を意味あるものに」の違反であり、
回数上限より早く検知して止めたい。

第5章のフック(BeforeToolCallEvent)で、直近のツール呼び出しを記録し、
同一の (ツール名, 引数) が閾値回数を超えたらそのツールをキャンセルする。

このノックは AWS 不要(モックモデルで動く)。
実行: uv run knocks/k107_runaway_guard.py
"""

import json

from mock_model import MockModel, ToolCall

from strands import Agent, tool
from strands.hooks import BeforeToolCallEvent, HookProvider, HookRegistry


@tool
def lookup(key: str) -> str:
    """辞書を引く(存在しないキーは毎回同じ空振りになる)。"""
    data = {"apple": "りんご"}
    return data.get(key, "見つかりません")


class RepetitionGuard(HookProvider):
    """同一の (ツール名, 引数) が threshold 回を超えたら止めるフック。"""

    def __init__(self, threshold: int = 2):
        self.threshold = threshold
        self.counts: dict[str, int] = {}

    def register_hooks(self, registry: HookRegistry, **kwargs) -> None:
        registry.add_callback(BeforeToolCallEvent, self.check)

    def check(self, event: BeforeToolCallEvent) -> None:
        # 呼び出しの指紋 = ツール名 + 引数
        fingerprint = (
            event.tool_use["name"]
            + json.dumps(event.tool_use["input"], sort_keys=True, ensure_ascii=False)
        )
        self.counts[fingerprint] = self.counts.get(fingerprint, 0) + 1
        if self.counts[fingerprint] > self.threshold:
            event.cancel_tool = (
                f"同じ操作({event.tool_use['name']})を{self.threshold}回超えて"
                "繰り返しています。別の方法を試すか、できないと報告してください。"
            )
            print(f"[guard] 反復を検出して停止: {fingerprint}")


class StubbornModel(MockModel):
    """学習せず、同じキーで lookup を呼び続けるモデル(空回り)。"""

    async def stream(self, messages, tool_specs=None, system_prompt=None, **kw):
        # 直近に guard の error が返っていたら諦めてテキストを返す
        last = messages[-1]
        gave_up = any(
            "繰り返しています" in b.get("toolResult", {}).get("content", [{}])[0].get("text", "")
            for b in last["content"]
            if isinstance(b, dict) and "toolResult" in b
        )
        script = ["諦めます。banana は辞書にありませんでした。"] if gave_up else [ToolCall("lookup", {"key": "banana"})]
        async for event in MockModel(script).stream(messages, tool_specs, system_prompt, **kw):
            yield event


if __name__ == "__main__":
    guard = RepetitionGuard(threshold=2)
    agent = Agent(
        model=StubbornModel([]),
        tools=[lookup],
        hooks=[guard],
        callback_handler=None,
    )

    result = agent("banana の意味を lookup で調べて", limits={"turns": 10})
    print(f"\n最終応答: {result}")
    print(f"stop_reason: {result.stop_reason}")

    print(
        "\nポイント: Limits(turns=10)まで回る前に、guard が3回目の同一呼び出しで止めた。"
        "『有界』(102)と『前進しているか』(107)は別の安全網 — 両方を掛ける。"
        "外側=回数/予算の絶対上限、内側=空回りの早期検出、の二重化が定石。"
    )
