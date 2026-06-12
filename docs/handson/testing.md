# 番外編: Strands エージェントのテスト

LLM を実際に呼ぶテストは「遅い・高い・毎回結果が変わる」の三重苦になる。
このリポジトリでは **モックモデル方式** でテストを書く: Strands の `Model`
インターフェースを実装した偽物のモデル(`agents/tests/mock_model.py`)に
「この順番でこう応答しろ」と指示しておき、エージェントループの**振る舞い**を検証する。

```bash
cd agents
uv run pytest          # AWS 認証情報なしで動く。コストゼロ
```

## テストの3つのレイヤー

| レイヤー | 何をテストするか | LLM 呼び出し |
|---|---|---|
| ツール単体 | `@tool` 関数を直接呼ぶ。ただの関数テスト | なし |
| エージェントループ | MockModel で「ツール実行→結果が履歴に入る→続行」の配線 | なし(モック) |
| 品質評価 | 本物のモデルで「良い応答か」を採点(第8章で扱う) | あり |

ポイント: **1段目と2段目で「壊れていないこと」を保証し、3段目は別物として扱う**。
「正しいツールが呼ばれるか」「良い文章を書くか」はモデルの性質であって、
ユニットテストの守備範囲ではない。

## MockModel の仕組み

`MockModel` は応答のリストを受け取り、呼ばれるたびに順番に返す。
文字列ならテキスト応答、`ToolCall(name, input)` ならツール呼び出しを
Bedrock のストリームイベント形式でエミュレートする。

```python
from mock_model import MockModel, ToolCall
from strands import Agent

# 1ターン目: add ツールを呼ぶ / 2ターン目: 最終回答
agent = Agent(
    model=MockModel([ToolCall("add", {"a": 2, "b": 3}), "答えは5です"]),
    tools=[add],
    callback_handler=None,
)
result = agent("2+3は?")

assert result.metrics.cycle_count == 2   # ツール実行でループが2周した
```

`MockModel.calls` にはモデルに渡されたリクエストが記録されるので、
「system_prompt が渡っているか」「ツール仕様が渡っているか」も検証できる
(`tests/test_agent_basics.py` / `tests/test_tool_loop.py` 参照)。

## 各章のツールをテストする

第2章以降のノックは、ツール定義をモジュールの先頭に置き、実行部分を
`if __name__ == "__main__":` で囲ってある。これによりテストから
`import k011_calculator` してツールだけを検証できる(`tests/conftest.py` が
`knocks/` をパスに追加している)。

```python
from k011_calculator import add

def test_add():
    assert add(2, 3) == 5   # @tool 付きでも普通の関数として呼べる
```
