"""ノック51: ファイルセッション — FileSessionManager で会話を自動永続化する

ノック40では messages を手で保存した。FileSessionManager を渡すだけで、
会話・state・会話マネージャの状態がターンごとに自動でディスクに保存される。

実行: uv run knocks/k051_file_session.py
"""

from pathlib import Path

from common import make_model

from strands import Agent
from strands.session.file_session_manager import FileSessionManager

STORAGE = "/tmp/knock-sessions"

if __name__ == "__main__":
    agent = Agent(
        model=make_model(),
        session_manager=FileSessionManager(session_id="knock51", storage_dir=STORAGE),
        callback_handler=None,
    )

    print(agent("私の名前はタミコです。覚えておいて。"))
    agent.state.set("favorite", "寿司")  # state もセッションに含まれる
    print(agent("好きな食べ物は寿司です。"))

    # 保存されたファイルを覗いてみる
    print("\n===== 保存されたファイル =====")
    for path in sorted(Path(STORAGE).rglob("*.json")):
        print(path)
    # session.json / agent.json / messages/message_N.json という構造。
    # ノック40で手作りした仕組みの完成形がこれ
