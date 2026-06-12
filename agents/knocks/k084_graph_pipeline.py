"""ノック84: Graph 直列 — リサーチ→分析→執筆のパイプライン

Swarm(82)は「誰が動くかをエージェントが決める」自律型。Graph は逆に、
処理の流れを**開発者が決定的に固定**する。ノードとエッジで DAG を組み、
あるノードの出力が次のノードの入力になる。再現性が要る業務処理向き。

実行: uv run knocks/k084_graph_pipeline.py
"""

from common import make_model

from strands import Agent
from strands.multiagent import GraphBuilder

researcher = Agent(
    model=make_model(),
    name="researcher",
    system_prompt="与えられたテーマについて事実を箇条書きで調査する。",
    callback_handler=None,
)
analyst = Agent(
    model=make_model(),
    name="analyst",
    system_prompt="調査結果を受け取り、重要なポイントと示唆を分析する。",
    callback_handler=None,
)
writer = Agent(
    model=make_model(),
    name="writer",
    system_prompt="分析を受け取り、一般向けの短い記事にまとめる。",
    callback_handler=None,
)

if __name__ == "__main__":
    builder = GraphBuilder()
    builder.add_node(researcher, "research")
    builder.add_node(analyst, "analyze")
    builder.add_node(writer, "write")

    # research → analyze → write の一本道。出力が自動で次の入力になる
    builder.add_edge("research", "analyze")
    builder.add_edge("analyze", "write")
    builder.set_entry_point("research")

    graph = builder.build()
    result = graph("リモートワークが生産性に与える影響")

    print("\n===== 実行されたノード =====")
    for node_id in result.results:
        print(f"→ {node_id}")
    print(f"\nステータス: {result.status}")
