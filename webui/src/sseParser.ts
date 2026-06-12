// ノック98の核: SSE (Server-Sent Events) パーサ
//
// AgentCore Runtime のストリーミング応答は SSE 形式で届く:
//   data: {"type":"text","content":"こん"}\n\n
//   data: {"type":"text","content":"にちは"}\n\n
//   data: {"type":"done"}\n\n
//
// fetch のレスポンスボディはチャンク単位で届くため、イベントが途中で切れる。
// このパーサは「バッファに溜めて、完全なイベント(\n\n 区切り)だけ切り出す」。
// 純粋関数なので Vitest で簡単にテストできる(tests/sseParser.test.ts)。

export interface AgentEvent {
  type: string;
  content?: string;
}

export class SseParser {
  private buffer = "";

  /**
   * 届いたテキストチャンクを渡すと、完成した AgentEvent の配列を返す。
   * 不完全なイベントは内部バッファに残し、次のチャンクと結合する。
   */
  push(chunk: string): AgentEvent[] {
    this.buffer += chunk;
    const events: AgentEvent[] = [];

    // SSE はイベント同士を空行(\n\n)で区切る
    let separatorIndex: number;
    while ((separatorIndex = this.buffer.indexOf("\n\n")) !== -1) {
      const rawEvent = this.buffer.slice(0, separatorIndex);
      this.buffer = this.buffer.slice(separatorIndex + 2);

      const parsed = this.parseEvent(rawEvent);
      if (parsed) events.push(parsed);
    }
    return events;
  }

  private parseEvent(raw: string): AgentEvent | null {
    // "data: " で始まる行から JSON を取り出す(複数行 data: も結合)
    const dataLines = raw
      .split("\n")
      .filter((line) => line.startsWith("data:"))
      .map((line) => line.slice(5).trim());

    if (dataLines.length === 0) return null;

    const payload = dataLines.join("");
    if (payload === "[DONE]") return { type: "done" };

    try {
      return JSON.parse(payload) as AgentEvent;
    } catch {
      // JSON でない data はプレーンテキストとして扱う
      return { type: "text", content: payload };
    }
  }
}
