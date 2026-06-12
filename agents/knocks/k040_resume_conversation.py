"""ノック40: 会話の復元 — messages を保存して別プロセスで再開する

会話の実体は messages のリスト(ノック6)。これを JSON で保存し、
新しい Agent の messages 引数に渡せば会話の続きから再開できる。
第6章のセッションマネージャは、これを自動でやってくれる仕組み。

実行: uv run knocks/k040_resume_conversation.py
"""

import json
from pathlib import Path

from common import make_model

from strands import Agent

SAVE_FILE = Path("/tmp/knock40_conversation.json")


def save_conversation(agent: Agent, path: Path) -> None:
    """会話履歴を JSON ファイルに保存する。"""
    path.write_text(json.dumps(agent.messages, ensure_ascii=False, indent=2))


def load_conversation(path: Path) -> list:
    """保存した会話履歴を読み込む。"""
    return json.loads(path.read_text()) if path.exists() else []


if __name__ == "__main__":
    # --- 1回目の会話 ---
    agent = Agent(model=make_model(), callback_handler=None)
    print(agent("私の名前はタミコです。覚えておいて。"))
    save_conversation(agent, SAVE_FILE)
    print(f"\n会話を保存しました: {SAVE_FILE}({len(agent.messages)}件)")

    # --- プロセスが再起動した想定。履歴から新しいエージェントを作る ---
    del agent
    restored = Agent(
        model=make_model(),
        messages=load_conversation(SAVE_FILE),  # ここで過去を注入
        callback_handler=None,
    )
    print("\n--- 復元したエージェントで継続 ---")
    print(restored("私の名前を覚えていますか?"))
