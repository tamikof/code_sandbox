"""ノック27: MCP (Streamable HTTP) — HTTP トランスポートでの接続

stdio はローカルのサブプロセス向け。リモートで動いている MCP サーバには
Streamable HTTP で接続する。AgentCore Gateway(第10章)もこの方式。

前提: 別ターミナルで自作サーバを HTTP モードで起動しておく
  uv run knocks/k028_mcp_server.py http

実行: uv run knocks/k027_mcp_http.py
"""

from common import make_model
from mcp.client.streamable_http import streamablehttp_client

from strands import Agent
from strands.tools.mcp import MCPClient

# FastMCP の streamable-http のデフォルトは http://127.0.0.1:8000/mcp
recipe_mcp = MCPClient(lambda: streamablehttp_client("http://127.0.0.1:8000/mcp"))

if __name__ == "__main__":
    with recipe_mcp:
        tools = recipe_mcp.list_tools_sync()
        print("接続先のツール:", [t.tool_name for t in tools])

        agent = Agent(model=make_model(), tools=tools)
        agent("卵を使ったレシピを探して、そのうち1品のカロリーを教えて。")
