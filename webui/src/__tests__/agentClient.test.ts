// ノック97・99のテスト: AgentClient
// fetch をモックして、ネットワークなしで「リクエストの組み立て」と
// 「ストリームの読み取り」を検証する。

import { describe, it, expect, vi, afterEach } from "vitest";
import { AgentClient, newSessionId } from "../agentClient";

/** 文字列の配列を ReadableStream(fetch のボディ相当)に変換する。 */
function streamFrom(chunks: string[]): ReadableStream<Uint8Array> {
  const encoder = new TextEncoder();
  let i = 0;
  return new ReadableStream({
    pull(controller) {
      if (i < chunks.length) {
        controller.enqueue(encoder.encode(chunks[i++]));
      } else {
        controller.close();
      }
    },
  });
}

afterEach(() => {
  vi.restoreAllMocks();
});

describe("AgentClient", () => {
  it("ストリームのテキストイベントを順に yield する", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        body: streamFrom([
          'data: {"type":"text","content":"こん"}\n\n',
          'data: {"type":"text","content":"にちは"}\n\n',
          'data: {"type":"done"}\n\n',
        ]),
      }),
    );

    const client = new AgentClient({ endpoint: "http://localhost:8080" });
    const collected: string[] = [];
    for await (const event of client.invoke("やあ")) {
      if (event.type === "text") collected.push(event.content!);
    }
    expect(collected.join("")).toBe("こんにちは");
  });

  it("セッションIDをヘッダに乗せて送る(会話継続)", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      body: streamFrom(['data: {"type":"done"}\n\n']),
    });
    vi.stubGlobal("fetch", fetchMock);

    const client = new AgentClient({ endpoint: "http://x", sessionId: "sess-123" });
    // ジェネレータを最後まで回す
    for await (const _ of client.invoke("hi")) {
      void _;
    }

    const [, init] = fetchMock.mock.calls[0];
    expect(init.headers["X-Amzn-Bedrock-AgentCore-Runtime-Session-Id"]).toBe("sess-123");
    expect(JSON.parse(init.body)).toEqual({ prompt: "hi" });
  });

  it("HTTP エラー時は例外を投げる", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: false, status: 500 }));

    const client = new AgentClient({ endpoint: "http://x" });
    await expect(async () => {
      for await (const _ of client.invoke("hi")) {
        void _;
      }
    }).rejects.toThrow("500");
  });
});

describe("newSessionId", () => {
  it("毎回ユニークな ID を生成する", () => {
    const ids = new Set([newSessionId(), newSessionId(), newSessionId()]);
    expect(ids.size).toBe(3);
    expect([...ids].every((id) => id.startsWith("sess-"))).toBe(true);
  });
});
