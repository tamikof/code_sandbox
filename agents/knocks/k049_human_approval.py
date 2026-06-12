"""ノック49: 人間の承認フロー — 危険な操作の前で止める (human-in-the-loop)

ノック46の cancel_tool を応用し、「危険なツールは実行前に人間へ確認する」
フックを作る。承認の取り方(approver)は差し替え可能にしておく:
  - ターミナルなら input()
  - WebUI なら確認ダイアログ(第10章)
  - テストなら固定値を返す関数(tests/test_chapter05.py)

実行: uv run knocks/k049_human_approval.py
"""

from typing import Callable

from common import make_model

from strands import Agent, tool
from strands.hooks import BeforeToolCallEvent, HookProvider, HookRegistry


@tool
def send_invoice(to: str, amount: int) -> str:
    """請求書を送付する(取り消せない操作)。"""
    return f"{to} に {amount}円の請求書を送付しました"


class ApprovalHook(HookProvider):
    """指定したツールの実行前に承認を求めるフック。"""

    def __init__(self, dangerous_tools: set[str], approver: Callable[[str, dict], bool]):
        self.dangerous_tools = dangerous_tools
        self.approver = approver  # (ツール名, 引数) -> 承認するか

    def register_hooks(self, registry: HookRegistry, **kwargs) -> None:
        registry.add_callback(BeforeToolCallEvent, self.confirm)

    def confirm(self, event: BeforeToolCallEvent) -> None:
        name = event.tool_use["name"]
        if name not in self.dangerous_tools:
            return  # 安全なツールは素通し
        if not self.approver(name, event.tool_use["input"]):
            event.cancel_tool = "ユーザーが操作を承認しませんでした"


def console_approver(name: str, tool_input: dict) -> bool:
    """ターミナルで y/n を聞く承認関数。"""
    answer = input(f"\n⚠ {name}({tool_input}) を実行しますか? [y/N]: ")
    return answer.strip().lower() == "y"


if __name__ == "__main__":
    agent = Agent(
        model=make_model(),
        tools=[send_invoice],
        hooks=[ApprovalHook({"send_invoice"}, console_approver)],
    )

    agent("田中商事に 50000円の請求書を送って。")
    # n を入力すると: ツールは実行されず、モデルは「承認されなかった」と認識して引き下がる
