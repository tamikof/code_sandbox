"""ノック4: モデル比較 — 同じプロンプトを複数モデルに投げる

モデルによって応答の質・スタイル・速度がどう変わるかを体感する。
使えるモデルはリージョンと Bedrock のモデルアクセス設定に依存するので、
エラーになったら MODEL_IDS を自分の環境で有効なものに書き換えること。

実行: uv run knocks/k004_model_compare.py
"""

import time

from strands import Agent
from strands.models import BedrockModel

MODEL_IDS = [
    "global.anthropic.claude-sonnet-4-6",  # SDK のデフォルト
    "us.amazon.nova-lite-v1:0",            # 軽量・高速なモデル
]

PROMPT = "再帰関数を小学生にもわかるように2文で説明して。"

for model_id in MODEL_IDS:
    print(f"\n===== {model_id} =====")
    agent = Agent(model=BedrockModel(model_id=model_id))
    start = time.perf_counter()
    agent(PROMPT)
    elapsed = time.perf_counter() - start
    print(f"\n(所要時間: {elapsed:.2f}秒)")
