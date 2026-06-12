"""ノック94: AgentCore Identity — OAuth で外部サービスに安全にアクセス

エージェントがユーザーの代わりに Google カレンダーや Slack を操作するには、
そのユーザーの OAuth トークンが要る。Identity は、トークンの取得・保存・更新を
マネージドで行い、エージェントのコードからは「@requires_access_token で
デコレートしたら token が降ってくる」だけにしてくれる。

このノックは「使い方の形」を示すコード。実際には Identity に
OAuth プロバイダ(Google 等)を登録しておく必要がある。

前提: AgentCore Identity に Google プロバイダを登録
実行: (AgentCore 環境で) uv run knocks/k094_agentcore_identity.py
"""


# @requires_access_token デコレータの使い方の例。
# 実行には bedrock_agentcore.identity と登録済みプロバイダが必要。
def show_usage_pattern() -> None:
    code = '''
from bedrock_agentcore.identity.auth import requires_access_token
from strands import Agent, tool

@tool
@requires_access_token(
    provider_name="google-calendar",   # Identity に登録したプロバイダ
    scopes=["https://www.googleapis.com/auth/calendar.readonly"],
    auth_flow="USER_FEDERATION",        # ユーザー本人の認可を使う
)
async def list_events(access_token: str) -> str:
    """Google カレンダーの予定を取得する。"""
    # access_token は Identity が用意してくれる(取得・更新は自動)
    import httpx
    resp = httpx.get(
        "https://www.googleapis.com/calendar/v3/calendars/primary/events",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    return resp.text

# エージェントは普通にツールとして使うだけ
agent = Agent(tools=[list_events])
agent("今日の予定を教えて")
'''
    print(code)


if __name__ == "__main__":
    print("===== AgentCore Identity の使い方 =====")
    show_usage_pattern()
    print(
        "ポイント:\n"
        "- トークンの取得・暗号化保存・期限切れ更新を Identity が肩代わりする\n"
        "- コードに API キーや refresh token が一切現れない(第7章の安全性の延長)\n"
        "- ユーザーごとに異なるトークンを安全に使い分けられる(マルチユーザー)"
    )
