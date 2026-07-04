"""ノック104: 自己修正ループ(Reflexion)— 生成→自己批評→改稿

ループ設計の第2原則「各周を意味あるものに」。ただ再試行するだけでは前進しない。
Reflexion は「生成 → その出力を自分で批評 → 批評を踏まえて改稿」を繰り返すことで、
1周ごとに品質を上げるループ。合格するか、上限回数に達したら止める(=有界)。

構成:
  worker  … 答えを作る/直すエージェント
  critic  … 答えを採点し、ダメなら改善点を返すエージェント(第8章 ノック76 の応用)
  ループ  … critic が合格を出す or max_rounds に達するまで worker を回す

このノックは AWS 不要(MockModel で worker/critic の応答を台本化する)。
実運用では make_model() に差し替えれば本物の自己修正になる。
実行: uv run knocks/k104_reflexion_loop.py
"""

from dataclasses import dataclass

from mock_model import MockModel

from strands import Agent


@dataclass
class Critique:
    passed: bool
    feedback: str


def reflexion(
    task: str,
    worker: Agent,
    critique_fn,
    max_rounds: int = 3,
) -> tuple[str, int]:
    """合格するか max_rounds に達するまで、生成→批評→改稿を回す。

    戻り値: (最終成果物, 実行ラウンド数)
    """
    draft = str(worker(task))
    for round_no in range(1, max_rounds + 1):
        critique = critique_fn(task, draft)
        if critique.passed:
            print(f"  [round {round_no}] 合格 ✅")
            return draft, round_no
        print(f"  [round {round_no}] 不合格 → 改稿: {critique.feedback}")
        # 批評を次の入力に含めて改稿させる(ここが「前進」の仕掛け)
        draft = str(worker(f"以下の指摘を直して再提出して:\n{critique.feedback}\n\n現状:\n{draft}"))
    print(f"  上限 {max_rounds} ラウンドに到達(打ち切り)")
    return draft, max_rounds


if __name__ == "__main__":
    # worker: 1回目は雑、2回目でちゃんとする(台本)
    worker = Agent(
        model=MockModel(["カレーの作り方: 適当に煮る", "カレーの作り方: 1.野菜を切る 2.炒める 3.水とルーで煮込む"]),
        callback_handler=None,
    )

    # critic: 1回目は不合格、2回目は合格(台本)。実運用は LLM-as-a-Judge。
    verdicts = iter([Critique(False, "手順が具体的でない。番号付きにして"), Critique(True, "OK")])

    def critique_fn(task: str, draft: str) -> Critique:
        return next(verdicts)

    print("===== Reflexion ループ =====")
    final, rounds = reflexion("カレーのレシピを書いて", worker, critique_fn, max_rounds=3)
    print(f"\n最終成果物({rounds}ラウンドで到達):\n{final}")

    print(
        "\nポイント: 『再試行』と『自己修正』は違う。批評を次の入力に戻すから前進する。"
        "そして必ず max_rounds で有界化する — 批評が延々と不合格を出す事故を防ぐ。"
    )
