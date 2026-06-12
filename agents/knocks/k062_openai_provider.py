"""ノック62: OpenAI プロバイダ — OpenAI および互換 API への接続

OpenAIModel は base_url を差し替えれば OpenAI 互換 API
(Azure OpenAI、vLLM、LM Studio など)にも繋がる。

実行: OPENAI_API_KEY=sk-... uv run knocks/k062_openai_provider.py
"""

import os

from strands import Agent
from strands.models.openai import OpenAIModel

if __name__ == "__main__":
    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("環境変数 OPENAI_API_KEY を設定してください")

    model = OpenAIModel(
        # 互換APIなら client_args={"base_url": "http://localhost:8000/v1"} を足す
        model_id="gpt-4o-mini",
        params={"max_tokens": 1024},
    )

    agent = Agent(model=model)
    agent("自己紹介して。あなたはどのモデル?")
