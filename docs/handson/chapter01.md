# 第1章 ハンズオン: エージェントの基礎(ノック1〜10)

この章では Strands Agents の最小単位 —「エージェントを作って呼ぶ」— を徹底的に触る。
ツールもマルチエージェントもまだ出てこない。その代わり、**呼び出しの戻り値に何が入っているか**、
**履歴がどう持たれるか** を正確に理解するのがゴール。ここが曖昧だと後の章が全部曖昧になる。

コードは `agents/knocks/` にある。写経してもいいし、実行して改造するだけでもいい。

## 事前準備

```bash
cd agents
uv sync
export AWS_PROFILE=your-profile
export AWS_REGION=us-west-2
```

- Bedrock コンソールで Claude のモデルアクセスを有効化しておく
- 動作確認: `uv run knocks/k001_hello_agent.py` が応答を返せば準備完了

---

## ノック1: Hello Agent

📄 `knocks/k001_hello_agent.py`

```python
from common import make_model
from strands import Agent

agent = Agent(model=make_model())
agent("こんにちは!あなたは何ができますか?3行で教えて。")
```

これが Strands のベースになる形。実は `Agent()` だけでも動く(その場合はデフォルトの
Claude Sonnet が使われる)が、このノック集ではコスト節約のため `knocks/common.py` の
`make_model()` で **Claude Haiku 4.5**(Sonnet の約1/3の価格)を明示している。
`KNOCK_MODEL_ID` 環境変数で別モデルへの差し替えも可能。
呼び出すと応答が**ストリーミングで標準出力に流れる**。

**観察ポイント**

- `print()` を書いていないのに応答が表示される。これはデフォルトの
  `callback_handler`(`PrintingCallbackHandler`)の仕事。後のノックで `None` にして消す
- エージェントとは突き詰めると「モデル + (ツール) + 会話ループ」のオブジェクトに過ぎない

**発展**: `result = agent(...)` の戻り値を `print(type(result))` してみる(→ノック10の伏線)

---

## ノック2: ペルソナエージェント

📄 `knocks/k002_persona.py`

`system_prompt` は全ターンに効く「役割設定」で、ユーザー入力よりも強い前提として扱われる。

```python
agent = Agent(
    system_prompt="あなたは大阪出身のベテラン板前です。関西弁で話し、..."
)
```

**観察ポイント**

- デバッグの質問をしても板前キャラが維持される
- system_prompt は `agent.messages` には現れない(履歴とは別枠で毎回送られる)

**発展**: 「標準語で話して」とユーザー側から頼んでキャラが崩れるか試す。
system_prompt とユーザー指示の力関係を体感する

---

## ノック3: モデル設定

📄 `knocks/k003_model_config.py`

モデルを明示的に作って渡す。これ以降ずっと使う形。

```python
from strands.models import BedrockModel

model = BedrockModel(
    model_id="global.anthropic.claude-haiku-4-5-20251001-v1:0",
    temperature=0.0,
    max_tokens=100,
)
agent = Agent(model=model)
```

(スクリプトでは `make_model(temperature=..., max_tokens=...)` 経由で同じことをしている)

スクリプトは同じ俳句プロンプトを temperature 0.0 / 1.0 ×各2回実行する。

**観察ポイント**

- `temperature=0.0` は2回ともほぼ同じ出力、`1.0` は毎回変わる
- 分類・抽出系タスクは低温、創作系は高温が定石
- `max_tokens` を 20 などに絞ると俳句が途中で切れる(→ノック10の `stop_reason` が
  `max_tokens` になる)

---

## ノック4: モデル比較

📄 `knocks/k004_model_compare.py`

`model_id` を差し替えるだけで別モデルになる。コードの他の部分は一切変わらない —
この「モデル非依存」が Strands の設計思想(model-driven)の核。

**観察ポイント**

- 応答の質・文体・所要時間の差
- 利用できるモデルはリージョンとモデルアクセス設定次第。エラーが出たら
  `MODEL_IDS` を自分の環境で有効な ID に書き換える

**発展**: 第7章では Bedrock 以外(Anthropic API 直、Ollama 等)に差し替える。
やることは今回と同じで、model オブジェクトを変えるだけ

---

## ノック5: 非同期呼び出し

📄 `knocks/k005_async.py`

```python
result = await agent.invoke_async(prompt)
```

同期呼び出し `agent(...)` の非同期版。`asyncio.gather` で2エージェントを並行実行すると、
所要時間が「2つの合計」ではなく「遅い方」に近くなる。

**観察ポイント**

- `callback_handler=None` にしている理由: 並行実行中に2つのストリーミング出力が
  混ざって表示が壊れるから。戻り値だけ受け取って後でまとめて表示している
- WebUI のバックエンドやマルチエージェント(第9章)は基本この非同期版を使う

**発展**: `gather` をやめて `await` を2回直列に並べ、所要時間の差を測る

---

## ノック6: マルチターン会話

