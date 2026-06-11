"""ノック17で使うモジュール形式ツール。

モジュール形式の規約:
  - TOOL_SPEC(仕様の dict)を持つ
  - モジュール名と同じ名前の関数を持つ(shout.py → def shout)
コミュニティツール (strands-agents-tools) もこの形式で書かれている。
"""

from strands.types.tools import ToolResult, ToolUse

TOOL_SPEC = {
    "name": "shout",
    "description": "テキストを大声(全部大文字 + ビックリマーク)に変換する。",
    "inputSchema": {
        "json": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "変換したいテキスト"},
            },
            "required": ["text"],
        }
    },
}


# 戻り値の ToolResult はデコレータ形式と違い自分で組み立てる
def shout(tool: ToolUse, **kwargs) -> ToolResult:
    text = tool["input"]["text"]
    return {
        "toolUseId": tool["toolUseId"],
        "status": "success",
        "content": [{"text": text.upper() + "!!!"}],
    }
