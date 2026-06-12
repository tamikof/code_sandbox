"""ノック93: AgentCore Gateway — 既存 API を MCP ツールに変える

社内にある REST API や Lambda を、エージェントのツールにしたい。
Gateway は OpenAPI 仕様や Lambda を「MCP サーバ」として公開してくれる
マネージドサービス。エージェント側は第3章の MCP 接続(ノック27)と同じ
要領で繋ぐだけ。

このノックは「接続の形」を示すコード。実際には Gateway を作成して
エンドポイント URL とアクセストークンを得る必要がある。

前提: Gateway を作成し、OpenAPI ターゲットを登録しておく
実行: KNOCK_GATEWAY_URL=https://...amazonaws.com/mcp \\
      KNOCK_GATEWAY_TOKEN=xxx uv run knocks/k093_agentcore_gateway.py
"""

import os

from common import make_model
from mcp.client.streamable_http import streamablehttp_client

from strands import Agent
from strands.tools.mcp import MCPClient

if __name__ == "__main__":
    gateway_url = os.environ.get("KNOCK_GATEWAY_URL")
    token = os.environ.get("KNOCK_GATEWAY_TOKEN")
    if not (gateway_url and token):
        raise SystemExit("KNOCK_GATEWAY_URL と KNOCK_GATEWAY_TOKEN を設定してください")

    # Gateway は MCP サーバ。第3章の HTTP 接続に認証ヘッダを足すだけ
    gateway = MCPClient(
        lambda: streamablehttp_client(
            gateway_url,
            headers={"Authorization": f"Bearer {token}"},
        )
    )

    with gateway:
        tools = gateway.list_tools_sync()
        print("Gateway 経由で使えるツール:", [t.tool_name for t in tools])

        agent = Agent(model=make_model(), tools=tools)
        agent("利用可能な社内ツールを使って、注文 ID 12345 の状況を調べて。")
    # ポイント: 既存 API を1行も書き換えずにエージェントから使えるようになる。
    # 認証・スキーマ変換・スケーリングは Gateway がマネージドで面倒を見る
