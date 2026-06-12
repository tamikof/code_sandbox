import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// 超シンプル構成: React プラグインだけ。テストは vitest(node 環境)。
export default defineConfig({
  plugins: [react()],
  test: {
    environment: "node",
  },
});
