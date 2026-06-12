"""ノック57: AgentCore Memory(長期) — 会話を跨いで「学習」する記憶

短期メモリ(ノック56)は会話の生ログ。長期メモリは、そこから
ユーザーの嗜好・事実・要約を**サービス側が自動抽出**して蓄積する仕組み。
セッションが変わっても「このユーザーはこういう人」が残る。

前提: 長期メモリ戦略つきの Memory リソース
  aws bedrock-agentcore-control create-memory --name knocks-lt \\
    --event-expiry-duration P30D \\
    --memory-strategies '[{"userPreferenceMemoryStrategy": {"name": "prefs", "namespaces": ["/users/{actorId}"]}}]'

実行: KNOCK_MEMORY_ID=xxx uv run knocks/k057_agentcore_memory_long.py
"""

import os

from common import make_model
from strands_tools.agent_core_memory import AgentCoreMemoryToolProvider

from strands import Agent


def build_agent(session_id: str, memory_id: str) -> Agent:
    provider = AgentCoreMemoryToolProvider(
        memory_id=memory_id,
        actor_id="user-tamiko",
        session_id=session_id,             # セッションは毎回変える
        namespace="/users/user-tamiko",    # 長期メモリの名前空間
    )
    return Agent(
        model=make_model(),
        tools=provider.tools,
        system_prompt=(
            "ユーザーの発言は create_event で記録してください。"
            "提案をする前に retrieve_memory_records でユーザーの嗜好を検索してください。"
        ),
    )


if __name__ == "__main__":
    memory_id = os.environ.get("KNOCK_MEMORY_ID")
    if not memory_id:
        raise SystemExit("環境変数 KNOCK_MEMORY_ID を設定してください")

    # 会話1: 嗜好を話す(裏で長期メモリへの抽出が走る。反映には少し時間がかかる)
    agent1 = build_agent("session-A", memory_id)
    agent1("私は辛い食べ物が大好きで、パクチーは苦手です。")

    input("\n(長期メモリへの抽出を待つため、1分ほど待って Enter...)")

    # 会話2: 完全に別のセッション。それでも嗜好が引ける
    agent2 = build_agent("session-B", memory_id)
    agent2("今夜の夕食を提案して。")
    # → retrieve_memory_records が「辛いもの好き・パクチー苦手」を引き当てて提案が変わる
