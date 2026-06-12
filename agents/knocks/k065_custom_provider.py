"""ノック65: カスタムプロバイダ — Model インターフェースを自分で実装する

対応プロバイダがない社内LLM・独自API には、Model を継承した
プロバイダを書けば接続できる。実装するのは実質 stream() ひとつ:
リクエストを変換して送り、応答を「ストリームイベント」に変換して yield する。

ここでは外部APIの代わりに、ルールベースで応答する RuleBasedModel を作って
インターフェースの要点だけを学ぶ(テストで使った MockModel も同じ作り)。

このノックは AWS 不要。
実行: uv run knocks/k065_custom_provider.py
"""

from typing import Any

from strands import Agent
from strands.models.model import Model


class RuleBasedModel(Model):
    """キーワードに反応するだけの「モデル」。LLM は使わない。

    本物のプロバイダを書くときは、stream() の中で
      1. messages / tool_specs / system_prompt を自社APIのリクエスト形式に変換
      2. API を呼ぶ(ストリーミング)
      3. 届いたチャンクを以下のイベント形式に変換して yield
    という3ステップになる。
    """

    RULES = {
        "天気": "本日は快晴です(ルールベース応答)",
        "時刻": "午後3時です(ルールベース応答)",
    }

    def get_config(self) -> dict[str, Any]:
        return {"model_id": "rule-based-v1"}

    def update_config(self, **kwargs: Any) -> None:
        pass

    async def structured_output(self, output_model, prompt, system_prompt=None, **kwargs):
        raise NotImplementedError("このプロバイダは structured output 非対応")
        yield

    async def stream(self, messages, tool_specs=None, system_prompt=None, **kwargs):
        # 1. リクエストの変換(ここでは最後のユーザー発言を取るだけ)
        last_user_text = "".join(
            block.get("text", "") for block in messages[-1]["content"]
        )

        # 2. 「推論」(ここではルールマッチ)
        reply = next(
            (answer for keyword, answer in self.RULES.items() if keyword in last_user_text),
            "すみません、天気か時刻のことしか分かりません(ルールベース応答)",
        )

        # 3. ストリームイベントへの変換(この形式は Bedrock Converse 互換)
        yield {"messageStart": {"role": "assistant"}}
        for char in reply:  # 1文字ずつ流してストリーミングらしさを出す
            yield {"contentBlockDelta": {"delta": {"text": char}}}
        yield {"contentBlockStop": {}}
        yield {"messageStop": {"stopReason": "end_turn"}}
        yield {
            "metadata": {
                "usage": {"inputTokens": 0, "outputTokens": len(reply), "totalTokens": len(reply)},
                "metrics": {"latencyMs": 0},
            }
        }


if __name__ == "__main__":
    agent = Agent(model=RuleBasedModel())

    agent("今日の天気は?")
    print()
    agent("好きな食べ物は?")
    # Agent / ストリーミング / フック / セッション、すべてこの自作モデルでも動く。
    # Strands の機能はモデルが何であるかに依存していない
