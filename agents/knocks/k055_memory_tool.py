"""ノック55: メモリツール — エージェント自身に「覚える/思い出す」を任せる

セッション(51〜54)は会話の「全文」を保存する仕組み。メモリツールは
エージェントが**自分の判断で要点だけ**をメモし、必要なときに思い出す仕組み。
ここでは最小のメモ帳ツールを自作して、その動きを観察する。

本格版はコミュニティツールにある:
  - strands_tools.memory      (Bedrock Knowledge Base ベース)
  - strands_tools.mem0_memory (mem0 ベース、セマンティック検索つき)

このノックは AWS 不要ではない(モデルがメモを取る判断をするため実モデル推奨)。
実行: uv run knocks/k055_memory_tool.py
"""

import json
from pathlib import Path

from common import make_model

from strands import Agent, tool

NOTES_FILE = Path("/tmp/knock55_notes.json")


def _load() -> list[str]:
    return json.loads(NOTES_FILE.read_text()) if NOTES_FILE.exists() else []


@tool
def remember(fact: str) -> str:
    """ユーザーに関する重要な事実を長期メモリに保存する。

    ユーザーの名前・好み・制約(アレルギー等)・繰り返し使いそうな情報を
    見つけたら、このツールで保存すること。
    """
    notes = _load()
    if fact not in notes:
        notes.append(fact)
        NOTES_FILE.write_text(json.dumps(notes, ensure_ascii=False, indent=2))
    return f"保存しました(現在 {len(notes)} 件)"


@tool
def recall() -> str:
    """長期メモリに保存した事実をすべて読み出す。"""
    notes = _load()
    return "\n".join(f"- {n}" for n in notes) if notes else "メモはまだありません"


SYSTEM = (
    "あなたはパーソナルアシスタントです。"
    "会話の中でユーザーの重要な情報(名前・好み・制約)が出てきたら remember で保存し、"
    "ユーザーについて知る必要があれば recall で思い出してください。"
)

if __name__ == "__main__":
    # --- 会話1: メモが取られる ---
    agent = Agent(model=make_model(), tools=[remember, recall], system_prompt=SYSTEM)
    agent("はじめまして。タミコです。エビアレルギーがあるので料理の提案では避けてね。")

    # --- 会話2: 履歴ゼロの新しいエージェント。それでもメモから思い出せる ---
    print("\n" + "=" * 40 + "(新しい会話)" + "=" * 40 + "\n")
    fresh = Agent(model=make_model(), tools=[remember, recall], system_prompt=SYSTEM)
    fresh("私に合う夕食を提案して。")
    # セッションと違い「会話全文」は引き継がない。要点だけが残る = トークン効率が良い
