"""ノック53: S3 セッション — クラウドにセッションを永続化する

FileSessionManager を S3SessionManager に替えるだけ。
複数サーバー・コンテナから同じセッションを共有できるようになる
(AgentCore Runtime のようなステートレス環境で会話を継続する基本形)。

前提: S3 バケットと書き込み権限
実行: KNOCK_S3_BUCKET=my-bucket uv run knocks/k053_s3_session.py
"""

import os

from common import make_model

from strands import Agent
from strands.session.s3_session_manager import S3SessionManager

if __name__ == "__main__":
    bucket = os.environ.get("KNOCK_S3_BUCKET")
    if not bucket:
        raise SystemExit("環境変数 KNOCK_S3_BUCKET にバケット名を設定してください")

    agent = Agent(
        model=make_model(),
        session_manager=S3SessionManager(
            session_id="knock53",
            bucket=bucket,
            prefix="strands-knocks/",  # バケット内の置き場所
        ),
        callback_handler=None,
    )

    if not agent.messages:
        print(agent("私の名前はタミコです。覚えておいて。"))
        print("\n→ もう一度実行すると、S3 から会話が復元されます。")
        print(f"   確認: aws s3 ls s3://{bucket}/strands-knocks/ --recursive")
    else:
        print(f"S3 から履歴 {len(agent.messages)}件を復元しました\n")
        print(agent("私の名前を覚えていますか?"))
