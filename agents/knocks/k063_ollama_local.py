"""ノック63: ローカルLLM — Ollama でクラウドなしのエージェント

API キーもクラウドも不要。機密データを外に出せない環境や、
開発中の高速な試行錯誤に向く。ツールも普通に使える(モデルの能力次第)。

前提:
  1. https://ollama.com からインストール
  2. ollama pull qwen3:4b   (ツール対応の軽量モデル)
  3. ollama serve           (常駐していなければ)

実行: uv run knocks/k063_ollama_local.py
"""

from strands import Agent, tool
from strands.models.ollama import OllamaModel


@tool
def get_time() -> str:
    """現在時刻を返す。"""
    from datetime import datetime

    return datetime.now().strftime("%H:%M")


if __name__ == "__main__":
    model = OllamaModel(
        host="http://localhost:11434",
        model_id="qwen3:4b",
    )

    agent = Agent(model=model, tools=[get_time])
    agent("いま何時?ツールで調べて一言コメントして。")
    # クラウドモデルとの応答品質・速度・ツール選択精度の差を体感する
