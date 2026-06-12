"""ノック12: 型ヒントと docstring — ツール仕様(スキーマ)の生成を覗く

@tool は関数の型ヒントと docstring から JSON スキーマを自動生成する。
モデルはこのスキーマ「だけ」を見てツールの使い方を決める。
つまり docstring の質 = ツールが正しく使われる確率。

このノックは LLM を呼ばない。生成されたスキーマを観察するだけ。

実行: uv run knocks/k012_tool_spec.py
"""

import json
from typing import Literal

from strands import tool


@tool
def convert_temperature(
    value: float,
    from_unit: Literal["celsius", "fahrenheit"],
    to_unit: Literal["celsius", "fahrenheit"],
) -> float:
    """温度を摂氏・華氏の間で変換する。

    Args:
        value: 変換したい温度の値
        from_unit: 変換元の単位
        to_unit: 変換先の単位
    """
    if from_unit == to_unit:
        return value
    if from_unit == "celsius":
        return value * 9 / 5 + 32
    return (value - 32) * 5 / 9


if __name__ == "__main__":
    # 関数 → ツール仕様 への変換結果。Literal が enum に、Args が description になる
    print(json.dumps(convert_temperature.tool_spec, ensure_ascii=False, indent=2))
