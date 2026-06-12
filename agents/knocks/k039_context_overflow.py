"""ノック39: コンテキスト溢れ対応 — overflow からの自動回復を観察する

履歴がモデルのコンテキスト窓を超えると ContextWindowOverflowException が起きる。
このとき Strands は会話マネージャの reduce_context() を呼んで履歴を削り、
自動でリトライする。この一連の流れをモックモデルで再現する。

このノックは AWS 不要(モックモデルで動く)。
実行: uv run knocks/k039_context_overflow.py
"""

from mock_model import MockModel

from strands import Agent
from strands.agent.conversation_manager import SlidingWindowConversationManager
from strands.types.exceptions import ContextWindowOverflowException


class TinyContextModel(MockModel):
    """履歴が4件を超えるとコンテキスト溢れを起こす、窓の小さいモデル(の振り)。"""

    async def stream(self, messages, tool_specs=None, system_prompt=None, **kwargs):
        if len(messages) > 4:
            print(f"  [モデル] 履歴{len(messages)}件は入りきりません! overflow 発生")
            raise ContextWindowOverflowException("context window exceeded")
        print(f"  [モデル] 履歴{len(messages)}件を受信、応答します")
        async for event in super().stream(messages, tool_specs, system_prompt, **kwargs):
            yield event


if __name__ == "__main__":
    agent = Agent(
        model=TinyContextModel(["1つ目の回答", "2つ目の回答", "3つ目の回答"]),
        conversation_manager=SlidingWindowConversationManager(window_size=4),
        callback_handler=None,
    )

    for i in (1, 2, 3):
        print(f"--- ターン{i} ---")
        result = agent(f"質問{i}")
        print(f"  応答: {result}")

    # ターン3で overflow → SlidingWindow が古い履歴を削除 → 自動リトライ → 成功
    print(f"最終的な履歴: {len(agent.messages)}件")
    print("\n回復は自動で行われた。NullConversationManager だとここで例外がそのまま落ちる")
