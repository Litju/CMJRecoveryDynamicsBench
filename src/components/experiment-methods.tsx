"use client";
import { useState } from "react";
import { ArrowUpRight } from "lucide-react";
import { data, models, sourceLink, type ModelId } from "@/lib/science";
import methods from "@/data/methods.json";

export function MetricLesson() {
  const [model, setModel] = useState<ModelId>("ridge_full");
  const [root, setRoot] = useState("A");
  const [index, setIndex] = useState(0);
  const selectedRoot = data.roots.find((r) => r.id === root)!;
  const cells = selectedRoot.models[model].cells;
  const current = cells[index];
  const outcome = index % 2 ? "net impulse" : "force";
  const unit = index % 2 ? "m/s" : "N/kg";
  return (
    <div className="metric-lesson" id="metric-lesson">
      <div className="lesson-heading">
        <span className="eyebrow">READ THE METRIC / TRY A REAL CELL</span>
        <h3>
          How much error,
          <br />
          <span>relative to what?</span>
        </h3>
        <p>
          NRMSE compares prediction error with the spread of the target in the
          same cell. It is unitless. It is never “percent prediction accuracy.”
        </p>
      </div>
      <div className="lesson-workbench">
        <div className="lesson-selects">
          <label>
            Recorded model
            <select
              value={model}
              onChange={(e) => setModel(e.target.value as ModelId)}
            >
              {models.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.name}
                </option>
              ))}
            </select>
          </label>
          <label>
            Test root
            <select value={root} onChange={(e) => setRoot(e.target.value)}>
              {data.roots.map((r) => (
                <option key={r.id}>{r.id}</option>
              ))}
            </select>
          </label>
        </div>
        <fieldset className="six-cells">
          <legend>Six equal-weight cells · select one</legend>
          {cells.map((c, i) => (
            <button
              key={c.cell}
              aria-pressed={index === i}
              onClick={() => setIndex(i)}
            >
              <span>
                H{[24, 48, 72][Math.floor(i / 2)]} ·{" "}
                {i % 2 ? "impulse" : "force"}
              </span>
              <strong>{c.nrmse.toFixed(4)}</strong>
            </button>
          ))}
        </fieldset>
        <div className="metric-equation" aria-live="polite" aria-atomic="true">
          <div>
            <span>RMSE · {unit}</span>
            <strong data-testid="lesson-rmse">{current.rmse.toFixed(6)}</strong>
          </div>
          <span aria-hidden="true">÷</span>
          <div>
            <span>Truth population SD · {unit}</span>
            <strong data-testid="lesson-sd">
              {current.truth_population_sd.toFixed(6)}
            </strong>
          </div>
          <span aria-hidden="true">=</span>
          <div>
            <span>Cell NRMSE</span>
            <strong data-testid="lesson-nrmse">
              {current.nrmse.toFixed(6)}
            </strong>
          </div>
        </div>
        <p className="method-note">
          Actual H{[24, 48, 72][Math.floor(index / 2)]} {outcome}, root {root};{" "}
          {current.rows.toLocaleString("en-US")} labels. Arithmetic uses
          unrounded values. Population SD uses ddof = 0.
        </p>
        <div className="lesson-aggregate">
          <span>Sum the six normalized errors, then divide by 6.</span>
          <strong data-testid="lesson-aggregate">
            {selectedRoot.models[model].mean_six_cell_nrmse.toFixed(6)}
          </strong>
          <small>Six-cell mean NRMSE</small>
        </div>
      </div>
      <details className="methods-sheet lesson-methods">
        <summary>Why can predicting zero produce NRMSE greater than 1?</summary>
        <p>
          “Zero innovation” predicts no change from baseline, not zero
          measurement error. If innovations have a nonzero mean, a zero forecast
          misses that mean as well as the variation around it.
        </p>
        <p className="formula-text">
          RMSE(0)² = population variance(y) + mean(y)²
          <br />
          NRMSE(0) = √(1 + mean(y)² / population variance(y))
        </p>
        <p>
          With nonzero truth SD this is at least 1. Training-fitted constants
          instead estimate each cell’s mean from training labels; a shifted test
          population can still give normalized error above 1.
        </p>
        <p>
          Normalize within each outcome/horizon/root first. Force N/kg and
          impulse m/s cannot be combined as raw RMSE. The across-root view is
          the mean of root-specific ratios, not mean RMSE divided by mean SD.
        </p>
      </details>
    </div>
  );
}

