"""ノック35: エージェント状態 — agent.state の読み書き

会話履歴(messages)はモデルに毎回送られるが、agent.state は送られない。
「モデルに見せる必要はないがアプリとして保持したい情報」の置き場所。
  - 履歴: モデルが見る。会話管理で消えることがある
  - state: モデルは見ない。会話管理の影響を受けない。セッション保存の対象(第6章)

実行: uv run knocks/k035_agent_state.py
"""

from common import make_model

from strands import Agent

if __name__ == "__main__":
    agent = Agent(
        model=make_model(),
        state={"user_id": "u-001", "visit_count": 3},  # 初期状態を渡せる
        callback_handler=None,
    )

    # state の読み書きは get / set / delete
    agent.state.set("plan", "premium")
    print("user_id    :", agent.state.get("user_id"))
    print("plan       :", agent.state.get("plan"))
    print("全体       :", agent.state.get())

    # state はモデルには送られていない → モデルは user_id を知らない
    print("\nモデルに聞いてみる:")
    print(agent("私の user_id を知っていますか?"))

    # モデルに使わせたいなら、ツール経由 (ノック16の ToolContext) か
    # プロンプトに明示的に埋め込むかのどちらか
    print(agent(f"あなたへのメモ: このユーザーのプランは {agent.state.get('plan')} です。"
                "私のプランは何ですか?"))
