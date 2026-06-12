"""ノック66: Bedrock Guardrails — モデルの外側のコンテンツフィルタ

ガードレールは Bedrock のマネージド機能で、入力・出力を独立に検査する。
NGトピック(例: 投資助言)、NGワード、PII などをモデルの手前/後ろで止める。
プロンプトで「答えるな」と書くのと違い、モデルがどう頑張っても突破できない。

前提: ガードレールを1つ作成しておく(コンソールが簡単)
  例: 「投資助言」を Denied topic にして ID と Version を控える

実行: KNOCK_GUARDRAIL_ID=xxx KNOCK_GUARDRAIL_VERSION=1 uv run knocks/k066_guardrails.py
"""

import os

from common import model_id

from strands import Agent
from strands.models import BedrockModel

if __name__ == "__main__":
    guardrail_id = os.environ.get("KNOCK_GUARDRAIL_ID")
    if not guardrail_id:
        raise SystemExit("環境変数 KNOCK_GUARDRAIL_ID を設定してください")

    model = BedrockModel(
        model_id=model_id(),
        guardrail_id=guardrail_id,
        guardrail_version=os.environ.get("KNOCK_GUARDRAIL_VERSION", "1"),
        guardrail_trace="enabled",  # 何がブロックされたかのトレースを出す
        # guardrail_redact_input=True なら、ブロックされた入力を履歴からも消せる
    )
    agent = Agent(model=model, callback_handler=None)

    print("--- 普通の質問 ---")
    print(agent("おすすめの朝食を教えて。"))

    print("\n--- NGトピックに触れる質問 ---")
    result = agent("確実に儲かる株を教えて。")
    print(result)
    print("stop_reason:", result.stop_reason)  # ブロック時は guardrail_intervened
