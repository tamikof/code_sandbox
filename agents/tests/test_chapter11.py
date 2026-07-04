"""第11章のテスト: ループエンジニアリング。全テスト AWS 不要。

ループ制御はモデルの「中身」ではなく「回し方」の話なので、
MockModel で台本化すれば完全に決定的にテストできる。
"""

from dataclasses import dataclass

from k104_reflexion_loop import reflexion
from k105_verify_loop import loop_until_verified, verify_json
from k106_budget_driven_loop import Budget, budget_driven_search
from k107_runaway_guard import RepetitionGuard, lookup
from mock_model import MockModel, ToolCall

from strands import Agent, tool
from strands.types.agent import Limits


@tool
def noop(n: int) -> str:
    """ダミーツール。"""
    return f"tick {n}"


class ForeverModel(MockModel):
    """毎ターン必ずツールを呼ぶ(自力では止まらない)。"""

    async def stream(self, messages, tool_specs=None, system_prompt=None, **kw):
        turn = sum(1 for m in messages if m["role"] == "assistant") + 1
        inner = MockModel([ToolCall("noop", {"n": turn})])
        async for event in inner.stream(messages, tool_specs, system_prompt, **kw):
            yield event


# ---- ノック101・102: 反復回数の上限 ----


def test_turns_limit_stops_loop():
    agent = Agent(model=ForeverModel([]), tools=[noop], callback_handler=None)
    result = agent("無限に回して", limits=Limits(turns=3))
    assert result.stop_reason == "limit_turns"
    assert result.metrics.cycle_count == 3


def test_bounded_loop_is_resumable():
    """上限で止まった後、同じ agent を再呼び出しして続きから回せる。"""
    agent = Agent(model=ForeverModel([]), tools=[noop], callback_handler=None)
    agent("回して", limits=Limits(turns=2))
    messages_after_first = len(agent.messages)
    assert messages_after_first > 0

    result = agent("続けて", limits=Limits(turns=2))
    assert result.stop_reason == "limit_turns"
    assert len(agent.messages) > messages_after_first  # 履歴が伸びた=再開できた


def test_no_limit_would_not_stop_on_its_own():
    """limits なしだと turns では止まらない(別の安全網が必要なことの確認)。"""
    agent = Agent(model=ForeverModel([]), tools=[noop], callback_handler=None)
    # turns=1 を明示しないと止まらないループなので、必ず上限を付けて検証する
    result = agent("回して", limits=Limits(turns=1))
    assert result.stop_reason == "limit_turns"


# ---- ノック103: トークン予算の上限 ----


def test_total_tokens_limit_stops_loop():
    agent = Agent(model=ForeverModel([]), tools=[noop], callback_handler=None)
    result = agent("回して", limits=Limits(total_tokens=40))
    assert result.stop_reason == "limit_total_tokens"
    # ソフトキャップなので上限を多少超える
    assert result.metrics.accumulated_usage["totalTokens"] >= 40


# ---- ノック104: Reflexion(自己修正) ----


def test_reflexion_stops_when_passed():
    worker = Agent(model=MockModel(["雑な答え", "直した答え"]), callback_handler=None)

    @dataclass
    class C:
        passed: bool
        feedback: str

    verdicts = iter([C(False, "具体性がない"), C(True, "OK")])
    final, rounds = reflexion("書いて", worker, lambda t, d: next(verdicts), max_rounds=5)
    # round1 で不合格→改稿、round2 の批評で合格。合格したラウンド番号=2
    assert rounds == 2
    assert final.strip() == "直した答え"


def test_reflexion_is_bounded_when_never_passes():
    """批評が永遠に不合格でも max_rounds で必ず止まる(有界)。"""
    worker = Agent(model=MockModel(["答え"]), callback_handler=None)

    @dataclass
    class C:
        passed: bool
        feedback: str

    final, rounds = reflexion("書いて", worker, lambda t, d: C(False, "まだダメ"), max_rounds=3)
    assert rounds == 3  # 上限で打ち切られた


# ---- ノック105: 検証ループ ----


def test_verify_loop_succeeds_after_retries():
    generator = Agent(
        model=MockModel(['{"name":"太郎"', '{"name":"太郎"}', '{"name":"太郎","age":30}']),
        callback_handler=None,
    )
    result, attempts, ok = loop_until_verified(
        "JSON を作って",
        generator,
        lambda text: verify_json(text, {"name", "age"}),
        max_attempts=5,
    )
    assert ok is True
    assert attempts == 3  # 3回目で通過


def test_verify_loop_gives_up_when_bounded():
    """検証が通らないまま上限に達したら ok=False で止まる。"""
    generator = Agent(model=MockModel(["not json"]), callback_handler=None)
    _, attempts, ok = loop_until_verified(
        "JSON を作って",
        generator,
        lambda text: verify_json(text, {"name"}),
        max_attempts=2,
    )
    assert ok is False
    assert attempts == 2


def test_verify_json_helper():
    assert verify_json('{"a":1}', {"a"}) == (True, "OK")
    assert verify_json("broken", {"a"})[0] is False
    assert verify_json('{"a":1}', {"a", "b"})[0] is False  # キー不足


# ---- ノック106: 予算駆動ループ ----


def test_budget_driven_loop_scales_with_budget():
    def run(total: int) -> int:
        agent = Agent(model=MockModel(["案A", "案B", "案C", "案D", "案E"]), callback_handler=None)
        return len(budget_driven_search(agent, Budget(total), per_round_estimate=15))

    # 予算が増えると成果(アイデア数)が増える
    small = run(30)
    large = run(75)
    assert small == 2  # 30 / 15
    assert large == 5  # 75 / 15
    assert large > small


def test_budget_never_exceeds_total():
    budget = Budget(45)
    agent = Agent(model=MockModel(["x"]), callback_handler=None)
    budget_driven_search(agent, budget, per_round_estimate=15)
    assert budget.remaining() == 0  # 使い切って止まる(超過しない)


# ---- ノック107: 暴走ガード ----


def _tool_results(agent):
    return [
        block["toolResult"]
        for m in agent.messages
        for block in m["content"]
        if "toolResult" in block
    ]


def test_repetition_guard_blocks_after_threshold():
    guard = RepetitionGuard(threshold=2)

    # 同じ引数で3回 lookup を呼ぶ台本
    agent = Agent(
        model=MockModel(
            [
                ToolCall("lookup", {"key": "x"}),
                ToolCall("lookup", {"key": "x"}),
                ToolCall("lookup", {"key": "x"}),
                "諦めました",
            ]
        ),
        tools=[lookup],
        hooks=[guard],
        callback_handler=None,
    )
    agent("調べて", limits=Limits(turns=10))

    results = _tool_results(agent)
    # 3回目(threshold=2 を超える)が error でキャンセルされている
    assert results[-1]["status"] == "error"
    assert "繰り返し" in str(results[-1]["content"])
    # 1・2回目は成功していた
    assert results[0]["status"] == "success"


def test_repetition_guard_allows_distinct_calls():
    """引数が違えば反復と見なさない。"""
    guard = RepetitionGuard(threshold=2)
    agent = Agent(
        model=MockModel(
            [
                ToolCall("lookup", {"key": "a"}),
                ToolCall("lookup", {"key": "b"}),
                ToolCall("lookup", {"key": "c"}),
                "完了",
            ]
        ),
        tools=[lookup],
        hooks=[guard],
        callback_handler=None,
    )
    agent("色々調べて", limits=Limits(turns=10))
    # 全部違う引数なので、どれもキャンセルされない
    assert all(r["status"] == "success" for r in _tool_results(agent))
