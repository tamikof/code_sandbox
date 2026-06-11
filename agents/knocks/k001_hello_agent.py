"""ノック1: Hello Agent — 最小のエージェント

実行: uv run knocks/k001_hello_agent.py
"""

from common import make_model

from strands import Agent

# Agent() だけでも動く(その場合はデフォルトの Claude Sonnet が使われる)が、
# このノック集ではコスト節約のため Haiku を明示する。knocks/common.py 参照。
agent = Agent(model=make_model())

agent("こんにちは!あなたは何ができますか?3行で教えて。")
