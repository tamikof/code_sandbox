"""ノック61: Anthropic 直接続 — Bedrock を経由せず API を直叩きする

モデルプロバイダの差し替えはオブジェクトを替えるだけ。コードの他の部分
(ツール、フック、セッション...)は一切変わらない。これが Strands の
「モデル非依存」設計の価値。

前提: pyproject の strands-agents[anthropic] extra(インストール済み)
実行: ANTHROPIC_API_KEY=sk-ant-... uv run knocks/k061_anthropic_direct.py
"""

import os

from strands import Agent
from strands.models.anthropic import AnthropicModel

if __name__ == "__main__":
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit("環境変数 ANTHROPIC_API_KEY を設定してください")

    model = AnthropicModel(
        # client_args={"api_key": "..."} でも渡せるが、環境変数が自動で使われる
        model_id="claude-haiku-4-5",  # Anthropic API のモデルID (Bedrock とは形式が違う)
        max_tokens=1024,
    )

    agent = Agent(model=model)
    agent("BedrockとAnthropic API直接続、それぞれの利点を2つずつ挙げて。")
