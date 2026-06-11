"""ノック1: Hello Agent — 最小のエージェント

実行: uv run knocks/k001_hello_agent.py
"""

from strands import Agent

# 引数なしの Agent() はデフォルトモデル(Bedrock の Claude)を使う。
# 呼び出すと応答がストリーミングでそのまま標準出力に流れる。
agent = Agent()

agent("こんにちは!あなたは何ができますか?3行で教えて。")
