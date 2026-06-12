"""ノック54: 自作リポジトリ — SessionRepository を SQLite で実装する

File / S3 以外の保存先(RDB、DynamoDB、Redis...)が欲しければ
SessionRepository を実装して RepositorySessionManager に渡す。
ここでは SQLite で実装する。実装するのは9メソッド(session / agent /
message それぞれの create / read 系)。

このノックは AWS 不要(モックモデルで動く)。
実行: uv run knocks/k054_sqlite_repository.py
"""

import json
import sqlite3
from typing import Any

from strands import Agent
from strands.session.repository_session_manager import RepositorySessionManager
from strands.session.session_repository import SessionRepository
from strands.types.session import Session, SessionAgent, SessionMessage


class SqliteSessionRepository(SessionRepository):
    """セッション3点セット (session / agent / message) を SQLite に保存する。"""

    def __init__(self, db_path: str):
        # Strands は同期呼び出しでも内部でワーカースレッドのイベントループを使うため、
        # スレッドチェックを緩める(本番は接続プールやスレッドローカルにすること)
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY, data TEXT);
            CREATE TABLE IF NOT EXISTS agents (
                session_id TEXT, agent_id TEXT, data TEXT,
                PRIMARY KEY (session_id, agent_id));
            CREATE TABLE IF NOT EXISTS messages (
                session_id TEXT, agent_id TEXT, message_id INTEGER, data TEXT,
                PRIMARY KEY (session_id, agent_id, message_id));
            """
        )

    # --- session ---
    def create_session(self, session: Session, **kwargs: Any) -> Session:
        self.conn.execute(
            "INSERT OR REPLACE INTO sessions VALUES (?, ?)",
            (session.session_id, json.dumps(session.to_dict())),
        )
        self.conn.commit()
        return session

    def read_session(self, session_id: str, **kwargs: Any) -> Session | None:
        row = self.conn.execute(
            "SELECT data FROM sessions WHERE session_id = ?", (session_id,)
        ).fetchone()
        return Session.from_dict(json.loads(row[0])) if row else None

    # --- agent ---
    def create_agent(self, session_id: str, session_agent: SessionAgent, **kwargs: Any) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO agents VALUES (?, ?, ?)",
            (session_id, session_agent.agent_id, json.dumps(session_agent.to_dict())),
        )
        self.conn.commit()

    def read_agent(self, session_id: str, agent_id: str, **kwargs: Any) -> SessionAgent | None:
        row = self.conn.execute(
            "SELECT data FROM agents WHERE session_id = ? AND agent_id = ?",
            (session_id, agent_id),
        ).fetchone()
        return SessionAgent.from_dict(json.loads(row[0])) if row else None

    def update_agent(self, session_id: str, session_agent: SessionAgent, **kwargs: Any) -> None:
        self.create_agent(session_id, session_agent)

    # --- message ---
    def create_message(
        self, session_id: str, agent_id: str, session_message: SessionMessage, **kwargs: Any
    ) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO messages VALUES (?, ?, ?, ?)",
            (
                session_id,
                agent_id,
                session_message.message_id,
                json.dumps(session_message.to_dict()),
            ),
        )
        self.conn.commit()

    def read_message(
        self, session_id: str, agent_id: str, message_id: int, **kwargs: Any
    ) -> SessionMessage | None:
        row = self.conn.execute(
            "SELECT data FROM messages WHERE session_id=? AND agent_id=? AND message_id=?",
            (session_id, agent_id, message_id),
        ).fetchone()
        return SessionMessage.from_dict(json.loads(row[0])) if row else None

    def update_message(
        self, session_id: str, agent_id: str, session_message: SessionMessage, **kwargs: Any
    ) -> None:
        self.create_message(session_id, agent_id, session_message)

    def list_messages(
        self,
        session_id: str,
        agent_id: str,
        limit: int | None = None,
        offset: int = 0,
        **kwargs: Any,
    ) -> list[SessionMessage]:
        query = "SELECT data FROM messages WHERE session_id=? AND agent_id=? ORDER BY message_id"
        rows = self.conn.execute(query, (session_id, agent_id)).fetchall()
        messages = [SessionMessage.from_dict(json.loads(r[0])) for r in rows]
        return messages[offset : offset + limit] if limit else messages[offset:]


if __name__ == "__main__":
    from mock_model import MockModel

    DB = "/tmp/knock54_sessions.db"
    repo = SqliteSessionRepository(DB)

    agent = Agent(
        model=MockModel(["覚えました!"]),
        session_manager=RepositorySessionManager(session_id="knock54", session_repository=repo),
        callback_handler=None,
    )
    agent("私はタミコです")

    # 別の「プロセス」から同じ DB を開いて復元
    restored = Agent(
        model=MockModel(["タミコさんですね"]),
        session_manager=RepositorySessionManager(
            session_id="knock54", session_repository=SqliteSessionRepository(DB)
        ),
        callback_handler=None,
    )
    print(f"SQLite から復元した履歴: {len(restored.messages)}件")
    print(restored("私の名前は?"))
