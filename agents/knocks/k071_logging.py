"""ノック71: ロギング — strands ロガーでエージェントの内部を覗く

Strands は標準の logging を使っている。"strands" ロガーのレベルを下げると、
モデルへのリクエスト、ツール選択、イベントループの判断が見えるようになる。
デバッグの第一歩。

このノックは AWS 不要(モックモデルで動く)。
実行: uv run knocks/k071_logging.py
"""

import logging

from mock_model import MockModel, ToolCall

from strands import Agent, tool

# strands ロガーを DEBUG にすると内部の動きが標準エラーに流れる
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)-7s | %(name)s | %(message)s",
)
logging.getLogger("strands").setLevel(logging.DEBUG)


@tool
def get_weather(city: str) -> str:
    """都市の天気を返す。"""
    return f"{city}: 晴れ"


if __name__ == "__main__":
    agent = Agent(model=MockModel([ToolCall("get_weather", {"city": "東京"}), "晴れです"]),
                  tools=[get_weather], callback_handler=None)
    agent("東京の天気は?")
    # ログに「どのツールを選んだか」「サイクルが何周したか」などが出る。
    # 本番では特定のロガー(strands.tools 等)だけ DEBUG にして絞り込む
