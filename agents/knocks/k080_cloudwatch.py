"""ノック80: CloudWatch 連携 — AWS 上での GenAI Observability

AWS 上で動かすなら、メトリクス・トレースを CloudWatch / X-Ray に送って
マネージドなダッシュボードで見るのが定番。Strands の OTel 出力を
ADOT (AWS Distro for OpenTelemetry) Collector 経由で CloudWatch に流す。

仕組み(全体像):
  Strands (OTLP) → ADOT Collector → CloudWatch Logs / Metrics / X-Ray

このノックは「設定の形」を示すだけで、実行には AWS 環境が要る。
AgentCore Runtime(第10章)にデプロイすると、この配線は概ね自動で入る。

実行: (参考用。実際は ADOT Collector を立てて環境変数を設定する)
"""

import os

# CloudWatch へ送るための一般的な環境変数設定(コード外で設定するのが普通)
EXAMPLE_ENV = {
    # ADOT Collector のエンドポイント(サイドカー or ローカル)
    "OTEL_EXPORTER_OTLP_ENDPOINT": "http://localhost:4318",
    # CloudWatch 側で識別するためのサービス名
    "OTEL_RESOURCE_ATTRIBUTES": "service.name=strands-knocks,deployment.environment=prod",
    # X-Ray 形式のトレースID を使う場合
    "OTEL_PROPAGATORS": "xray",
}


def setup_for_cloudwatch():
    """CloudWatch 連携の設定例(実際は環境変数で渡す)。"""
    from mock_model import MockModel

    from strands import Agent
    from strands.telemetry import StrandsTelemetry

    telemetry = StrandsTelemetry()
    telemetry.setup_otlp_exporter()  # OTEL_EXPORTER_OTLP_ENDPOINT(=ADOT)へ送る

    return Agent(
        model=MockModel(["ok"]),
        trace_attributes={
            "service.name": "strands-knocks",
            "deployment.environment": "prod",
        },
        callback_handler=None,
    )


if __name__ == "__main__":
    print("===== CloudWatch 連携に必要な環境変数(例) =====")
    for key, value in EXAMPLE_ENV.items():
        print(f"export {key}='{value}'")

    configured = all(k in os.environ for k in ["OTEL_EXPORTER_OTLP_ENDPOINT"])
    print(f"\n現在の環境で OTLP エンドポイント設定済み: {configured}")
    print(
        "\nまとめ: ノック72(メトリクス)・73(トレース)で見たデータを、"
        "ADOT Collector 経由で CloudWatch に流すと、マネージドな GenAI ダッシュボードになる。"
        "AgentCore Runtime にデプロイすればこの配線は概ね自動(第10章)。"
    )
