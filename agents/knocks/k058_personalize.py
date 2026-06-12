"""ノック58: パーソナライズ — 記憶を「最初から」プロンプトに焼き込む

ノック55〜57は「必要なときにツールで思い出す」方式だった。
もう1つの定石は、会話開始時に記憶を検索してシステムプロンプトに
埋め込んでしまう方式。ツール呼び出しの往復が減り、応答が最初から
そのユーザー仕様になる。

このノックは自作メモ帳(ノック55)を使うので AWS の追加リソース不要。
実行: uv run knocks/k055_memory_tool.py を先に実行してメモを作ってから
      uv run knocks/k058_personalize.py
"""

from common import make_model
from k055_memory_tool import _load

from strands import Agent


def build_personalized_agent() -> Agent:
    """保存済みのメモをシステムプロンプトに焼き込んだエージェントを作る。"""
    notes = _load()
    profile = "\n".join(f"- {note}" for note in notes) if notes else "(情報なし)"
    return Agent(
        model=make_model(),
        system_prompt=(
            "あなたはパーソナルアシスタントです。\n"
            "## このユーザーについて知っていること\n"
            f"{profile}\n\n"
            "上記を踏まえ、聞かれなくても相手に合わせた提案をしてください。"
        ),
    )


if __name__ == "__main__":
    agent = build_personalized_agent()
    print("焼き込まれたプロフィール:")
    print(agent.system_prompt, "\n")

    agent("夕食のおすすめを3つ教えて。")
    # エビアレルギー(ノック55で保存)が考慮された提案になるはず。
    # ツール方式(55) vs 焼き込み方式(58) の使い分け:
    #   - 記憶が少ない/毎回使う → 焼き込み(速い・確実)
    #   - 記憶が大量にある     → ツールで都度検索(コンテキスト節約)
