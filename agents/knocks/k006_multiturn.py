"""ノック6: マルチターン会話 — agent.messages の中身を覗く

同じ Agent インスタンスへの呼び出しは履歴を共有する。
「前の発言」を覚えていること、履歴がどんな構造かを確認する。

実行: uv run knocks/k006_multiturn.py
"""

from strands import Agent

agent = Agent(callback_handler=None)

print(agent("私の好きな食べ物は寿司です。覚えておいて。"))
print(agent("私の好きな食べ物は何だったか覚えてる?"))

# 履歴は agent.messages にロール付きで蓄積されている
print("\n===== agent.messages =====")
for i, message in enumerate(agent.messages):
    text = "".join(block.get("text", "") for block in message["content"])
    print(f"{i}: role={message['role']:9s} {text[:60]!r}")
