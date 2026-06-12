"""ノック31: 無管理の限界 — NullConversationManager で履歴の肥大化を観察する

会話管理を切ると、履歴は無限に伸び、毎ターン全部モデルに送られる。
入力トークン数がターンごとに増えていくのを実測する。

実行: uv run knocks/k031_null_manager.py
"""

from common import make_model

from strands import Agent
from strands.agent.conversation_manager import NullConversationManager

if __name__ == "__main__":
    agent = Agent(
        model=make_model(),
        conversation_manager=NullConversationManager(),  # 何も管理しない
        callback_handler=None,
    )

    topics = ["寿司", "ラーメン", "カレー", "天ぷら", "うどん"]
    for i, topic in enumerate(topics, 1):
        result = agent(f"{topic}の魅力を2文で語って。")
        usage = result.metrics.accumulated_usage
        print(
            f"ターン{i}: 履歴 {len(agent.messages):2d}件 / "
            f"今回の入力トークン {usage['inputTokens']}"
        )

    # 入力トークンがターンごとに増える = 過去の全履歴を毎回送り直しているから。
    # 長く動くエージェントでは、これがコスト増とコンテキスト溢れの原因になる
