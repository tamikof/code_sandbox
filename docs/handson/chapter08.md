# 第8章 ハンズオン: 観測性と評価(ノック71〜80)

「動いている」と「ちゃんと動いている」は別物。この章は2つの問いに答える道具を揃える:

- **観測性**(71〜75, 80): 何が起きているか? — ログ・メトリクス・トレース
- **評価**(76〜79): 良い仕事をしているか? — LLM採点・ツール選択・回帰・コスト

ほとんどのノックが AWS 不要(モックで完結)。実データの収集基盤連携(74・80)だけ
外部リソースが要る。

## ノック71: ロギング

📄 `knocks/k071_logging.py`(AWS 不要)

```python
logging.getLogger("strands").setLevel(logging.DEBUG)
```

**観察ポイント**

- Strands は標準 logging を使う。`"strands"` ロガーを DEBUG にすると、モデルへの
  リクエスト・ツール選択・サイクルの判断が流れる
- 本番では `strands.tools` など特定のロガーだけ DEBUG にして絞る

## ノック72: メトリクス取得

📄 `knocks/k072_metrics.py`(AWS 不要)

`AgentResult.metrics.get_summary()` で、その呼び出しの全統計が dict になる。

| 取れるもの | キー |
|---|---|
| サイクル数 | `total_cycles` |
| トークン | `accumulated_usage.totalTokens` |
| レイテンシ | `accumulated_metrics.latencyMs` |
| ツール別統計 | `tool_usage.<名前>.execution_stats`(呼出回数・成功率・平均時間) |

**観察ポイント**

- ツール別に「成功率」「平均実行時間」が取れる。遅いツール・失敗するツールの特定に直結
- 後続のコスト集計(79)も観測ダッシュボード(80)も、すべてこのデータが源泉

## ノック73: OTel トレース

📄 `knocks/k073_otel_traces.py`(AWS 不要)

```python
telemetry = StrandsTelemetry()
telemetry.setup_console_exporter()
```

**観察ポイント**

- 1回の呼び出しが「スパンの木」になる: 呼び出し → サイクル → モデル呼び出し / ツール実行
- メトリクス(72)は「数字の集計」、トレース(73)は「1リクエストの時系列の木」。
  前者はダッシュボード向き、後者は「この1件がなぜ遅い/失敗したか」の調査向き
- `setup_console_exporter()` でまず標準出力で形を見るのが入門に最適

## ノック74: トレースの送信

📄 `knocks/k074_otlp_export.py`(要 OTLP 受信先)

コンソール出力を `setup_otlp_exporter()` に替えると、Langfuse / Jaeger / Grafana Tempo /
Datadog などに送れる。設定は標準の `OTEL_EXPORTER_OTLP_*` 環境変数。

**観察ポイント**

- ローカル Jaeger なら `docker run ... jaegertracing/all-in-one` ですぐ試せる
- Langfuse は `OTEL_EXPORTER_OTLP_HEADERS` に認証を入れる。LLM 特化の収集基盤として人気

## ノック75: トレース属性

📄 `knocks/k075_trace_attributes.py`(AWS 不要)

```python
Agent(..., trace_attributes={"user.id": "u-001", "app.version": "1.2.0"})
```

**観察ポイント**

- 全スパンに付く共通タグ。「user.id=u-001 のリクエストだけ」「app.version 別のエラー率」
  のような絞り込みが収集基盤でできるようになる
- OpenTelemetry の semantic convention に沿った名前にしておくと既製ダッシュボードが効く

## ノック76: LLM-as-a-Judge

📄 `knocks/k076_llm_judge.py`

正解のない応答(要約・接客など)の品質を、**別の LLM に採点させる**。

```python
class Evaluation(BaseModel):
    score: int = Field(ge=1, le=5)
    helpful: bool
    reason: str

evaluator.structured_output(Evaluation, JUDGE_PROMPT.format(...))
```

**観察ポイント**

