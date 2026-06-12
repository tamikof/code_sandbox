# 第3章 ハンズオン: ツール応用と MCP(ノック21〜30)

第2章で「ツールを持たせる」を覚えた。この章は**ツールが増えてきたとき・本格化したとき**の技術:
実行の制御(直接呼び出し・並列化)、MCP によるツールの取り込み、大量ツールの絞り込み。

この章から **MCP (Model Context Protocol)** が登場する。MCP は「ツールの標準配布形式」で、
世の中で公開されている MCP サーバをそのままエージェントのツールにできる。
第10章の AgentCore Gateway も MCP の応用なので、ここで仕組みを掴んでおくと後が楽。

## ノック21: ツールの直接呼び出し

📄 `knocks/k021_direct_tool_call.py`

```python
result = agent.tool.get_user_plan(user_id="u-001")  # モデルを介さず強制実行
```

**観察ポイント**

- モデルに「使うかどうか」を委ねたくない処理(ログイン後のユーザー情報取得など)は
  `agent.tool.<ツール名>(引数)` でコードから確実に実行できる
- 実行結果はデフォルトで会話履歴にも記録される(`record_direct_tool_call`)。
  だから直後に「どのプランでしたか?」と聞くと、モデルはツールを呼び直さずに答える
- 現行 SDK では per-request の `tool_choice` は公開されておらず、強制実行はこの直接呼び出しで行う

## ノック22: 動的ツール管理

📄 `knocks/k022_dynamic_tools.py`

```python
agent.tool_registry.register_tool(transfer_money)  # 実行中に追加
```

**観察ポイント**

- 送金ツールがない段階では、モデルは「送金できません」と正しく断る(ツールがない=できない)
- 追加後は同じ質問に応えられる。「権限に応じてツールを増減する」のが実務パターン
- `agent.tool_names` でいつでも現在のツール一覧を確認できる

## ノック23・24: 並列 vs 直列ツール実行

📄 `knocks/k023_concurrent_tools.py` / `k024_sequential_tools.py`

モデルが1ターンで複数ツールを呼んだときの実行戦略を `tool_executor` で制御する。

**観察ポイント**

- `ConcurrentToolExecutor`(デフォルト)では1秒かかるツール2つが約1秒で終わる。
  `SequentialToolExecutor` だと約2秒。**async ツール(ノック15)はここで効いてくる**
- 直列にしたい場面: 同じファイルを触るツール、順序依存の操作、レート制限のある API
- テスト `test_chapter03.py` では 0.2 秒のツール2つの所要時間差で並列性を検証している

## ノック25: ストリーミングツール

📄 `knocks/k025_streaming_tool.py`

```python
@tool
async def batch_convert(count: int):
    for i in range(1, count + 1):
        yield f"変換中... {i}/{count}"   # 途中経過(ストリームに流れる)
    yield f"{count}件のファイルを変換しました"  # 最後の yield だけが結果になる
```

**観察ポイント**

- `stream_async` のイベントに `tool_stream_event` が現れ、`data` に yield した値が入る
- **最後の yield がツールの最終結果**としてモデルに渡る(途中経過はモデルに渡らない)
- 「実行に1分かかるツールの進捗バー」は WebUI(第10章)でこの仕組みを使って作る

## ノック26: MCP (stdio)

📄 `knocks/k026_mcp_stdio.py`

AWS Documentation MCP サーバ(公式ドキュメント検索)を `uvx` でサブプロセス起動して接続。

```python
aws_docs_mcp = MCPClient(lambda: stdio_client(
    StdioServerParameters(command="uvx", args=["awslabs.aws-documentation-mcp-server@latest"])
))
with aws_docs_mcp:                       # 接続中だけツールが有効
    tools = aws_docs_mcp.list_tools_sync()
    agent = Agent(model=make_model(), tools=tools)
```

**観察ポイント**

- **`with` ブロックが必須**。MCP ツールはクライアントの接続中だけ有効で、
  ブロックを出た後に使うとエラーになる(ハマりどころ No.1)
