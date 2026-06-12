"""ノック48: メッセージへの介入 — MessageAddedEvent で履歴追加を捕捉する

履歴(messages)に1件追加されるたびに発火するフック。
会話ログの外部保存、内容の検査、リアルタイム分析の入口になる。

実行: uv run knocks/k048_message_hook.py
"""

from common import make_model

from strands import Agent
from strands.hooks import HookProvider, HookRegistry, MessageAddedEvent


class ConversationRecorder(HookProvider):
    """追加されたメッセージを記録する(DB保存の代わりにリストへ)。"""

    def __init__(self):
        self.records: list[str] = []

    def register_hooks(self, registry: HookRegistry, **kwargs) -> None:
        registry.add_callback(MessageAddedEvent, self.on_message)

    def on_message(self, event: MessageAddedEvent) -> None:
        message = event.message
        text = "".join(block.get("text", "") for block in message["content"])
        self.records.append(f"{message['role']}: {text[:50]}")
        print(f"[recorder] {message['role']} のメッセージを記録({len(text)}文字)")


if __name__ == "__main__":
    recorder = ConversationRecorder()
    agent = Agent(model=make_model(), hooks=[recorder], callback_handler=None)

    print(agent("こんにちは!"))
    print(agent("今日の晩ごはんのおすすめは?"))

    print("\n===== 記録された会話 =====")
    for record in recorder.records:
        print(record)
