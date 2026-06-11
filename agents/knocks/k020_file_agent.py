"""ノック20: ファイル操作エージェント — ローカル作業をさせる

file_write / file_read でエージェントがファイルシステムを操作する。
危険な操作には確認プロンプトが出る(BYPASS_TOOL_CONSENT=true で省略可)。
この「人間の確認を挟む」仕組みは第5章 (human-in-the-loop) につながる。

実行: uv run knocks/k020_file_agent.py
"""

from common import make_model
from strands_tools import file_read, file_write

from strands import Agent

if __name__ == "__main__":
    agent = Agent(model=make_model(), tools=[file_read, file_write])

    agent(
        "秋をテーマに俳句を一句詠んで /tmp/knock20_haiku.txt に保存して。"
        "そのあとファイルを読み直して、保存できたか確認して。"
    )
