"""ノック75: トレース属性 — ユーザーIDなどのカスタムタグを付ける

trace_attributes はすべてのスパンに付く共通タグ。本番では
「どのユーザーの・どのセッションの・どのバージョンの」リクエストかを
タグ付けしておき、収集基盤で絞り込めるようにする。

このノックは AWS 不要(モックモデルで動く)。
実行: uv run knocks/k075_trace_attributes.py
"""

from mock_model import MockModel

from strands import Agent

if __name__ == "__main__":
    # リクエストの文脈を表す属性をまとめて付ける。
    # OpenTelemetry の semantic convention に沿った名前にしておくと
    # 収集基盤のダッシュボードがそのまま使えることが多い。
    agent = Agent(
        model=MockModel(["承知しました"]),
        trace_attributes={
            "user.id": "u-001",
            "session.id": "sess-abc",
            "app.version": "1.2.0",
            "app.feature": "recipe-suggestion",
        },
        callback_handler=None,
    )

    agent("夕食のおすすめは?")

    # trace_attributes は agent に保持され、全スパンに伝播する
    print("付与されるトレース属性:")
    for key, value in agent.trace_attributes.items():
        print(f"  {key} = {value}")
    print(
        "\nこれで収集基盤上で「user.id=u-001 のリクエストだけ」「app.version=1.2.0 のエラー率」"
        "のような分析ができる"
    )
