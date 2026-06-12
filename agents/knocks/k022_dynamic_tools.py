"""ノック22: 動的ツール管理 — 実行中にツールを追加する

ツールは Agent 生成時に固定ではなく、tool_registry を通じて後から追加できる。
「権限が付与されたらツールを増やす」「プラグインを動的に読み込む」といった
場面で使うパターン。

実行: uv run knocks/k022_dynamic_tools.py
"""

from common import make_model

from strands import Agent, tool


@tool
def read_balance(account: str) -> str:
    """口座残高を照会する(読み取り専用)。"""
    return f"{account} の残高: 123,456円"


@tool
def transfer_money(to_account: str, amount: int) -> str:
    """指定口座へ送金する(危険な操作)。"""
    return f"{to_account} へ {amount}円 送金しました"


if __name__ == "__main__":
    # 最初は読み取り専用ツールだけ
    agent = Agent(model=make_model(), tools=[read_balance])
    print("初期ツール:", agent.tool_names)

    agent("A口座から B口座へ 1000円送金して。")  # → ツールがないので断られる

    # 認証が済んだ想定で、送金ツールを後から追加
    agent.tool_registry.register_tool(transfer_money)
    print("\n追加後のツール:", agent.tool_names)

    agent("もう一度: A口座から B口座へ 1000円送金して。")
