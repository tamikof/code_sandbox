"""ノック81: Agents as Tools — オーケストレーター + 専門エージェント

最も基本的なマルチエージェント構成。「司令塔」エージェントが、専門エージェントを
ツールとして呼ぶ。agent.as_tool() で任意のエージェントをツール化できる。

  オーケストレーター
   ├─ researcher(調査の専門家)を tool として持つ
   └─ calculator_agent(計算の専門家)を tool として持つ

実行: uv run knocks/k081_agents_as_tools.py
"""

from common import make_model

from strands import Agent
from strands_tools import calculator

# --- 専門エージェントたち ---

researcher = Agent(
    model=make_model(),
    name="researcher",
    system_prompt="あなたは調査の専門家です。事実を簡潔にまとめて報告します。",
    callback_handler=None,
)

math_agent = Agent(
    model=make_model(),
    name="math_expert",
    system_prompt="あなたは計算の専門家です。calculator ツールを使って正確に計算します。",
    tools=[calculator],
    callback_handler=None,
)

if __name__ == "__main__":
    # 専門エージェントをツールに変換して、司令塔に持たせる
    orchestrator = Agent(
        model=make_model(),
        system_prompt=(
            "あなたは司令塔です。調査が必要なら researcher に、"
            "計算が必要なら math_expert に委譲してください。"
        ),
        tools=[
            researcher.as_tool(name="researcher", description="事実の調査を依頼する"),
            math_agent.as_tool(name="math_expert", description="計算を依頼する"),
        ],
    )

    orchestrator(
        "日本の人口はおよそ1.2億人です。これを47都道府県で均等に割ると"
        "1県あたり何人になる?調査と計算を適切な担当に振って答えて。"
    )
