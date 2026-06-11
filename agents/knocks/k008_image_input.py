"""ノック8: 画像入力 — マルチモーダルなプロンプト

プロンプトは文字列だけでなく「コンテンツブロックのリスト」も渡せる。
画像ブロック + テキストブロックを組み合わせて画像について質問する。

実行: uv run knocks/k008_image_input.py <画像ファイルのパス>
例:   uv run knocks/k008_image_input.py ~/Pictures/cat.png
"""

import sys
from pathlib import Path

from strands import Agent

if len(sys.argv) != 2:
    print(__doc__)
    sys.exit(1)

path = Path(sys.argv[1])
image_format = path.suffix.lstrip(".").lower().replace("jpg", "jpeg")

agent = Agent()

agent(
    [
        {"image": {"format": image_format, "source": {"bytes": path.read_bytes()}}},
        {"text": "この画像に写っているものを説明して。"},
    ]
)
