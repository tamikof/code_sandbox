"""ノック60: 記憶戦略の比較 — 全部保存 / 要約 / 抽出 を並べて考える

第4〜6章で登場した「記憶」の手段を1つの表に整理し、
「抽出」戦略(会話の終わりに要点だけ構造化して取り出す)を実装して締める。

このノックは AWS 不要(モックモデルで動く)。
実行: uv run knocks/k060_memory_strategies.py
"""

from mock_model import MockModel, ToolCall

from strands import Agent, tool

# ============================================================
# 戦略の整理
#
# | 戦略     | 実装                          | 残るもの   | コスト | 向き           |
# |----------|-------------------------------|-----------|--------|----------------|
# | 全部保存 | SessionManager (51〜54)       | 会話の全文 | 高い   | 同一会話の継続 |
# | 要約     | SummarizingManager (33)       | 圧縮した文 | 中     | 長い1会話      |
# | 抽出     | メモリツール (55〜57) や本ノック | 構造化事実 | 低い   | 会話を跨ぐ記憶 |
#
# 実務では併用する: 会話中はセッション、会話を跨ぐ事実は抽出メモリ。
# ============================================================


@tool
def save_fact(category: str, fact: str) -> str:
    """会話から得たユーザーの事実を保存する。category は profile/preference/constraint。"""
    FACTS.append({"category": category, "fact": fact})
    return f"保存: [{category}] {fact}"


FACTS: list[dict] = []

EXTRACT_PROMPT = (
    "この会話からユーザーに関する長期的に有用な事実だけを save_fact で保存して。"
    "一時的な話題(今日の天気など)は保存しないこと。"
)

if __name__ == "__main__":
    # 会話本体(モック): 重要情報と雑談が混ざっている
    agent = Agent(
        model=MockModel(
            [
                "覚えました!",
                # 抽出フェーズでモデルが選ぶツール呼び出し(雑談は保存しない判断)
                [
                    ToolCall("save_fact", {"category": "profile", "fact": "名前はタミコ"}),
                    ToolCall(
                        "save_fact",
                        {"category": "constraint", "fact": "エビアレルギーがある"},
                    ),
                ],
                "2件の事実を保存しました",
            ]
        ),
        tools=[save_fact],
        callback_handler=None,
    )

    agent("私はタミコ。エビアレルギーがあります。あと今日は暑いですね。")

    # 会話の終わりに「抽出」を実行(実モデルなら雑談を捨てる判断もモデルがする)
    agent(EXTRACT_PROMPT)

    print("===== 抽出された事実(これだけを永続化する) =====")
    for fact in FACTS:
        print(f"[{fact['category']}] {fact['fact']}")
    print("\n会話全文を保存する場合と比べ、次回の会話に持ち込むトークンが激減する")