- 自分では1行もツールを書いていないのに「AWS ドキュメントを調べるエージェント」が完成する

## ノック27: MCP (Streamable HTTP)

📄 `knocks/k027_mcp_http.py`

リモートの MCP サーバには HTTP で接続する。別ターミナルで
`uv run knocks/k028_mcp_server.py http` を立ててから実行。

**観察ポイント**

- 変わるのはトランスポート(`stdio_client` → `streamablehttp_client`)だけ。ツールの使い方は同一
- AgentCore Gateway(第10章)はこの Streamable HTTP で社内 API を MCP 化して配る仕組み

## ノック28: 自作 MCP サーバ

📄 `knocks/k028_mcp_server.py`(サーバ)+ `k028_mcp_connect.py`(クライアント)

FastMCP なら約30行で MCP サーバが書ける。

```python
mcp = FastMCP("recipe-server")

@mcp.tool()
def search_recipe(ingredient: str) -> str:
    """指定した食材を使うレシピを検索する。"""
    ...
```

**観察ポイント**

- `@mcp.tool()` の書き味は Strands の `@tool` とほぼ同じ(型ヒント+docstring → スキーマ)
- 違いは**配布範囲**: `@tool` はそのプロセス内だけ、MCP サーバは Claude Desktop など
  任意の MCP クライアントから使える。「社内 API のツール化」は MCP で作ると使い回せる
- テストではこのサーバを実際にサブプロセス起動して接続している(`test_mcp_server_roundtrip`)

## ノック29: 複数ソースのツール統合

📄 `knocks/k029_multi_mcp.py`

MCP ツール + 自作 `@tool` + コミュニティツールを1つの `tools` リストに混ぜる。

**観察ポイント**

- 出自の違うツールを区別するコードは1行もない。モデルから見ればどれも同じ「ツール」
- 実務エージェントの構成はほぼ必ずこの形になる

## ノック30: 大量ツールの絞り込み

📄 `knocks/k030_tool_selection.py`

ツールが何十個もあると、スキーマでトークンを浪費し選択精度も落ちる。
対策は2段構え: **軽い1段目がカタログから必要ツールを選び、2段目が選ばれたツールだけで解く**。

```python
selection = selector.structured_output(ToolSelection, f"...タスク: {task}...カタログ: {catalog}")
worker = Agent(model=make_model(), tools=filter_tools(ALL_TOOLS, selection.tool_names))
```

**観察ポイント**

- 1段目はツールを1つも持たない。見るのは「名前と説明のカタログ」だけ(スキーマ全体より軽い)
- ノック7の structured_output がここで実戦投入される(選択結果を `list[str]` で確実に受ける)
- 公式の `retrieve` ツールはこれを Bedrock Knowledge Base の埋め込み検索でやる本格版

---

## この章のテスト

`tests/test_chapter03.py`(`uv run pytest`)。見どころは2つ:

- **並列性のテスト** — 0.2秒×2 のツールが Concurrent なら 0.35秒未満、Sequential なら以上、
  という所要時間で実行戦略を検証
- **MCP の実通信テスト** — 自作 FastMCP サーバを実際にサブプロセス起動して
  list_tools → エージェントループまで通す(ネットワーク・AWS 不要)

## 第3章のまとめ

- 強制実行は `agent.tool.xxx()`、実行中の増減は `tool_registry.register_tool()`
- 複数ツールの同時呼び出しはデフォルト並列。直列が必要なら `SequentialToolExecutor`
- ストリーミングツールは途中経過を yield、最後の yield が結果
- MCP は「ツールの標準配布形式」。stdio(ローカル)と Streamable HTTP(リモート)があり、
  接続は `with` ブロック内で。FastMCP なら自作も30行
- ツールが増えたら「選んでから持たせる」(カタログ→絞り込みの2段構え)

次章(第4章)はコンテキストと会話管理。「履歴が長くなると何が起きるか」を扱う。
