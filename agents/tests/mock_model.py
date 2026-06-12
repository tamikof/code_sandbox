"""テスト用のモックモデル。

Strands の Model インターフェースを実装した偽物のモデル。
あらかじめ決めた応答(テキスト or ツール呼び出し)を順番に返すので、
AWS 認証情報なし・コストゼロ・決定的にエージェントループをテストできる。

使い方:
    # テキストを返すだけ
    agent = Agent(model=MockModel(["こんにちは"]), callback_handler=None)

    # 1ターン目でツールを呼び、2ターン目で最終回答(エージェントループのテスト)
    agent = Agent(
        model=MockModel([ToolCall("add", {"a": 2, "b": 3}), "答えは5です"]),
        tools=[add],
        callback_handler=None,
    )
"""

import json
from dataclasses import dataclass
from typing import Any

from strands.models.model import Model


@dataclass
class ToolCall:
    """モックに「このツールをこの引数で呼べ」と指示するための応答指定。"""

    name: str
    input: dict[str, Any]
    tool_use_id: str = "mock-tool-use-1"

    def __post_init__(self):
        # 複数ツールを同一ターンで返すとき ID が重複しないように連番を振る
        if self.tool_use_id == "mock-tool-use-1":
            ToolCall._counter += 1
            self.tool_use_id = f"mock-tool-use-{ToolCall._counter}"


ToolCall._counter = 0


class MockModel(Model):
    """決め打ちの応答を順番に返すモデル。応答が尽きたら最後の応答を繰り返す。"""

    def __init__(self, responses: list[str | ToolCall]):
        self.responses = list(responses)
        self.calls: list[dict[str, Any]] = []  # 受け取ったリクエストの記録(検証用)
        self._index = 0

    def get_config(self) -> dict[str, Any]:
        return {"model_id": "mock"}

    def update_config(self, **kwargs: Any) -> None:
        pass

    async def structured_output(self, output_model, prompt, system_prompt=None, **kwargs):
        raise NotImplementedError("MockModel は structured_output 未対応")
        yield  # async generator にするためのダミー

    async def stream(self, messages, tool_specs=None, system_prompt=None, **kwargs):
        # 検証用に「モデルに何が渡されたか」を記録しておく
        self.calls.append(
            {
                "messages": messages,
                "tool_specs": tool_specs,
                "system_prompt": system_prompt,
            }
        )

        turn = self.responses[min(self._index, len(self.responses) - 1)]
        self._index += 1

        # 以下は Bedrock Converse API のストリームイベント形式
        yield {"messageStart": {"role": "assistant"}}
        if isinstance(turn, (ToolCall, list)):
            # ToolCall 単体 or リスト(1ターンで複数ツールを同時に呼ぶケース)
            tool_calls = [turn] if isinstance(turn, ToolCall) else turn
            for call in tool_calls:
                yield {
                    "contentBlockStart": {
                        "start": {"toolUse": {"toolUseId": call.tool_use_id, "name": call.name}}
                    }
                }
                yield {"contentBlockDelta": {"delta": {"toolUse": {"input": json.dumps(call.input)}}}}
                yield {"contentBlockStop": {}}
            yield {"messageStop": {"stopReason": "tool_use"}}
        else:
            yield {"contentBlockDelta": {"delta": {"text": turn}}}
            yield {"contentBlockStop": {}}
            yield {"messageStop": {"stopReason": "end_turn"}}
        yield {
            "metadata": {
                "usage": {"inputTokens": 10, "outputTokens": 5, "totalTokens": 15},
                "metrics": {"latencyMs": 1},
            }
        }
