"""ノック105: 検証ループ(loop-until-verified)— 通るまで有界に再試行

Reflexion(104)の批評は LLM だった。検証ループは、批評役を
「機械的なチェッカ」にする形。テストの実行、スキーマ検証、正規表現、
コンパイル — 客観的に合否が出るものが相手なら、こちらが確実。

これは「エージェンティックなコーディング」の心臓部そのもの:
  コード生成 → テスト実行 → 落ちたらエラーを見せて修正 → 通るまで(有界に)

構成:
  generator … 成果物を作る/直すエージェント
  verifier  … 成果物を検証して (ok, エラー詳細) を返す純粋関数
  ループ    … verifier が ok を返す or max_attempts に達するまで

このノックは AWS 不要(MockModel + Python 関数の検証)。
実行: uv run knocks/k105_verify_loop.py
"""

import json

from mock_model import MockModel

from strands import Agent


def verify_json(text: str, required_keys: set[str]) -> tuple[bool, str]:
    """出力が「必須キーを持つ有効な JSON か」を機械的に検証する。"""
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        return False, f"JSON として不正: {e}"
    missing = required_keys - data.keys()
    if missing:
        return False, f"必須キーが不足: {missing}"
    return True, "OK"


def loop_until_verified(task: str, generator: Agent, verify_fn, max_attempts: int = 4):
    """verify_fn が通るまで generator を回す(有界)。戻り値: (成果物, 試行回数, 成功したか)。"""
    output = str(generator(task))
    for attempt in range(1, max_attempts + 1):
        ok, detail = verify_fn(output)
        if ok:
            print(f"  [試行 {attempt}] 検証通過 ✅")
            return output, attempt, True
        print(f"  [試行 {attempt}] 検証失敗: {detail}")
        # エラー詳細を戻して直させる(機械のフィードバック)
        output = str(generator(f"検証エラーを直して:\n{detail}\n\n現状:\n{output}"))
    print(f"  上限 {max_attempts} 回に到達(未達で打ち切り)")
    return output, max_attempts, False


if __name__ == "__main__":
    # 1回目: 壊れたJSON、2回目: キー不足、3回目: 正しい(台本)
    generator = Agent(
        model=MockModel(
            [
                '{"name": "太郎", ',                        # 壊れている
                '{"name": "太郎"}',                          # age がない
                '{"name": "太郎", "age": 30}',               # OK
            ]
        ),
        callback_handler=None,
    )

    print("===== 検証ループ(loop-until-verified)=====")
    result, attempts, ok = loop_until_verified(
        "name と age を持つ JSON を作って",
        generator,
        lambda text: verify_json(text, {"name", "age"}),
        max_attempts=4,
    )
    print(f"\n結果({attempts}回で {'成功' if ok else '失敗'}):\n{result}")

    print(
        "\nポイント: 検証が『客観的な機械』なら、自己採点(104)より信頼できる。"
        "テストを verifier にすれば、これがそのままコード生成エージェントになる。"
        "成功でも失敗でも必ず有界に止まる — 通らないタスクで無限に回らない。"
    )
