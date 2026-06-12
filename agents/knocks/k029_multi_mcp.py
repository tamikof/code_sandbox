"""ノック29: 複数ソースのツール統合 — MCP + 自作 + コミュニティの混在

実務のエージェントは「MCP サーバ数個 + 自作ツール + コミュニティツール」の
寄せ集めになる。Strands ではどの出自のツールも同じ tools リストに並べるだけ。

実行: uv run knocks/k029_multi_mcp.py
"""

import sys
from pathlib import Path

from common import make_model
from mcp import StdioServerParameters, stdio_client
from strands_tools import calculator

from strands import Agent, tool
from strands.tools.mcp import MCPClient

SERVER = Path(__file__).parent / "k028_mcp_server.py"

recipe_mcp = MCPClient(
    lambda: stdio_client(
        StdioServerParameters(command=sys.executable, args=[str(SERVER)])
    )
)


@tool
def get_budget() -> str:
    """今日の食費予算を取得する。"""
    return "今日の食費予算は 1200円 です"


if __name__ == "__main__":
    with recipe_mcp:
        # MCP のツール + 自作ツール + コミュニティツールを1つのリストに
        tools = [*recipe_mcp.list_tools_sync(), get_budget, calculator]

        agent = Agent(model=make_model(), tools=tools)
        print("統合されたツール:", agent.tool_names, "\n")

        agent(
            "卵かけご飯のカロリーを調べて、3人前だと予算内で作れそうか、"
            "1人前300円として計算して教えて。"
        )
