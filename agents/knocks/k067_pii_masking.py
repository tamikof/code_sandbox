"""ノック67: PII マスキング — 個人情報をモデルに見せない

ノック47ではツール結果のマスキングをやった。今回は逆方向:
**ユーザー入力に含まれる PII を、モデルに送る前にマスクする**。
MessageAddedEvent フックで履歴に追加された瞬間に書き換えるので、
モデルにも、保存されるセッションにも、生の PII が残らない。

(マネージドにやるなら Bedrock Guardrails の Sensitive information filter。
 ここでは仕組みを理解するため自作する)

このノックは AWS 不要(モックモデルで動く)。
実行: uv run knocks/k067_pii_masking.py
"""

import re

from mock_model import MockModel

from strands import Agent
from strands.hooks import HookProvider, HookRegistry, MessageAddedEvent

PII_PATTERNS = [
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"), "<メールアドレス>"),
    (re.compile(r"\d{2,4}-\d{2,4}-\d{4}"), "<電話番号>"),
    (re.compile(r"\d{3}-\d{4}(?!\d)"), "<郵便番号>"),
]


class PiiMasker(HookProvider):
    """履歴に追加される user メッセージから PII を除去する。"""

    def register_hooks(self, registry: HookRegistry, **kwargs) -> None:
        registry.add_callback(MessageAddedEvent, self.mask)

    def mask(self, event: MessageAddedEvent) -> None:
        if event.message["role"] != "user":
            return
        for block in event.message["content"]:
            if "text" in block:
                for pattern, replacement in PII_PATTERNS:
                    block["text"] = pattern.sub(replacement, block["text"])


if __name__ == "__main__":
    model = MockModel(["お問い合わせを受け付けました。"])
    agent = Agent(model=model, hooks=[PiiMasker()], callback_handler=None)

    agent("返金してください。連絡先は tamiko@example.com、電話は 090-1234-5678 です。")

    print("===== 履歴に残ったユーザー発言 =====")
    print(agent.messages[0]["content"][0]["text"])

    print("\n===== モデルが実際に受け取ったもの =====")
    print(model.calls[0]["messages"][0]["content"][0]["text"])
    # どちらにも生のメールアドレス・電話番号は存在しない