📄 `knocks/k006_multiturn.py`

同じ `Agent` インスタンスへの呼び出しは履歴(`agent.messages`)を共有する。
「寿司が好き」と伝えた後に「何が好きだった?」と聞くと答えられるのはこのため。

**観察ポイント**

- `agent.messages` は `{"role": "user" | "assistant", "content": [block, ...]}` のリスト。
  この構造は第4章(履歴の直接操作)、第6章(セッション永続化)でそのまま使う
- 「記憶」の正体は単なるリスト。エージェントを作り直せば全部忘れる
- 履歴は毎回モデルに全部送られる = ターンが進むほど入力トークンが増える
  (→第4章の ConversationManager がこの問題を解決する)

**発展**: 2つの `Agent` インスタンスを作って交互に話しかけ、記憶が混ざらないことを確認

---

## ノック7: 構造化出力

📄 `knocks/k007_structured_output.py`

```python
class Recipe(BaseModel):
    name: str
    minutes: int
    ingredients: list[str]
    steps: list[str]

recipe = agent.structured_output(Recipe, "卵かけご飯のレシピを教えて。")
```

戻り値は文字列ではなく **検証済みの `Recipe` インスタンス**。
「LLM の出力を正規表現でパースする」地獄から解放される、実務で最重要の機能のひとつ。

**観察ポイント**

- `recipe.minutes * 2` ができる = ちゃんと `int` 型
- `Field(description=...)` がモデルへのヒントになる。説明の質 = 出力の質
- バリデーションに失敗すると Pydantic のエラーになる(壊れた JSON が黙って通ることはない)

**発展**: `minutes: int = Field(ge=1, le=60)` のような制約を付けて挙動を見る。
ネストしたモデル(`list[Step]`)も試す

---

## ノック8: 画像入力

📄 `knocks/k008_image_input.py`

プロンプトは文字列だけでなく「コンテンツブロックのリスト」を渡せる。

```python
agent([
    {"image": {"format": "png", "source": {"bytes": image_bytes}}},
    {"text": "この画像に写っているものを説明して。"},
])
```

```bash
uv run knocks/k008_image_input.py ~/Pictures/cat.png
```

**観察ポイント**

- ノック6で見た `content` ブロックの構造と同じ。テキストも画像も「ブロックの一種」
- 画像はトークンを大きく消費する(ノック10のメトリクスで確認できる)

---

## ノック9: ドキュメント入力

📄 `knocks/k009_document_input.py`

画像と同じ要領で `document` ブロックを使うと PDF などを渡せる。

```bash
uv run knocks/k009_document_input.py ./some-paper.pdf
```

**観察ポイント**

- 「PDF を読んで要約するエージェント」がツールなしの素の機能でできてしまう
- 大きいドキュメントはコンテキスト溢れの原因になる(→第4章のノック39)

---

## ノック10: 結果の解剖

📄 `knocks/k010_result_anatomy.py`

`agent(...)` の戻り値 `AgentResult` を分解する。

| フィールド | 中身 |
|---|---|
| `str(result)` | 最終応答のテキスト |
| `result.stop_reason` | 停止理由: `end_turn` / `max_tokens` / `tool_use` など |
| `result.message` | 最終 assistant メッセージ(content ブロックのリスト) |
| `result.metrics.accumulated_usage` | 入力/出力/合計トークン数 |
| `result.metrics.cycle_count` | エージェントループの周回数 |
| `result.metrics.accumulated_metrics` | レイテンシなど |

**観察ポイント**

- 今はツールがないので `cycle_count` は 1。第2章でツールを持たせると、
  ツール実行のたびにループが回って 2 以上になる。**この値の変化を見ると
  「エージェントループ」が腹落ちする**
- トークン数 × モデル単価 = コスト。第8章のコスト集計はこの値の集計に過ぎない

**発展**: ノック3の `max_tokens=20` を再現して `stop_reason` が変わるのを確認する

---

## 第1章のまとめ

- エージェント = `Agent(model, system_prompt, ...)`。呼べば `AgentResult` が返る
- 会話履歴は `agent.messages` のただのリスト。マルチターンの「記憶」の正体
- プロンプトは文字列 or コンテンツブロックのリスト(テキスト・画像・ドキュメント)
- `structured_output` で型付きの結果を得るのが実務の基本形
- `AgentResult.metrics` にトークン・サイクル数・レイテンシが全部入っている

次章(第2章: ツールの基礎)では、エージェントに `@tool` で道具を持たせて、
`cycle_count` が増える様子 — つまりエージェントループの実体 — を観察する。

> 🔁 **ループ視点**: ノック10で見た `cycle_count`(何周したか)と `stop_reason`(なぜ止まったか)は、
> 実は**ループエンジニアリング**の出発点。エージェントは「観察→行動→観察」の反復ループで、
> この2つはその制御信号だ。詳しくは [loop-engineering.md](loop-engineering.md) と第11章。
