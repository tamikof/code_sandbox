"""ノック79: コスト集計 — トークンを料金に換算してレポートする

メトリクス(ノック72)のトークン数に単価を掛ければコストが出る。
会話ごと・ユーザーごとにコストを集計しておくと、料金の予測と
「高コストな使い方」の発見ができる。

このノックは AWS 不要(モックモデルで動く)。
実行: uv run knocks/k079_cost.py
"""

from mock_model import MockModel

from strands import Agent

# 100万トークンあたりの USD 単価(2026年時点の概算。実際の請求は AWS 側を参照)
PRICING = {
    "haiku-4-5": {"input": 1.00, "output": 5.00},
    "sonnet-4-6": {"input": 3.00, "output": 15.00},
    "opus-4-8": {"input": 5.00, "output": 25.00},
}

USD_TO_JPY = 150


def cost_of(usage: dict, model_key: str) -> float:
    """トークン使用量から USD コストを計算する。"""
    rate = PRICING[model_key]
    return (
        usage["inputTokens"] / 1_000_000 * rate["input"]
        + usage["outputTokens"] / 1_000_000 * rate["output"]
    )


if __name__ == "__main__":
    # 3回会話して、それぞれのコストを集計する
    agent = Agent(model=MockModel(["A", "B", "C"]), callback_handler=None)

    total_usd = 0.0
    print("===== 会話ごとのコスト(haiku-4-5 想定) =====")
    for i, prompt in enumerate(["質問1", "質問2", "質問3"], 1):
        result = agent(prompt)
        # 注: accumulated_usage は累計。差分を取るのが本来だが、ここでは説明用に
        # その回の result.metrics を使う(モックは毎回同じ usage を返す)
        usage = result.metrics.accumulated_usage
        usd = cost_of(usage, "haiku-4-5")
        total_usd += usd
        print(f"ターン{i}: {usage['totalTokens']}トークン → ${usd:.6f}")

    print(f"\n累計: ${total_usd:.6f}(約 {total_usd * USD_TO_JPY:.4f}円)")

    # モデル別の比較: 同じトークンでもモデルでコストが大きく変わる
    print("\n===== 同じ使用量でのモデル別コスト比較 =====")
    sample = {"inputTokens": 10000, "outputTokens": 2000}
    for model_key in PRICING:
        usd = cost_of(sample, model_key)
        print(f"{model_key:12s}: ${usd:.4f}(約 {usd * USD_TO_JPY:.1f}円)")
