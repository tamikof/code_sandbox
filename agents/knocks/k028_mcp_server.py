"""ノック28で使う自作 MCP サーバ(FastMCP 製)。

MCP (Model Context Protocol) サーバは「ツールの配布形式」。
ここで定義したツールは、Strands に限らず Claude Desktop など
任意の MCP クライアントから利用できる。

単体起動:
  uv run knocks/k028_mcp_server.py        # stdio で待ち受け(ノック28)
  uv run knocks/k028_mcp_server.py http   # Streamable HTTP で待ち受け(ノック27)
"""

import sys

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("recipe-server")


@mcp.tool()
def search_recipe(ingredient: str) -> str:
    """指定した食材を使うレシピを検索する。"""
    recipes = {
        "卵": "卵かけご飯、オムレツ、茶碗蒸し",
        "豚肉": "生姜焼き、豚汁、とんかつ",
        "トマト": "カプレーゼ、トマトパスタ、ガスパチョ",
    }
    return recipes.get(ingredient, f"{ingredient} のレシピは見つかりませんでした")


@mcp.tool()
def calc_calories(dish: str, servings: int = 1) -> str:
    """料理のカロリーを概算する。"""
    table = {"卵かけご飯": 350, "生姜焼き": 450, "トマトパスタ": 550}
    kcal = table.get(dish)
    if kcal is None:
        return f"{dish} のカロリーデータがありません"
    return f"{dish} {servings}人前: 約{kcal * servings}kcal"


if __name__ == "__main__":
    use_http = len(sys.argv) > 1 and sys.argv[1] == "http"
    mcp.run(transport="streamable-http" if use_http else "stdio")
