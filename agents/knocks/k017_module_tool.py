"""ノック17: モジュール形式のツール — デコレータを使わない定義方法

ツール本体は knocks/shout.py を参照。
モジュール形式では「TOOL_SPEC + モジュール名と同じ名前の関数」が規約。
スキーマを完全に手書きで制御したい場合や、ツールをファイル単位で管理したい場合の形式。

実行: uv run knocks/k017_module_tool.py
"""

import shout
from common import make_model

from strands import Agent

if __name__ == "__main__":
    # モジュール自体を tools に渡す
    agent = Agent(model=make_model(), tools=[shout])
    agent("「hello world」を shout ツールで叫んで。")
