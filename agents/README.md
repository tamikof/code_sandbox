# strands-knocks

Strands Agents 100本ノックの Python 実装。
ノック一覧は [docs/strands-agents-100-knocks.md](../docs/strands-agents-100-knocks.md)、
進め方の解説は [docs/handson/](../docs/handson/) を参照。

## セットアップ

```bash
cd agents
uv sync
```

AWS 認証情報(Bedrock の `InvokeModelWithResponseStream` 権限)が必要。

```bash
export AWS_PROFILE=your-profile       # または AWS_ACCESS_KEY_ID など
export AWS_REGION=us-west-2           # Claude が使えるリージョン
```

Bedrock コンソールの「モデルアクセス」で Anthropic Claude を有効化しておくこと。

## 実行

```bash
uv run knocks/k001_hello_agent.py
```

モデルはデフォルトで Claude Haiku 4.5(`knocks/common.py`)。
`KNOCK_MODEL_ID` 環境変数で差し替え可能。

## テスト

```bash
uv run pytest
```

AWS 認証情報は不要(モックモデルで動く)。詳細は
[docs/handson/testing.md](../docs/handson/testing.md) を参照。
