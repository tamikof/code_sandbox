"""ノック3: モデル設定 — model_id / temperature / max_tokens

同じプロンプトを temperature 0.0 と 1.0 で投げて、出力の「ブレ」を観察する。

実行: uv run knocks/k003_model_config.py
"""

from strands import Agent
from strands.models import BedrockModel

PROMPT = "「春」をテーマに一句、俳句を詠んで。俳句だけを出力して。"

for temperature in (0.0, 1.0):
    print(f"\n===== temperature={temperature} =====")
    # 同じ temperature で2回ずつ実行して再現性を見る
    for i in range(2):
        model = BedrockModel(
            model_id="global.anthropic.claude-sonnet-4-6",
            temperature=temperature,
            max_tokens=100,
        )
        agent = Agent(model=model)
        print(f"--- {i + 1}回目 ---")
        agent(PROMPT)
        print()
