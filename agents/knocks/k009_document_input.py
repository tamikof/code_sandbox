"""ノック9: ドキュメント入力 — PDF を渡して要約させる

画像と同様に、document ブロックで PDF などのファイルを渡せる。

実行: uv run knocks/k009_document_input.py <PDFファイルのパス>
"""

import sys
from pathlib import Path

from strands import Agent

if len(sys.argv) != 2:
    print(__doc__)
    sys.exit(1)

path = Path(sys.argv[1])

agent = Agent()

agent(
    [
        {
            "document": {
                "format": "pdf",
                "name": path.stem,
                "source": {"bytes": path.read_bytes()},
            }
        },
        {"text": "このドキュメントの要点を3つ、箇条書きでまとめて。"},
    ]
)
