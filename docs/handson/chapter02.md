# 第2章 ハンズオン: ツールの基礎(ノック11〜20)

この章でエージェントが「ただのチャット」から「行動できるプログラム」になる。
ゴールは2つ:

1. **@tool の仕組みを理解する** — 関数の型ヒントと docstring がそのままモデルへの「説明書」になる
2. **エージェントループを体感する** — モデルがツールを選ぶ → Strands が実行 → 結果を見てモデルが続きを考える、の循環

第1章との大きな違いとして、この章からスクリプトの実行部分は
`if __name__ == "__main__":` で囲ってある。これはテスト(後述)から
ツール定義だけを import できるようにするため。

## ノック11: 電卓エージェント

📄 `knocks/k011_calculator.py`

```python
@tool
def add(a: float, b: float) -> float:
    """2つの数を足し算する。"""
    return a + b

agent = Agent(model=make_model(), tools=[add, multiply])
agent("(3 + 4) × 25 はいくつ?ツールを使って計算して。")
```

**観察ポイント**

- 「どの順でツールを使うか」は一切書いていないのに、add → multiply の順で呼ばれる。
  これがエージェントの本質: **手順はコードでなくモデルが決める**
- 実行ログに `Tool #1: add` のような表示が出る(デフォルトの callback handler の仕事)
- ノック10で仕込んだ伏線: `result.metrics.cycle_count` を見ると 3 になっているはず
  (add → multiply → 最終回答で3周)

**発展**: `agent("こんにちは")` だとツールは呼ばれない。モデルは「使うべきときだけ」使う

## ノック12: 型ヒントと docstring

📄 `knocks/k012_tool_spec.py`(LLM を呼ばないノック)

`@tool` が関数から生成したスキーマ(`tool.tool_spec`)を直接観察する。

**観察ポイント**

- `Literal["celsius", "fahrenheit"]` が JSON スキーマの `enum` になる
- docstring の `Args:` セクションが各パラメータの `description` になる
- **モデルはこのスキーマしか見ていない。** 関数の実装コードは見えない。
  だから docstring が雑だとツールは正しく使われない

**発展**: docstring から Args を消してスキーマがどう変わるか見る

## ノック13: ツールの使い分け

📄 `knocks/k013_multi_tools.py`

天気ツールと時刻ツールを持たせ、質問によって選択が変わるのを観察する。

**観察ポイント**

- 「いま何時?あと東京の天気も」のような複合質問では1ターンで複数ツールが呼ばれる
- ツール選択の決め手は **ツール名と description**。`get_weather` の description を
  「株価を返す」と書き換えると、モデルは天気の質問で使わなくなる(試してみる)

## ノック14: ツールのエラー処理

📄 `knocks/k014_tool_errors.py`

ゼロ除算の例外をわざと起こす。

**観察ポイント**

- ツール内の例外でプログラムは落ちない。`status: "error"` の toolResult として
  モデルに渡り、モデルは「0では割れません」のように自力でリカバリする
- エラーメッセージはモデルへの情報。`raise ValueError("bは0以外を指定")` のように
  **モデルが読んで分かるメッセージ**にするのが実務のコツ

## ノック15: 非同期ツール

📄 `knocks/k015_async_tool.py`

`async def` のツール。使い方は同期ツールと同じで、I/O 待ちの多いツールで効く。
真価は第3章の並列ツール実行(ノック23)で体感する。

## ノック16: ToolContext

📄 `knocks/k016_tool_context.py`

`@tool(context=True)` でツールがエージェント本体にアクセスできる。

```python
@tool(context=True)
def add_to_cart(item: str, tool_context: ToolContext) -> str:
    cart = tool_context.agent.state.get("cart") or []
    ...
```

**観察ポイント**

- カートの中身を「会話履歴」ではなく `agent.state` に持つ。履歴は要約・圧縮で
  消えることがある(第4章)が、state は消えない — 状態の置き場所の使い分けが学べる
- `tool_context.tool_use["toolUseId"]` で呼び出しの追跡 ID も取れる(監査ログに使う)

## ノック17: モジュール形式のツール

📄 `knocks/k017_module_tool.py` + `knocks/shout.py`

デコレータを使わず、`TOOL_SPEC` dict + 関数でツールを定義する形式。

**観察ポイント**

- 規約: **モジュール名 = 関数名**(`shout.py` の中に `def shout`)。
  これを破ると "Tool not found" になる(ハマりどころ)
- 戻り値の `ToolResult`(toolUseId / status / content)を自分で組み立てる。
  @tool が裏でやってくれていたことが見える
- コミュニティツールはすべてこの形式。ソースを読むときの予備知識になる

## ノック18: コミュニティツール入門

📄 `knocks/k018_community_tools.py`

`strands-agents-tools` の `calculator`(sympy ベースの数式評価)と `current_time`。

**観察ポイント**

- 2の100乗のような巨大な計算も正確(LLM の暗算ではなくツールの仕事)
- `calculator` のソースを読んでみる: ノック17のモジュール形式 + 多機能な実装

## ノック19: HTTP リクエスト

📄 `knocks/k019_http_request.py`

`http_request` ツールで GitHub API を叩き、結果を解釈させる。

**観察ポイント**

- URL・メソッドの組み立てはモデルがやる。JSON レスポンスの解釈もモデルがやる。
  「API を叩いて説明する」だけのコードを書く必要がなくなる
- レスポンスが大きいとトークンを大量消費する(コンテキストに全部入るため)。
  第3章以降の「結果を絞る」工夫につながる

## ノック20: ファイル操作エージェント

📄 `knocks/k020_file_agent.py`

`file_write` / `file_read` でファイルの書き込み→読み戻しをさせる。

**観察ポイント**

- 書き込み時に**確認プロンプト**が出る(`y` で許可)。危険な操作に人間の確認を
  挟む仕組みが最初から入っている — 第5章の human-in-the-loop の入口
- `BYPASS_TOOL_CONSENT=true` 環境変数で確認を省略できる(CI や自動化用)

---

## この章のテスト

`agents/tests/test_chapter02.py` に2種類のテストがある(`uv run pytest`)。

1. **ツール単体テスト** — `@tool` 付き関数は普通の関数として呼べるので、ただの関数テスト
   ```python
   from k011_calculator import add
   assert add(2, 3) == 5
   ```
2. **エージェントループテスト** — `MockModel` に「divide を a=10, b=0 で呼べ」と
   指示し、エラーが `status: "error"` で履歴に入ることを AWS なしで検証

詳しい方針は [testing.md](testing.md) を参照。

## 第2章のまとめ

- ツール = 型ヒント + docstring 付きの関数。スキーマがモデルへの唯一の説明書
- 手順を書かなくても、モデルがツールの選択・順序・引数を決める(エージェントループ)
- 例外は error 結果としてモデルに渡り、モデルが自力でリカバリする
- 状態は `agent.state`(ToolContext 経由)、危険な操作には確認プロンプト
- 定義方法は3つ: @tool デコレータ / モジュール形式 / コミュニティツール

次章(第3章)では MCP で外部のツール群を接続し、ツール実行の並列化・動的選択など
「ツールが増えてきたとき」の技術を学ぶ。
