"""ノック45: ライフサイクルフック — 呼び出しの前後に処理を挟む

ストリーミング(ノック41〜44)は「観察」、フックは「介入」。
HookProvider を実装してエージェントの節目に処理を差し込む。
まずは安全な用途 = ロギングと計測から。

実行: uv run knocks/k045_lifecycle_hooks.py
"""

import time

from common import make_model

from strands import Agent
from strands.hooks import (
    AfterInvocationEvent,
    AgentInitializedEvent,
    BeforeInvocationEvent,
    HookProvider,
    HookRegistry,
)


class TimingLogger(HookProvider):
    """呼び出しごとの所要時間とトークン数を記録するフック。"""

    def register_hooks(self, registry: HookRegistry, **kwargs) -> None:
        registry.add_callback(AgentInitializedEvent, self.on_init)
        registry.add_callback(BeforeInvocationEvent, self.on_before)
        registry.add_callback(AfterInvocationEvent, self.on_after)

    def on_init(self, event: AgentInitializedEvent) -> None:
        print(f"[hook] エージェント初期化: {event.agent.name}")

    def on_before(self, event: BeforeInvocationEvent) -> None:
        self._start = time.perf_counter()
        print("[hook] 呼び出し開始")

    def on_after(self, event: AfterInvocationEvent) -> None:
        elapsed = time.perf_counter() - self._start
        usage = event.agent.event_loop_metrics.accumulated_usage
        print(f"[hook] 呼び出し終了: {elapsed:.2f}秒 / 累計 {usage['totalTokens']} トークン")


if __name__ == "__main__":
    agent = Agent(model=make_model(), hooks=[TimingLogger()], callback_handler=None)

    print(agent("いま一番おすすめの旬の食材は?一言で。"))
    print(agent("それを使った料理を1つ挙げて。"))
    # フックは Agent に紐づくので、毎回の呼び出しで自動的に発火する
