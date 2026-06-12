"""ノック30: 大量ツールの絞り込み — 必要なツールだけ持たせる

ツールが何十個もあると、(1) スキーマだけでトークンを浪費し、(2) モデルの
ツール選択精度も落ちる。対策は「質問に関係するツールだけ持たせる」こと。

ここでは2段構えで実装する:
  1段目: 軽いモデルにツールカタログを見せて、必要なツール名を選ばせる
  2段目: 選ばれたツールだけ持つエージェントが実際のタスクを解く

公式の `retrieve` ツール(Bedrock Knowledge Base のセマンティック検索)は
この選択を埋め込みベースでやる本格版。考え方は同じ。

実行: uv run knocks/k030_tool_selection.py
"""

from common import make_model
from pydantic import BaseModel, Field

from strands import Agent, tool

# --- ツールが大量にある想定(ここでは8個で雰囲気を出す) ---


@tool
def search_flights(destination: str) -> str:
    """航空券を検索する。"""
    return f"{destination} 行き: 32,000円〜"


@tool
def search_hotels(city: str) -> str:
    """ホテルを検索する。"""
    return f"{city} のホテル: 8,000円/泊〜"


@tool
def get_exchange_rate(currency: str) -> str:
    """為替レートを取得する。"""
    return f"1 {currency} = 150円"


@tool
def translate_text(text: str, target_lang: str) -> str:
    """テキストを翻訳する。"""
    return f"({target_lang}訳) {text}"


@tool
def get_stock_price(ticker: str) -> str:
    """株価を取得する。"""
    return f"{ticker}: 1,234円"


@tool
def send_email(to: str, body: str) -> str:
    """メールを送信する。"""
    return f"{to} に送信しました"


@tool
def create_calendar_event(title: str, date: str) -> str:
    """カレンダーに予定を登録する。"""
    return f"{date} に「{title}」を登録しました"


@tool
def summarize_news(topic: str) -> str:
    """ニュースを要約する。"""
    return f"{topic} の最新ニュース: ...(ダミー)"


ALL_TOOLS = [
    search_flights,
    search_hotels,
    get_exchange_rate,
    translate_text,
    get_stock_price,
    send_email,
    create_calendar_event,
    summarize_news,
]


class ToolSelection(BaseModel):
    """タスクに必要なツールの選択結果"""

    tool_names: list[str] = Field(description="タスクの遂行に必要なツール名のリスト")


def tool_catalog(tools: list) -> str:
    """ツール名と説明の一覧(カタログ)を作る。スキーマ全体より遥かに軽い。"""
    return "\n".join(f"- {t.tool_name}: {t.tool_spec['description']}" for t in tools)


def filter_tools(tools: list, names: list[str]) -> list:
    """選択されたツール名だけを残す。"""
    return [t for t in tools if t.tool_name in names]


if __name__ == "__main__":
    task = "来月ハワイ旅行に行きたい。航空券とホテルを調べて、ドルのレートも教えて。"

    # 1段目: ツールを持たない軽いエージェントが、カタログから必要なツールを選ぶ
    selector = Agent(model=make_model())
    selection = selector.structured_output(
        ToolSelection,
        f"次のタスクに必要なツールを選んで。\n\nタスク: {task}\n\nツール一覧:\n{tool_catalog(ALL_TOOLS)}",
    )
    print("選ばれたツール:", selection.tool_names, "\n")

    # 2段目: 選ばれたツールだけを持つエージェントがタスクを解く
    worker = Agent(model=make_model(), tools=filter_tools(ALL_TOOLS, selection.tool_names))
    worker(task)
