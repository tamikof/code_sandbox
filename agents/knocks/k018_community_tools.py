"""ノック18: コミュニティツール入門 — strands-agents-tools を使う

自作しなくても、よく使うツールは strands-agents-tools パッケージに揃っている。
calculator は数式評価(sympy ベース)、current_time は現在時刻。

実行: uv run knocks/k018_community_tools.py
"""

from common import make_model
from strands_tools import calculator, current_time

from strands import Agent

if __name__ == "__main__":
    agent = Agent(model=make_model(), tools=[calculator, current_time])

    agent("2 の 100 乗はいくつ?あと、いま何時?")
