"""ノック2: ペルソナエージェント — system_prompt で役割を固定する

実行: uv run knocks/k002_persona.py
"""

from common import make_model

from strands import Agent

# system_prompt はすべてのターンの前提になる「役割設定」。
# ユーザー入力より優先度の高い指示として扱われる。
agent = Agent(
    model=make_model(),
    system_prompt=(
        "あなたは大阪出身のベテラン板前です。"
        "関西弁で話し、何を聞かれても必ず料理の例え話を交えて答えます。"
        "回答は3文以内に収めてください。"
    )
)

agent("プログラミングのデバッグのコツを教えて。")
