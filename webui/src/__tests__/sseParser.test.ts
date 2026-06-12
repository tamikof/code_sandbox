// ノック98のテスト: SSE パーサの境界条件
// TS 初学者向けに「テストとは何を確かめるものか」が分かる粒度で書く。

import { describe, it, expect } from "vitest";
import { SseParser } from "../sseParser";

describe("SseParser", () => {
  it("1チャンクに収まった単一イベントを解釈する", () => {
    const parser = new SseParser();
    const events = parser.push('data: {"type":"text","content":"こんにちは"}\n\n');
    expect(events).toEqual([{ type: "text", content: "こんにちは" }]);
  });

  it("1チャンクの複数イベントを分割する", () => {
    const parser = new SseParser();
    const events = parser.push(
      'data: {"type":"text","content":"あ"}\n\n' + 'data: {"type":"text","content":"い"}\n\n',
    );
    expect(events).toHaveLength(2);
    expect(events[1].content).toBe("い");
  });

  it("チャンク境界で途切れたイベントを次のチャンクと結合する(最重要)", () => {
    const parser = new SseParser();
    // イベントが途中で切れて届く
    const first = parser.push('data: {"type":"text","con');
    expect(first).toEqual([]); // まだ完成していないので何も返さない

    const second = parser.push('tent":"統合"}\n\n');
    expect(second).toEqual([{ type: "text", content: "統合" }]);
  });

  it("done イベントを解釈する", () => {
    const parser = new SseParser();
    expect(parser.push('data: {"type":"done"}\n\n')).toEqual([{ type: "done" }]);
  });

  it("[DONE] センチネルを done として扱う", () => {
    const parser = new SseParser();
    expect(parser.push("data: [DONE]\n\n")).toEqual([{ type: "done" }]);
  });

  it("完成イベントを返しつつ未完成分はバッファに残す", () => {
    const parser = new SseParser();
    // 1件は完成、2件目は途中までしか来ていない
    const events = parser.push(
      'data: {"type":"text","content":"完成"}\n\n' + 'data: {"type":"text","content":"未完',
    );
    expect(events).toEqual([{ type: "text", content: "完成" }]); // 完成分だけ返る

    // 残りが届いたら2件目が取れる
    const rest = parser.push('成"}\n\n');
    expect(rest).toEqual([{ type: "text", content: "未完成" }]);
  });
});
