"""ノック96: Browser ツール — Web を操作するエージェント

AgentCore Browser は、マネージドなヘッドレスブラウザをエージェントに与える。
ログインが必要なサイトの操作、スクリーンショット取得、フォーム入力など、
API のない Web サービスを「人間のように」操作できる。

このノックは Browser クライアントの使い方の形を示す。
実行には AWS の AgentCore 権限が必要。Playwright 等と組み合わせて使う。

前提: uv add bedrock-agentcore[browser] playwright
実行: (AgentCore 環境で) uv run knocks/k096_browser_tool.py
"""


def show_usage_pattern() -> None:
    code = '''
import os
from bedrock_agentcore.tools.browser_client import BrowserClient
from playwright.sync_api import sync_playwright

region = os.environ.get("AWS_REGION", "us-west-2")

client = BrowserClient(region=region)
client.start()                       # マネージドブラウザを起動
ws_url, headers = client.generate_ws_headers()  # 接続情報を得る

# Playwright (CDP) でそのブラウザに接続して操作する
with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp(ws_url, headers=headers)
    page = browser.contexts[0].pages[0]
    page.goto("https://example.com")
    title = page.title()
    print("ページタイトル:", title)
    browser.close()

client.stop()
'''
    print(code)


if __name__ == "__main__":
    print("===== AgentCore Browser の使い方 =====")
    show_usage_pattern()
    print(
        "ポイント:\n"
        "- API のない Web サービスでも「ブラウザ操作」でエージェントが扱える\n"
        "- 実行環境はマネージド(ローカルにブラウザを立てなくてよい)\n"
        "- @tool でラップすれば、他のツールと同じようにエージェントに持たせられる\n"
        "- 強力なぶん危険も大きい。第5章の承認フロー・第7章の権限最小化と併用する"
    )
