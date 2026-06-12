"""第9章のテスト: マルチエージェント。全テスト AWS 不要。"""

from mock_model import MockModel, ToolCall

from strands import Agent
from strands.multiagent import GraphBuilder, Swarm
from strands.multiagent.graph import GraphState


# ---- ノック81: Agents as Tools ----


def test_agent_as_tool_is_callable_by_orchestrator():
    specialist = Agent(
        model=MockModel(["専門家の回答です"]),
        name="specialist",
        description="専門家",
        callback_handler=None,
    )
    orchestrator = Agent(
        model=MockModel([ToolCall("specialist", {"prompt": "質問"}), "まとめました"]),
        tools=[specialist.as_tool(name="specialist", description="専門家に聞く")],
        callback_handler=None,
    )
    result = orchestrator("専門家に聞いて")

    # オーケストレーターが specialist ツールを呼んだ
    called = [
        block["toolUse"]["name"]
        for m in orchestrator.messages
        for block in m["content"]
        if "toolUse" in block
    ]
    assert "specialist" in called
    assert str(result).strip() == "まとめました"


# ---- ノック82: Swarm ----


def test_swarm_completes_with_single_agent():
    worker = Agent(
        model=MockModel(["完了しました"]),
        name="worker",
        description="作業者",
        callback_handler=None,
    )
    swarm = Swarm([worker], entry_point=worker, max_iterations=3)
    result = swarm("タスクをやって")

    assert str(result.status) == "Status.COMPLETED"
    assert [n.node_id for n in result.node_history] == ["worker"]


# ---- ノック83: Swarm 制御(上限が効く) ----


def test_swarm_respects_entry_point():
    a = Agent(model=MockModel(["Aが対応"]), name="agent_a", description="A",
              callback_handler=None)
    b = Agent(model=MockModel(["Bが対応"]), name="agent_b", description="B",
              callback_handler=None)
    swarm = Swarm([a, b], entry_point=b, max_handoffs=2, max_iterations=2)
    result = swarm("対応して")
    # 指定した entry_point(b)から始まる
    assert result.node_history[0].node_id == "agent_b"


# ---- ノック84: Graph 直列パイプライン ----


def test_graph_executes_nodes_in_order():
    n1 = Agent(model=MockModel(["研究完了"]), name="r", callback_handler=None)
    n2 = Agent(model=MockModel(["分析完了"]), name="a", callback_handler=None)
    n3 = Agent(model=MockModel(["執筆完了"]), name="w", callback_handler=None)

    builder = GraphBuilder()
    builder.add_node(n1, "research")
    builder.add_node(n2, "analyze")
    builder.add_node(n3, "write")
    builder.add_edge("research", "analyze")
    builder.add_edge("analyze", "write")
    builder.set_entry_point("research")

    result = builder.build()("テーマ")
    assert str(result.status) == "Status.COMPLETED"
    # 3ノードすべて実行され、順序が research→analyze→write
    assert [str(n) for n in result.execution_order] == [
        "research",
        "analyze",
        "write",
    ] or list(result.results.keys()) == ["research", "analyze", "write"]


# ---- ノック85: Graph 条件分岐 ----


def _routing_graph():
    classifier = Agent(model=MockModel(["これは技術問題 TECH"]), name="c",
                       callback_handler=None)
    tech = Agent(model=MockModel(["技術サポート対応"]), name="t", callback_handler=None)
    general = Agent(model=MockModel(["総合窓口対応"]), name="g", callback_handler=None)

    def is_tech(state: GraphState) -> bool:
        r = state.results.get("classify")
        return r is not None and "TECH" in str(r.result)

    builder = GraphBuilder()
    builder.add_node(classifier, "classify")
    builder.add_node(tech, "tech")
    builder.add_node(general, "general")
    builder.add_edge("classify", "tech", condition=is_tech)
    builder.add_edge("classify", "general", condition=lambda s: not is_tech(s))
    builder.set_entry_point("classify")
    return builder.build()


def test_graph_conditional_routes_to_tech():
    result = _routing_graph()("PCが壊れた")
    executed = list(result.results.keys())
    assert "tech" in executed
    assert "general" not in executed  # 条件分岐で general は実行されない


# ---- ノック86: Graph 並列集約 ----


def test_graph_parallel_fanin_runs_aggregator_once():
    revs = [
        Agent(model=MockModel([f"{n}レビュー"]), name=n, callback_handler=None)
        for n in ("sec", "perf", "ux")
    ]
    agg = Agent(model=MockModel(["集約しました"]), name="agg", callback_handler=None)

    builder = GraphBuilder()
    for r in revs:
        builder.add_node(r, r.name)
    builder.add_node(agg, "agg")
    for name in ("sec", "perf", "ux"):
        builder.add_edge(name, "agg")
        builder.set_entry_point(name)

    result = builder.build()("レビューして")
    assert str(result.status) == "Status.COMPLETED"
    # 4ノード(レビュアー3 + 集約1)すべて実行
    assert set(result.results.keys()) == {"sec", "perf", "ux", "agg"}
    # aggregator は1回だけ
    assert result.results["agg"].execution_count == 1


# ---- ノック90: マルチエージェント観測 ----


def test_graph_result_exposes_per_node_metrics():
    n1 = Agent(model=MockModel(["研究"]), name="r", callback_handler=None)
    n2 = Agent(model=MockModel(["分析"]), name="a", callback_handler=None)

    builder = GraphBuilder()
    builder.add_node(n1, "research")
    builder.add_node(n2, "analyze")
    builder.add_edge("research", "analyze")
    builder.set_entry_point("research")

    result = builder.build()("テーマ")
    assert result.completed_nodes == 2
    assert result.total_nodes == 2
    assert result.accumulated_usage["totalTokens"] > 0
    # ノードごとにトークンが取れる
    for node_id in ("research", "analyze"):
        assert result.results[node_id].accumulated_usage["totalTokens"] > 0
