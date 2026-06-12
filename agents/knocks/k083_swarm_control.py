"""ノック83: Swarm 制御 — entry point・上限・ループ検出

Swarm は放っておくと無限ハンドオフ(2人が延々と譲り合う)に陥ることがある。
上限とループ検出で暴走を止める。

  - entry_point             : 最初に動くエージェント
  - max_handoffs            : ハンドオフ回数の上限
  - max_iterations          : 総実行回数の上限
  - repetitive_handoff_*    : 同じ相手への往復ループの検出

このノックは AWS 不要(モックモデルで動く)。
実行: uv run knocks/k083_swarm_control.py
"""

from mock_model import MockModel

from strands import Agent
from strands.multiagent import Swarm

if __name__ == "__main__":
    # ハンドオフせず即答するエージェント2体(制御パラメータの効果を見るための単純構成)
    a = Agent(model=MockModel(["担当Aが対応しました"]), name="agent_a",
              description="担当A", callback_handler=None)
    b = Agent(model=MockModel(["担当Bが対応しました"]), name="agent_b",
              description="担当B", callback_handler=None)

    swarm = Swarm(
        [a, b],
        entry_point=a,            # a から開始
        max_handoffs=5,           # ハンドオフは5回まで
        max_iterations=5,         # 総実行は5回まで
        node_timeout=30.0,        # 1ノードが30秒を超えたら打ち切り
        execution_timeout=120.0,  # 全体が120秒を超えたら打ち切り
        # 同じ相手に繰り返しハンドオフするループを検出して止める
        repetitive_handoff_detection_window=4,
        repetitive_handoff_min_unique_agents=2,
    )

    result = swarm("簡単な問い合わせに対応して。")
    print("ステータス:", result.status)
    print("実行経路:", [n.node_id for n in result.node_history])
    print(
        "\n制御パラメータがないと、相性の悪いプロンプト次第で"
        "エージェント同士が延々と譲り合う事故が起きる。本番では必ず上限を設定する。"
    )
