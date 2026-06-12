"""ノック89: A2A クライアント — リモートのエージェントを呼ぶ

ノック88で公開した A2A サーバに、別のエージェントから接続して仕事を頼む。
A2AClientToolProvider が「リモートエージェントを発見して話す」ツール一式を提供する。
これにより、ローカルのオーケストレーターがリモートの専門エージェントを
あたかも自分のツールのように使える(分散マルチエージェント)。

前提:
  1. uv add strands-agents-tools[a2a_client]
  2. 別ターミナルで uv run knocks/k088_a2a_server.py を起動しておく

実行: uv run knocks/k089_a2a_client.py
"""

from common import make_model
from strands_tools.a2a_client import A2AClientToolProvider

from strands import Agent

if __name__ == "__main__":
    # 既知の A2A サーバ URL を渡すと、発見・通信ツールが使えるようになる
    provider = A2AClientToolProvider(known_agent_urls=["http://127.0.0.1:9000"])

    # ローカルのオーケストレーターが、リモートのレシピ専門家を使う
    orchestrator = Agent(model=make_model(), tools=provider.tools)

    orchestrator(
        "カレーの作り方を知りたい。利用可能なリモートエージェントを探して、"
        "レシピの専門家に聞いて、結果を教えて。"
    )
    # a2a_discover_agent でサーバを発見 → a2a_send_message でレシピを問い合わせる、
    # という流れをオーケストレーターが自分で組み立てる
