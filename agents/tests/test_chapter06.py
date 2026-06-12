"""第6章のテスト: セッションとメモリ。全テスト AWS 不要。"""

import json

from k054_sqlite_repository import SqliteSessionRepository
from k055_memory_tool import recall, remember
from k059_multi_user import agent_for
from k060_memory_strategies import EXTRACT_PROMPT, FACTS, save_fact
from mock_model import MockModel, ToolCall

from strands import Agent
from strands.session.file_session_manager import FileSessionManager
from strands.session.repository_session_manager import RepositorySessionManager


# ---- ノック51・52: ファイルセッション ----


def test_file_session_persists_messages_and_state(tmp_path):
    agent = Agent(
        model=MockModel(["覚えました"]),
        session_manager=FileSessionManager(session_id="t1", storage_dir=str(tmp_path)),
        callback_handler=None,
    )
    agent.state.set("name", "タミコ")
    agent("私はタミコです")

    # プロセス再起動の想定: 同じ session_id で新しいエージェントを作る
    restored = Agent(
        model=MockModel(["タミコさん"]),
        session_manager=FileSessionManager(session_id="t1", storage_dir=str(tmp_path)),
        callback_handler=None,
    )
    assert len(restored.messages) == 2
    assert restored.state.get("name") == "タミコ"


def test_different_session_ids_are_isolated(tmp_path):
    for sid, text in (("a", "Aの話"), ("b", "Bの話")):
        agent = Agent(
            model=MockModel(["はい"]),
            session_manager=FileSessionManager(session_id=sid, storage_dir=str(tmp_path)),
            callback_handler=None,
        )
        agent(text)

    restored_a = Agent(
        model=MockModel(["はい"]),
        session_manager=FileSessionManager(session_id="a", storage_dir=str(tmp_path)),
        callback_handler=None,
    )
    assert "Aの話" in json.dumps(restored_a.messages, ensure_ascii=False)
    assert "Bの話" not in json.dumps(restored_a.messages, ensure_ascii=False)


# ---- ノック54: SQLite リポジトリ ----


def test_sqlite_repository_roundtrip(tmp_path):
    db = str(tmp_path / "sessions.db")

    agent = Agent(
        model=MockModel(["覚えました"]),
        session_manager=RepositorySessionManager(
            session_id="s1", session_repository=SqliteSessionRepository(db)
        ),
        callback_handler=None,
    )
    agent("私はタミコです")

    restored = Agent(
        model=MockModel(["はい"]),
        session_manager=RepositorySessionManager(
            session_id="s1", session_repository=SqliteSessionRepository(db)
        ),
        callback_handler=None,
    )
    assert len(restored.messages) == 2
    assert "タミコ" in json.dumps(restored.messages, ensure_ascii=False)


# ---- ノック55: メモリツール ----


def test_memory_tool_remember_and_recall(tmp_path, monkeypatch):
    import k055_memory_tool

    monkeypatch.setattr(k055_memory_tool, "NOTES_FILE", tmp_path / "notes.json")

    assert "保存しました" in remember("エビアレルギーがある")
    assert "保存しました" in remember("名前はタミコ")
    assert remember("名前はタミコ") == "保存しました(現在 2 件)"  # 重複は増えない

    recalled = recall()
    assert "エビアレルギー" in recalled
    assert "タミコ" in recalled


# ---- ノック59: マルチユーザー分離 ----


def test_multi_user_sessions_do_not_leak(tmp_path, monkeypatch):
    import k059_multi_user

    monkeypatch.setattr(k059_multi_user, "STORAGE", str(tmp_path))

    agent_for("alice", "c1", MockModel(["はい"]))("私はアリス。趣味は登山。")
    agent_for("bob", "c1", MockModel(["はい"]))("私はボブ。趣味は釣り。")

    alice = agent_for("alice", "c1", MockModel(["はい"]))
    dump = json.dumps(alice.messages, ensure_ascii=False)
    assert "登山" in dump
    assert "釣り" not in dump  # ボブの会話は混入しない


# ---- ノック60: 抽出戦略 ----


def test_fact_extraction_strategy():
    FACTS.clear()
    agent = Agent(
        model=MockModel(
            [
                "覚えました",
                [
                    ToolCall("save_fact", {"category": "profile", "fact": "名前はタミコ"}),
                    ToolCall("save_fact", {"category": "constraint", "fact": "エビアレルギー"}),
                ],
                "保存しました",
            ]
        ),
        tools=[save_fact],
        callback_handler=None,
    )
    agent("私はタミコ。エビアレルギーがあります。今日は暑いですね。")
    agent(EXTRACT_PROMPT)

    assert {f["category"] for f in FACTS} == {"profile", "constraint"}
    assert len(FACTS) == 2  # 雑談(天気)は抽出されていない
