"""ノック74: トレースの送信 — OTLP で Langfuse / Jaeger に送る

コンソール出力(ノック73)は開発用。本番では OTLP エクスポーターで
収集基盤(Langfuse, Jaeger, Grafana Tempo, Datadog...)に送る。
設定は環境変数 OTEL_EXPORTER_OTLP_* に従う標準的なもの。

前提: OTLP 受信先(ローカル Jaeger なら docker で簡単に立つ)
  docker run -d -p 4318:4318 -p 16686:16686 jaegertracing/all-in-one

実行:
  export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
  uv run knocks/k074_otlp_export.py
  → http://localhost:16686 でトレースを確認
"""

import os

from mock_model import MockModel, ToolCall

from strands import Agent, tool
from strands.telemetry import StrandsTelemetry


@tool
def get_weather(city: str) -> str:
    """都市の天気を返す。"""
    return f"{city}: 晴れ"


if __name__ == "__main__":
    endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")
    if not endpoint:
        raise SystemExit(
            "OTEL_EXPORTER_OTLP_ENDPOINT を設定してください(例: http://localhost:4318)"
        )

    telemetry = StrandsTelemetry()
    telemetry.setup_otlp_exporter()  # 環境変数のエンドポイントへ送る

    agent = Agent(
        model=MockModel([ToolCall("get_weather", {"city": "大阪"}), "大阪は晴れです"]),
        tools=[get_weather],
        trace_attributes={"service.name": "strands-knocks", "deployment.env": "dev"},
        callback_handler=None,
    )

    agent("大阪の天気を調べて。")
    print(f"トレースを {endpoint} に送信しました。収集基盤の UI で確認してください。")
    # Langfuse の場合は OTEL_EXPORTER_OTLP_HEADERS に認証ヘッダを設定する
