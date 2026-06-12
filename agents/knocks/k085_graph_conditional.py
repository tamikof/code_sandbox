"""ノック85: Graph 条件分岐 — 内容に応じてルートを変える

エッジに condition(GraphState を見て True/False を返す関数)を付けると、
分岐するグラフが作れる。問い合わせを分類して、適切な担当ノードへ振り分ける
「ルーター」パターン。

  classify ─[技術なら]→ tech_support
           ─[それ以外]→ general_support

実行: uv run knocks/k085_graph_conditional.py
"""

from common import make_model

from strands import Agent
from strands.multiagent import GraphBuilder
from strands.multiagent.graph import GraphState

classifier = Agent(
    model=make_model(),
    name="classifier",
    system_prompt=(
        "問い合わせを分類します。技術的な問題なら必ず 'TECH' とだけ、"
        "それ以外なら 'GENERAL' とだけ、最後の行に出力してください。"
    ),
    callback_handler=None,
)
tech_support = Agent(
    model=make_model(),
    name="tech_support",
    system_prompt="あなたは技術サポートです。トラブルシューティングを案内します。",
    callback_handler=None,
)
general_support = Agent(
    model=make_model(),
    name="general_support",
    system_prompt="あなたは総合窓口です。一般的な問い合わせに対応します。",
    callback_handler=None,
)


def classified_as_tech(state: GraphState) -> bool:
    """classify ノードの出力に 'TECH' が含まれるかを判定する。"""
    result = state.results.get("classify")
    return result is not None and "TECH" in str(result.result)


if __name__ == "__main__":
    builder = GraphBuilder()
    builder.add_node(classifier, "classify")
    builder.add_node(tech_support, "tech")
    builder.add_node(general_support, "general")

    # 条件付きエッジ: classify の結果で行き先が変わる
    builder.add_edge("classify", "tech", condition=classified_as_tech)
    builder.add_edge("classify", "general", condition=lambda s: not classified_as_tech(s))
    builder.set_entry_point("classify")

    graph = builder.build()

    for question in ["パソコンが起動しません", "営業時間を教えてください"]:
        print(f"\n##### 質問: {question} #####")
        result = graph(question)
        print("通ったノード:", list(result.results.keys()))