const ablations = [
  {
    id: "ridge_no_prior_history",
    name: "Remove prior history",
    family: "Ridge",
  },
  {
    id: "ridge_no_current_exposure",
    name: "Remove current exposure",
    family: "Ridge",
  },
  {
    id: "ridge_no_participant_context",
    name: "Remove participant context",
    family: "Ridge",
  },
  {
    id: "structured_no_prior_history",
    name: "Remove prior history",
    family: "Structured",
  },
] as const;
export function StudyMethods() {
  const [ablation, setAblation] = useState<(typeof ablations)[number]["id"]>(
    "ridge_no_participant_context",
  );
  const [camps, setCamps] = useState<24 | 48 | 96>(24);
  const variant = methods.variants[ablation];
  const family = ablation.startsWith("ridge")
    ? "ridge_full"
    : "structured_full";
  const difference =
    variant.root_mean_nrmse - methods.variants[family].root_mean_nrmse;
  return (
    <div className="study-methods">
      <details className="methods-sheet">
        <summary>
          Methods & evidence · splits, transformations and model selection
        </summary>
        <div className="split-design">
          {[
            {
              label: "01 / FIT",
              d: data.training,
              text: "Fit preprocessing, target scaling and model coefficients.",
            },
            {
              label: "02 / SELECT",
              d: data.development,
              text: "Choose alpha once. Freeze a content-addressed selection lock.",
            },
            {
              label: "03 / TEST × 3",
              d: data.roots[0].data,
              text: "Independent public roots A/B/C. Evaluate only after the lock.",
            },
          ].map((s) => (
            <article key={s.label}>
              <span className="eyebrow">{s.label}</span>
              <h4>{s.d.camps} camps</h4>
              <p>
                {s.d.episodes.toLocaleString("en-US")} episodes
                <br />
                {s.d.rows.toLocaleString("en-US")} horizon rows
              </p>
              <p>{s.text}</p>
            </article>
          ))}
        </div>
        <p>
          Participant, episode and query keys are checked for separation. Three
          horizons from an episode stay together. Public roots share a
          generator; this is not an independent empirical validation cohort.
        </p>
        <p>
          Ridge uses training-only feature and target standardization, an
          unpenalized intercept, and deterministic closed-form fitting. The
          structured comparator uses normalized public exposure primitives ×
          fixed exponential bases, public baseline/context and observed prior
          innovations; coefficients are learned from training rows, not copied
          from the generator.
        </p>
        <p>
          Grid: [{data.protocol.alpha_grid.join(", ")}]. Minimize development
          six-cell NRMSE; break ties toward lower alpha. All six
          ridge/structured configurations selected 0.01. A boundary winner is
          not an established optimum.
        </p>
        <div
          className="table-scroll"
          tabIndex={0}
          role="region"
          aria-label="Frozen selection results"
        >
          <table>
            <caption>
              Development-only selection · never retuned on test roots
            </caption>
            <thead>
              <tr>
                <th scope="col">Configuration</th>
                <th scope="col">Selected α</th>
                <th scope="col">Development NRMSE</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(methods.selection).map(([id, s]) => (
                <tr key={id}>
                  <th scope="row">{id.replaceAll("_", " ")}</th>
                  <td>{s.selected_alpha}</td>
                  <td>
                    {s.alpha_scores
                      .find((a) => a.alpha === s.selected_alpha)!
                      .development_mean_six_cell_nrmse.toFixed(6)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <a
          className="quiet-link"
          href={sourceLink("docs/M8_FIXED_MODE_PUBLIC_REFERENCE_STUDY.md")}
        >
          Selection lock, feature hashes & reproduction{" "}
          <ArrowUpRight size={14} />
        </a>
        <details className="protocol-raw">
          <summary>Inspect the exact frozen protocol JSON</summary>
          <pre
            tabIndex={0}
            role="region"
            aria-label="Frozen study protocol JSON"
          >
            {JSON.stringify(data.protocol, null, 2)}
          </pre>
        </details>
      </details>
      <div className="diagnostic-grid">
        <article className="diagnostic-panel">
          <span className="eyebrow">FALSIFICATION / REMOVE INFORMATION</span>
          <h3>Which inputs mattered here?</h3>
          <label htmlFor="ablation-select">Prespecified ablation</label>
          <select
            id="ablation-select"
            value={ablation}
            onChange={(e) => setAblation(e.target.value as typeof ablation)}
          >
            {ablations.map((a) => (
              <option key={a.id} value={a.id}>
                {a.family}: {a.name}
              </option>
            ))}
          </select>
          <div className="diagnostic-number" aria-live="polite">
            <strong data-testid="ablation-delta">
              +{difference.toFixed(6)}
            </strong>
            <span>mean NRMSE vs the full model · higher is worse</span>
          </div>
          <div className="diagnostic-bars">
            {[
              {
                name: "Full model",
                v: methods.variants[family].root_mean_nrmse,
              },
              { name: "Without selected inputs", v: variant.root_mean_nrmse },
            ].map((row) => (
              <div key={row.name}>
                <span>
                  {row.name}
                  <strong>{row.v.toFixed(6)}</strong>
                </span>
                <div>
                  <i style={{ width: `${row.v * 100}%` }} />
                </div>
              </div>
            ))}
          </div>
          <p>
            Removing participant context changed ridge’s mean error by about
            0.000076. Current exposure and prior history helped more on these
            same-world roots. This is descriptive; no direct ablation contrast
            interval is supplied.
          </p>
        </article>
        <article className="diagnostic-panel">
          <span className="eyebrow">SAMPLE EFFICIENCY / NESTED SUBSETS</span>
          <h3>More camps. Small differences.</h3>
          <fieldset>
            <legend>Training camps</legend>
            <div className="segmented">
              {([24, 48, 96] as const).map((n) => (
                <button
                  key={n}
                  aria-pressed={camps === n}
                  onClick={() => setCamps(n)}
                >
                  {n} camps
                </button>
              ))}
            </div>
          </fieldset>
          <div className="sample-scores" aria-live="polite">
            {(["ridge", "structured", "training_constant"] as const).map(
              (id) => (
                <div key={id}>
                  <span>
                    {id === "ridge"
                      ? "Ridge"
                      : id === "structured"
                        ? "Structured"
                        : "Constant"}
                  </span>
                  <strong data-testid={`sample-${id}`}>
                    {methods.variants[
                      `${id}_n${camps}`
                    ].root_mean_nrmse.toFixed(6)}
                  </strong>
                </div>
              ),
            )}
          </div>
          <p>
            {camps} camps contain {(camps * 250).toLocaleString("en-US")}{" "}
            episodes. The 24-camp subset is already substantial. Full-data alpha
            stays fixed; preprocessing and coefficients are refitted within each
            nested subset.
          </p>
        </article>
      </div>
      <p className="story-caption">
        All diagnostic values are arithmetic means over the three recorded
        roots. Same six-cell metric, separate prespecified configurations.{" "}
        <a href="/data/methods.json" download>
          Download all 17 configurations + selection evidence ↗
        </a>
      </p>
    </div>
  );
}

export function IntervalPlot({
  model,
  root,
}: {
  model: ModelId;
  root: string;
}) {
  const roots = data.roots.filter((r) => root === "mean" || r.id === root);
  const bounds = roots.flatMap(
    (r) => r.models[model].bootstrap.mean_six_cell_nrmse_95_percentile_interval,
  );
  const pad = Math.max(
    (Math.max(...bounds) - Math.min(...bounds)) * 0.2,
    0.002,
  );
  const low = Math.min(...bounds) - pad,
    high = Math.max(...bounds) + pad;
  const x = (v: number) => 90 + ((v - low) / (high - low)) * 720;
  return (
    <figure className="interval-plot">
      <figcaption>REPORTED AGGREGATE INTERVALS · 95% CAMP BOOTSTRAP</figcaption>
      <svg
        viewBox={`0 0 900 ${70 + roots.length * 48}`}
        role="img"
        aria-label="Each root’s aggregate NRMSE and its recorded 95 percent camp-bootstrap interval. Exact endpoints are in the following table; these are not cell intervals or paired differences between selected models."
      >
        {roots.map((r, i) => {
          const m = r.models[model];
          const [a, b] = m.bootstrap.mean_six_cell_nrmse_95_percentile_interval;
          return (
            <g key={r.id}>
              <text x="12" y={44 + i * 48} fill="#a6b0ae" fontSize="13">
                Root {r.id}
              </text>
              <line
                x1="90"
                x2="810"
                y1={40 + i * 48}
                y2={40 + i * 48}
                stroke="#2d3639"
              />
              <line
                x1={x(a)}
                x2={x(b)}
                y1={40 + i * 48}
                y2={40 + i * 48}
                stroke="#a9f5dc"
                strokeWidth="5"
              />
              <circle
                cx={x(m.mean_six_cell_nrmse)}
                cy={40 + i * 48}
                r="6"
                fill="#eef2ef"
              />
              <line
                x1={x(a)}
                x2={x(a)}
                y1={32 + i * 48}
                y2={48 + i * 48}
                stroke="#a9f5dc"
              />
              <line
                x1={x(b)}
                x2={x(b)}
                y1={32 + i * 48}
                y2={48 + i * 48}
                stroke="#a9f5dc"
              />
            </g>
          );
        })}
        {[low, (low + high) / 2, high].map((v) => (
          <text
            key={v}
            x={x(v)}
            y={65 + roots.length * 48}
            fill="#a6b0ae"
            fontSize="12"
            textAnchor="middle"
          >
            {v.toFixed(4)}
          </text>
        ))}
      </svg>
      <p>
        Dots: aggregate NRMSE. Lines: within-root intervals. Axis is zoomed to
        the shown endpoints; intervals do not include training refits.
      </p>
    </figure>
  );
}
