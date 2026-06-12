"""ノック64: LiteLLM — 100以上のプロバイダを統一インターフェースで

LiteLLM は各社 API の差異を吸収するゲートウェイライブラリ。
model_id のプレフィックスを変えるだけでプロバイダを切り替えられる。
「将来どのモデルに乗り換えるか分からない」案件の保険として定番。

実行例:
  GEMINI_API_KEY=...    uv run knocks/k064_litellm.py gemini/gemini-2.0-flash
  ANTHROPIC_API_KEY=... uv run knocks/k064_litellm.py anthropic/claude-haiku-4-5
  (Bedrock 経由なら)    uv run knocks/k064_litellm.py bedrock/global.anthropic.claude-haiku-4-5-20251001-v1:0
"""

import sys

from strands import Agent
from strands.models.litellm import LiteLLMModel

if __name__ == "__main__":
    model_id = sys.argv[1] if len(sys.argv) > 1 else "gemini/gemini-2.0-flash"
    print(f"モデル: {model_id}\n")

    model = LiteLLMModel(model_id=model_id, params={"max_tokens": 1024})
    agent = Agent(model=model)
    agent("こんにちは。あなたはどの会社のなんというモデル?一言で。")
