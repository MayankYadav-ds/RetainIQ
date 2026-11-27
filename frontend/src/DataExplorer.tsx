import { useEffect, useState } from "react";
import { base } from "./api";

interface Summary {
  dataset: string;
  provenance: string;
  source: string;
  attribution: string;
  license: string;
  version: string;
  rows: number;
  features: number;
  churn: number;
  retained: number;
  missing: number;
  warnings: Record<string, number>;
  eligibility: Record<string, string>;
  capabilities: Record<string, boolean>;
}
type State =
  | { kind: "loading" | "failure" }
  | { kind: "ready"; items: Summary[] };
const label = (s: string) => s.replaceAll("_", " ");
function isSummary(x: unknown): x is Summary {
  if (!x || typeof x !== "object") return false;
  const obj = x as Record<string, unknown>;
  const map = (key: string, type: string) =>
    obj[key] !== null &&
    typeof obj[key] === "object" &&
    !Array.isArray(obj[key]) &&
    Object.values(obj[key] as object).every((v) => typeof v === type);
  return (
    [
      "dataset",
      "provenance",
      "source",
      "attribution",
      "license",
      "version",
    ].every((k) => typeof obj[k] === "string") &&
    ["rows", "features", "churn", "retained", "missing"].every(
      (k) => Number.isSafeInteger(obj[k]) && Number(obj[k]) >= 0,
    ) &&
    map("warnings", "number") &&
    map("eligibility", "string") &&
    map("capabilities", "boolean")
  );
}
export default function DataExplorer() {
  const [state, setState] = useState<State>({ kind: "loading" });
  const [attempt, retry] = useState(0);
  useEffect(() => {
    const ctl = new AbortController();
    async function load() {
      try {
        const r = await fetch(base + "/api/v1/datasets", {
          signal: AbortSignal.any([ctl.signal, AbortSignal.timeout(5000)]),
          credentials: "omit",
        });
        if (!r.ok) throw new Error();
        const items: unknown = await r.json();
        if (!Array.isArray(items) || !items.every(isSummary)) throw new Error();
        if (!ctl.signal.aborted) setState({ kind: "ready", items });
      } catch {
        if (!ctl.signal.aborted) setState({ kind: "failure" });
      }
    }
    void load();
    return () => ctl.abort();
  }, [attempt]);
  return (
    <section className="explorer" aria-labelledby="explorer-title">
      <h1 id="explorer-title">Data Explorer</h1>
      <p>
        Inspect approved dataset versions, quality findings and feature
        eligibility.
      </p>
      {state.kind === "loading" && (
        <p role="status">Loading dataset registry…</p>
      )}
      {state.kind === "failure" && (
        <div role="status">
          <p>Dataset registry unavailable.</p>
          <button
            className="theme-button"
            onClick={() => {
              setState({ kind: "loading" });
              retry((n) => n + 1);
            }}
          >
            Retry registry
          </button>
        </div>
      )}
      {state.kind === "ready" &&
        (state.items.length === 0 ? (
          <p role="status">No approved datasets registered.</p>
        ) : (
          state.items.map((s) => (
            <article key={s.dataset} className="capability">
              <h2>{label(s.dataset)}</h2>
              <p>
                {s.provenance} · {s.license}
              </p>
              <p>{s.attribution}</p>
              <p>{s.source}</p>
              <p>
                Version <code>{s.version}</code>
              </p>
              <dl>
                {Object.entries({
                  Observations: s.rows,
                  "Source predictors": s.features,
                  Churn: s.churn,
                  "Non-churn": s.retained,
                  "Missing cells": s.missing,
                }).map(([k, v]) => (
                  <div key={k}>
                    <dt>{k}</dt>
                    <dd>{v.toLocaleString()}</dd>
                  </div>
                ))}
              </dl>
              <h3>Quality findings</h3>
              <p>
                Counts show affected rows per rule. A row can trigger multiple
                findings.
              </p>
              {Object.keys(s.warnings).length ? (
                <ul>
                  {Object.entries(s.warnings).map(([k, v]) => (
                    <li key={k}>
                      {label(k)} · {v}
                    </li>
                  ))}
                </ul>
              ) : (
                <p>No warnings recorded.</p>
              )}
              <h3>Feature eligibility</h3>
              <ul>
                {Object.entries(s.eligibility).map(([k, v]) => (
                  <li key={k}>
                    {label(k)} · {v}
                  </li>
                ))}
              </ul>
              <h3>Analysis support</h3>
              <ul>
                {Object.entries(s.capabilities).map(([k, v]) => (
                  <li key={k}>
                    {label(k)} · {v ? "Supported" : "Unsupported"}
                  </li>
                ))}
              </ul>
            </article>
          ))
        ))}
    </section>
  );
}
