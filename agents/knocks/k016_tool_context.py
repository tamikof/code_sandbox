"""ノック16: ToolContext — ツールの中からエージェント本体にアクセスする

@tool(context=True) にすると、ツール関数が ToolContext を受け取れる。
ToolContext からは以下が見える:
  - tool_context.tool_use         : 今回の呼び出し情報 (toolUseId など)
  - tool_context.agent            : エージェント本体 (state や messages にアクセス可)
  - tool_context.invocation_state : 呼び出し単位で渡された値 (第4章ノック36)

実行: uv run knocks/k016_tool_context.py
"""

from common import make_model

from strands import Agent, tool
from strands.types.tools import ToolContext


@tool(context=True)
def add_to_cart(item: str, tool_context: ToolContext) -> str:
    """商品をカートに追加する。"""
    # 会話履歴ではなく agent.state にカートを持つ(履歴が圧縮されても消えない)
    cart = tool_context.agent.state.get("cart") or []
    cart.append(item)
    tool_context.agent.state.set("cart", cart)
    return f"{item} を追加しました(現在 {len(cart)} 件 / 呼び出しID: {tool_context.tool_use['toolUseId']})"


if __name__ == "__main__":
    agent = Agent(model=make_model(), tools=[add_to_cart])

    agent("りんごとバナナをカートに入れて。")

    # ツールが書き込んだ状態はエージェント側からも読める
    print("\n===== agent.state =====")
    print(agent.state.get("cart"))
