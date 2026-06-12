# 第9章 ハンズオン: マルチエージェント(ノック81〜90)

1つのエージェントでは荷が重いタスクを、役割を分けた複数エージェントで解く。
Strands には協調のパターンが複数あり、**「誰が次に動くかを誰が決めるか」**で整理できる:

| パターン | 制御 | 誰が次を決める | 向く用途 |
|---|---|---|---|
| Agents as Tools(81) | 中央集権 | 司令塔が明示的に委譲 | 役割が明確な分業 |
| Swarm(82・83) | 自律分散 | エージェント自身がハンドオフ | 柔軟な引き継ぎ |
| Graph(84〜86) | 決定的 | 開発者が定義した DAG | 再現性が要る業務処理 |
| Workflow(87) | 宣言的 | タスクの依存関係 | バッチ的なタスク列 |
| A2A(88・89) | 分散 | プロトコル越しに発見・依頼 | フレームワーク/言語を跨ぐ |

ほとんどのノックが MockModel で構造をテストできる(81〜86・90 はテスト済み、A2A はサーバ実起動)。

## ノック81: Agents as Tools

📄 `knocks/k081_agents_as_tools.py`

```python
orchestrator = Agent(model=..., tools=[
    researcher.as_tool(name="researcher", description="調査を依頼する"),
    math_agent.as_tool(name="math_expert", description="計算を依頼する"),
])
```

**観察ポイント**

- `agent.as_tool()` で任意のエージェントがツールになる。司令塔はそれを
  第2章のツールと同じ感覚で呼ぶ ── マルチエージェントの最も素直な入口
- 制御は中央集権的。司令塔が「これは researcher の仕事」と明示的に振り分ける
- 専門エージェントは自分の system_prompt とツールを持つ(math_expert は calculator を持つ)

## ノック82: Swarm 入門

📄 `knocks/k082_swarm_basics.py`

```python
swarm = Swarm([planner, budgeter, writer], entry_point=planner)
```

**観察ポイント**

- 81と逆で、**対等なエージェントが自律的にバトンを渡す**。Swarm が各エージェントに
  「他の誰かにハンドオフする」ツールを自動で与える
- planner → budgeter → writer と引き継がれる。誰がいつ渡すかはプロンプト次第
- `result.node_history` で実際の経路(誰がどの順で動いたか)が分かる

## ノック83: Swarm 制御

📄 `knocks/k083_swarm_control.py`(AWS 不要)

Swarm は放置すると**2人が延々と譲り合う無限ループ**に陥りうる。上限で守る。

| パラメータ | 役割 |
|---|---|
| `entry_point` | 最初に動くエージェント |
| `max_handoffs` / `max_iterations` | 回数の上限 |
| `node_timeout` / `execution_timeout` | 時間の上限 |
| `repetitive_handoff_detection_window` | 往復ループの検出 |

**観察ポイント**

- 自律性の代償は予測不能性。**本番の Swarm は必ず上限を設定する**のが鉄則
- テストでは `entry_point=b` を指定して、確かに b から始まることを検証している

## ノック84: Graph 直列パイプライン

📄 `knocks/k084_graph_pipeline.py`

```python
builder.add_edge("research", "analyze")
builder.add_edge("analyze", "write")
```

**観察ポイント**

- Swarm の自律性とは正反対。**開発者が処理の流れを DAG で固定**する
- あるノードの出力が次のノードの入力に自動で渡る(research の結果が analyze に入る)
- 再現性が命の業務処理(レポート生成パイプライン等)はこちら

## ノック85: Graph 条件分岐

📄 `knocks/k085_graph_conditional.py`

エッジに `condition`(`GraphState` を見て True/False を返す関数)を付けると分岐する。

```python
builder.add_edge("classify", "tech", condition=classified_as_tech)
builder.add_edge("classify", "general", condition=lambda s: not classified_as_tech(s))
```

**観察ポイント**

- 「分類 → 振り分け」のルーターパターン。技術問題は tech へ、それ以外は general へ
- `condition` は `state.results["classify"].result` を読んで判定する。
  前のノードの出力で次の経路が変わる
- テストでは「技術問題なら general は実行されない」ことまで検証

## ノック86: Graph 並列集約

📄 `knocks/k086_graph_parallel.py`

