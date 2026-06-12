"""ノック95: Code Interpreter — サンドボックスでコードを実行させる

エージェントにコードを「書かせる」だけでなく「実行させて」結果を返したい
場面(データ分析、計算、グラフ生成)がある。第2章の python_repl は
ローカル実行で危険を伴うが、AgentCore Code Interpreter は隔離された
マネージドサンドボックスで安全に実行する。

このノックは Code Interpreter ツールをエージェントに持たせる形を示す。
実行には AWS の AgentCore 権限が必要。

前提: AgentCore の権限(Code Interpreter は事前作成不要、デフォルトを使える)
実行: uv run knocks/k095_code_interpreter.py
"""

import os

from common import make_model

from strands import Agent, tool
from bedrock_agentcore.tools.code_interpreter_client import CodeInterpreter

REGION = os.environ.get("AWS_REGION", "us-west-2")


@tool
def run_python(code: str) -> str:
    """Python コードをサンドボックスで実行し、標準出力を返す。"""
    interpreter = CodeInterpreter(region=REGION)
    interpreter.start()
    try:
        response = interpreter.invoke("executeCode", {"language": "python", "code": code})
        # ストリーム応答からテキストを集める
        chunks = []
        for event in response.get("stream", []):
            result = event.get("result", {})
            for content in result.get("content", []):
                if content.get("type") == "text":
                    chunks.append(content["text"])
        return "\n".join(chunks) or "(出力なし)"
    finally:
        interpreter.stop()


if __name__ == "__main__":
    agent = Agent(model=make_model(), tools=[run_python])

    agent(
        "1から100までの素数の個数を Python で数えて。"
        "run_python ツールでコードを実行して、結果の数を教えて。"
    )
    # モデルがコードを書く → サンドボックスで実行 → 結果を見て答える。
    # ローカルの python_repl(第2章)と違い、無限ループや危険な操作が隔離される
