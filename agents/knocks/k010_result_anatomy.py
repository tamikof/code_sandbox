"""ノック10: 結果の解剖 — AgentResult の中身を観察する

エージェント呼び出しの戻り値には、応答テキスト以外に
停止理由・トークン使用量・実行メトリクスが入っている。
運用時のコスト管理やデバッグの土台になる情報。

実行: uv run knocks/k010_result_anatomy.py
"""

from strands import Agent

agent = Agent(callback_handler=None)

result = agent("日本で一番高い山は?一言で。")

print("===== 応答テキスト =====")
print(result)  # str(result) は最終応答のテキストになる

print("\n===== AgentResult の中身 =====")
print(f"stop_reason : {result.stop_reason}")  # end_turn / max_tokens / tool_use など
print(f"message     : {result.message}")

usage = result.metrics.accumulated_usage
print("\n===== メトリクス =====")
print(f"入力トークン : {usage['inputTokens']}")
print(f"出力トークン : {usage['outputTokens']}")
print(f"合計トークン : {usage['totalTokens']}")
print(f"サイクル数   : {result.metrics.cycle_count}")  # ツールを使うと増える
print(f"レイテンシ   : {result.metrics.accumulated_metrics['latencyMs']}ms")
