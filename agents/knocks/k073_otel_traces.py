"""ノック73: OTel トレース — OpenTelemetry でエージェントループを可視化

Strands は OpenTelemetry に対応している。トレースを有効にすると、
1回の呼び出しが「スパンの木」になる:
  エージェント呼び出し
   └ サイクル1
      └ モデル呼び出し
      └ ツール実行 (get_weather)
   └ サイクル2
      └ モデル呼び出し
setup_console_exporter() を使うと、そのスパンを標準出力で確認できる。

このノックは AWS 不要(モックモデルで動く)。
実行: uv run knocks/k073_otel_traces.py
"""

from mock_model import MockModel, ToolCall

from strands import Agent, tool
from strands.telemetry import StrandsTelemetry

# トレースを有効化し、コンソールにスパンを出力する。
# OTLP で外部に送る場合は setup_otlp_exporter()(ノック74)
telemetry = StrandsTelemetry()
telemetry.setup_console_exporter()


@tool
def get_weather(city: str) -> str:
    """都市の天気を返す。"""
    return f"{city}: 晴れ"


if __name__ == "__main__":
    agent = Agent(
        model=MockModel([ToolCall("get_weather", {"city": "東京"}), "東京は晴れです"]),
        tools=[get_weather],
        # trace_attributes はすべてのスパンに付く共通タグ(ノック75)
        trace_attributes={"service.name": "knock-demo"},
        callback_handler=None,
    )

    agent("東京の天気を調べて。")
    # 標準出力に JSON 形式のスパンが出る。name / duration / attributes を見ると、
    # どのツールがどれだけ時間を使ったかが木構造で分かる
    print("\n(上に出力された span を確認してください)")
