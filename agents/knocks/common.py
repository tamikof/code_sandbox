"""ノック共通設定。

普段のノックは安価な Claude Haiku 4.5 を使う。
環境変数 KNOCK_MODEL_ID を設定すると別モデルに差し替えられる。

例: KNOCK_MODEL_ID=global.anthropic.claude-sonnet-4-6 uv run knocks/k001_hello_agent.py
"""

import os

from strands.models import BedrockModel

DEFAULT_MODEL_ID = "global.anthropic.claude-haiku-4-5-20251001-v1:0"


def model_id() -> str:
    return os.environ.get("KNOCK_MODEL_ID", DEFAULT_MODEL_ID)


def make_model(**kwargs) -> BedrockModel:
    """ノック用のデフォルトモデルを作る。temperature 等は kwargs で上書き可能。"""
    return BedrockModel(model_id=model_id(), **kwargs)
