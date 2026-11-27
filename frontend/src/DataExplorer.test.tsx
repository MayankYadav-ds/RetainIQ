import { render, screen, fireEvent } from "@testing-library/react";
import { vi, it, expect, afterEach } from "vitest";
import DataExplorer from "./DataExplorer";
afterEach(() => vi.unstubAllGlobals());
it("displays loading, handles failure and retries into an empty registry", async () => {
  const fetch = vi
    .fn()
    .mockRejectedValueOnce(Error())
    .mockResolvedValue({ ok: true, json: async () => [] });
  vi.stubGlobal("fetch", fetch);
  render(<DataExplorer />);
  expect(screen.getByRole("status")).toHaveTextContent("Loading");
  fireEvent.click(
    await screen.findByRole("button", { name: "Retry registry" }),
  );
  await screen.findByText("No approved datasets registered.");
});
it("renders provenance, capability limits and counts returned by the server", async () => {
  vi.stubGlobal(
    "fetch",
    vi
      .fn()
      .mockResolvedValue({
        ok: true,
        json: async () => [
          {
            dataset: "benchmark",
            provenance: "UCI benchmark",
            source: "UCI",
            license: "CC BY 4.0",
            attribution: "Archive citation",
            version: "example",
            rows: 73,
            features: 2,
            churn: 3,
            retained: 70,
            missing: 0,
            warnings: {},
            eligibility: { status: "excluded" },
            capabilities: { survival_analysis: false },
          },
        ],
      }),
  );
  render(<DataExplorer />);
  await screen.findByText("Archive citation");
  expect(screen.getByText("73")).toBeVisible();
  expect(screen.getByText("survival analysis · Unsupported")).toBeVisible();
});
