"""ノック47: ツール結果の加工 — AfterToolCallEvent で監査ログとマスキング

ツールの実行後、結果がモデルに渡る前に介入する。
  - 監査ログ: 誰が・何を・どんな結果で(コンプライアンス要件の定番)
  - 結果の加工: event.result を編集して機密情報をマスクしてからモデルに見せる

実行: uv run knocks/k047_tool_audit.py
"""

import re

from common import make_model

from strands import Agent, tool
from strands.hooks import AfterToolCallEvent, HookProvider, HookRegistry


@tool
def get_customer(customer_id: str) -> str:
    """顧客情報を取得する。"""
    return f"顧客 {customer_id}: 山田太郎 / メール yamada@example.com / 電話 090-1234-5678"


class AuditAndMask(HookProvider):
    audit_log: list[str] = []

    def register_hooks(self, registry: HookRegistry, **kwargs) -> None:
        registry.add_callback(AfterToolCallEvent, self.on_after)

    def on_after(self, event: AfterToolCallEvent) -> None:
        # 1) 監査ログ(マスク前の生情報はログ側にだけ残すこともできる)
        self.audit_log.append(
            f"tool={event.tool_use['name']} input={event.tool_use['input']} "
            f"status={event.result['status']}"
        )

        # 2) モデルに渡る前に電話番号をマスクする
        for block in event.result.get("content", []):
            if "text" in block:
                block["text"] = re.sub(r"\d{2,4}-\d{2,4}-\d{4}", "***-****-****", block["text"])


if __name__ == "__main__":
    hook = AuditAndMask()
    agent = Agent(model=make_model(), tools=[get_customer], hooks=[hook])

    agent("顧客 C-100 の連絡先を教えて。")
    # モデルは電話番号のマスク済みデータしか見ていないので、応答にも出てこない

    print("\n===== 監査ログ =====")
    for line in hook.audit_log:
        print(line)
