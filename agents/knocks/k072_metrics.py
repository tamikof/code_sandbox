"""ノック72: メトリクス取得 — EventLoopMetrics を読む

AgentResult.metrics には、その呼び出しのトークン・レイテンシ・サイクル数・
ツール別の統計が詰まっている。get_summary() で扱いやすい dict になる。
コスト管理とパフォーマンス分析の素データ。

このノックは AWS 不要(モックモデルで動く)。
実行: uv run knocks/k072_metrics.py
"""

import json

from mock_model import MockModel, ToolCall

from strands import Agent, tool


@tool
def search(keyword: str) -> str:
    """検索する。"""
    return f"{keyword}: 10件"


@tool
def translate(text: str) -> str:
    """翻訳する。"""
    return f"translated: {text}"


if __name__ == "__main__":
    agent = Agent(
        model=MockModel(
            [
                [ToolCall("search", {"keyword": "寿司"}), ToolCall("translate", {"text": "sushi"})],
                "完了しました",
            ]
        ),
        tools=[search, translate],
        callback_handler=None,
    )

    result = agent("寿司を検索して英訳もして。")
    summary = result.metrics.get_summary()

    print("===== サマリー =====")
    print(f"サイクル数      : {summary['total_cycles']}")
    print(f"合計トークン    : {summary['accumulated_usage']['totalTokens']}")
    print(f"レイテンシ(ms)  : {summary['accumulated_metrics']['latencyMs']}")

    print("\n===== ツール別の統計 =====")
    for name, stats in summary["tool_usage"].items():
        exec_stats = stats["execution_stats"]
        print(
            f"{name}: 呼出 {exec_stats['call_count']}回 / "
            f"成功率 {exec_stats['success_rate']:.0%} / "
            f"平均 {exec_stats['average_time'] * 1000:.1f}ms"
        )
