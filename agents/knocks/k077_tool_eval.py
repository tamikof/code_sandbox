"""ノック77: ツール選択の評価 — 「正しいツールを呼べたか」を測る

エージェントの正しさは応答テキストだけでなく「正しい行動を取ったか」でも測る。
テストケース(入力 → 期待されるツール)を用意し、エージェントが実際に
呼んだツールと突き合わせて正答率を出す。回帰テストの土台。

このノックは AWS 不要(モックモデルで動く。実モデルでは expected を確認する形になる)。
実行: uv run knocks/k077_tool_eval.py
"""

from dataclasses import dataclass

from mock_model import MockModel, ToolCall

from strands import Agent, tool


@tool
def get_weather(city: str) -> str:
    """天気を調べる。"""
    return f"{city}: 晴れ"


@tool
def get_news(topic: str) -> str:
    """ニュースを調べる。"""
    return f"{topic}: 最新ニュース"


@tool
def calculate(expression: str) -> str:
    """計算する。"""
    return "42"


def tools_called(agent: Agent) -> list[str]:
    """エージェントが実際に呼んだツール名を履歴から抽出する。"""
    return [
        block["toolUse"]["name"]
        for message in agent.messages
        for block in message["content"]
        if "toolUse" in block
    ]


@dataclass
class Case:
    prompt: str
    expected_tool: str
    # 実モデルの代わりに、その入力で「正しく動いた場合」のモック応答
    mock_response: ToolCall


CASES = [
    Case("東京の天気は?", "get_weather", ToolCall("get_weather", {"city": "東京"})),
    Case("AIの最新ニュースを教えて", "get_news", ToolCall("get_news", {"topic": "AI"})),
    Case("15×3はいくつ?", "calculate", ToolCall("calculate", {"expression": "15*3"})),
]


if __name__ == "__main__":
    tools = [get_weather, get_news, calculate]
    passed = 0

    print("===== ツール選択の評価 =====")
    for case in CASES:
        # 実運用では make_model() を使う。ここでは決定的に評価するためモックで
        # 「正しいツールを呼んだ場合」を再現している
        agent = Agent(model=MockModel([case.mock_response, "完了"]), tools=tools,
                      callback_handler=None)
        agent(case.prompt)
        called = tools_called(agent)
        ok = case.expected_tool in called
        passed += ok
        print(f"[{'OK ' if ok else 'NG '}] {case.prompt} → 期待 {case.expected_tool} / 実際 {called}")

    print(f"\n正答率: {passed}/{len(CASES)} ({passed / len(CASES):.0%})")
    # この CASES を pytest に載せれば回帰テストになる(ノック78)
