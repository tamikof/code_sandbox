"""ノック14: ツールのエラー処理 — 例外が起きたときのリカバリを観察する

ツール内の例外は status=error の toolResult としてモデルに渡る。
モデルはエラーメッセージを読んで、謝る・別の方法を試す・聞き返す、を自分で選ぶ。

実行: uv run knocks/k014_tool_errors.py
"""

from common import make_model

from strands import Agent, tool


@tool
def divide(a: float, b: float) -> float:
    """a を b で割る。b が 0 の場合はエラーになる。"""
    return a / b  # b=0 なら ZeroDivisionError がそのまま飛ぶ


if __name__ == "__main__":
    agent = Agent(model=make_model(), tools=[divide])

    agent("10 ÷ 0 を divide ツールで計算して。")

    # エラー後の履歴を確認: toolResult の status が "error" になっている
    print("\n===== ツール結果の履歴 =====")
    for message in agent.messages:
        for block in message["content"]:
            if "toolResult" in block:
                print(block["toolResult"])
