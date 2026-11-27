import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { afterEach, beforeEach, describe, it, expect, vi } from "vitest";
import App from "./App";
import { verifyConnection } from "./api";
const version = { name: "RetainIQ", version: "0.2.0", phase: 1 };
const ready = { status: "ready", database: "reachable" };
const fetchMock = vi.fn();
beforeEach(() => {
  vi.stubGlobal("fetch", fetchMock);
  fetchMock.mockReset();
  localStorage.clear();
});
afterEach(() => vi.unstubAllGlobals());
function success() {
  fetchMock.mockImplementation((url: string) =>
    Promise.resolve({
      ok: true,
      json: () => Promise.resolve(url.endsWith("/ready") ? ready : version),
    }),
  );
}
describe("application", () => {
  it("renders honest capabilities and empty state", async () => {
    success();
    render(<App />);
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent(
      "Understand risk.",
    );
    expect(screen.getAllByText("PLANNED")).toHaveLength(3);
    expect(screen.getByText("Dataset evidence")).toBeInTheDocument();
    await screen.findByText("Backend connected");
  });
  it("shows loading until both resource checks resolve", async () => {
    let resolveReady!: (v: unknown) => void;
    const pending = new Promise((resolve) => {
      resolveReady = resolve;
    });
    fetchMock.mockImplementation((url: string) =>
      url.endsWith("/ready")
        ? pending
        : Promise.resolve({ ok: true, json: () => Promise.resolve(version) }),
    );
    render(<App />);
    expect(screen.getByText("Checking backend…")).toBeInTheDocument();
    resolveReady({ ok: true, json: () => Promise.resolve(ready) });
    await screen.findByText("Backend connected");
  });
  it("connects and verifies readiness", async () => {
    success();
    render(<App />);
    await screen.findByText("Backend connected");
    expect(screen.getByText("v0.2.0 · Database reachable")).toBeInTheDocument();
    expect(fetchMock.mock.calls.map((c) => c[0])).toEqual(
      expect.arrayContaining([
        "http://127.0.0.1:8000/ready",
        "http://127.0.0.1:8000/api/v1/version",
      ]),
    );
  });
  it("handles failure and recovers on retry", async () => {
    fetchMock.mockRejectedValue(new Error("private server details"));
    render(<App />);
    await screen.findByText("Backend unavailable");
    expect(
      screen.queryByText("private server details"),
    ).not.toBeInTheDocument();
    success();
    fireEvent.click(screen.getByRole("button", { name: "Retry" }));
    await screen.findByText("Backend connected");
  });
  it("toggles theme accessibly", async () => {
    success();
    render(<App />);
    fireEvent.click(screen.getByRole("button", { name: "Dark theme" }));
    await waitFor(() =>
      expect(document.documentElement.dataset.theme).toBe("dark"),
    );
    expect(screen.getByRole("button", { name: "Dark theme" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    await screen.findByText("Backend connected");
  });
});
describe("API contract", () => {
  it("rejects HTTP failure", async () => {
    fetchMock.mockResolvedValue({ ok: false });
    await expect(verifyConnection()).rejects.toThrow("not ready");
  });
  it("rejects malformed response", async () => {
    fetchMock.mockResolvedValue({ ok: true, json: () => Promise.resolve({}) });
    await expect(verifyConnection()).rejects.toThrow("Unexpected");
  });
  it("propagates timeout or network failure", async () => {
    fetchMock.mockRejectedValue(new DOMException("Timed out", "TimeoutError"));
    await expect(verifyConnection()).rejects.toThrow("Timed out");
  });
});
