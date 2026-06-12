"""ノック70: 出力の制約 — structured output + バリデーションで安全な出力を保証

自由文の出力は、表記ゆれ・想定外の値・インジェクションの温床になる。
出力先が決まっている(DB・API・UI)なら、Pydantic で型と値域を縛り、
モデルに「許された形でしか答えられない」ようにする。

このノックは AWS 不要(モデル呼び出しをモックではなく構造を学ぶ用途で書く)。
※ structured_output は実モデルが必要なので、ここでは検証ロジックを単体で学ぶ。
実行: uv run knocks/k070_constrained_output.py
"""

from typing import Literal

from pydantic import BaseModel, Field, ValidationError


class SupportTicket(BaseModel):
    """サポート問い合わせの分類結果。出力の「形」を厳密に定義する。"""

    category: Literal["請求", "技術", "返品", "その他"] = Field(description="問い合わせの種別")
    priority: int = Field(ge=1, le=5, description="緊急度(1=低 〜 5=高)")
    summary: str = Field(max_length=100, description="100文字以内の要約")
    needs_human: bool = Field(description="人間のオペレータ対応が必要か")


if __name__ == "__main__":
    # 本番では: agent.structured_output(SupportTicket, 問い合わせ文)
    # ここではモデルが返したと仮定した値を検証して、制約の効き方を見る。

    print("===== 正常な出力 =====")
    ok = SupportTicket(category="請求", priority=4, summary="二重請求の問い合わせ", needs_human=True)
    print(ok)

    print("\n===== 制約違反は弾かれる =====")
    bad_cases = [
        {"category": "宇宙", "priority": 3, "summary": "x", "needs_human": False},  # 未定義カテゴリ
        {"category": "技術", "priority": 9, "summary": "x", "needs_human": False},  # 範囲外の優先度
    ]
    for case in bad_cases:
        try:
            SupportTicket(**case)
        except ValidationError as e:
            print(f"却下: {case} → {e.errors()[0]['msg']}")

    # structured_output を使うと、モデルの出力もこの検証を通る。
    # category は4種以外を返せず、priority は1〜5に必ず収まる =
    # 後続の処理(DBのenumカラム等)が壊れない。これが「出力の安全性」。
