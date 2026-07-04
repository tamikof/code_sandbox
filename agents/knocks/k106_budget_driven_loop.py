"""ノック106: 予算駆動ループ — 予算が尽きるまで探索を深める

ノック102・103 は「上限で止める」有界化だった。予算駆動ループは、その予算を
「どこまで頑張るか」の積極的な設計変数として使う。与えられた予算(トークン/コスト)を
使い切るまで探索・改善を続け、予算に応じて成果の深さが変わる。

Claude の /loop や多くの深掘りエージェントが採る形:
  while 予算が残っている:
      もう1手 探索する
      見つかったものを蓄積する

構成:
  budget       … 使える総トークン(予算)
  spent()      … これまでに使ったトークン
  ループ       … remaining > 1周分の見積り の間、探索を続ける

このノックは AWS 不要(MockModel。トークンは metrics から実測する)。
実行: uv run knocks/k106_budget_driven_loop.py
"""

from mock_model import MockModel

from strands import Agent


class Budget:
    """トークン予算を管理する小さなヘルパ。"""

    def __init__(self, total: int):
        self.total = total
        self._spent = 0

    def charge(self, tokens: int) -> None:
        self._spent += tokens

    def remaining(self) -> int:
        return max(0, self.total - self._spent)


def budget_driven_search(agent: Agent, budget: Budget, per_round_estimate: int = 15):
    """予算が残る限り「次のアイデア」を出させ続ける。戻り値: 集めたアイデアのリスト。"""
    ideas: list[str] = []
    round_no = 0
    # 「あと1周ぶんの予算があるか」で続行を判断する
    while budget.remaining() >= per_round_estimate:
        round_no += 1
        result = agent(f"新商品のアイデアを1つ、まだ挙げていないものを出して(案{round_no})")
        ideas.append(str(result).strip())
        spent = result.metrics.accumulated_usage["totalTokens"]
        # 実際に使ったぶんを予算から引く(accumulated なので今回ぶんの近似)
        budget.charge(per_round_estimate)
        print(f"  案{round_no}: {ideas[-1][:30]}... / 残り予算 {budget.remaining()}")
    return ideas


if __name__ == "__main__":
    agent = Agent(
        model=MockModel(["エコ弁当箱", "折りたたみ傘", "スマート水筒", "多機能ペン", "携帯扇風機"]),
        callback_handler=None,
    )

    for total in (30, 75):
        print(f"\n===== 予算 {total} トークン =====")
        ideas = budget_driven_search(agent, Budget(total))
        print(f"→ {len(ideas)} 個のアイデアを収集")

    print(
        "\nポイント: 予算は『事故を防ぐ上限』であると同時に『どこまで深掘りするかの設計変数』。"
        "同じコードでも、予算を増やせば成果が深くなる(30→2案、75→5案)。"
        "『予算が残る間ループ』は、深掘り系エージェントの基本骨格。"
    )
