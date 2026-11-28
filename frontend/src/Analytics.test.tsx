import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import Analytics from "./Analytics";
afterEach(() => vi.unstubAllGlobals());
it("recovers from API failure into a meaningful empty state", async () => {
  const catalog = {
    schema_version: "features-v1",
    approved: [],
    excluded: {},
    derived: {},
    sets: {},
  };
  const fetch = vi
    .fn()
    .mockRejectedValueOnce(new Error("network"))
    .mockImplementation(async (url: string) => ({
      ok: true,
      json: async () => (url.endsWith("/features") ? catalog : null),
    }));
  vi.stubGlobal("fetch", fetch);
  render(<Analytics mode="analytics" />);
  expect(screen.getByRole("status")).toHaveTextContent("Loading analysis");
  fireEvent.click(
    await screen.findByRole("button", { name: "Retry analysis" }),
  );
  expect(await screen.findByRole("status")).toHaveTextContent(
    "No approved analysis",
  );
});
