"""第7章のテスト: モデルプロバイダと安全性。全テスト AWS 不要。"""

from k065_custom_provider import RuleBasedModel
from k067_pii_masking import PiiMasker
from k068_prompt_injection import InjectionDefense, fetch_page
from k069_least_privilege import make_agent
from k070_constrained_output import SupportTicket
from mock_model import MockModel, ToolCall
from pydantic import ValidationError

from strands import Agent


def _tool_results(agent):
    return [
        block["toolResult"]
        for m in agent.messages
        for block in m["content"]
        if "toolResult" in block
    ]


# ---- ノック65: カスタムプロバイダ ----


def test_custom_provider_works_with_agent():
    agent = Agent(model=RuleBasedModel(), callback_handler=None)
    assert "快晴" in str(agent("今日の天気は?"))
    assert "分かりません" in str(agent("好きな食べ物は?"))


def test_custom_provider_supports_tools_and_hooks():
    """自作モデルでもフックなどの機能が普通に動く(モデル非依存の証明)。"""
    from strands.hooks import BeforeInvocationEvent, HookProvider, HookRegistry

    fired = []

    class H(HookProvider):
        def register_hooks(self, registry: HookRegistry, **kwargs) -> None:
            registry.add_callback(BeforeInvocationEvent, lambda e: fired.append(1))

    agent = Agent(model=RuleBasedModel(), hooks=[H()], callback_handler=None)
    agent("天気は?")
    assert fired == [1]


# ---- ノック67: PII マスキング ----


def test_pii_masked_before_reaching_model():
    model = MockModel(["受け付けました"])
    agent = Agent(model=model, hooks=[PiiMasker()], callback_handler=None)
    agent("連絡先は tamiko@example.com、電話は 090-1234-5678 です。")

    # 履歴にもモデルへの入力にも生の PII が残らない
    history_text = agent.messages[0]["content"][0]["text"]
    model_input = model.calls[0]["messages"][0]["content"][0]["text"]
    for leaked in ("tamiko@example.com", "090-1234-5678"):
        assert leaked not in history_text
        assert leaked not in model_input
    assert "<メールアドレス>" in history_text
    assert "<電話番号>" in history_text


# ---- ノック68: プロンプトインジェクション防御 ----


def test_injection_defense_neutralizes_tool_output():
    agent = Agent(
        model=MockModel([ToolCall("fetch_page", {"url": "http://x"}), "特売情報です"]),
        tools=[fetch_page],
        hooks=[InjectionDefense()],
        callback_handler=None,
    )
    agent("ページを見て")

    result_text = str(_tool_results(agent)[0]["content"])
    assert "SYSTEM:" not in result_text  # 命令注入パターンが除去された
    assert "<external_data>" in result_text  # 外部データの枠で囲まれた


def test_without_defense_injection_reaches_model():
    """防御フックなしだと、注入された指示がそのままモデルに渡る(危険side)。"""
    agent = Agent(
        model=MockModel([ToolCall("fetch_page", {"url": "http://x"}), "応答"]),
        tools=[fetch_page],
        callback_handler=None,
    )
    agent("ページを見て")
    assert "SYSTEM:" in str(_tool_results(agent)[0]["content"])


# ---- ノック69: 権限の最小化 ----


def test_allowlist_blocks_unpermitted_tool():
    viewer = make_agent(
        MockModel([ToolCall("delete_file", {"path": "x"}), "できません"]),
        allowed={"list_files"},
    )
    viewer("消して")
    result = _tool_results(viewer)[0]
    assert result["status"] == "error"
    assert "許可されていません" in str(result["content"])


def test_allowlist_permits_listed_tool():
    admin = make_agent(
        MockModel([ToolCall("delete_file", {"path": "x"}), "削除しました"]),
        allowed={"list_files", "delete_file"},
    )
    admin("消して")
    assert _tool_results(admin)[0]["status"] == "success"


# ---- ノック70: 出力の制約 ----


def test_constrained_output_accepts_valid():
    ticket = SupportTicket(category="技術", priority=3, summary="ログイン不可", needs_human=False)
    assert ticket.category == "技術"
    assert ticket.priority == 3


def test_constrained_output_rejects_invalid():
    # 未定義カテゴリ
    try:
        SupportTicket(category="宇宙", priority=3, summary="x", needs_human=False)
        assert False, "却下されるべき"
    except ValidationError:
        pass

    # 範囲外の優先度
    try:
        SupportTicket(category="技術", priority=99, summary="x", needs_human=False)
        assert False, "却下されるべき"
    except ValidationError:
        pass
