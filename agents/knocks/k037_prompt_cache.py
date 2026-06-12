"""ノック37: プロンプトキャッシュ — 長いシステムプロンプトのコストを削減する

巨大なシステムプロンプト(社内規定、ペルソナ定義、Few-shot例など)を
毎ターン全額払うのはもったいない。Bedrock のプロンプトキャッシュを使うと
2回目以降はキャッシュ読み取り料金(約1/10)になる。

注意: キャッシュには最低トークン数(Haiku 4.5 は約2048トークン)があり、
それ未満のプロンプトは黙ってキャッシュされない。

実行: uv run knocks/k037_prompt_cache.py
"""

from common import model_id

from strands import Agent
from strands.models import BedrockModel

# わざと長いシステムプロンプトを作る(実務では社内規定や Few-shot 例が入る想定)
LONG_RULES = "\n".join(
    f"ルール{i}: お客様への回答では、専門用語{i}を使う場合は必ず平易な説明を添えること。"
    for i in range(1, 201)
)

if __name__ == "__main__":
    model = BedrockModel(
        model_id=model_id(),
        cache_prompt="default",  # システムプロンプトをキャッシュする
    )
    agent = Agent(
        model=model,
        system_prompt=f"あなたはサポート担当です。以下の社内ルールに従ってください。\n{LONG_RULES}",
        callback_handler=None,
    )

    for i in (1, 2):
        result = agent("こんにちは。一言で挨拶して。")
        usage = result.metrics.accumulated_usage
        print(
            f"{i}回目: 入力 {usage['inputTokens']} / "
            f"キャッシュ書込 {usage.get('cacheWriteInputTokens', 0)} / "
            f"キャッシュ読取 {usage.get('cacheReadInputTokens', 0)}"
        )

    # 1回目: cacheWrite に大きな値(キャッシュ作成 = 約1.25倍の料金)
    # 2回目: cacheRead に大きな値(約0.1倍の料金)→ ここで元が取れる
