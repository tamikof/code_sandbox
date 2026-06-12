"""ノック52: プロセス再起動テスト — 同じ session_id で会話が続くことを確認する

このスクリプトを「2回以上」実行する。
同じ session_id を指定する限り、プロセスを再起動しても会話は続いている。

実行: uv run knocks/k052_session_restart.py   ← 2回実行する
リセット: rm -rf /tmp/knock-sessions/session_knock52
"""

from common import make_model

from strands import Agent
from strands.session.file_session_manager import FileSessionManager

if __name__ == "__main__":
    agent = Agent(
        model=make_model(),
        session_manager=FileSessionManager(
            session_id="knock52", storage_dir="/tmp/knock-sessions"
        ),
        callback_handler=None,
    )

    run_count = len(agent.messages) // 2 + 1
    print(f"これまでの履歴: {len(agent.messages)}件(おそらく {run_count} 回目の起動)\n")

    if not agent.messages:
        print(agent("私の名前はタミコで、北海道旅行を計画中です。覚えておいて。"))
        print("\n→ もう一度このスクリプトを実行してみてください。")
    else:
        print(agent("私が誰で、何を計画していたか覚えていますか?"))
        # 新しいプロセスなのに覚えている。Agent 生成時に session_id のデータが
        # 自動で読み込まれているから
