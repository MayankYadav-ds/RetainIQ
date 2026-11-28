import { useEffect, useRef, useState } from "react";
import { base } from "./api";
type Stats = Record<string, number | null>;
type Leader = {
  family: string;
  status: string;
  metrics?: Stats;
  features?: string[];
  seconds?: number;
  ap_sd?: number;
};
type Charts = {
  roc: number[][];
  pr: number[][];
  calibration: {
    bin: number;
    count: number;
    predicted: number;
    observed: number;
  }[];
  ranking: {
    fraction: number;
    precision: number;
    recall: number;
    lift: number;
  }[];
  ece: number;
};
type Active = {
  model: string;
  family: string;
  feature_set: string;
  calibration: string;
  threshold: number;
  dataset: string;
  target: string;
  limitations: string;
};
type Evidence = {
  leaderboard: Leader[];
  development: Charts;
  threshold_sweep: Record<string, number>[];
  experiment: string;
  selected: string;
};
type Final = {
  receipt: string;
  metrics: Stats;
  charts: Charts;
  threshold: number;
};
type Prediction = {
  model: string;
  probability: number;
  raw_probability: number;
  threshold: number;
  predicted_class: number;
  risk_tier: string;
  warnings: string[];
  target: string;
  limitations: string;
};
const fmt = (x: number | null | undefined) => (x == null ? "—" : x.toFixed(3));
const title = (x: string) => x.replaceAll("_", " ");
const percent = (x: number) => (x * 100).toFixed(1) + "%";
const all = [
  ["ap", "Average precision"],
  ["auc", "ROC-AUC"],
  ["brier", "Brier"],
  ["precision", "Precision"],
  ["recall", "Recall"],
  ["f1", "F1"],
  ["accuracy", "Accuracy"],
] as const;
async function get<T>(url: string, signal: AbortSignal): Promise<T> {
  const r = await fetch(base + url, { signal });
  if (!r.ok) throw Error("request_failed");
  return r.json() as Promise<T>;
}
function Curve({
  points,
  label,
  x,
  y,
}: {
  points: number[][];
  label: string;
  x: string;
  y: string;
}) {
  const ref = useRef<HTMLCanvasElement>(null);
  useEffect(() => {
    const c = ref.current?.getContext("2d");
    if (!c) return;
    const maxY = Math.max(1, ...points.map((p) => p[1]));
    c.clearRect(0, 0, 520, 250);
    c.strokeStyle = "#6d7d77";
    c.lineWidth = 1;
    for (let i = 0; i <= 4; i++) {
      const xx = 48 + i * 110;
      const yy = 20 + i * 50;
      c.beginPath();
      c.moveTo(xx, 20);
      c.lineTo(xx, 220);
      c.moveTo(48, yy);
      c.lineTo(488, yy);
      c.stroke();
    }
    c.fillStyle = "#657874";
    c.font = "12px system-ui";
    for (let i = 0; i <= 4; i++) {
      c.fillText((i / 4).toFixed(2), 35 + i * 110, 239);
      c.fillText(((maxY * i) / 4).toFixed(2), 9, 224 - i * 50);
    }
    c.beginPath();
    c.strokeStyle = "#37a581";
    c.lineWidth = 3;
    points.forEach(([xx, yy], i) => {
      const a = 48 + 440 * xx,
        b = 220 - (200 * yy) / maxY;
      if (i) c.lineTo(a, b);
      else c.moveTo(a, b);
    });
    c.stroke();
  }, [points]);
  return (
    <figure>
      <figcaption>
        {label} · horizontal {x}, vertical {y}
      </figcaption>
      <canvas
        width="520"
        height="250"
        ref={ref}
        aria-label={label}
        role="img"
      />
      <details>
        <summary>View chart values</summary>
        <table>
          <caption>{label} values</caption>
          <thead>
            <tr>
              <th>{x}</th>
              <th>{y}</th>
            </tr>
          </thead>
          <tbody>
            {points.map(([a, b], i) => (
              <tr key={i}>
                <td>{fmt(a)}</td>
                <td>{fmt(b)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </details>
    </figure>
  );
}
export default function ModelLab() {
  const [result, setResult] = useState<{
    active: Active | null;
    board: Evidence | null;
    final: Final | null;
  } | null>(null);
  const [error, setError] = useState(false),
    [retry, setRetry] = useState(0);
  const [sort, setSort] = useState("ap"),
    [panel, setPanel] = useState("roc"),
    [scope, setScope] = useState("development"),
    [threshold, setThreshold] = useState(50);
  useEffect(() => {
    const c = new AbortController();
    const signal = AbortSignal.any([c.signal, AbortSignal.timeout(6000)]);
    Promise.all([
      get<Active | null>("/api/v1/models/active", signal),
      get<Evidence | null>("/api/v1/models/benchmark", signal),
      get<Final | null>("/api/v1/models/evaluation", signal),
    ])
      .then(([active, board, final]) => {
        if (!c.signal.aborted) setResult({ active, board, final });
      })
      .catch(() => {
        if (!c.signal.aborted) setError(true);
      });
    return () => c.abort();
  }, [retry]);
  const model = result?.active,
    board = result?.board,
    final = result?.final;
  const chart = scope === "final" ? final?.charts : board?.development;
  const chosen = board?.leaderboard.find((x) => x.family === board.selected);
  const cm = scope === "final" ? final?.metrics : chosen?.metrics;
  const at = board?.threshold_sweep.find(
    (x) => Math.round(x.threshold * 100) === threshold,
  );
  const rows = [...(board?.leaderboard ?? [])].sort((a, b) => {
    const value = (l: Leader) =>
      sort === "seconds" ? l.seconds : l.metrics?.[sort];
    const first = value(a),
      second = value(b);
    if (first == null) return second == null ? 0 : 1;
    if (second == null) return -1;
    return sort === "brier" || sort === "seconds"
      ? first - second
      : second - first;
  });
  const curve =
    chart &&
    (
      {
        roc: [chart.roc, "False positive rate", "True positive rate"],
        pr: [chart.pr, "Recall", "Precision"],
        calibration: [
          chart.calibration.map((c) => [c.predicted, c.observed]),
          "Mean predicted probability",
          "Observed prevalence",
        ],
        gains: [
          chart.ranking.map((r) => [r.fraction, r.recall]),
          "Fraction reviewed",
          "Recall",
        ],
        lift: [
          chart.ranking.map((r) => [r.fraction, r.lift]),
          "Fraction reviewed",
          "Lift",
        ],
      } as Record<string, [number[][], string, string]>
    )[panel];
  return (
    <section
      className="explorer analytics-page model-lab"
      aria-labelledby="model-title"
    >
      <h1 id="model-title">Model Lab</h1>
      {error ? (
        <div role="status">
          Model evidence could not be loaded.{" "}
          <button
            className="theme-button"
            onClick={() => {
              setError(false);
              setRetry((i) => i + 1);
            }}
          >
            Retry models
          </button>
        </div>
      ) : !result ? (
        <p role="status">Loading model evidence…</p>
      ) : !model || !board ? (
        <p role="status">
          No approved model is active. Configure a verified local model to view
          its evidence.
        </p>
      ) : (
        <>
          <article className="capability">
            <h2>{title(model.family)}</h2>
            <p>
              {title(model.dataset)} · {model.feature_set} · {model.calibration}{" "}
              calibration
            </p>
            <p>
              <code>{model.model}</code>
            </p>
            <p>
              {model.target}. {model.limitations}
            </p>
            <p>
              Selection uses grouped development average precision, then Brier
              score and model complexity. The UCI protocol searches three
              feature sets in nested folds. Outer results are
              development-informed.
            </p>
          </article>
          <article className="capability">
            <h2>Development leaderboard</h2>
            <label htmlFor="model-sort">Sort by</label>{" "}
            <select
              id="model-sort"
              value={sort}
              onChange={(e) => setSort(e.target.value)}
            >
              {all.map(([id, name]) => (
                <option key={id} value={id}>
                  {name}
                </option>
              ))}
              <option value="seconds">Training seconds</option>
            </select>
            <div
              className="table-scroll"
              tabIndex={0}
              role="region"
              aria-label="Scrollable model comparison"
            >
              <table>
                <caption>Pooled outer out-of-fold scores</caption>
                <thead>
                  <tr>
                    <th>Family</th>
                    <th>Feature sets by fold</th>
                    {all.map(([k, n]) => (
                      <th key={k}>{n}</th>
                    ))}
                    <th>Seconds</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((r) => (
                    <tr key={r.family}>
                      <th scope="row">{title(r.family)}</th>
                      <td>{r.features?.join(", ") || r.status}</td>
                      {all.map(([k]) => (
                        <td key={k}>{fmt(r.metrics?.[k])}</td>
                      ))}
                      <td>{fmt(r.seconds)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </article>
          <article className="capability">
            <h2>Evaluation evidence</h2>
            <label htmlFor="evaluation-scope">Evaluation scope</label>{" "}
            <select
              id="evaluation-scope"
              value={scope}
              onChange={(e) => setScope(e.target.value)}
            >
              <option value="development">Development OOF</option>
              {final && <option value="final">Frozen final holdout</option>}
            </select>{" "}
            <label htmlFor="metric-chart">Chart</label>{" "}
            <select
              id="metric-chart"
              value={panel}
              onChange={(e) => setPanel(e.target.value)}
            >
              {["roc", "pr", "calibration", "gains", "lift"].map((p) => (
                <option key={p} value={p}>
                  {
                    {
                      roc: "ROC",
                      pr: "Precision–recall",
                      calibration: "Calibration",
                      gains: "Cumulative gains",
                      lift: "Cumulative lift",
                    }[p]
                  }
                </option>
              ))}
            </select>
            {curve && (
              <Curve
                points={curve[0]}
                label={title(panel)}
                x={curve[1]}
                y={curve[2]}
              />
            )}
            {panel === "calibration" && chart && (
              <table>
                <caption>Reliability bins</caption>
                <thead>
                  <tr>
                    <th>Bin</th>
                    <th>Sample count</th>
                    <th>Predicted</th>
                    <th>Observed</th>
                  </tr>
                </thead>
                <tbody>
                  {chart.calibration.map((c) => (
                    <tr key={c.bin}>
                      <th scope="row">{c.bin + 1}</th>
                      <td>{c.count}</td>
                      <td>{percent(c.predicted)}</td>
                      <td>{percent(c.observed)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
            {cm && (
              <table>
                <caption>
                  {scope === "final"
                    ? "Confusion at frozen operating threshold"
                    : "Pooled confusion at fold-specific thresholds"}
                </caption>
                <thead>
                  <tr>
                    <th>Observed</th>
                    <th>Predicted non-churn</th>
                    <th>Predicted churn</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <th scope="row">Non-churn</th>
                    <td>{cm.tn}</td>
                    <td>{cm.fp}</td>
                  </tr>
                  <tr>
                    <th scope="row">Churn</th>
                    <td>{cm.fn}</td>
                    <td>{cm.tp}</td>
                  </tr>
                </tbody>
              </table>
            )}
            {scope === "final" && final && (
              <>
                <p>
                  Frozen threshold {percent(final.threshold)}. Receipt{" "}
                  <code>{final.receipt}</code>
                </p>
                <dl>
                  {all.map(([k, n]) => (
                    <div key={k}>
                      <dt>{n}</dt>
                      <dd>{fmt(final.metrics[k])}</dd>
                    </div>
                  ))}
                </dl>
              </>
            )}
            {scope === "development" && at && (
              <>
                <h3>Development threshold explorer</h3>
                <p>
                  Illustrative comparisons use pooled development OOF
                  probabilities.
                </p>
                <label htmlFor="dev-threshold">Threshold {threshold}%</label>
                <input
                  id="dev-threshold"
                  type="range"
                  min="5"
                  max="95"
                  value={threshold}
                  onChange={(e) => setThreshold(Number(e.target.value))}
                />
                <p>
                  Precision {fmt(at.precision)} · Recall {fmt(at.recall)} · F1{" "}
                  {fmt(at.f1)} · F2 {fmt(at.f2)}
                </p>
              </>
            )}
          </article>
        </>
      )}
    </section>
  );
}
const sample = {
  call_failure: 3,
  complains: 0,
  subscription_length: 17,
  seconds_of_use: 1200,
  frequency_of_use: 24,
  frequency_of_sms: 8,
  distinct_called_numbers: 9,
  tariff_plan: 1,
};
const names: [keyof typeof sample, string][] = [
  ["call_failure", "Call failures (count)"],
  ["complains", "Complaint status"],
  ["subscription_length", "Subscription length (months)"],
  ["seconds_of_use", "Total usage (seconds)"],
  ["frequency_of_use", "Usage frequency (count)"],
  ["frequency_of_sms", "SMS frequency (count)"],
  ["distinct_called_numbers", "Distinct called numbers (count)"],
  ["tariff_plan", "Tariff plan"],
];
export function Simulator() {
  const [values, setValues] = useState(
    Object.fromEntries(Object.entries(sample).map(([k, v]) => [k, String(v)])),
  );
  const [prediction, setPrediction] = useState<Prediction | null>(null);
  const [error, setError] = useState(""),
    [waiting, setWaiting] = useState(false);
  const change = (k: string, v: string) => {
    setValues((old) => ({ ...old, [k]: v }));
    setPrediction(null);
    setError("");
  };
  return (
    <section className="explorer analytics-page" aria-labelledby="sim-title">
      <h1 id="sim-title">Prediction simulator</h1>
      <p>
        The starting values are an invented example. Enter first-nine-month
        aggregates to obtain a benchmark prediction for month-twelve churn
        state.
      </p>
      <form
        className="capability prediction-form"
        onSubmit={async (e) => {
          e.preventDefault();
          setError("");
          setPrediction(null);
          const input = Object.fromEntries(
            Object.entries(values).map(([k, v]) => [
              k,
              v.trim() === "" ? NaN : Number(v),
            ]),
          );
          if (
            Object.values(input).some((v) => !Number.isSafeInteger(v) || v < 0)
          ) {
            setError("Enter a nonnegative integer for each count.");
            return;
          }
          setWaiting(true);
          try {
            const r = await fetch(base + "/api/v1/predictions/single", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify(input),
              signal: AbortSignal.timeout(6000),
            });
            if (!r.ok) {
              setError(
                r.status === 503
                  ? "No approved model is active."
                  : "Prediction unavailable. Check the inputs and try again.",
              );
              return;
            }
            setPrediction((await r.json()) as Prediction);
          } catch {
            setError("Could not reach the prediction service. Try again.");
          } finally {
            setWaiting(false);
          }
        }}
      >
        {names.map(([k, n]) => (
          <div key={k}>
            <label htmlFor={k}>{n}</label>
            {k === "complains" || k === "tariff_plan" ? (
              <select
                id={k}
                value={values[k]}
                disabled={waiting}
                onChange={(e) => change(k, e.target.value)}
              >
                {(k === "complains"
                  ? [
                      [0, "No complaint"],
                      [1, "Complaint"],
                    ]
                  : [
                      [1, "Pay as you go"],
                      [2, "Contract"],
                    ]
                ).map(([v, t]) => (
                  <option key={v} value={v}>
                    {t}
                  </option>
                ))}
              </select>
            ) : (
              <input
                id={k}
                type="number"
                min={0}
                max={Number.MAX_SAFE_INTEGER}
                step={1}
                required
                disabled={waiting}
                value={values[k]}
                onChange={(e) => change(k, e.target.value)}
              />
            )}
          </div>
        ))}
        <button type="submit" className="theme-button" disabled={waiting}>
          {waiting ? "Predicting…" : "Predict churn"}
        </button>
      </form>
      {error && <p role="alert">{error}</p>}
      {prediction && (
        <article className="capability" aria-live="polite">
          <h2>Churn probability {percent(prediction.probability)}</h2>
          <p>
            Risk tier {prediction.risk_tier} · Class{" "}
            {prediction.predicted_class ? "churn" : "non-churn"} · Decision
            threshold {percent(prediction.threshold)}
          </p>
          <p>
            Raw model probability {percent(prediction.raw_probability)} · Model{" "}
            <code>{prediction.model}</code>
          </p>
          <p>
            {prediction.target}. {prediction.limitations}
          </p>
          {prediction.warnings.length > 0 && (
            <ul>
              {prediction.warnings.map((w) => (
                <li key={w}>{w}</li>
              ))}
            </ul>
          )}
          <p>
            SHAP explanations are planned. Changing the inputs illustrates model
            sensitivity.
          </p>
        </article>
      )}
    </section>
  );
}
