"""ノック82: Swarm 入門 — 自律的なハンドオフ

Agents as Tools(81)は司令塔が中央集権的に振り分ける。Swarm は対等な
エージェント同士が「これは君の担当だ」と自律的にバトンを渡し合う方式。
誰がいつ引き継ぐかはエージェント自身が決める。

実行: uv run knocks/k082_swarm_basics.py
"""

from common import make_model

from strands import Agent
from strands.multiagent import Swarm

# 役割の違う3エージェント。Swarm が各自に handoff ツールを自動で与える
planner = Agent(
    model=make_model(),
    name="planner",
    system_prompt=(
        "あなたは旅行プランナーです。大枠の計画を立てたら、"
        "詳細な予算計算は budgeter に引き継いでください。"
    ),
    callback_handler=None,
)
budgeter = Agent(
    model=make_model(),
    name="budgeter",
    system_prompt=(
        "あなたは予算担当です。費用を見積もったら、"
        "最終的な文章まとめは writer に引き継いでください。"
    ),
    callback_handler=None,
)
writer = Agent(
    model=make_model(),
    name="writer",
    system_prompt="あなたは編集者です。受け取った情報を読みやすい提案書にまとめます。",
    callback_handler=None,
)

if __name__ == "__main__":
    swarm = Swarm([planner, budgeter, writer], entry_point=planner)

    result = swarm("2泊3日の京都旅行プランを、予算込みで提案して。")

    print("\n===== 実行経路 =====")
    for node in result.node_history:
        print(f"→ {node.node_id}")
    print(f"\nステータス: {result.status}")
    # planner → budgeter → writer と自律的にハンドオフされたはず
