"""ノック88: A2A サーバ — 自分のエージェントをプロトコルで公開する

A2A (Agent-to-Agent) は「エージェント間通信の標準プロトコル」。
MCP がツールの標準なら、A2A はエージェントそのものの標準。
自分のエージェントを A2A サーバとして公開すると、別フレームワーク・別言語の
エージェントからも呼べるようになる。

前提: uv add strands-agents[a2a]
実行: uv run knocks/k088_a2a_server.py   (http://localhost:9000 で待ち受け)
"""

from common import make_model

from strands import Agent, tool


@tool
def get_recipe(dish: str) -> str:
    """料理のレシピを返す。"""
    recipes = {"カレー": "1.野菜を炒める 2.煮込む 3.ルーを入れる"}
    return recipes.get(dish, f"{dish} のレシピは準備中です")


# 公開したいエージェント(name と description が A2A の「名刺」になる)
recipe_agent = Agent(
    model=make_model(),
    name="recipe-expert",
    description="料理のレシピを提供する専門エージェント",
    tools=[get_recipe],
)

if __name__ == "__main__":
    # A2A サーバとしてラップして起動する
    from strands.multiagent.a2a import A2AServer

    server = A2AServer(agent=recipe_agent, host="127.0.0.1", port=9000)
    print("A2A サーバを http://127.0.0.1:9000 で起動します")
    print("エージェントカード: http://127.0.0.1:9000/.well-known/agent-card.json")
    print("ノック89のクライアントから接続できます。Ctrl+C で停止。")
    server.serve()
