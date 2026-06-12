"""ノック32: スライディングウィンドウ — 直近 N 件だけを保持する

SlidingWindowConversationManager は履歴を window_size 件に維持する。
古い発言は捨てられる = エージェントは「忘れる」。

実行: uv run knocks/k032_sliding_window.py
"""

from common import make_model

from strands import Agent
from strands.agent.conversation_manager import SlidingWindowConversationManager

if __name__ == "__main__":
    agent = Agent(
        model=make_model(),
        # 4メッセージ(=2往復)しか覚えない極端な設定で「忘却」を体感する
        conversation_manager=SlidingWindowConversationManager(window_size=4),
        callback_handler=None,
    )

    print(agent("私の名前はタミコです。覚えておいて。"))
    print(agent("好きな食べ物は寿司です。"))
    print(agent("趣味はランニングです。"))

    # 名前を言ったターンはウィンドウから押し出されているはず
    print("\n履歴の件数:", len(agent.messages))
    print(agent("私の名前は何でしたか?"))
