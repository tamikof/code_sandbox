"""ノック87: Workflow ツール — タスク依存つきの実行

Graph(84〜86)はエージェントをノードにする。workflow ツールはより手軽に、
1つのエージェントに「依存関係つきのタスク列」を実行させる community ツール。
タスクの定義・依存解決・並列実行をツール側が面倒見てくれる。

実行: uv run knocks/k087_workflow_tool.py
"""

from common import make_model
from strands_tools import workflow

from strands import Agent

if __name__ == "__main__":
    agent = Agent(model=make_model(), tools=[workflow])

    # タスクと依存関係を定義する(data_extraction → trend_analysis → report の順に解決される)
    agent.tool.workflow(
        action="create",
        workflow_id="sales_report",
        tasks=[
            {
                "task_id": "extract",
                "description": "売上データから主要な数字を抽出する",
                "system_prompt": "あなたはデータ抽出の担当です。",
                "priority": 5,
            },
            {
                "task_id": "analyze",
                "description": "抽出した数字から傾向を分析する",
                "dependencies": ["extract"],  # extract の完了を待つ
                "system_prompt": "あなたは傾向分析の担当です。",
                "priority": 3,
            },
            {
                "task_id": "report",
                "description": "分析結果を経営層向けレポートにまとめる",
                "dependencies": ["analyze"],
                "system_prompt": "あなたはレポート作成の担当です。",
                "priority": 2,
            },
        ],
    )

    print("ワークフローを作成しました。実行します...")
    agent.tool.workflow(action="start", workflow_id="sales_report")

    status = agent.tool.workflow(action="status", workflow_id="sales_report")
    print("\n実行ステータス:", status["status"])
