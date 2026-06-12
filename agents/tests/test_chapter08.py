"""第8章のテスト: 観測性と評価。全テスト AWS 不要。"""

from k072_metrics import search, translate
from k077_tool_eval import CASES, tools_called
from k078_regression import SUITE, evaluate
from k079_cost import cost_of
from mock_model import MockModel, ToolCall

from strands import Agent, tool


@tool
def boom() -> str:
    """必ず失敗するツール。"""
    raise RuntimeError("失敗")


# ---- ノック72: メトリクス ----


def test_metrics_summary_has_tool_stats():
    agent = Agent(
        model=MockModel([ToolCall("search", {"keyword": "寿司"}), "完了"]),
        tools=[search, translate],
        callback_handler=None,
    )
    result = agent("寿司を検索")
    summary = result.metrics.get_summary()

    assert summary["total_cycles"] == 2  # ツール実行で2周
    assert summary["accumulated_usage"]["totalTokens"] > 0
    assert "search" in summary["tool_usage"]
    assert summary["tool_usage"]["search"]["execution_stats"]["call_count"] == 1
    assert summary["tool_usage"]["search"]["execution_stats"]["success_rate"] == 1.0


def test_tool_error_reflected_in_metrics():
    agent = Agent(
        model=MockModel([ToolCall("boom", {}), "エラーでした"]),
        tools=[boom],
        callback_handler=None,
    )
    result = agent("実行して")
    stats = result.metrics.get_summary()["tool_usage"]["boom"]["execution_stats"]
    assert stats["error_count"] == 1
    assert stats["success_rate"] == 0.0


# ---- ノック77: ツール選択の評価 ----


def test_tool_selection_eval_all_pass():
    """各ケースで期待ツールが呼ばれることを確認(回帰テストの形)。"""
    from k077_tool_eval import calculate, get_news, get_weather

    tools = [get_weather, get_news, calculate]
    for case in CASES:
        agent = Agent(
            model=MockModel([case.mock_response, "完了"]),
            tools=tools,
            callback_handler=None,
        )
        agent(case.prompt)
        assert case.expected_tool in tools_called(agent), case.prompt


# ---- ノック78: 回帰スイート ----


def test_regression_suite_passes():
    """評価スイートの全ケースが合格すること(プロンプト変更時の安全網)。"""
    for case in SUITE:
        ok, answer = evaluate(case)
        assert ok, f"{case.name} が失敗: {answer}"


def test_regression_catches_bad_output():
    """わざと悪い応答を返すと回帰スイートが検知することを確認。"""
    from k078_regression import EvalCase

    bad_case = EvalCase(
        name="敬語チェック",
        prompt="返金して",
        mock_reply="無理。",  # 敬語になっていない
        must_include=["ます", "いたし"],
    )
    ok, _ = evaluate(bad_case)
    assert ok is False  # 評価器がちゃんと不合格を出す


# ---- ノック79: コスト集計 ----


def test_cost_calculation():
    usage = {"inputTokens": 1_000_000, "outputTokens": 1_000_000}
    # haiku: input $1 + output $5 = $6
    assert cost_of(usage, "haiku-4-5") == 6.0
    # opus は haiku より高い
    assert cost_of(usage, "opus-4-8") > cost_of(usage, "haiku-4-5")


def test_cost_scales_with_tokens():
    small = {"inputTokens": 1000, "outputTokens": 200}
    large = {"inputTokens": 100_000, "outputTokens": 20_000}
    assert cost_of(large, "haiku-4-5") == cost_of(small, "haiku-4-5") * 100
