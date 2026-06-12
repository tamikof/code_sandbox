"""ノック42: コールバックハンドラ — イベント処理のもう1つの口

ノック1から応答が勝手に表示されていたのは、デフォルトの
PrintingCallbackHandler が "data" イベントを print していたから。
自作の関数に差し替えると、すべてのイベントが kwargs で流れ込んでくる。

stream_async(ノック41)との違い:
  - callback_handler: Agent に紐づく。同期呼び出しでも動く
  - stream_async   : 呼び出し側がループを握る。WebUI のバックエンド向き

実行: uv run knocks/k042_callback_handler.py
"""

from common import make_model

from strands import Agent


def my_handler(**kwargs) -> None:
    """イベントを受け取るコールバック。興味のあるキーだけ拾う。"""
    if "data" in kwargs:
        print(kwargs["data"], end="", flush=True)
    elif "current_tool_use" in kwargs and kwargs["current_tool_use"].get("name"):
        print(f"\n[ツール準備中: {kwargs['current_tool_use']['name']}]")


if __name__ == "__main__":
    agent = Agent(model=make_model(), callback_handler=my_handler)
    agent("おにぎりの具で一番人気は何だと思う?2文で。")
    print()
