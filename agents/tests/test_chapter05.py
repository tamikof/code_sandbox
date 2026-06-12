"""第5章のテスト: ストリーミングとフック。全テスト AWS 不要。"""

import asyncio

from k046_tool_guard import FileAccessGuard, read_file
from k047_tool_audit import AuditAndMask, get_customer
from k048_message_hook import ConversationRecorder
from k049_human_approval import ApprovalHook, send_invoice
from mock_model import MockModel, ToolCall

from strands import Agent
from strands.hooks import (
    AfterInvocationEvent,
    BeforeInvocationEvent,
    HookProvider,
    HookRegistry,
)


# ---- ノック41: ストリーミング ----


def test_stream_async_yields_text_deltas():
    agent = Agent(model=MockModel(["こんにちは!"]), callback_handler=None)

    async def collect() -> str:
        chunks = []
        async for event in agent.stream_async("やあ"):
            if "data" in event:
                chunks.append(event["data"])
        return "".join(chunks)

    assert asyncio.run(collect()) == "こんにちは!"


# ---- ノック42: コールバックハンドラ ----


def test_custom_callback_handler_receives_data():
    received = []
    agent = Agent(
        model=MockModel(["はい"]),
        callback_handler=lambda **kw: received.append(kw["data"]) if "data" in kw else None,
    )
    agent("やあ")
    assert "".join(received) == "はい"


# ---- ノック45: ライフサイクルフック ----


def test_lifecycle_hooks_fire_in_order():
    order = []

    class Recorder(HookProvider):
        def register_hooks(self, registry: HookRegistry, **kwargs) -> None:
            registry.add_callback(BeforeInvocationEvent, lambda e: order.append("before"))
            registry.add_callback(AfterInvocationEvent, lambda e: order.append("after"))

    agent = Agent(model=MockModel(["a", "b"]), hooks=[Recorder()], callback_handler=None)
    agent("1回目")
    agent("2回目")
    assert order == ["before", "after", "before", "after"]


# ---- ノック46: ツールガード ----


def _tool_results(agent):
    return [
        block["toolResult"]
        for m in agent.messages
        for block in m["content"]
        if "toolResult" in block
    ]


def test_guard_blocks_forbidden_path():
    agent = Agent(
        model=MockModel([ToolCall("read_file", {"path": "/etc/passwd"}), "了解"]),
        tools=[read_file],
        hooks=[FileAccessGuard()],
        callback_handler=None,
    )
    agent("読んで")
    result = _tool_results(agent)[0]
    assert result["status"] == "error"
    assert "ポリシー違反" in str(result["content"])


def test_guard_rewrites_relative_path():
    agent = Agent(
        model=MockModel([ToolCall("read_file", {"path": "notes.txt"}), "了解"]),
        tools=[read_file],
        hooks=[FileAccessGuard()],
        callback_handler=None,
    )
    agent("読んで")
    result = _tool_results(agent)[0]
    assert result["status"] == "success"
    assert "/workspace/notes.txt" in str(result["content"])  # 正規化された引数で実行された


# ---- ノック47: 監査とマスキング ----


def test_audit_hook_masks_phone_number():
    hook = AuditAndMask()
    agent = Agent(
        model=MockModel([ToolCall("get_customer", {"customer_id": "C-1"}), "どうぞ"]),
        tools=[get_customer],
        hooks=[hook],
        callback_handler=None,
    )
    agent("顧客情報を")
    result = _tool_results(agent)[0]
    assert "090-1234-5678" not in str(result["content"])  # モデルに渡る前にマスク済み
    assert "***-****-****" in str(result["content"])
    assert any("tool=get_customer" in line for line in hook.audit_log)


# ---- ノック48: メッセージフック ----


def test_message_hook_records_all_messages():
    recorder = ConversationRecorder()
    agent = Agent(model=MockModel(["やあ"]), hooks=[recorder], callback_handler=None)
    agent("こんにちは")
    assert len(recorder.records) == 2  # user と assistant の2件
    assert recorder.records[0].startswith("user:")
    assert recorder.records[1].startswith("assistant:")


# ---- ノック49: 承認フロー ----


def _run_invoice_agent(approve: bool):
    agent = Agent(
        model=MockModel([ToolCall("send_invoice", {"to": "田中商事", "amount": 50000}), "完了"]),
        tools=[send_invoice],
        hooks=[ApprovalHook({"send_invoice"}, lambda name, args: approve)],
        callback_handler=None,
    )
    agent("請求書を送って")
    return _tool_results(agent)[0]


def test_approval_denied_cancels_tool():
    result = _run_invoice_agent(approve=False)
    assert result["status"] == "error"
    assert "承認しませんでした" in str(result["content"])


def test_approval_granted_runs_tool():
    result = _run_invoice_agent(approve=True)
    assert result["status"] == "success"
    assert "送付しました" in str(result["content"])


# ---- ノック50: スナップショット ----


def test_snapshot_restores_messages_and_state():
    agent = Agent(model=MockModel(["r1", "r2"]), callback_handler=None)
    agent("最初の質問")
    agent.state.set("step", 1)
    checkpoint = agent.take_snapshot(preset="session")

    agent("余計な質問")
    agent.state.set("step", 2)
    assert len(agent.messages) == 4

    agent.load_snapshot(checkpoint)
    assert len(agent.messages) == 2  # チェックポイント時点に巻き戻った
    assert agent.state.get("step") == 1
