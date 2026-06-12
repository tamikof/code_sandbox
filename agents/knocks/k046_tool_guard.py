"""ノック46: ツール呼び出しの検証 — BeforeToolCallEvent で検査・書き換え・拒否

モデルが組み立てたツール引数を、実行前にコードでチェックする。
LLM の判断をそのまま信用しない「最後の砦」をフックで作る。

  - 検証: 引数がポリシー違反なら event.cancel_tool = "理由" で拒否
        (ツールは実行されず、理由が error 結果としてモデルに返る)
  - 書き換え: event.tool_use["input"] を直接編集できる

実行: uv run knocks/k046_tool_guard.py
"""

from common import make_model

from strands import Agent, tool
from strands.hooks import BeforeToolCallEvent, HookProvider, HookRegistry


@tool
def read_file(path: str) -> str:
    """ファイルの中身を読む。"""
    return f"({path} の中身...)"


class FileAccessGuard(HookProvider):
    """ /etc 配下へのアクセスを拒否し、相対パスは /workspace 起点に正規化する。"""

    def register_hooks(self, registry: HookRegistry, **kwargs) -> None:
        registry.add_callback(BeforeToolCallEvent, self.check)

    def check(self, event: BeforeToolCallEvent) -> None:
        if event.tool_use["name"] != "read_file":
            return
        path = event.tool_use["input"].get("path", "")

        if path.startswith(("/etc", "/root")) or ".." in path:
            # 拒否: ツールは実行されない。この文字列が error 結果になる
            event.cancel_tool = f"ポリシー違反: {path} へのアクセスは禁止されています"
            print(f"[guard] 拒否: {path}")
        elif not path.startswith("/"):
            # 書き換え: モデルの引数を正規化してから実行させる
            event.tool_use["input"]["path"] = f"/workspace/{path}"
            print(f"[guard] 正規化: {path} → /workspace/{path}")


if __name__ == "__main__":
    agent = Agent(model=make_model(), tools=[read_file], hooks=[FileAccessGuard()])

    agent("notes.txt を読んで。")          # → /workspace/notes.txt に正規化される
    print("\n" + "=" * 40 + "\n")
    agent("/etc/passwd を読んで。")        # → 拒否され、モデルは謝るか代替案を出す
