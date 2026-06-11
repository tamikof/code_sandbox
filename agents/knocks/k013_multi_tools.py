"""ノック13: ツールの使い分け — モデルがどのツールを選ぶか観察する

実行: uv run knocks/k013_multi_tools.py
"""

from datetime import datetime, timezone, timedelta

from common import make_model

from strands import Agent, tool


@tool
def get_weather(city: str) -> str:
    """指定した都市の現在の天気を返す。"""
    # 本物の API は第3章 (http_request) で。ここではダミーデータ
    dummy = {"東京": "晴れ 22℃", "大阪": "曇り 20℃", "札幌": "雪 -1℃"}
    return dummy.get(city, f"{city} の天気情報はありません")


@tool
def get_current_time() -> str:
    """現在の日時(日本時間)を返す。"""
    jst = timezone(timedelta(hours=9))
    return datetime.now(jst).strftime("%Y-%m-%d %H:%M:%S JST")


if __name__ == "__main__":
    agent = Agent(model=make_model(), tools=[get_weather, get_current_time])

    # 質問に応じて使うツールが変わる。両方使う質問も試してみる
    agent("札幌の天気は?")
    print("\n" + "=" * 40 + "\n")
    agent("いま何時?あと東京の天気も教えて。")
