"""第2章のテスト: 各ノックのツールを LLM なしで検証する。

- ツール単体: @tool 付きの関数は普通の関数としても呼べる
- エージェントループ: MockModel でツール実行の配線を検証
"""

import asyncio

import shout
from k011_calculator import add, multiply
from k012_tool_spec import convert_temperature
from k013_multi_tools import get_weather
from k014_tool_errors import divide
from k015_async_tool import slow_search
from k016_tool_context import add_to_cart
from mock_model import MockModel, ToolCall

from strands import Agent


# ---- ツール単体テスト(ただの関数として呼ぶ) ----


def test_calculator_tools_direct():
    assert add(2, 3) == 5
    assert multiply(3, 4) == 12


def test_convert_temperature():
    assert convert_temperature(0, "celsius", "fahrenheit") == 32
    assert convert_temperature(212, "fahrenheit", "celsius") == 100
    assert convert_temperature(25, "celsius", "celsius") == 25


def test_tool_spec_generated_from_hints():
    """型ヒント・docstring がスキーマになる(ノック12)。"""
    spec = convert_temperature.tool_spec
    schema = spec["inputSchema"]["json"]
    assert spec["name"] == "convert_temperature"
    assert "温度を摂氏・華氏の間で変換する" in spec["description"]
    assert schema["required"] == ["value", "from_unit", "to_unit"]
    assert schema["properties"]["from_unit"]["enum"] == ["celsius", "fahrenheit"]
    assert "変換したい温度の値" in schema["properties"]["value"]["description"]


def test_get_weather_unknown_city():
    assert "ありません" in get_weather("京都")


def test_async_tool_direct():
    assert "寿司" in asyncio.run(slow_search("寿司"))


# ---- エージェントループテスト(MockModel) ----


def test_divide_error_becomes_error_result():
    """ゼロ除算の例外が status=error の toolResult になる(ノック14)。"""
    agent = Agent(
        model=MockModel([ToolCall("divide", {"a": 10, "b": 0}), "0では割れません"]),
        tools=[divide],
        callback_handler=None,
    )
    agent("10÷0は?")

    tool_results = [
        block["toolResult"]
        for message in agent.messages
        for block in message["content"]
        if "toolResult" in block
    ]
    assert tool_results[0]["status"] == "error"


def test_tool_context_writes_agent_state():
    """ToolContext 経由で agent.state に書き込める(ノック16)。"""
    agent = Agent(
        model=MockModel(
            [
                ToolCall("add_to_cart", {"item": "りんご"}, tool_use_id="t-1"),
                "追加しました",
            ]
        ),
        tools=[add_to_cart],
        callback_handler=None,
    )
    agent("りんごをカートに入れて")
    assert agent.state.get("cart") == ["りんご"]


def test_module_style_tool():
    """TOOL_SPEC + 関数のモジュールがツールとして動く(ノック17)。"""
    agent = Agent(
        model=MockModel([ToolCall("shout", {"text": "hello"}), "叫びました"]),
        tools=[shout],
        callback_handler=None,
    )
    agent("叫んで")

    tool_results = [
        block["toolResult"]
        for message in agent.messages
        for block in message["content"]
        if "toolResult" in block
    ]
    assert tool_results[0]["status"] == "success"
    assert tool_results[0]["content"] == [{"text": "HELLO!!!"}]