- 評価器も Strands エージェント + structured_output(ノック7・70の応用)。
  スコアを `int` で、理由を `str` で構造化して受け取る
- 採点軸を Pydantic フィールドで定義する = 「何を良しとするか」がコードに明文化される

## ノック77: ツール選択の評価

📄 `knocks/k077_tool_eval.py`(AWS 不要)

応答テキストではなく**正しい行動(ツール選択)**を測る。テストケース
「入力 → 期待ツール」を並べ、実際に呼ばれたツールと突き合わせて正答率を出す。

**観察ポイント**

- `tools_called()` で履歴から実際の `toolUse` を抽出して照合する
- エージェントの正しさは「何を言ったか」だけでなく「何をしたか」でも測る、という視点
- この CASES をそのまま pytest に載せれば回帰テストになる(→ ノック78)

## ノック78: 回帰テスト

📄 `knocks/k078_regression.py`(AWS 不要)

「プロンプトを変えたら別のケースが壊れた」を防ぐ評価スイート。
`must_include` / `must_exclude` で応答が満たすべき条件を宣言する。

**観察ポイント**

- `evaluate(case, model_factory=...)` で**モデルを差し替え可能**にしてある。
  CI ではモック(無料・高速・決定的)、本番前チェックでは実モデル、と使い分けられる
- テスト(`test_regression_catches_bad_output`)では「わざと悪い応答を入れると
  スイートが不合格を出す」ことまで検証 — 評価器自体が機能している保証

## ノック79: コスト集計

📄 `knocks/k079_cost.py`(AWS 不要)

メトリクス(72)のトークン数 × 単価 = コスト。会話別・モデル別に集計する。

**観察ポイント**

- 同じ使用量(入力1万・出力2千トークン)でも haiku $0.02 / opus $0.10 と5倍差。
  「普段は Haiku」(第7章で設定した方針)の効果が金額で見える
- 実運用では `accumulated_usage` は累計なので、ターンごとの差分を取って集計する

## ノック80: CloudWatch 連携

📄 `knocks/k080_cloudwatch.py`(参考用、要 AWS)

AWS 上では OTel 出力を ADOT Collector 経由で CloudWatch / X-Ray に流す。

```
Strands (OTLP) → ADOT Collector → CloudWatch Logs / Metrics / X-Ray
```

**観察ポイント**

- ノック72・73 で見たデータを、マネージドな GenAI ダッシュボードに載せる配線
- **AgentCore Runtime にデプロイすると、この配線は概ね自動で入る**(第10章への布石)

---

## この章のテスト

`tests/test_chapter08.py`(全部 AWS 不要、計 61 passed)。見どころ:

- **メトリクスのテスト** — ツール成功時の `success_rate=1.0`、失敗時の `error_count=1` /
  `success_rate=0.0` を検証(観測データが正しく取れている保証)
- **回帰スイートのテスト** — 全ケース合格に加え、**わざと悪い応答が不合格になる**ことも検証。
  「評価器が壊れていないこと」を評価器自身でテストする入れ子構造
- **コストのテスト** — 単価計算の正しさ(100万×100万トークンで haiku=$6.0)と、
  トークン量に比例することを検証

## 第8章のまとめ

- 観測性は3階層: ログ(`strands` ロガー)/ メトリクス(`get_summary()` の集計)/
  トレース(OTel のスパンの木)。トレースは OTLP で外部基盤(Langfuse/Jaeger/CloudWatch)へ
- `trace_attributes` で user.id 等を付けて絞り込み可能にする
- 評価は2軸: 出力品質(LLM-as-a-Judge)と行動の正しさ(ツール選択)
- 評価ケースを pytest に載せれば回帰テスト。`model_factory` を差し替えてモック/実モデルを使い分け
- コストはトークン × 単価。Haiku 採用の効果が金額で見える

次章(第9章)はマルチエージェント。1つのエージェントから、協調する複数エージェントへ。
