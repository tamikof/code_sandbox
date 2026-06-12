"""ノック90: マルチエージェント観測 — ネストしたトレースで全体を追う

マルチエージェントは「どのエージェントがどれだけ時間とトークンを使ったか」が
見えないと改善できない。Graph / Swarm の結果オブジェクトには、ノードごとの
メトリクスが集約されている。これを取り出して可視化する。

このノックは AWS 不要(モックモデルで動く)。
実行: uv run knocks/k090_multiagent_observability.py
"""

from mock_model import MockModel

from strands import Agent
from strands.multiagent import GraphBuilder

if __name__ == "__main__":
    researcher = Agent(model=MockModel(["調査結果: 3つの事実"]), name="researcher",
                       callback_handler=None)
    analyst = Agent(model=MockModel(["分析: 重要な傾向あり"]), name="analyst",
                    callback_handler=None)
    writer = Agent(model=MockModel(["記事: まとめました"]), name="writer",
                   callback_handler=None)

    builder = GraphBuilder()
    builder.add_node(researcher, "research")
    builder.add_node(analyst, "analyze")
    builder.add_node(writer, "write")
    builder.add_edge("research", "analyze")
    builder.add_edge("analyze", "write")
    builder.set_entry_point("research")

    graph = builder.build()
    result = graph("AIの最新動向についての記事を作って")

    # グラフ全体のメトリクス
    print("===== グラフ全体 =====")
    print(f"ステータス     : {result.status}")
    print(f"総ノード実行数 : {result.completed_nodes}/{result.total_nodes}")
    print(f"合計トークン   : {result.accumulated_usage['totalTokens']}")

    # ノードごとのメトリクス(どのエージェントが重いかが分かる)
    print("\n===== ノード別 =====")
    for node_id, node_result in result.results.items():
        usage = node_result.accumulated_usage
        print(
            f"{node_id:10s}: {usage['totalTokens']:3d}トークン / "
            f"実行 {node_result.execution_count}回 / "
            f"{node_result.execution_time}ms"
        )

    print(
        "\n本番では OTel トレース(ノック73)を有効にすると、これがネストした"
        "スパンの木として収集基盤に送られ、ボトルネックを視覚的に追える。"
    )
