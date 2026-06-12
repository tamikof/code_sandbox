"""ノック33: 要約による圧縮 — SummarizingConversationManager

捨てる(ノック32)のではなく、古い履歴を要約して1メッセージに畳む。
要約には別のエージェント(=安いモデル)を使える。

実行: uv run knocks/k033_summarizing.py
"""

from common import make_model

from strands import Agent
from strands.agent.conversation_manager import SummarizingConversationManager

if __name__ == "__main__":
    # 要約係は安いモデルで十分(メインを Sonnet にしても要約は Haiku、という構成が定石)
    summarizer = Agent(
        model=make_model(),
        system_prompt="会話の要点を、固有名詞と決定事項を落とさずに箇条書きで要約してください。",
        callback_handler=None,
    )

    manager = SummarizingConversationManager(
        summary_ratio=0.5,  # 溢れたら古い方から50%を要約に置き換える
        preserve_recent_messages=2,  # 直近2件は絶対に要約しない
        summarization_agent=summarizer,
    )

    agent = Agent(model=make_model(), conversation_manager=manager, callback_handler=None)

    print(agent("私の名前はタミコです。"))
    print(agent("北海道旅行を計画していて、予算は10万円です。"))
    print(agent("2月の連休に行く予定です。"))

    # 本来はコンテキスト溢れ時に自動発動するが、ここでは手動で発動させて観察する
    print("\n--- 要約を強制実行 ---")
    manager.reduce_context(agent)

    print("履歴の件数:", len(agent.messages))
    print("先頭メッセージ(要約):", agent.messages[0]["content"][0]["text"][:200])

    # 要約に「名前・予算・時期」が残っていれば、続きの会話が成立する
    print(agent("\n私の旅行計画をまとめて。"))
