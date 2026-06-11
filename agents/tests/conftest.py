"""pytest 共通設定。

knocks/ ディレクトリを import パスに追加して、
各ノックのツール定義をテストから直接 import できるようにする。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "knocks"))
