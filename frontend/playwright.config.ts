import { defineConfig } from "@playwright/test";
const python =
  process.env.RETAINIQ_PYTHON ??
  (process.platform === "win32"
    ? "../backend/.venv/Scripts/python.exe"
    : "../backend/.venv/bin/python");
export default defineConfig({
  testDir: "./e2e",
  workers: 1,
  retries: 0,
  reporter: "list",
  use: { baseURL: "http://127.0.0.1:4173", browserName: "chromium" },
  webServer: [
    {
      command: `"${python}" -m uvicorn retainiq.main:create_app --factory --no-access-log --host 127.0.0.1 --port 8000`,
      url: "http://127.0.0.1:8000/ready",
      reuseExistingServer: !process.env.CI,
      env: { RETAINIQ_CORS_ORIGINS: '["http://127.0.0.1:4173"]' },
    },
    {
      command: "npm run preview",
      url: "http://127.0.0.1:4173",
      reuseExistingServer: !process.env.CI,
    },
  ],
});
