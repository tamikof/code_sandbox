"""ノック7: 構造化出力 — Pydantic モデルで型のついた応答を受け取る

自由文ではなく「検証済みの Python オブジェクト」として結果を得る。
アプリケーションにエージェントを組み込むときの基本形。

実行: uv run knocks/k007_structured_output.py
"""

from pydantic import BaseModel, Field

from strands import Agent


class Recipe(BaseModel):
    """料理レシピ"""

    name: str = Field(description="料理名")
    minutes: int = Field(description="調理時間(分)")
    ingredients: list[str] = Field(description="材料のリスト")
    steps: list[str] = Field(description="手順。各ステップ1文")


agent = Agent()

# 第1引数に Pydantic モデル、第2引数にプロンプト。
# 戻り値は文字列ではなく Recipe のインスタンスになる。
recipe = agent.structured_output(Recipe, "卵かけご飯のレシピを教えて。")

print(f"type        : {type(recipe)}")
print(f"name        : {recipe.name}")
print(f"minutes     : {recipe.minutes}(int として演算可能: 2倍={recipe.minutes * 2})")
print(f"ingredients : {recipe.ingredients}")
for i, step in enumerate(recipe.steps, 1):
    print(f"step {i}      : {step}")
