// ノック97・99の核: AgentCore Runtime を呼ぶクライアント
//
// 本番では AWS SigV4 署名が要るが、ローカル開発では
// ノック91/92 の app.run()(http://localhost:8080)をそのまま叩ける。
// この薄いラッパーが「リクエスト組み立て」と「ストリーム読み取り」を担う。

import { SseParser, type AgentEvent } from "./sseParser";

export interface AgentClientOptions {
  // ローカル開発: http://localhost:8080 / 本番: Runtime の InvokeAgentRuntime URL
  endpoint: string;
  // ノック99: 会話を継続するためのセッションID
  sessionId?: string;
}

export class AgentClient {
  constructor(private options: AgentClientOptions) {}

  /**
   * プロンプトを送り、ストリームのイベントを1つずつ yield する。
   * UI 側は for await でこれを回してトークンを表示する。
   */
  async *invoke(prompt: string): AsyncGenerator<AgentEvent> {
    const response = await fetch(`${this.options.endpoint}/invocations`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        // ノック99: セッションIDを渡すと Runtime 側で会話が継続する
        ...(this.options.sessionId
          ? { "X-Amzn-Bedrock-AgentCore-Runtime-Session-Id": this.options.sessionId }
          : {}),
      },
      body: JSON.stringify({ prompt }),
    });

    if (!response.ok) {
      throw new Error(`Runtime returned ${response.status}`);
    }
    if (!response.body) {
      throw new Error("レスポンスボディがありません");
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    const parser = new SseParser();

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      const chunk = decoder.decode(value, { stream: true });
      for (const event of parser.push(chunk)) {
        yield event;
      }
    }
  }
}

/** ノック99: ブラウザのセッションごとに一意なIDを作る(会話の単位)。 */
export function newSessionId(): string {
  return `sess-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
}
