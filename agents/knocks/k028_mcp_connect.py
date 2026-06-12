"""ノック28: 自作 MCP サーバ — FastMCP で作って Strands から使う

サーバ本体は knocks/k028_mcp_server.py(FastMCP 製、約30行)。
このスクリプトはそれを stdio でサブプロセス起動して接続する。
「社内 API をツール化して配る」の最小構成。

実行: uv run knocks/k028_mcp_connect.py
"""

import sys
from pathlib import Path

from common import make_model
from mcp import StdioServerParameters, stdio_client

from strands import Agent
from strands.tools.mcp import MCPClient

SERVER = Path(__file__).parent / "k028_mcp_server.py"

recipe_mcp = MCPClient(
    lambda: stdio_client(
        StdioServerParameters(command=sys.executable, args=[str(SERVER)])
    )
)

if __name__ == "__main__":
    with recipe_mcp:
        tools = recipe_mcp.list_tools_sync()
        print("自作サーバのツール:", [t.tool_name for t in tools])

        agent = Agent(model=make_model(), tools=tools)
        agent("豚肉で作れる料理を探して。")
