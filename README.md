# Strands Agents 100本ノック

[Strands Agents](https://strandsagents.com/)(Python SDK)を基礎から本番デプロイまで
一周する演習集。エージェントは Python、WebUI は TypeScript、デプロイ先は
Amazon Bedrock AgentCore Runtime。

## 構成

| ディレクトリ | 中身 |
|---|---|
| [docs/strands-agents-100-knocks.md](docs/strands-agents-100-knocks.md) | 演習リスト(10章 × 10本 + 発展章) |
| [docs/handson/](docs/handson/) | 章ごとのハンズオン解説(chapter01〜11 + testing + loop-engineering) |
| [docs/handson/loop-engineering.md](docs/handson/loop-engineering.md) | **ループエンジニアリング**(100本を貫く横断テーマ / 第11章の前提) |
| [agents/](agents/) | Python 実装(`knocks/k001`〜`k107` + テスト) |
| [webui/](webui/) | TypeScript の最小チャット UI(第10章) |

## クイックスタート

```bash
# Python 側(エージェント)
cd agents
uv sync
uv run pytest                        # 81 tests、AWS 不要
uv run knocks/k001_hello_agent.py    # 要 AWS 認証情報(Bedrock)

# TypeScript 側(WebUI、第10章)
cd webui
npm install
npm test                             # 10 tests、ネットワーク不要
npm run dev
```

モデルはデフォルトで Claude Haiku 4.5(`KNOCK_MODEL_ID` 環境変数で変更可)。

## 進め方

第1章から順に。各章のハンズオン(`docs/handson/chapterNN.md`)を読みながら
`agents/knocks/` のスクリプトを実行・改造していく。AWS なしで動くノックには
ドキュメント中に「AWS 不要」と明記してある。

第11章「ループエンジニアリング」は、第1〜10章を「エージェントの外側のループをどう設計・制御するか」
という横断テーマで束ね直す発展章(全ノック AWS 不要)。各章末尾の「🔁 ループ視点」注釈が
その章とループ制御のつながりを示している。まず [loop-engineering.md](docs/handson/loop-engineering.md) を読むとよい。

テストの書き方(モックモデル方式)は [docs/handson/testing.md](docs/handson/testing.md) を参照。
