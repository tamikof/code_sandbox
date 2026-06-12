"""第3章のテスト: ツール応用と MCP。

MCP のテストは自作 FastMCP サーバ (k028_mcp_server.py) をサブプロセス起動するので、
ネットワークも AWS も不要で全部ローカルで動く。
"""

import asyncio
import sys
import time
from pathlib import Path

from k021_direct_tool_call import get_user_plan
from k030_tool_selection import ALL_TOOLS, filter_tools, tool_catalog
from mock_model import MockModel, ToolCall

from strands import Agent, tool
from strands.tools.executors import ConcurrentToolExecutor, SequentialToolExecutor

KNOCKS_DIR = Path(__file__).parent.parent / "knocks"


# ---- ノック21: 直接呼び出し ----


def test_direct_tool_call_records_history():
    agent = Agent(model=MockModel(["ok"]), tools=[get_user_plan], callback_handler=None)
    result = agent.tool.get_user_plan(user_id="u-001")

    assert result["status"] == "success"
    assert result["content"] == [{"text": "プレミアム"}]
    # 直接呼び出しでも履歴に記録される (record_direct_tool_call=True がデフォルト)
    assert any("toolResult" in block for m in agent.messages for block in m["content"])


# ---- ノック22: 動的ツール管理 ----


def test_dynamic_tool_registration():
    @tool
    def late_tool() -> str:
        """あとから追加されるツール。"""
        return "追加されたツールです"

    agent = Agent(model=MockModel([ToolCall("late_tool", {}), "done"]), callback_handler=None)
    assert agent.tool_names == []

    agent.tool_registry.register_tool(late_tool)
    assert agent.tool_names == ["late_tool"]

    agent("実行して")  # 追加したツールがループで実行できる
    tool_results = [
        block["toolResult"]
        for m in agent.messages
        for block in m["content"]
        if "toolResult" in block
    ]
    assert tool_results[0]["status"] == "success"


# ---- ノック23・24: 並列 vs 直列実行 ----


def _make_slow_tools(log: list):
    @tool
    async def slow_a() -> str:
        """遅いツールA。"""
        await asyncio.sleep(0.2)
        log.append("a")
        return "A"

    @tool
    async def slow_b() -> str:
        """遅いツールB。"""
        await asyncio.sleep(0.2)
        log.append("b")
        return "B"

    return [slow_a, slow_b]


def _run_two_tools(executor) -> float:
    """1ターンで2ツールを同時に呼ぶターンを実行して所要時間を返す。"""
    agent = Agent(
        model=MockModel([[ToolCall("slow_a", {}), ToolCall("slow_b", {})], "done"]),
        tools=_make_slow_tools([]),
        tool_executor=executor,
        callback_handler=None,
    )
    start = time.perf_counter()
    agent("両方やって")
    return time.perf_counter() - start


def test_concurrent_executor_runs_tools_in_parallel():
    elapsed = _run_two_tools(ConcurrentToolExecutor())
    assert elapsed < 0.35  # 0.2秒×2 が並列なら ≈0.2秒


def test_sequential_executor_runs_tools_one_by_one():
    elapsed = _run_two_tools(SequentialToolExecutor())
    assert elapsed >= 0.35  # 直列なら ≈0.4秒


# ---- ノック25: ストリーミングツール ----


def test_streaming_tool_yields_progress_and_final_result():
    @tool
    async def batch(n: int):
        """バッチ処理。"""
        for i in range(1, n + 1):
            yield f"step {i}"
        yield "完了"

    agent = Agent(
        model=MockModel([ToolCall("batch", {"n": 2}), "done"]),
        tools=[batch],
        callback_handler=None,
    )

    async def collect():
        chunks = []
        async for event in agent.stream_async("やって"):
            if "tool_stream_event" in event:
                chunks.append(event["tool_stream_event"]["data"])
        return chunks

    chunks = asyncio.run(collect())
    assert chunks == ["step 1", "step 2", "完了"]

    # 最後の yield だけがツール結果としてモデルに渡る
    tool_results = [
        block["toolResult"]
        for m in agent.messages
        for block in m["content"]
        if "toolResult" in block
    ]
    assert tool_results[0]["content"] == [{"text": "完了"}]


# ---- ノック28: 自作 MCP サーバ(stdio で実サーバと通信) ----


def test_mcp_server_roundtrip():
    from mcp import StdioServerParameters, stdio_client

    from strands.tools.mcp import MCPClient

    client = MCPClient(
        lambda: stdio_client(
            StdioServerParameters(
                command=sys.executable, args=[str(KNOCKS_DIR / "k028_mcp_server.py")]
            )
        )
    )
    with client:
        tools = client.list_tools_sync()
        assert sorted(t.tool_name for t in tools) == ["calc_calories", "search_recipe"]

        # MCP ツールも普通のツールとしてエージェントループで動く
        agent = Agent(
            model=MockModel([ToolCall("search_recipe", {"ingredient": "卵"}), "どうぞ"]),
            tools=tools,
            callback_handler=None,
        )
        agent("卵のレシピは?")
        tool_results = [
            block["toolResult"]
            for m in agent.messages
            for block in m["content"]
            if "toolResult" in block
        ]
        assert tool_results[0]["status"] == "success"
        assert "卵かけご飯" in str(tool_results[0]["content"])


# ---- ノック30: ツールの絞り込み ----


def test_tool_catalog_and_filter():
    catalog = tool_catalog(ALL_TOOLS)
    assert "search_flights" in catalog
    assert "航空券を検索する" in catalog

    selected = filter_tools(ALL_TOOLS, ["search_flights", "search_hotels"])
    assert [t.tool_name for t in selected] == ["search_flights", "search_hotels"]
