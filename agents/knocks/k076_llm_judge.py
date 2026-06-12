"""ノック76: LLM-as-a-Judge — 別エージェントに出力を採点させる

エージェントの出力品質を自動で測りたい。決まった正解がない応答(要約、
カスタマー対応など)では、別の LLM に評価基準を渡して採点させるのが定番。
「評価器」も Strands のエージェント + structured_output で作れる。

実行: uv run knocks/k076_llm_judge.py
"""

from common import make_model
from pydantic import BaseModel, Field

from strands import Agent


class Evaluation(BaseModel):
    """採点結果。スコアと理由を構造化して受け取る。"""

    score: int = Field(ge=1, le=5, description="総合評価(1=悪い 〜 5=良い)")
    helpful: bool = Field(description="ユーザーの役に立つ回答か")
    polite: bool = Field(description="丁寧な言葉遣いか")
    reason: str = Field(description="採点の理由")


JUDGE_PROMPT = """あなたはカスタマーサポートの品質評価者です。
以下の【質問】に対する【回答】を、有用性・丁寧さの観点で採点してください。

【質問】
{question}

【回答】
{answer}
"""


def judge(question: str, answer: str) -> Evaluation:
    """回答を採点する評価エージェント。"""
    evaluator = Agent(model=make_model(), callback_handler=None)
    return evaluator.structured_output(
        Evaluation, JUDGE_PROMPT.format(question=question, answer=answer)
    )


if __name__ == "__main__":
    question = "注文した商品がまだ届きません。どうすればいいですか?"

    # 評価対象のエージェント(被験者)
    support = Agent(
        model=make_model(),
        system_prompt="あなたは丁寧なカスタマーサポートです。",
        callback_handler=None,
    )
    answer = str(support(question))

    # 評価器に採点させる
    evaluation = judge(question, answer)
    print(f"\n===== 採点結果 =====")
    print(f"スコア  : {evaluation.score}/5")
    print(f"有用    : {evaluation.helpful}")
    print(f"丁寧    : {evaluation.polite}")
    print(f"理由    : {evaluation.reason}")
