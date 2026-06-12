"""ノック34: 自作会話マネージャ — ConversationManager を継承する

「最初の指示(要件)は絶対に消さず、途中は直近 N 件だけ残す」という
ピン留め付きウィンドウを自作する。apply_management と reduce_context の
2つを実装すればよい。

実行: uv run knocks/k034_custom_manager.py
"""

from common import make_model

from strands import Agent
from strands.agent.conversation_manager import ConversationManager
from strands.types.exceptions import ContextWindowOverflowException


class PinnedWindowManager(ConversationManager):
    """先頭 pinned 件 + 直近 window 件だけを残す会話マネージャ。

    注意: 実務では toolUse / toolResult のペアを泣き別れさせない配慮が必要
    (SlidingWindowConversationManager のソース参照)。ここでは簡略化している。
    """

    def __init__(self, pinned: int = 2, window: int = 4):
        super().__init__()
        self.pinned = pinned
        self.window = window

    def apply_management(self, agent, **kwargs) -> None:
        """毎ターン終了後に呼ばれる。ここで履歴を刈り込む。"""
        messages = agent.messages
        overflow = len(messages) - (self.pinned + self.window)
        if overflow > 0:
            # 先頭(ピン留め)と末尾(直近)の間を削除する
            del messages[self.pinned : self.pinned + overflow]
            self.removed_message_count += overflow

    def reduce_context(self, agent, e=None, **kwargs) -> None:
        """コンテキスト溢れ時に呼ばれる。さらに削れないなら例外を投げ直す。"""
        messages = agent.messages
        if len(messages) <= self.pinned + 1:
            raise ContextWindowOverflowException("これ以上削れません") from e
        del messages[self.pinned]
        self.removed_message_count += 1


if __name__ == "__main__":
    agent = Agent(
        model=make_model(),
        conversation_manager=PinnedWindowManager(pinned=2, window=4),
        callback_handler=None,
    )

    # 最初の指示(ペルソナ要件)はピン留めされて消えない
    print(agent("あなたは語尾に『ですわ』を付けるお嬢様です。以後ずっとそう話して。"))
    for q in ["寿司の魅力は?", "ラーメンは?", "カレーは?", "天ぷらは?"]:
        print(agent(q))

    print("\n履歴の件数:", len(agent.messages), "(pinned 2 + window 4 に収まる)")
    print("先頭メッセージ:", agent.messages[0]["content"][0]["text"][:40])
