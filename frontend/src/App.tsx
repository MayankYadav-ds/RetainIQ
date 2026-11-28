import { useEffect, useState } from "react";
import { verifyConnection, type Connection } from "./api";

import Analytics from "./Analytics";
import ModelLab, { Simulator } from "./ModelLab";
import DataExplorer from "./DataExplorer";

type Status =
  | { state: "loading" }
  | { state: "error" }
  | { state: "connected"; data: Connection };
const capabilities = [
  [
    "01",
    "Understand churn",
    "Calibrated risk estimates, grounded in point-in-time customer behavior.",
    "Prediction",
  ],
  [
    "02",
    "See the drivers",
    "Individual explanations that describe model behavior without implying causality.",
    "Explainability",
  ],
  [
    "03",
    "Prioritize action",
    "Contribution margin at risk and budget-constrained retention scenarios.",
    "Decision support",
  ],
];

export default function App() {
  const [explorer, setExplorer] = useState(window.location.hash);
  useEffect(() => {
    const changed = () => setExplorer(window.location.hash);
    window.addEventListener("hashchange", changed);
    return () => window.removeEventListener("hashchange", changed);
  }, []);
  const [status, setStatus] = useState<Status>({ state: "loading" });
  const [attempt, setAttempt] = useState(0);
  const [dark, setDark] = useState(() => {
    try {
      return localStorage.getItem("retainiq-theme") === "dark";
    } catch {
      return false;
    }
  });
  useEffect(() => {
    document.documentElement.dataset.theme = dark ? "dark" : "light";
    try {
      localStorage.setItem("retainiq-theme", dark ? "dark" : "light");
    } catch {
      /* optional preference */
    }
  }, [dark]);
  useEffect(() => {
    const controller = new AbortController();
    verifyConnection(controller.signal)
      .then((data) => {
        if (!controller.signal.aborted) setStatus({ state: "connected", data });
      })
      .catch(() => {
        if (!controller.signal.aborted) setStatus({ state: "error" });
      });
    return () => controller.abort();
  }, [attempt]);

  return (
    <>
      <a className="skip-link" href="#main">
        Skip to content
      </a>
      <header className="header">
        <a className="brand" href="#main" aria-label="RetainIQ home">
          <span className="brand-mark" aria-hidden="true"></span>Retain
          <span>IQ</span>
        </a>
        <nav aria-label="Main navigation">
          <a href="#datasets">Data Explorer</a>
          <a href="#analytics">Analytics</a>
          <a href="#models">Model Lab</a>
          <a href="#predict">Prediction simulator</a>
          <a href="#features">Feature Lab</a>
          <a href="#evaluation">Evaluation design</a>
          <a href="#approach">Approach</a>
          <a href="#foundation">Foundation</a>
          <a href="https://github.com/MayankYadav-ds/RetainIQ">
            Documentation <span aria-hidden="true">↗</span>
          </a>
        </nav>
        <button
          className="theme-button"
          aria-label="Dark theme"
          aria-pressed={dark}
          onClick={() => setDark(!dark)}
        >
          <span aria-hidden="true">◐</span> Dark theme
        </button>
      </header>
      <main id="main">
        {explorer === "#models" ? (
          <ModelLab />
        ) : explorer === "#predict" ? (
          <Simulator />
        ) : explorer === "#analytics" ||
          explorer === "#features" ||
          explorer === "#evaluation" ? (
          <Analytics
            mode={
              explorer === "#analytics"
                ? "analytics"
                : explorer === "#features"
                  ? "features"
                  : "evaluation"
            }
          />
        ) : explorer === "#datasets" ? (
          <DataExplorer />
        ) : (
          <>
            <section className="hero" aria-labelledby="headline">
              <div className="hero-copy">
                <p className="eyebrow">
                  <span className="dot" /> CUSTOMER RETENTION INTELLIGENCE
                </p>
                <h1 id="headline">
                  Understand risk.
                  <br />
                  Make retention
                  <br />
                  <em>worth the investment.</em>
                </h1>
                <p className="intro">
                  From customer signals to evidence-based decisions. RetainIQ is
                  being built to connect explainable churn prediction with the
                  economics of retention.
                </p>
                <div className="hero-actions">
                  <a className="button primary" href="#foundation">
                    Explore the foundation <span aria-hidden="true">↓</span>
                  </a>
                  <a
                    className="text-link"
                    href="https://github.com/MayankYadav-ds/RetainIQ"
                  >
                    View source <span aria-hidden="true">↗</span>
                  </a>
                </div>
                <p className="phase-note">
                  <span className="phase-pill">PHASE 3</span> Churn benchmark ·
                  Local benchmark inference
                </p>
              </div>
              <aside
                className="system-card"
                aria-label="Platform foundation status"
              >
                <div className="card-top">
                  <span className="mini-label">PLATFORM / SYSTEM CHECK</span>
                  <span className="outline-pill">LOCAL FIRST</span>
                </div>
                <div className="orbit" aria-hidden="true">
                  <div className="orbit-ring outer" />
                  <div className="orbit-ring inner" />
                  <div className="orbit-core">IQ</div>
                  <span className="orbit-node n1" />
                  <span className="orbit-node n2" />
                  <span className="orbit-node n3" />
                  <span className="orbit-line" />
                </div>
                <div className="system-heading">
                  <h2>A verifiable starting point.</h2>
                  <p>Live connectivity. Transparent delivery status.</p>
                </div>
                <div className="connection" role="status" aria-live="polite">
                  <span className={`status-dot ${status.state}`} />
                  <div>
                    <strong>
                      {status.state === "loading"
                        ? "Checking backend…"
                        : status.state === "connected"
                          ? "Backend connected"
                          : "Backend unavailable"}
                    </strong>
                    <span>
                      {status.state === "connected"
                        ? `v${status.data.version.version} · Database reachable`
                        : status.state === "loading"
                          ? "Verifying API and database readiness"
                          : "Start the API, then check the connection again."}
                    </span>
                  </div>
                  {status.state === "error" && (
                    <button
                      className="retry"
                      onClick={() => {
                        setStatus({ state: "loading" });
                        setAttempt((x) => x + 1);
                      }}
                    >
                      Retry
                    </button>
                  )}
                </div>
                <div className="card-bottom">
                  <span>Prediction engine</span>
                  <span>Open Model Lab</span>
                </div>
              </aside>
            </section>
            <section
              id="approach"
              className="approach"
              aria-labelledby="approach-title"
            >
              <div className="section-heading">
                <div>
                  <p className="eyebrow">THE DIRECTION</p>
                  <h2 id="approach-title">
                    A clearer path from insight to action.
                  </h2>
                </div>
                <p>
                  Planned capabilities.
                  <br />
                  Built on evidence, not promises.
                </p>
              </div>
              <div className="capability-grid">
                {capabilities.map(([number, title, description, category]) => (
                  <article className="capability" key={number}>
                    <div className="capability-top">
                      <span>{number}</span>
                      <span className="planned">PLANNED</span>
                    </div>
                    <h3>{title}</h3>
                    <p>{description}</p>
                    <span className="category">
                      {category} <span aria-hidden="true">↗</span>
                    </span>
                  </article>
                ))}
              </div>
            </section>
            <section
              id="foundation"
              className="foundation"
              aria-labelledby="foundation-title"
            >
              <div>
                <p className="eyebrow">BUILT TO BE INSPECTED</p>
                <h2 id="foundation-title">Trust starts with the foundation.</h2>
                <p>
                  Local execution, explicit data provenance and reproducible
                  evaluation are design commitments from day one.
                </p>
              </div>
              <dl>
                <div>
                  <dt>Available now</dt>
                  <dd>
                    Health and readiness APIs, version metadata, typed
                    configuration and this connected application shell.
                  </dd>
                </div>
                <div>
                  <dt>Dataset evidence</dt>
                  <dd>
                    The Data Explorer shows approved aggregate metadata. Local
                    churn predictions require an approved active model.
                  </dd>
                </div>
                <div>
                  <dt>Scientific integrity</dt>
                  <dd>
                    Predictive explanations are associations. Intervention ROI
                    requires causal evidence or clearly labeled assumptions.
                  </dd>
                </div>
              </dl>
            </section>
          </>
        )}
      </main>
      <footer>
        <a className="brand small" href="#main">
          Retain<span>IQ</span>
        </a>
        <span>Evidence before impact.</span>
        <span>v0.4.0 · Phase 3</span>
      </footer>
    </>
  );
}
