"""ノック19: HTTP リクエスト — 外部 API を叩くエージェント

http_request ツールは GET/POST 等を実行し、レスポンスをモデルに返す。
「APIを叩いて結果を解釈して説明する」がエージェントの定番パターン。

実行: uv run knocks/k019_http_request.py
"""

from common import make_model
from strands_tools import http_request

from strands import Agent

if __name__ == "__main__":
    agent = Agent(model=make_model(), tools=[http_request])

    # 認証不要の公開APIで試す
    agent(
        "https://api.github.com/repos/strands-agents/sdk-python を GET して、"
        "このリポジトリのスター数と説明を教えて。"
    )
