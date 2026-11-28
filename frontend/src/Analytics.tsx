import { useEffect, useState } from "react";
import { base } from "./api";
type Cell = {
  label: string;
  count: number;
  churn: number | null;
  low: number | null;
  high: number | null;
};
type Distribution = {
  name: string;
  unit: string;
  n: number;
  missing: number;
  summary: Record<string, number>;
  cells: Cell[];
  class_means: number[];
  effect: number | null;
  interval: number[];
};
type Report = {
  dataset: string;
  version: string;
  view_version: string;
  eligible: number;
  positives: number;
  audit: Record<string, number>;
  folds: number[][];
  distributions: Distribution[];
  associations: { left: string; right: string; r: number }[];
  parity: boolean;
  repeated_groups: number;
  conflicting_groups: number;
};
type Catalog = {
  schema_version: string;
  approved: string[];
  excluded: Record<string, string>;
  derived: Record<string, [string, string, string]>;
  sets: Record<string, string[]>;
};
const label = (s: string) => s.replaceAll("_", " ");
const number = (v: number) =>
  v.toLocaleString(undefined, { maximumFractionDigits: 3 });
const percent = (v: number) => number(100 * v) + "%";
export default function Analytics({
  mode,
}: {
  mode: "analytics" | "features" | "evaluation";
}) {
  const [result, setResult] = useState<{
    report: Report | null;
    catalog: Catalog;
  } | null>(null);
  const [error, setError] = useState(false);
  const [attempt, bump] = useState(0);
  const [selected, select] = useState("");
  const [comparison, compare] = useState("");
  useEffect(() => {
    const controller = new AbortController();
    const signal = AbortSignal.any([
      controller.signal,
      AbortSignal.timeout(5000),
    ]);
    const get = async (url: string) => {
      const response = await fetch(base + url, { signal });
      if (!response.ok) throw Error();
      return response.json();
    };
    Promise.all([
      get(
        "/api/v1/analytics" +
          (import.meta.env.VITE_ANALYTICS_DATASET === "synthetic_churn_fixture"
            ? "?dataset=synthetic_churn_fixture"
            : ""),
      ),
      get("/api/v1/features"),
    ])
      .then(([report, catalog]) => {
        if (!controller.signal.aborted) setResult({ report, catalog });
      })
      .catch(() => {
        if (!controller.signal.aborted) setError(true);
      });
    return () => controller.abort();
  }, [attempt]);
  const title = {
    analytics: "Analytics",
    features: "Feature Lab",
    evaluation: "Evaluation design",
  }[mode];
  const report = result?.report;
  const dist =
    report?.distributions.find((d) => d.name === selected) ??
    report?.distributions[0];
  const correlations = report?.associations.filter(
    (a) => !comparison || a.left === comparison || a.right === comparison,
  );
  return (
    <section
      className="explorer analytics-page"
      aria-labelledby="analysis-title"
    >
      <h1 id="analysis-title">{title}</h1>
      {error ? (
        <div role="status">
          <p>Analysis could not be loaded.</p>
          <button
            className="theme-button"
            onClick={() => {
              setError(false);
              bump((n) => n + 1);
            }}
          >
            Retry analysis
          </button>
        </div>
      ) : !result ? (
        <p role="status">Loading analysis…</p>
      ) : mode === "features" ? (
        <div className="capability">
          <p>
            Feature schema {result.catalog.schema_version}. Batch and
            single-record parity:{" "}
            {report
              ? report.parity
                ? "verified"
                : "failed"
              : "no analysis available"}
            .
          </p>
          <h2>Approved source fields</h2>
          <p>{result.catalog.approved.map(label).join(", ")}</p>
          <h2>Excluded fields</h2>
          <ul>
            {Object.entries(result.catalog.excluded).map(([k, v]) => (
              <li key={k}>
                {label(k)} · {v}
              </li>
            ))}
          </ul>
          <h2>Engineered features</h2>
          {Object.entries(result.catalog.derived).map(
            ([n, [deps, formula, reason]]) => (
              <div key={n}>
                <h3>{label(n)}</h3>
                <p>
                  <code>{formula}</code> · Inputs: {label(deps)}. {reason}.
                </p>
              </div>
            ),
          )}
          <h2>Candidate sets</h2>
          <ul>
            {Object.entries(result.catalog.sets).map(([name, fields]) => (
              <li key={name}>
                {name} · {fields.length} raw and engineered columns ·{" "}
                {fields.map(label).join(", ")}
              </li>
            ))}
          </ul>
          <p>
            Snapshot features describe the source observation window.
            Comparative model performance has yet to be evaluated.
          </p>
        </div>
      ) : !report ? (
        <p role="status">
          No approved analysis is available. Generate a local report and enable
          its source in the backend configuration.
        </p>
      ) : (
        <>
          <p>
            {report.dataset === "synthetic_churn_fixture"
              ? "Synthetic fixture"
              : "UCI Iranian Churn"}{" "}
            · Eligible development observations only
          </p>
          <p>
            Dataset <code>{report.version}</code> · View{" "}
            <code>{report.view_version}</code>
          </p>
          <dl className="analysis-summary">
            <div>
              <dt>Eligible development</dt>
              <dd>{number(report.eligible)}</dd>
            </div>
            <div>
              <dt>Churn</dt>
              <dd>
                {number(report.positives)} (
                {percent(report.positives / report.eligible)})
              </dd>
            </div>
            <div>
              <dt>Approved predictors</dt>
              <dd>{report.distributions.length}</dd>
            </div>
            <div>
              <dt>Quarantined</dt>
              <dd>{report.audit.affected_dev}</dd>
            </div>
          </dl>
          {mode === "evaluation" ? (
            <article className="capability">
              <h2>Partition integrity</h2>
              <p>
                {report.audit.development} original development ·{" "}
                {report.audit.holdout} protected holdout ·{" "}
                {report.audit.shared_approved} shared approved vectors before
                quarantine.
              </p>
              <p>
                Group-based snapshot validation. Source customer identities and
                event dates are unavailable.
              </p>
              <table>
                <caption>Development validation folds</caption>
                <thead>
                  <tr>
                    <th>Fold</th>
                    <th>Non-churn</th>
                    <th>Churn</th>
                    <th>Total</th>
                  </tr>
                </thead>
                <tbody>
                  {report.folds.map(([neg, pos], i) => (
                    <tr key={i}>
                      <th scope="row">{i + 1}</th>
                      <td>{neg}</td>
                      <td>{pos}</td>
                      <td>{neg + pos}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </article>
          ) : (
            <>
              <article className="capability">
                <h2>Distributions</h2>
                <p>
                  {report.repeated_groups} repeated predictor groups, including{" "}
                  {report.conflicting_groups} with conflicting labels.{" "}
                  {report.folds.length} validation folds.
                </p>
                <label>
                  Feature{" "}
                  <select
                    value={dist?.name ?? ""}
                    onChange={(e) => select(e.target.value)}
                  >
                    {report.distributions.map((d) => (
                      <option key={d.name} value={d.name}>
                        {label(d.name)}
                      </option>
                    ))}
                  </select>
                </label>
                {dist && (
                  <>
                    <p>
                      {number(dist.n)} observations · {dist.unit} ·{" "}
                      {dist.missing} missing
                    </p>
                    <div className="bars" aria-hidden="true">
                      {dist.cells.map((c) => (
                        <div key={c.label}>
                          <span>{c.label}</span>
                          <div>
                            <b
                              style={{ width: (100 * c.count) / dist.n + "%" }}
                            />
                          </div>
                          <span>{c.count}</span>
                        </div>
                      ))}
                    </div>
                    <table>
                      <caption>
                        Distribution counts by value or interval
                      </caption>
                      <thead>
                        <tr>
                          <th>Value or bin</th>
                          <th>Count</th>
                          <th>Churn prevalence and 95% interval</th>
                        </tr>
                      </thead>
                      <tbody>
                        {dist.cells.map((c) => (
                          <tr key={c.label}>
                            <th scope="row">{c.label}</th>
                            <td>{c.count}</td>
                            <td>
                              {c.churn === null
                                ? "—"
                                : `${percent(c.churn / c.count)} (${percent(c.low!)}–${percent(c.high!)})`}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                    {dist.class_means.length === 2 && (
                      <p>
                        Mean without churn {number(dist.class_means[0])}; with
                        churn {number(dist.class_means[1])}. Standardized
                        difference{" "}
                        {dist.effect === null
                          ? "undefined"
                          : number(dist.effect)}
                        . Approximate unadjusted mean-difference interval{" "}
                        {dist.interval.map(number).join(" to ")}.
                      </p>
                    )}
                    <p>
                      {Object.entries(dist.summary)
                        .map(([k, v]) => label(k) + " " + number(v))
                        .join(" · ")}
                    </p>
                  </>
                )}
              </article>
              <article className="capability">
                <h2>Numeric associations</h2>
                <p>
                  Pearson r compares pairs of numeric predictors. Associations
                  describe the development sample and cannot establish cause.
                  Intervals above assume independent observations and may be too
                  narrow for grouped data.
                </p>
                <label>
                  Compare feature{" "}
                  <select
                    value={comparison}
                    onChange={(e) => compare(e.target.value)}
                  >
                    <option value="">All pairs</option>
                    {[
                      ...new Set(
                        report.associations.flatMap((a) => [a.left, a.right]),
                      ),
                    ]
                      .sort()
                      .map((n) => (
                        <option key={n} value={n}>
                          {label(n)}
                        </option>
                      ))}
                  </select>
                </label>
                <table>
                  <caption>
                    Pearson correlations · n = {number(report.eligible)}
                  </caption>
                  <thead>
                    <tr>
                      <th>Predictor</th>
                      <th>Compared with</th>
                      <th>r</th>
                    </tr>
                  </thead>
                  <tbody>
                    {correlations?.map((a) => (
                      <tr key={a.left + a.right}>
                        <th scope="row">{label(a.left)}</th>
                        <td>{label(a.right)}</td>
                        <td>{number(a.r)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </article>
            </>
          )}
        </>
      )}
    </section>
  );
}
