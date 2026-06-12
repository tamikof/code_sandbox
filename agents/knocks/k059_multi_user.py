"""ノック59: マルチユーザー分離 — ユーザーごとにセッションを分ける

WebUI のバックエンドでは複数ユーザーが同時に来る。鉄則は1つ:
**session_id をユーザー(+会話)ごとに分け、エージェントを使い回さない**。

このノックは AWS 不要(モックモデルで動く)。
実行: uv run knocks/k059_multi_user.py
"""

from mock_model import MockModel

from strands import Agent
from strands.session.file_session_manager import FileSessionManager

STORAGE = "/tmp/knock59-sessions"


def agent_for(user_id: str, conversation_id: str, model) -> Agent:
    """リクエストのたびに、そのユーザーのセッションを背負ったエージェントを作る。

    エージェント自体は毎回作り直してよい(安い)。
    会話の実体はセッションストレージ側にあるので、何も失われない。
    """
    return Agent(
        model=model,
        # ユーザーIDと会話IDを組み合わせて完全に分離する
        session_manager=FileSessionManager(
            session_id=f"{user_id}--{conversation_id}", storage_dir=STORAGE
        ),
        callback_handler=None,
    )


if __name__ == "__main__":
    # --- ユーザーAのリクエスト ---
    agent = agent_for("alice", "conv-1", MockModel(["アリスさんですね、覚えました"]))
    agent("私はアリス。趣味は登山です。")

    # --- ユーザーBのリクエスト(別セッションなのでAの情報は見えない) ---
    agent = agent_for("bob", "conv-1", MockModel(["ボブさんですね、覚えました"]))
    agent("私はボブ。趣味は釣りです。")

    # --- ユーザーAが戻ってきた(新しいプロセス/リクエストの想定) ---
    agent = agent_for("alice", "conv-1", MockModel(["アリスさんの趣味は登山ですね"]))
    print(f"アリスの履歴: {len(agent.messages)}件(ボブの発言は混ざっていない)")
    print(agent("私の趣味は何だった?"))

    # 確認: ストレージにはユーザー×会話ごとのディレクトリができている
    from pathlib import Path

    print("\nセッション一覧:", sorted(p.name for p in Path(STORAGE).iterdir()))
