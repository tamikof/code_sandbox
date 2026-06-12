"""ノック86: Graph 並列集約 — 複数の専門家 + 集約ノード

1つの入力を複数の専門家に同時に渡し(ファンアウト)、その結果を
1つの集約ノードでまとめる(ファンイン)。多角的なレビューの定番構成。

         ┌→ security_review ┐
  input ─┼→ perf_review    ─┼→ aggregator
         └→ ux_review      ┘

同じノードに複数のエッジが入ると、Graph は親が全部終わるまで待ってから実行する。

実行: uv run knocks/k086_graph_parallel.py
"""

from common import make_model

from strands import Agent
from strands.multiagent import GraphBuilder


def reviewer(name: str, focus: str) -> Agent:
    return Agent(
        model=make_model(),
        name=name,
        system_prompt=f"あなたは{focus}の専門レビュアーです。その観点だけで簡潔に指摘します。",
        callback_handler=None,
    )


security = reviewer("security", "セキュリティ")
performance = reviewer("performance", "パフォーマンス")
ux = reviewer("ux", "ユーザー体験")

aggregator = Agent(
    model=make_model(),
    name="aggregator",
    system_prompt="複数のレビュアーの指摘を受け取り、優先度をつけて1つの報告書にまとめます。",
    callback_handler=None,
)

if __name__ == "__main__":
    builder = GraphBuilder()
    for agent in (security, performance, ux, aggregator):
        builder.add_node(agent, agent.name)

    # 3人の専門家へファンアウト → aggregator へファンイン
    for r in ("security", "performance", "ux"):
        builder.add_edge(r, "aggregator")
        builder.set_entry_point(r)  # 3人とも入口(並列スタート)

    graph = builder.build()
    result = graph("新しいログイン画面のデザイン案をレビューして。")

    print("\n通ったノード:", list(result.results.keys()))
    print("ステータス:", result.status)
    # security/performance/ux が並列実行され、その後 aggregator が1回だけ動く
