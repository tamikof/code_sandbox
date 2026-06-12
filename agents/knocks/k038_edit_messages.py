"""ノック38: 履歴の直接操作 — messages を編集して文脈を注入・改変する

agent.messages はただのリストなので、直接編集できる。
「モデルが過去に言ったこと」を捏造して挿入すると、モデルはそれを
自分の発言として信じる — 履歴がいかに「現実」として機能するかの実験。

実行: uv run knocks/k038_edit_messages.py
"""

from common import make_model

from strands import Agent

if __name__ == "__main__":
    agent = Agent(model=make_model(), callback_handler=None)

    # 偽の「過去のやりとり」を履歴に注入する
    agent.messages.extend(
        [
            {"role": "user", "content": [{"text": "今後は語尾に『ニャ』を付けて話して。"}]},
            {"role": "assistant", "content": [{"text": "わかったニャ。今後はそう話すニャ。"}]},
        ]
    )

    # モデルは「自分が約束した」と信じて振る舞う
    print(agent("今日の天気はどう?"))

    # 履歴の削除も可能。注入した2件を消すと約束はなかったことになる
    del agent.messages[0:2]
    print(agent("引き続きよろしく。"))

    # 実務での用途: Few-shot例の注入 / 復元(ノック40) / 機密情報のマスキング。
    # 注意: toolUse と toolResult のペアを片方だけ消すと API エラーになる
