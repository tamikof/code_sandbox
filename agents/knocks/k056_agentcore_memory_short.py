"""ノック56: AgentCore Memory(短期) — マネージドなメモリサービスを使う

ノック55の自作メモ帳のマネージド版が Amazon Bedrock AgentCore Memory。
短期メモリ(raw event)は会話のやりとりをそのままサービス側に記録する。

前提:
  1. uv add strands-agents-tools[agent_core_memory]
  2. AgentCore Memory リソースを作成(コンソール or CLI)して MEMORY_ID を控える
     aws bedrock-agentcore-control create-memory --name knocks --event-expiry-duration P30D

実行: KNOCK_MEMORY_ID=xxx uv run knocks/k056_agentcore_memory_short.py
"""

import os

from common import make_model
from strands_tools.agent_core_memory import AgentCoreMemoryToolProvider

from strands import Agent

if __name__ == "__main__":
    memory_id = os.environ.get("KNOCK_MEMORY_ID")
    if not memory_id:
        raise SystemExit("環境変数 KNOCK_MEMORY_ID に AgentCore Memory の ID を設定してください")

    provider = AgentCoreMemoryToolProvider(
        memory_id=memory_id,
        actor_id="user-tamiko",      # 誰の記憶か
        session_id="knock56",        # どの会話か
        namespace=f"/actor/user-tamiko",
    )

    # provider.tools に record/retrieve 系のツール一式が入っている
    agent = Agent(
        model=make_model(),
        tools=provider.tools,
        system_prompt=(
            "会話の重要なやりとりは create_event で記録し、"
            "過去の文脈が必要なら retrieve_memory_records で検索してください。"
        ),
    )

    agent("私はタミコです。北海道旅行を計画していて予算は10万円です。記録しておいて。")
    agent("私の旅行の予算はいくらだったか、メモリから思い出して。")
