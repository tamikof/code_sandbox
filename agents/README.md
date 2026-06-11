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
