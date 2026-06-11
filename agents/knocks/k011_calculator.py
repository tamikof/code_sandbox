"""ノック11: 電卓エージェント — @tool で最初の自作ツール

実行: uv run knocks/k011_calculator.py
"""

from common import make_model

from strands import Agent, tool


@tool
def add(a: float, b: float) -> float:
    """2つの数を足し算する。"""
    return a + b


@tool
def multiply(a: float, b: float) -> float:
    """2つの数を掛け算する。"""
    return a * b


if __name__ == "__main__":
    # tools に渡すだけで、モデルが「いつ・どの順で」使うかを自分で判断する
    agent = Agent(model=make_model(), tools=[add, multiply])
    agent("(3 + 4) × 25 はいくつ?ツールを使って計算して。")
