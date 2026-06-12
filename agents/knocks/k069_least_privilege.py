"""ノック69: ツール権限の最小化 — read-only モードを許可リストで作る

安全なエージェントの基本は「できることを最小限にする」。
同じツール群でも、文脈に応じて使えるツールを許可リストで絞る。
ここでは「閲覧専用モード」と「管理者モード」を BeforeToolCallEvent で切り替える。

このノックは AWS 不要(モックモデルで動く)。
実行: uv run knocks/k069_least_privilege.py
"""

from mock_model import MockModel, ToolCall

from strands import Agent, tool
from strands.hooks import BeforeToolCallEvent, HookProvider, HookRegistry


@tool
def list_files() -> str:
    """ファイル一覧を表示する(読み取り)。"""
    return "report.txt, data.csv"


@tool
def delete_file(path: str) -> str:
    """ファイルを削除する(書き込み)。"""
    return f"{path} を削除しました"


class AllowList(HookProvider):
    """許可リストにないツールの実行を拒否するフック。"""

    def __init__(self, allowed: set[str]):
        self.allowed = allowed

    def register_hooks(self, registry: HookRegistry, **kwargs) -> None:
        registry.add_callback(BeforeToolCallEvent, self.check)

    def check(self, event: BeforeToolCallEvent) -> None:
        name = event.tool_use["name"]
        if name not in self.allowed:
            event.cancel_tool = f"現在のモードでは {name} は許可されていません"


def make_agent(model, allowed: set[str]) -> Agent:
    return Agent(
        model=model,
        tools=[list_files, delete_file],  # ツール自体は全部持つ
        hooks=[AllowList(allowed)],        # が、許可リストで実行を絞る
        callback_handler=None,
    )


if __name__ == "__main__":
    # 閲覧専用モード: list_files だけ許可
    print("===== 閲覧専用モード =====")
    viewer = make_agent(
        MockModel([ToolCall("delete_file", {"path": "report.txt"}),
                   "申し訳ありません、削除権限がありません。"]),
        allowed={"list_files"},
    )
    viewer("report.txt を削除して。")
    tr = [b["toolResult"] for m in viewer.messages for b in m["content"] if "toolResult" in b]
    print("結果:", tr[0]["status"], "-", str(tr[0]["content"]))

    # 管理者モード: 両方許可
    print("\n===== 管理者モード =====")
    admin = make_agent(
        MockModel([ToolCall("delete_file", {"path": "report.txt"}), "削除しました。"]),
        allowed={"list_files", "delete_file"},
    )
    admin("report.txt を削除して。")
    tr = [b["toolResult"] for m in admin.messages for b in m["content"] if "toolResult" in b]
    print("結果:", tr[0]["status"], "-", str(tr[0]["content"]))
