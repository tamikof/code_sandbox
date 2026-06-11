"""第2章の概念のテスト: ツール実行を含むエージェントループを MockModel で検証する。"""

from mock_model import MockModel, ToolCall

from strands import Agent, tool


@tool
def add(a: int, b: int) -> int:
    """2つの数を足し算する。"""
    return a + b


@tool
def fail_tool() -> str:
    """必ず失敗するツール。"""
    raise RuntimeError("わざと失敗")


def test_tool_loop_executes_tool():
    """モデルが tool_use を返す → ツールが実行され、結果が履歴に入り、ループが2周する。"""
    agent = Agent(
        model=MockModel([ToolCall("add", {"a": 2, "b": 3}), "答えは5です"]),
        tools=[add],
        callback_handler=None,
    )
    result = agent("2+3は?")

    assert str(result).strip() == "答えは5です"
    assert result.metrics.cycle_count == 2  # ツール実行でループが1周増える

    tool_results = [
        block["toolResult"]
        for message in agent.messages
        for block in message["content"]
        if "toolResult" in block
    ]
    assert len(tool_results) == 1
    assert tool_results[0]["status"] == "success"
    assert tool_results[0]["content"] == [{"text": "5"}]


def test_tool_error_returns_error_result():
    """ツール内の例外は status=error の toolResult になり、エージェントは続行できる(ノック14)。"""
    agent = Agent(
        model=MockModel([ToolCall("fail_tool", {}), "ツールが失敗したようです"]),
        tools=[fail_tool],
        callback_handler=None,
    )
    result = agent("実行して")

    tool_results = [
        block["toolResult"]
        for message in agent.messages
        for block in message["content"]
        if "toolResult" in block
    ]
    assert tool_results[0]["status"] == "error"
    assert "わざと失敗" in str(tool_results[0]["content"])
    assert str(result).strip() == "ツールが失敗したようです"


def test_tool_specs_sent_to_model():
    """登録したツールの仕様がモデルに渡っている。"""
    model = MockModel(["はい"])
    Agent(model=model, tools=[add], callback_handler=None)("こんにちは")
    spec_names = [spec["name"] for spec in model.calls[0]["tool_specs"]]
    assert spec_names == ["add"]