1入力を複数の専門家に同時に渡し(ファンアウト)、結果を集約ノードでまとめる(ファンイン)。

```
       ┌→ security ┐
input ─┼→ perf    ─┼→ aggregator
       └→ ux      ┘
```

**観察ポイント**

- 同じノード(aggregator)に複数エッジが入ると、Graph は**親が全部終わるまで待つ**
- 3人のレビュアーは並列実行され、aggregator は1回だけ動く(テストで execution_count=1 を検証)
- 多角的レビュー・アンサンブルの定番構成

## ノック87: Workflow ツール

📄 `knocks/k087_workflow_tool.py`

エージェントをノードにする Graph に対し、`workflow` ツールは1エージェントに
「依存関係つきのタスク列」を実行させる手軽な方式。

```python
agent.tool.workflow(action="create", workflow_id="...", tasks=[
    {"task_id": "extract", ...},
    {"task_id": "analyze", "dependencies": ["extract"], ...},
])
```

**観察ポイント**

- タスク定義・依存解決・並列実行をツール側が面倒見る。Graph を組むより手軽
- Graph(コードで構造を組む)と Workflow(データでタスクを宣言)の使い分け

## ノック88・89: A2A(サーバ / クライアント)

📄 `knocks/k088_a2a_server.py` / `k089_a2a_client.py`(要 a2a extra、サーバ実起動)

A2A (Agent-to-Agent) は**エージェント間通信の標準プロトコル**。MCP がツールの標準なら、
A2A はエージェントそのものの標準。

- **サーバ(88)**: `A2AServer(agent=...)` で自分のエージェントを公開。`name` と
  `description` が「エージェントカード」(名刺)になり、`/.well-known/agent-card.json` で配られる
- **クライアント(89)**: `A2AClientToolProvider(known_agent_urls=[...])` が
  「発見(a2a_discover_agent)」「送信(a2a_send_message)」ツールを提供。
  オーケストレーターがリモートのエージェントを自分のツールのように使う

**観察ポイント**

- 81〜87 が同一プロセス内の協調なのに対し、A2A は**プロセス・マシン・フレームワーク・
  言語を跨ぐ**分散マルチエージェント
- 第10章の AgentCore Runtime は、デプロイした各エージェントを A2A で繋ぐ構成と相性が良い

## ノック90: マルチエージェント観測

📄 `knocks/k090_multiagent_observability.py`(AWS 不要)

マルチエージェントは「どのエージェントが重いか」が見えないと改善できない。
Graph / Swarm の結果には**ノードごとのメトリクスが集約**されている。

**観察ポイント**

- `result.accumulated_usage`(全体)と `result.results[node_id].accumulated_usage`(ノード別)
- `completed_nodes` / `total_nodes` で進捗、`execution_time` でノード別の所要時間
- 第8章の OTel トレース(73)を有効にすると、これがネストしたスパンの木として
  収集基盤に送られ、ボトルネックを視覚的に追える

---

## この章のテスト

`tests/test_chapter09.py`(全部 AWS 不要、計 68 passed)。見どころ:

- **Agents as Tools** — オーケストレーターが specialist ツールを実際に呼んだことを履歴で検証
- **条件分岐** — 技術問題ルートで general ノードが**実行されない**ことを検証(分岐が効いている)
- **並列集約** — 4ノードすべて実行 + aggregator が1回だけ(ファンインの待ち合わせ)を検証
- **観測** — Graph 結果からノード別トークンが取れることを検証

## 第9章のまとめ

- 協調パターンは制御の所在で選ぶ: 中央集権(as Tools)/ 自律(Swarm)/ 決定的(Graph)/
  宣言的(Workflow)/ 分散(A2A)
- Swarm は柔軟だが暴走しうる ── 上限設定は必須
- Graph は条件分岐(condition 付きエッジ)と並列集約(ファンイン)で複雑なフローを表現
- A2A はプロセス/言語を跨ぐエージェント連携の標準プロトコル
- マルチエージェントの観測は結果オブジェクトのノード別メトリクス + OTel トレース

次章(第10章)はいよいよ AgentCore Runtime へのデプロイと、TypeScript の WebUI 統合。
ここまで作ったエージェントを本番に出し、ブラウザから呼べるようにする。
