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
      command: `"${python}" ../scripts/prepare_analysis_fixture.py --serve`,
      url: "http://127.0.0.1:8000/ready",
      reuseExistingServer: false,
      env: {
        RETAINIQ_DATA_ROOT: ".retainiq-data",
        RETAINIQ_ANALYTICS_DATASETS: '["synthetic_churn_fixture"]',
        RETAINIQ_PUBLIC_DATASETS: '["synthetic_churn_fixture"]',
        RETAINIQ_CORS_ORIGINS: '["http://127.0.0.1:4173"]',
      },
    },
    {
      command: "npm run preview",
      url: "http://127.0.0.1:4173",
      reuseExistingServer: false,
    },
  ],
});
