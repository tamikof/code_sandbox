"""第4章のテスト: コンテキストと会話管理。全テスト AWS 不要。"""

import json

from k034_custom_manager import PinnedWindowManager
from k036_invocation_state import get_my_orders
from k040_resume_conversation import load_conversation, save_conversation
from mock_model import MockModel

from strands import Agent
from strands.agent.conversation_manager import (
    SlidingWindowConversationManager,
    SummarizingConversationManager,
)
from strands.types.exceptions import ContextWindowOverflowException


class TinyContextModel(MockModel):
    """履歴が max_messages 件を超えるとコンテキスト溢れを起こすモデル(ノック39)。"""

    def __init__(self, responses, max_messages: int = 4):
        super().__init__(responses)
        self.max_messages = max_messages
        self.overflow_count = 0

    async def stream(self, messages, tool_specs=None, system_prompt=None, **kwargs):
        if len(messages) > self.max_messages:
            self.overflow_count += 1
            raise ContextWindowOverflowException("context window exceeded")
        async for event in super().stream(messages, tool_specs, system_prompt, **kwargs):
            yield event


# ---- ノック32: スライディングウィンドウ ----


def test_sliding_window_caps_history():
    agent = Agent(
        model=MockModel(["a", "b", "c", "d"]),
        conversation_manager=SlidingWindowConversationManager(window_size=4),
        callback_handler=None,
    )
    for i in range(4):
        agent(f"質問{i}")
    assert len(agent.messages) == 4  # 8件たまるはずが4件に維持される


# ---- ノック33: 要約マネージャ ----


def test_summarizing_manager_replaces_old_history_with_summary():
    summarizer = Agent(model=MockModel(["要約: ユーザーは寿司が好き"]), callback_handler=None)
    manager = SummarizingConversationManager(
        summary_ratio=0.5,
        preserve_recent_messages=2,
        summarization_agent=summarizer,
    )
    agent = Agent(
        model=MockModel(["res1", "res2", "res3"]),
        conversation_manager=manager,
        callback_handler=None,
    )
    agent("寿司が好きです")
    agent("天気の話をしよう")
    agent("元気?")

    assert len(agent.messages) == 6
    manager.reduce_context(agent)  # 溢れ時に自動で呼ばれる処理を手動発火

    assert len(agent.messages) < 6
    # 先頭が要約メッセージに置き換わっている
    assert "要約" in agent.messages[0]["content"][0]["text"]


# ---- ノック34: 自作マネージャ ----


def test_pinned_window_manager_keeps_head_and_tail():
    agent = Agent(
        model=MockModel([f"r{i}" for i in range(6)]),
        conversation_manager=PinnedWindowManager(pinned=2, window=4),
        callback_handler=None,
    )
    agent("最初の重要な指示")
    for i in range(5):
        agent(f"雑談{i}")

    assert len(agent.messages) == 6  # pinned 2 + window 4
    # 先頭(ピン留め)は最初の指示のまま
    assert agent.messages[0]["content"][0]["text"] == "最初の重要な指示"
    # 末尾は直近の会話
    assert agent.messages[-2]["content"][0]["text"] == "雑談4"
    assert agent.conversation_manager.removed_message_count == 6


# ---- ノック35: agent.state ----


def test_agent_state_is_separate_from_messages():
    agent = Agent(
        model=MockModel(["はい"]),
        state={"user_id": "u-001"},
        callback_handler=None,
    )
    agent.state.set("plan", "premium")

    assert agent.state.get("user_id") == "u-001"
    assert agent.state.get("plan") == "premium"

    agent("こんにちは")
    # state の中身は会話履歴に一切現れない
    assert "u-001" not in json.dumps(agent.messages)
    assert "premium" not in json.dumps(agent.messages)


# ---- ノック36: invocation_state ----


def test_invocation_state_reaches_tool():
    from mock_model import ToolCall

    agent = Agent(
        model=MockModel([ToolCall("get_my_orders", {}), "どうぞ"]),
        tools=[get_my_orders],
        callback_handler=None,
    )
    agent("注文履歴は?", invocation_state={"user_id": "u-002"})

    tool_results = [
        block["toolResult"]
        for m in agent.messages
        for block in m["content"]
        if "toolResult" in block
    ]
    assert "ラーメン" in str(tool_results[0]["content"])  # u-002 の注文が引けた


# ---- ノック39: overflow からの自動回復 ----


def test_overflow_triggers_reduce_and_retry():
    model = TinyContextModel(["a", "b", "c"], max_messages=4)
    agent = Agent(
        model=model,
        conversation_manager=SlidingWindowConversationManager(window_size=4),
        callback_handler=None,
    )
    agent("1")
    agent("2")
    result = agent("3")  # 履歴5件 → overflow → 削減 → 自動リトライ

    assert model.overflow_count == 1
    assert str(result).strip() == "c"  # 例外で落ちずに応答が返った
    assert len(agent.messages) <= 4


# ---- ノック40: 会話の保存と復元 ----


def test_save_and_resume_conversation(tmp_path):
    save_file = tmp_path / "conv.json"

    agent = Agent(model=MockModel(["覚えました"]), callback_handler=None)
    agent("私の名前はタミコです")
    save_conversation(agent, save_file)

    restored = Agent(
        model=MockModel(["タミコさんですね"]),
        messages=load_conversation(save_file),
        callback_handler=None,
    )
    assert len(restored.messages) == 2  # 過去の1往復が入った状態で始まる
    restored("私の名前は?")
    # 復元した履歴がモデルへのリクエストに含まれている
    assert "タミコ" in json.dumps(restored.model.calls[0]["messages"], ensure_ascii=False)
