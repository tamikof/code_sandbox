"""ノック26: MCP (stdio) — 既存の MCP サーバに接続する

MCP (Model Context Protocol) はツールの標準配布形式。世の中の MCP サーバを
そのままエージェントのツールにできる。ここでは AWS Documentation MCP サーバ
(AWS 公式ドキュメント検索)に stdio で接続する。

前提: uvx コマンド(uv に同梱)とネットワーク接続
実行: uv run knocks/k026_mcp_stdio.py
"""

from common import make_model
from mcp import StdioServerParameters, stdio_client

from strands import Agent
from strands.tools.mcp import MCPClient

# stdio = MCP サーバをサブプロセスとして起動し、標準入出力で通信する
aws_docs_mcp = MCPClient(
    lambda: stdio_client(
        StdioServerParameters(
            command="uvx",
            args=["awslabs.aws-documentation-mcp-server@latest"],
        )
    )
)

if __name__ == "__main__":
    # MCP のツールはクライアントの接続中だけ有効。with ブロックで囲むのが必須
    with aws_docs_mcp:
        tools = aws_docs_mcp.list_tools_sync()
        print("MCP サーバが提供するツール:", [t.tool_name for t in tools])

        agent = Agent(model=make_model(), tools=tools)
        agent("Amazon Bedrock AgentCore Runtime とは何か、AWS ドキュメントを調べて要約して。")
