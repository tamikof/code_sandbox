"""第1章の概念のテスト: エージェントの基本動作を MockModel で検証する。"""

from mock_model import MockModel

from strands import Agent


def test_text_response():
    agent = Agent(model=MockModel(["こんにちは!"]), callback_handler=None)
    result = agent("やあ")
    assert str(result).strip() == "こんにちは!"
    assert result.stop_reason == "end_turn"


def test_messages_accumulate():
    """マルチターン会話で履歴が user / assistant 交互に積まれる(ノック6)。"""
    agent = Agent(model=MockModel(["1回目", "2回目"]), callback_handler=None)
    agent("最初の質問")
    agent("次の質問")
    assert [m["role"] for m in agent.messages] == ["user", "assistant", "user", "assistant"]
    assert "2回目" in str(agent.messages[-1])


def test_system_prompt_passed_to_model():
    """system_prompt は履歴ではなくモデルへのリクエストに毎回乗る(ノック2)。"""
    model = MockModel(["ほな、そうしまひょ"])
    agent = Agent(model=model, system_prompt="関西弁で話す", callback_handler=None)
    agent("こんにちは")
    assert model.calls[0]["system_prompt"] == "関西弁で話す"
    assert all(m["role"] != "system" for m in agent.messages)


def test_metrics_recorded():
    """AgentResult.metrics にトークン使用量が入る(ノック10)。"""
    agent = Agent(model=MockModel(["はい"]), callback_handler=None)
    result = agent("質問")
    assert result.metrics.accumulated_usage["totalTokens"] == 15
    assert result.metrics.cycle_count == 1
