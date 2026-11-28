import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import ModelLab, { Simulator } from "./ModelLab";
afterEach(() => vi.unstubAllGlobals());
it("uses the actual model response and distinguishes unavailable inference", async () => {
  const fetch = vi
    .fn()
    .mockResolvedValueOnce({ ok: false, status: 503 })
    .mockResolvedValue({
      ok: true,
      json: async () => ({
        model: "test-model",
        probability: 0.627,
        raw_probability: 0.51,
        threshold: 0.3,
        predicted_class: 1,
        risk_tier: "critical",
        warnings: [],
        target: "Month-twelve state",
        limitations: "Snapshot",
      }),
    });
  vi.stubGlobal("fetch", fetch);
  render(<Simulator />);
  fireEvent.click(screen.getByRole("button", { name: "Predict churn" }));
  expect(await screen.findByRole("alert")).toHaveTextContent(
    "No approved model",
  );
  fireEvent.click(screen.getByRole("button", { name: "Predict churn" }));
  expect(
    await screen.findByRole("heading", { name: "Churn probability 62.7%" }),
  ).toBeVisible();
  expect(JSON.parse(fetch.mock.calls[1][1].body).tariff_plan).toBe(1);
});
it("recovers from evidence failure without fabricating model metrics", async () => {
  const fetch = vi
    .fn()
    .mockRejectedValueOnce(Error())
    .mockResolvedValue({ ok: true, json: async () => null });
  vi.stubGlobal("fetch", fetch);
  render(<ModelLab />);
  fireEvent.click(await screen.findByRole("button", { name: "Retry models" }));
  expect(await screen.findByRole("status")).toHaveTextContent(
    "No approved model",
  );
});
