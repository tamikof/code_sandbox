"""ノック21: ツールの直接呼び出し — agent.tool.xxx() で強制実行する

モデルに「使うかどうか」を委ねず、コード側からツールを確実に実行したいときは
agent.tool.<ツール名>(引数) で直接呼べる。実行結果はデフォルトで会話履歴にも
記録されるので、その後の会話でモデルは「ツールを使った」前提で話せる。

実行: uv run knocks/k021_direct_tool_call.py
"""

from common import make_model

from strands import Agent, tool


@tool
def get_user_plan(user_id: str) -> str:
    """ユーザーの契約プランを取得する。"""
    return {"u-001": "プレミアム", "u-002": "フリー"}.get(user_id, "不明")


if __name__ == "__main__":
    # record_direct_tool_call=True (デフォルト) なら直接呼び出しも履歴に残る
    agent = Agent(model=make_model(), tools=[get_user_plan])

    # ログイン処理などアプリ側で確定している情報は、モデルに任せず直接実行する
    result = agent.tool.get_user_plan(user_id="u-001")
    print("直接呼び出しの結果:", result["status"], result["content"])

    # 履歴に記録済みなので、モデルはツールを呼び直さずに答えられる
    agent("このユーザーはどのプランでしたか?")
