"""ノック36: 呼び出しスコープの状態 — invocation_state でツールに値を渡す

agent.state は「エージェントの寿命」の状態。これに対し invocation_state は
「この1回の呼び出しだけ」の状態。リクエストごとに変わる値(ユーザーID、
認可トークン、リクエストIDなど)をツールに渡すのに使う。
モデルには見えず、履歴にも残らない。

実行: uv run knocks/k036_invocation_state.py
"""

from common import make_model

from strands import Agent, tool
from strands.types.tools import ToolContext


@tool(context=True)
def get_my_orders(tool_context: ToolContext) -> str:
    """ログイン中のユーザーの注文履歴を取得する。"""
    # ユーザーIDはモデル経由ではなく invocation_state から受け取る。
    # モデルに「あなたのIDは?」と聞かせない = なりすましの余地を作らない
    user_id = tool_context.invocation_state.get("user_id", "anonymous")
    orders = {"u-001": "寿司セット ×1", "u-002": "ラーメン ×2"}
    return f"{user_id} の注文: {orders.get(user_id, 'なし')}"


if __name__ == "__main__":
    agent = Agent(model=make_model(), tools=[get_my_orders])

    # 同じエージェントでも、呼び出しごとに違うユーザーとして実行できる
    agent("私の注文履歴を見せて。", invocation_state={"user_id": "u-001"})
    print("\n" + "=" * 40 + "\n")
    agent("私の注文履歴を見せて。", invocation_state={"user_id": "u-002"})
