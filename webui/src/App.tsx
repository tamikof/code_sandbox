// ノック97〜99の UI: 最小チャット画面
//
// 状態管理ライブラリは使わず useState だけ。ロジック(fetch/SSE)は
// agentClient.ts / sseParser.ts に逃がしてあるので、ここは「表示」に集中する。

import { useRef, useState } from "react";
import { AgentClient, newSessionId, type AgentClientOptions } from "./agentClient";

interface Message {
  role: "user" | "assistant";
  text: string;
}

const ENDPOINT = "http://localhost:8080"; // ローカルの app.run()(ノック91/92)

export default function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);

  // ノック99: セッションIDをブラウザ滞在中ずっと保持して会話を継続する
  const sessionId = useRef(newSessionId());

  async function send() {
    const prompt = input.trim();
    if (!prompt || busy) return;

    setInput("");
    setBusy(true);
    setMessages((prev) => [...prev, { role: "user", text: prompt }, { role: "assistant", text: "" }]);

    const options: AgentClientOptions = { endpoint: ENDPOINT, sessionId: sessionId.current };
    const client = new AgentClient(options);

    try {
      // ノック98: ストリームのテキストイベントを最後の assistant メッセージに追記
      for await (const event of client.invoke(prompt)) {
        if (event.type === "text" && event.content) {
          setMessages((prev) => appendToLast(prev, event.content!));
        }
      }
    } catch (err) {
      setMessages((prev) => appendToLast(prev, `\n[エラー] ${String(err)}`));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div style={{ maxWidth: 600, margin: "2rem auto", fontFamily: "sans-serif" }}>
      <h1>Strands Knocks Chat</h1>
      <div style={{ minHeight: 300, border: "1px solid #ccc", padding: 12, borderRadius: 8 }}>
        {messages.map((m, i) => (
          <p key={i}>
            <strong>{m.role === "user" ? "あなた" : "AI"}:</strong> {m.text}
          </p>
        ))}
      </div>
      <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
        <input
          style={{ flex: 1, padding: 8 }}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && send()}
          placeholder="メッセージを入力..."
          disabled={busy}
        />
        <button onClick={send} disabled={busy}>
          {busy ? "..." : "送信"}
        </button>
      </div>
    </div>
  );
}

/** 最後の assistant メッセージにテキストを追記した新しい配列を返す。 */
function appendToLast(messages: Message[], text: string): Message[] {
  const copy = [...messages];
  const last = copy[copy.length - 1];
  copy[copy.length - 1] = { ...last, text: last.text + text };
  return copy;
}
