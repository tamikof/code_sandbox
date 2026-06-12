"""ノック50: スナップショット — エージェントの状態を丸ごと保存・復元する

take_snapshot() は messages / state / 会話マネージャの状態などを
1つのスナップショットに固めて返す。ノック40で手作りした「保存・復元」の
公式版で、新しめの機能。チェックポイント(やり直し地点)として使える。

このノックは AWS 不要(モックモデルで動く)。
実行: uv run knocks/k050_snapshot.py
"""

from mock_model import MockModel

from strands import Agent

if __name__ == "__main__":
    agent = Agent(
        model=MockModel(["了解、和食で考えます", "提案: 肉じゃが定食", "提案: 麻婆豆腐定食"]),
        callback_handler=None,
    )

    print(agent("夕食の献立を考えたい。和食でお願い。"))
    agent.state.set("cuisine", "和食")

    # ここを「やり直し地点」として保存
    checkpoint = agent.take_snapshot(preset="session")
    print(f"チェックポイント保存(履歴 {len(agent.messages)}件)")

    print(agent("1つ提案して。"))
    print(f"提案後の履歴: {len(agent.messages)}件")

    # 提案が気に入らなかったので、チェックポイントまで巻き戻す
    agent.load_snapshot(checkpoint)
    print(f"\n--- 巻き戻し(履歴 {len(agent.messages)}件 / state: {agent.state.get('cuisine')}) ---")
    print(agent("やっぱり中華で1つ提案して。"))

    # 用途: A/Bで応答を試す、失敗したら巻き戻す、会話の分岐を作る…
    # 第6章のセッションマネージャは、この保存・復元を自動化したもの
